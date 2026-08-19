---
description: "Task list for feature implementation"
---

# Tasks: Consumo Faturável e Fila de Lançamento

**Input**: Design documents from `/specs/016-consumo-faturavel/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de produção
antes de um teste que falhe pela ausência dela, e pelo motivo certo.

**Organization**: Tarefas agrupadas por história (US1–US14), na ordem da spec.
Esquema (`item_vendavel` + triggers + CHECK + visão), porta de identificação,
recados puros, `abrir_consumo` e CRUD interno do item **sem HTTP** entram na
Foundational. O corte que **liga** o fork no processador já existente
(`registrar_pedido_servico`) fica na US1. **Não** nasce tipo novo na fila.
`lancar_consumo` já está na matriz — esta fatia só liga as rotas (US3/US13).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US14)

## Como ver os testes falharem nesta fatia

**Esquema.** `testes/integracao/test_conformidade_do_esquema.py` compara o banco
migrado com `docs/04-schema.sql`. Editar o documento **antes** da revisão deixa a
conformidade vermelha apontando `item_vendavel` / triggers / desfechos da visão.
A revisão `0015` a devolve ao verde.

**Recado / porta.** Função pura e `AttributeError` no protocolo: o teste falha
até o módulo/método existir.

**Fork no processador.** Hoje `processar_trabalho_registrar_pedido` sempre chama
`abrir_servico` e **não** chama LLM. Os testes da US1 ficam vermelhos até o fork
existir. Os testes da F3.4 de toalha **permanecem** (caminho `nenhum`).

**F3.6.** `testes/integracao/test_resolver_chamado.py` espera `409` em tipo
`consumo`. A US10 **inverte** esse teste — não é regressão, é a fatia.

**HTTP.** Hoje não existem `/itens-vendaveis`, `/consumos/pendentes` nem
`POST .../lancamento`. A integração falha com `404` de rota até o roteador
existir.

---

## Phase 1: Setup

**Purpose**: helpers do consumo, sem repetir payload e textos de recusa em cada
arquivo

- [X] T001 [P] Criar `testes/suporte/consumo.py` com constantes estáveis:
      nome de item (`Cerveja`), `preco_atual` `12.00`, detalhe `409` já lançado
      (`Este consumo ja foi lancado.`), já dispensado (`Este consumo ja foi
      dispensado.`), `404` de solicitação (`Solicitacao nao encontrada.`),
      `404` de item (`Item vendavel nao encontrado.`), `409` de nome duplicado,
      e `proibicoes_do_recado_consumo()` (palavras `extrato`, `conta`, afirmação
      de lançamento já ocorrido). Sem segredo, sem rede
- [X] T002 [P] Em `testes/suporte/pedido_servico.py`, documentar no docstring
      que F3.7 faz fork no mesmo trabalho `registrar_pedido_servico`: item
      vendável único → consumo; nenhum → serviço da F3.4. Sem mudar textos de
      toalha nem eixos

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: tabela `item_vendavel`, triggers de especialização e de lançamento,
CHECK de autor no terminal, desfechos na visão, porta
`identificar_item_vendavel`, `LLMFalso` configurável, recados puros,
repositório/serviço de item (sem HTTP) e `abrir_consumo` (sem HTTP, sem envio).
O processador da F3.4 **ainda não** identifica. **Nenhuma rota HTTP nova.**

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. Ordem do esquema:
T003 → T004 → T006 → T007 (teste vermelho no documento, depois migração verde).

- [X] T003 Estender `testes/integracao/test_garantias_do_banco.py`: `INSERT` em
      `item_vendavel` com preço >= 0 aceito; preço negativo recusado; segundo
      item ativo com o mesmo nome (casefold) no mesmo hotel viola
      `uq_item_vendavel_hotel_nome_ativo`; `INSERT` em `consumo` cujo pai é
      tipo `servico` recusado; `INSERT` tipo `consumo` **sem** filho falha no
      commit (constraint deferrable); pai `consumo` + filho na mesma transação
      aceito; `lancado`/`dispensado` sem autor ou sem instante recusados;
      `pendente` → `lancado` e `pendente` → `dispensado` aceitos; `lancado` →
      `pendente` recusado. Rodar e **ver falhar** (FR-003, FR-004, FR-013,
      FR-017, [data-model.md](./data-model.md))
- [X] T004 Aplicar o delta em `docs/04-schema.sql`: `CREATE TABLE
      item_vendavel` + índices; substituir `ck_consumo_lancado_tem_autor` por
      `ck_consumo_terminal_tem_autor`; triggers
      `fn_consumo_pai_tipo_consumo`, `fn_solicitacao_consumo_tem_filho`
      (DEFERRABLE) e `fn_valida_transicao_lancamento`; `vw_fila_do_dia` com
      `item_ambiguo` e `identificacao_indisponivel` no `IN` de
      `precisa_atendimento_humano`. **Não** alterar `ck_trabalho_tipo`. Rodar
      `testes/integracao/test_conformidade_do_esquema.py` e **ver falhar** pela
      divergência
- [X] T005 [P] Alinhar `docs/04-modelagem-de-dados.md`: `item_vendavel`;
      `consumo` deixa de ser tabela morta; valor praticado é retrato; máquina
      `pendente` → `lancado`/`dispensado`; identificação não emite preço;
      desfechos humanos novos. Não dizer que todo `pedido_de_servico` é serviço
      sem cobrança
- [X] T006 Criar `alembic/versions/sql/0015_consumo_faturavel.sql` — cópia
      congelada do delta da T004
- [X] T007 Criar `alembic/versions/0015_consumo_faturavel.py`
      (`down_revision = "0014_resolver_chamado"`), `upgrade` executa o SQL
      congelado, `downgrade` remove triggers/CHECK/tabela e restaura a visão
      da `0014`. T003 e a conformidade verdes
- [X] T008 [P] Unitário em `testes/unitarios/portas/test_identificar_item.py`
      (criar): `ResultadoIdentificacao` com `desfecho` `unico`/`nenhum`/
      `ambiguo`; `FalhaDeIdentificacao(codigo)` sem eco de texto. **Ver falhar**
      ([contracts/identificacao-e-preco.md](./contracts/identificacao-e-preco.md))
- [X] T009 Acrescentar `FalhaDeIdentificacao`, `ResultadoIdentificacao` e
      `identificar_item_vendavel` em `app/portas/llm.py`. T008 verde. **Não**
      mudar `classificar` nem `responder_duvida`
- [X] T010 [P] Estender `testes/unitarios/adaptadores/test_llm_falso.py`:
      `configurar_identificacao` / `falhar_identificacao`; lista vazia **não** é
      responsabilidade do falso (o serviço não chama); `unico` devolve id+quantidade;
      `ambiguo` e `FalhaDeIdentificacao` configuráveis; `chamadas_identificar`
      registra `(texto, itens)` — o teste **não** lê o texto em log de produção.
      **Ver falhar**
- [X] T011 Implementar o método e a configuração em
      `app/adaptadores/llm_falso.py`. T010 verde. Padrão: se não configurado e
      houver itens, **não** casar o primeiro por acidente — devolver `nenhum`
      (protege a F3.4)
- [X] T012 [P] Unitário em
      `testes/unitarios/modulos/conversa/test_texto_confirmacao_consumo.py`:
      `montar_confirmacao_consumo` usa prenome, cita `descricao_item`, formata
      `R$ 12,00`, afirma que a equipe vai atender, **não** contém as proibições
      de T001. **Ver falhar** (FR-007,
      [contracts/mensageria-sessao.md](./contracts/mensageria-sessao.md))
- [X] T013 Implementar `montar_confirmacao_consumo` em
      `app/modulos/conversa/texto_confirmacao_consumo.py` (função pura,
      `Decimal`, nunca `float`). T012 verde
- [X] T014 [P] Unitário em
      `testes/unitarios/modulos/conversa/test_texto_aviso_identificacao.py`:
      `montar_aviso_identificacao` usa prenome, diz que a recepção vai conferir,
      **sem** valor e **sem** as proibições de T001. **Ver falhar** (FR-006)
- [X] T015 Implementar `montar_aviso_identificacao` em
      `app/modulos/conversa/texto_aviso_identificacao.py`. T014 verde
- [X] T016 [P] Unitário em
      `testes/unitarios/modulos/propriedade/test_item_vendavel.py`:
      `criar_item_vendavel` / `listar_ativos` / `listar_manutencao` /
      `atualizar_item_vendavel` no hotel da sessão; `listar_ativos` devolve
      tupla `(id, nome)` **sem** preço; inativo não entra em ativos; hotel B
      não vê A; preço negativo e nome vazio recusados. **Ver falhar** (FR-017).
      Depende de T007
- [X] T017 Implementar repositório e serviço em
      `app/modulos/propriedade/repository.py`,
      `app/modulos/propriedade/service.py` e
      `app/modulos/propriedade/schema.py` (sem HTTP, sem LLM). T016 verde
- [X] T018 [P] Unitário em
      `testes/unitarios/modulos/atendimento/test_abrir_consumo.py`:
      `abrir_consumo` insere `solicitacao` tipo `consumo` + filho `pendente`
      com `valor_praticado` e `descricao_item` informados, quarto extraído ou
      nulo, urgência copiada, **sem** autor de lançamento; reserva de outro
      hotel não insere. **Ver falhar** (FR-002, FR-004). Depende de T007
- [X] T019 Implementar `inserir_consumo` em
      `app/modulos/atendimento/repository.py` e `abrir_consumo` em
      `app/modulos/atendimento/service.py` (exceção `HotelIncompativel` já
      existente). Sem HTTP. Sem mensageria. T018 verde

**Checkpoint**: dá para cadastrar item, abrir consumo e montar recados. Worker
ainda trata todo pedido como serviço da F3.4. Sem rotas novas.

---

## Phase 3: User Story 1 - Pedido cobrado nasce pendente (Priority: P1) 🎯 MVP

**Goal**: identificação `unico` no processador `registrar_pedido_servico`
grava confirmação com valor, `solicitacao` tipo `consumo` e filho `pendente`.

**Independent Test**: item ativo + falso `unico` + mensagem `pedido_de_servico`
→ uma enviada com `R$ 12,00`, um `consumo` pendente com o mesmo valor, JSON
`resposta = confirmacao_consumo`, `precisa_atendimento_humano = false`.

### Tests for User Story 1 ⚠️

- [X] T020 [P] [US1] Unitário em
      `testes/unitarios/modulos/conversa/test_registrar_consumo.py` (criar):
      processador com identificador espião `unico`, `listar_ativos` com um
      item, `abrir_consumo` espião — chama identificar **com ids e nomes, sem
      preço**; lê preço uma vez; INSERT enviada com recado da T013 **antes**
      de `abrir_consumo`; JSON `confirmacao_consumo`; **não** chama
      `abrir_servico`. Lista vazia **não** chama a porta. **Ver falhar**
      (FR-001, FR-003, FR-005, FR-007, FR-008) — hoje o processador só abre
      serviço
- [X] T021 [P] [US1] Integração em
      `testes/integracao/test_registrar_consumo.py` (criar): semear item via
      serviço da T017, configurar `LLMFalso` `unico`, webhook
      `pedido_de_servico`, `python -m worker --uma-passagem` → `tipo=consumo`,
      `valor_praticado=12.00`, `status_lancamento=pendente`, enviada com valor,
      fila do dia com flag falso, `reserva.status` intocado. **Ver falhar**
      (SC-001)

### Implementation for User Story 1

- [X] T022 [US1] Estender `processar_trabalho_registrar_pedido` em
      `app/modulos/conversa/service.py` com colaboradores injetados
      (`listar_itens_ativos`, `identificar`, `abrir_consumo`, default reais no
      worker). Validar `ResultadoIdentificacao` no domínio (id ∈ tupla,
      quantidade >= 1). Em `worker/consumidor.py`, injetar os três. **Não**
      criar tipo novo de trabalho. T020 e T021 verdes. Caminho `nenhum` /
      humano ainda pode ficar para US6/US9 se o default for `nenhum` quando a
      porta não casa — toalha da F3.4 não pode quebrar

**Checkpoint**: cerveja cadastrada vira consumo pendente. Toalha sem item ativo
continua serviço (padrão do falso = `nenhum`).

---

## Phase 4: User Story 2 - Confirmação antes de tramitar (Priority: P1)

**Goal**: na transação, a enviada com valor existe **antes** de `abrir_consumo`;
o recado não afirma lançamento.

**Independent Test**: espião de `abrir_consumo` observa que a enviada já está
gravada; o corpo é o recado da T013.

### Tests for User Story 2 ⚠️

- [X] T023 [P] [US2] Em
      `testes/unitarios/modulos/conversa/test_registrar_consumo.py`: o espião
      verifica enviada presente no instante da chamada; se `abrir_consumo`
      levantar, a transação não deixa consumo órfão sem enviada; o corpo não
      contém as proibições de T001. **Ver falhar** (FR-007, FR-008, SC-002)

### Implementation for User Story 2

- [X] T024 [US2] Garantir a ordem em `processar_trabalho_registrar_pedido` (
      `app/modulos/conversa/service.py`): identificar → ler preço → INSERT
      enviada → `abrir_consumo` → JSON → envio. T023 verde — se T022 já
      ordenava, esta tarefa é o teste de ordem e o ajuste se o serviço abria
      consumo primeiro

**Checkpoint**: zero consumos tramitam sem confirmação gravada com o mesmo valor.

---

## Phase 5: User Story 3 - Recepção marca como lançado (Priority: P1)

**Goal**: `POST /solicitacoes/{id}/lancamento` (só recepção) grava autor e
instante, tira da pendência, recusa o segundo clique.

**Independent Test**: recepção POST num pendente → `200` com
`status_lancamento=lancado`, autor e instante; segundo POST `409`; valor
intocado.

### Tests for User Story 3 ⚠️

- [X] T025 [P] [US3] Unitário em
      `testes/unitarios/modulos/atendimento/test_lancar.py` (criar): `lancar`
      preenche autor/instante quando o UPDATE acha `pendente` do hotel;
      já terminal → `LancamentoNaoPermitido`; outro hotel / não consumo →
      `SolicitacaoNaoEncontrada`; valor não muda. **Ver falhar** (FR-010,
      FR-011, FR-013)
- [X] T026 [P] [US3] Integração em
      `testes/integracao/test_consumos_pendentes.py` (criar): login recepção,
      POST `/solicitacoes/{id}/lancamento` → `200` no contrato de
      [contracts/api-de-atendimento.md](./contracts/api-de-atendimento.md);
      segundo POST `409` com detalhe de T001. **Ver falhar** (rota inexistente)
      (SC-005)

### Implementation for User Story 3

- [X] T027 [US3] Implementar `lancar` em
      `app/modulos/atendimento/service.py` e `repository.py` (`UPDATE`
      condicional via `JOIN reserva`, relógio injetável). Schema
      `LancamentoResposta` em `app/modulos/atendimento/schema.py`. Rota POST
      em `app/modulos/atendimento/router.py` com
      `exigir_operacao("lancar_consumo")`. Mapear 404/409. Sem mensageria.
      T025 e T026 verdes

**Checkpoint**: o clique financeiro existe. Staff/gestão (US7) e dispensa
(US13) ainda não são o foco. Fila HTTP destacada é a US4.

---

## Phase 6: User Story 4 - Fila destacada na passagem de turno (Priority: P1)

**Goal**: `GET /consumos/pendentes` lista só `pendente`, inclusive já resolvido
no quarto; toalha não aparece.

**Independent Test**: um consumo pendente, um serviço aberto e um consumo
lançado → a lista tem só o pendente; hotel B não o vê.

### Tests for User Story 4 ⚠️

- [X] T028 [P] [US4] Unitário em
      `testes/unitarios/modulos/atendimento/test_listar_pendentes.py` (criar):
      `listar_pendentes` devolve só `status_lancamento=pendente` do hotel,
      com valor e `descricao_item`, **sem** nome/telefone; serviço não entra;
      lançado não entra. **Ver falhar** (FR-009, FR-015)
- [X] T029 [P] [US4] Integração em
      `testes/integracao/test_consumos_pendentes.py`: GET
      `/consumos/pendentes` (recepção) 200 no contrato; item lançado some
      depois da US3; toalha da F3.4 ausente. **Ver falhar** (SC-003, SC-004)

### Implementation for User Story 4

- [X] T030 [US4] Implementar `listar_pendentes` no repositório/serviço e GET
      `/consumos/pendentes` em `app/modulos/atendimento/router.py` com
      `exigir_operacao("ler_solicitacao_atribuida")`. Estender
      `ItemSolicitacao` em `app/modulos/atendimento/schema.py` com
      `valor_praticado` e `status_lancamento` (nulos em reclamação/serviço) e
      o JOIN correspondente em `listar_abertas`. T028 e T029 verdes. Testes
      da F3.4/F3.5 de GET que não esperavam as chaves: aceitar nulos — ajustar
      `testes/integracao/test_solicitacoes.py` se o modelo Pydantic quebrar

**Checkpoint**: passagem de turno financeira é uma lista distinta.

---

## Phase 7: User Story 5 - Reajuste não reescreve histórico (Priority: P1)

**Goal**: mudar `preco_atual` não altera `valor_praticado` já gravado; pedido
novo usa o preço novo.

**Independent Test**: consumo a 12; PATCH/serviço a 20; o consumo continua 12;
novo `unico` nasce 20.

### Tests for User Story 5 ⚠️

- [X] T031 [P] [US5] Integração em `test_registrar_consumo.py`: após T021,
      `atualizar_item_vendavel` para `20.00`; `SELECT valor_praticado` do
      primeiro consumo = `12.00`; segundo webhook+worker → `20.00`. **Ver
      falhar** se houver FK viva ou UPDATE em cascata (FR-003, SC-006)

### Implementation for User Story 5

- [X] T032 [US5] Confirmar em `docs/04-schema.sql` e
      `alembic/versions/sql/0015_consumo_faturavel.sql` a ausência de FK
      `consumo → item_vendavel` e de trigger que copie preço. Se T017/T019 já
      gravam retrato, T031 verde sem código novo — **não** “corrigir” ligando
      o valor ao preço atual

**Checkpoint**: histórico de cobrança não acompanha tabela.

---

## Phase 8: User Story 6 - Serviço sem cobrança fora da fila (Priority: P1)

**Goal**: identificação `nenhum` (ou lista vazia) permanece F3.4: tipo
`servico`, zero `consumo`, ausente de `/consumos/pendentes`.

**Independent Test**: toalha extra sem item ativo → confirmação sem preço,
`GET /consumos/pendentes` vazio para aquele id.

### Tests for User Story 6 ⚠️

- [X] T033 [P] [US6] Estender
      `testes/unitarios/modulos/conversa/test_registrar_pedido.py`: lista vazia
      ou identificador `nenhum` → `abrir_servico`, **não** `abrir_consumo`,
      porta **não** chamada se a lista for vazia. **Ver falhar** se o fork
      da US1 tiver quebrado a toalha (FR-005)
- [X] T034 [P] [US6] Estender `testes/integracao/test_registrar_pedido.py`:
      toalha continua sem `consumo` e não aparece em GET
      `/consumos/pendentes`. **Ver falhar** (SC-003)

### Implementation for User Story 6

- [X] T035 [US6] No processador (`app/modulos/conversa/service.py`), ramo
      `nenhum` = caminho F3.4 inalterado. T033 e T034 verdes

**Checkpoint**: toalha não entra na fila de lançamento.

---

## Phase 9: User Story 7 - Staff entrega; só recepção lança (Priority: P1)

**Goal**: staff vê consumo em `GET /solicitacoes` com valor, sem ficha, e toma
`403` no POST de lançamento; gestão vê pendências e toma `403` ao lançar;
hotel B `404`.

**Independent Test**: os três perfis no consumo pendente de A; B não o vê.

### Tests for User Story 7 ⚠️

- [X] T036 [P] [US7] Integração em `test_consumos_pendentes.py` e
      `test_solicitacoes.py`: staff GET `/solicitacoes` tem
      `valor_praticado` e **não** tem nome/telefone; staff e gestão POST
      lançamento `403`; gestão GET `/consumos/pendentes` `200`; hotel B POST
      `404` uniforme; staff `GET /reservas/{id}/ficha` continua 403. **Ver
      falhar** (FR-014, FR-015, SC-007, SC-008, SC-009)

### Implementation for User Story 7

- [X] T037 [US7] Conferir `exigir_operacao("lancar_consumo")` no POST e
      `ler_solicitacao_atribuida` nos GETs em
      `app/modulos/atendimento/router.py`. Isolamento pelo hotel da sessão no
      `UPDATE`/`SELECT`. Sem operação nova na matriz
      (`app/modulos/acesso/politica.py` já tem `lancar_consumo`). T036 verde

**Checkpoint**: matriz da F0.3 exercida no lançamento.

---

## Phase 10: User Story 8 - Recepção mantém itens vendáveis (Priority: P1)

**Goal**: `POST`/`GET`/`PATCH /itens-vendaveis`; gestão lê e não altera; staff
recusado; desativar sai da identificação.

**Independent Test**: recepção cria Cerveja; gestão GET vê; gestão POST 403;
desativar → novo pedido não casa.

### Tests for User Story 8 ⚠️

- [X] T038 [P] [US8] Integração em
      `testes/integracao/test_item_vendavel.py` (criar): POST 201, GET
      manutenção (recepção e gestão), PATCH preço/ativo, nome duplicado 409,
      preço negativo 422, staff GET 403, gestão POST 403, hotel B 404/lista
      vazia — contrato
      [contracts/api-de-item-vendavel.md](./contracts/api-de-item-vendavel.md).
      **Ver falhar** (rota inexistente) (FR-017, SC-007)

### Implementation for User Story 8

- [X] T039 [US8] Rotas em `app/modulos/propriedade/router.py`:
      `POST /itens-vendaveis` e `PATCH` com `alterar_catalogo`; `GET` com
      `ler_catalogo`. Registrar o roteador em `app/main.py` se o prefixo novo
      precisar. T038 verde. Item inativo some de `listar_ativos` (já T017)

**Checkpoint**: a recepção consegue cadastrar o preço sem SQL.

---

## Phase 11: User Story 9 - Ambíguo ou IA caída não inventa preço (Priority: P1)

**Goal**: `ambiguo` / `FalhaDeIdentificacao` / formato inválido → aviso sem
valor, zero consumo, `precisa_atendimento_humano`, trabalho `concluido`.

**Independent Test**: falso `ambiguo` ou `falhar_identificacao` → flag na fila
do dia, nenhuma confirmacao com `R$`.

### Tests for User Story 9 ⚠️

- [X] T040 [P] [US9] Unitário em
      `testes/unitarios/modulos/conversa/test_registrar_consumo.py`:
      identificador `ambiguo` ou exceção → `montar_aviso_identificacao`,
      **não** `abrir_consumo` nem `abrir_servico`, JSON `item_ambiguo` ou
      `identificacao_indisponivel`, id fora da tupla / quantidade < 1 tratado
      como falha. **Ver falhar** (FR-006)
- [X] T041 [P] [US9] Integração em
      `testes/integracao/test_registrar_consumo.py`: flag
      `precisa_atendimento_humano = true`; zero linha em `consumo`; enviada
      sem `R$`. **Ver falhar** (SC-013)

### Implementation for User Story 9

- [X] T042 [US9] Ramos humano no processador
      (`app/modulos/conversa/service.py`). Trabalho `concluido` (não copiar
      backoff de `interpretar_ficha`). T040 e T041 verdes. Visão já inclui os
      desfechos (T007)

**Checkpoint**: na dúvida, a recepção vê; o hóspede não leva preço inventado.

---

## Phase 12: User Story 10 - Entregar no quarto não é lançar (Priority: P1)

**Goal**: `POST .../resolucao` aceita tipo `consumo`; o lançamento permanece
`pendente`; recado de conclusão sem valor e sem “lançado”.

**Independent Test**: staff resolve o consumo → some de `GET /solicitacoes`,
permanece em `GET /consumos/pendentes`.

### Tests for User Story 10 ⚠️

- [X] T043 [P] [US10] **Inverter**
      `testes/integracao/test_resolver_chamado.py` (e o unitário
      `test_resolver.py` que recusa tipo consumo): POST resolução em consumo
      aberto → `200`; `status_lancamento` continua `pendente`; GET
      `/consumos/pendentes` ainda lista. Remover a asserção ao
      `DETALHE_TIPO_CONSUMO`. **Ver falhar** (FR-016, SC-010) — hoje é 409
- [X] T044 [P] [US10] Unitário em
      `testes/unitarios/modulos/conversa/test_texto_confirmacao_resolucao.py`:
      tipo `consumo` usa o espírito de pedido atendido; **não** cita valor,
      lançamento, `extrato` nem `conta`. **Ver falhar** se o recado só aceitar
      reclamação/serviço

### Implementation for User Story 10

- [X] T045 [US10] Em `app/modulos/atendimento/repository.py` /
      `service.py`, o `UPDATE` de resolver passa a admitir `tipo IN
      ('reclamacao','servico','consumo')`. Ajustar
      `montar_confirmacao_resolucao` em
      `app/modulos/conversa/texto_confirmacao_resolucao.py`. T043 e T044
      verdes. `DETALHE_TIPO_CONSUMO` em `testes/suporte/resolucao.py` deixa de
      ser usado no caminho feliz — pode permanecer como constante morta só até
      o polish limpar

**Checkpoint**: dois ciclos distintos (quarto vs PMS).

---

## Phase 13: User Story 11 - Reprocessar não duplica (Priority: P1)

**Goal**: a mesma mensagem gera no máximo uma confirmação e um consumo.

**Independent Test**: processar de novo o trabalho já concluído → zero segunda
enviada, zero segundo `consumo`.

### Tests for User Story 11 ⚠️

- [X] T046 [P] [US11] Unitário em
      `testes/unitarios/modulos/conversa/test_registrar_consumo.py`: JSON já
      com `resposta=confirmacao_consumo` e `id_solicitacao` → não chama
      identificar de novo, não chama `abrir_consumo`; unique de origem → trata
      como já registrado. **Ver falhar** (FR-018, SC-011)

### Implementation for User Story 11

- [X] T047 [US11] Guard no processador (`app/modulos/conversa/service.py`)
      espelhando `confirmacao_pedido`. T046 verde. Unique da F3.4 já cobre o
      banco (T003)

**Checkpoint**: retrabalho não cobra duas vezes.

---

## Phase 14: User Story 12 - Falha ao gravar ou enviar não perde o pedido (Priority: P1)

**Goal**: envio falho preserva consumo e enviada; gravação falha não envia
recado com valor.

**Independent Test**: gateway que falha após INSERT → pendência na fila;
`abrir_consumo` que levanta → zero enviada commitada.

### Tests for User Story 12 ⚠️

- [X] T048 [P] [US12] Unitário em
      `testes/unitarios/modulos/conversa/test_registrar_consumo.py`:
      mensageria falha depois de gravar → consumo permanece, trabalho
      reagendável, valor intocado; `abrir_consumo` falha → gateway **não** é
      chamado. **Ver falhar** (FR-019, FR-020, SC-012)

### Implementation for User Story 12

- [X] T049 [US12] Reusar o padrão de reagendar mensageria da F3.4 no ramo
      `unico` (`app/modulos/conversa/service.py`). T048 verde. Sem backoff de
      LLM neste ramo (humano já é US9)

**Checkpoint**: gravar antes de enviar vale no ramo cobrado.

---

## Phase 15: User Story 13 - Dispensar sem fingir lançamento (Priority: P2)

**Goal**: `POST .../dispensa` (recepção) tira da fila como `dispensado`, com
autor e instante; não é `lancado`; staff/gestão 403.

**Independent Test**: recepção dispensa → some de `/consumos/pendentes`;
`status_lancamento=dispensado`.

### Tests for User Story 13 ⚠️

- [X] T050 [P] [US13] Unitário em
      `testes/unitarios/modulos/atendimento/test_dispensar.py` (criar):
      `dispensar` análogo a `lancar`; já terminal recusa. **Ver falhar**
      (FR-012, FR-013)
- [X] T051 [P] [US13] Integração em `test_consumos_pendentes.py`: POST
      dispensa `200`; segundo clique `409`; gestão/staff `403`; não aparece
      como `lancado`. **Ver falhar** (rota inexistente)

### Implementation for User Story 13

- [X] T052 [US13] `dispensar` no serviço/repositório e POST
      `/solicitacoes/{id}/dispensa` no roteador, mesma
      `exigir_operacao("lancar_consumo")`. Sem recado ao hóspede. T050 e T051
      verdes

**Checkpoint**: cortesia não mente “lançado”.

---

## Phase 16: User Story 14 - Conteúdo não vaza em log (Priority: P2)

**Goal**: eventos de consumo/identificação/lançamento com ids e resultado; sem
texto do pedido nem da confirmação.

**Independent Test**: caplog nos desfechos feliz, humano, lançar, dispensar,
envio falho.

### Tests for User Story 14 ⚠️

- [X] T053 [P] [US14] Estender
      `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py` (e
      `test_lancar.py` / `test_dispensar.py` se o evento for em `atendimento`):
      eventos `consumo_registrado`, `consumo_ja_registrado`,
      `consumo_envio_falhou`, `identificacao_humana`, `consumo_lancado`,
      `consumo_dispensado` — sem conteúdo, sem recado, sem
      `valor_praticado` por extenso; há ids e `resultado`. **Ver falhar**
      (FR-021, SC-014)

### Implementation for User Story 14

- [X] T054 [US14] Logs em `app/modulos/conversa/service.py` e
      `app/modulos/atendimento/service.py` conforme
      [contracts/fila-e-worker.md](./contracts/fila-e-worker.md). T053 verde

**Checkpoint**: trilha técnica sem cópia da conversa nem do preço no recado.

---

## Phase 17: Polish & Cross-Cutting Concerns

**Purpose**: regressão F3.4–F3.6, fronteiras, documentação, suíte, quickstart

- [X] T055 [P] Regressão: `test_registrar_pedido.py`, `test_abrir_chamado.py`,
      `test_resolver_chamado.py` (reclamação/serviço), `test_solicitacoes.py`,
      `test_classificar_mensagem.py` e claims de outros tipos continuam verdes;
      classificar **não** identifica e **não** enfileira tipo novo; toalha não
      liga `precisa_atendimento_humano`
- [X] T056 [P] Limpar `DETALHE_TIPO_CONSUMO` de
      `testes/suporte/resolucao.py` se ninguém mais asserir 409 de tipo
- [X] T057 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F3.7
      andamento/concluída, revisão `0015`, `item_vendavel`, fork no
      `registrar_pedido_servico`, `GET /consumos/pendentes`, POST lançamento/
      dispensa, resolver consumo sem lançar, próxima fatia **F3.8** (pulso).
      Não apontar F2.3. Fechar o adiamento de preço estruturado da F2.1
- [X] T058 Revisar fronteiras: `conversa` não dá INSERT em `consumo`;
      `atendimento` não chama LLM nem mensageria; `propriedade` não abre
      consumo; SQL de `trabalho` só em `app/fila/`; preço fora do prompt;
      `id_hotel` em toda consulta; nenhum teste instancia adaptador WhatsApp
      real nem LLM real. Rodar [quickstart.md](./quickstart.md),
      `pytest testes/unitarios -q` e a integração desta fatia
      (`test_registrar_consumo.py`, `test_consumos_pendentes.py`,
      `test_item_vendavel.py`, `test_registrar_pedido.py`,
      `test_resolver_chamado.py`, `test_conformidade_do_esquema.py`,
      `test_garantias_do_banco.py`). Tudo verde, sem rede (SC-015)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: após Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: após Foundational — **é o corte do worker** (fork)
- **US2 (Phase 4)**: após US1 (ordem na mesma transação)
- **US3 (Phase 5)**: após US1 (precisa existir `consumo`)
- **US4 (Phase 6)**: após US1; US3 ajuda a testar “lançado some”
- **US5 (Phase 7)**: após US1 (e T017 para atualizar preço)
- **US6 (Phase 8)**: após US1 (ramo `nenhum`); US4 para asserir a fila
- **US7 (Phase 9)**: após US3 e US4 (POST + GETs)
- **US8 (Phase 10)**: após Foundational (HTTP sobre o serviço da T017); pode
  seguir em paralelo com US1 se o MVP semear item via serviço
- **US9 (Phase 11)**: após US1
- **US10 (Phase 12)**: após US1 e US4
- **US11 (Phase 13)**: após US1
- **US12 (Phase 14)**: após US1
- **US13 (Phase 15)**: após US3 (mesmo padrão de UPDATE)
- **US14 (Phase 16)**: após US1 (e de preferência US3/US9/US13 para os eventos)
- **Polish (Phase 17)**: após as histórias desejadas

### User Story Dependencies

- **US1**: após Phase 2 — sem dependência de outra história; **é o MVP cobrado**
- **US8**: após Phase 2 — independente de US1 se os testes da US1 semeiam item
  pelo serviço, não pelo HTTP
- **US3 / US4**: após US1
- **US6**: após US1 (não quebrar F3.4)
- **US10**: após US1; inverte teste da F3.6
- **US13**: após US3
- Demais: após US1, testáveis isoladamente

### Within Each User Story

1. Testes escritos e **vermelhos pelo motivo certo**
2. Implementação mínima
3. Verde
4. Próxima história (ou commit, se o usuário pedir)

### Parallel Opportunities

- T001 // T002
- T005 // T008 // T010 // T012 // T014 (depois de T007 para T016/T018)
- T016 // T018
- T020 // T021
- T025 // T026
- T028 // T029
- T033 // T034
- T040 // T041
- T043 // T044
- T050 // T051
- T055 // T056 // T057

---

## Parallel Example: User Story 1

```text
# Testes em paralelo (antes da implementação):
T020 test_registrar_consumo.py (unitário, espiões)
T021 test_registrar_consumo.py (integração worker)

# Depois:
T022 fork no processador + injeção no worker
```

## Parallel Example: User Story 3

```text
T025 test_lancar.py
T026 test_consumos_pendentes.py (POST)

# Depois:
T027 lancar + rota
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: pedido identificado vira consumo pendente com valor na confirmação
4. Demo: `SELECT` em `consumo` + enviada. Lançamento visível é a US3; fila
   destacada é a US4

### Incremental Delivery

1. US1 → consumo pendente + confirmação com valor
2. US2 → ordem confirmação → tramitação
3. US3 → clique de lançamento
4. US4 → fila destacada
5. US5 → retrato de preço
6. US6 → toalha fora da fila
7. US7 → matriz
8. US8 → manutenção HTTP do item
9. US9 → humano sem preço inventado
10. US10 → resolver quarto ≠ lançar
11. US11 / US12 → idempotência e gravar-antes-de-enviar
12. US13 → dispensar
13. US14 → log limpo
14. Polish → estado do projeto / quickstart / regressão

### Suggested MVP scope

**US1** (T001–T022) prova o valor financeiro (nasce pendente com preço do
banco). **US3 e US4 são aceite obrigatório** antes de marcar F3.7 concluída
(clique de lançamento + fila visível — critérios do backlog). **US6** protege
a F3.4. **US8** é o que torna o preço configurável sem SQL. **US9** é Artigo
II. **US10** fecha o ciclo operacional que a F3.6 adiou. US13 e US14 são P2 e
entram nesta entrega no padrão das fatias anteriores.

---

## Notes

- [P] = arquivos distintos, sem depender de tarefa incompleta da mesma sequência
- Sem React, sem `GET /solicitacoes/{id}`, sem tipo novo de trabalho, sem
  intenção nova no classificador, sem débito no PMS, sem lista no checkout
  (F4.2), sem recado no lançar/dispensar
- Nenhum teste chama o adaptador WhatsApp real nem o LLM real
- Preço **nunca** entra no prompt
- Commit por tarefa ou grupo lógico **só se o usuário pedir commit**
- Evitar: allowlist de tipo novo; `conversa` INSERT em `consumo`;
  `atendimento` chamar LLM; preço no `LLMFalso` como se fosse do modelo;
  toalha virar consumo; `409` eterno em resolver consumo; texto ou valor do
  recado em log; ciclo `conversa` ↔ `atendimento` ↔ `propriedade`; tela
  agregada de turno
