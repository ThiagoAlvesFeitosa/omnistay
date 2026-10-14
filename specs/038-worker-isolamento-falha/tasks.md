---
description: "Lista de tarefas para implementação da fatia"
---

# Tarefas: F9.1 O worker não para por causa de um trabalho

**Input**: documentos em `specs/038-worker-isolamento-falha/`
**Pré-requisitos**: [plan.md](./plan.md), [spec.md](./spec.md),
[research.md](./research.md), [data-model.md](./data-model.md),
[contracts/](./contracts/), [quickstart.md](./quickstart.md)

**TDD (obrigatório)**: nenhuma linha de produção antes de um teste que
falhe pela ausência dela. Em cada tarefa de teste: escrever, rodar,
**ver falhar pelo motivo certo**. Só então a implementação. Um teste
que passa de primeira é suspeito.

**pytest**: `uv run pytest testes/unitarios -q` no ciclo;
`uv run pytest -k nome` para um só.
**Vitest**: `npm --prefix frontend test -- --run`. Sem Playwright.
Portas falsas; sem Gemini nem WhatsApp.

**Duas guardas (não negociar):**

1. **Reuso, não peça nova.** Teto =
   `tentativas_max_envio_mensagem` (ausente/ilegível → 5). Espera =
   `backoff_apos`. Falha inesperada → `registrar_falha_de_envio` com
   `type(exc).__name__`. Sem chave nova de espera, sem Redis, sem
   operação `ciente`, sem rota nova, sem tipo novo em `trabalho`.
2. **Nome da exceção, nunca a mensagem.** `erro_ultima_tentativa` e
   log sem CPF, SQL, parâmetros nem conteúdo. `hide_parameters=True`
   em `obter_engine()`. Worker deixa o `create_engine` solto.

**Organização**: US1 passagem; US2 registro/LGPD; US3 ciclo; US4
distintivos na Fila do dia. Setup e Foundational sem rótulo de
história.

## Format: `[ID] [P?] [USx?] Descrição`

- **[P]**: paralelizable (arquivos diferentes, sem dependência incompleta)
- **[USn]**: história correspondente
- Caminho de arquivo em cada tarefa

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: constantes e montagem de cenário só de teste. O monólito
já existe; não criar pacote de produção.

- [X] T001 [P] Criar `testes/suporte/isolamento_falha.py` com
  `CPF_NA_MENSAGEM` (`529.982.247-25` ou equivalente só de teste),
  `excecao_com_cpf()` que devolve `IntegrityError` (ou `RuntimeError`)
  cuja `str` contém esse CPF, e `trabalho_minimo(tipo, *, id_hotel,
  id_reserva=None, tentativas=0, status="pendente")` para INSERT em
  `trabalho` (payload só identificadores). Docstring: uso só em teste.
  Sem importar produção além de tipos SQLAlchemy se precisar.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: teto ilegível não derruba; engine da API esconde
parâmetros. **Nenhuma história começa antes desta fase.**

**Checkpoint**: `tentativas_maximas` devolve 5 se o parâmetro falta
ou não é inteiro; `obter_engine()` tem `hide_parameters=True`.

- [X] T002 [P] Estender
  `testes/unitarios/fila/test_service_da_fila.py`: `tentativas_maximas`
  com parâmetro `None` devolve 5; com `"abc"` devolve 5 (MUST NOT
  levantar); com `"7"` devolve 7; hotel distinto não lê o teto do
  outro (repositório falso). Rodar e **ver falhar** (FR-008).

- [X] T003 Em `app/fila/service.py`, `tentativas_maximas` trata
  ausente e `int(...)` ilegível como `TENTATIVAS_MAX_PADRAO`. Sem
  chave nova. Rodar T002 até ficar **verde**.

- [X] T004 [P] Escrever
  `testes/unitarios/test_engine_esconde_parametros.py` (ou estender o
  unitário que já instancia `obter_engine` se houver): a engine
  criada por `app.database.obter_engine` tem `hide_parameters` verdadeiro.
  Limpar o cache `lru` no teste. Rodar e **ver falhar**.

- [X] T005 Em `app/database.py`, passar `hide_parameters=True` no
  `create_engine`. Rodar T004 até ficar **verde**. Não mudar o worker
  ainda (US2).

**Checkpoint**: teto e parâmetros da API prontos; o consumidor ainda
propaga exceção.

---

## Phase 3: User Story 1 - Um trabalho com erro não derruba o resto da fila (Priority: P1) 🎯 MVP

**Goal**: savepoint por trabalho; exceção reagenda (ou `falha` no
teto) pelo `registrar_falha_de_envio`; o seguinte da passagem corre;
concluído não desfaz; unicidade da ficha não encerra o processo.

**Independent Test**: enfileirar um trabalho que estoura e outro
saudável; `processar_uma_passagem` devolve os dois claims; o primeiro
está reagendado com espera maior; o segundo concluído; repetir até o
teto → `falha` e `reclamar_proximo` ignora.

### Tests (escrever e ver falhar)

- [X] T006 [P] [US1] Escrever
  `testes/unitarios/worker/test_isolamento_da_passagem.py` (banco de
  teste / conexão da suíte, portas falsas): (1) primeiro handler
  levanta `RuntimeError`, segundo tipo distinto conclui — o primeiro
  fica `pendente` com `tentativas+1` e `proxima_tentativa_em` no
  futuro, o segundo `concluido`, a função **não** propaga, o worker
  não chama `sys.exit`; (2) trabalho já no teto-1 que estoura fica
  `status=falha` e uma segunda passagem **não** o reclama; (3)
  trabalho marcado `concluido` antes do que estoura permanece
  `concluido`. Nomes em português. Uma asserção conceitual por teste.
  Rodar e **ver falhar** (FR-001 a FR-005).

- [X] T007 [P] [US1] Escrever
  `testes/integracao/test_isolamento_unicidade_ficha.py`: cenário no
  espírito 18/09 — `interpretar_ficha` dispara unicidade ao
  consolidar (ou monkeypatch de `consolidar_ficha_titular` que
  levanta `IntegrityError`); `processar_uma_passagem` / passagem na
  engine **não** levanta para o teste; trabalho reagendado ou em
  `falha` conforme teto; um segundo trabalho na fila é processado.
  Rodar e **ver falhar** (FR-006).

### Implementation

- [X] T008 [US1] Em `worker/consumidor.py`, cada claim+despacho em
  `conexao.begin_nested()`; `except Exception` faz rollback do
  savepoint e `fila_service.registrar_falha_de_envio` com
  `codigo_erro=type(exc).__name__`, `id_hotel` e `tentativas` do
  snapshot. Não relançar. Tipo desconhecido permanece o caminho
  `tipo_desconhecido` (também dentro do savepoint). Rodar T006 e T007
  até ficar **verde**.

**Checkpoint**: passagem isolada. Log/CPF ainda não são a US2.
`executar_ciclo` ainda não existe.

---

## Phase 4: User Story 2 - O registro da falha não vaza dado pessoal (Priority: P1)

**Goal**: campo do trabalho e log só com o nome da classe; engine do
worker igual à da API (`obter_engine`, parâmetros ocultos).

**Independent Test**: forçar `excecao_com_cpf()`; `erro_ultima_tentativa`
== `IntegrityError` (ou o nome usado); log capturado sem o CPF e sem
SQL interpolado.

### Tests (escrever e ver falhar)

- [X] T009 [P] [US2] Estender
  `testes/unitarios/worker/test_isolamento_da_passagem.py`: handler
  levanta `excecao_com_cpf()`; `erro_ultima_tentativa` é só o nome da
  classe; o CPF **não** está no campo nem nos records de log da
  passagem (`caplog`). Rodar e **ver falhar** se o consumidor logar
  `str(exc)` ou `logger.exception(exc)` (FR-007).

- [X] T010 [P] [US2] Estender `testes/unitarios/worker/test_cli_worker.py`:
  `--uma-passagem` **não** chama `create_engine` direto; usa
  `app.database.obter_engine` (monkeypatch nesse alvo). O teste atual
  que patcha `worker_main.create_engine` deve passar a falhar pelo
  motivo certo. Rodar e **ver falhar**.

### Implementation

- [X] T011 [US2] No `except` de `worker/consumidor.py`, log só com
  `id_trabalho`, `tipo` e `type(exc).__name__` — MUST NOT passar a
  exceção crua ao logger. Rodar T009 até ficar **verde**.

- [X] T012 [US2] Em `worker/__main__.py`, trocar `create_engine` por
  `obter_engine()`; remover o import de `create_engine` se sobrar.
  Ajustar `testes/unitarios/worker/test_cli_worker.py` para patchar
  `obter_engine`. Rodar T010 até ficar **verde**. Timeout por
  consulta = o da API (FR-011).

**Checkpoint**: 18/09 não vaza CPF no registro. Ciclo horário ainda
é um bloco único.

---

## Phase 5: User Story 3 - Mensagens e rotinas agendadas não se derrubam (Priority: P1)

**Goal**: `executar_ciclo` isola passagem, cadastros, boas-vindas,
pulso, mercado e retenção. Uma etapa que estoura não pula as outras.
Flags pontuais intactas.

**Independent Test**: injetar falha na passagem e ver as cinco
rotinas chamadas; injetar falha só no mercado e ver retenção e as
outras; `--uma-passagem` continua sem agendador.

### Tests (escrever e ver falhar)

- [X] T013 [US3] Escrever
  `testes/unitarios/worker/test_isolamento_do_ciclo.py`:
  `executar_ciclo` com funções injetáveis (ou monkeypatch das
  `_rodar_*` e da passagem); (1) passagem levanta — as cinco
  verificações ainda são chamadas; (2) só mercado levanta — cadastros,
  boas-vindas, pulso, retenção e passagem ocorrem; (3) retenção
  levanta — passagem e as outras verificações não são puladas; (4)
  log da etapa falha contém o nome da exceção e **não** o CPF de
  `excecao_com_cpf()`. Sem `sleep`. Rodar e **ver falhar** (FR-009,
  FR-010).

### Implementation

- [X] T014 [US3] Extrair `executar_ciclo` em `worker/__main__.py`
  (try/except por etapa; log com nome da etapa + nome da classe).
  O `while True` chama `executar_ciclo` no lugar do bloco atual.
  Flags `--uma-passagem` e `--verificar-*` **não** passam pelo ciclo
  completo. Estender
  `test_uma_passagem_nao_chama_agendador` se o nome interno mudar.
  Rodar T013 e o CLI existente até ficar **verde**.

**Checkpoint**: expurgo não depende da passagem ter sucesso. Fila do
dia ainda sem rótulo de omissão.

---

## Phase 6: User Story 4 - A recepção vê o que deixou de acontecer (Priority: P1)

**Goal**: `GET /fila-do-dia` traz `omissoes[]` (chave, texto,
contagem) derivadas de `trabalho.status='falha'` com `id_reserva`;
tela pinta rótulos sky, agrupados pelo catálogo; mercado e
`encerrado` sem distintivo; sem “ciente”.

**Independent Test**: reserva na fila + trabalho `falha` ligado →
rótulo próprio; dois tipos → dois textos; dois do mesmo tipo →
contagem; coleta de mercado em falha não muda linha; após
`encerrado`, `omissoes: []`.

### Tests (escrever e ver falhar)

- [X] T015 [P] [US4] Atualizar `docs/04-schema.sql`: `vw_fila_do_dia`
  inclui JSON `omissoes_brutas` (ou nome estável) — agregação de
  `trabalho` `falha` do mesmo `id_hotel` com
  `(payload->>'id_reserva')::bigint = r.id_reserva`; reserva
  `encerrado` → JSON vazio/`[]`; `coletar_mercado` sem
  `id_reserva` não entra. Comentário da visão. **Não** alterar
  `0001`. Rodar
  `uv run pytest testes/integracao/test_conformidade_do_esquema.py -q`
  e **ver falhar**.

- [X] T016 [P] [US4] Escrever
  `testes/unitarios/modulos/hospedagem/test_omissoes_da_fila.py`:
  catálogo do [research.md](./research.md) §6 — um
  `interpretar_ficha` → texto **Ficha não processada** contagem 1;
  dois `classificar_mensagem` → **2 mensagens do hóspede sem
  resposta**; `classificar_mensagem` + `responder_duvida` colapsam
  na mesma chave; tipo futuro sem chave **não** inventa frase;
  `coletar_mercado` não produz omissão. Rodar e **ver falhar**
  (FR-014, FR-015, FR-017).

- [X] T017 [P] [US4] Estender
  `testes/unitarios/modulos/hospedagem/test_service_da_fila.py` (e/ou
  integração `testes/integracao/test_fila_do_dia.py`): item com
  trabalho `falha` de `interpretar_ficha` traz `omissoes` com a
  frase da ficha; booleanos da 029 intactos; hotel da sessão;
  reserva `encerrado` (se ainda listada) com lista vazia. Rodar e
  **ver falhar** (FR-013, FR-016).

- [X] T018 [P] [US4] Estender `frontend/src/painel/fila.ts` tipos e
  `frontend/src/painel/TelaFila.test.tsx`: `omissoes` no `item()`
  (default `[]`); linha mostra o `texto`; classe sky distinta de
  vermelho/laranja/âmbar/violeta; dois rótulos visíveis; um rótulo
  com contagem; **sem** botão de ciente; quatro sinais antigos
  regressão. Rodar
  `npm --prefix frontend test -- --run src/painel/TelaFila.test.tsx`
  e **ver falhar**.

### Implementation

- [X] T019 [US4] Criar `alembic/versions/sql/0026_omissoes_fila_do_dia.sql`
  (cópia congelada do delta da visão em T015) e
  `alembic/versions/0026_omissoes_fila_do_dia.py`
  (`down_revision = "0025_resposta_recepcao"`), padrão DROP VIEW /
  CREATE das revisões 0023–0025. Conformidade **verde**.

- [X] T020 [US4] Implementar montagem do catálogo (função em
  `app/modulos/hospedagem/service.py` ou módulo mínimo no mesmo
  pacote — sem lib nova). T016 **verde**.

- [X] T021 [US4] Ler o JSON da visão em
  `app/modulos/hospedagem/repository.py`; mapear `omissoes` em
  `ItemFilaDoDia` em `app/modulos/hospedagem/schema.py` e
  `listar_fila_do_dia` em `app/modulos/hospedagem/service.py`. Sem
  rota nova. Sem operação na matriz. T017 **verde**.

- [X] T022 [US4] Tipo `omissoes` em `frontend/src/painel/fila.ts`;
  spans sky em `frontend/src/painel/TelaFila.tsx` na célula de
  situação, depois dos quatro sinais. Atualizar mocks de
  `Casca.test.tsx` / outros `item()` da fila com `omissoes: []` se
  o tipo exigir. T018 **verde**. Sem destino novo.

**Checkpoint**: recepção vê o que deixou de acontecer. F9.2–F9.5
intocadas.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: estado do projeto, regressão da suíte, quickstart.

- [X] T023 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: achado alto
  do worker/expurgo e o médio de `hide_parameters` desta fatia como
  endereçados pela F9.1 (sem apagar o histórico de 18/09). Se
  `docs/05-arquitetura.md` ainda disser que uma exceção encerra o
  consumidor, alinhar ao savepoint + ciclo isolado. Sem PMS.

- [X] T024 [P] Confirmar `testes/unitarios/modulos/acesso/test_politica.py`
  sem operação nova; nenhuma rota em `ROTAS_PUBLICAS`. Se algum teste
  de schema Pydantic da fila quebrar por campo extra, ajustar default
  `omissoes: []` só onde o contrato mandar.

- [X] T025 Rodar a validação de [quickstart.md](./quickstart.md):
  `uv run pytest testes/unitarios/worker testes/unitarios/fila
  testes/unitarios/modulos/hospedagem -q`; integração da unicidade e
  da fila do dia; `npm --prefix frontend test -- --run
  src/painel/TelaFila.test.tsx`. Tudo verde. Sem rede externa.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: depois do Setup — **bloqueia** as histórias
- **US1 (Phase 3)**: depois da Foundational — MVP
- **US2 (Phase 4)**: depois da US1 (o `except` da passagem precisa
  existir para afirmar log/campo)
- **US3 (Phase 5)**: depois da US1 (ciclo envolve a passagem já isolada);
  US2 pode seguir em paralelo com US3 se o log da passagem já estiver
  estável
- **US4 (Phase 6)**: independente da US3 no código da tela; depende
  de trabalhos em `falha` (US1) para o cenário ponta a ponta
- **Polish**: depois das histórias desejadas

### User Story Dependencies

- **US1 (P1)**: Foundational; sem dependência de US2–US4
- **US2 (P1)**: acoplada ao `except` da US1
- **US3 (P1)**: acoplada à passagem da US1; não precisa da US4
- **US4 (P1)**: precisa do status `falha` da US1; visão/API/tela
  podem ser desenvolvidas com INSERT direto de `trabalho` em falha

### Within Each User Story

- Teste vermelho **antes** da produção
- Uma asserção conceitual por teste
- História completa no checkpoint antes de avançar (salvo US3∥US4)

### Parallel Opportunities

- T001 ∥ (início da Foundational depois do helper, se T002 não
  precisar do helper)
- T002 ∥ T004
- T006 ∥ T007
- T009 ∥ T010
- T015 ∥ T016 ∥ T017 ∥ T018 (depois da US1, arquivos distintos)
- T023 ∥ T024
- US3 e US4 em paralelo após US1, se duas pessoas

---

## Parallel Example: User Story 1

```text
T006 testes/unitarios/worker/test_isolamento_da_passagem.py
T007 testes/integracao/test_isolamento_unicidade_ficha.py
```

Depois, só T008 no consumidor.

## Parallel Example: User Story 4

```text
T015 docs/04-schema.sql
T016 testes/unitarios/modulos/hospedagem/test_omissoes_da_fila.py
T017 testes/unitarios/modulos/hospedagem/test_service_da_fila.py
T018 frontend/src/painel/TelaFila.test.tsx
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: passagem isolada; unicidade não mata o worker
4. Demo mínima: `--uma-passagem` com trabalho ruim + bom

### Incremental Delivery

1. Setup + Foundational
2. US1 → worker sobrevive (MVP)
3. US2 → registro sem CPF
4. US3 → expurgo e rotinas no mesmo ciclo
5. US4 → recepção vê a omissão
6. Polish

### Parallel Team Strategy

Um desenvolvedor: ordem US1 → US2 → US3 → US4. Dois: depois da US1,
um faz US2+US3, o outro US4 com INSERT de `falha`.

---

## Notes

- [P] = arquivos diferentes, sem dependência incompleta
- Verificar o vermelho pelo **motivo certo** (AttributeError /
  exceção não capturada / conformidade da visão / campo ausente)
- Commit só se o usuário pedir
- Evitar: parâmetro novo de espera, tela nova, `logger.exception(e)`,
  transação única na passagem, operação na matriz
