---
description: "Task list for feature implementation"
---

# Tasks: Expurgo por Retenção

**Input**: Design documents from `/specs/023-expurgo-retencao/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de
produção sem teste que falhe antes pelo motivo certo.

**Organization**: Tarefas agrupadas por história (US1–US5), na ordem da spec.
Esquema (`execucao_retencao` + UNIQUE do dia UTC), marcas, semente dos prazos,
`ler_retencao` na matriz e esqueleto do agendador entram na Foundational. A
passagem que **anonimiza conteúdo livre** e mantém a linha é a US1 (MVP).
Volume (US2) trava a invariante da US1. Ficha aos cinco anos é a US3. Prazo,
idempotência e isolamento são a US4. Comprovante HTTP é a US5. Sem tipo novo
na fila `trabalho`. Sem APScheduler.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US5)

## Como ver os testes falharem nesta fatia

**Esquema.** `testes/integracao/test_conformidade_do_esquema.py` compara o banco
migrado com `docs/04-schema.sql`. Editar o documento **antes** da revisão deixa
a conformidade vermelha. A `0021` a devolve ao verde.

**Garantias.** `testes/integracao/test_garantias_do_banco.py`: sem a migração, o
segundo `INSERT` de `execucao_retencao` no mesmo hotel no mesmo dia UTC entra;
quantidade negativa entra. O UNIQUE e os CHECKs deixam esses testes vermelhos
pelo motivo certo.

**CLI.** Sem `--verificar-retencao` o parser recusa. O unitário da US1 falha
até a flag existir. `--uma-passagem` já é testado nas fatias anteriores; esta
fatia **estende** o teste para também não chamar a varredura de retenção.

**HTTP.** Sem `/retencao` a integração da US5 falha com `404` de rota até o
roteador ganhar o GET. `testes/integracao/test_rotas_protegidas.py` varre o
que estiver registrado: depois de ligar a rota, ela exige `401` sem cookie —
**não** editar `ROTAS_PUBLICAS`.

**Matriz.** Acrescentar `ler_retencao` em `OPERACOES_ESPERADAS` **antes** de
`politica.py` deixa `test_matriz_completa_bate_com_o_contrato` vermelho.

**Serviço / varredura.** Unitários falham por `AttributeError` /
`NotImplementedError` até existir a implementação.

---

## Phase 1: Setup

**Purpose**: constantes de teste, semente dos prazos nas duas propriedades
de integração, helper para montar estadia encerrada **sem** chamar o worker.
O monólito já existe; não criar pacote novo.

- [X] T001 [P] Criar `testes/suporte/retencao.py` com constantes estáveis:
      `MARCA_TEXTO` (`[anonimizado]`), `MARCA_PAYLOAD` (`{"anonimizado": true}`),
      `MARCA_TELEFONE` (`anonimizado`), chaves `meses_retencao_conteudo_livre`
      e `anos_retencao_ficha`, valores `12` e `5`, e instante âncora de teste
      (ex. 24/08/2026 12:00 UTC). Sem segredo. Docstring: uso só em teste
- [X] T002 [P] Em `testes/suporte/ambiente_de_acesso.py`, semear
      `meses_retencao_conteudo_livre=12` e `anos_retencao_ficha=5` nas duas
      propriedades (junto das chaves já existentes). Sem isso, a varredura
      das integrações cai em prazo ausente e afirma o caminho errado
- [X] T003 [P] Em `testes/suporte/retencao.py`, acrescentar
      `gravar_estadia_encerrada(conexao, id_hotel, *, checkout_em, texto,
      comentario=None, descricao=None, id_externo=None)` que insere hóspede,
      reserva `encerrado` com `checkin_em`/`checkout_em`, vínculo titular,
      mensagem recebida, e opcionalmente `evento_webhook`, `solicitacao` e
      `avaliacao`. Devolve ids. Sem chamar worker

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: revisão `0021`, tabela de comprovante, semente dos prazos,
marcas e vencimento civil, operação na matriz, SQL nomeado em esqueleto.
**Nenhuma rota HTTP nova ainda.** Nenhuma flag `--verificar-retencao` ainda.

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. Ordem do esquema:
T004 → T005 → T006 → T007 (teste vermelho no documento, depois migração
verde).

- [X] T004 Estender `testes/integracao/test_garantias_do_banco.py`: `INSERT`
      de `execucao_retencao` aceito; segundo `INSERT` do **mesmo** hotel no
      **mesmo** dia civil UTC recusado por `uq_execucao_retencao_hotel_dia`;
      hotel distinto no mesmo dia **passa**; segundo comprovante no dia
      seguinte **passa**; quantidade negativa recusada pelo CHECK. Rodar e
      **ver falhar** (FR-016, Artigo IX, [data-model.md](./data-model.md))
- [X] T005 Aplicar o delta em `docs/04-schema.sql`: tabela `execucao_retencao`
      (colunas, CHECKs ≥ 0, FK `id_hotel`); índice único
      `(id_hotel, ((executado_em AT TIME ZONE 'UTC')::date))`; chaves
      `meses_retencao_conteudo_livre` e `anos_retencao_ficha` no comentário
      de `parametro_hotel`. **Não** alterar `0001`. Rodar
      `testes/integracao/test_conformidade_do_esquema.py` e **ver falhar**
- [X] T006 Criar `alembic/versions/sql/0021_expurgo_retencao.sql` — cópia
      congelada do delta da T005 **mais** `INSERT` idempotente das duas
      chaves (`12` e `5`) por hotel (padrão da `0016`/`0020`)
- [X] T007 Criar `alembic/versions/0021_expurgo_retencao.py`
      (`down_revision = "0020_coleta_agendada"`), `upgrade` executa o SQL
      congelado, `downgrade` remove índice e tabela e **não** apaga as
      chaves já semeadas. T004 e a conformidade verdes
- [X] T008 [P] Unitário em
      `testes/unitarios/modulos/propriedade/test_bootstrap.py`: instalação
      inicial grava `meses_retencao_conteudo_livre` = `12` e
      `anos_retencao_ficha` = `5` (incluir no conjunto de chaves
      esperado). Rodar e **ver falhar** (FR-015)
- [X] T009 Acrescentar as duas chaves ao mapa de semente e gravá-las em
      `criar_instalacao_inicial` em `app/modulos/propriedade/service.py`
      até T008 verde
- [X] T010 [P] Acrescentar casos em
      `testes/unitarios/modulos/acesso/test_politica.py`: `ler_retencao`
      permitida **só** para `gestor`, recusada para `recepcao` e `staff`;
      incluir em `OPERACOES_ESPERADAS`. Rodar e **ver falhar**
      (FR-017, [contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))
- [X] T011 Acrescentar `ler_retencao` a `OPERACOES` em
      `app/modulos/acesso/politica.py` (`gestor` somente) até T010 passar.
      **Não** nascer `disparar_retencao` nem `alterar_retencao`
- [X] T012 [P] Unitários em `testes/unitarios/comum/test_retencao.py`:
      `vencido_em_meses` / `vencido_em_anos` com `calendar` (31 jan + 1
      mês → último dia de fev); exatamente no limite **não** vence antes;
      `checkout_em` nulo nunca vence. Constantes `MARCA_*` iguais às de
      `testes/suporte/retencao.py`. Rodar e **ver falhar**
      ([contracts/anonimizacao-e-exclusao.md](./contracts/anonimizacao-e-exclusao.md))
- [X] T013 Implementar `app/comum/retencao.py` (marcas + vencimento civil,
      sem SQL, sem `dateutil`) até T012 verde
- [X] T014 [P] Acrescentar em `app/modulos/propriedade/schema.py` o contrato
      de `GET /retencao` conforme
      [contracts/api-de-comprovante.md](./contracts/api-de-comprovante.md)
      (sem `id_hotel` no JSON; `extra="forbid"` se houver entrada)
- [X] T015 [P] Acrescentar funções nomeadas em esqueleto
      (`NotImplementedError`) — todo SQL futuro com `id_hotel` via reserva
      ou coluna da execução:
      `anonimizar_mensagens_vencidas` e `anonimizar_payloads_vencidos` em
      `app/modulos/conversa/repository.py` + `service.py`;
      `anonimizar_descricoes_vencidas` em
      `app/modulos/atendimento/repository.py` + `service.py`;
      `anonimizar_comentarios_vencidos` em
      `app/modulos/feedback/repository.py` + `service.py`;
      `apagar_fichas_vencidas` em
      `app/modulos/hospedagem/repository.py` + `service.py`;
      `registrar_execucao_retencao`, `ja_executou_retencao_no_dia` e
      `listar_execucoes_retencao` em
      `app/modulos/propriedade/repository.py` + `service.py`.
      Sem SQL de `parametro_hotel` fora de `propriedade.repository`
- [X] T016 Acrescentar `verificar_retencao` em `worker/agendador.py` com
      `agora` injetável e `NotImplementedError` até a US1 (padrão de
      `verificar_coletas_mercado`)

**Checkpoint**: tabela e UNIQUE no banco; prazos semeados; matriz com
`ler_retencao`; nomes de SQL existem; ainda não há GET `/retencao` nem
flag do worker. Histórias podem começar.

---

## Phase 3: User Story 1 - Conteúdo livre some no prazo, a linha fica (Priority: P1) 🎯 MVP

**Goal**: Passagem automática substitui texto de mensagem (ambas as
direções), comentário, descrição e payload da estadia com `checkout_em`
além de 12 meses; a linha permanece; eixos/nota intactos; comentário **e**
descrição vazios não ganham marca (FR-009).

**Independent Test**: Estadia encerrada há 13 meses (relógio injetável) com
mensagem recebida e enviada, webhook no mesmo `id_externo`, descrição e
comentário → `--verificar-retencao` marca o conteúdo; `COUNT(*)` igual;
classificação bruta nula; eixos permanecem. Estadia há 11 meses intacta.
Descrição `''` ou só espaços permanece vazia. `--uma-passagem` não dispara
(cobrado na US4).

### Tests for User Story 1 ⚠️

> Escrever primeiro; rodar; ver falhar pelo motivo certo antes de implementar.

- [X] T017 [P] [US1] Unitários em
      `testes/unitarios/modulos/conversa/test_anonimizar_mensagem_retencao.py`
      com repositório falso: reserva vencida → `conteudo` vira `MARCA_TEXTO`
      e `classificacao_bruta` some **nas duas direções**; eixos permanecem;
      já marcado não conta de novo; payload casa por `id_externo`; payload
      órfão não é tocado (FR-003, FR-006, FR-007, FR-014,
      [contracts/anonimizacao-e-exclusao.md](./contracts/anonimizacao-e-exclusao.md))
- [X] T018 [P] [US1] Unitários em
      `testes/unitarios/modulos/atendimento/test_anonimizar_descricao_retencao.py`:
      descrição vencida com texto vira marca; status/tipo/urgência intactos;
      já marcada não conta; `''` ou só espaços **não** recebem marca
      (FR-005, FR-008, FR-009)
- [X] T019 [P] [US1] Unitários em
      `testes/unitarios/modulos/feedback/test_anonimizar_comentario_retencao.py`:
      comentário com texto vira marca; nota/origem intactos; `NULL` ou só
      espaços **não** recebem marca (FR-004, FR-009)
- [X] T020 [P] [US1] Unitários em
      `testes/unitarios/worker/test_verificar_retencao.py`: com prazos
      válidos, `agora` injetável, chama os três serviços de conteúdo e
      `registrar_execucao_retencao`; devolve 1 hotel comprovado; log
      `retencao_aplicada` com `id_hotel` e quantidades, **sem** texto
      (FR-001, FR-016, FR-020,
      [contracts/agendador-e-retencao.md](./contracts/agendador-e-retencao.md))
- [X] T021 [US1] Integração em `testes/integracao/test_retencao.py`: via
      `ambiente_de_acesso` + `gravar_estadia_encerrada`, `checkout_em` =
      âncora − 13 meses; chamar `verificar_retencao`; texto/payload/
      descrição/comentário marcados; linhas ainda lá; 1 `execucao_retencao`;
      descrição originalmente vazia permanece vazia. Rodar e ver falhar
      (`NotImplementedError` / 0 linhas)

### Implementation for User Story 1

- [X] T022 [US1] Implementar `anonimizar_mensagens_vencidas` e
      `anonimizar_payloads_vencidos` em
      `app/modulos/conversa/repository.py` + `service.py` (`make_interval`
      em meses, `reserva.id_hotel`, `WHERE` distinto da marca, **sem**
      filtrar `direcao`). T017 verde
- [X] T023 [US1] Implementar `anonimizar_descricoes_vencidas` em
      `app/modulos/atendimento/repository.py` + `service.py` com
      `btrim(descricao) <> ''` além de distinto da marca. T018 verde
- [X] T024 [US1] Implementar `anonimizar_comentarios_vencidos` em
      `app/modulos/feedback/repository.py` + `service.py`. T019 verde
- [X] T025 [US1] Implementar `registrar_execucao_retencao` e
      `ja_executou_retencao_no_dia` em
      `app/modulos/propriedade/repository.py` + `service.py`; colisão do
      UNIQUE do dia = já executada (não propaga erro). Completar
      `verificar_retencao` em `worker/agendador.py`: por hotel, se já
      rodou hoje → log `retencao_ja_executada_hoje`; senão lê meses (anos
      pode no-opar até a US3), chama os três serviços, INSERT comprovante.
      T020–T021 verdes
- [X] T026 [US1] Acrescentar `--verificar-retencao` e
      `_rodar_verificacao_retencao` em `worker/__main__.py`; no modo
      contínuo, chamar junto com cadastros/boas-vindas/pulsos/mercado.
      Unitário da flag em `testes/unitarios/worker/test_cli_worker.py`.
      `--uma-passagem` ainda **não** dispara a varredura

**Checkpoint**: US1 entregável sozinha — conteúdo vencido irrecuperável,
volume da linha intacto, comprovante no banco. GET, ficha aos 5 anos e
isolamento fino ainda podem faltar.

---

## Phase 4: User Story 2 - A estatística de volume continua correta (Priority: P1)

**Goal**: Depois da anonimização, contagens de mensagem, de solicitação por
tipo e de avaliação por nota são as mesmas. Nenhum chamado muda de status.
`numero_quarto` e `janela_preferencia` não são tocados. Trava a invariante
da US1: anonimizar ≠ apagar.

**Independent Test**: Contar N mensagens, solicitações por tipo e notas
**antes**; rodar a passagem; as mesmas N e as mesmas distribuições. Status
`aberta` permanece `aberta`. Nota não vira nula.

### Tests for User Story 2 ⚠️

- [X] T027 [P] [US2] Unitários em
      `testes/unitarios/modulos/conversa/test_anonimizar_mensagem_retencao.py`
      (e equivalentes em `testes/unitarios/modulos/atendimento/` e
      `testes/unitarios/modulos/feedback/`): o serviço **não** chama DELETE;
      devolve só a quantidade de UPDATE; `janela_preferencia` e
      `numero_quarto` permanecem (FR-008,
      [contracts/anonimizacao-e-exclusao.md](./contracts/anonimizacao-e-exclusao.md))
- [X] T028 [US2] Integração em `testes/integracao/test_retencao.py`:
      `COUNT(*)` de `mensagem`, `solicitacao` agrupada por `tipo` e
      `avaliacao` agrupada por `nota` iguais antes/depois; `status` da
      solicitação inalterado; nota não vira nula (FR-008, SC-002)

### Implementation for User Story 2

- [X] T029 [US2] Se T027–T028 falharem porque a US1 apagou linha, mudou
      status ou tocou `janela_preferencia`/`numero_quarto`, corrigir os
      UPDATEs em `app/modulos/conversa/repository.py`,
      `app/modulos/atendimento/repository.py` e
      `app/modulos/feedback/repository.py` (sem DELETE, sem `UPDATE status`).
      Se já passarem, a invariante está trancada — **não** enfraquecer o teste

**Checkpoint**: Volume operacional sobrevive à retenção de conteúdo.

---

## Phase 5: User Story 3 - A ficha some cinco anos depois da última saída (Priority: P1)

**Goal**: Hóspede cuja última reserva vinculada tem `checkout_em` além de
5 anos é apagado, com consentimento; a reserva operacional permanece sem
telefone da pessoa; última saída recente ou `checkout_em` nulo não apaga.

**Independent Test**: Ficha + consentimento, saída há 6 anos → linhas
ausentes; reserva existe; `telefone_contato` = `MARCA_TELEFONE`. Duas
reservas, a mais nova há 1 ano → ficha intacta. Hospedado sem
`checkout_em` → ficha intacta.

### Tests for User Story 3 ⚠️

- [X] T030 [P] [US3] Unitários em
      `testes/unitarios/modulos/hospedagem/test_apagar_ficha_retencao.py`:
      elegível (todas as reservas com `checkout_em`, `MAX` vencido) →
      apaga ficha e consentimento; telefone só se a reserva ficou sem
      vínculo; duas reservas, a mais nova dentro do prazo → 0 exclusões;
      alguma reserva sem `checkout_em` → 0 exclusões (FR-010 a FR-013)
- [X] T031 [US3] Integração em `testes/integracao/test_retencao.py`:
      `checkout_em` = âncora − 6 anos; após `verificar_retencao` com anos
      válido, `hospede`/`consentimento` ausentes; reserva permanece;
      `telefone_contato` = `MARCA_TELEFONE`; comprovante
      `fichas_apagadas >= 1`

### Implementation for User Story 3

- [X] T032 [US3] Implementar `apagar_fichas_vencidas` em
      `app/modulos/hospedagem/repository.py` + `service.py` (ordem
      consentimento → `reserva_hospede` → `hospede` → telefone se órfão;
      `make_interval` em anos; elegibilidade com **todas** as reservas
      vinculadas). T030 verde
- [X] T033 [US3] Em `verificar_retencao` (`worker/agendador.py`), se anos
      válido chamar `apagar_fichas_vencidas` e somar no comprovante; se
      inválido, flag `prazo_ficha_ausente` e 0 fichas. T031 verde

**Checkpoint**: Identidade cai no prazo; estadia operacional permanece.

---

## Phase 6: User Story 4 - Dentro do prazo, nada é tocado (Priority: P1)

**Goal**: Dentro do prazo, sem `checkout_em`, já tratado, outro hotel ou
chave ausente: zero tratamento indevido. Segunda passagem no mesmo dia
UTC não gera segundo comprovante. `--uma-passagem` não varre retenção.

**Independent Test**: 11 meses → texto original. Dois hotéis: A vencido, B
não → só A muda. Apagar chave de meses → 0 marcas de conteúdo e log
`prazo_conteudo_ausente`. Segunda `--verificar-retencao` no mesmo dia:
um comprovante. CLI `--uma-passagem` não chama a varredura.

### Tests for User Story 4 ⚠️

- [X] T034 [P] [US4] Unitários em
      `testes/unitarios/worker/test_verificar_retencao.py`: 11 meses não
      chama anonimizar (ou chama e os serviços devolvem 0); chave
      ausente/zero/não numérica → não chama conteúdo daquele tipo, log
      `prazo_conteudo_ausente` / `prazo_ficha_ausente`, comprovante com a
      flag; `ja_executou_retencao_no_dia` → 0 tratamentos e log
      `retencao_ja_executada_hoje`; **não** assume 12 nem 5
      (FR-013, FR-015, FR-014, Artigo XIII)
- [X] T035 [P] [US4] Integração em `testes/integracao/test_retencao.py`:
      dois hotéis via `ambiente_de_acesso`; só o vencido de A é marcado;
      B intacto; segunda chamada no mesmo `agora` → ainda 1 comprovante
      por hotel (FR-018, FR-014)
- [X] T036 [P] [US4] Estender
      `testes/unitarios/worker/test_cli_worker.py`: `--uma-passagem` não
      chama `_rodar_verificacao_retencao` (além de cadastros/pulsos/mercado
      já cobertos) (FR-001, FR-019)

### Implementation for User Story 4

- [X] T037 [US4] Completar leitura dos prazos em `verificar_retencao`
      (`worker/agendador.py`: inteiro ≥ 1, cache por hotel, flags no
      comprovante, skip do dia) até T034–T035 verdes — se já nasceu na
      US1, só fechar os casos novos
- [X] T038 [US4] Fechar T036: `worker/__main__.py` não dispara retenção em
      `--uma-passagem`. Se já estiver assim, só o teste

**Checkpoint**: Relógio honesto; multi-tenant; parâmetro sem default
silencioso; sem disparo no consumidor de fila.

---

## Phase 7: User Story 5 - O cumprimento pode ser demonstrado (Priority: P1)

**Goal**: Gestão consulta `GET /retencao` e vê instante + quantidades por
tipo (inclusive zeros). Recepção e operação recusadas. Sem rota de
disparo. Comprovante e log sem dado do titular.

**Independent Test**: Cookie de gestão → `200` com a passagem da US1.
Recepção → `403`. Sem cookie → `401`. `POST /retencao` → `405`. Hotel B
não vê a linha de A. Passagem sem vencidos → quantidades zero.

### Tests for User Story 5 ⚠️

- [X] T039 [P] [US5] Unitários em
      `testes/unitarios/modulos/propriedade/test_comprovante_retencao.py`:
      `listar_execucoes_retencao(id_hotel)` devolve a lista daquele hotel
      em ordem `executado_em DESC`; hotel sem linha → `[]`; **não** inclui
      texto de hóspede (FR-016, FR-018,
      [contracts/api-de-comprovante.md](./contracts/api-de-comprovante.md))
- [X] T040 [US5] Integração em `testes/integracao/test_retencao.py`: gestão
      `GET /retencao` `200` com quantidades; lista vazia sem erro; recepção
      e staff `403`; sem cookie `401`; `POST /retencao` `405`; gestão do
      hotel B não vê execução de A. Rodar e ver falhar (`404` de rota)

### Implementation for User Story 5

- [X] T041 [US5] Implementar `listar_execucoes_retencao` em
      `app/modulos/propriedade/repository.py` + `service.py`
      (`WHERE id_hotel`, `ORDER BY executado_em DESC`). T039 verde.
      Log da consulta: `id_hotel`, ação `comprovante` — sem nome/telefone/
      documento/texto
- [X] T042 [US5] Implementar `GET /retencao` em
      `app/modulos/propriedade/router.py` com
      `exigir_operacao("ler_retencao")`, `id_hotel` só da sessão. T040
      verde. **Não** registrar POST/PATCH/DELETE nem `/retencao/executar`

**Checkpoint**: Cumprimento demonstrável pela consulta autenticada da gestão.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: logs, estado do projeto, dicionário, fronteiras, suíte cheia

- [X] T043 [P] Estender
      `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py` (e/ou
      arquivo irmão da retenção): passagem e GET registram `id_hotel`,
      quantidades e códigos (`retencao_aplicada`, `prazo_conteudo_ausente`,
      `retencao_ja_executada_hoje`); **não** registram conteúdo, comentário,
      payload, nome, telefone nem documento (FR-020)
- [X] T044 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F6.1 em andamento /
      concluída na entrega; APScheduler continua recusado; comprovante ≠
      auditoria genérica; `solicitacao.descricao` e `classificacao_bruta`
      no prazo de 12 meses (divergência da tabela resumida do Artefato 5
      §9.1); payload órfão fora; próxima fatia F6.2; revisão `0021`; sem
      React, sem disparo manual
- [X] T045 [P] Atualizar `docs/04-modelagem-de-dados.md`: registrar
      `execucao_retencao`; marcar a pendência do item 4 (rotina de expurgo)
      como cumprida pela passagem (não por trigger); citar as duas chaves
- [X] T046 Revisar fronteiras: SQL de cada tabela só no módulo dono;
      `verificar_retencao` orquestra (parâmetro em `propriedade`);
      `conversa`/`atendimento`/`feedback`/`hospedagem` **não** importam uns
      aos outros por causa desta fatia; `app/comum/retencao.py` sem SQL;
      `testes/integracao/test_rotas_protegidas.py` verde sem acréscimo em
      `ROTAS_PUBLICAS`
- [X] T047 Percorrer [quickstart.md](./quickstart.md) (ou equivalente
      automatizado): `pytest testes/unitarios -q`,
      `pytest testes/integracao/test_retencao.py -q`,
      `testes/integracao/test_garantias_do_banco.py`,
      `testes/integracao/test_conformidade_do_esquema.py` e
      `testes/integracao/test_rotas_protegidas.py`; tudo verde **sem**
      esperar doze meses reais e **sem** WhatsApp

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: após Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: após Foundational — MVP
- **US2 (Phase 4)**: após os UPDATEs da US1 (trava “não apagar”)
- **US3 (Phase 5)**: após a passagem existir (US1); pode em paralelo com
  US2 (arquivos de hospedagem distintos)
- **US4 (Phase 6)**: após a varredura existir (US1); casos de chave/skip
  do dia podem ser preenchidos se a US1 já leu o parâmetro
- **US5 (Phase 7)**: após existir `execucao_retencao` gravada (US1); GET
  não depende da US3
- **Polish (Phase 8)**: após as histórias desejadas

### User Story Dependencies

- **US1**: só Foundational — MVP isolado (marca no conteúdo vencido +
  comprovante no banco)
- **US2**: depende dos UPDATEs da US1; aceite independente se o teste
  contar antes/depois
- **US3**: independente no aceite da ficha; reusa a passagem da US1
- **US4**: transversal sobre varredura, parâmetro e `id_hotel`
- **US5**: GET sobre o comprovante que a US1 já grava

### Within Each User Story

1. Testes escritos e vermelhos
2. Implementação mínima
3. Verde
4. Só então próxima história

### Parallel Opportunities

- T001–T003 em paralelo
- T008, T010, T012, T014, T015 em paralelo após T007 (esquema no banco) —
  T008/T009 não dependem da matriz
- T017, T018, T019, T020 em paralelo
- T022, T023, T024 em paralelo (módulos distintos) após os testes
- T027 paralelo a T028
- T030 paralelo a T031
- T034, T035, T036 em paralelo
- T043, T044, T045 em paralelo

---

## Parallel Example: User Story 1

```text
T017 Unitários conversa em testes/unitarios/modulos/conversa/test_anonimizar_mensagem_retencao.py
T018 Unitários atendimento em testes/unitarios/modulos/atendimento/test_anonimizar_descricao_retencao.py
T019 Unitários feedback em testes/unitarios/modulos/feedback/test_anonimizar_comentario_retencao.py
T020 Unitários da varredura em testes/unitarios/worker/test_verificar_retencao.py
```

Depois, em sequência: T021 → T022–T024 (paralelos) → T025 → T026.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup
2. Phase 2: Foundational (bloqueia)
3. Phase 3: US1 — estadia vencida → texto irrecuperável, linha viva,
   comprovante gravado
4. **STOP and VALIDATE**: `verificar_retencao` com relógio injetável
5. US2–US5 e polish na mesma entrega (um desenvolvedor)

### Incremental Delivery

1. Setup + Foundational → tabela, prazos, matriz
2. US1 → demo: conteúdo de 13 meses vira marca
3. US2 → volume trancado
4. US3 → ficha de 6 anos some
5. US4 → prazo, isolamento, sem default
6. US5 → gestão lê o comprovante
7. Polish → estado do projeto e suíte cheia

### Parallel Team Strategy

Um desenvolvedor, prazo fixo: ordem US1 → US2 → US3 → US4 → US5. Não
paralelizar histórias que mexem no mesmo `verificar_retencao` no mesmo
passo; US3 (hospedagem) pode seguir US2 se a US1 já orquestra.

---

## Notes

- Sem tipo na fila, sem porta nova, sem React, sem botão de expurgo
- Relógio injetável; nunca esperar 12 meses de parede
- `0001` congelado; documento vivo + `0021`
- Nomes de arquivo de teste de anonimização são distintos por módulo:
  pytest no Windows não coleta dois `test_anonimizar_retencao.py`
- FR-009 cobre comentário **e** descrição vazia (`btrim <> ''`); a coluna
  `solicitacao.descricao` é `NOT NULL`, então vazio é string em branco, não
  `NULL`
- Mensagens enviadas pelo hotel entram no mesmo UPDATE (FR-003 não filtra
  `direcao`)
- `solicitacao.janela_preferencia` e `numero_quarto` ficam fora
- Próximo: F6.2 (simulador da apresentação)
