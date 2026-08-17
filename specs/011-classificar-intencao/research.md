# Pesquisa — F3.2 Classificar a Intenção

Decisões técnicas tomadas antes de escrever teste. Cada uma traz o que foi escolhido, por
quê, e o que foi recusado. Nada aqui é preferência estética: tudo tem consequência em teste
ou em risco operacional.

---

## 1. Allowlist e ramo no mesmo passo; inverter os testes da F3.1

**Decisão:** `reclamar_proximo` passa a incluir `classificar_mensagem` na allowlist **e**
o consumidor ganha o ramo `processar_trabalho_classificar_mensagem` no mesmo commit. Os
testes da F3.1 que afirmam o contrário são atualizados nesta fatia, não deixados verdes.

Inventário conhecido:

| Teste atual (F3.1) | Destino nesta fatia |
| --- | --- |
| `test_reclamar_proximo_nao_consome_classificar_mensagem` | Reclama `classificar_mensagem` (pode coexistir com outros tipos) |
| `test_fila_so_com_classificar_mensagem_nao_devolve_claim` | Devolve o claim desse tipo |
| `test_worker_nao_consome_classificar_mensagem` | Worker classifica e marca `concluido` |

**Rationale:** a F3.1 filtrou o claim de propósito — o `else` `tipo_desconhecido` → `falha`
destruiria o gancho. A spec desta fatia é exatamente consumir esse gancho. Deixar um dos
dois lados (allowlist sem ramo, ou ramo sem allowlist) reproduz o defeito que a F3.1
evitou.

**Alternativas recusadas:** ramo no-op que recolocava em `pendente` — loop; worker
separado só para classificar — Artigo XI; manter os testes da F3.1 e criar outros com
nomes novos sem apagar a afirmação antiga — suíte contraditória.

---

## 2. `LLMProvider.classificar`; taxonomia valida no domínio

**Decisão:** a porta ganha um segundo método, ao lado de `extrair_ficha` (F1.3). O domínio
não confia no modelo: valida intenção, sentimento e urgência **depois** da porta, em
função pura do módulo `conversa`.

```text
classificar(texto) -> ResultadoClassificacao
  intencao, sentimento, urgencia  # podem vir vazios ou fora da lista
  bruto                           # dict da resposta completa, para auditoria
```

Indisponibilidade / recusa / tempo esgotado: a porta levanta `FalhaDeClassificacao`
(código sem texto da mensagem). Isso **não** reusa `FalhaDeExtracao` — o tratamento é
outro (escala na hora; a ficha ainda retenta).

Conjuntos fechados (iguais ao `CHECK` de `mensagem`):

| Eixo | Valores |
| --- | --- |
| Intenção | `duvida_geral`, `pedido_de_servico`, `reclamacao_tecnica`, `upsell`, `solicitacao_de_checkout`, `fora_de_escopo` |
| Sentimento | `positivo`, `neutro`, `negativo` |
| Urgência | `baixa`, `media`, `alta` |

Falta de eixo, valor fora da lista ou bruto inutilizável → desfecho `formato_invalido`
(User Story 3). Não existe “classificação parcial”.

**Rationale:** Artigo X (porta trocável, teste sem rede); Artefato 5 §10.1 (classificação
é chamada curta e estruturada, distinta da conversação); FR-002, FR-003, FR-016.

**Alternativas recusadas:** reusar `extrair_ficha` com desfecho inventado — mistura ficha
e estadia; validar taxonomia no adaptador — o domínio deixaria de ser a fonte da regra;
sétimo valor de intenção — a spec e o CHECK já fecharam a lista.

---

## 3. Primeira falha escala; trabalho `concluido`, sem retentativa de classificador

**Decisão:** `FalhaDeClassificacao` e `formato_invalido` gravam o desfecho humano na
mensagem e marcam o trabalho **`concluido`**. Não há `reagendar` contra o classificador.
Não se usa `status = falha` nesse caminho — `falha` convidaria nova passagem a insistir
no LLM.

Se o `UPDATE` da mensagem falhar, a transação desfaz e o reclaim por expiração devolve o
item a `pendente` (FR-017). Isso já existe na fila; não se inventa mecanismo novo.

**Rationale:** FR-006, FR-007, FR-012. A spec recusa “limbo de retentativas enquanto
ninguém olha”. A ficha (F1.3) ainda retenta porque o hóspede da pré-chegada não está
esperando atendimento da estadia; aqui a regra é Artigo II na primeira ocorrência.

**Alternativas recusadas:** copiar o backoff de `interpretar_ficha` — contradiz FR-012;
marcar `falha` e olhar a fila de trabalhos no painel — a spec pede visibilidade **na
recepção**, na superfície que ela já usa, não na tabela `trabalho`.

---

## 4. Desfecho em `classificacao_bruta`; sinal na fila do dia

**Decisão:** nenhuma coluna nova em `mensagem`. Os três eixos já existem. O JSON
`classificacao_bruta` desta fatia usa `tipo = classificacao_intencao` e um `desfecho`:

| `desfecho` | Eixos estruturados | Bruto do classificador | Sinal humano |
| --- | --- | --- | --- |
| `classificado` | preenchidos (`duvida_geral` / `pedido_de_servico` / `reclamacao_tecnica`) | sim | não |
| `encaminhado_humano` | preenchidos (`upsell` / `solicitacao_de_checkout` / `fora_de_escopo`) | sim | sim |
| `formato_invalido` | permanecem `NULL` | sim (o que veio) | sim |
| `indisponivel` | permanecem `NULL` | ausente | sim |

`conteudo` da mensagem **nunca** entra no `UPDATE` (FR-005). O JSON **não** copia o
texto do hóspede; só o que o classificador devolveu.

Visibilidade (FR-008): coluna derivada **`precisa_atendimento_humano`** em
`vw_fila_do_dia` — verdadeira quando a reserva está `hospedado` e existe mensagem
`recebida` com `tipo = classificacao_intencao` e `desfecho` ∈ (`encaminhado_humano`,
`formato_invalido`, `indisponivel`). `GET /fila-do-dia` (já `ler_fila_do_dia`, só
recepção) passa a devolver o booleano.

Não se reusa `estado_cadastro = leitura_humana`: esse valor é da ficha em
`aguardando_cadastro`. Misturar cadastro com conversa da estadia tornaria a coluna
mentirosa para quem já fez check-in.

**Rationale:** FR-008, FR-010, Artigo IV (a fila do painel é a verdade, não uma
notificação). Padrão das colunas `chegada_nao_confirmada` e `boas_vindas_nao_enviadas`.

**Alternativas recusadas:** abrir `solicitacao` nesta fatia — é o chamado da F3.5, com
confirmação e janela; flag só em memória — some na queda; `GET` novo de histórico —
Artigo XI e fora do critério de pronto, como na F3.1.

---

## 5. Ramo automático não executa; intenção sem fatia posterior já vai a humano

**Decisão:**

- `duvida_geral`, `pedido_de_servico`, `reclamacao_tecnica`: grava eixos +
  `desfecho = classificado`. Zero envio, zero `solicitacao`, zero leitura de catálogo.
- `upsell`, `solicitacao_de_checkout`, `fora_de_escopo`: grava eixos +
  `desfecho = encaminhado_humano` (senão a mensagem fica classificada e invisível —
  não há F3.x para esses três).

**Rationale:** FR-009, FR-010, User Story 4. O propósito desta fatia é decidir, não
tramitar.

**Alternativa recusada:** deixar os três “sem ramo” só classificados — violaria Artigo
II e a própria spec.

---

## 6. Idempotência: já classificada não chama o LLM de novo

**Decisão:** se `classificacao_bruta->>'tipo'` já é `classificacao_intencao` com
`desfecho` preenchido, o worker **não** chama a porta, **não** altera eixos e marca o
trabalho `concluido`. Cobre reclaim após crash entre gravar e concluir, e segundo
claim acidental.

**Rationale:** FR-013. O índice único do trabalho já impede dois itens; este guard é o
efeito observável na mensagem.

**Alternativa recusada:** classificar de novo “para corrigir” — a spec não pede
reclassificação; um segundo encaminhamento humano duplicaria o sinal sem novo fato.

---

## 7. `LLMFalso` ganha classificação sem quebrar a ficha

**Decisão:** o falso já usado na F1.3 ganha `classificar` e configuração **separada**
(`configurar_classificacao` / `falhar_classificacao`). `extrair_ficha` permanece
idêntico. Nenhum teste instancia adaptador real de provedor.

Padrão ausente de configuração de classificação: devolve um resultado **válido**
`duvida_geral` / `neutro` / `baixa` (o caminho feliz mínimo). Testes de falha e de
outras intenções configuram explicitamente. Testes de formato inválido devolvem eixos
fora da lista ou incompletos, com `bruto` preenchido.

**Rationale:** FR-016; o default evita que uma passagem do worker após o webhook de
estadia caia em humano por acidente de configuração.

**Alternativa recusada:** segundo falso só para classificar — duas portas falsas para a
mesma interface.

---

## 8. Migração `0010_classificar_intencao`: só a visão

**Decisão:** SQL congelado em `alembic/versions/sql/0010_classificar_intencao.sql`:
`DROP` + `CREATE` de `vw_fila_do_dia` com `precisa_atendimento_humano`. Sem tabela nova,
sem coluna nova em `mensagem`, sem mudar `ck_trabalho_tipo` (já tem o tipo desde a
`0009`). `downgrade` restaura a visão da `0008`/`0009` (são a mesma visão). Atualizar
`docs/04-schema.sql` no mesmo passo. Teste de conformidade nos dois sentidos.

**Rationale:** o domínio de classificação já mora no esquema inicial. O que falta é o
sinal visível (Artigo V / FR-008).

**Alternativa recusada:** coluna persistida `precisa_atendimento_humano` em `reserva` —
desnormaliza um fato que já está nas mensagens e exigiria UPDATE em todo desfecho.

---

## 9. Módulo `conversa` classifica; `hospedagem` só projeta a fila

**Decisão:** `processar_trabalho_classificar_mensagem` vive em `conversa` (dona de
`mensagem`). O worker orquestra o claim e chama esse serviço, **sem** `hospedagem` no
ramo — não muda status de reserva e não consolida ficha. `hospedagem` apenas acrescenta
o booleano em `ItemFilaDoDia` / `ler_fila_do_dia`, lendo a visão.

`UPDATE` da mensagem sempre no contexto de `id_hotel` do trabalho (via `reserva` da
mensagem). Hotel B não vê sinal nem eixos do hotel A.

**Rationale:** fronteira já usada na F1.3 (conversa grava `classificacao_bruta`;
hospedagem expõe `estado_cadastro`). Artigo XIV.

**Alternativa recusada:** módulo `atendimento` nesta fatia — não há `solicitacao`.

---

## 10. HTTP: zero rota nova; webhook intocado

**Decisão:** o `POST /webhook` permanece o da F3.1 (grava e enfileira). Classificar é
só worker. Não nasce `GET` de histórico. A recepção vê o sinal em `GET /fila-do-dia`.
A suíte confirma eixos e `classificacao_bruta` no banco, como o histórico da F3.1.

**Rationale:** Artigo XI; critério de pronto da spec (superfície já existente).

---

## 11. Log: identificadores e intenção; nunca texto nem bruto

**Decisão:** eventos `mensagem_classificada` (com `intencao` quando houver),
`classificacao_indisponivel`, `classificacao_formato_invalido`. Campos: `id_trabalho`,
`id_mensagem`, `id_reserva`, `id_hotel`, `desfecho`, `intencao` (só no sucesso
estruturado). Ausentes: `conteudo`, telefone, `bruto`, payload do LLM.

**Rationale:** FR-011, Artigo VIII. Intenção resultante é o que a constituição já
autoriza no log.

---

## 12. O que esta pesquisa não reabre

- Assinatura HMAC / falha fechada do webhook (F3.1).
- Caminho `interpretar_ficha` e retentativa da extração.
- Máquina de estados da reserva e trigger de transição.
- `CatalogoRepository` e `MensageriaGateway` neste tipo de trabalho.
- Tabela `solicitacao` / Alert Center (F3.3–F3.5).
- Adaptador real de provedor de IA na suíte.
- Ordem estrita entre mensagens (Artigo XV).
- Simulador visual (F6.2).
