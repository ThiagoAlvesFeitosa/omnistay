# Fase 0 — Pesquisa e decisões técnicas: Disparar Coleta de Dados

Cada seção registra a decisão, por que ela foi tomada e o que foi rejeitado. As divergências
documentais encontradas no caminho estão consolidadas na seção 10.

---

## 1. Independência estrutural: gravar + enfileirar na mesma transação; enviar depois

**Decisão**: `POST /reservas` bem-sucedido, na **mesma transação** que já cria hóspede/reserva/
vínculo, também:

1. grava uma `mensagem` de saída com `status_envio = 'pendente'`;
2. grava uma linha em `trabalho` com `tipo = 'enviar_coleta'` e `status = 'pendente'`.

A resposta HTTP `201` volta **sem** chamar a mensageria. Um processo `worker` consome
`trabalho` com `SELECT … FOR UPDATE SKIP LOCKED`, chama `MensageriaGateway` e atualiza
`mensagem.status_envio` e o status do trabalho.

**Rationale**: a spec e o Artigo III exigem independência estrutural, não `try/except` na
mesma requisição. Se a API chamar o provedor e falhar, ou a reserva “parece” frágil ao
usuário, ou alguém é tentado a desfazer o commit — os dois caminhos violam a premissa.
Enfileirar no mesmo `COMMIT` da reserva garante: ou existe reserva **e** pendência, ou não
existe nenhuma das duas (FR-016).

**Alternativas consideradas**:

- **`BackgroundTasks` / thread na API**: Artefato 5 já rejeitou — reinício perde o envio sem
  rastro.
- **Enviar na requisição e “só não rollbackar”**: satisfaz o sintoma, não a estrutura; a API
  fica lenta e acoplada à Meta.
- **Outbox em tabela aparte sem `mensagem` na criação**: o histórico e o status na fila do dia
  nasceriam só depois do worker; falha antes do primeiro insert de mensagem deixaria a
  recepção sem sinalização. Rejeitado.

---

## 2. Tabela `trabalho` (a fila que faltava no esquema)

**Decisão**: criar a tabela `trabalho` no PostgreSQL, com migração Alembic **e** atualização de
`docs/04-schema.sql` na mesma entrega. Nome no singular, vocabulário do domínio (“um trabalho
pendente”), alinhado a `mensagem` / `reserva`.

| Campo | Função |
| --- | --- |
| `id_trabalho` | PK |
| `id_hotel` | Multi-tenant (Artigo XIV); filtro em toda consulta |
| `tipo` | Domínio fechado; nesta fatia só `enviar_coleta` |
| `payload` | `JSONB` com pelo menos `id_reserva` e `id_mensagem` |
| `status` | `pendente` · `processando` · `concluido` · `falha` |
| `tentativas` | Contador de tentativas de envio |
| `proxima_tentativa_em` | `NULL` = elegível agora; preenchido no backoff |
| `erro_ultima_tentativa` | Código/resumo **sem** conteúdo pessoal |
| `processando_desde` | Para reclaim se o worker morrer após marcar `processando` |
| `criado_em` / `atualizado_em` | Auditoria operacional |

**Unicidade da coleta**: índice único parcial

```sql
UNIQUE ( ((payload->>'id_reserva')::bigint) )
  WHERE tipo = 'enviar_coleta'
```

Garante no banco no máximo um trabalho de coleta por reserva (Artigo IX / FR-001 / FR-005).

**Rationale**: o Artefato 5 §8.1 descreveu os campos de controle e omitiu o DDL — lacuna que a
spec 005 já apontou. Sem a tabela, a independência estrutural não tem onde morar.

**Alternativas consideradas**:

- **Reusar `evento_webhook`**: depósito de entrada idempotente; não é fila de saída.
- **Só `mensagem.status_envio = pendente` como fila**: mistura histórico de conversa com
  agendamento de retry/`SKIP LOCKED`; o worker teria de escanear `mensagem` com regras
  diferentes por tipo futuro. Tabela de trabalho genérica antecipa F1.4/F3 sem segunda
  invenção.
- **Redis/Celery**: proibidos pelo Artigo XI e pela stack fixa.

---

## 3. Uma `mensagem` lógica por coleta; retry não duplica pedido ao hóspede

**Decisão**: a linha em `mensagem` nasce **uma vez**, no commit da reserva, com o texto da
coleta já montado e `status_envio = 'pendente'`. O worker só **atualiza** essa linha
(`enviada` ou, após esgotar tentativas, `falha`) e grava `id_externo` do provedor quando
houver. Retries reutilizam o mesmo `id_mensagem` referenciado no `payload` do `trabalho`.

**Rationale**: FR-005 e SC-004 — reprocessamento técnico não pode gerar segundo pedido no
histórico nem segundo disparo ao titular. Separar “tentativa de rede” de “mensagem de
domínio” evita o anti-padrão insert-on-retry.

**Estado `entregue`**: fora desta fatia. Sem webhook de status do provedor, o mínimo
observável é `pendente` → `enviada` | `falha` (Artigo XV / assumption da spec). A coluna e o
`CHECK` já admitem `entregue` para a F1.3+ quando o webhook de status entrar.

---

## 4. Porta `MensageriaGateway` + implementação falsa obrigatória

**Decisão**:

- Interface em `app/portas/mensageria.py` (Protocol): método de envio da coleta tipado
  (destinatário canônico, primeiro nome, texto/corpo ou nome de template + variáveis,
  metadados sem PII extra).
- `app/adaptadores/mensageria_falsa.py`: registra envios em memória; pode ser configurada
  para falhar — base de todos os testes (SC-008 / Artigo X).
- Adaptador WhatsApp Cloud (`mensageria_whatsapp.py`): implementação real mínima (template
  Utility), ligada só quando a configuração do ambiente pedir. **Não** é exercitada pela
  suíte. Número de teste da Meta e limite de destinatários são restrição de implantação.

O worker recebe a porta por injeção (composição em `worker` / bootstrap de processo), nunca
importando o adaptador concreto a partir do domínio.

**Rationale**: constituição Artigo X e restrição explícita do specify. Sem a porta, o primeiro
envio vira acoplamento permanente à Meta e inviabiliza o simulador da apresentação.

**Alternativas consideradas**:

- **Só adaptador real “desligado” nos testes com mock de HTTP**: ainda acopla URL/SDK e
  estimula atalho de chamar a Meta “só desta vez”. Rejeitado.
- **Adiar a interface e chamar `httpx` no worker**: economiza um arquivo, custa o Artigo X na
  primeira fatia que o exercita. Rejeitado.

---

## 5. Fronteiras de módulo: `conversa` nasce; `hospedagem` só dispara

**Decisão**:

| Módulo / pasta | Responsabilidade nesta fatia |
| --- | --- |
| `hospedagem` | Após inserir reserva+titular, chama o serviço de conversa para agendar a coleta **na mesma transação**; continua dono de `reserva` / `hospede` / `reserva_hospede` |
| `conversa` | Monta o texto da coleta, grava `mensagem`, pede enfileiramento; atualiza `status_envio` quando o worker conclui |
| `app/fila` | Persistência e claim de `trabalho` (sem regra de texto de mensagem) |
| `worker` | Loop de consumo; orquestra fila + conversa + `MensageriaGateway` |
| `acesso` / `propriedade` | Sem mudança de matriz; `propriedade`/bootstrap ganha parâmetros novos |

`conversa` **não** importa router de hospedagem. `hospedagem` **não** escreve SQL em
`mensagem` nem em `trabalho` — chama serviços/funções de fronteira.

**Rationale**: `AGENTS.md` já atribui `mensagem` a `conversa`. Colocar INSERT de mensagem
dentro de `hospedagem.repository` criaria o segundo ciclo de fronteira furada (o primeiro foi
registrado na F0.3). Nascer o módulo agora, mínimo, é mais barato que migrar depois.

---

## 6. Texto da coleta, privacidade e contato do responsável

**Decisão**:

- Função pura monta o corpo com: saudação só com **primeiro token** de `nome_completo`; lista
  numerada dos nove campos da ficha (Artefato 1 §3.1); frase de opcionalidade / evitar espera;
  finalidade; contato do responsável.
- Contato vem de `parametro_hotel` chave `contato_responsavel_dados`, por hotel. Bootstrap
  grava valor inicial = telefone do hotel criado (canal já existente) — não um e-mail genérico
  “omnistay@…”.
- Conteúdo completo fica em `mensagem.conteudo` (histórico). Logs só com `id_reserva`,
  `id_mensagem`, `id_trabalho`, status e código de erro.

**Rationale**: FR-007–FR-011 e aviso LGPD da jornada §9.3c. Telefone do hotel como default
evita inventar DPO fictício e usa dado que o bootstrap já pede.

**Alternativas consideradas**:

- **Template só com variáveis na Meta, sem gravar texto**: o histórico e os testes de
  privacidade ficam cegos; a porta falsa precisaria reconstituir o texto. Gravar o corpo
  renderizado no banco atende FR-006 e os unitários de conteúdo.
- **Hardcodar contato no código**: Artigo XIII / multi-propriedade.

---

## 7. Status de entrega na fila do dia

**Decisão**: ampliar `vw_fila_do_dia` com coluna `status_envio_coleta` — `status_envio` da
mensagem de saída de coleta da reserva (a única desta fatia). Migração `DROP` + `CREATE` da
visão (mesmo padrão `0003`/`0004`). Contrato `GET /fila-do-dia` ganha o campo; `null` só se
não houver mensagem (não deve ocorrer para reservas criadas após esta fatia).

**Rationale**: FR-012 / SC-003 — a recepção vê a falha sem sair da fila. Não inventar segundo
vocabulário além de `pendente|enviada|entregue|falha`.

---

## 8. Tentativas, backoff e reclaim

**Decisão**:

- `parametro_hotel.tentativas_max_envio_mensagem` (default `"5"`) — Artigo XIII.
- Backoff técnico crescente entre tentativas (implementação na fila; sem PII no erro).
- Ao marcar `processando`, preencher `processando_desde`. Worker (ou claim) devolve a
  `pendente` trabalhos `processando` com bloqueio expirado — cobre queda do processo
  (Artefato 5 §8.3).

Esgotadas as tentativas: `trabalho.status = 'falha'`, `mensagem.status_envio = 'falha'`;
reserva **intacta**.

---

## 9. Superfície desta fatia: API + worker, sem tela React, sem webhook de entrada

**Decisão**: comportamento observável por (1) `POST /reservas` + `GET /fila-do-dia` já
existentes, com campo novo de status; (2) worker acionável nos testes de integração (uma
passagem de consumo, não precisa de daemon eterno na suíte); (3) porta falsa. Sem React. Sem
receber resposta do hóspede. Sem lembrete por silêncio.

**Rationale**: mesmo padrão da F1.1; F1.3/F1.4 são fatias seguintes. Artigo XV: declarar o
recorte.

---

## 10. Divergências documentais encontradas

| Onde | O que está escrito | O que esta fatia faz | Correção |
| --- | --- | --- | --- |
| Artefato 5 §8.1 | Fila no PostgreSQL com campos de controle | Tabela `trabalho` ainda **não** existe no `04-schema.sql` | Migração + DDL no documento na mesma entrega |
| Spec F1.1 / contrato 004 | “Não envia mensagem ao hóspede” | F1.2 passa a enfileirar e enviar | Contrato 005 atualiza a fila; o 004 permanece histórico daquela fatia |
| `vw_fila_do_dia` | Sem status de envio | Coluna `status_envio_coleta` | Migração da visão + `04-schema.sql` |
| Bootstrap / `parametro_hotel` | Só durações de sessão | Passa a semear `contato_responsavel_dados` e `tentativas_max_envio_mensagem` | Código de bootstrap + comentário no schema |
| Artefato 2 R2 | Cadastro “dispara o template” | Agora sim, via fila | Alinhamento processo ↔ fatia |
| Modelo / conversa | Módulo `conversa` previsto, inexistente no código | Módulo mínimo nasce | Sem alterar dono de `mensagem` |

---

## 11. O que fica propositalmente de fora

- Interpretação da resposta / `ficha_completa` / mudança de status da reserva (F1.3)
- Lembrete único por silêncio e `reenvio_realizado` (F1.4)
- Webhook de mensagem recebida e webhook de status `entregue`
- Tela React / login no painel
- Aprovação do template na Meta como passo de CI (é pré-requisito de ambiente real, não da
  suíte)
- Agendador APScheduler completo (só o consumidor da fila nesta fatia)
