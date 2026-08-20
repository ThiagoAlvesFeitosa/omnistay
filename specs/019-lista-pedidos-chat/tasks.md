---
description: "Task list for feature implementation"
---

# Tasks: Lista de Pedidos Feitos pelo Chat

**Input**: Design documents from `/specs/019-lista-pedidos-chat/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de
produção antes de um teste que falhe pela ausência dela, e pelo motivo certo.

**Organization**: Tarefas agrupadas por história (US1–US9), na ordem da spec.
Esquema (`enviar_lista_pedidos_chat`), porta, fila, matriz e esqueletos HTTP
entram na Foundational. O clique que agenda a lista (com consumo cobrável) é
a US1 (MVP). O recorte (excluir serviço e dispensado) é a US2. O GET do
painel é a US3.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1–US9)

## Como ver os testes falharem nesta fatia

**Esquema.** `testes/integracao/test_conformidade_do_esquema.py` compara o banco
migrado com `docs/04-schema.sql`. Editar o documento **antes** da revisão deixa
a conformidade vermelha. A revisão `0018` a devolve ao verde.

**Garantias.** `testes/integracao/test_garantias_do_banco.py` prova tipo aceito
e unicidade. Sem a migração, o segundo `enviar_lista_pedidos_chat` da mesma
reserva entra — o teste fica vermelho pelo motivo certo.

**Matriz.** Acrescentar `ler_pedidos_feitos_pelo_chat` em
`OPERACOES_ESPERADAS` **antes** de editar `politica.py` deixa
`test_matriz_completa_bate_com_o_contrato` vermelho.

**Rotas.** `testes/integracao/test_rotas_protegidas.py` varre o que está
registrado: o GET novo passa a exigir `401` sem cookie. **Não** editar
`ROTAS_PUBLICAS`.

**Serviços / portas.** Unitários falham por `ImportError` / `AttributeError` /
`NotImplementedError` até a função existir.

**F4.1.** `POST /saida` **sem** consumo cobrável continua com exatamente 1
`enviar_pesquisa_saida`. Com consumo cobrável, o mesmo clique passa a gerar
também a lista — isso é a fatia, não regressão.

---

## Phase 1: Setup

**Purpose**: constantes de teste e esqueleto do texto da lista

- [X] T001 [P] Estender `testes/suporte/consumo.py` (ou criar
      `testes/suporte/pedidos_chat.py`) com constantes estáveis: rótulo
      `pedidos feitos pelo chat`, caminho
      `/reservas/{id}/pedidos-feitos-pelo-chat`,
      `proibicoes_da_lista()` (`extrato`, `conta`). Sem segredo, sem rede
- [X] T002 [P] Criar `app/modulos/conversa/texto_lista_pedidos_chat.py` com
      docstring e a assinatura
      `montar_texto_lista_pedidos_chat(*, nome_completo: str, itens: list) -> str`
      levantando `NotImplementedError` até a US6
      ([contracts/portas-lista.md](./contracts/portas-lista.md))

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: revisão `0018`, porta, fila, operação nova, schemas HTTP,
esqueleto do processador. Nenhuma lista ainda é agendada no clique.

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. Ordem do esquema:
T003 → T004 → T006 → T007 (teste vermelho no documento, depois migração verde).

- [X] T003 Estender `testes/integracao/test_garantias_do_banco.py`: `INSERT` de
      trabalho `enviar_lista_pedidos_chat` aceito pelo `ck_trabalho_tipo`;
      segundo `INSERT` da mesma reserva recusado por
      `uq_trabalho_enviar_lista_pedidos_chat_reserva`. Rodar e **ver falhar**
      (FR-011, Artigo IX, [data-model.md](./data-model.md))
- [X] T004 Aplicar o delta em `docs/04-schema.sql`: tipo
      `enviar_lista_pedidos_chat` em `ck_trabalho_tipo`; índice único parcial
      `uq_trabalho_enviar_lista_pedidos_chat_reserva`. Rodar
      `testes/integracao/test_conformidade_do_esquema.py` e **ver falhar**
- [X] T005 [P] Alinhar `docs/04-modelagem-de-dados.md`: a lista de pedidos
      feitos pelo chat usa `consumo.descricao_item` + `valor_praticado`
      (pendente ou lançado); dispensado fica fora; trabalho
      `enviar_lista_pedidos_chat` único por reserva. Sem tabela nova
- [X] T006 Criar `alembic/versions/sql/0018_lista_pedidos_chat.sql` — cópia
      congelada do delta da T004 (CHECK com **todos** os tipos vigentes da
      `0017` + o novo; `CREATE UNIQUE INDEX`)
- [X] T007 Criar `alembic/versions/0018_lista_pedidos_chat.py`
      (`down_revision = "0017_confirmar_saida"`), `upgrade` executa o SQL
      congelado, `downgrade` restaura o `CHECK` da `0017` e derruba o índice.
      T003 e a conformidade verdes
- [X] T008 Acrescentar em `testes/unitarios/modulos/acesso/test_politica.py`:
      `ler_pedidos_feitos_pelo_chat` para `recepcao` e `gestor`, recusado
      para `staff`. Incluir em `OPERACOES_ESPERADAS` e **ver falhar**
      ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))
- [X] T009 Acrescentar a operação a `OPERACOES` em
      `app/modulos/acesso/politica.py`. T008 verde
- [X] T010 [P] Unitário em `testes/unitarios/adaptadores/test_mensageria_falsa.py`
      (estender): o Protocol declara `enviar_lista_pedidos_chat` com
      `telefone_destino`, `primeiro_nome`, `corpo`, `id_mensagem`,
      `id_reserva`; sucesso registra `tipo=lista_pedidos_chat` distinguível
      de `pesquisa_saida`/`pulso`/`sessao`; modo falha levanta
      `FalhaDeEnvio` sem eco do corpo. **Ver falhar**
      ([contracts/portas-lista.md](./contracts/portas-lista.md))
- [X] T011 Acrescentar `enviar_lista_pedidos_chat` ao Protocol em
      `app/portas/mensageria.py` e implementar em
      `app/adaptadores/mensageria_falsa.py`. T010 verde. **Nunca** abre rede.
      Adaptador WhatsApp em `app/adaptadores/mensageria_whatsapp.py`: método
      no Protocol (pode levantar `NotImplementedError` — nenhum teste o
      instancia)
- [X] T012 [P] Unitário em
      `testes/unitarios/fila/test_enfileirar_lista_pedidos_chat.py` (criar):
      `enfileirar_enviar_lista_pedidos_chat` existe, grava o tipo novo e
      entra em `TIPOS_CONSUMIVEIS`. **Ver falhar**
      ([contracts/fila-e-worker.md](./contracts/fila-e-worker.md))
- [X] T013 Acrescentar constante e `enfileirar_enviar_lista_pedidos_chat` em
      `app/fila/repository.py` e `app/fila/service.py`; incluir o tipo em
      `TIPOS_CONSUMIVEIS` / `reclamar_proximo`. T012 verde
- [X] T014 [P] Contratos HTTP em `app/modulos/hospedagem/schema.py`:
      `SaidaResposta` ganha `lista: str` com default `"ausente"` (F4.1 sem
      consumo continua verde);
      `ItemPedidoFeitoPeloChat` + `ListaPedidosFeitosPeloChat`
      (`id_reserva`, `itens`, `total`) conforme
      [contracts/api-de-pedidos.md](./contracts/api-de-pedidos.md)
- [X] T015 [P] Acrescentar ramo `enviar_lista_pedidos_chat` em
      `worker/consumidor.py` delegando a
      `conversa.processar_trabalho_enviar_lista_pedidos_chat` que ainda
      levanta `NotImplementedError` (processador na US1). Sem isso o claim
      marcaria `tipo_desconhecido`

**Checkpoint**: esquema, porta falsa, fila, matriz e CLI de consumo
prontos. Nenhuma lista foi agendada ainda.

---

## Phase 3: User Story 1 - Hóspede recebe a lista no encerramento (Priority: P1) 🎯 MVP

**Goal**: confirmação de saída de reserva com consumo cobrável agenda
exatamente uma lista distinta da pesquisa; o worker envia via porta falsa

**Independent Test**: cookie de recepção + `POST /reservas/{id}/saida` numa
hospedada **com** consumo pendente → `200`, `pesquisa=agendada`,
`lista=agendada`, 1 `enviar_pesquisa_saida` **e** 1
`enviar_lista_pedidos_chat` + mensagem pendente da lista. Worker
`--uma-passagem` entrega via `MensageriaFalsa` (`tipo=lista_pedidos_chat`).
O POST **não** chama a porta

### Tests for User Story 1

- [X] T016 [P] [US1] Estender
      `testes/unitarios/modulos/hospedagem/test_confirmar_saida.py`: com
      listar devolvendo itens, chama `agendar_lista_pedidos_chat` e
      `lista=agendada`; recusa de estado **não** agenda lista. **Ver falhar**
      (FR-001, FR-002, FR-010)
- [X] T017 [P] [US1] Integração em
      `testes/integracao/test_lista_pedidos_chat.py` (criar): semear consumo
      (reusar `abrir_consumo` / padrão de
      `testes/integracao/test_consumos_pendentes.py`); `POST /saida` → 200 +
      `lista=agendada` + trabalho + mensagem; o POST **não** envia; worker
      uma passagem marca enviada. **Ver falhar**
      ([contracts/api-de-saida.md](./contracts/api-de-saida.md),
      [contracts/fila-e-worker.md](./contracts/fila-e-worker.md))

### Implementation for User Story 1

- [X] T018 [US1] Implementar `listar_pedidos_feitos_pelo_chat` em
      `app/modulos/atendimento/repository.py` e
      `app/modulos/atendimento/service.py` (`id_hotel` + `id_reserva`; por
      ora pode devolver todo `consumo` da reserva — o recorte fino é a US2)
- [X] T019 [US1] Implementar `agendar_lista_pedidos_chat` em
      `app/modulos/conversa/service.py` (+ repositório): monta texto
      (placeholder até a US6, mas já grava `mensagem` pendente), enfileira
      `enviar_lista_pedidos_chat`, devolve `agendada` / `ja_agendada`.
      Unicidade pelo índice da T007
- [X] T020 [US1] Em `app/modulos/hospedagem/service.py`, `confirmar_saida`
      orquestra: pesquisa (já existe) → `atendimento.listar` → se não vazio,
      `conversa.agendar_lista`. Preencher `SaidaResposta.lista`. **Não**
      importar `atendimento` em `conversa` (ciclo)
- [X] T021 [US1] Implementar
      `processar_trabalho_enviar_lista_pedidos_chat` em
      `app/modulos/conversa/service.py`: lê telefone, chama
      `gateway.enviar_lista_pedidos_chat` com o corpo já gravado, espelha
      `status_envio`; `FalhaDeEnvio` reagenda o mesmo id. Ligar o ramo da
      T015. T016 e T017 verdes

**Checkpoint**: reserva com consumo cobrável recebe pesquisa **e** lista
gravadas; o worker envia a lista. Sem consumo ainda pode estar agendando
lista vazia — isso fecha na US4

---

## Phase 4: User Story 2 - Só o que gera cobrança entra na lista (Priority: P1)

**Goal**: recorte cobrável = pendente + lançado; serviço operacional e
dispensado ficam de fora; status de lançamento não vaza

**Independent Test**: reserva mista (consumo pendente, consumo lançado,
consumo dispensado, toalha) → lista (mensagem e consulta) só com pendente
e lançado, valores praticados, zero toalha, zero dispensado

### Tests for User Story 2

- [X] T022 [P] [US2] Unitário em
      `testes/unitarios/modulos/atendimento/test_listar_pedidos_chat.py`
      (criar): misto → só cobráveis; serviço não aparece; dispensado não
      aparece; ordem por `aberta_em`. **Ver falhar** (FR-005, FR-006)
- [X] T023 [P] [US2] Integração em
      `testes/integracao/test_lista_pedidos_chat.py` (estender): checkout da
      reserva mista; corpo da mensagem **não** cita a toalha nem o
      dispensado. **Ver falhar**

### Implementation for User Story 2

- [X] T024 [US2] Apertar o `WHERE` em
      `app/modulos/atendimento/repository.py`:
      `status_lancamento IN ('pendente', 'lancado')`; **não** selecionar
      `solicitacao.descricao` nem `status_lancamento` para o recado.
      T022 e T023 verdes

**Checkpoint**: o recorte da spec está no SQL

---

## Phase 5: User Story 3 - Recepção consulta a lista no painel (Priority: P1)

**Goal**: GET autenticado devolve o mesmo recorte da mensagem, mesmo com
envio pendente ou falho; lista vazia é `200` com `itens: []`

**Independent Test**: `GET /reservas/{id}/pedidos-feitos-pelo-chat` com
cookie de recepção da casa → `200` com itens cobráveis e `total`; staff
`403`; outro hotel `404`

### Tests for User Story 3

- [X] T025 [P] [US3] Integração em
      `testes/integracao/test_lista_pedidos_chat.py` (estender): GET da
      reserva com consumo, **antes** do worker, devolve os mesmos itens;
      reserva sem consumo → `itens: []`, `total: 0`; **não** inclui nome,
      telefone, `status_lancamento`. **Ver falhar**
      ([contracts/api-de-pedidos.md](./contracts/api-de-pedidos.md))

### Implementation for User Story 3

- [X] T026 [US3] Expor GET em `app/modulos/hospedagem/router.py`
      (`exigir_operacao("ler_pedidos_feitos_pelo_chat")`) delegando a
      `atendimento.listar_pedidos_feitos_pelo_chat`; `404` uniforme
      `Reserva nao encontrada.` quando a reserva não é do hotel (ler
      existência via `hospedagem` sem vazar). Soma `total` no serviço.
      T025 verde. `test_rotas_protegidas` cobre o `401`

**Checkpoint**: o painel é a fonte da verdade (Artigo IV)

---

## Phase 6: User Story 4 - Sem consumo cobrável, nenhuma mensagem extra (Priority: P1)

**Goal**: recorte vazio → `lista=ausente`, zero trabalho de lista; pesquisa
segue; sem backfill

**Independent Test**: `POST /saida` sem consumo (ou só toalha / só
dispensado) → `lista=ausente`, 0 `enviar_lista_pedidos_chat`, 1 pesquisa

### Tests for User Story 4

- [X] T027 [P] [US4] Estender
      `testes/unitarios/modulos/hospedagem/test_confirmar_saida.py`: listar
      vazio **não** chama `agendar_lista`; `lista=ausente`. **Ver falhar**
      (FR-009)
- [X] T028 [P] [US4] Integração: saída sem consumo e saída só com
      dispensado → `lista=ausente`, zero trabalho de lista; pesquisa
      `agendada`. Confirmar que
      `testes/integracao/test_confirmar_saida.py` (F4.1, sem consumo)
      permanece com 1 `enviar_pesquisa_saida`. **Ver falhar** se a US1
      ainda agenda lista vazia

### Implementation for User Story 4

- [X] T029 [US4] Em `app/modulos/hospedagem/service.py`, só chamar
      `agendar_lista` quando `listar` não for vazio; log
      `lista_pedidos_ausente` só com ids (sem valor). T027 e T028 verdes

**Checkpoint**: silêncio quando não há o que conferir (Artigo VII)

---

## Phase 7: User Story 5 - Valor na lista é o do momento do pedido (Priority: P1)

**Goal**: reajuste de `preco_atual` não altera a lista; dois pedidos do
mesmo item conservam cada `valor_praticado`

**Independent Test**: consumo a 12,00 → item vendável a 20,00 → checkout
mostra 12,00 na mensagem e no GET

### Tests for User Story 5

- [X] T030 [P] [US5] Integração em
      `testes/integracao/test_lista_pedidos_chat.py`: gravar consumo,
      atualizar `item_vendavel.preco_atual`, confirmar saída; GET e corpo
      da mensagem trazem o valor original. **Ver falhar** se alguém reler
      o cardápio (FR-004)

### Implementation for User Story 5

- [X] T031 [US5] Garantir que
      `app/modulos/atendimento/repository.py` lê só
      `consumo.valor_praticado` / `descricao_item` — sem JOIN de preço
      atual. T030 verde (provavelmente já está; não “passar de primeira”
      sem o teste ter falhado antes por ausência da asserção)

**Checkpoint**: histórico financeiro intacto

---

## Phase 8: User Story 6 - Honestidade: a lista não é a fatura da casa (Priority: P1)

**Goal**: texto com rótulo certo, itens, total dos pedidos do chat, frase
de alcance; zero `extrato`/`conta`; zero pergunta; zero convite a pagar

**Independent Test**: inspecionar o corpo montado e o enviado — rótulo,
alcance, proibições

### Tests for User Story 6

- [X] T032 [P] [US6] Unitário em
      `testes/unitarios/modulos/conversa/test_texto_lista_pedidos_chat.py`
      (criar): prenome; rótulo `pedidos feitos pelo chat`; cada item com
      valor no formato `R$ 12,00` (mesmo helper da confirmação de
      consumo); total rotulado como total **dos pedidos feitos pelo chat**;
      frase de que cobre só o chat; `proibicoes_da_lista()` ausentes; sem
      `?` de confirmação. **Ver falhar** (FR-003, FR-007, FR-008)
- [X] T033 [P] [US6] Integração: corpo enviado pelo worker contém o rótulo
      e **não** as proibições; pesquisa de saída da mesma reserva **não**
      incorpora a lista. **Ver falhar** (FR-002)

### Implementation for User Story 6

- [X] T034 [US6] Implementar `montar_texto_lista_pedidos_chat` em
      `app/modulos/conversa/texto_lista_pedidos_chat.py`; passar a usá-lo
      em `agendar_lista_pedidos_chat` (tirar o placeholder da US1).
      Reusar formatação de reais de
      `app/modulos/conversa/texto_confirmacao_consumo.py` (extrair helper
      se precisar, sem duplicar regra de vírgula). T032 e T033 verdes

**Checkpoint**: nomenclatura e Artigo XV no texto

---

## Phase 9: User Story 7 - Falha de envio não apaga a lista nem duplica (Priority: P1)

**Goal**: retry do mesmo trabalho; índice impede segunda lista; checkout
permanece `encerrado`; GET continua devolvendo itens

**Independent Test**: falha da falsa → mesmo `id_trabalho` retomado; INSERT
duplicado viola o único; `status` da reserva inalterado

### Tests for User Story 7

- [X] T035 [P] [US7] Unitário em
      `testes/unitarios/modulos/conversa/test_enviar_lista_pedidos_chat.py`
      (criar): `FalhaDeEnvio` não conclui o trabalho; segunda passagem
      envia a **mesma** mensagem. **Ver falhar** (FR-010, FR-011)
- [X] T036 [P] [US7] Integração: worker com falsa em modo falha; GET ainda
      lista o item; reserva `encerrado`; retomada entrega 1 envio
      `lista_pedidos_chat`. **Ver falhar**

### Implementation for User Story 7

- [X] T037 [US7] Ajustar
      `processar_trabalho_enviar_lista_pedidos_chat` no padrão da pesquisa
      de saída (reagendar o mesmo id; não criar mensagem nova). T035 e
      T036 verdes — a unicidade já está no banco (T007)

**Checkpoint**: gravar antes de enviar, de ponta a ponta

---

## Phase 10: User Story 8 - Isolar a lista por hotel e por perfil (Priority: P1)

**Goal**: staff não consulta; gestão consulta e não confirma saída; hotel
B leva `404` uniforme no GET e não dispara lista alheia

**Independent Test**: matriz + GET/POST cruzados entre hotéis e perfis

### Tests for User Story 8

- [X] T038 [P] [US8] Integração em
      `testes/integracao/test_lista_pedidos_chat.py`: staff GET `403`;
      gestão GET `200` e POST `/saida` `403`; recepção do hotel B no id do
      hotel A GET `404` (`Reserva nao encontrada.`) e POST `404`; zero
      trabalho de lista no hotel A por sessão B. **Ver falhar**
      (FR-015, FR-016,
      [contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))

### Implementation for User Story 8

- [X] T039 [US8] Conferir `exigir_operacao` no GET (T026) e o `404`
      uniforme (existência só com `id_hotel` da sessão). Sem revelar a
      reserva alheia. T038 verde

**Checkpoint**: multi-tenant e perfil

---

## Phase 11: User Story 9 - Conteúdo da mensagem não vaza em log (Priority: P2)

**Goal**: logs com ids, hotel, contagem e resultado — nunca corpo, descrição
de item nem valor por extenso

**Independent Test**: capturar logs em agendar, ausente, enviado e falha

### Tests for User Story 9

- [X] T040 [P] [US9] Estender
      `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py` (e/ou os
      unitários desta fatia): handler não contém o corpo, `Cerveja` nem
      `12,00` / `12.00`. **Ver falhar** se algum `logger.info` interpolar
      texto ou valor (FR-019)

### Implementation for User Story 9

- [X] T041 [US9] Trocar qualquer log restante por identificadores
      (`lista_pedidos_agendada`, `lista_pedidos_ausente`,
      `lista_pedidos_enviada`, `envio_tentativa_falhou`) com ids, hotel e
      contagem. T040 verde

**Checkpoint**: Artigo VIII na lista

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: estado do projeto, regressão F4.1, nomenclatura, quickstart

- [X] T042 [P] Estender os testes da F4.1 que confirmam saída **sem**
      consumo: continuam 1 `enviar_pesquisa_saida`, pesquisa intacta,
      `lista` ausente ou default. Worker da pesquisa não envia a lista
- [X] T043 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F4.2 concluída;
      próxima fatia do backlog (F5.1); decisões (mesmo clique, recorte
      cobrável, GET ao vivo, snapshot na mensagem, operação
      `ler_pedidos_feitos_pelo_chat`, sem React, sem extrato/conta)
- [X] T044 [P] Garantir que nenhum texto/rota desta fatia usa “extrato”
      ou “conta” (varredura nos arquivos tocados + `proibicoes_da_lista`)
      (FR-003, FR-020)
- [X] T045 Percorrer [quickstart.md](./quickstart.md) contra a suíte
      (`pytest testes/unitarios -q` e
      `pytest testes/integracao -q -k "saida or pedidos or lista"`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: depende do Setup — **bloqueia** todas as histórias
- **US1**: depois da Foundational — MVP (agenda + envia com consumo)
- **US2**: depois da US1 (há lista para recortar)
- **US3**: US2 (GET usa o mesmo recorte)
- **US4**: US1 (ramo vazio no mesmo `confirmar_saida`)
- **US5**: US2 (lê `valor_praticado`)
- **US6**: US1 (há agendar para plugar o texto real)
- **US7**: US1 (processador de envio)
- **US8**: US3 (GET existe)
- **US9**: caminhos felizes já logam
- **Polish**: no fim

### User Story Dependencies

- **US1**: nenhuma outra história
- **US2 / US4 / US6 / US7**: US1
- **US3**: US2 (recorte correto no painel)
- **US5**: US2
- **US8**: US3
- **US9**: US1 + US4 + US7

US4 pode ser antecipada logo após US1 se o recorte vazio já for óbvio;
US3 espera o WHERE da US2 para não ensinar o painel a mostrar dispensado.

### Within Each User Story

- Teste primeiro; **ver falhar pelo motivo certo**; implementar o mínimo;
  verde; só então a próxima

### Parallel Opportunities

- T001 // T002
- T005 // T008 // T010 // T012 // T014 // T015
- T016 // T017
- T022 // T023
- T027 // T028
- T032 // T033
- T035 // T036
- T042 // T043 // T044

Não paralelizar tarefas no mesmo arquivo (`hospedagem/service.py`,
`conversa/service.py`, `hospedagem/router.py`, `atendimento/repository.py`,
`docs/04-schema.sql`).

---

## Parallel Example: User Story 1

```bash
# Testes da US1 (arquivos distintos):
Task: "test_confirmar_saida.py unitário (lista=agendada)"
Task: "test_lista_pedidos_chat.py integração POST + worker"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Setup + Foundational
2. US1 (clique com consumo → lista gravada e enviável)
3. **Parar e validar** com o Independent Test da US1

### Incremental Delivery

1. US2 — recorte cobrável
2. US3 + US4 — painel e silêncio sem item
3. US5 + US6 — valor histórico e texto honesto
4. US7 + US8 + US9 — falha, isolamento, log
5. Polish e estado do projeto

### Suggested MVP scope

Só US1: no checkout com consumo cobrável, a intenção de enviar a lista
fica gravada e o worker entrega via porta falsa. Sem o clique nada
dispara. US2 é o recorte que impede toalha e cortesia — tratar em
seguida, antes do GET (US3).

---

## Notes

- [P] = arquivos distintos, sem dependência pendente
- Cada história é incrementável e testável sozinha depois da Foundational
- Ver o teste falhar **pelo motivo certo** antes de implementar
- Não inventar tela React, intenção nova no classificador, nem backfill
- A palavra "extrato" e a palavra "conta" não entram em rota, log, mensagem
  nem comentário de código desta fatia
