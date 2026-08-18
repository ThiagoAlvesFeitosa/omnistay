---
description: "Task list for feature implementation"
---

# Tasks: Registrar Pedido de Serviço

**Input**: Design documents from `/specs/013-registrar-pedido-servico/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de produção
antes de um teste que falhe pela ausência dela, e pelo motivo certo.

**Organization**: Tarefas agrupadas por história (US1–US7), na ordem da spec. Esquema
(`registrar_pedido_servico` + unicidade da origem), funções puras, `abrir_servico` e
enqueue **sem claim** entram na Foundational. O corte que **liga** o worker (enqueue
na classificação + allowlist + ramo) fica na US1 — os três no mesmo passo, para não
deixar `tipo_desconhecido` no meio do caminho. `GET /solicitacoes` é a US3. A
classificação de `pedido_de_servico` **continua** sem envio e sem `solicitacao` até
o worker consumir o tipo.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US7)

## Como ver os testes falharem nesta fatia

**Esquema.** `testes/integracao/test_conformidade_do_esquema.py` compara o banco
migrado com `docs/04-schema.sql`. Editar o documento **antes** da revisão deixa a
conformidade vermelha apontando `registrar_pedido_servico` / unicidade da origem. A
revisão `0012` a devolve ao verde.

**Quarto / recado.** Funções puras: o teste falha até o módulo existir.

**`abrir_servico`.** O módulo `atendimento` não existe; o unitário falha por
`ImportError` / `AttributeError`.

**Claim / worker.** Hoje a allowlist **não** inclui `registrar_pedido_servico` e o
consumidor não tem ramo. Os testes da US1 ficam vermelhos até allowlist e `elif`
existirem juntos. Não colocar o tipo na allowlist na Foundational — senão
`--uma-passagem` marca `tipo_desconhecido` antes do serviço existir.

**F3.2 / F3.3.** `test_pedido_e_reclamacao_nao_enfileiram_responder` em
`testes/unitarios/modulos/conversa/test_classificar_mensagem.py` **permanece**:
pedido não gera `responder_duvida`. O enqueue novo é outro callback. Não reescrever
o teste da F3.3 de dúvida coberta.

---

## Phase 1: Setup

**Purpose**: factories do pedido, sem repetir payload em cada arquivo

- [X] T001 [P] Criar `testes/suporte/pedido_servico.py` com helpers: texto de toalha
      com quarto (`toalha extra no quarto 402`), texto sem quarto (`travesseiro extra`),
      eixos `pedido_de_servico` / `neutro` / `baixa` via
      `testes/suporte/classificacao.py`. Sem segredo, sem rede
- [X] T002 [P] Em `testes/suporte/classificacao.py` (já existe), documentar no
      docstring que `pedido_de_servico` classificado é o gancho da F3.4
      (`registrar_pedido_servico`). Sem mudar eixos nem HMAC

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: tipo `registrar_pedido_servico` no banco, unicidade da origem,
`extrair_numero_quarto`, recado de confirmação, módulo `atendimento` com
`abrir_servico`, gravação do JSON da recebida, `enfileirar_registrar_pedido_servico`
**ainda sem claim**. Nenhuma história consome o trabalho ainda. Classificar **ainda
não** enfileira. **Nenhuma rota HTTP ainda.**

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. Ordem do esquema:
T003 → T004 → T006 → T007 (teste vermelho no documento, depois migração verde).

- [X] T003 Estender `testes/integracao/test_garantias_do_banco.py`: `INSERT` em
      `trabalho` com `tipo = 'registrar_pedido_servico'` aceito; segundo `INSERT`
      com o mesmo `payload.id_mensagem` viola
      `uq_trabalho_registrar_pedido_servico_mensagem`; segundo `INSERT` em
      `solicitacao` com o mesmo `id_mensagem_origem` viola
      `uq_solicitacao_mensagem_origem`. Rodar e **ver falhar** (FR-011,
      [data-model.md](./data-model.md))
- [X] T004 Aplicar o delta em `docs/04-schema.sql`: `ck_trabalho_tipo` inclui
      `registrar_pedido_servico`; índices
      `uq_trabalho_registrar_pedido_servico_mensagem` e
      `uq_solicitacao_mensagem_origem`. **Não** alterar `vw_fila_do_dia`. Rodar
      `testes/integracao/test_conformidade_do_esquema.py` e **ver falhar** pela
      divergência
- [X] T005 [P] Alinhar `docs/04-modelagem-de-dados.md`: tipo
      `registrar_pedido_servico`; JSON com `resposta = confirmacao_pedido` e
      `id_solicitacao`; pedido desta fatia **é** `solicitacao` tipo `servico`, sem
      `consumo`. Não dizer que pedido classificado permanece sem confirmação
- [X] T006 Criar `alembic/versions/sql/0012_registrar_pedido_servico.sql` — cópia
      congelada do CHECK e dos dois índices da T004
- [X] T007 Criar `alembic/versions/0012_registrar_pedido_servico.py`
      (`down_revision = "0011_responder_duvida_catalogo"`), `upgrade` executa o SQL
      congelado, `downgrade` restaura o CHECK da `0011` e remove os índices.
      T003 e a conformidade verdes
- [X] T008 [P] Unitário em `testes/unitarios/modulos/atendimento/test_quarto.py`:
      `extrair_numero_quarto` devolve `402` / `12` / `8B` / `15` nos exemplos de
      [contracts/quarto-e-descricao.md](./contracts/quarto-e-descricao.md); `None`
      para `toalha extra` e para `estou no 402`. **Ver falhar** (FR-002)
- [X] T009 Implementar `extrair_numero_quarto` em
      `app/modulos/atendimento/quarto.py` (módulo puro, sem SQL, sem HTTP). T008
      verde
- [X] T010 [P] Unitário em
      `testes/unitarios/modulos/conversa/test_texto_confirmacao_pedido.py`:
      `montar_confirmacao_pedido` confirma recebimento e que a equipe vai atender,
      usa só o prenome, **não** cita prazo, catálogo nem janela de preferência, **não**
      inclui o texto do pedido. **Ver falhar** (FR-004,
      [contracts/mensageria-sessao.md](./contracts/mensageria-sessao.md))
- [X] T011 Implementar `montar_confirmacao_pedido` em
      `app/modulos/conversa/texto_confirmacao_pedido.py` (função pura, padrão do
      aviso de dúvida). T010 verde
- [X] T012 [P] Unitário em
      `testes/unitarios/modulos/atendimento/test_abrir_servico.py`: `abrir_servico`
      insere `solicitacao` tipo `servico`, `status=aberta`, descrição = conteúdo
      informado, quarto extraído ou nulo, urgência copiada, `id_mensagem_origem`
      preenchido, **zero** linha em `consumo`; reserva de outro hotel não insere.
      **Ver falhar** (FR-001, FR-003, FR-015)
- [X] T013 Implementar `app/modulos/atendimento/repository.py` e
      `app/modulos/atendimento/service.py` (`abrir_servico` com `id_hotel` batendo
      em `reserva.id_hotel`). Sem router ainda. T012 verde. Depende de T007 e T009
- [X] T014 [P] Unitário em
      `testes/unitarios/modulos/conversa/test_registrar_pedido.py`:
      `gravar_confirmacao_pedido` (nome ilustrativo) atualiza JSON da recebida com
      `resposta=confirmacao_pedido`, `id_mensagem_resposta`, `id_solicitacao`;
      `desfecho` permanece `classificado`; **não** altera `conteudo` nem eixos;
      `id_hotel` tem de conferir. **Ver falhar** (FR-006, FR-015)
- [X] T015 Implementar a gravação em `app/modulos/conversa/repository.py` (`UPDATE`
      de `classificacao_bruta` com `WHERE` na mensagem **e** `id_hotel` via
      `reserva`; reusar `inserir_mensagem_enviada_pendente` para a enviada). T014
      verde
- [X] T016 [P] Unitário em
      `testes/unitarios/fila/test_enfileirar_registrar_pedido_servico.py`:
      `enfileirar_registrar_pedido_servico` insere tipo e payload só com IDs.
      **Ver falhar** ([contracts/fila-e-worker.md](./contracts/fila-e-worker.md)).
      Depende de T007
- [X] T017 Implementar `enfileirar_registrar_pedido_servico` em
      `app/fila/repository.py` e `app/fila/service.py`. **Não** incluir o tipo em
      `TIPOS_CONSUMIVEIS`. T016 verde

**Checkpoint**: esquema aceita o tipo; quarto e recado existem; dá para abrir
serviço, gravar JSON e enfileirar. Worker **não** consome o tipo. Classificar
**não** enfileira ainda. Sem `GET /solicitacoes`.

---

## Phase 3: User Story 1 - Pedido vira tarefa e o hóspede é confirmado (Priority: P1) 🎯 MVP

**Goal**: `pedido_de_servico` classificado → confirmação padrão gravada e enviada,
uma `solicitacao` tipo `servico` com descrição e quarto quando informado, zero
`consumo`, trabalho `concluido`, flag humano da fila do dia **falso**.

**Independent Test**: mensagem já `classificado`/`pedido_de_servico` com
`toalha extra no quarto 402` → enviada de confirmação, uma solicitação `servico`
com `numero_quarto=402` e descrição igual ao texto, `count(consumo)=0`,
`precisa_atendimento_humano=false`.

### Tests for User Story 1 ⚠️

- [X] T018 [P] [US1] Em
      `testes/unitarios/modulos/conversa/test_registrar_pedido.py`: repositório
      falso + `abrir_servico` espião + `MensageriaFalsa` →
      `processar_trabalho_registrar_pedido` insere enviada com o recado, chama
      `abrir_servico` com descrição = conteúdo e quarto `402`, atualiza JSON,
      chama `enviar_texto_sessao` **depois** de gravar, marca trabalho
      `concluido`. **Ver falhar** (FR-001, FR-003, FR-004, FR-006, FR-016)
- [X] T019 [P] [US1] Unitário em
      `testes/unitarios/fila/test_claim_registrar_pedido_servico.py`:
      `reclamar_proximo` **devolve** `registrar_pedido_servico` quando é o único
      pendente. **Ver falhar** (hoje a allowlist exclui)
- [X] T020 [P] [US1] Unitário em
      `testes/unitarios/modulos/conversa/test_classificar_mensagem.py`:
      `processar_trabalho_classificar_mensagem` com `pedido_de_servico`
      **enfileira** `registrar_pedido_servico` e **não** chama gateway nem
      `abrir_servico`. `test_pedido_e_reclamacao_nao_enfileiram_responder`
      permanece (pedido **não** gera `responder_duvida`). Caminho “já classificada”
      sem trabalho de pedido também enfileira. Dúvida geral continua só
      `responder_duvida`. **Ver falhar** (research §1)
- [X] T021 [US1] Integração em `testes/integracao/test_registrar_pedido.py`
      (criar): webhook + `LLMFalso` em `pedido_de_servico` +
      `processar_uma_passagem` → recebida intocada, existe enviada de confirmação,
      uma `solicitacao` `servico` com quarto `402`, zero `consumo`,
      `precisa_atendimento_humano=false`, `reserva.status=hospedado`. **Ver falhar**
      até o worker consumir o tipo (SC-001, SC-003)

### Implementation for User Story 1

- [X] T022 [US1] Implementar `processar_trabalho_registrar_pedido` em
      `app/modulos/conversa/service.py`: recado; gravar enviada; `abrir_servico`
      injetado; atualizar JSON; `gateway.enviar_texto_sessao`; `marcar_concluido`.
      Sem importar `atendimento` no módulo (callback, padrão da ficha). Sem LLM.
      Sem catálogo. T018 verde no caminho feliz
- [X] T023 [US1] Em `app/modulos/conversa/service.py`, ao gravar
      `pedido_de_servico` + `classificado` (e no caminho já classificada), chamar
      `enfileirar_registrar_pedido_servico`. Em `app/fila/repository.py`, incluir
      o tipo na allowlist. Em `worker/consumidor.py`, ramo com `gateway` e
      `abrir_servico=atendimento.abrir_servico` — **enqueue, allowlist e ramo no
      mesmo passo**. T019, T020 e T021 verdes. Nunca allowlist sem ramo
      (research §1)

**Checkpoint**: `--uma-passagem` classifica pedido de serviço, confirma e abre
solicitação tipo `servico` sem cobrança. HTTP da fila operacional ainda não existe
(US3). Quarto ausente ainda não tem teste próprio (US4).

---

## Phase 4: User Story 2 - Confirmação antes da tarefa (Priority: P1)

**Goal**: na transação, a enviada de confirmação é inserida **antes** de
`abrir_servico`; o recado não promete prazo nem fato da casa.

**Independent Test**: espião de `abrir_servico` observa que a enviada já existe
quando a solicitação nasce; o corpo é o recado da T011.

### Tests for User Story 2 ⚠️

- [X] T024 [P] [US2] Unitário em `test_registrar_pedido.py`: o espião de
      `abrir_servico` verifica que a mensagem enviada de confirmação **já está**
      no repositório no instante da chamada; se `abrir_servico` levantar, a
      transação não deixa solicitação órfã sem enviada. O corpo enviado não contém
      prazo nem catálogo. **Ver falhar** (FR-004, FR-005, SC-002)

### Implementation for User Story 2

- [X] T025 [US2] Garantir a ordem em `processar_trabalho_registrar_pedido` (
      `app/modulos/conversa/service.py`): INSERT enviada → `abrir_servico` → JSON
      → envio. T024 verde — se T022 já ordenava, esta tarefa é o teste de ordem e
      o ajuste se o serviço chamava `abrir_servico` primeiro

**Checkpoint**: zero pedidos tramitam sem confirmação gravada.

---

## Phase 5: User Story 3 - Fila da equipe sem ficha cadastral (Priority: P1)

**Goal**: `GET /solicitacoes` lista abertas/`em_andamento` da propriedade da
sessão; staff, recepção e gestão veem o mesmo JSON **sem** nome/telefone/documento;
hotel B não vê A; staff continua recusado na ficha e na fila do dia.

**Independent Test**: staff da propriedade A autentica, `GET /solicitacoes` devolve
o pedido aberto com quarto e descrição; o JSON não tem nome nem telefone; staff B
vê lista sem o item de A; `GET /reservas/{id}/ficha` do staff A continua 403.

### Tests for User Story 3 ⚠️

- [X] T026 [P] [US3] Unitário em
      `testes/unitarios/modulos/atendimento/test_listar_abertas.py`:
      `listar_abertas(id_hotel)` devolve itens operacionais (`id_solicitacao`,
      `id_reserva`, `tipo`, `descricao`, `numero_quarto`, `urgencia`, `status`,
      `aberta_em`), ordenados por `aberta_em` crescente; **não** inclui nome nem
      telefone; hotel B vazio. **Ver falhar** (FR-007, FR-008, FR-015)
- [X] T027 [P] [US3] Integração em `testes/integracao/test_solicitacoes.py`
      (criar): após um pedido registrado (US1) ou `abrir_servico` direto, login
      staff A → `GET /solicitacoes` 200 com o item e **sem** chaves cadastrais;
      recepção e gestão A também 200 no mesmo formato; staff B 200 sem o item de
      A. **Ver falhar** (SC-005, SC-006,
      [contracts/api-de-atendimento.md](./contracts/api-de-atendimento.md))
- [X] T028 [P] [US3] Estender `testes/integracao/test_rotas_protegidas.py`:
      `GET /solicitacoes` sem cookie 401; staff A em `GET /fila-do-dia` e
      `GET /reservas/{id}/ficha` continua 403. **Ver falhar** até a rota existir
      ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))

### Implementation for User Story 3

- [X] T029 [US3] Implementar `listar_abertas` em
      `app/modulos/atendimento/repository.py` e
      `app/modulos/atendimento/service.py` (JOIN `reserva`, filtro `id_hotel`,
      status `aberta`/`em_andamento`). T026 verde
- [X] T030 [US3] Criar `app/modulos/atendimento/schema.py` e
      `app/modulos/atendimento/router.py` (`GET /solicitacoes`,
      `exigir_operacao("ler_solicitacao_atribuida")`); incluir o roteador em
      `app/main.py`. Nenhuma operação nova na matriz. T027 e T028 verdes

**Checkpoint**: a equipe operacional lê a fila no painel sem carregar ficha no
dispositivo de sessão longa.

---

## Phase 6: User Story 4 - Pedido sem quarto ainda confirma (Priority: P1)

**Goal**: mensagem sem palavra-chave de quarto ainda gera confirmação e
`solicitacao` com `numero_quarto` nulo; nenhum quarto é inventado.

**Independent Test**: `travesseiro extra` → enviada + solicitação visível com
quarto nulo.

### Tests for User Story 4 ⚠️

- [X] T031 [P] [US4] Unitário em `test_registrar_pedido.py`: conteúdo sem quarto →
      `abrir_servico` chamado com `numero_quarto=None`; enviada mesmo assim.
      **Ver falhar** (FR-002, SC-004)
- [X] T032 [US4] Integração em `testes/integracao/test_registrar_pedido.py`:
      webhook sem quarto + passagem → `numero_quarto` nulo, item em
      `GET /solicitacoes` (ou `SELECT`) permanece visível. **Ver falhar**

### Implementation for User Story 4

- [X] T033 [US4] Garantir em `processar_trabalho_registrar_pedido` (
      `app/modulos/conversa/service.py`) que `extrair_numero_quarto` nulo **não**
      aborta o registro. T031 e T032 verdes — se T022 já fazia, esta tarefa é o
      teste e o ajuste se o serviço recusava quarto vazio

**Checkpoint**: ausência de quarto não silencia o hóspede nem esconde a tarefa.

---

## Phase 7: User Story 5 - Reprocessar não duplica (Priority: P1)

**Goal**: JSON já com `confirmacao_pedido` + `id_solicitacao` não insere segunda
enviada nem segunda solicitação; enviada `pendente` só retenta o envio.

**Independent Test**: segunda passagem após o cenário da US1 → zero segunda
enviada, zero segunda `solicitacao`.

### Tests for User Story 5 ⚠️

- [X] T034 [P] [US5] Unitário em `test_registrar_pedido.py`: JSON já com
      `resposta=confirmacao_pedido` e `id_solicitacao` → zero segunda enviada,
      zero segunda chamada a `abrir_servico`; se a enviada está `pendente`, chama
      `enviar_texto_sessao` uma vez. **Ver falhar** (FR-011, SC-007)
- [X] T035 [US5] Integração em `test_registrar_pedido.py`: segunda
      `processar_uma_passagem` após o pedido concluído; unicidade do banco já
      coberta na T003. **Ver falhar** até o guard existir

### Implementation for User Story 5

- [X] T036 [US5] Guard no `processar_trabalho_registrar_pedido` de
      `app/modulos/conversa/service.py` (research §6). T034 e T035 verdes.
      `IntegrityError` no enqueue (já classificada) continua só logando, como na
      F3.3

**Checkpoint**: retrabalho não manda duas toalhas nem duas mensagens.

---

## Phase 8: User Story 6 - Falha não perde o pedido (Priority: P1)

**Goal**: envio falho depois de gravar preserva enviada + `solicitacao` e reagenda
**só** mensageria; falha ao gravar não envia recado.

**Independent Test**: (a) `MensageriaFalsa` em modo falha após INSERT → pedido e
confirmação no banco, trabalho não `concluido` sem retry de envio; (b) `abrir_servico`
levantando → zero `enviar_texto_sessao`.

### Tests for User Story 6 ⚠️

- [X] T037 [P] [US6] Unitário em `test_registrar_pedido.py`: após gravar, gateway
      com `FalhaDeEnvio` → enviada e `id_solicitacao` permanecem; **não**
      `marcar_concluido` sem reagendar envio; **não** chama `abrir_servico` de
      novo. **Ver falhar** (FR-013, SC-008)
- [X] T038 [US6] Unitário em
      `testes/unitarios/modulos/conversa/test_registrar_pedido.py`: `abrir_servico`
      levanta antes do envio → zero chamada a `enviar_texto_sessao`; trabalho não
      deixa solicitação pela metade (transação desfaz). **Ver falhar** (FR-012)

### Implementation for User Story 6

- [X] T039 [US6] Em `app/modulos/conversa/service.py`: capturar `FalhaDeEnvio`
      depois de gravar e reagendar mensageria (padrão da coleta / dúvida); deixar
      a transação abortar se gravar falhar **antes** do envio. T037 e T038 verdes.
      Não usar `marcar_falha` por quarto ausente

**Checkpoint**: mensageria caída atrasa a confirmação; não apaga a tarefa.

---

## Phase 9: User Story 7 - Conteúdo não vaza em log (Priority: P2)

**Goal**: registro, já registrado e envio falho logam identificadores, hotel e
`resultado` — nunca pedido, confirmação, descrição ou quarto.

**Independent Test**: caplog nos desfechos; fixture de conteúdo ausente do log.

### Tests for User Story 7 ⚠️

- [X] T040 [P] [US7] Estender
      `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py`:
      `processar_trabalho_registrar_pedido` nos desfechos registrado, já
      registrado e envio falho — o texto do pedido e o da confirmação não
      aparecem; há `id_mensagem` / `id_trabalho` / `id_hotel` / `resultado`.
      **Ver falhar** (FR-014, SC-009)

### Implementation for User Story 7

- [X] T041 [US7] Ajustar logs em `app/modulos/conversa/service.py` (eventos
      `pedido_registrado`, `pedido_ja_registrado`, `pedido_envio_falhou` conforme
      [contracts/fila-e-worker.md](./contracts/fila-e-worker.md)). T040 verde

**Checkpoint**: trilha técnica sem cópia da conversa.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: intenções que não são pedido, regressão F3.3, fronteiras, documentação,
suíte

- [X] T042 [P] Unitário em `test_classificar_mensagem.py`: `duvida_geral`,
      `reclamacao_tecnica`, `upsell` e falha de classificação **não** inserem
      `registrar_pedido_servico`. Integração: F3.3 de dúvida coberta / não coberta
      continua **sem** `solicitacao` tipo `servico` (FR-010, FR-016)
- [X] T043 [P] Integração: após pedido registrado, `GET /fila-do-dia` (recepção)
      permanece `precisa_atendimento_humano=false`; visão **não** ganhou desfecho
      novo (`testes/integracao/test_fila_do_dia.py` ou
      `test_registrar_pedido.py`)
- [X] T044 [P] Regressão: `testes/integracao/test_responder_duvida.py`,
      `test_classificar_mensagem.py` (ramos que não são pedido),
      `test_webhook_estadia.py` e o claim de outros tipos continuam verdes;
      `responder_duvida` **não** chama `abrir_servico`
- [X] T045 Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F3.4 em andamento/concluída,
      revisão `0012`, módulo `atendimento` mínimo, `GET /solicitacoes`, worker
      consome `registrar_pedido_servico`, próxima fatia **F3.5**. Não apontar F2.3
- [X] T046 Revisar fronteiras: `conversa` não escreve `solicitacao` (só callback);
      `atendimento` não envia mensagem; SQL de `trabalho` só em `app/fila/`;
      `id_hotel` em `abrir_servico` / `listar_abertas`; nenhum teste instancia
      adaptador real de IA nem WhatsApp; falha de envio **depois** de gravar
      reagenda mensageria. Rodar [quickstart.md](./quickstart.md),
      `pytest testes/unitarios -q` e a integração desta fatia
      (`test_registrar_pedido.py`, `test_solicitacoes.py`,
      `test_classificar_mensagem.py`, `test_conformidade_do_esquema.py`,
      `test_garantias_do_banco.py`). Tudo verde, sem rede

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: após Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: após Foundational — MVP (consumo + confirmação + `solicitacao`)
- **US2 (Phase 4)**: após US1 (mesmo serviço; ordem na transação)
- **US3 (Phase 5)**: após Foundational para `abrir_servico`; na prática após US1
  para ter pedido real. Pode semear `abrir_servico` direto
- **US4 (Phase 6)**: após US1 (caminho quarto nulo)
- **US5 (Phase 7)**: após US1 (guard no mesmo processador)
- **US6 (Phase 8)**: após US1 (falha de envio / gravação)
- **US7 (Phase 9)**: após os desfechos existirem (US1 / US5 / US6)
- **Polish (Phase 10)**: após as histórias desejadas

### User Story Dependencies

- **US1**: após Phase 2 — sem dependência de outra história; **é o corte do worker**
- **US2**: após US1 (estende o processador)
- **US3**: após T013; independente do worker se o teste semear `abrir_servico`
- **US4**: após US1; não é novo tipo, é quarto nulo
- **US5**: após US1
- **US6**: após US1
- **US7**: após US1 (e de preferência US5/US6 para os três eventos)

### Within Each User Story

1. Testes escritos e **vermelhos pelo motivo certo**
2. Implementação mínima
3. Verde
4. Só então a próxima história

### Parallel Opportunities

- T001 e T002 em paralelo
- T005 em paralelo com T003/T004
- T008/T009, T010/T011 em paralelo entre si (arquivos distintos)
- T012/T013 depois de T007 e T009
- T014/T015 depois de T007
- T016/T017 depois de T007
- T018, T019 e T020 em paralelo na US1; T021 no arquivo novo de integração
- T023 é atômico (enqueue + allowlist + ramo)
- T026, T027 e T028 em paralelo na US3 depois de haver como semear solicitação
- T031 em paralelo com T032 na US4
- T034 em paralelo com T035 na US5
- T037 em paralelo com T038 na US6
- T042, T043 e T044 em paralelo no polish

**Sequência obrigatória em Foundational**: T003 → T004 → T006 → T007. Ver a
conformidade vermelha entre T004 e T007 é a prova de que ela vigia o documento.

**Sequência obrigatória na US1**: T022 (serviço) pode anteceder T023, mas **T023 é
atômico**. Não mergear allowlist sozinha. Não enfileirar na classificação antes do
ramo existir.

---

## Parallel Example: User Story 1

```text
# Testes em paralelo (antes da implementação):
T018 test_registrar_pedido.py                    (serviço / caminho feliz)
T019 test_claim_registrar_pedido_servico.py      (allowlist)
T020 test_classificar_mensagem.py                (enqueue na classificação)
T021 test_registrar_pedido.py (integração)       — arquivo novo

# Depois:
T022 processar_trabalho_registrar_pedido
T023 enqueue + allowlist + elif                  (juntos)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: worker confirma pedido e abre `solicitacao` tipo `servico`; zero
   `consumo`; flag humano falso
4. Demo: webhook “toalha extra no quarto 402” + `--uma-passagem`; `SELECT` da
   enviada e da solicitação

### Incremental Delivery

1. US1 → confirmação + tarefa sem cobrança
2. US2 → ordem confirmação → solicitação
3. US3 → `GET /solicitacoes` sem ficha
4. US4 → quarto ausente não bloqueia
5. US5 → idempotência
6. US6 → falha não perde o pedido
7. US7 → log limpo
8. Polish → intenções outras, estado do projeto, quickstart

### Suggested MVP scope

**US1** (T001–T023) prova o valor visível. **US2 e US3 são aceite obrigatório**
antes de marcar F3.4 concluída (confirmação antes de tramitar + fila da equipe no
backlog). US4 é Artigo I/XV nesta fatia. US5 e US6 são os casos obrigatórios de
idempotência e “gravar antes de enviar”. US7 é P2 e entra nesta entrega no padrão
das fatias anteriores (Artigo VIII).

---

## Notes

- [P] = arquivos distintos, sem depender de tarefa incompleta da mesma sequência
- Sem React, sem `consumo`, sem reclamação, sem resolver chamado, sem rota GET de
  histórico, sem LLM neste ramo, sem inferência de check-in, sem quarto mágico
- `test_pedido_e_reclamacao_nao_enfileiram_responder` **não** se inverte — o
  enqueue de pedido é outro callback
- Nenhum teste chama o provedor real de IA nem o adaptador WhatsApp
- Commit por tarefa ou grupo lógico **só se o usuário pedir commit**
- Evitar: `marcar_falha` por quarto nulo; allowlist sem ramo; enqueue na
  classificação antes do ramo; `conversa` escrever SQL em `solicitacao`;
  `atendimento` enviar WhatsApp; nome/telefone em `GET /solicitacoes`; texto em
  log; ligar `precisa_atendimento_humano`; ciclo `conversa` ↔ `atendimento`
