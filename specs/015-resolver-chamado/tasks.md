---
description: "Task list for feature implementation"
---

# Tasks: Resolver Chamado e Confirmar

**Input**: Design documents from `/specs/015-resolver-chamado/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de produção
antes de um teste que falhe pela ausência dela, e pelo motivo certo.

**Organization**: Tarefas agrupadas por história (US1–US8), na ordem da spec. Esquema
(`enviar_confirmacao_resolucao` + unicidade + trigger + CHECK de autor), recado
puro, `resolver` (UPDATE) e enqueue **sem claim** entram na Foundational. O
corte HTTP (POST + agendar na mesma transação) é a US1. O corte que **liga** o
worker (allowlist + ramo) fica na US2 — os dois no mesmo passo, para não deixar
`tipo_desconhecido` no meio do caminho. `GET /solicitacoes` **não** muda o JSON;
a US1/US4 só asserem que o resolvido some e o aberto permanece.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US8)

## Como ver os testes falharem nesta fatia

**Esquema.** `testes/integracao/test_conformidade_do_esquema.py` compara o banco
migrado com `docs/04-schema.sql`. Editar o documento **antes** da revisão deixa a
conformidade vermelha apontando o tipo novo / o unique / o trigger / o CHECK de
autor. A revisão `0014` a devolve ao verde.

**Recado.** Função pura: o teste falha até o módulo existir.

**`resolver`.** O unitário falha por `AttributeError` até o serviço existir.

**Claim / worker.** Hoje a allowlist **não** inclui `enviar_confirmacao_resolucao`
e o consumidor não tem ramo. Os testes da US2 ficam vermelhos até allowlist e
`elif` existirem juntos. Não colocar o tipo na allowlist na Foundational — senão
`--uma-passagem` marca `tipo_desconhecido` antes do processador existir.

**POST.** Hoje não existe `POST /solicitacoes/{id}/resolucao`. A integração da
US1 falha com `404` de rota até o roteador existir.

---

## Phase 1: Setup

**Purpose**: helpers da resolução, sem repetir payload e textos de recusa em cada
arquivo

- [X] T001 [P] Criar `testes/suporte/resolucao.py` com constantes estáveis:
      detalhe `409` já resolvida (`Esta solicitacao ja foi resolvida.`), detalhe
      `404` (`Solicitacao nao encontrada.`), detalhe tipo consumo, e um helper
      `proibicoes_do_recado()` (palavras `extrato`, `conta`, trechos de catálogo,
      pergunta de horário). Sem segredo, sem rede
- [X] T002 [P] Em `testes/suporte/reclamacao.py` e
      `testes/suporte/pedido_servico.py`, documentar no docstring que F3.6 fecha
      os dois tipos via `POST /solicitacoes/{id}/resolucao`. Sem mudar textos nem
      eixos

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: tipo `enviar_confirmacao_resolucao` no banco, unicidade por
`id_solicitacao`, trigger de transição, CHECK de autor, recado puro, `resolver`
(UPDATE), `agendar_confirmacao_resolucao` e enqueue **ainda sem claim**. Nenhuma
história consome o trabalho ainda. **Nenhuma rota HTTP nova.**

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. Ordem do esquema:
T003 → T004 → T006 → T007 (teste vermelho no documento, depois migração verde).

- [X] T003 Estender `testes/integracao/test_garantias_do_banco.py`: `INSERT` em
      `trabalho` com `tipo = 'enviar_confirmacao_resolucao'` aceito; segundo
      `INSERT` com o mesmo `payload.id_solicitacao` viola
      `uq_trabalho_enviar_confirmacao_resolucao_solicitacao`; transições
      `aberta`/`em_andamento` → `resolvida` aceitas quando há `resolvida_em` e
      `id_usuario_responsavel`; `resolvida` → `aberta` e `aberta` → `cancelada`
      recusadas pelo trigger; `resolvida` sem responsável recusada pelo CHECK.
      Rodar e **ver falhar** (FR-002, FR-008, [data-model.md](./data-model.md))
- [X] T004 Aplicar o delta em `docs/04-schema.sql`: `ck_trabalho_tipo` inclui
      `enviar_confirmacao_resolucao`; índice
      `uq_trabalho_enviar_confirmacao_resolucao_solicitacao`;
      `fn_valida_transicao_solicitacao` + `tg_valida_transicao_solicitacao`;
      `ck_solicitacao_resolvida_tem_responsavel`. **Não** alterar
      `vw_fila_do_dia` nem colunas de `solicitacao`. Rodar
      `testes/integracao/test_conformidade_do_esquema.py` e **ver falhar** pela
      divergência
- [X] T005 [P] Alinhar `docs/04-modelagem-de-dados.md`: tipo
      `enviar_confirmacao_resolucao`; máquina `aberta`/`em_andamento` →
      `resolvida`; `id_usuario_responsavel` preenchido na resolução; recado de
      conclusão é mensagem enviada distinta da origem. Não dizer que chamado
      permanece só `aberta`
- [X] T006 Criar `alembic/versions/sql/0014_resolver_chamado.sql` — cópia
      congelada do CHECK de tipo, do índice, do trigger e do CHECK de autor
- [X] T007 Criar `alembic/versions/0014_resolver_chamado.py`
      (`down_revision = "0013_abrir_chamado_reclamacao"`), `upgrade` executa o
      SQL congelado, `downgrade` restaura o CHECK da `0013`, remove o índice e o
      trigger (não afrouxa o CHECK de autor se já houver linhas resolvidas —
      o CHECK é compatível com abertas). T003 e a conformidade verdes
- [X] T008 [P] Unitário em
      `testes/unitarios/modulos/conversa/test_texto_confirmacao_resolucao.py`:
      `montar_confirmacao_resolucao` usa só o prenome; com `tipo='reclamacao'`
      fala de problema atendido / manutenção; com `tipo='servico'` fala de
      pedido atendido; **não** contém as proibições de T001. **Ver falhar**
      (FR-005, [contracts/mensageria-sessao.md](./contracts/mensageria-sessao.md))
- [X] T009 Implementar `montar_confirmacao_resolucao` em
      `app/modulos/conversa/texto_confirmacao_resolucao.py` (função pura, padrão
      dos recados de pedido/reclamação). T008 verde
- [X] T010 [P] Unitário em
      `testes/unitarios/modulos/atendimento/test_resolver.py`: repositório falso
      + `agendar_confirmacao` espião → `resolver` devolve snapshot `resolvida`
      com autor e instante quando o UPDATE encontra a linha; chama o espião
      **depois** do UPDATE, com `id_solicitacao`, `id_reserva`, `tipo` e
      `id_hotel`; zero linhas → `SolicitacaoNaoEncontrada` se não existe no
      hotel, `ResolucaoNaoPermitida` se já resolvida / tipo `consumo`; espião
      **não** é chamado na recusa. **Ver falhar** (FR-001, FR-002, FR-006,
      FR-008, FR-017)
- [X] T011 Implementar `marcar_resolvida` / `ler_do_hotel` em
      `app/modulos/atendimento/repository.py` (`UPDATE` condicional: hotel da
      sessão via `JOIN reserva`, `tipo IN ('reclamacao','servico')`, `status IN
      ('aberta','em_andamento')`, preenche `resolvida_em` com relógio injetável
      e `id_usuario_responsavel`) e `resolver` em
      `app/modulos/atendimento/service.py` (exceções nomeadas; `agendar` injetado
      com default `None` nesta tarefa — a US1 liga o default real). Sem HTTP.
      Sem porta de mensageria. T010 verde. Depende de T007
- [X] T012 [P] Unitário em
      `testes/unitarios/fila/test_enfileirar_enviar_confirmacao_resolucao.py`:
      `enfileirar_enviar_confirmacao_resolucao` insere tipo e payload
      `{id_reserva, id_solicitacao, id_mensagem}` só com IDs. **Ver falhar**
      ([contracts/fila-e-worker.md](./contracts/fila-e-worker.md)). Depende de
      T007
- [X] T013 Implementar `enfileirar_enviar_confirmacao_resolucao` em
      `app/fila/repository.py` e `app/fila/service.py`. **Não** incluir o tipo em
      `TIPOS_CONSUMIVEIS`. T012 verde
- [X] T014 [P] Unitário em
      `testes/unitarios/modulos/conversa/test_confirmacao_resolucao.py`:
      `agendar_confirmacao_resolucao` insere enviada `pendente` com recado do
      tipo (T009), JSON `tipo=confirmacao_resolucao` + `id_solicitacao`, e
      enfileira o trabalho; unique dispara → desfecho `ja_agendada` sem segunda
      enviada (savepoint, padrão de `agendar_boas_vindas`); **não** chama a
      porta de envio. **Ver falhar** (FR-007, FR-013). Depende de T007 e T013
- [X] T015 Implementar `agendar_confirmacao_resolucao` em
      `app/modulos/conversa/service.py` (lê prenome do titular como os outros
      recados; savepoint no INSERT+enqueue; **não** importa `atendimento`). T014
      verde

**Checkpoint**: esquema aceita o tipo e recusa transição inválida; dá para
resolver no serviço, gravar enviada e enfileirar. Worker **não** consome o tipo.
POST **ainda não** existe. `GET /solicitacoes` inalterado.

---

## Phase 3: User Story 1 - Equipe marca resolvido (quem e quando) (Priority: P1) 🎯 MVP

**Goal**: `POST /solicitacoes/{id}/resolucao` (recepção ou staff) grava
`resolvida` + autor + instante, agenda a confirmação (`confirmacao=agendada`) e
tira o item do Alert Center. Gestão ainda não é o foco (US5). Worker ainda não
envia (US2).

**Independent Test**: staff autentica, POST numa reclamação ou serviço abertos →
`200` com `status=resolvida`, `id_usuario_responsavel` do staff, `resolvida_em`
preenchido, sem nome/telefone/descrição; `GET /solicitacoes` **não** lista aquele
id; existe `trabalho` `enviar_confirmacao_resolucao` `pendente`.

### Tests for User Story 1 ⚠️

- [X] T016 [P] [US1] Em `test_resolver.py`: com repositório postgres
      (`testes/unitarios/modulos/atendimento/test_resolver.py`) e
      `agendar_confirmacao` espião, `resolver` persiste `resolvida` + autor +
      instante; `listar_abertas` deixa de devolver o item; reserva de outro
      hotel não muda. **Ver falhar** se T011 ainda não ligar o agendar no
      caminho feliz — nesta tarefa o teste exige a chamada ao espião (FR-001,
      FR-002, FR-003)
- [X] T017 [P] [US1] Integração em `testes/integracao/test_resolver_chamado.py`
      (criar): login staff, semear solicitação `aberta` (reusar helpers de
      `testes/integracao/test_solicitacoes.py`), `POST
      /solicitacoes/{id}/resolucao` → `200` no contrato de
      [contracts/api-de-atendimento.md](./contracts/api-de-atendimento.md);
      `GET /solicitacoes` sem o id; `reserva.status` intocado. **Ver falhar**
      (rota inexistente) (SC-001, SC-004)

### Implementation for User Story 1

- [X] T018 [US1] Criar `ResolucaoResposta` em
      `app/modulos/atendimento/schema.py`. Em
      `app/modulos/atendimento/service.py`, default
      `agendar_confirmacao=conversa.agendar_confirmacao_resolucao`. Em
      `app/modulos/atendimento/router.py`, `POST
      /solicitacoes/{id_solicitacao}/resolucao` com
      `exigir_operacao("resolver_solicitacao")`, corpo vazio, mapear
      `SolicitacaoNaoEncontrada` → `404` e `ResolucaoNaoPermitida` → `409`. Sem
      chamar a porta de mensageria. T016 e T017 verdes

**Checkpoint**: o clique fecha a pendência e agenda o recado. O hóspede ainda
não recebe (allowlist fechada). Segundo clique e gestão: US3 e US5.

---

## Phase 4: User Story 2 - Hóspede é avisado depois da resolução (Priority: P1)

**Goal**: o worker consome `enviar_confirmacao_resolucao`, envia o recado já
gravado via `enviar_texto_sessao`, **não** altera `solicitacao`. Recado adequado
ao tipo. Ordem: resolução gravada **antes** da enviada existir — já garantida no
POST; esta história garante a entrega.

**Independent Test**: POST `200` + `--uma-passagem` → enviada `enviada`, trabalho
`concluido`, `solicitacao` continua `resolvida`, corpo é o recado da T009.

### Tests for User Story 2 ⚠️

- [X] T019 [P] [US2] Unitário em `test_confirmacao_resolucao.py`:
      `processar_trabalho_enviar_confirmacao_resolucao` chama
      `enviar_texto_sessao` com o `conteudo` já gravado, marca enviada/trabalho
      concluídos, **não** chama `resolver` / não dá `UPDATE` em `solicitacao`.
      **Ver falhar** (FR-005, FR-006, FR-016)
- [X] T020 [P] [US2] Unitário em
      `testes/unitarios/fila/test_claim_enviar_confirmacao_resolucao.py`:
      `reclamar_proximo` **devolve** `enviar_confirmacao_resolucao` quando é o
      único pendente. **Ver falhar** (hoje a allowlist exclui)
- [X] T021 [US2] Integração em `test_resolver_chamado.py`: POST +
      `processar_uma_passagem` → uma enviada com recado de reclamação (ou
      serviço, segundo o tipo semeado), `status_envio=enviada`, solicitação
      `resolvida`, `GET /solicitacoes` sem o item. **Ver falhar** até o worker
      consumir (SC-002, SC-012)

### Implementation for User Story 2

- [X] T022 [US2] Implementar
      `processar_trabalho_enviar_confirmacao_resolucao` em
      `app/modulos/conversa/service.py` (padrão de
      `processar_trabalho_enviar_boas_vindas`: localiza `id_mensagem` do payload,
      envia, reagenda só `FalhaDeEnvio`). Sem importar `atendimento`. Sem LLM.
      T019 verde no caminho feliz
- [X] T023 [US2] Em `app/fila/repository.py`, incluir o tipo na allowlist. Em
      `worker/consumidor.py`, ramo com `gateway` —
      **allowlist e ramo no mesmo passo**. T020 e T021 verdes. Nunca allowlist
      sem ramo (research §1 / ponto de atenção 2 do plano)

**Checkpoint**: `--uma-passagem` depois do POST entrega o recado. Idempotência do
aviso e falha de envio: US6 e US7.

---

## Phase 5: User Story 3 - Não resolve duas vezes (Priority: P1)

**Goal**: segundo POST no mesmo id é `409`, autor/instante da primeira resolução
inalterados, zero segunda enviada.

**Independent Test**: POST `200`, POST de novo → `409` com o detalhe de T001;
`SELECT` de `resolvida_em` e `id_usuario_responsavel` iguais; `count(mensagem
enviada de confirmação)=1`.

### Tests for User Story 3 ⚠️

- [X] T024 [P] [US3] Unitário em `test_resolver.py`: segunda chamada de
      `resolver` no mesmo id levanta `ResolucaoNaoPermitida`; espião de agendar
      **não** é chamado de novo. **Ver falhar** se T011 ainda tratar o segundo
      UPDATE como sucesso (FR-008, SC-003)
- [X] T025 [US3] Integração em `test_resolver_chamado.py`: segundo POST `409`
      `Esta solicitacao ja foi resolvida.`; corrida documentada pelo unique do
      trabalho (já em T003) — aqui o caminho HTTP. **Ver falhar** (SC-003)

### Implementation for User Story 3

- [X] T026 [US3] Garantir o `UPDATE` condicional (zero linhas → `ler_do_hotel`
      → `ResolucaoNaoPermitida`) em
      `app/modulos/atendimento/service.py` e o detalhe estável no roteador
      (`app/modulos/atendimento/router.py`). T024 e T025 verdes. Não devolver
      `200` idempotente

**Checkpoint**: toque duplo no celular não avisa o hóspede duas vezes.

---

## Phase 6: User Story 4 - Passagem de turno mostra o que falta (Priority: P1)

**Goal**: `GET /solicitacoes` continua sendo a passagem de turno: abertos
permanecem (três perfis); resolvidos **não** voltam. Sem tela agregada com ficha
parcial.

**Independent Test**: duas pendências; POST na primeira; GET (recepção, staff,
gestão) lista só a segunda.

### Tests for User Story 4 ⚠️

- [X] T027 [P] [US4] Integração em `testes/integracao/test_solicitacoes.py`:
      semear duas abertas, resolver uma (login staff), GET nos três perfis da
      propriedade A lista só a restante, sem ficha; hotel B não vê nenhuma das
      duas. **Ver falhar** se o GET passar a listar `resolvida` (FR-003, FR-004,
      SC-004)
- [X] T028 [P] [US4] Unitário em
      `testes/unitarios/modulos/atendimento/test_listar_abertas.py`: depois de
      `resolver`, a lista do hotel não inclui o id; item ainda `aberta` de outra
      reserva permanece. **Ver falhar** (FR-004)

### Implementation for User Story 4

- [X] T029 [US4] **Não** alterar o filtro de `listar_abertas` em
      `app/modulos/atendimento/repository.py` (`status IN ('aberta',
      'em_andamento')`). Se T027/T028 vermelhos, o defeito está no `UPDATE` ou
      no GET — corrigir sem criar `GET /solicitacoes/{id}` nem listar
      resolvidas. T027 e T028 verdes

**Checkpoint**: passagem de turno = Alert Center já existente.

---

## Phase 7: User Story 5 - Quem não deve fechar não fecha (Priority: P1)

**Goal**: gestão `403`; outro hotel `404` sem revelar; staff `200` sem ficha.

**Independent Test**: gestão POST `403` e item segue na lista; staff do hotel B
POST no id de A → `404`; staff de A `200` sem chaves cadastrais.

### Tests for User Story 5 ⚠️

- [X] T030 [P] [US5] Integração em `test_resolver_chamado.py`: gestão da mesma
      propriedade `403` e solicitação permanece `aberta`; staff do hotel B `404`
      `Solicitacao nao encontrada.`; resposta `200` do staff de A **sem** as
      chaves de `CHAVES_CADASTRAIS` de `test_solicitacoes.py`. **Ver falhar**
      (FR-009, FR-010, FR-011, SC-005, SC-006)

### Implementation for User Story 5

- [X] T031 [US5] Confirmar `exigir_operacao("resolver_solicitacao")` no POST
      (`403` da dependência F0.3) e o `404` uniforme para outro hotel em
      `app/modulos/atendimento/router.py` / `service.py`. T030 verde. Não
      devolver `403` para hotel B (revelaria que existe)

**Checkpoint**: matriz exercitada na rota nova.

---

## Phase 8: User Story 6 - Falha não desfaz nem inventa resolução (Priority: P1)

**Goal**: envio falho **não** reabre; falha ao gravar no POST **não** envia.

**Independent Test**: (a) POST `200`, `MensageriaFalsa` em falha, uma passagem →
`resolvida`, enviada no histórico, trabalho não `concluido`, GET sem o item;
(b) `agendar` levantando no POST → transação desfaz, item `aberta`, zero envio.

### Tests for User Story 6 ⚠️

- [X] T032 [P] [US6] Unitário em `test_confirmacao_resolucao.py`: depois de
      gravada a enviada, gateway com `FalhaDeEnvio` → solicitação **não** é
      atualizada (já resolvida permanece); trabalho não `concluido` sem
      reagendar envio. **Ver falhar** (FR-013, SC-008)
- [X] T033 [US6] Integração em `test_resolver_chamado.py`: POST com agendar
      abortando (ou constraint) → `GET /solicitacoes` ainda mostra o item; zero
      `enviar_texto_sessao`. POST feliz + envio falho → item some da lista e
      `status=resolvida`. **Ver falhar** (FR-012, FR-013)

### Implementation for User Story 6

- [X] T034 [US6] Em `app/modulos/conversa/service.py`: capturar `FalhaDeEnvio`
      e reagendar mensageria (padrão das boas-vindas); **não** dar UPDATE em
      `solicitacao`. POST: resolução + agendar na mesma transação — falha de
      agendar desfaz o `UPDATE`. T032 e T033 verdes. Não usar `marcar_falha`
      por tipo serviço vs reclamação

**Checkpoint**: mensageria caída atrasa o aviso; não reabre o chamado.

---

## Phase 9: User Story 7 - Retrabalho do aviso não duplica (Priority: P1)

**Goal**: segundo claim do mesmo trabalho não insere segunda enviada; unique
impede segundo trabalho.

**Independent Test**: POST + duas passagens (ou claim após já `enviada`) →
exatamente uma mensagem `confirmacao_resolucao` daquela solicitação.

### Tests for User Story 7 ⚠️

- [X] T035 [P] [US7] Unitário em `test_confirmacao_resolucao.py`: enviada já
      `enviada` → processador conclui sem segunda INSERT e sem segundo
      `enviar_texto_sessao`; enviada `pendente` retenta o envio. **Ver falhar**
      (FR-013, SC-009)

### Implementation for User Story 7

- [X] T036 [US7] Guard no processador em `app/modulos/conversa/service.py`: se
      `status_envio` já é `enviada`, `marcar_concluido` e sair. T035 verde. Unique
      do trabalho (T003/T007) cobre o segundo enqueue

**Checkpoint**: retry de envio ≠ segundo recado.

---

## Phase 10: User Story 8 - Conteúdo não vaza em log (Priority: P2)

**Goal**: resolução, recusa, já agendada e envio falho logam identificadores,
hotel e `resultado` — nunca descrição, recado, telefone, quarto ou nome.

**Independent Test**: caplog nos desfechos; fixture de conteúdo ausente do log.

### Tests for User Story 8 ⚠️

- [X] T037 [P] [US8] Estender
      `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py` (e
      `test_resolver.py` se o evento for em `atendimento`): desfechos
      `chamado_resolvido`, `resolucao_recusada`, `resolucao_ja_agendada`,
      `resolucao_envio_falhou` — o texto do recado e a descrição não aparecem;
      há `id_solicitacao` / `id_hotel` / `resultado`. **Ver falhar** (FR-014,
      SC-010)

### Implementation for User Story 8

- [X] T038 [US8] Ajustar logs em `app/modulos/atendimento/service.py` e
      `app/modulos/conversa/service.py` conforme
      [contracts/fila-e-worker.md](./contracts/fila-e-worker.md). T037 verde

**Checkpoint**: trilha técnica sem cópia da conversa.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: consumo recusado, `em_andamento` fecha, regressão F3.4/F3.5,
fronteiras, documentação, suíte

- [X] T039 [P] Integração em `test_resolver_chamado.py`: solicitação tipo
      `consumo` (inserir pai + filha se o teste precisar) → POST `409` com o
      detalhe de tipo; `em_andamento` de reclamação/serviço → `200`; reserva
      `encerrado` **não** impede resolver (FR-016, FR-017, edge da spec)
- [X] T040 [P] Regressão: `testes/integracao/test_registrar_pedido.py`,
      `test_abrir_chamado.py`, `test_solicitacoes.py` (GET inalterado no JSON),
      `test_classificar_mensagem.py` e o claim de outros tipos continuam
      verdes; classificar **não** enfileira `enviar_confirmacao_resolucao`
- [X] T041 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F3.6 em
      andamento/concluída, revisão `0014`, `POST .../resolucao`, worker
      `enviar_confirmacao_resolucao`, limitação honesta da janela de 24h,
      próxima fatia **F3.7**. Não apontar F2.3
- [X] T042 Revisar fronteiras: `conversa` não dá UPDATE em `solicitacao`;
      `atendimento` não chama a porta de mensageria; SQL de `trabalho` só em
      `app/fila/`; `id_hotel` no `UPDATE` via `reserva`; `conversa` não importa
      `atendimento`; nenhum teste instancia adaptador WhatsApp real; falha de
      envio **depois** do POST não reabre. Rodar [quickstart.md](./quickstart.md),
      `pytest testes/unitarios -q` e a integração desta fatia
      (`test_resolver_chamado.py`, `test_solicitacoes.py`,
      `test_conformidade_do_esquema.py`, `test_garantias_do_banco.py`). Tudo
      verde, sem rede (SC-012)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: após Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: após Foundational — MVP HTTP (fecha + agenda)
- **US2 (Phase 4)**: após US1 — **é o corte do worker**
- **US3 (Phase 5)**: após US1 (mesmo POST)
- **US4 (Phase 6)**: após US1 (GET + UPDATE)
- **US5 (Phase 7)**: após US1 (rota existente para 403/404)
- **US6 (Phase 8)**: após US2 (processador de envio)
- **US7 (Phase 9)**: após US2
- **US8 (Phase 10)**: após US1 (e de preferência US3/US6 para os eventos)
- **Polish (Phase 11)**: após as histórias desejadas

### User Story Dependencies

- **US1**: após Phase 2 — sem dependência de outra história; **é o corte HTTP**
- **US2**: após US1; **T023 é atômico** (allowlist + ramo)
- **US3**: após US1; o `UPDATE` condicional já nasce na T011 — esta fase trava o HTTP
- **US4**: após US1; sem mudança de contrato do GET se o filtro F3.4 permanecer
- **US5**: após US1
- **US6**: após US2
- **US7**: após US2
- **US8**: após US1

### Within Each User Story

1. Testes escritos e **vermelhos pelo motivo certo**
2. Implementação mínima
3. Verde
4. Só então a próxima história

### Parallel Opportunities

- T001 e T002 em paralelo
- T005 em paralelo com T003/T004
- T008/T009 em paralelo com T010/T011 depois de T007 (arquivos distintos)
- T012/T013 depois de T007
- T014/T015 depois de T013
- T016 e T017 em paralelo na US1
- T019 e T020 em paralelo na US2; T021 no arquivo de integração
- T023 é atômico (allowlist + elif)
- T024 em paralelo com T025 na US3
- T027 e T028 em paralelo na US4
- T032 em paralelo com T033 na US6
- T039, T040 e T041 em paralelo no polish

**Sequência obrigatória em Foundational**: T003 → T004 → T006 → T007. Ver a
conformidade vermelha entre T004 e T007 é a prova de que ela vigia o documento.

**Sequência obrigatória na US2**: T022 (processador) pode anteceder T023, mas
**T023 é atômico**. Não mergear allowlist sozinha. Não enfileirar no POST antes
do ramo existir se o worker da suíte de integração já passar `--uma-passagem`
(T021 espera o ramo).

---

## Parallel Example: User Story 1

```text
# Testes em paralelo (antes da implementação):
T016 test_resolver.py (postgres + espião de agendar)
T017 test_resolver_chamado.py (POST HTTP)

# Depois:
T018 schema + router + default do agendar
```

## Parallel Example: User Story 2

```text
T019 test_confirmacao_resolucao.py   (processador)
T020 test_claim_enviar_confirmacao_resolucao.py
T021 test_resolver_chamado.py        (integração worker)

# Depois:
T022 processar_trabalho_enviar_confirmacao_resolucao
T023 allowlist + elif                 (juntos)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: POST fecha a pendência e agenda o recado; GET não lista o item
4. Demo: staff clica; `SELECT` de `solicitacao.resolvida_em` e do trabalho
   pendente. O envio visível ao hóspede é a US2

### Incremental Delivery

1. US1 → clique + autor/instante + some da passagem de turno
2. US2 → hóspede recebe o recado
3. US3 → segundo clique recusado
4. US4 → o que não foi clicado permanece visível
5. US5 → gestão e hotel B não fecham
6. US6 → falha de envio não reabre
7. US7 → retry não duplica recado
8. US8 → log limpo
9. Polish → consumo/`em_andamento`/estado do projeto/quickstart

### Suggested MVP scope

**US1** (T001–T018) prova o valor interno (ciclo fecha no painel). **US2 é
aceite obrigatório** antes de marcar F3.6 concluída (hóspede avisado — critério
do backlog). **US3** é o “não resolve duas vezes” do backlog. US4 é a passagem
de turno. US5 é a matriz. US6 e US7 são “gravar antes de enviar” e
idempotência. US8 é P2 e entra nesta entrega no padrão das fatias anteriores
(Artigo VIII).

---

## Notes

- [P] = arquivos distintos, sem depender de tarefa incompleta da mesma sequência
- Sem React, sem `GET /solicitacoes/{id}`, sem atribuir, sem cancelar, sem
  template Utility, sem pulso, sem inferência de conserto, sem LLM
- `GET /solicitacoes` **não** ganha campo — só perde o item resolvido
- Nenhum teste chama o adaptador WhatsApp real
- Commit por tarefa ou grupo lógico **só se o usuário pedir commit**
- Evitar: allowlist sem ramo; `conversa` UPDATE em `solicitacao`; `atendimento`
  chamar a porta de envio; nome/telefone no `200` do POST; texto em log; `200`
  no segundo clique; reabrir por falha de envio; ciclo `conversa` ↔
  `atendimento`; default de prazo novo; tela agregada de turno
