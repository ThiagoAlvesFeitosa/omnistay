---
description: "Task list for feature implementation"
---

# Tasks: Abrir Chamado de Reclamação

**Input**: Design documents from `/specs/014-abrir-chamado-reclamacao/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de produção
antes de um teste que falhe pela ausência dela, e pelo motivo certo.

**Organization**: Tarefas agrupadas por história (US1–US9), na ordem da spec. Esquema
(`abrir_chamado_reclamacao` + unicidade + semente do prazo), funções puras,
`abrir_reclamacao` e enqueue **sem claim** entram na Foundational. O corte que
**liga** o worker (enqueue na classificação + allowlist + ramo) fica na US1 — os
três no mesmo passo, para não deixar `tipo_desconhecido` no meio do caminho.
`GET /solicitacoes` já existe (F3.4); a US3 só estende o JSON. O atalho de janela
é a US4. O destaque por tempo é a US6. Classificar `reclamacao_tecnica` **continua**
sem INSERT em `solicitacao` até o worker consumir o tipo.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US9)

## Como ver os testes falharem nesta fatia

**Esquema.** `testes/integracao/test_conformidade_do_esquema.py` compara o banco
migrado com `docs/04-schema.sql`. Editar o documento **antes** da revisão deixa a
conformidade vermelha apontando `abrir_chamado_reclamacao` / o único novo / a
chave de prazo. A revisão `0013` a devolve ao verde.

**Janela / recado.** Funções puras: o teste falha até o módulo existir.

**`abrir_reclamacao`.** O unitário falha por `AttributeError` até o serviço existir.

**Claim / worker.** Hoje a allowlist **não** inclui `abrir_chamado_reclamacao` e o
consumidor não tem ramo. Os testes da US1 ficam vermelhos até allowlist e `elif`
existirem juntos. Não colocar o tipo na allowlist na Foundational — senão
`--uma-passagem` marca `tipo_desconhecido` antes do serviço existir.

**F3.2 / F3.4.** `test_reclamacao_nao_abre_chamado` em
`testes/unitarios/modulos/conversa/test_classificar_mensagem.py` **inverte o
enqueue, não a fronteira**: passa a exigir `abrir_chamado_reclamacao` enfileirado
e **continua** a proibir INSERT de `solicitacao` no classificar. Pedido **não**
gera este tipo. `test_pedido_e_reclamacao_nao_enfileiram_responder` **permanece**.

---

## Phase 1: Setup

**Purpose**: factories da reclamação, sem repetir payload em cada arquivo

- [X] T001 [P] Criar `testes/suporte/reclamacao.py` com helpers: texto com quarto
      e sem horário (`o ar do quarto 402 nao esta gelando`), texto com horário na
      origem (`o chuveiro vazou, pode ser depois das 16h`), texto sem quarto
      (`o ar nao esta gelando`), resposta só de horário (`depois das 14h`), eixos
      `reclamacao_tecnica` / `negativo` / `alta` e variante sentimento `neutro`
      via `testes/suporte/classificacao.py`. Sem segredo, sem rede
- [X] T002 [P] Em `testes/suporte/classificacao.py`, documentar no docstring que
      `reclamacao_tecnica` classificada é o gancho da F3.5
      (`abrir_chamado_reclamacao`). Sem mudar eixos nem HMAC

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: tipo `abrir_chamado_reclamacao` no banco, unicidade por mensagem,
semente de `horas_destaque_chamado_aberto`, `extrair_janela_preferencia` /
`parece_resposta_de_horario`, recado de confirmação, `abrir_reclamacao`,
gravação do JSON da recebida, `enfileirar_abrir_chamado_reclamacao` **ainda sem
claim**. Nenhuma história consome o trabalho ainda. Classificar **ainda não**
enfileira. **Nenhuma rota HTTP nova.**

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. Ordem do esquema:
T003 → T004 → T006 → T007 (teste vermelho no documento, depois migração verde).

- [X] T003 Estender `testes/integracao/test_garantias_do_banco.py`: `INSERT` em
      `trabalho` com `tipo = 'abrir_chamado_reclamacao'` aceito; segundo `INSERT`
      com o mesmo `payload.id_mensagem` viola
      `uq_trabalho_abrir_chamado_reclamacao_mensagem`. Rodar e **ver falhar**
      (FR-015, [data-model.md](./data-model.md)). A unicidade de
      `solicitacao.id_mensagem_origem` **já existe** na `0012` — não recriar o
      teste, só garantir que reclamação também a herda quando a US1 inserir
- [X] T004 Aplicar o delta em `docs/04-schema.sql`: `ck_trabalho_tipo` inclui
      `abrir_chamado_reclamacao`; índice
      `uq_trabalho_abrir_chamado_reclamacao_mensagem`; `COMMENT` de
      `parametro_hotel` lista `horas_destaque_chamado_aberto`. **Não** alterar
      `vw_fila_do_dia` nem colunas de `solicitacao`. Rodar
      `testes/integracao/test_conformidade_do_esquema.py` e **ver falhar** pela
      divergência
- [X] T005 [P] Alinhar `docs/04-modelagem-de-dados.md`: tipo
      `abrir_chamado_reclamacao`; JSON com `resposta = confirmacao_reclamacao` e
      `id_solicitacao`; chamado desta fatia **é** `solicitacao` tipo
      `reclamacao`, com `janela_preferencia` escrita; chave
      `horas_destaque_chamado_aberto`. Não dizer que reclamação classificada
      permanece sem chamado
- [X] T006 Criar `alembic/versions/sql/0013_abrir_chamado_reclamacao.sql` — cópia
      congelada do CHECK, do índice e do `INSERT` da chave
      `horas_destaque_chamado_aberto = 2` por hotel (padrão da `0007`/`0008`)
- [X] T007 Criar `alembic/versions/0013_abrir_chamado_reclamacao.py`
      (`down_revision = "0012_registrar_pedido_servico"`), `upgrade` executa o
      SQL congelado, `downgrade` restaura o CHECK da `0012` e remove o índice
      (não apaga o parâmetro). Semear a mesma chave no bootstrap em
      `app/modulos/propriedade/service.py`. Estender
      `testes/unitarios/modulos/propriedade/test_bootstrap.py` para exigir
      `horas_destaque_chamado_aberto == "2"`. T003, bootstrap e a conformidade
      verdes
- [X] T008 [P] Unitário em `testes/unitarios/modulos/atendimento/test_janela.py`:
      `extrair_janela_preferencia` e `parece_resposta_de_horario` nos exemplos de
      [contracts/quarto-e-janela.md](./contracts/quarto-e-janela.md). **Ver
      falhar** (FR-007, FR-008, FR-009)
- [X] T009 Implementar as duas funções em `app/modulos/atendimento/janela.py`
      (módulo puro, sem SQL, sem HTTP, teto 60 caracteres). T008 verde
- [X] T010 [P] Unitário em
      `testes/unitarios/modulos/conversa/test_texto_confirmacao_reclamacao.py`:
      `montar_confirmacao_reclamacao` confirma recebimento e acionamento da
      manutenção, usa só o prenome; com `perguntar_horario=True` pergunta o
      horário; com `False` **não** pergunta; **não** cita prazo de conserto nem
      catálogo; **não** inclui o texto da reclamação. **Ver falhar** (FR-004,
      FR-007, [contracts/mensageria-sessao.md](./contracts/mensageria-sessao.md))
- [X] T011 Implementar `montar_confirmacao_reclamacao` em
      `app/modulos/conversa/texto_confirmacao_reclamacao.py` (função pura, padrão
      da confirmação de pedido). T010 verde
- [X] T012 [P] Unitário em
      `testes/unitarios/modulos/atendimento/test_abrir_reclamacao.py`:
      `abrir_reclamacao` insere `solicitacao` tipo `reclamacao`, `status=aberta`,
      descrição = conteúdo, quarto extraído ou nulo, janela extraída ou nula,
      urgência copiada, `id_mensagem_origem` preenchido, **zero** linha em
      `consumo`; reserva de outro hotel não insere. **Ver falhar** (FR-001,
      FR-003, FR-014, FR-019)
- [X] T013 Implementar `inserir_reclamacao` em
      `app/modulos/atendimento/repository.py` e `abrir_reclamacao` em
      `app/modulos/atendimento/service.py` (`id_hotel` batendo em
      `reserva.id_hotel`). `abrir_servico` **não** muda de contrato. T012 verde.
      Depende de T007
- [X] T014 [P] Unitário em
      `testes/unitarios/modulos/conversa/test_abrir_chamado.py` (criar):
      `gravar_confirmacao_reclamacao` atualiza JSON da recebida com
      `resposta=confirmacao_reclamacao`, `id_mensagem_resposta`,
      `id_solicitacao`; `desfecho` permanece `classificado`; **não** altera
      `conteudo` nem eixos; `id_hotel` tem de conferir. **Ver falhar** (FR-006,
      FR-019)
- [X] T015 Implementar a gravação em `app/modulos/conversa/repository.py`
      (`UPDATE` de `classificacao_bruta` com `WHERE` na mensagem **e** `id_hotel`
      via `reserva`; reusar `inserir_mensagem_enviada_pendente` para a enviada).
      T014 verde
- [X] T016 [P] Unitário em
      `testes/unitarios/fila/test_enfileirar_abrir_chamado_reclamacao.py`:
      `enfileirar_abrir_chamado_reclamacao` insere tipo e payload só com IDs.
      **Ver falhar** ([contracts/fila-e-worker.md](./contracts/fila-e-worker.md)).
      Depende de T007
- [X] T017 Implementar `enfileirar_abrir_chamado_reclamacao` em
      `app/fila/repository.py` e `app/fila/service.py`. **Não** incluir o tipo em
      `TIPOS_CONSUMIVEIS`. T016 verde

**Checkpoint**: esquema aceita o tipo; janela e recado existem; dá para abrir
reclamação, gravar JSON e enfileirar. Worker **não** consome o tipo. Classificar
**não** enfileira ainda. `GET /solicitacoes` ainda sem os campos novos.

---

## Phase 3: User Story 1 - Reclamação vira chamado e o hóspede é confirmado (Priority: P1) 🎯 MVP

**Goal**: `reclamacao_tecnica` classificada → confirmação padrão gravada e enviada
(manutenção acionada; pergunta de horário se a janela for nula), uma
`solicitacao` tipo `reclamacao` com descrição, quarto e janela quando o texto da
origem os tiver, zero `consumo`, trabalho `concluido`, flag humano da fila do
dia **falso**.

**Independent Test**: mensagem já `classificado`/`reclamacao_tecnica` com
`o ar do quarto 402 nao esta gelando` → enviada de confirmação com pergunta de
horário, uma solicitação `reclamacao` com `numero_quarto=402`, janela nula,
descrição igual ao texto, `count(consumo)=0`,
`precisa_atendimento_humano=false`.

### Tests for User Story 1 ⚠️

- [X] T018 [P] [US1] Em
      `testes/unitarios/modulos/conversa/test_abrir_chamado.py`: repositório
      falso + `abrir_reclamacao` espião + `MensageriaFalsa` →
      `processar_trabalho_abrir_chamado` insere enviada com o recado (pergunta
      horário se janela nula), chama `abrir_reclamacao` com descrição = conteúdo,
      quarto `402` e janela `None`, atualiza JSON, chama `enviar_texto_sessao`
      **depois** de gravar, marca trabalho `concluido`. **Ver falhar** (FR-001,
      FR-003, FR-004, FR-006, FR-020)
- [X] T019 [P] [US1] Unitário em
      `testes/unitarios/fila/test_claim_abrir_chamado_reclamacao.py`:
      `reclamar_proximo` **devolve** `abrir_chamado_reclamacao` quando é o único
      pendente. **Ver falhar** (hoje a allowlist exclui)
- [X] T020 [P] [US1] Unitário em
      `testes/unitarios/modulos/conversa/test_classificar_mensagem.py`:
      `processar_trabalho_classificar_mensagem` com `reclamacao_tecnica`
      **enfileira** `abrir_chamado_reclamacao` e **não** chama gateway nem
      `abrir_reclamacao`. Inverter `test_reclamacao_nao_abre_chamado` para esse
      contrato (continua sem INSERT). Caminho “já classificada” sem trabalho de
      chamado também enfileira. Pedido continua só `registrar_pedido_servico`;
      dúvida continua só `responder_duvida`. Sentimento `neutro` também
      enfileira. **Ver falhar** (research §1, FR-014)
- [X] T021 [US1] Integração em `testes/integracao/test_abrir_chamado.py`
      (criar): webhook + `LLMFalso` em `reclamacao_tecnica` +
      `processar_uma_passagem` → recebida intocada, existe enviada de
      confirmação, uma `solicitacao` `reclamacao` com quarto `402`, zero
      `consumo`, `precisa_atendimento_humano=false`, `reserva.status=hospedado`.
      **Ver falhar** até o worker consumir o tipo (SC-001, SC-006)

### Implementation for User Story 1

- [X] T022 [US1] Implementar `processar_trabalho_abrir_chamado` em
      `app/modulos/conversa/service.py`: recado (`perguntar_horario` se
      `extrair_janela_preferencia` nulo); gravar enviada; `abrir_reclamacao`
      injetado; atualizar JSON; `gateway.enviar_texto_sessao`;
      `marcar_concluido`. Sem importar `atendimento` no módulo (callbacks). Sem
      LLM. Sem catálogo. T018 verde no caminho feliz
- [X] T023 [US1] Em `app/modulos/conversa/service.py`, ao gravar
      `reclamacao_tecnica` + `classificado` (e no caminho já classificada),
      chamar `enfileirar_abrir_chamado_reclamacao`. Em `app/fila/repository.py`,
      incluir o tipo na allowlist. Em `worker/consumidor.py`, ramo com `gateway`
      e `abrir_reclamacao=atendimento.abrir_reclamacao` — **enqueue, allowlist e
      ramo no mesmo passo**. T019, T020 e T021 verdes. Nunca allowlist sem ramo
      (research §1)

**Checkpoint**: `--uma-passagem` classifica reclamação técnica, confirma e abre
solicitação tipo `reclamacao` sem cobrança. Campos novos do GET ainda não
existem (US3). Follow-up de horário ainda não existe (US4).

---

## Phase 4: User Story 2 - Confirmação antes do chamado (Priority: P1)

**Goal**: na transação, a enviada de confirmação é inserida **antes** de
`abrir_reclamacao`; o recado não promete prazo de conserto nem fato da casa.

**Independent Test**: espião de `abrir_reclamacao` observa que a enviada já
existe quando a solicitação nasce; o corpo é o recado da T011.

### Tests for User Story 2 ⚠️

- [X] T024 [P] [US2] Unitário em `test_abrir_chamado.py`: o espião de
      `abrir_reclamacao` verifica que a mensagem enviada de confirmação **já
      está** no repositório no instante da chamada; se `abrir_reclamacao`
      levantar, a transação não deixa solicitação órfã sem enviada. O corpo
      enviado não contém prazo de conserto nem catálogo. **Ver falhar** (FR-004,
      FR-005, SC-002)

### Implementation for User Story 2

- [X] T025 [US2] Garantir a ordem em `processar_trabalho_abrir_chamado` (
      `app/modulos/conversa/service.py`): INSERT enviada → `abrir_reclamacao` →
      JSON → envio. T024 verde — se T022 já ordenava, esta tarefa é o teste de
      ordem e o ajuste se o serviço chamava `abrir_reclamacao` primeiro

**Checkpoint**: zero reclamações tramitam sem confirmação gravada.

---

## Phase 5: User Story 3 - Alert Center sem ficha cadastral (Priority: P1)

**Goal**: `GET /solicitacoes` lista também `tipo=reclamacao`; o item ganha
`janela_preferencia` e `destaque_tempo_excedido` (este último `false` até a
US6); staff, recepção e gestão veem o mesmo JSON **sem** nome/telefone/documento;
hotel B não vê A.

**Independent Test**: staff da propriedade A autentica, `GET /solicitacoes`
devolve o chamado aberto com quarto, tipo `reclamacao` e janela nula ou
preenchida; o JSON não tem nome nem telefone; staff B vê lista sem o item de A.

### Tests for User Story 3 ⚠️

- [X] T026 [P] [US3] Estender
      `testes/unitarios/modulos/atendimento/test_listar_abertas.py`: após
      `abrir_reclamacao`, `listar_abertas(id_hotel)` devolve o item com `tipo`,
      `janela_preferencia` e `destaque_tempo_excedido`; chaves cadastrais
      ausentes; pedido `servico` da F3.4 continua listado com
      `janela_preferencia` nulo e destaque `false`; hotel B vazio. Atualizar
      `CHAVES_ESPERADAS`. **Ver falhar** (FR-010, FR-011, FR-019,
      [contracts/api-de-atendimento.md](./contracts/api-de-atendimento.md))
- [X] T027 [P] [US3] Estender `testes/integracao/test_solicitacoes.py`: após um
      chamado da US1 (ou `abrir_reclamacao` direto), login staff A →
      `GET /solicitacoes` 200 com o item `reclamacao` e **sem** chaves
      cadastrais; recepção e gestão A também 200 no mesmo formato; staff B 200
      sem o item de A. **Ver falhar** (SC-007, SC-008)

### Implementation for User Story 3

- [X] T028 [US3] Incluir `janela_preferencia` no SELECT de
      `app/modulos/atendimento/repository.py`; em
      `app/modulos/atendimento/service.py` projetar
      `destaque_tempo_excedido=False` (cálculo real é a US6); atualizar
      `app/modulos/atendimento/schema.py`. Sem rota nova. T026 e T027 verdes

**Checkpoint**: a equipe vê o chamado no mesmo Alert Center da F3.4, sem ficha.

---

## Phase 6: User Story 4 - Horário pedido e registrado, sem atrasar o chamado (Priority: P1)

**Goal**: origem com horário → janela gravada e recado **sem** pergunta; origem
sem horário → pergunta no recado e chamado mesmo assim; follow-up
`depois das 14h` preenche o mesmo chamado, sem LLM, sem segunda confirmação, sem
segundo chamado. Não espera a resposta para abrir.

**Independent Test**: (a) `pode ser depois das 16h` na origem → janela no
chamado, recado sem pergunta; (b) origem sem horário abre mesmo assim; (c)
webhook `depois das 14h` com chamado aberto sem janela → mesma `id_solicitacao`,
zero segunda enviada.

### Tests for User Story 4 ⚠️

- [X] T029 [P] [US4] Unitário em `test_abrir_chamado.py`: conteúdo com
      `depois das 16h` → `abrir_reclamacao` com essa janela e recado
      `perguntar_horario=False`; conteúdo sem horário → janela `None` e
      `perguntar_horario=True`, chamado mesmo assim. **Ver falhar** (FR-007,
      FR-008, SC-003)
- [X] T030 [P] [US4] Unitário em
      `testes/unitarios/modulos/atendimento/test_abrir_reclamacao.py`:
      `completar_janela_se_resposta` preenche a reclamação aberta mais antiga
      sem janela da reserva; devolve `None` se o texto não
      `parece_resposta_de_horario`, se não houver chamado aberto, ou se o hotel
      não bater; segunda chamada com janela já preenchida é no-op. **Ver falhar**
      (FR-009)
- [X] T031 [P] [US4] Unitário em `test_classificar_mensagem.py`: com
      `completar_janela` injetado e reclamação aberta sem janela, texto
      `depois das 14h` → `desfecho=janela_registrada`, **zero** chamada ao LLM,
      **zero** enqueue de `abrir_chamado_reclamacao`, **zero** envio. Texto
      `o chuveiro tambem vazou` **não** toma o atalho (segue classificação).
      **Ver falhar** (research §4)
- [X] T032 [US4] Integração em `testes/integracao/test_abrir_chamado.py`: depois
      do cenário da US1, webhook `depois das 14h` + passagem → mesma
      `solicitacao` com janela, zero segunda enviada, zero segunda linha.
      Origem que já traz horário não pergunta de novo. **Ver falhar** (SC-003,
      SC-004)

### Implementation for User Story 4

- [X] T033 [US4] Implementar `completar_janela_se_resposta` em
      `app/modulos/atendimento/repository.py` e
      `app/modulos/atendimento/service.py`. T030 verde
- [X] T034 [US4] Em `processar_trabalho_classificar_mensagem` (
      `app/modulos/conversa/service.py`): **antes** do LLM, chamar o colaborador
      `completar_janela`; se devolver id, gravar `janela_registrada` e concluir.
      Worker injeta `completar_janela=atendimento.completar_janela_se_resposta`.
      Garantir em `processar_trabalho_abrir_chamado` a pergunta condicional
      (T029). T031 e T032 verdes. `conversa` não escreve SQL em `solicitacao`

**Checkpoint**: o chamado não espera o horário; a resposta posterior não duplica
nem aciona a recepção como humano.

---

## Phase 7: User Story 5 - Reclamação sem quarto ainda confirma (Priority: P1)

**Goal**: mensagem sem palavra-chave de quarto ainda gera confirmação e
`solicitacao` com `numero_quarto` nulo; nenhum quarto é inventado.

**Independent Test**: `o ar nao esta gelando` → enviada + chamado visível com
quarto nulo.

### Tests for User Story 5 ⚠️

- [X] T035 [P] [US5] Unitário em `test_abrir_chamado.py`: conteúdo sem quarto →
      `abrir_reclamacao` com `numero_quarto=None`; enviada mesmo assim. **Ver
      falhar** (FR-002, SC-005)
- [X] T036 [US5] Integração em `testes/integracao/test_abrir_chamado.py`: webhook
      sem quarto + passagem → `numero_quarto` nulo, item em `GET /solicitacoes`
      (ou `SELECT`) permanece visível. **Ver falhar**

### Implementation for User Story 5

- [X] T037 [US5] Garantir em `processar_trabalho_abrir_chamado` (
      `app/modulos/conversa/service.py`) que `extrair_numero_quarto` nulo **não**
      aborta o registro. T035 e T036 verdes — se T022 já fazia, esta tarefa é o
      teste e o ajuste se o serviço recusava quarto vazio

**Checkpoint**: ausência de quarto não silencia o hóspede nem esconde o chamado.

---

## Phase 8: User Story 6 - Chamado antigo é destacado (Priority: P1)

**Goal**: reclamação aberta além de `horas_destaque_chamado_aberto` aparece com
`destaque_tempo_excedido=true`; dentro do prazo, `false`; pedido `servico`
sempre `false` nesta fatia; prazo ausente → todos `false` e log `prazo_ausente`,
sem número mágico.

**Independent Test**: relógio injetado além do prazo → destaque na reclamação;
serviço igualmente antigo sem destaque; hotel sem a chave → zero destaque.

### Tests for User Story 6 ⚠️

- [X] T038 [P] [US6] Unitário em `test_listar_abertas.py`: com relógio injetado e
      prazo `2`, reclamação com `aberta_em` há 3 horas →
      `destaque_tempo_excedido=true`; há 1 hora → `false`; `servico` há 3 horas
      → `false`. Sem a chave (ou valor não numérico) → todos `false`. **Ver
      falhar** (FR-013, SC-009, Artigo XIII)
- [X] T039 [P] [US6] Unitário em
      `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py` (ou o de
      atendimento, se o log nascer em `listar_abertas`): prazo ausente registra
      `prazo_ausente` com `id_hotel`, **sem** descrição nem janela. **Ver falhar**
      (FR-018)

### Implementation for User Story 6

- [X] T040 [US6] Em `app/modulos/atendimento/service.py`, `listar_abertas` lê
      `horas_destaque_chamado_aberto` via serviço/repositório de `propriedade`
      (não SQL direto), compara com `relogio.agora()` injetável, só destaca
      `tipo=reclamacao`. T038 e T039 verdes. Sem default `2` no código

**Checkpoint**: omissão de manutenção antiga fica visível no Alert Center.

---

## Phase 9: User Story 7 - Reprocessar não duplica (Priority: P1)

**Goal**: JSON já com `confirmacao_reclamacao` + `id_solicitacao` não insere
segunda enviada nem segundo chamado; enviada `pendente` só retenta o envio.

**Independent Test**: segunda passagem após o cenário da US1 → zero segunda
enviada, zero segunda `solicitacao`.

### Tests for User Story 7 ⚠️

- [X] T041 [P] [US7] Unitário em `test_abrir_chamado.py`: JSON já com
      `resposta=confirmacao_reclamacao` e `id_solicitacao` → zero segunda
      enviada, zero segunda chamada a `abrir_reclamacao`; se a enviada está
      `pendente`, chama `enviar_texto_sessao` uma vez. **Ver falhar** (FR-015,
      SC-010)
- [X] T042 [US7] Integração em `test_abrir_chamado.py`: segunda
      `processar_uma_passagem` após o chamado concluído; unicidade do banco já
      coberta na T003. **Ver falhar** até o guard existir

### Implementation for User Story 7

- [X] T043 [US7] Guard no `processar_trabalho_abrir_chamado` de
      `app/modulos/conversa/service.py` (research §8). T041 e T042 verdes.
      `IntegrityError` no enqueue (já classificada) continua só logando, como na
      F3.4

**Checkpoint**: retrabalho não aciona a manutenção duas vezes nem manda duas
mensagens.

---

## Phase 10: User Story 8 - Falha não perde o chamado (Priority: P1)

**Goal**: envio falho depois de gravar preserva enviada + `solicitacao` e
reagenda **só** mensageria; falha ao gravar não envia recado.

**Independent Test**: (a) `MensageriaFalsa` em modo falha após INSERT → chamado e
confirmação no banco, trabalho não `concluido` sem retry de envio; (b)
`abrir_reclamacao` levantando → zero `enviar_texto_sessao`.

### Tests for User Story 8 ⚠️

- [X] T044 [P] [US8] Unitário em `test_abrir_chamado.py`: após gravar, gateway
      com `FalhaDeEnvio` → enviada e `id_solicitacao` permanecem; **não**
      `marcar_concluido` sem reagendar envio; **não** chama `abrir_reclamacao` de
      novo. **Ver falhar** (FR-017, SC-011)
- [X] T045 [US8] Unitário em `test_abrir_chamado.py`: `abrir_reclamacao` levanta
      antes do envio → zero chamada a `enviar_texto_sessao`; trabalho não deixa
      solicitação pela metade (transação desfaz). **Ver falhar** (FR-016)

### Implementation for User Story 8

- [X] T046 [US8] Em `app/modulos/conversa/service.py`: capturar `FalhaDeEnvio`
      depois de gravar e reagendar mensageria (padrão da coleta / pedido);
      deixar a transação abortar se gravar falhar **antes** do envio. T044 e
      T045 verdes. Não usar `marcar_falha` por quarto ou janela ausentes

**Checkpoint**: mensageria caída atrasa a confirmação; não apaga o chamado.

---

## Phase 11: User Story 9 - Conteúdo não vaza em log (Priority: P2)

**Goal**: abertura, já aberto, envio falho, janela registrada e prazo ausente
logam identificadores, hotel e `resultado` — nunca reclamação, confirmação,
descrição, quarto ou janela em texto livre.

**Independent Test**: caplog nos desfechos; fixture de conteúdo ausente do log.

### Tests for User Story 9 ⚠️

- [X] T047 [P] [US9] Estender
      `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py`:
      `processar_trabalho_abrir_chamado` nos desfechos aberto, já aberto e envio
      falho, e o atalho `janela_registrada` — o texto da reclamação, o da
      confirmação e a janela não aparecem; há `id_mensagem` / `id_trabalho` /
      `id_hotel` / `resultado`. **Ver falhar** (FR-018, SC-012)

### Implementation for User Story 9

- [X] T048 [US9] Ajustar logs em `app/modulos/conversa/service.py` (eventos
      `chamado_aberto`, `chamado_ja_aberto`, `chamado_envio_falhou`,
      `janela_registrada` conforme
      [contracts/fila-e-worker.md](./contracts/fila-e-worker.md)). T047 verde
      (somar o `prazo_ausente` da T040 se ainda faltar)

**Checkpoint**: trilha técnica sem cópia da conversa.

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: intenções que não são reclamação, regressão F3.3/F3.4, fronteiras,
documentação, suíte

- [X] T049 [P] Unitário em `test_classificar_mensagem.py`: `duvida_geral`,
      `pedido_de_servico`, `upsell` e falha de classificação **não** inserem
      `abrir_chamado_reclamacao`. Integração: F3.4 de pedido e F3.3 de dúvida
      continuam **sem** `solicitacao` tipo `reclamacao` (FR-014, FR-020)
- [X] T050 [P] Integração: após chamado aberto, `GET /fila-do-dia` (recepção)
      permanece `precisa_atendimento_humano=false`; visão **não** ganhou
      desfecho novo (`testes/integracao/test_fila_do_dia.py` ou
      `test_abrir_chamado.py`) (FR-022)
- [X] T051 [P] Regressão: `testes/integracao/test_registrar_pedido.py`,
      `test_responder_duvida.py`, `test_classificar_mensagem.py` (ramos que não
      são reclamação), `test_webhook_estadia.py` e o claim de outros tipos
      continuam verdes; `registrar_pedido_servico` **não** chama
      `abrir_reclamacao`
- [X] T052 Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F3.5 em andamento/concluída,
      revisão `0013`, `abrir_chamado_reclamacao`, janela + destaque no
      `GET /solicitacoes`, próxima fatia **F3.6**. Não apontar F2.3
- [X] T053 Revisar fronteiras: `conversa` não escreve `solicitacao` (só
      callback); `atendimento` não envia mensagem; SQL de `trabalho` só em
      `app/fila/`; `id_hotel` em `abrir_reclamacao` / `completar_janela` /
      `listar_abertas`; nenhum teste instancia adaptador real de IA nem
      WhatsApp; falha de envio **depois** de gravar reagenda mensageria; prazo
      de destaque não é constante. Rodar [quickstart.md](./quickstart.md),
      `pytest testes/unitarios -q` e a integração desta fatia
      (`test_abrir_chamado.py`, `test_solicitacoes.py`,
      `test_classificar_mensagem.py`, `test_conformidade_do_esquema.py`,
      `test_garantias_do_banco.py`). Tudo verde, sem rede (SC-013)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: após Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: após Foundational — MVP (consumo + confirmação + `solicitacao`)
- **US2 (Phase 4)**: após US1 (mesmo serviço; ordem na transação)
- **US3 (Phase 5)**: após Foundational para `abrir_reclamacao`; na prática após
  US1 para ter chamado real. Pode semear `abrir_reclamacao` direto
- **US4 (Phase 6)**: após US1 (atalho de janela no classificar + pergunta
  condicional no processador)
- **US5 (Phase 7)**: após US1 (caminho quarto nulo)
- **US6 (Phase 8)**: após US3 (campo `destaque_tempo_excedido` já no JSON)
- **US7 (Phase 9)**: após US1 (guard no mesmo processador)
- **US8 (Phase 10)**: após US1 (falha de envio / gravação)
- **US9 (Phase 11)**: após os desfechos existirem (US1 / US4 / US7 / US8)
- **Polish (Phase 12)**: após as histórias desejadas

### User Story Dependencies

- **US1**: após Phase 2 — sem dependência de outra história; **é o corte do worker**
- **US2**: após US1 (estende o processador)
- **US3**: após T013; independente do worker se o teste semear `abrir_reclamacao`
- **US4**: após US1; precisa do enqueue da classificação para o atalho
- **US5**: após US1; não é novo tipo, é quarto nulo
- **US6**: após US3
- **US7**: após US1
- **US8**: após US1
- **US9**: após US1 (e de preferência US4/US7/US8 para os eventos)

### Within Each User Story

1. Testes escritos e **vermelhos pelo motivo certo**
2. Implementação mínima
3. Verde
4. Só então a próxima história

### Parallel Opportunities

- T001 e T002 em paralelo
- T005 em paralelo com T003/T004
- T008/T009, T010/T011 em paralelo entre si (arquivos distintos)
- T012/T013 depois de T007
- T014/T015 depois de T007
- T016/T017 depois de T007
- T018, T019 e T020 em paralelo na US1; T021 no arquivo novo de integração
- T023 é atômico (enqueue + allowlist + ramo)
- T026 e T027 em paralelo na US3
- T029, T030 e T031 em paralelo na US4
- T035 em paralelo com T036 na US5
- T038 em paralelo com T039 na US6
- T041 em paralelo com T042 na US7
- T044 em paralelo com T045 na US8
- T049, T050 e T051 em paralelo no polish

**Sequência obrigatória em Foundational**: T003 → T004 → T006 → T007. Ver a
conformidade vermelha entre T004 e T007 é a prova de que ela vigia o documento.

**Sequência obrigatória na US1**: T022 (serviço) pode anteceder T023, mas **T023 é
atômico**. Não mergear allowlist sozinha. Não enfileirar na classificação antes do
ramo existir.

---

## Parallel Example: User Story 1

```text
# Testes em paralelo (antes da implementação):
T018 test_abrir_chamado.py                         (serviço / caminho feliz)
T019 test_claim_abrir_chamado_reclamacao.py        (allowlist)
T020 test_classificar_mensagem.py                  (enqueue na classificação)
T021 test_abrir_chamado.py (integração)            — arquivo novo

# Depois:
T022 processar_trabalho_abrir_chamado
T023 enqueue + allowlist + elif                    (juntos)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: worker confirma reclamação e abre `solicitacao` tipo `reclamacao`;
   zero `consumo`; flag humano falso
4. Demo: webhook “o ar do quarto 402 nao esta gelando” + `--uma-passagem`;
   `SELECT` da enviada e da solicitação

### Incremental Delivery

1. US1 → confirmação + chamado sem cobrança
2. US2 → ordem confirmação → solicitação
3. US3 → Alert Center lista reclamação sem ficha
4. US4 → janela na origem e no follow-up, sem atrasar
5. US5 → quarto ausente não bloqueia
6. US6 → destaque por tempo da propriedade
7. US7 → idempotência
8. US8 → falha não perde o chamado
9. US9 → log limpo
10. Polish → intenções outras, estado do projeto, quickstart

### Suggested MVP scope

**US1** (T001–T023) prova o valor visível. **US2 e US3 são aceite obrigatório**
antes de marcar F3.5 concluída (confirmação antes de tramitar + Alert Center no
backlog). **US4 é o diferencial desta fatia** (horário sem silêncio). US5 é
Artigo I/XV. US6 é o critério “tempo excessivo”. US7 e US8 são os casos
obrigatórios de idempotência e “gravar antes de enviar”. US9 é P2 e entra nesta
entrega no padrão das fatias anteriores (Artigo VIII).

---

## Notes

- [P] = arquivos distintos, sem depender de tarefa incompleta da mesma sequência
- Sem React, sem `consumo`, sem resolver chamado, sem rota GET de histórico, sem
  LLM no ramo do chamado, sem inferência de check-in, sem quarto/horário mágico,
  sem pulso
- `test_reclamacao_nao_abre_chamado` **inverte só o enqueue** — classificar
  continua sem INSERT de `solicitacao`
- `test_pedido_e_reclamacao_nao_enfileiram_responder` **não** se inverte
- Nenhum teste chama o provedor real de IA nem o adaptador WhatsApp
- Commit por tarefa ou grupo lógico **só se o usuário pedir commit**
- Evitar: `marcar_falha` por quarto/janela nulos; allowlist sem ramo; enqueue na
  classificação antes do ramo; `conversa` escrever SQL em `solicitacao`;
  `atendimento` enviar WhatsApp; nome/telefone em `GET /solicitacoes`; texto ou
  janela em log; ligar `precisa_atendimento_humano`; default `2` no código quando
  o prazo faltar; ciclo `conversa` ↔ `atendimento`; esperar a janela para abrir
  o chamado
