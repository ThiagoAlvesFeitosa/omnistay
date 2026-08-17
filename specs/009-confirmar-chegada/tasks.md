---
description: "Task list for feature implementation"
---

# Tasks: Confirmar Chegada e Boas-vindas

**Input**: Design documents from `/specs/009-confirmar-chegada/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de produção antes
de um teste que falhe pela ausência dela, e pelo motivo certo.

**Organization**: Tarefas agrupadas por história (US1–US7). **A ordem das fases não segue a
numeração da spec**: US6 (os três slots) vem antes de US2 (o pacote), porque o pacote lê os
slots e sem eles o teste de US2 não teria como afirmar o conteúdo. As duas são P1.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US7)

## Como ver os testes falharem nesta fatia

**Esquema.** `testes/integracao/test_conformidade_do_esquema.py` compara o banco migrado com
`docs/04-schema.sql`. Editar o documento **antes** da revisão deixa a conformidade vermelha
apontando o delta — é a prova de que o teste vigia o que diz vigiar. A revisão `0008` a
devolve ao verde.

**Garantias.** `testes/integracao/test_garantias_do_banco.py` roda com
`OMNISTAY_SEM_MIGRACAO=1` para provar que cada garantia falha sem a migração. O índice
`uq_trabalho_enviar_boas_vindas_reserva` e o tipo `enviar_boas_vindas` entram por lá.

**Matriz.** Acrescentar as duas operações em `OPERACOES_ESPERADAS` **antes** de editar
`politica.py` deixa `test_matriz_completa_bate_com_o_contrato` vermelho.

**Rotas.** `testes/integracao/test_rotas_protegidas.py` varre o que está registrado: cada rota
nova passa a exigir `401` sem cookie. **Não editar `ROTAS_PUBLICAS`.**

**Serviços.** Unitários com repositório falso falham por `AttributeError` / exceção ausente
até a implementação existir.

---

## Phase 1: Setup

**Purpose**: os dois arquivos que todas as histórias assumem existir

- [X] T001 [P] Criar `app/modulos/conversa/texto_boas_vindas.py` com docstring do módulo e a
      assinatura `montar_texto_boas_vindas(*, nome_completo, cafe, wifi, checkout) -> str`
      levantando `NotImplementedError` (o corpo entra na US2)
- [X] T002 [P] Ampliar `testes/suporte/ambiente_de_acesso.py` com `_semear_boas_vindas`
      (os três slots com valor válido e `horas_validade_boas_vindas` = `12`) chamada em
      `_montar_propriedade`, nas duas propriedades, com **valores distintos** por hotel.
      Sem valores distintos, T024 passa sem provar o isolamento. Sem a semeadura, todo
      teste de integração de confirmação nasceria com slot ausente e afirmaria o caminho
      errado

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: revisão `0008`, matriz, porta, fila e contratos HTTP — o que nenhuma história
deve reinventar

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase.

- [X] T003 Estender `testes/integracao/test_garantias_do_banco.py`: `INSERT` de trabalho
      `enviar_boas_vindas` com tipo aceito pelo `ck_trabalho_tipo`; segundo `INSERT` para a
      mesma reserva recusado por `uq_trabalho_enviar_boas_vindas_reserva`;
      `sem_cadastro_previo → hospedado` e `ficha_parcial → hospedado` em `TRANSICOES_ACEITAS`.
      Rodar e **ver falhar** (FR-008, Artigo IX)
- [X] T004 Aplicar o delta em `docs/04-schema.sql`: tipo `enviar_boas_vindas` no
      `ck_trabalho_tipo`, índice `uq_trabalho_enviar_boas_vindas_reserva`, coluna
      `boas_vindas_nao_enviadas` na `vw_fila_do_dia`, quatro chaves novas no `COMMENT` de
      `parametro_hotel`. Rodar `test_conformidade_do_esquema.py` e **ver falhar** pela
      divergência
- [X] T005 Criar `alembic/versions/sql/0008_confirmar_chegada.sql` — cópia congelada do delta
      da T004, com a visão recriada por inteiro e a semeadura idempotente das **quatro** chaves
      (os três slots e `horas_validade_boas_vindas` = `12`) no padrão `WHERE NOT EXISTS` da
      `0007` ([data-model.md](./data-model.md))
- [X] T006 Criar `alembic/versions/0008_confirmar_chegada.py`
      (`down_revision = "0007_controlar_silencio"`), aplicando o SQL no `upgrade` e com
      `downgrade` explícito: derruba o índice, restaura o `CHECK` sem `enviar_boas_vindas` e
      recria a visão da `0007`. T003 e T004 verdes
- [X] T007 Acrescentar em `testes/unitarios/modulos/acesso/test_politica.py`:
      `alterar_texto_de_boas_vindas` só `recepcao`; `ler_texto_de_boas_vindas` para `recepcao`
      e `gestor`; `confirmar_fase_da_reserva` continua só `recepcao`; nenhuma operação da
      matriz contém `parametro` no nome (SC-014a). Incluir as duas em `OPERACOES_ESPERADAS` e
      **ver falhar**
- [X] T008 Acrescentar as duas operações a `OPERACOES` em
      `app/modulos/acesso/politica.py` até T007 verde
      ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))
- [X] T009 [P] Ampliar `app/modulos/propriedade/repository.py` com `upsert_parametro`
      (`ON CONFLICT (id_hotel, chave) DO UPDATE`, `atualizado_em = now()`) e
      `ler_parametros(conexao, id_hotel, chaves)` devolvendo dicionário
- [X] T010 [P] Acrescentar `enfileirar_enviar_boas_vindas` em `app/fila/repository.py`
      (tipo `enviar_boas_vindas`, payload só com `id_reserva` e `id_mensagem`) e o
      encaminhamento correspondente em `app/fila/service.py`
- [X] T011 [P] Acrescentar `enviar_boas_vindas` ao Protocol em `app/portas/mensageria.py`
      (`telefone_destino`, `variaveis`, `corpo`, `id_mensagem`, `id_reserva`), implementar em
      `app/adaptadores/mensageria_falsa.py` e em `app/adaptadores/mensageria_whatsapp.py`
      (template `boas_vindas`, quatro parâmetros de corpo na ordem da tupla)
      ([contracts/boas-vindas-fila-e-porta.md](./contracts/boas-vindas-fila-e-porta.md))
- [X] T012 [P] Criar os contratos HTTP: `BoasVindasEntrada` / `BoasVindasResposta` em
      `app/modulos/propriedade/schema.py`; `ChegadaResposta` (`id_reserva`, `status`,
      `checkin_em`, `boas_vindas`) e o campo `boas_vindas_nao_enviadas` em `ItemFilaDoDia` em
      `app/modulos/hospedagem/schema.py`
      ([contracts/api-de-chegada.md](./contracts/api-de-chegada.md))

**Checkpoint**: banco migrado e documentado, matriz com as duas operações, porta e fila
prontas para receber o pacote. Nenhuma rota nova ainda.

---

## Phase 3: User Story 1 - Confirmar a chegada no painel (Priority: P1) 🎯 MVP

**Goal**: recepção confirma a chegada de uma reserva elegível da própria propriedade; a
reserva passa a `hospedado` e o instante real fica em `checkin_em`.

**Independent Test**: sessão de recepção → `POST /reservas/{id}/chegada` em reserva
`ficha_recebida` → `200` com `status: "hospedado"`; no banco, `checkin_em` preenchido e
distinto da `data_checkin_prevista`.

### Tests for User Story 1 ⚠️

> Escrever primeiro; rodar; ver falhar pelo motivo certo.

- [X] T013 [P] [US1] Unitário em
      `testes/unitarios/modulos/hospedagem/test_confirmar_chegada.py` com repositório falso:
      a confirmação chama o `UPDATE` com `id_hotel` e com os três estados de origem;
      `rowcount = 1` devolve resultado `hospedado` e chama o agendador injetado;
      `rowcount = 0` não chama o agendador (FR-001, FR-002, FR-005)
- [X] T014 [US1] Integração em `testes/integracao/test_confirmar_chegada.py`: recepção
      confirma reserva `ficha_recebida` → `200`, `status` hospedado, `checkin_em` não nulo e
      distinto da data prevista; sem cookie → `401`. Rodar e ver falhar

### Implementation for User Story 1

- [X] T015 [US1] Implementar em `app/modulos/hospedagem/repository.py`:
      `confirmar_chegada` (`UPDATE ... WHERE id_hotel AND status IN (...) RETURNING status,
      checkin_em`) e `ler_reserva_do_hotel` (para distinguir inexistente de estado inválido)
      conforme [data-model.md](./data-model.md)
- [X] T016 [US1] Implementar `confirmar_chegada` em `app/modulos/hospedagem/service.py` com
      as exceções `ReservaNaoEncontrada` e `ChegadaNaoPermitida`, agendador injetável (mesmo
      padrão de `criar_reserva`) e log `chegada_confirmada id_reserva id_hotel` sem dado
      pessoal. T013 verde
- [X] T017 [US1] Implementar `POST /reservas/{id_reserva}/chegada` em
      `app/modulos/hospedagem/router.py` com
      `exigir_operacao("confirmar_fase_da_reserva")`, `id_hotel` só da sessão, `200` /
      `404` / `409`. T014 verde

**Checkpoint**: o clique de fronteira existe e registra o instante real. Nenhuma mensagem
ainda.

---

## Phase 4: User Story 3 - Recusar confirmação inválida sem corromper o ciclo (Priority: P1)

**Goal**: encerrada, cancelada, já hospedada e ainda aguardando cadastro recebem recusa clara;
nada é gravado, nada é disparado.

**Independent Test**: tentar confirmar em cada um dos quatro estados → `409`; no já
hospedado, `checkin_em` permanece o que era; `trabalho` e `mensagem` não crescem em nenhum
caso.

### Tests for User Story 3 ⚠️

- [X] T018 [P] [US3] Unitário em
      `testes/unitarios/modulos/hospedagem/test_confirmar_chegada.py`: cada estado recusado
      levanta `ChegadaNaoPermitida` com o status atual no log, e o agendador não é chamado
      (FR-004, FR-005)
- [X] T019 [P] [US3] Integração em `testes/integracao/test_confirmar_chegada.py`: `409` para
      `encerrado`, `cancelada`, `hospedado` e `aguardando_cadastro`; `checkin_em` intacto na
      reserva já hospedada; zero linhas novas em `trabalho` e em `mensagem`
- [X] T020 [P] [US3] Integração em `testes/integracao/test_confirmar_chegada.py`: reserva
      `ficha_parcial` e reserva `sem_cadastro_previo` são **aceitas** (`200`) — ficha
      incompleta não bloqueia o balcão (FR-003)

### Implementation for User Story 3

- [X] T021 [US3] Ajustar `app/modulos/hospedagem/service.py` e `router.py` até T018–T020
      verdes: `409` com motivo legível para estado não admitido, `404` para reserva ausente,
      e nenhuma gravação nos caminhos recusados

**Checkpoint**: a máquina de estados está fechada na aplicação e garantida pela trigger
(T003).

---

## Phase 5: User Story 6 - Guardar as três informações de entrada (Priority: P1)

**Goal**: recepção lê e grava café, wi-fi e checkout; valor inválido para o canal é recusado
na hora; a instalação já nasce com os três preenchidos.

**Independent Test**: `GET /propriedade/boas-vindas` → três valores; `PUT` válido → `200`;
`PUT` com quebra de linha → `422` e os três valores anteriores intactos; gestão lê e não
grava; `staff` recusado nas duas.

### Tests for User Story 6 ⚠️

- [X] T022 [P] [US6] Unitário em
      `testes/unitarios/modulos/propriedade/test_slots_boas_vindas.py`: a validação recusa
      vazio, só espaços, `\n`, `\r`, `\t`, cinco espaços seguidos e mais de 255 caracteres;
      **aceita** quatro espaços seguidos; grava o valor após `strip`; um valor inválido entre
      os três impede a gravação dos outros dois (FR-028, atomicidade)
- [X] T023 [P] [US6] Estender `testes/unitarios/modulos/propriedade/test_bootstrap.py`: em
      `test_criacao_inicial_grava_propriedade_gestor_e_duracoes`, a asserção `chaves ==
      {...}` fica vermelha até incluir os três slots e `horas_validade_boas_vindas`; cada
      valor semeado dos slots passa pela própria função de validação; o prazo é inteiro
      positivo (FR-029, FR-031b). Estender `testes/integracao/test_bootstrap.py`: banco
      migrado + hotel criado pelo bootstrap (sem `ambiente_de_acesso`) → as quatro chaves
      presentes e não vazias. Sem essa asserção, T002 mascararia uma `0008` ou
      `criar_instalacao_inicial` sem semeadura, e a propriedade já instalada seria pulada
      em silêncio por `prazo_ausente`
- [X] T024 [US6] Integração em `testes/integracao/test_boas_vindas_slots.py`: `GET` de
      recepção → `200` com os três; `PUT` válido → `200`; `PUT` inválido → `422` sem alterar
      nada; gestão `GET` `200` e `PUT` `403`; `staff` `403` nas duas; sessão do hotel B não vê
      valor do hotel A (FR-027)

### Implementation for User Story 6

- [X] T025 [US6] Implementar em `app/modulos/propriedade/service.py` a função pura de
      validação, `ler_textos_de_boas_vindas` e `gravar_textos_de_boas_vindas` (os três na
      mesma transação), com `DadosInvalidos` nomeando o campo recusado sem repetir o valor
- [X] T026 [US6] Completar `upsert_parametro` / `ler_parametros` em
      `app/modulos/propriedade/repository.py` se a T009 deixou esqueleto
- [X] T027 [US6] Implementar `GET` e `PUT /propriedade/boas-vindas` em
      `app/modulos/propriedade/router.py` com `ler_texto_de_boas_vindas` e
      `alterar_texto_de_boas_vindas`. T024 verde
- [X] T028 [US6] Acrescentar `PARAMETROS_BOAS_VINDAS_PADRAO` (três slots +
      `horas_validade_boas_vindas`) e a semeadura em `criar_instalacao_inicial`
      (`app/modulos/propriedade/service.py`) até T023 verde. A chave de prazo **não** entra na
      rota de boas-vindas nem na permissão da recepção

**Checkpoint**: a propriedade tem o que dizer no recado, e erro de digitação aparece na
configuração — não na chegada do hóspede.

---

## Phase 6: User Story 2 - Disparar o pacote curto de boas-vindas (Priority: P1)

**Goal**: a confirmação registra uma mensagem pendente e um trabalho; o worker entrega pelo
gateway; um pacote por reserva, garantido pelo índice.

**Independent Test**: confirmar chegada → uma linha em `trabalho` e uma em `mensagem`
(`pendente`) → passagem do worker → `mensagem` `enviada`, `trabalho` `concluido`, gateway
falso com as quatro variáveis; nenhum segundo pacote em reprocessamento.

### Tests for User Story 2 ⚠️

- [X] T029 [P] [US2] Unitário em
      `testes/unitarios/modulos/conversa/test_texto_boas_vindas.py`: o texto confirma a
      chegada; traz os três rótulos fixos com os três valores; termina com exatamente uma
      interrogação; não contém termo de oferta, desconto ou promoção; o único dado pessoal é
      o primeiro nome; a função não recebe nem lê catálogo (FR-010 a FR-014)
- [X] T030 [P] [US2] Unitário em
      `testes/unitarios/modulos/conversa/test_agendar_boas_vindas.py` com falsos: três slots
      válidos → insere mensagem pendente, enfileira e devolve `agendada`; slot ausente ou
      inválido → **nada gravado** e devolve `nao_enviada_slot_ausente`; `IntegrityError` do
      índice → devolve `ja_agendada` sem propagar a exceção (FR-006, FR-009, FR-030)
- [X] T031 [P] [US2] Estender `testes/unitarios/adaptadores/test_mensageria_falsa.py`:
      `enviar_boas_vindas` registra `tipo="boas_vindas"` e as quatro variáveis na ordem;
      `falhar_sempre` levanta `FalhaDeEnvio` (FR-015)
- [X] T032 [US2] Integração em `testes/integracao/test_boas_vindas_envio.py`: confirmar →
      1 trabalho `pendente` + 1 mensagem `pendente`; `processar_uma_passagem` → mensagem
      `enviada` com `enviada_em` e `id_externo`, trabalho `concluido`, gateway recebeu as
      quatro variáveis; com gateway que falha, o trabalho reagenda e a reserva **permanece**
      hospedada com `checkin_em` intacto (FR-007, FR-016)
- [X] T033 [US2] Integração no mesmo arquivo: confirmação com slot ausente → `200` com
      `boas_vindas: "nao_enviada_slot_ausente"`, `hospedado` gravado, zero mensagens e zero
      trabalhos; segunda tentativa sequencial de agendar para reserva que já tem trabalho →
      a violação do índice é tratada como `ja_agendada` (já enviado), sem erro propagado ao
      chamador e sem segunda mensagem (FR-008, FR-030). Não é teste de concorrência: T003
      prova que a restrição dispara; este prova o comportamento da aplicação diante dela

### Implementation for User Story 2

- [X] T034 [US2] Implementar `montar_texto_boas_vindas` em
      `app/modulos/conversa/texto_boas_vindas.py` na estrutura do contrato (rótulo fixo antes
      de cada variável, convite único ao final). T029 verde
- [X] T035 [US2] Implementar `agendar_boas_vindas` em
      `app/modulos/conversa/service.py`: lê as três chaves com `id_hotel`, reusa a validação
      da propriedade, grava a mensagem pendente e insere o trabalho dentro de
      `conexao.begin_nested()`, tratando `IntegrityError`. Logs conforme o contrato. T030
      verde
- [X] T036 [US2] Implementar `processar_trabalho_enviar_boas_vindas` em
      `app/modulos/conversa/service.py` (lê os slots, monta a tupla de variáveis, delega ao
      padrão de envio existente; slot inválido no envio → falha com código `slot_invalido`) e
      acrescentar o ramo `enviar_boas_vindas` em `worker/consumidor.py`. T032 verde
- [X] T037 [US2] Ligar `agendar_boas_vindas` em
      `app/modulos/hospedagem/service.confirmar_chegada` (parâmetro injetável) e devolver o
      desfecho no campo `boas_vindas` da resposta. T033 verde

**Checkpoint**: o hóspede recebe o recado curto, uma vez, e a falha de envio não desfaz o
check-in.

---

## Phase 7: User Story 4 - Destacar quem deveria ter chegado (Priority: P1)

**Goal**: a fila do dia distingue clique esquecido (`chegada_nao_confirmada`) de recado que
não saiu (`boas_vindas_nao_enviadas`), e a confirmação apaga o primeiro destaque.

**Independent Test**: quatro reservas na fila (atrasada sem confirmação, do dia sem
confirmação, hospedada com pacote, hospedada sem pacote) → cada uma com a combinação
esperada das duas colunas; nenhuma com as duas `true`.

### Tests for User Story 4 ⚠️

- [X] T038 [P] [US4] Estender `testes/integracao/test_fila_do_dia.py` com os quatro casos
      acima, incluindo a asserção de que as duas sinalizações nunca são `true` no mesmo item
      (FR-017, FR-019, FR-030)
- [X] T039 [P] [US4] Integração em `testes/integracao/test_confirmar_chegada.py`: reserva
      atrasada destacada → confirmar → a consulta seguinte não a traz mais como chegada não
      confirmada (FR-018)

### Implementation for User Story 4

- [X] T040 [US4] Expor `boas_vindas_nao_enviadas` no `SELECT` de
      `listar_fila_do_hotel` (`app/modulos/hospedagem/repository.py`) e no mapeamento de
      `listar_fila_do_dia` (`service.py`), consumindo a coluna criada na T005. T038 e T039
      verdes

**Checkpoint**: as duas omissões possíveis desta fatia são visíveis e distinguíveis.

---

## Phase 8: User Story 5 - Isolar a confirmação por hotel e por perfil (Priority: P1)

**Goal**: só a recepção do próprio hotel confirma; gestão e operação recebem `403`; reserva
alheia responde `404` sem revelar existência.

**Independent Test**: gestão e `staff` no próprio hotel → `403`; recepção do hotel B no id do
hotel A → `404` e status inalterado; sem cookie → `401` nas três rotas novas.

### Tests for User Story 5 ⚠️

- [X] T041 [P] [US5] Integração em `testes/integracao/test_confirmar_chegada.py`: cookie de
      gestão e cookie de `staff` → `403` no `POST` de chegada, sem alterar status (FR-021)
- [X] T042 [P] [US5] Integração no mesmo arquivo: recepção do hotel B no id de reserva do
      hotel A → `404` (não `403`, não `409`), status e `checkin_em` inalterados; zero
      trabalhos criados (FR-020, FR-022)
- [X] T043 [P] [US5] Conferir `testes/integracao/test_rotas_protegidas.py` com as três rotas
      novas registradas: cada uma exige `401` sem cookie. **Não** editar `ROTAS_PUBLICAS`

### Implementation for User Story 5

- [X] T044 [US5] Revisar `id_hotel` em todo SQL novo (`hospedagem/repository.py`,
      `propriedade/repository.py`) e a `exigir_operacao` de cada rota nova. T041–T043 verdes
      — se a recusa já nasceu nas fases anteriores, só fechar os testes

**Checkpoint**: multi-tenant e matriz exercitados nas três rotas novas.

---

## Phase 9: User Story 7 - Recuperar as boas-vindas recentes (Priority: P2)

**Goal**: completados os slots, a passagem seguinte envia para quem está hospedado com check-in
dentro da janela de validade configurada — e só para esses. A janela conta do `checkin_em`,
nunca de data de calendário.

**Independent Test**: duas reservas hospedadas sem pacote (check-in de 40 minutos atrás e de
três dias atrás) → completar os slots → uma passagem → só a recente recebe exatamente um
pacote; a antiga continua sinalizada e sem envio. Com o relógio posicionado depois da
meia-noite, a reserva cujo check-in foi 23h30 do dia anterior **continua** recebendo.

### Tests for User Story 7 ⚠️

- [X] T045 [P] [US7] Unitário em `testes/unitarios/worker/test_recuperar_boas_vindas.py`:
      elegível apenas `hospedado` + `checkin_em` preenchido + dentro da janela + sem trabalho;
      `checkin_em` anterior à janela não agenda; `hospedado` sem `checkin_em` não agenda; slot
      ainda inválido não agenda e a reserva permanece candidata; prazo ausente ou não inteiro
      positivo pula o hotel com log `prazo_ausente` e **não** supõe 12; segunda passagem não
      agenda de novo (FR-031, FR-031b, FR-032, FR-032a)
- [X] T046 [P] [US7] Unitário no mesmo arquivo — **teste da virada de dia**: reserva com
      `data_checkin_prevista` do dia anterior e `checkin_em` 35 minutos atrás, com `agora`
      posicionado às 00h05; a reserva **é** elegível e recebe pacote. Complemento no mesmo
      teste: reserva com `data_checkin_prevista` de hoje e `checkin_em` de 13 horas atrás
      **não** é elegível. O par prova que o eixo é o instante, não o calendário (FR-031a,
      SC-016a)
- [X] T047 [P] [US7] Estender `testes/unitarios/worker/test_cli_worker.py`:
      `--verificar-boas-vindas` executa a varredura uma vez e encerra, sem entrar no laço
- [X] T048 [US7] Integração em `testes/integracao/test_boas_vindas_envio.py`: o cenário das
      duas reservas descrito acima (gravando `checkin_em` com deslocamento explícito), com
      contagem de mensagens por reserva e verificação de que a antiga mantém
      `boas_vindas_nao_enviadas: true` na fila (SC-016)

### Implementation for User Story 7

- [X] T049 [US7] Implementar `listar_hospedados_sem_boas_vindas` em
      `app/modulos/hospedagem/repository.py` (`status = 'hospedado'`,
      `checkin_em IS NOT NULL`, `NOT EXISTS` do trabalho, devolvendo `checkin_em`) e o
      encaminhamento em `service.py`. **Sem** filtro de data no SQL — a janela é por
      propriedade ([data-model.md](./data-model.md))
- [X] T050 [US7] Implementar `verificar_boas_vindas_pendentes` em `worker/agendador.py` com
      parâmetro `agora` (instante ou callable, como em `verificar_cadastros_pendentes`), cache
      de `horas_validade_boas_vindas` por hotel reusando `_inteiro_positivo`, descarte do que
      está fora da janela e log `boas_vindas_recuperadas`. T045 e T046 verdes
      ([contracts/agendador-de-recuperacao.md](./contracts/agendador-de-recuperacao.md))
- [X] T051 [US7] Acrescentar `--verificar-boas-vindas` em `worker/__main__.py` e incluir a
      varredura no mesmo ciclo horário da verificação de cadastros — **sem** intervalo novo e
      sem parâmetro de periodicidade novo. T047 e T048 verdes

**Checkpoint**: a falha por slot vazio é recuperável enquanto o hóspede acabou de chegar, e a
virada da meia-noite não engole ninguém.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: log, fronteiras, documentação e roteiro manual

- [X] T052 [P] Estender `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py`: os
      eventos de boas-vindas (agendada, bloqueada, já agendada, enviada, recuperada) registram
      identificadores e, no caso de bloqueio, o **nome** da chave — e nunca conteúdo de
      mensagem, valor de slot, nome do hóspede ou telefone (FR-023)
- [X] T053 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F2.2 concluída com a revisão
      `0008_confirmar_chegada`, as quatro chaves novas na lista de parâmetros e as duas
      operações novas na matriz; apontar F2.3 como próxima fatia do backlog
- [X] T054 Revisar fronteiras: `conversa` não escreve em `reserva`, `hospedagem` não escreve
      em `mensagem`, SQL de `trabalho` só em `app/fila/repository.py`, e nenhum módulo lê
      `catalogo_item` neste fluxo
- [X] T055 Rodar [quickstart.md](./quickstart.md) inteiro, mais `pytest testes/unitarios -q`
      e a integração desta fatia (`test_confirmar_chegada.py`,
      `test_boas_vindas_slots.py`, `test_boas_vindas_envio.py`, `test_bootstrap.py`,
      `test_fila_do_dia.py`, `test_garantias_do_banco.py`, `test_conformidade_do_esquema.py`,
      `test_rotas_protegidas.py`). Tudo verde, sem rede

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: após Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: após Foundational — MVP
- **US3 (Phase 4)**: após US1 (mesma rota, mesmo serviço)
- **US6 (Phase 5)**: após Foundational; independente de US1 e US3
- **US2 (Phase 6)**: após US1 e US6 — precisa do clique e dos slots
- **US4 (Phase 7)**: após US2 (a coluna deriva da existência do trabalho)
- **US5 (Phase 8)**: após as três rotas existirem (US1, US6)
- **US7 (Phase 9)**: após US2 (reusa `agendar_boas_vindas`)
- **Polish (Phase 10)**: após as histórias desejadas

### Within Each User Story

1. Testes escritos e **vermelhos pelo motivo certo**
2. Implementação mínima
3. Verde
4. Só então a próxima história

### Parallel Opportunities

- T001 e T002 em paralelo
- T009–T012 em paralelo depois de T008
- T013 em paralelo com a preparação de T014
- T018–T020 em paralelo na US3
- T022 e T023 em paralelo na US6
- T029–T031 em paralelo na US2
- T038 e T039 em paralelo na US4
- T041–T043 em paralelo na US5
- T045–T047 em paralelo na US7
- T052 e T053 em paralelo no polish

**Sequência obrigatória em Foundational**: T003 → T004 → T005 → T006. Ver a conformidade
vermelha entre T004 e T006 é a única prova de que ela vigia o documento.

---

## Parallel Example: User Story 2

```text
# Testes em paralelo (antes da implementação):
T029 test_texto_boas_vindas.py       (montagem pura)
T030 test_agendar_boas_vindas.py     (decisão, com falsos)
T031 test_mensageria_falsa.py        (porta)

# Depois, implementação na ordem:
T034 → T035 → T036 → T037
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: `POST /reservas/{id}/chegada` → `hospedado` com `checkin_em`
4. Demo: curl da recepção confirma uma chegada; a fila deixa de destacá-la

### Incremental Delivery

1. US1 → o clique de fronteira existe
2. US3 → recusas fecham a máquina de estados
3. US6 → a propriedade tem o que dizer
4. US2 → o hóspede recebe o recado, uma vez
5. US4 → as duas omissões ficam visíveis
6. US5 → hotel e perfil
7. US7 → recuperação dentro da janela de validade
8. Polish → log, fronteiras, estado do projeto, quickstart

### Suggested MVP scope

**Só US1** (T001–T017) prova "a chegada passou a ser registrada". Mas **US3, US6, US2, US4 e
US5 são aceite obrigatório da spec** antes de marcar F2.2 concluída — o valor da fatia para o
hóspede está na US2, e ela depende da US6. US7 (P2) é a única que poderia ficar para uma segunda
entrega sem quebrar o critério de pronto; **a decisão foi mantê-la nesta entrega**, porque sem
ela slot vazio significa hóspede que nunca recebe nada, e a sinalização na fila seria a única
saída.

---

## Notes

- [P] = arquivos distintos, sem depender de tarefa incompleta da mesma sequência
- Sem React, sem checkout, sem envio manual para reserva fora da janela, sem confirmação em
  lote, sem inferência por mensagem recebida
- `id_hotel` só da sessão; `parametro_hotel` alcançado pelas quatro chaves novas — os três
  slots pela rota e permissão da recepção; `horas_validade_boas_vindas` só lida pelo worker,
  fora da permissão da recepção
- Nenhum teste chama `MensageriaWhatsapp`
- Commit por tarefa ou grupo lógico **só se o usuário pedir commit**
- Evitar: variável de template vazia; verificação de unicidade em código no lugar do índice;
  desfazer o check-in por falha de envio; conteúdo de mensagem ou valor de slot em log
