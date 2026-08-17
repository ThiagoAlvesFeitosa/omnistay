---
description: "Task list for feature implementation"
---

# Tasks: Receber Mensagem com Segurança

**Input**: Design documents from `/specs/010-receber-mensagem/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de produção antes
de um teste que falhe pela ausência dela, e pelo motivo certo.

**Organization**: Tarefas agrupadas por história (US1–US5), na ordem da spec. A allowlist do
claim entra na fase Foundational — sem ela a US1 criaria trabalho que a primeira passagem
do worker marcaria `falha`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US5)

## Como ver os testes falharem nesta fatia

**Esquema.** `testes/integracao/test_conformidade_do_esquema.py` compara o banco migrado com
`docs/04-schema.sql`. Editar o documento **antes** da revisão deixa a conformidade vermelha
apontando o delta. A revisão `0009` a devolve ao verde.

**Garantias.** `testes/integracao/test_garantias_do_banco.py` com
`OMNISTAY_SEM_MIGRACAO=1` prova que tipo e índice falham sem a migração.

**Serviços.** Unitários com repositório falso falham por `AttributeError` até
`resolver_reserva_hospedada` e o ramo de estadia existirem.

**Borda HTTP.** Sem segredo, o `POST /webhook` hoje aceita o corpo. O teste de falha
fechada fica vermelho até o router recusar.

**Claim.** Sem allowlist, `reclamar_proximo` pega `classificar_mensagem` e o consumidor
marca `tipo_desconhecido`. O teste da US4 / Foundational falha até o filtro existir.

---

## Phase 1: Setup

**Purpose**: helper de envelope assinado para as integrações desta fatia, sem copiar HMAC
em cada arquivo

- [X] T001 [P] Criar `testes/suporte/webhook.py` com `assinar(corpo, segredo) -> str`
      (`sha256=` + HMAC-SHA256) e `postar_webhook(cliente, payload, *, segredo, cabecalho=
      "X-Omnistay-Signature")` que posta JSON em `/webhook`. Sem valor secreto versionado.
      Os testes da F1.3 em `testes/integracao/test_webhook_coleta.py` podem continuar com o
      helper local — não refatorar nesta tarefa
- [X] T002 [P] Em `.env.example`, na chave `WHATSAPP_APP_SECRET`, anotar que o `POST
      /webhook` recusa (`401`) se a variável estiver vazia — falha fechada da F3.1. Sem
      gravar segredo

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: revisão `0009` (tipo + unicidade), fila que enfileira sem consumir, allowlist
do claim. Nenhuma história de estadia começa antes.

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. Ordem do esquema: T003 → T004 →
T006 → T007 (teste vermelho no documento, depois migração verde).

- [X] T003 Estender `testes/integracao/test_garantias_do_banco.py`: `INSERT` de trabalho
      `classificar_mensagem` aceito pelo `ck_trabalho_tipo`; segundo `INSERT` com o mesmo
      `id_mensagem` no payload recusado por `uq_trabalho_classificar_mensagem_mensagem`.
      Rodar e **ver falhar** (FR-018, Artigo IX)
- [X] T004 Aplicar o delta em `docs/04-schema.sql`: `classificar_mensagem` no
      `ck_trabalho_tipo` e índice `uq_trabalho_classificar_mensagem_mensagem` exatamente
      como em [data-model.md](./data-model.md). Rodar
      `testes/integracao/test_conformidade_do_esquema.py` e **ver falhar** pela divergência
- [X] T005 [P] Alinhar a narrativa de `trabalho` em `docs/04-modelagem-de-dados.md` (o
      webhook de estadia grava `classificar_mensagem` pendente; o worker desta fatia não
      consome) se o parágrafo da fila listar os tipos
- [X] T006 Criar `alembic/versions/sql/0009_receber_mensagem.sql` — cópia congelada do
      delta da T004 (`DROP`/`ADD` do CHECK incluindo os quatro tipos anteriores +
      `classificar_mensagem`; `CREATE UNIQUE INDEX` parcial)
- [X] T007 Criar `alembic/versions/0009_receber_mensagem.py`
      (`down_revision = "0008_confirmar_chegada"`), `upgrade` executa o SQL congelado,
      `downgrade` derruba o índice e restaura o CHECK da `0008`. T003 e T004 verdes
- [X] T008 Unitário em `testes/unitarios/fila/test_claim_nao_consome_classificar.py`:
      inserir um `classificar_mensagem` `pendente` (e, se útil, um `enviar_coleta`
      `pendente` mais novo); `reclamar_proximo` **não** devolve o de classificação; o
      status dele permanece `pendente`. Rodar contra PostgreSQL de teste e **ver falhar**
      (hoje o claim pega qualquer `pendente`). FR-009, [contracts/fila-e-worker.md](./contracts/fila-e-worker.md)
- [X] T009 Em `app/fila/repository.py`, restringir `reclamar_proximo` a
      `enviar_coleta`, `interpretar_ficha`, `enviar_lembrete`, `enviar_boas_vindas`
      (constante `TIPOS_CONSUMIVEIS`). **Não** acrescentar ramo em
      `worker/consumidor.py`. T008 verde
- [X] T010 [P] Acrescentar `TIPO_CLASSIFICAR_MENSAGEM` /
      `enfileirar_classificar_mensagem` em `app/fila/repository.py` (payload
      `{id_reserva, id_mensagem, id_evento}`) e o encaminhamento em
      `app/fila/service.py`. Tratar `IntegrityError` do índice único como “já
      enfileirado” só na camada de serviço de conversa (US1), não aqui

**Checkpoint**: banco admite o tipo; o worker existente não o come; dá para enfileirar.
Nenhum ramo de estadia no webhook ainda.

---

## Phase 3: User Story 1 - Mensagem autêntica da estadia é gravada (Priority: P1) 🎯 MVP

**Goal**: notificação autêntica de texto de reserva `hospedado` vira mensagem no histórico
e um `classificar_mensagem` `pendente`; o provedor já foi respondido; nada classifica nem
envia.

**Independent Test**: reserva hospedada + `POST /webhook` assinado → `200`, 1 mensagem
`recebida`, 1 trabalho `pendente`, status da reserva inalterado, `intencao` nula.

### Tests for User Story 1 ⚠️

- [X] T011 [P] [US1] Estender `testes/unitarios/modulos/conversa/test_receber_mensagem.py`:
      repositório falso com reserva `hospedado` no telefone canônico →
      `receber_evento_entrada` devolve `enfileirado`, grava mensagem e chama
      `enfileirar_estadia` (não `enfileirar` de ficha). Reserva só em
      `aguardando_cadastro` continua no caminho antigo. **Ver falhar** (FR-006, FR-013)
- [X] T012 [US1] Em `testes/unitarios/modulos/conversa/test_receber_mensagem.py`: se
      as duas reservas existirem para o mesmo telefone, prevalece `aguardando_cadastro`
      (ficha). Telefone sem as duas → `sem_reserva`, sem mensagem. Mídia
      `tem_texto_utilizavel=False` → `sem_texto`, sem trabalho de estadia (FR-012, FR-014)
- [X] T013 [US1] Integração `testes/integracao/test_webhook_estadia.py` (helper da T001):
      tornar a reserva `hospedado` (padrão `_tornar` de
      `testes/integracao/test_confirmar_chegada.py`), postar texto assinado → `200` /
      enfileirado; 1 `evento_webhook`; 1 `mensagem` `recebida` com o texto na reserva
      certa; 1 `classificar_mensagem` `pendente`; `reserva.status` continua `hospedado`;
      `intencao`/`sentimento`/`urgencia` nulos; zero mensagem `enviada` nova nesta
      requisição (FR-006, FR-007, FR-016, SC-001, SC-007)
- [X] T014 [US1] Em `testes/integracao/test_webhook_estadia.py`: reserva
      `ficha_recebida` **sem** check-in + texto assinado → só evento, zero mensagem,
      status inalterado (não infere chegada). Isolamento: telefone do hotel A não grava
      no hotel B (FR-011, FR-012)

### Implementation for User Story 1

- [X] T015 [US1] Acrescentar `resolver_reserva_hospedada` em
      `app/modulos/conversa/repository.py` (`id_hotel` + telefone canônico +
      `status = 'hospedado'`, `ORDER BY id_reserva DESC LIMIT 1`). Nos fakes de
      `test_receber_mensagem.py` e `test_log_sem_conteudo.py`, o método novo devolve
      `None` para não quebrar a F1.3
- [X] T016 [US1] Estender `receber_evento_entrada` em
      `app/modulos/conversa/service.py`: após o ramo `aguardando_cadastro` inalterado,
      resolver hospedada e enfileirar via `enfileirar_estadia` (default
      `fila_service.enfileirar_classificar_mensagem`). Sem LLM, sem gateway, sem mudar
      status. Log só com IDs. T011–T014 verdes
- [X] T017 [US1] Em `app/modulos/conversa/schema.py` e no INSERT de mensagem recebida:
      `instante_origem` opcional em `EventoEntrada` vira `mensagem.enviada_em` quando o
      envelope trouxer `timestamp`; senão o default do banco. Router preenche se o JSON
      Meta-like tiver o campo. Sem coluna nova

**Checkpoint**: a conversa da estadia existe no banco; o hóspede ainda não recebe resposta.

---

## Phase 4: User Story 2 - Notificação falsa não entra (Priority: P1)

**Goal**: sem prova, prova inválida ou segredo ausente → `401` e zero efeito. Furo da F1.3
(segredo vazio aceitava qualquer corpo) fecha aqui.

**Independent Test**: três POSTs (sem cabeçalho, HMAC errado, `WHATSAPP_APP_SECRET` vazio)
em reserva hospedada → `401`, zero `mensagem`, zero `trabalho`, zero `evento_webhook`.

### Tests for User Story 2 ⚠️

- [X] T018 [P] [US2] Em `testes/integracao/test_webhook_estadia.py`: POST sem cabeçalho de
      assinatura, com segredo configurado → `401`; contagens de evento/mensagem/trabalho
      inalteradas (FR-003). `test_assinatura_invalida_e_rejeitada` em
      `testes/integracao/test_webhook_coleta.py` já cobre HMAC errado com segredo — não
      duplicar; só garantir o caso **sem cabeçalho** na estadia
- [X] T019 [US2] Em `testes/integracao/test_webhook_estadia.py`: HMAC inválido em
      reserva hospedada → `401` e zero rastro (FR-004)
- [X] T020 [US2] Em `testes/integracao/test_webhook_estadia.py`:
      `WHATSAPP_APP_SECRET` vazio / ausente, envelope qualquer → `401`, nada gravado
      (FR-005). **Ver falhar** — hoje o `if cfg.whatsapp_app_secret` pula a verificação.
      [contracts/webhook-e-entrada.md](./contracts/webhook-e-entrada.md)

### Implementation for User Story 2

- [X] T021 [US2] Em `app/modulos/conversa/router.py`, verificar assinatura **sempre**,
      sobre o corpo cru, **antes** de `json.loads` e de qualquer INSERT: cabeçalho
      ausente, HMAC inválido ou segredo vazio → `401`. Manter
      `hmac.compare_digest` e os dois nomes de cabeçalho. T018–T020 verdes. GET de posse
      inalterado

**Checkpoint**: o endereço público não aceita conversa forjada nem “modo aberto”.

---

## Phase 5: User Story 3 - Reenvio do mesmo evento não duplica (Priority: P1)

**Goal**: o mesmo `id_externo` na estadia confirma de novo e não cria segunda mensagem nem
segundo trabalho.

**Independent Test**: dois POSTs assinados idênticos → uma mensagem, um
`classificar_mensagem`.

### Tests for User Story 3 ⚠️

- [X] T022 [P] [US3] Unitário em `test_receber_mensagem.py`: segundo
      `receber_evento_entrada` com o mesmo `id_externo` em reserva hospedada →
      `duplicado`; uma mensagem; um `enfileirar_estadia` (FR-008)
- [X] T023 [US3] Integração em `test_webhook_estadia.py`: reenvio do mesmo corpo → `200`
      com status de duplicado; `COUNT` de `mensagem` recebida e de
      `classificar_mensagem` inalterado (SC-003)

### Implementation for User Story 3

- [X] T024 [US3] Confirmar que o `ON CONFLICT` de `evento_webhook` já usado na F1.3 cobre
      a estadia (o INSERT de mensagem/trabalho não roda quando `id_evento is None`). Se
      T022/T023 já estiverem verdes após a US1, só fechar os testes — **não** inventar
      segunda conferência em memória

**Checkpoint**: o provedor pode reenviar à vontade; o hóspede aparece uma vez.

---

## Phase 6: User Story 4 - Queda não perde mensagem já aceita (Priority: P1)

**Goal**: depois do webhook, uma passagem do worker (e um “reinício” simulado) deixa o
`classificar_mensagem` `pendente` e a mensagem no histórico.

**Independent Test**: cenário 1 da US1 → `python -m worker --uma-passagem` (ou
`processar_uma_passagem` na suíte) → o trabalho continua `pendente`; log sem
`trabalho_claim` desse tipo.

### Tests for User Story 4 ⚠️

- [X] T025 [P] [US4] Integração em `test_webhook_estadia.py`: após o POST da estadia,
      `processar_uma_passagem` (gateway falso) → `classificar_mensagem` permanece
      `pendente` com o mesmo `id_trabalho`; `interpretar_ficha` / `enviar_boas_vindas`
      pendentes **podem** ser consumidos na mesma passagem se existirem (FR-009, SC-004,
      SC-005)
- [X] T026 [US4] Em `testes/integracao/test_webhook_estadia.py`: o consumidor não marca
      `falha`/`tipo_desconhecido` nesse id. Prova observável da allowlist da T009 no
      fluxo HTTP, não só no INSERT direto

### Implementation for User Story 4

- [X] T027 [US4] Se T025/T026 falharem, corrigir `app/fila/repository.py` (allowlist) ou
      `worker/consumidor.py` **sem** despachar `classificar_mensagem` e sem marcar
      `concluido`. T025 e T026 verdes

**Checkpoint**: a fila durável sobrevive ao worker desta fatia.

---

## Phase 7: User Story 5 - Conteúdo não vaza em log (Priority: P2)

**Goal**: todos os desfechos desta fatia logam identificadores, nunca o texto, o telefone
em claro nem o JSON cru.

**Independent Test**: aceita, recusada, duplicada, sem reserva — o `logger.info` não
contém o texto da fixture.

### Tests for User Story 5 ⚠️

- [X] T028 [P] [US5] Estender `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py`:
      `receber_evento_entrada` no caminho hospedado, `sem_reserva`, `sem_texto` e
      `duplicado` — o texto da mensagem e o telefone não aparecem; há `id_evento` /
      `id_mensagem` / `id_externo` conforme o desfecho (FR-010, SC-006)
- [X] T029 [US5] Integração leve no `test_webhook_estadia.py` (caplog): POST bem-sucedido
      e POST `401` não escrevem o corpo da mensagem no log. Payload de `evento_webhook`
      sem chave de texto (research §10)

### Implementation for User Story 5

- [X] T030 [US5] Ajustar logs e o dict gravado em `evento_webhook` em
      `app/modulos/conversa/service.py` / `router.py` até T028 e T029 verdes. Não logar
      `evento.texto` nem `request.body`

**Checkpoint**: trilha técnica sem cópia da conversa.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: regressão F1.3, envelope de status, documentação, suíte

- [X] T031 [P] Regressão: `testes/integracao/test_webhook_coleta.py` e
      `test_interpretar_ficha.py` continuam verdes com a falha fechada (os fixtures já
      definem `WHATSAPP_APP_SECRET`)
- [X] T032 [P] Em `test_webhook_estadia.py` (ou o router): envelope de **status de
      entrega** (sem `messages`, com `statuses`) → `200`, zero `mensagem` de hóspede.
      JSON irreconhecível continua `400` ([research.md](./research.md) §7)
- [X] T033 [P] `GET /webhook` com token certo/errado — cenário 7 do
      [quickstart.md](./quickstart.md) — em teste de integração se ainda não existir
      (F1.3 pode já cobrir; neste caso só conferir verde)
- [X] T034 Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F3.1 em andamento/concluída,
      revisão `0009`, falha fechada no segredo (divergência da F1.3 fechada), próxima
      fatia **F3.2**. Não apontar F2.3
- [X] T035 Revisar fronteiras: `conversa` não escreve `reserva.status`; SQL de `trabalho`
      só em `app/fila/repository.py`; `worker/consumidor.py` sem ramo
      `classificar_mensagem`; nenhum teste instancia o adaptador WhatsApp real
- [X] T036 Rodar [quickstart.md](./quickstart.md), `pytest testes/unitarios -q` e a
      integração desta fatia (`test_webhook_estadia.py`, `test_webhook_coleta.py`,
      `test_garantias_do_banco.py`, `test_conformidade_do_esquema.py`, o claim da T008).
      Tudo verde, sem rede

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: após Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: após Foundational — MVP
- **US2 (Phase 4)**: após Foundational; pode seguir a US1 (mesmo `router.py`)
- **US3 (Phase 5)**: após US1 (precisa do caminho hospedado)
- **US4 (Phase 6)**: após US1 e T009
- **US5 (Phase 7)**: após US1 (e de preferência US2/US3, para cobrir recusa e duplicado)
- **Polish (Phase 8)**: após as histórias desejadas

### User Story Dependencies

- **US1**: após Phase 2 — sem dependência de outra história
- **US2**: após Phase 2 — independente da US1 no comportamento; mesmo arquivo de router
- **US3**: após US1
- **US4**: após US1 + allowlist (T009)
- **US5**: após os desfechos existirem

### Within Each User Story

1. Testes escritos e **vermelhos pelo motivo certo**
2. Implementação mínima
3. Verde
4. Só então a próxima história

### Parallel Opportunities

- T001 e T002 em paralelo
- T005 em paralelo com T003/T004
- T010 em paralelo com T008/T009 depois de T007
- T011 em paralelo com T013 (arquivos distintos; T012 segue T011 no mesmo unitário)
- T018 → T019 → T020 em série (mesmo `test_webhook_estadia.py`)
- T022 em paralelo com T023 na US3
- T028 em paralelo com T029 na US5
- T031, T032 e T033 em paralelo no polish

**Sequência obrigatória em Foundational**: T003 → T004 → T006 → T007. Ver a conformidade
vermelha entre T004 e T007 é a prova de que ela vigia o documento. T008 só depois de T007
(senão o INSERT falha pelo CHECK, motivo errado).

---

## Parallel Example: User Story 1

```text
# Testes em paralelo (antes da implementação):
T011 test_receber_mensagem.py          (hospedado vs ficha)
T012 test_receber_mensagem.py          (prioridade e mídia) — mesmo arquivo, em série com T011
T014 test_webhook_estadia.py           (sem check-in + isolamento)

# Depois:
T015 resolver_reserva_hospedada
T016 receber_evento_entrada
T017 instante_origem opcional
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: `POST /webhook` de hospedado grava mensagem + trabalho pendente
4. Demo: curl assinado; `SELECT` no banco; worker não classifica

### Incremental Delivery

1. US1 → a estadia entra no histórico
2. US2 → forjado não entra (aceite de segurança da fatia)
3. US3 → reenvio inócuo
4. US4 → worker não apaga a fila
5. US5 → log limpo
6. Polish → F1.3, status, estado do projeto, quickstart

### Suggested MVP scope

**US1** (T001–T017) prova o valor visível. **US2 e US4 são aceite obrigatório** antes de
marcar F3.1 concluída: sem US2 o canal público continua aberto se o segredo faltar; sem
US4 a primeira `--uma-passagem` destrói o gancho da F3.2. US3 provavelmente já nasce da
US1 (`evento_webhook` UNIQUE). US5 é P2 e entra nesta entrega no padrão das fatias
anteriores (Artigo VIII).

---

## Notes

- [P] = arquivos distintos, sem depender de tarefa incompleta da mesma sequência
- Sem React, sem classificação, sem resposta ao hóspede, sem inferência de check-in, sem
  rota GET de histórico, sem ramo novo no consumidor
- `id_hotel` só do canal (`WHATSAPP_ID_HOTEL` / menor hotel, como na F1.3)
- Nenhum teste chama o provedor real nem o LLM para esta fatia
- Commit por tarefa ou grupo lógico **só se o usuário pedir commit**
- Evitar: `if cfg.whatsapp_app_secret` que reabre o furo; marcar `classificar_mensagem`
  como `falha` ou `concluido`; texto em log ou em `evento_webhook.payload`
