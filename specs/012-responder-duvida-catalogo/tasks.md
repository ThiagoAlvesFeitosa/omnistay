---
description: "Task list for feature implementation"
---

# Tasks: Responder Dúvida a partir do Catálogo

**Input**: Design documents from `/specs/012-responder-duvida-catalogo/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de produção
antes de um teste que falhe pela ausência dela, e pelo motivo certo.

**Organization**: Tarefas agrupadas por história (US1–US6), na ordem da spec. Esquema
(`responder_duvida` + `duvida_nao_coberta`), portas e fidelidade entram na Foundational.
O corte que **liga** o worker (enqueue na classificação + allowlist + ramo) fica na US1 —
os três no mesmo passo, para não deixar `tipo_desconhecido` no meio do caminho. A
passagem completa da F3.2 com `duvida_geral` e catálogo vazio muda de significado:
atualizá-la quando o worker passar a consumir o tipo.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US6)

## Como ver os testes falharem nesta fatia

**Esquema.** `testes/integracao/test_conformidade_do_esquema.py` compara o banco migrado
com `docs/04-schema.sql`. Editar o documento **antes** da revisão deixa a conformidade
vermelha apontando `responder_duvida` / `duvida_nao_coberta`. A revisão `0011` a devolve
ao verde.

**Porta LLM.** Unitários que importam `ResultadoResposta` / `FalhaDeConversacao` ou
chamam `LLMFalso.responder_duvida` falham por `AttributeError` até a porta e o falso
existirem.

**Fidelidade / aviso.** Funções puras: o teste falha até o módulo existir.

**Mensageria.** `enviar_texto_sessao` não existe no Protocol; o teste falha por
`AttributeError`.

**Serviço.** `processar_trabalho_responder_duvida` não existe; o unitário falha por
`AttributeError`.

**Claim / worker.** Hoje a allowlist **não** inclui `responder_duvida` e o consumidor
não tem ramo. Os testes da US1 ficam vermelhos até allowlist e `elif` existirem juntos.
Não colocar o tipo na allowlist na Foundational — senão `--uma-passagem` marca
`tipo_desconhecido` antes do serviço existir.

**F3.2.** `test_classificacao_valida_nao_liga_sinal_nem_altera_conteudo` em
`testes/integracao/test_classificar_mensagem.py` roda uma passagem completa. Só
reescrevê-lo na US1 (catálogo com o fato → coberta, flag falso, enviada presente).
Pedido, reclamação e falha de classificar **não** se mexem até o polish.

---

## Phase 1: Setup

**Purpose**: factories da conversação, sem repetir `ResultadoResposta` em cada arquivo

- [x] T001 [P] Criar `testes/suporte/resposta_duvida.py` com helpers de
      `ItemCatalogo` (um horário de café ativo; um item de outro hotel) e, **depois**
      que a porta existir, factories de `ResultadoResposta` — nesta tarefa só o
      esqueleto: `item_cafe(*, id_hotel=1) -> ItemCatalogo` usando
      `app/portas/catalogo.py` (já existe). Sem segredo, sem rede
- [x] T002 [P] Em `testes/suporte/classificacao.py` (já existe), documentar no
      docstring que dúvida geral classificada é o gancho da F3.3
      (`responder_duvida`). Sem mudar eixos nem HMAC

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: tipo `responder_duvida` no banco, visão com `duvida_nao_coberta`, portas
de conversação e sessão, fidelidade pura, recado de aviso, gravação do JSON da
recebida, `enfileirar_responder_duvida` **ainda sem claim**. Nenhuma história consome
o trabalho ainda. Classificar **ainda não** enfileira.

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. Ordem do esquema:
T003 → T004 → T006 → T007 (teste vermelho no documento, depois migração verde).

- [x] T003 Estender `testes/integracao/test_garantias_do_banco.py`: `INSERT` em
      `trabalho` com `tipo = 'responder_duvida'` aceito; segundo `INSERT` com o mesmo
      `payload.id_mensagem` viola `uq_trabalho_responder_duvida_mensagem`. Rodar e
      **ver falhar** (FR-013, [data-model.md](./data-model.md))
- [x] T004 Aplicar o delta em `docs/04-schema.sql`: `ck_trabalho_tipo` inclui
      `responder_duvida`; índice `uq_trabalho_responder_duvida_mensagem`;
      `DROP`/`CREATE` de `vw_fila_do_dia` com `'duvida_nao_coberta'` no `IN` de
      `precisa_atendimento_humano`; atualizar o `COMMENT ON VIEW`. Rodar
      `testes/integracao/test_conformidade_do_esquema.py` e **ver falhar** pela
      divergência
- [x] T005 [P] Alinhar `docs/04-modelagem-de-dados.md`: tipo `responder_duvida`;
      desfecho `duvida_nao_coberta`; JSON com `resposta` e `id_mensagem_resposta`;
      chamado desta fatia **não** é `solicitacao`. Não dizer que dúvida geral
      classificada permanece sem resposta
- [x] T006 Criar `alembic/versions/sql/0011_responder_duvida_catalogo.sql` — cópia
      congelada do CHECK, do índice e do `CREATE VIEW` da T004
- [x] T007 Criar `alembic/versions/0011_responder_duvida_catalogo.py`
      (`down_revision = "0010_classificar_intencao"`), `upgrade` executa o SQL
      congelado, `downgrade` restaura CHECK / índice / visão da `0010`. T003 e a
      conformidade verdes
- [x] T008 [P] Unitário em `testes/unitarios/adaptadores/test_llm_falso.py` (ou
      `testes/unitarios/portas/test_llm_conversacao.py`): a porta declara
      `responder_duvida`, `ResultadoResposta` (`coberta`, `texto`,
      `trechos_citados`) e `FalhaDeConversacao(codigo)` distinta de
      `FalhaDeClassificacao` e `FalhaDeExtracao`. **Ver falhar**
      ([contracts/llm-e-conversacao.md](./contracts/llm-e-conversacao.md))
- [x] T009 Implementar em `app/portas/llm.py`: `FalhaDeConversacao`,
      `ResultadoResposta`, `LLMProvider.responder_duvida`. Não alterar
      `extrair_ficha` nem `classificar`. T008 verde o bastante para importar os tipos
- [x] T010 [P] Em `testes/unitarios/adaptadores/test_llm_falso.py`:
      `responder_duvida` configurável (`configurar_resposta` /
      `falhar_conversacao`); default com itens vazios devolve `coberta=False`; com
      itens devolve `coberta=True` e trechos do primeiro item; `extrair_ficha` e
      `classificar` permanecem idênticos. **Ver falhar** (research §7)
- [x] T011 Implementar `responder_duvida` em `app/adaptadores/llm_falso.py` com
      configuração **separada**. T010 verde; testes antigos de extração e
      classificação intactos. Completar factories em
      `testes/suporte/resposta_duvida.py` com `ResultadoResposta`
- [x] T012 [P] Unitário em `testes/unitarios/modulos/conversa/test_fidelidade.py`:
      `resposta_fiel_ao_catalogo` aceita trechos que são substring do catálogo **e**
      do texto; rejeita trechos vazios, trecho órfão e trecho ausente do texto.
      **Ver falhar** (FR-008)
- [x] T013 Implementar `resposta_fiel_ao_catalogo` em
      `app/modulos/conversa/fidelidade.py` (módulo puro, sem SQL, sem HTTP). T012
      verde
- [x] T014 [P] Unitário em `testes/unitarios/modulos/conversa/test_texto_aviso_duvida.py`:
      `montar_aviso_duvida_nao_coberta` menciona que a recepção vai atender, usa só
      o prenome, **não** cita horário/cardápio/regra. **Ver falhar** (FR-005)
- [x] T015 Implementar `montar_aviso_duvida_nao_coberta` em
      `app/modulos/conversa/texto_aviso_duvida.py` (função pura, padrão do lembrete).
      T014 verde
- [x] T016 [P] Unitário em `testes/unitarios/adaptadores/test_mensageria_falsa.py`
      (criar se não existir): `enviar_texto_sessao` registra `tipo=sessao` e `corpo`;
      `FalhaDeEnvio` no modo falha. **Ver falhar**
      ([contracts/mensageria-sessao.md](./contracts/mensageria-sessao.md))
- [x] T017 Implementar `enviar_texto_sessao` em `app/portas/mensageria.py`,
      `app/adaptadores/mensageria_falsa.py` e o método correspondente em
      `app/adaptadores/mensageria_whatsapp.py` (`type: text`; suíte **não** instancia
      o adaptador real). T016 verde
- [x] T018 Unitário/integração em
      `testes/unitarios/modulos/conversa/test_responder_duvida.py`:
      `gravar_resposta_duvida` (nome ilustrativo) atualiza JSON da recebida com
      `resposta` + `id_mensagem_resposta` (+ `desfecho` quando aviso) e **não**
      altera `conteudo` nem eixos; `id_hotel` tem de conferir. **Ver falhar**
      (FR-011, FR-015)
- [x] T019 Implementar a gravação em `app/modulos/conversa/repository.py` (`UPDATE`
      de `classificacao_bruta` com `WHERE` na mensagem **e** `id_hotel` via
      `reserva`; reusar `inserir_mensagem_enviada_pendente` para a enviada). T018
      verde
- [x] T020 [P] Unitário em `testes/unitarios/fila/test_enfileirar_responder_duvida.py`:
      `enfileirar_responder_duvida` insere tipo e payload só com IDs. **Ver falhar**
      ([contracts/fila-e-worker.md](./contracts/fila-e-worker.md)). Depende de T007
- [x] T021 Implementar `enfileirar_responder_duvida` em `app/fila/repository.py` e
      `app/fila/service.py`. **Não** incluir o tipo em `TIPOS_CONSUMIVEIS`. T020
      verde

**Checkpoint**: esquema aceita o tipo; portas e falso conversam; fidelidade e aviso
existem; dá para gravar JSON e enfileirar. Worker **não** consome o tipo. Classificar
**não** enfileira ainda.

---

## Phase 3: User Story 1 - Dúvida coberta recebe resposta automática (Priority: P1) 🎯 MVP

**Goal**: `duvida_geral` classificada + catálogo com o fato → resposta automática
fiel, gravada antes do envio, trabalho `concluido`, flag humano **falso**, zero
`solicitacao`.

**Independent Test**: mensagem já `classificado`/`duvida_geral` + `CatalogoFalso` com
horário de café + `LLMFalso` coberto fiel → enviada com o fato, `resposta=automatica`,
`precisa_atendimento_humano=false`, `count(solicitacao)=0`.

### Tests for User Story 1 ⚠️

- [x] T022 [P] [US1] Em `testes/unitarios/modulos/conversa/test_responder_duvida.py`:
      repositório falso + catálogo com o fato + `LLMFalso` coberto fiel →
      `processar_trabalho_responder_duvida` insere enviada com o texto, JSON
      `resposta=automatica`, chama `enviar_texto_sessao` **depois** de gravar, marca
      trabalho `concluido`, não liga desfecho humano. **Ver falhar** (FR-001, FR-002,
      FR-011, FR-012)
- [x] T023 [US1] Atualizar
      `test_classificacao_valida_nao_liga_sinal_nem_altera_conteudo` em
      `testes/integracao/test_classificar_mensagem.py`: semear item de café no
      catálogo do hotel da reserva; após `processar_uma_passagem`, recebida intocada,
      `intencao=duvida_geral`, existe enviada automática, `precisa_atendimento_humano
      = false`, zero `solicitacao`. **Ver falhar** até o worker consumir o tipo
      (research §1)
- [x] T024 [P] [US1] Unitário em `testes/unitarios/fila/test_claim_responder_duvida.py`:
      `reclamar_proximo` **devolve** `responder_duvida` quando é o único pendente.
      **Ver falhar** (hoje a allowlist exclui)
- [x] T025 [P] [US1] Unitário em `testes/unitarios/modulos/conversa/test_classificar_mensagem.py`:
      `processar_trabalho_classificar_mensagem` com `duvida_geral` **enfileira**
      `responder_duvida` e **não** chama catálogo nem gateway. Pedido/reclamação
      continuam sem esse enqueue. Caminho “já classificada” sem trabalho de resposta
      também enfileira. **Ver falhar** (research §1 e §2)

### Implementation for User Story 1

- [x] T026 [US1] Implementar `processar_trabalho_responder_duvida` em
      `app/modulos/conversa/service.py`: `listar_ativos(id_hotel)` pela porta;
      `llm.responder_duvida`; `resposta_fiel_ao_catalogo`; gravar enviada; atualizar
      JSON; `gateway.enviar_texto_sessao`; `marcar_concluido`. Sem importar
      `hospedagem`. Sem `solicitacao`. T022 verde no caminho feliz
- [x] T027 [US1] Em `app/modulos/conversa/service.py`, ao gravar `duvida_geral` +
      `classificado` (e no caminho já classificada), chamar
      `enfileirar_responder_duvida`. Em `app/fila/repository.py`, incluir o tipo na
      allowlist. Em `worker/consumidor.py`, ramo com `llm`, `CatalogoBanco(conexao)`
      (ou catálogo injetado) e `gateway` — **enqueue, allowlist e ramo no mesmo
      passo**. T023, T024 e T025 verdes. Nunca allowlist sem ramo (research §1)
- [x] T028 [US1] Idempotência: se JSON já tem `resposta` ∈ (`automatica`, `aviso`) e
      `id_mensagem_resposta`, não chamar o LLM de novo; se a enviada ainda está
      `pendente`, só tenta o envio; senão conclui. Teste no mesmo
      `test_responder_duvida.py` (contador de `chamadas_responder`). FR-013, SC-010

**Checkpoint**: `--uma-passagem` classifica dúvida geral coberta e envia a resposta
automática. Flag humano permanece falso. Catálogo vazio ainda não tem teste próprio
(US2 / US5).

---

## Phase 4: User Story 2 - Dúvida fora do catálogo avisa e abre chamado (Priority: P1)

**Goal**: `coberta=False` (catálogo com itens que não cobrem a pergunta) → recado
padrão gravado **antes** do desfecho `duvida_nao_coberta`, sinal na fila, zero fato
inventado, zero `solicitacao`.

**Independent Test**: dúvida classificada + catálogo ativo sem o fato + falso
`coberta=False` → enviada de aviso, `precisa_atendimento_humano=true`, trabalho
`concluido`.

### Tests for User Story 2 ⚠️

- [x] T029 [P] [US2] Unitário em `test_responder_duvida.py`: `coberta=False` →
      enviada é o aviso (não o `texto` do modelo), JSON `desfecho=duvida_nao_coberta`
      e `resposta=aviso` **depois** de inserir a enviada, `enviar_texto_sessao` com o
      aviso, `marcar_concluido`, zero `reagendar` de LLM. **Ver falhar** (FR-004,
      FR-005, FR-006)
- [x] T030 [US2] Integração em `testes/integracao/test_responder_duvida.py` (criar):
      após o worker, `GET /fila-do-dia` (recepção) tem
      `precisa_atendimento_humano=true`; o corpo da enviada não afirma horário /
      cardápio ausente; `count(solicitacao)=0`. **Ver falhar** (SC-002, SC-006)

### Implementation for User Story 2

- [x] T031 [US2] No `processar_trabalho_responder_duvida` de
      `app/modulos/conversa/service.py`: ramo não coberto usa
      `montar_aviso_duvida_nao_coberta`, grava enviada, **depois** atualiza
      `desfecho=duvida_nao_coberta`, envia, conclui. T029 e T030 verdes. Não copiar
      backoff de LLM

**Checkpoint**: pergunta não coberta não inventa fato; a recepção vê a pendência.

---

## Phase 5: User Story 3 - Redação não cita fato ausente (Priority: P1)

**Goal**: `coberta=True` com trecho órfão (ou trechos vazios) **não** envia esse
texto; desfecho idêntico ao da US2 (aviso + chamado).

**Independent Test**: catálogo fechado (só café) + falso com trecho “piscina” → aviso,
não o texto inventado, flag verdadeiro.

### Tests for User Story 3 ⚠️

- [x] T032 [P] [US3] Unitário em `test_responder_duvida.py`: `coberta=True` + trecho
      fora do catálogo **e** `coberta=True` + trechos vazios → o `texto` do modelo
      **não** é enviado; segue aviso + `duvida_nao_coberta`. **Ver falhar** (FR-008,
      SC-003)
- [x] T033 [US3] Integração em `testes/integracao/test_responder_duvida.py`: após o
      worker, `mensagem.conteudo` da enviada é o aviso, não contém o fato inventado;
      flag `true`. **Ver falhar**

### Implementation for User Story 3

- [x] T034 [US3] Em `app/modulos/conversa/service.py`, se `coberta` e
      `resposta_fiel_ao_catalogo` rejeitar: mesmo ramo da US2 (`resposta_nao_fiel` no
      log na US6). T032 e T033 verdes. Não enviar “a parte boa”

**Checkpoint**: mentira estruturada do modelo não chega ao hóspede.

---

## Phase 6: User Story 4 - Catálogo de outro hotel nunca é usado (Priority: P1)

**Goal**: `listar_ativos` só com `id_hotel` do trabalho; fato de A não responde B.

**Independent Test**: mesmo texto de pergunta; A tem o fato, B não → A recebe
automática com o fato de A; B recebe aviso; fila de A não muda por causa de B.

### Tests for User Story 4 ⚠️

- [x] T035 [P] [US4] Unitário em `test_responder_duvida.py`: `CatalogoFalso` com
      itens só no hotel A; trabalho do hotel B → `listar_ativos(B)` vazio (ou sem o
      fato); desfecho de não coberta; o texto enviado **não** contém o conteúdo de
      A. **Ver falhar** (FR-002, FR-015, SC-004)
- [x] T036 [US4] Integração em `testes/integracao/test_responder_duvida.py` (ou
      `test_fila_do_dia.py`): duas propriedades; item ativo só em A; pergunta em B →
      flag em B verdadeiro, flag/enviada de A inalterados. **Ver falhar**

### Implementation for User Story 4

- [x] T037 [US4] Garantir em `processar_trabalho_responder_duvida` (
      `app/modulos/conversa/service.py`) que o único argumento de `listar_ativos` é
      `trabalho["id_hotel"]` e que o LLM só recebe essa tupla. T035 e T036 verdes —
      se T026 já filtrava, esta tarefa é o teste de isolamento e o ajuste se o
      serviço tiver lido catálogo global

**Checkpoint**: o hóspede de B não ouve o hotel A.

---

## Phase 7: User Story 5 - Falha ao redigir ou catálogo vazio escala (Priority: P1)

**Goal**: catálogo ativo vazio **não** chama o LLM; `FalhaDeConversacao` na primeira
ocorrência vira aviso + chamado; trabalho `concluido` (não `falha` / não limbo).

**Independent Test**: (a) `CatalogoFalso` vazio → zero chamada a
`responder_duvida`, aviso, flag true; (b) `falhar_conversacao` com itens → mesmo
desfecho visível, trabalho `concluido`.

### Tests for User Story 5 ⚠️

- [x] T038 [P] [US5] Unitário em `test_responder_duvida.py`: itens vazios →
      `LLMFalso.chamadas_responder` (ou equivalente) permanece vazio; aviso +
      `duvida_nao_coberta`; `marcar_concluido`. **Ver falhar** (FR-009, FR-010)
- [x] T039 [US5] Unitário: `falhar_conversacao` com itens presentes → aviso +
      desfecho humano, **zero** `reagendar` / `marcar_falha` de LLM, trabalho
      `concluido`. Integração: flag `true` após o worker; sinal permanece num
      segundo `GET /fila-do-dia`. **Ver falhar** (SC-005, SC-008)

### Implementation for User Story 5

- [x] T040 [US5] Em `app/modulos/conversa/service.py`: se `listar_ativos` vazio,
      pular a porta LLM e seguir o ramo de aviso; capturar `FalhaDeConversacao` do
      mesmo modo (sem backoff da ficha). T038 e T039 verdes

**Checkpoint**: propriedade recém-instalada e IA caída não inventam fato nem perdem a
pergunta.

---

## Phase 8: User Story 6 - Conteúdo não vaza em log (Priority: P2)

**Goal**: coberta, não coberta, não fiel e indisponível logam identificadores, hotel e
`resultado` — nunca pergunta, resposta, trechos nem conteúdo de item.

**Independent Test**: caplog nos quatro desfechos; fixture de conteúdo ausente do log.

### Tests for User Story 6 ⚠️

- [x] T041 [P] [US6] Estender `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py`:
      `processar_trabalho_responder_duvida` nos desfechos automática, aviso, não fiel
      e indisponível — o texto da pergunta, o da resposta e o `conteudo` do item não
      aparecem; há `id_mensagem` / `id_trabalho` / `id_hotel` / `resultado`.
      **Ver falhar** (FR-014, SC-007)

### Implementation for User Story 6

- [x] T042 [US6] Ajustar logs em `app/modulos/conversa/service.py` (eventos
      `duvida_respondida`, `duvida_nao_coberta`, `resposta_nao_fiel`,
      `conversacao_indisponivel`, `duvida_ja_respondida` conforme
      [contracts/fila-e-worker.md](./contracts/fila-e-worker.md)). T041 verde

**Checkpoint**: trilha técnica sem cópia da conversa nem do catálogo recitado.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: intenções que não são dúvida, item desativado, regressão F3.2/F1.3,
fronteiras, documentação, suíte

- [x] T043 [P] Unitário em `test_classificar_mensagem.py`: `pedido_de_servico`,
      `reclamacao_tecnica`, `upsell` e falha de classificação **não** inserem
      `responder_duvida`. Integração: F3.2 de indisponível / inválido / upsell
      continua ligando o sinal **sem** enviada de catálogo (FR-012)
- [x] T044 [P] Integração: item **desativado** não cobre a pergunta (desfecho de
      aviso); item reativado cobre. Usar rotas de catálogo da F2.1 ou SQL no teste
      (`testes/integracao/test_responder_duvida.py`)
- [x] T045 [P] `testes/integracao/test_rotas_protegidas.py`: `GET /fila-do-dia`
      segue só recepção; nenhuma operação nova na matriz
      ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))
- [x] T046 [P] Regressão: `testes/integracao/test_webhook_coleta.py`,
      `test_interpretar_ficha.py`, `test_classificar_mensagem.py` (ramos que não são
      dúvida coberta) e o claim de outros tipos continuam verdes;
      `interpretar_ficha` **não** chama `responder_duvida`
- [x] T047 Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F3.3 em andamento/concluída,
      revisão `0011`, worker consome `responder_duvida`, chamada de recepção via
      `duvida_nao_coberta`, próxima fatia **F3.4**. Não apontar F2.3
- [x] T048 Revisar fronteiras: `conversa` não escreve `reserva.status` nem
      `solicitacao`; SQL de `trabalho` só em `app/fila/`; catálogo só pela porta;
      `hospedagem` só projeta a visão; nenhum teste instancia adaptador real de IA
      nem WhatsApp; falha de envio **depois** de gravar reagenda mensageria, não o
      LLM. Rodar [quickstart.md](./quickstart.md), `pytest testes/unitarios -q` e a
      integração desta fatia (`test_responder_duvida.py`,
      `test_classificar_mensagem.py`, `test_fila_do_dia.py`,
      `test_conformidade_do_esquema.py`, `test_garantias_do_banco.py`). Tudo verde,
      sem rede

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: após Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: após Foundational — MVP (consumo + resposta coberta)
- **US2 (Phase 4)**: após US1 (mesmo serviço; ramo não coberto)
- **US3 (Phase 5)**: após US1 (fidelidade já existe; o serviço ainda não recusava)
- **US4 (Phase 6)**: após US1; isolamento do `id_hotel` já usado na US2/US5
- **US5 (Phase 7)**: após US2 (reusa o ramo de aviso)
- **US6 (Phase 8)**: após os desfechos existirem (US1–US3/US5)
- **Polish (Phase 9)**: após as histórias desejadas

### User Story Dependencies

- **US1**: após Phase 2 — sem dependência de outra história; **é o corte do worker**
- **US2**: após US1 (estende `processar_trabalho_responder_duvida`)
- **US3**: após US1 (e T013); independente da US2 no arquivo de teste, mesmo
  `service.py`
- **US4**: após US1; teste de isolamento, não novo desfecho
- **US5**: após US2 (mesmo aviso); T038 pode ser escrito em paralelo ao teste da US2
- **US6**: após os desfechos existirem

### Within Each User Story

1. Testes escritos e **vermelhos pelo motivo certo**
2. Implementação mínima
3. Verde
4. Só então a próxima história

### Parallel Opportunities

- T001 e T002 em paralelo
- T005 em paralelo com T003/T004
- T008 em paralelo com o esquema; T009 depois de T008
- T010/T011 depois de T009
- T012/T013, T014/T015 e T016/T017 em paralelo entre si (arquivos distintos)
- T018/T019 depois de T007 (INSERT real)
- T020/T021 depois de T007
- T022, T024 e T025 em paralelo na US1; T023 no mesmo arquivo de integração da F3.2
  (série se conflitar com outro teste nesse arquivo)
- T027 é atômico (enqueue + allowlist + ramo)
- T029 em paralelo com T030 na US2 depois da US1
- T032 em paralelo com T033 na US3
- T035 em paralelo com T036 na US4
- T038 em paralelo com T039 na US5
- T043, T044, T045 e T046 em paralelo no polish

**Sequência obrigatória em Foundational**: T003 → T004 → T006 → T007. Ver a
conformidade vermelha entre T004 e T007 é a prova de que ela vigia o documento.

**Sequência obrigatória na US1**: T026 (serviço) pode anteceder T027, mas **T027 é
atômico**. Não mergear allowlist sozinha. Não enfileirar na classificação antes do
ramo existir.

---

## Parallel Example: User Story 1

```text
# Testes em paralelo (antes da implementação):
T022 test_responder_duvida.py              (serviço / caminho coberto)
T024 test_claim_responder_duvida.py        (allowlist)
T025 test_classificar_mensagem.py          (enqueue na classificação)
T023 test_classificar_mensagem.py          (integração F3.2 atualizada) — série com T025 se o arquivo for o mesmo

# Depois:
T026 processar_trabalho_responder_duvida   (caminho automático)
T027 enqueue + allowlist + elif            (juntos)
T028 idempotência
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: worker responde dúvida coberta; flag falso; zero `solicitacao`
4. Demo: catálogo com café + webhook “que horas e o cafe” + `--uma-passagem`;
   `SELECT` da enviada; fila com flag falso

### Incremental Delivery

1. US1 → resposta automática quando o fato está no catálogo
2. US2 → não coberta avisa e a recepção vê
3. US3 → redação infiel não passa
4. US4 → hotel A não fala por B
5. US5 → vazio e IA caída escalam
6. US6 → log limpo
7. Polish → intenções outras, item desativado, estado do projeto, quickstart

### Suggested MVP scope

**US1** (T001–T028) prova o valor visível. **US2 é aceite obrigatório** antes de
marcar F3.3 concluída (caso explícito do backlog e Artigo II). US3 é o critério “não
cita informação ausente”. US4 é Artigo XIV nesta fatia. US5 cobre o estado inicial
da propriedade. US6 é P2 e entra nesta entrega no padrão das fatias anteriores
(Artigo VIII).

---

## Notes

- [P] = arquivos distintos, sem depender de tarefa incompleta da mesma sequência
- Sem React, sem `solicitacao`, sem Alert Center operacional, sem rota GET de
  histórico, sem retentativa de LLM, sem inferência de check-in, sem busca no
  catálogo
- Atualizar o teste da F3.2 de passagem completa com `duvida_geral` é a feature, não
  regressão
- Nenhum teste chama o provedor real de IA nem o adaptador WhatsApp
- Commit por tarefa ou grupo lógico **só se o usuário pedir commit**
- Evitar: `reagendar` na conversação; `marcar_falha` no escala-humano; allowlist sem
  ramo; enqueue na classificação antes do ramo; abrir `solicitacao`; texto, trechos
  ou item em log; ciclo `conversa` ↔ `hospedagem`; ler catálogo sem a porta
