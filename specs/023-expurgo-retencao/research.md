# Fase 0 — Pesquisa e decisões técnicas: Expurgo por Retenção

Cada seção registra a decisão, por que ela foi tomada e o que foi recusado.
Divergências documentais estão na seção 10.

---

## 1. Varredura no agendador existente; sem fila e sem APScheduler

**Decisão**: `verificar_retencao` em `worker/agendador.py`, relógio
injetável (`agora`), flag `--verificar-retencao`. No modo contínuo, a
passagem horária que já chama cadastros, boas-vindas, pulsos e mercado
passa a chamar a retenção também. `--uma-passagem` **não** dispara a
varredura (igual às anteriores).

A função **executa** o tratamento no banco. Não enfileira tipo novo em
`trabalho`. Não há I/O de rede.

Efetividade **diária**: se o hotel já tem `execucao_retencao` no mesmo
dia civil UTC de `agora`, a passagem no-opa aquele hotel. O UNIQUE do
dia no banco é a garantia contra duas passagens simultâneas.

**Rationale**: F1.4–F5.2 já recusaram APScheduler (Artigo XI). O Artefato 5
nomeia a lib e “expurgo diário”; o Artigo XI vence, e a cadência horária
já existe. Fila (Artigo III) justifica-se quando há rede ou IA **depois**
de gravar a intenção. Aqui o trabalho *é* o SQL. Enfileirar um
`expurgar_por_retencao` por hotel seria peça móvel sem problema presente.

**Alternativas consideradas**:

- **APScheduler só para retenção**: quinta peça sem problema que a flag
  não resolva. Rejeitado.
- **Tipo `expurgar_retencao` na fila**: simetria com mercado, mas mercado
  tem visita HTTP. Rejeitado.
- **Disparar retenção dentro de `--uma-passagem`**: mistura consumidor de
  trabalhos com calendário. Rejeitado.
- **Comprovante a cada hora**: ~8 mil linhas/hotel/ano para demonstrar o
  mesmo cumprimento. A spec pede cada *execução*; a arquitetura pede
  diária. Uma execução por dia civil UTC atende os dois.

---

## 2. Orquestração no agendador; SQL em cada módulo dono

**Decisão**: o agendador lê os prazos (via `propriedade.repository`,
padrão já usado) e chama, por hotel:

| Dono | Função | Tabelas |
| --- | --- | --- |
| `conversa` | anonimizar conteúdo livre da estadia | `mensagem`, `evento_webhook` |
| `atendimento` | anonimizar descrição | `solicitacao` |
| `feedback` | anonimizar comentário | `avaliacao` |
| `hospedagem` | apagar ficha vencida | `hospede`, `consentimento`, `reserva_hospede`, `reserva.telefone_contato` |
| `propriedade` | gravar/listar comprovante | `execucao_retencao` |

Nenhum módulo escreve tabela de outro. `mercado` e `acesso` não entram.

Se o prazo de conteúdo livre estiver ausente/inválido, o agendador **não**
chama conversa/atendimento/feedback naquele hotel e registra
`prazo_conteudo_ausente`. O prazo de ficha, se válido, continua na mesma
passagem — e o inverso.

**Rationale**: fronteira de módulo + lição da F0.3 (orquestração não mora
num dos módulos). Artigo XIV: cada UPDATE/DELETE filtra pelo hotel da
reserva ou da execução.

**Alternativas consideradas**:

- **Módulo `retencao` novo**: um dono só, mas nasceria o sexto módulo para
  orquestrar o que o agendador já faz. Artigo XI.
- **Todo o SQL no agendador**: o agendador passaria a conhecer esquema de
  quatro módulos. Rejeitado.
- **`propriedade` chamar os outros serviços**: ciclo de import. Rejeitado.

---

## 3. Relógio = `checkout_em`; vencimento em intervalo civil

**Decisão**: elegível a conteúdo livre se `reserva.checkout_em IS NOT NULL`
**e** `checkout_em + make_interval(months => N) <= agora`, com `N` lido de
`meses_retencao_conteudo_livre`. Data prevista **nunca** entra no predicado.

Ficha: hóspede com ao menos uma reserva **deste** hotel, considerando
**todas** as reservas vinculadas (qualquer hotel): nenhuma com
`checkout_em` nulo, e `MAX(checkout_em) + make_interval(years => A) <= agora`.

Função pura em `app/comum/retencao.py` replica o vencimento com `calendar`
(fim de mês: 31 jan + 1 mês → 28/29 fev) para unitário sem banco. A
passagem real usa o SQL. Sem `python-dateutil`.

**Rationale**: spec FR-002/FR-010/FR-013 + Artigo I. `MAX` ignora NULL no
PostgreSQL — sem `BOOL_AND(checkout_em IS NOT NULL)` um hóspede ainda
hospedado seria apagado pela estadia velha. Multi-tenant: apagar a ficha
no hotel A não pode destruir quem ainda tem estadia recente no hotel B
(hoje cada reserva cria hóspede novo, mas a regra da spec é a última
vinculada).

**Alternativas consideradas**:

- **365 dias / 1825 dias**: barato, mas a política pública fala em meses e
  anos civis. Rejeitado.
- **`timedelta(days=30*N)` no Python e filtrar em memória**: carrega
  conteúdo (que o log não pode ecoar) e arredonda o prazo. Rejeitado.
- **Usar `data_checkout_prevista` quando `checkout_em` falta**: inventa a
  partida. Rejeitado (Artigo I e XV).

---

## 4. Marca de anonimização, não DELETE da linha operacional

**Decisão**: constantes em `app/comum/retencao.py`:

| Alvo | Marca | Como detectar “já tratado” |
| --- | --- | --- |
| `mensagem.conteudo` | texto `[anonimizado]` | `IS DISTINCT FROM` a marca (NOT NULL; vazio `''` também recebe marca — não há mensagem sem texto) |
| `solicitacao.descricao` | texto `[anonimizado]` | só se havia texto (`btrim(descricao) <> ''`) e distinto da marca |
| `avaliacao.comentario` | texto `[anonimizado]` | só se havia texto (`IS NOT NULL` e `btrim <> ''`) |
| `evento_webhook.payload` | jsonb `{"anonimizado": true}` | `IS DISTINCT FROM` a marca |
| `mensagem.classificacao_bruta` | `NULL` | `IS NOT NULL` no momento do UPDATE |
| comentário/descrição originalmente vazios | não toca | vazio continua vazio (FR-009) |

Toda `mensagem` da reserva elegível entra, **incluindo as enviadas pelo hotel**.
A FR-003 não filtra por `direcao`. Volume de atendimento conta as duas mãos.

`evento_webhook.id_externo` permanece (UNIQUE de idempotência do webhook).
Eixos `intencao`, `sentimento`, `urgencia`, nota, tipo, status, valores de
consumo **não** mudam.

Payload ligado à estadia: `evento_webhook.id_externo = mensagem.id_externo`
das mensagens da reserva elegível. Sem FK nova nesta fatia (Artigo XI).

**Rationale**: spec FR-003–FR-009 + arquitetura §9.1. Apagar a linha
destruiria volume. `NULL` em `conteudo` é impossível (`NOT NULL`). Marca
explícita distingue “nunca teve comentário/descrição” de “tinha e saiu”
(FR-009). Idempotência é o `WHERE` que exclui a marca — segunda passagem
conta 0.

**Alternativas consideradas**:

- **DELETE das mensagens**: viola volume (FR-008). Rejeitado.
- **Esvaziar para `''`**: colide com comentário que nunca existiu vs. texto
  retirado; `conteudo` vazio ainda seria uma string. Marca é observável.
- **Coluna `anonimizado_em`**: honesta, mas a spec não pede campo novo nas
  linhas operacionais; a marca no próprio conteúdo basta. Artigo XI.
- **FK `id_reserva` em `evento_webhook`**: correto a longo prazo; fora do
  recorte. JOIN pelo `id_externo` já usado na gravação do webhook.

---

## 5. Exclusão da ficha: ordem e telefone da reserva

**Decisão**: para cada hóspede elegível, na mesma transação da passagem:

1. `DELETE consentimento` daquele `id_hospede`
2. `DELETE reserva_hospede` daquele `id_hospede`
3. `DELETE hospede`
4. `UPDATE reserva.telefone_contato` para a marca de telefone
   `anonimizado` **somente** se a reserva ficou sem nenhum `reserva_hospede`
   restante

A reserva (datas, status, `checkin_em`, `checkout_em`) permanece. Não há
coluna `nome` em `reserva`.

A marca `anonimizado` cabe em `VARCHAR(20)`, **não** passa em
`app/comum/telefone.py` (não é canônico `55…`), então o webhook não
casa essa reserva com um hóspede vivo.

**Rationale**: spec FR-010–FR-012. Consentimento tem FK para hóspede;
deixar a linha órfã identificável viola FR-011. Telefone de contato na
reserva é DP copiado antes da ficha (comentário do esquema); se ficar,
a pessoa continua identificável depois da exclusão.

**Alternativas consideradas**:

- **Anonimizar a ficha em vez de apagar**: a política pública e o
  dicionário dizem apagar DP/DPS aos cinco anos. Rejeitado.
- **Apagar a reserva**: destruiria volume de estadias e chamados já
  anonimizados. Rejeitado.
- **Anular `telefone_contato`**: a coluna é `NOT NULL`. Marca textual.
- **Apagar telefone mesmo com acompanhante restante**: no MVP cada reserva
  cria hóspede novo; a guarda “só se não restar vínculo” cobre o caso da
  spec de N hóspedes sem cegar o que ainda existe.

---

## 6. Prazos na configuração; semente 12 e 5; ausência falha alto

**Decisão**:

| Chave | Unidade | Semente | Predicado |
| --- | --- | --- | --- |
| `meses_retencao_conteudo_livre` | inteiro ≥ 1 | `12` | `make_interval(months => N)` |
| `anos_retencao_ficha` | inteiro ≥ 1 | `5` | `make_interval(years => A)` |

Bootstrap e revisão `0021` semeiam (idempotente, padrão das chaves
anteriores). Ausência, vazio, zero, negativo ou não numérico: aquele
**tipo** não é tratado naquele hotel; log
`prazo_conteudo_ausente` / `prazo_ficha_ausente`; nenhum default no
verificador. O comprovante do dia ainda nasce, com as flags de prazo
ausente e quantidades zero daquele tipo.

Não há tela para editar as chaves. Não nasce
`alterar_parametro_hotel` genérico (já recusado na F2.2).

**Rationale**: Artigo XIII + spec FR-015. Unidades seguem a linguagem
pública (meses / anos), não forçam hora como as chaves de silêncio.

**Alternativas consideradas**:

- **Tudo em horas** (`8760`, `43800`): ilegível e falso em ano bissexto.
  Rejeitado.
- **Default 12/5 no código quando a chave falta**: o pulso e o mercado
  recusam; a spec também. Rejeitado.
- **Uma chave só**: os dois relógios são independentes (um pode faltar).

---

## 7. Comprovante durável; GET só da gestão; sem POST

**Decisão**: tabela `execucao_retencao` (ver [data-model.md](./data-model.md)).
Cada passagem que efetivamente roda o hotel no dia **insere** uma linha,
mesmo com todas as quantidades zero.

`GET /retencao` — cookie de sessão, hotel da sessão, operação
`ler_retencao` só `gestor`. Lista da propriedade, mais recente primeiro.
Sem `id_hotel` no JSON. Escrita HTTP inexistente → `405`. Sem flag
“expurgar agora”.

Não reutilizar `ler_indicadores` (a recepção lê contagem de chegadas).

**Rationale**: spec FR-001/FR-016/FR-017. Log rotativo não sobrevive à
banca. Artigo IV: o comprovante é recuperável pela leitura do painel
(aqui, a consulta autenticada). Artigo XV: não é auditoria genérica de
qualquer UPDATE.

**Alternativas consideradas**:

- **Só `logger.info`**: some com o processo; a spec pede demonstrar.
  Rejeitado.
- **Reusar `ler_indicadores`**: abriria o comprovante à recepção.
- **POST `/retencao`**: o botão que a spec recusa.

---

## 8. Log só com identificadores, quantidades e desfecho

**Decisão**: `logger.info` com `id_hotel`, quantidades por tipo, flags de
prazo ausente, desfecho `retencao_aplicada` / `retencao_ja_executada_hoje`.
Sem conteúdo de mensagem, sem comentário, sem payload, sem nome, sem
telefone, sem documento, sem marca concatenada a texto original.

Teste estende o padrão `test_log_sem_conteudo`.

**Rationale**: Artigo VIII e spec FR-020.

---

## 9. Sem porta nova, sem React, sem tipo na fila

**Decisão**: domínio só fala com SQL e com o relógio. Worker não autentica
perfil. A suíte não precisa de `MensageriaGateway` nem de `LLMProvider`
nesta fatia.

**Rationale**: Artigo X (portas são para I/O trocável) + Artigo XI.

---

## 10. Divergências documentais

| Onde | O que está escrito | O que esta fatia faz |
| --- | --- | --- |
| Artefato 5 §9 | `APScheduler`; `expurgar_por_retencao` diária | Sem a lib; flag + passagem horária com UNIQUE do dia. Já divergido desde a F1.4; registrar no estado |
| Artefato 5 §9.1 | lista `mensagem.conteudo`, `evento_webhook.payload`, `avaliacao.comentario`, ficha | Acrescenta `solicitacao.descricao` e `classificacao_bruta` porque o dicionário (DPC / eco do texto) já os classificou. A spec vence a tabela resumida. Registrar no estado |
| `evento_webhook` no esquema | sem FK de reserva | JOIN por `id_externo`; payload órfão fora. Não silenciar |
| Constituição Artigo XV | sem auditoria genérica de alteração | Comprovante **específico** da retenção (quantidades + instante). Não abre trilha de qualquer campo |
| Comentário de `parametro_hotel` | não cita as duas chaves novas | `0021` + documento vivo fecham |
| Pendência Artefato 4 item 4 | “rotina de expurgo não está no DDL” | Continua verdade: a rotina é a passagem, não um trigger. A **tabela de comprovante** entra no DDL. A pendência de *cumprir* o prazo fecha nesta fatia |

Clarify não rodou. Planejamento usou a spec (clique de saída, marca que
preserva volume, comprovante consultável, prazos na propriedade, sem
disparo manual).
