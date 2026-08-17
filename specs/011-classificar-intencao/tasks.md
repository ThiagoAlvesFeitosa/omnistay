---
description: "Task list for feature implementation"
---

# Tasks: Classificar a Intenção

**Input**: Design documents from `/specs/011-classificar-intencao/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de produção
antes de um teste que falhe pela ausência dela, e pelo motivo certo.

**Organization**: Tarefas agrupadas por história (US1–US5), na ordem da spec. Esquema da
visão, porta `classificar` e taxonomia entram na fase Foundational. O corte que **inverte**
os testes da F3.1 (claim + worker consomem `classificar_mensagem`) fica na US1 — allowlist
e ramo no mesmo passo, para não deixar `tipo_desconhecido` no meio do caminho.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US5)

## Como ver os testes falharem nesta fatia

**Esquema.** `testes/integracao/test_conformidade_do_esquema.py` compara o banco migrado
com `docs/04-schema.sql`. Editar o documento **antes** da revisão deixa a conformidade
vermelha apontando `precisa_atendimento_humano`. A revisão `0010` a devolve ao verde.

**Porta.** Unitários que importam `ResultadoClassificacao` / `FalhaDeClassificacao` ou
chamam `LLMFalso.classificar` falham por `AttributeError` até a porta e o falso existirem.

**Taxonomia.** Função pura: valores fora da lista não têm implementação — o teste falha
até `validar_classificacao` existir.

**Serviço.** `processar_trabalho_classificar_mensagem` não existe; o unitário com
repositório falso falha por `AttributeError`.

**Claim / worker.** Hoje a allowlist **exclui** `classificar_mensagem` e o consumidor não
tem ramo. Os testes invertidos da F3.1 ficam vermelhos até allowlist e `elif` existirem
juntos. Não inverter esses testes na Foundational — senão `--uma-passagem` marca
`tipo_desconhecido` antes do serviço existir.

---

## Phase 1: Setup

**Purpose**: helper de fixture para estadia + trabalho pendente, sem repetir INSERT em
cada arquivo

- [X] T001 [P] Criar `testes/suporte/classificacao.py` com
      `ResultadoClassificacao` de exemplo (dúvida geral válida; eixos inválidos; bruto
      mínimo) **depois** que a porta existir — nesta tarefa só o esqueleto do módulo:
      `eixos_validos(*, intencao="duvida_geral") -> dict` com as três chaves da
      taxonomia, sem importar a porta ainda. Sem segredo, sem rede
- [X] T002 [P] Em `testes/suporte/webhook.py` (já existe), documentar no docstring que
      o caminho desta fatia é webhook (F3.1) + `python -m worker --uma-passagem` com
      `LLMFalso`. Sem mudar HMAC

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: visão `precisa_atendimento_humano`, porta `classificar`, taxonomia pura,
gravação dos eixos sem tocar `conteudo`, mapeamento na fila do dia. Nenhuma história
consome o trabalho ainda.

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. Ordem do esquema:
T003 → T004 → T006 → T007 (teste vermelho no documento, depois migração verde).

- [X] T003 Estender `testes/integracao/test_fila_do_dia.py` (ou
      `test_garantias_do_banco.py`): `SELECT precisa_atendimento_humano FROM
      vw_fila_do_dia LIMIT 0` aceito (coluna existe). Rodar e **ver falhar** (FR-008,
      [data-model.md](./data-model.md))
- [X] T004 Aplicar o delta em `docs/04-schema.sql`: `DROP`/`CREATE` de `vw_fila_do_dia`
      com `precisa_atendimento_humano` exatamente como em [data-model.md](./data-model.md);
      atualizar o `COMMENT ON VIEW`. Rodar
      `testes/integracao/test_conformidade_do_esquema.py` e **ver falhar** pela
      divergência
- [X] T005 [P] Alinhar `docs/04-modelagem-de-dados.md` §7.1: o worker da F3.2 **passa a
      consumir** `classificar_mensagem`; `classificacao_bruta` de estadia usa
      `tipo = classificacao_intencao` e os quatro `desfecho`; a visão ganha
      `precisa_atendimento_humano`. Não dizer que o item permanece pendente (isso era a
      F3.1)
- [X] T006 Criar `alembic/versions/sql/0010_classificar_intencao.sql` — cópia congelada
      do `CREATE VIEW` da T004 (visão vigente + a coluna nova). Sem mudar
      `ck_trabalho_tipo`
- [X] T007 Criar `alembic/versions/0010_classificar_intencao.py`
      (`down_revision = "0009_receber_mensagem"`), `upgrade` executa o SQL congelado,
      `downgrade` recria a visão da `0009` (sem o booleano). T003 e a conformidade
      verdes
- [X] T008 [P] Unitário em `testes/unitarios/adaptadores/test_llm_falso.py` (ou
      `testes/unitarios/portas/test_llm_classificar.py`): a porta declara
      `classificar`, `ResultadoClassificacao` (eixos + `bruto`) e
      `FalhaDeClassificacao(codigo)` distinta de `FalhaDeExtracao`. **Ver falhar**
      ([contracts/llm-e-classificacao.md](./contracts/llm-e-classificacao.md))
- [X] T009 Implementar em `app/portas/llm.py`: `FalhaDeClassificacao`,
      `ResultadoClassificacao`, `LLMProvider.classificar`. Não alterar
      `extrair_ficha`. T008 verde o bastante para importar os tipos
- [X] T010 [P] Em `testes/unitarios/adaptadores/test_llm_falso.py`: `classificar`
      configurável (`configurar_classificacao` / `falhar_classificacao`); default sem
      config devolve `duvida_geral` / `neutro` / `baixa`; `extrair_ficha` permanece
      idêntico (`irreconhecivel` sem config; `FalhaDeExtracao` no modo falha da ficha).
      **Ver falhar** (research §7)
- [X] T011 Implementar `classificar` em `app/adaptadores/llm_falso.py` com configuração
      **separada** da ficha. T010 verde; testes antigos de extração intactos
- [X] T012 [P] Unitário em `testes/unitarios/modulos/conversa/test_classificar_mensagem.py`:
      função pura `validar_classificacao` aceita os seis valores de intenção × três
      sentimentos × três urgências; rejeita eixo faltando, valor fora da lista e
      “classificação parcial”. **Ver falhar** (FR-002, FR-003)
- [X] T013 Implementar `validar_classificacao` em
      `app/modulos/conversa/classificacao.py` (módulo puro, sem SQL, sem HTTP). T012
      verde
- [X] T014 Unitário/integração com repositório real em
      `testes/unitarios/modulos/conversa/test_classificar_mensagem.py` (ou integração
      curta): `gravar_classificacao_intencao` preenche eixos + JSON
      `tipo=classificacao_intencao` e **não** altera `conteudo`; `id_hotel` da reserva
      tem de conferir. **Ver falhar** (FR-004, FR-005, FR-014)
- [X] T015 Implementar `gravar_classificacao_intencao` em
      `app/modulos/conversa/repository.py` (`UPDATE` de `intencao`, `sentimento`,
      `urgencia`, `classificacao_bruta` com `WHERE` na mensagem **e** `id_hotel` via
      `reserva`). Não reutilizar `gravar_classificacao_bruta` da ficha se isso
      apagaria eixos. T014 verde
- [X] T016 [P] Estender `testes/integracao/test_fila_do_dia.py`: item `hospedado` sem
      classificação de intenção devolve `precisa_atendimento_humano = false` no
      `GET /fila-do-dia` autenticado como recepção. **Ver falhar** até o schema
      mapear a coluna (T017). FR-008
- [X] T017 Acrescentar `precisa_atendimento_humano` em
      `app/modulos/hospedagem/schema.py` (`ItemFilaDoDia`), no `SELECT` de
      `app/modulos/hospedagem/repository.py` e no mapeamento de
      `app/modulos/hospedagem/service.py`. T016 verde. Nenhuma operação nova na matriz

**Checkpoint**: visão no banco; porta e falso classificam; taxonomia pura existe; dá
para gravar eixos; a fila expõe o booleano (ainda sempre falso). Worker **não** consome
o tipo.

---

## Phase 3: User Story 1 - Mensagem classificada ganha os três eixos (Priority: P1) 🎯 MVP

**Goal**: trabalho `classificar_mensagem` + classificador válido → intenção, sentimento,
urgência e bruto gravados; conteúdo intacto; trabalho `concluido`; zero resposta ao
hóspede.

**Independent Test**: mensagem de estadia pendente + `LLMFalso` em dúvida geral → eixos
preenchidos, `desfecho=classificado`, trabalho `concluido`, `conteudo` igual, zero
`mensagem` enviada, `precisa_atendimento_humano=false`.

### Tests for User Story 1 ⚠️

- [X] T018 [P] [US1] Em `testes/unitarios/modulos/conversa/test_classificar_mensagem.py`:
      repositório falso + `LLMFalso` configurado (`duvida_geral` / `neutro` / `baixa`)
      → `processar_trabalho_classificar_mensagem` grava os três eixos, JSON com
      `desfecho=classificado` e `bruto`, não chama gateway, marca trabalho `concluido`.
      **Ver falhar** (FR-001, FR-004, FR-012)
- [X] T019 [US1] Inverter `testes/unitarios/fila/test_claim_nao_consome_classificar.py`:
      `reclamar_proximo` **devolve** `classificar_mensagem` quando é o único pendente
      (e ainda pode preferir outro tipo se a ordem `id_trabalho` assim o fizer — o
      que importa é o tipo entrar na allowlist). **Ver falhar** (hoje a allowlist
      exclui). [contracts/fila-e-worker.md](./contracts/fila-e-worker.md)
- [X] T020 [US1] Substituir `test_worker_nao_consome_classificar_mensagem` em
      `testes/integracao/test_webhook_estadia.py` por
      `test_worker_classifica_mensagem_de_estadia`: webhook de hospedado +
      `--uma-passagem` com `LLMFalso` padrão → eixos `duvida_geral`/`neutro`/`baixa`,
      trabalho `concluido`, reserva `hospedado`, zero `solicitacao`. **Ver falhar**
- [X] T021 [P] [US1] Integração em `testes/integracao/test_classificar_mensagem.py`:
      conteúdo da mensagem idêntico antes/depois; `GET /fila-do-dia` com
      `precisa_atendimento_humano=false`. **Ver falhar** até o serviço existir
      (FR-005, SC-001, SC-004)

### Implementation for User Story 1

- [X] T022 [US1] Implementar `processar_trabalho_classificar_mensagem` em
      `app/modulos/conversa/service.py`: ler mensagem no `id_hotel` do trabalho;
      chamar `llm.classificar`; `validar_classificacao`; gravar
      `desfecho=classificado` para `duvida_geral` / `pedido_de_servico` /
      `reclamacao_tecnica`; `marcar_concluido`. Sem `reagendar`. Sem importar
      `hospedagem`. Sem `MensageriaGateway` e sem catálogo. T018 verde no caminho
      feliz
- [X] T023 [US1] Em `app/fila/repository.py`, incluir `classificar_mensagem` na
      allowlist de `reclamar_proximo`. Em `worker/consumidor.py`, ramo
      `processar_trabalho_classificar_mensagem` (**os dois no mesmo passo**). T019 e
      T020 verdes. Nunca allowlist sem ramo (research §1)
- [X] T024 [US1] Idempotência: se `classificacao_bruta->>'tipo'` já é
      `classificacao_intencao` com `desfecho`, não chamar o LLM e só
      `marcar_concluido`. Teste no mesmo `test_classificar_mensagem.py` (unitário:
      falso com contador de chamadas). FR-013

**Checkpoint**: `--uma-passagem` classifica dúvida geral e conclui o trabalho. Hóspede
ainda não recebe nada.

---

## Phase 4: User Story 2 - Serviço indisponível encaminha a uma pessoa (Priority: P1)

**Goal**: `FalhaDeClassificacao` preserva a mensagem, deixa eixos `NULL`, grava
`desfecho=indisponivel`, conclui o trabalho (sem retentativa de LLM) e liga o sinal
na fila da recepção.

**Independent Test**: falso com `falhar_classificacao` → conteúdo intacto, eixos nulos,
`precisa_atendimento_humano=true`, trabalho `concluido` (não `pendente` nem `falha`),
zero envio.

### Tests for User Story 2 ⚠️

- [X] T025 [P] [US2] Unitário em `test_classificar_mensagem.py`:
      `FalhaDeClassificacao("llm_indisponivel")` → JSON `desfecho=indisponivel` sem
      `bruto` obrigatório, eixos `NULL`, `marcar_concluido`, **zero** `reagendar` /
      `marcar_falha`. **Ver falhar** (FR-006, FR-012)
- [X] T026 [US2] Integração em `testes/integracao/test_classificar_mensagem.py`: após
      o worker, `GET /fila-do-dia` (recepção) tem
      `precisa_atendimento_humano=true` na reserva; gestão/staff continuam recusados
      na fila nominada. Reinício não é preciso matar processo: o sinal é coluna da
      visão. **Ver falhar** (FR-008, SC-002)

### Implementation for User Story 2

- [X] T027 [US2] No `processar_trabalho_classificar_mensagem` de
      `app/modulos/conversa/service.py`: capturar `FalhaDeClassificacao`, gravar
      desfecho humano **sem** preencher eixos, concluir o trabalho. Não copiar o
      backoff de `interpretar_ficha`. T025 e T026 verdes

**Checkpoint**: classificador caído não apaga a conversa e a recepção vê a pendência.

---

## Phase 5: User Story 3 - Resposta inválida também vai para humano (Priority: P1)

**Goal**: eixos incompletos ou fora da taxonomia não são usados para decidir; o bruto
fica para auditoria; sinal humano ligado; trabalho `concluido`.

**Independent Test**: falso devolve intenção `"nao_existe"` (ou omite urgência) com
`bruto` → eixos `NULL`, `desfecho=formato_invalido`, `bruto` no JSON, fila com sinal,
zero envio.

### Tests for User Story 3 ⚠️

- [X] T028 [P] [US3] Unitário em `test_classificar_mensagem.py`: resultado com eixo
      faltando **e** resultado com valor fora da lista → `formato_invalido`, eixos
      `NULL`, `bruto` preservado, trabalho `concluido`, sem ramo `classificado`.
      **Ver falhar** (FR-007, SC-003)
- [X] T029 [US3] Integração: `classificacao_bruta.bruto` recuperável no banco após o
      worker; `precisa_atendimento_humano=true`. **Ver falhar**

### Implementation for User Story 3

- [X] T030 [US3] Em `app/modulos/conversa/service.py`, se `validar_classificacao`
      rejeitar: gravar `formato_invalido` + `bruto`, eixos `NULL`, `marcar_concluido`.
      T028 e T029 verdes. Não tratar como “classificação parcial”

**Checkpoint**: lixo do modelo não roteia; dá para auditar o que veio.

---

## Phase 6: User Story 4 - Classificar não é responder nem abrir chamado (Priority: P1)

**Goal**: dúvida / pedido / reclamação só ficam registrados; upsell, checkout e fora de
escopo vão a humano visível; status da reserva não muda.

**Independent Test**: três mensagens classificadas como dúvida, serviço e reclamação
negativa → zero `enviada`, zero `solicitacao`; uma `upsell` → eixos gravados,
`desfecho=encaminhado_humano`, sinal `true`; `reserva.status` inalterado.

### Tests for User Story 4 ⚠️

- [X] T031 [P] [US4] Unitário/integração em `test_classificar_mensagem.py`:
      `reclamacao_tecnica`+`negativo`+`alta` e `pedido_de_servico` →
      `desfecho=classificado`, `count(solicitacao)=0`, zero chamada a gateway, zero
      leitura de catálogo (não passar `CatalogoRepository` ao serviço). **Ver falhar**
      se o ramo humano por intenção ainda não existir só neste teste — o caminho
      `classificado` já veio da US1; aqui o aceite é **ausência** de efeito (FR-009,
      SC-004)
- [X] T032 [US4] Unitário: `upsell`, `solicitacao_de_checkout` e `fora_de_escopo`
      válidos → eixos preenchidos, `desfecho=encaminhado_humano`. Integração: sinal
      `true` na fila. **Ver falhar** (FR-010, SC-005)
- [X] T033 [P] [US4] Assertar `reserva.status` inalterado em
      `testes/integracao/test_classificar_mensagem.py` (e que F1.3 /
      `test_interpretar_ficha.py` / `test_webhook_coleta.py` não passam a preencher
      `intencao` de estadia). FR-015

### Implementation for User Story 4

- [X] T034 [US4] Em `app/modulos/conversa/classificacao.py` + `service.py`: intenções
      `upsell` / `solicitacao_de_checkout` / `fora_de_escopo` gravam
      `encaminhado_humano` (eixos preenchidos). As outras três válidas continuam
      `classificado`. T032 verde. T031 deve permanecer verde — não inserir
      `solicitacao` “já que reclamação classificou”

**Checkpoint**: a fatia decide; F3.3–F3.5 é que executam os ramos automáticos/operacionais.

---

## Phase 7: User Story 5 - Conteúdo não vaza em log (Priority: P2)

**Goal**: sucesso, indisponível e inválido logam identificadores, hotel, desfecho e
intenção quando houver — nunca o texto, nunca o `bruto`.

**Independent Test**: caplog nos três desfechos; fixture de conteúdo ausente do log.

### Tests for User Story 5 ⚠️

- [X] T035 [P] [US5] Estender `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py`:
      `processar_trabalho_classificar_mensagem` nos desfechos `classificado`,
      `indisponivel` e `formato_invalido` — o texto da mensagem e o dict `bruto` não
      aparecem; há `id_mensagem` / `id_trabalho` / `id_hotel` / `desfecho` (e
      `intencao` no sucesso). **Ver falhar** se o log atual ecoar o retorno do LLM
      (FR-011, SC-006)

### Implementation for User Story 5

- [X] T036 [US5] Ajustar logs em `app/modulos/conversa/service.py` (eventos
      `mensagem_classificada`, `classificacao_indisponivel`,
      `classificacao_formato_invalido` conforme
      [contracts/fila-e-worker.md](./contracts/fila-e-worker.md)). T035 verde. Não
      logar `mensagem["conteudo"]` nem `resultado.bruto`

**Checkpoint**: trilha técnica sem cópia da conversa nem do payload do modelo.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: isolamento, regressão F1.3, fronteiras, documentação, suíte

- [X] T037 [P] Isolamento: em `testes/integracao/test_classificar_mensagem.py` (ou
      `test_fila_do_dia.py`), classificação no hotel A não aparece na fila do hotel B;
      `gravar_classificacao_intencao` com `id_hotel` errado não atualiza a mensagem
      (FR-014)
- [X] T038 [P] Regressão: `testes/integracao/test_webhook_coleta.py`,
      `test_interpretar_ficha.py` e o claim de outros tipos continuam verdes;
      `interpretar_ficha` **não** chama `classificar` e vice-versa
- [X] T039 [P] `testes/integracao/test_rotas_protegidas.py`: `GET /fila-do-dia` segue
      só recepção; nenhuma operação nova na matriz
      ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))
- [X] T040 Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F3.2 em andamento/concluída,
      revisão `0010`, worker consome `classificar_mensagem`, sinal na fila, próxima
      fatia **F3.3**. Não apontar F2.3
- [X] T041 Revisar fronteiras: `conversa` não escreve `reserva.status` nem
      `solicitacao`; SQL de `trabalho` só em `app/fila/`; `hospedagem` só projeta a
      visão; nenhum teste instancia adaptador real de IA nem WhatsApp; texto vazio /
      trabalho órfão não inventa conteúdo para o LLM (encaminha como inválido/humano
      se aparecer)
- [X] T042 Completar `eixos_validos` / factories em `testes/suporte/classificacao.py`
      usando `ResultadoClassificacao` da porta (T001). Rodar
      [quickstart.md](./quickstart.md), `pytest testes/unitarios -q` e a integração
      desta fatia (`test_classificar_mensagem.py`, `test_webhook_estadia.py`,
      `test_fila_do_dia.py`, `test_conformidade_do_esquema.py`, claim invertido).
      Tudo verde, sem rede

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: após Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: após Foundational — MVP (consumo do trabalho + classificação válida)
- **US2 (Phase 4)**: após US1 (mesmo serviço; ramo de exceção)
- **US3 (Phase 5)**: após US1 (validação já existe; o serviço ainda não gravava inválido)
- **US4 (Phase 6)**: após US1; T032 depende do sinal da visão (Phase 2) e do serviço
- **US5 (Phase 7)**: após US1, de preferência após US2/US3 para cobrir os três logs
- **Polish (Phase 8)**: após as histórias desejadas

### User Story Dependencies

- **US1**: após Phase 2 — sem dependência de outra história; **é o corte do worker**
- **US2**: após US1 (estende `processar_trabalho_classificar_mensagem`)
- **US3**: após US1 (e T013); independente da US2 no arquivo de teste, mesmo `service.py`
- **US4**: após US1; T031 é aceite negativo sobre a US1; T032 é comportamento novo
- **US5**: após os desfechos existirem

### Within Each User Story

1. Testes escritos e **vermelhos pelo motivo certo**
2. Implementação mínima
3. Verde
4. Só então a próxima história

### Parallel Opportunities

- T001 e T002 em paralelo
- T005 em paralelo com T003/T004
- T008 em paralelo com o esquema (arquivo distinto); T009 depois de T008
- T010/T011 depois de T009; T012/T013 em paralelo com T010/T011
- T014/T015 depois de T007 (INSERT real precisa da visão? não — só `mensagem`)
- T016 depois de T007; T017 depois de T016
- T018 e T021 em paralelo na US1; T019 → T023 (mesmo claim)
- T025 em paralelo com T026 na US2 depois da US1
- T028 em paralelo com T029 na US3
- T031 e T033 em paralelo na US4
- T037, T038 e T039 em paralelo no polish

**Sequência obrigatória em Foundational**: T003 → T004 → T006 → T007. Ver a conformidade
vermelha entre T004 e T007 é a prova de que ela vigia o documento.

**Sequência obrigatória na US1**: T022 (serviço) pode anteceder T023, mas **T023 é
atômico** (allowlist + ramo). Não mergear allowlist sozinha.

---

## Parallel Example: User Story 1

```text
# Testes em paralelo (antes da implementação):
T018 test_classificar_mensagem.py     (serviço / repositório falso)
T021 test_classificar_mensagem.py     (integração conteúdo + fila) — arquivo pode ser o mesmo: em série com T018 se necessário
T019 test_claim_nao_consome_classificar.py  (inverter)
T020 test_webhook_estadia.py          (worker classifica)

# Depois:
T022 processar_trabalho_classificar_mensagem  (caminho classificado)
T023 allowlist + elif no consumidor           (juntos)
T024 idempotência
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: worker classifica dúvida geral; trabalho `concluido`; hóspede sem resposta
4. Demo: webhook de estadia + `--uma-passagem`; `SELECT` eixos; fila com flag falso

### Incremental Delivery

1. US1 → classificação válida no histórico
2. US2 → IA caída não perde mensagem; recepção vê
3. US3 → formato inválido auditável
4. US4 → não tramita; intenções sem ramo já vão a humano
5. US5 → log limpo
6. Polish → F1.3, isolamento, estado do projeto, quickstart

### Suggested MVP scope

**US1** (T001–T024) prova o valor visível. **US2 é aceite obrigatório** antes de marcar
F3.2 concluída (caso explícito do backlog e Artigo II). US3 é o outro modo de falha do
mesmo artigo. US4 impede que esta fatia coma F3.3–F3.5. US5 é P2 e entra nesta entrega
no padrão das fatias anteriores (Artigo VIII).

---

## Notes

- [P] = arquivos distintos, sem depender de tarefa incompleta da mesma sequência
- Sem React, sem resposta ao hóspede, sem `solicitacao`, sem catálogo neste trabalho, sem
  rota GET de histórico, sem retentativa de LLM, sem inferência de check-in
- Inverter testes da F3.1 é a feature, não regressão
- Nenhum teste chama o provedor real de IA
- Commit por tarefa ou grupo lógico **só se o usuário pedir commit**
- Evitar: `reagendar` no classificador; `marcar_falha` no escala-humano; allowlist sem
  ramo; reusar `estado_cadastro=leitura_humana`; texto ou `bruto` em log; ciclo
  `conversa` ↔ `hospedagem`
