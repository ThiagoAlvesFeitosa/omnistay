# Tasks: Verificação de Saúde da Aplicação

**Input**: Design documents from `/specs/001-health-check/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/health.openapi.yaml, quickstart.md

**Tests**: Incluídos — FR-008, FR-009 e Artigo XII exigem testes automatizados escritos antes do código (TDD).

**Organization**: Tasks grouped by user story. Bootstrap inicial nas fases Setup e Foundational.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Bootstrap do monólito API e ambiente local PostgreSQL

- [X] T001 Create project directory structure per plan.md: `app/`, `app/modulos/sistema/`, `app/portas/`, `app/adaptadores/`, `app/comum/`, `testes/unitarios/modulos/sistema/`, `testes/integracao/`, `alembic/`
- [X] T002 Create `pyproject.toml` with Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2.x, psycopg2-binary, pydantic-settings, pytest, httpx dev dependencies
- [X] T003 [P] Create `docker-compose.yml` with PostgreSQL 16 service for local development
- [X] T004 [P] Create `.env.example` listing `DATABASE_URL`, `HEALTH_DB_TIMEOUT_SECONDS`, `LOG_LEVEL` with no values
- [X] T005 [P] Initialize Alembic in `alembic/` with `alembic.ini` and `alembic/env.py` (no migration revision for this feature)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestrutura compartilhada que bloqueia ambas as user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement `app/config.py` with pydantic-settings loading `DATABASE_URL`, `HEALTH_DB_TIMEOUT_SECONDS` (default 1), `LOG_LEVEL` (default INFO) from environment
- [X] T007 Implement `app/database.py` with SQLAlchemy sync engine factory and session/connection helper used by repositories
- [X] T008 [P] Implement `app/comum/log.py` with structured logging setup that never logs message content or credentials (Artigo VIII)
- [X] T009 Create `app/main.py` with FastAPI application factory and placeholder for router registration
- [X] T010 Create `testes/conftest.py` with pytest fixtures: settings override, FastAPI TestClient, optional postgres availability marker
- [X] T011 [P] Add package `__init__.py` files in `app/`, `app/modulos/`, `app/modulos/sistema/`, `app/comum/`, `app/portas/`, `app/adaptadores/`

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Confirmar que o sistema está operacional (Priority: P1) 🎯 MVP

**Goal**: `GET /health` retorna HTTP 200 com `{ "aplicacao": "ok", "banco": "ok" }` quando PostgreSQL responde

**Independent Test**: `pytest -k banco_disponivel` — TestClient com banco acessível retorna 200 e corpo de sucesso

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [US1] Write failing integration test `test_banco_disponivel_retorna_200` in `testes/integracao/test_health_endpoint.py` asserting HTTP 200 and body per `contracts/health.openapi.yaml`
- [X] T013 [P] [US1] Write failing unit test `test_service_banco_ok_retorna_sucesso` in `testes/unitarios/modulos/sistema/test_health_service.py` with mocked repository returning True

### Implementation for User Story 1

- [X] T014 [P] [US1] Create `app/modulos/sistema/schema.py` with Pydantic `HealthResponse` (`aplicacao`, `banco` enums per `data-model.md`)
- [X] T015 [US1] Implement `app/modulos/sistema/repository.py` with `verificar_conectividade_banco()` executing `SELECT 1` via `app/database.py`
- [X] T016 [US1] Implement `app/modulos/sistema/service.py` with `obter_saude()` returning success when repository ping succeeds
- [X] T017 [US1] Implement `app/modulos/sistema/router.py` with public unauthenticated `GET /health` returning HTTP 200 on success
- [X] T018 [US1] Register sistema router in `app/main.py` and verify T012/T013 pass

**Checkpoint**: User Story 1 fully functional — happy path independently testable

---

## Phase 4: User Story 2 — Detectar indisponibilidade do banco sem derrubar a aplicação (Priority: P1)

**Goal**: `GET /health` retorna HTTP 503 com `{ "aplicacao": "ok", "banco": "indisponivel" }` quando banco falha ou timeout; app continua respondendo

**Independent Test**: `pytest -k banco_indisponivel` — mock ou DATABASE_URL inválida retorna 503; segunda chamada ainda responde

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T019 [US2] Write failing unit test `test_service_banco_indisponivel_retorna_falha` in `testes/unitarios/modulos/sistema/test_health_service.py` with mocked repository raising/returning failure — acrescentado `testes/unitarios/modulos/sistema/test_health_repository.py` para cobrir o tratamento de erro na camada onde ele vive (research R4)
- [X] T020 [US2] Write failing integration test in `testes/integracao/test_health_endpoint.py` asserting HTTP 503, degraded body, and second request still responds — dividido em `test_banco_indisponivel_retorna_503` e `test_banco_indisponivel_app_continua_respondendo` (uma asserção conceitual por teste)

### Implementation for User Story 2

- [X] T021 [US2] Extend `app/modulos/sistema/repository.py` to catch connection errors and timeouts using `HEALTH_DB_TIMEOUT_SECONDS` from `app/config.py`, log only error codes (`DB_TIMEOUT`, `DB_CONNECTION_FAILED`) in `app/comum/log.py`
- [X] T022 [US2] Extend `app/modulos/sistema/service.py` to map repository failures to `banco: indisponivel` without propagating exceptions
- [X] T023 [US2] Extend `app/modulos/sistema/router.py` to return HTTP 503 when `banco` is `indisponivel` while keeping `aplicacao: ok`
- [X] T024 [US2] Verify T019/T020 pass and repeated calls to `/health` remain side-effect free per spec edge cases

**Checkpoint**: User Stories 1 and 2 both independently testable via pytest

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Validação final e conformidade com quickstart

- [X] T025 [P] Update `.gitignore` if needed to exclude `.env`, `.venv/`, `__pycache__/` (verify existing entries sufficient)
- [X] T026 Run full test suite: `pytest testes/unitarios testes/integracao -v` and confirm all tests green
- [X] T027 Run manual validation steps from `specs/001-health-check/quickstart.md` (curl 200 with postgres up, curl 503 with postgres down)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user stories**
- **User Story 1 (Phase 3)**: Depends on Phase 2
- **User Story 2 (Phase 4)**: Depends on Phase 3 (extends same endpoint and module)
- **Polish (Phase 5)**: Depends on Phases 3 and 4

### User Story Dependencies

- **User Story 1 (P1)**: First vertical slice — establishes endpoint happy path
- **User Story 2 (P1)**: Extends US1 repository/service/router for failure path; independently testable via dedicated pytest cases

### Within Each User Story

- Tests MUST be written and FAIL before implementation (Artigo XII)
- schema → repository → service → router
- Verify story checkpoint before next phase

### Parallel Opportunities

- **Phase 1**: T003, T004, T005 in parallel after T001/T002
- **Phase 2**: T008, T011 in parallel with T006–T007 sequence
- **Phase 3**: T013 parallel with T012; T014 parallel before T015
- **Phase 5**: T025 parallel with test runs

---

## Parallel Example: User Story 1

```bash
# Tests first (parallel):
pytest testes/unitarios/modulos/sistema/test_health_service.py -k banco_ok -v   # T013
pytest testes/integracao/test_health_endpoint.py -k banco_disponivel -v        # T012

# Schema while tests are red:
# T014 app/modulos/sistema/schema.py
```

---

## Parallel Example: User Story 2

```bash
# Tests first:
pytest testes/unitarios/modulos/sistema/test_health_service.py -k indisponivel -v  # T019
pytest testes/integracao/test_health_endpoint.py -k indisponivel -v                # T020
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (tests → implementation)
4. **STOP and VALIDATE**: `pytest -k banco_disponivel` green
5. Demo: `curl http://127.0.0.1:8000/health` → 200

### Full Feature Delivery

1. Setup + Foundational → foundation ready
2. User Story 1 → happy path deployable
3. User Story 2 → failure path + resilience validated
4. Polish → quickstart checklist complete

### Single Developer (recommended)

Execute T001→T027 sequentially; use [P] tasks only when context-switching is worth it.

---

## Notes

- No Alembic migration — feature has no persistent entities (`data-model.md`)
- No `id_hotel` on health endpoint (Artigo XIV N/A)
- Contract reference: `specs/001-health-check/contracts/health.openapi.yaml`
- Commit after each checkpoint; one descriptive commit per phase is acceptable
