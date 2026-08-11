# Implementation Plan: Verificação de Saúde da Aplicação

**Branch**: `001-health-check` | **Date**: 2026-08-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-health-check/spec.md`

**Note**: Primeira feature do repositório — bootstrap da estrutura `app/` e `testes/`.

## Summary

Expor `GET /health` que reporta estado da aplicação e conectividade com PostgreSQL.
Resposta HTTP 200 quando ambos disponíveis; HTTP 503 com corpo estruturado (aplicação ok,
banco indisponível) quando o banco falha ou estoura timeout — sem encerrar o processo.

Implementação mínima em módulo `sistema`, seguindo camadas router → service → repository,
com testes pytest escritos antes do código (Artigo XII). Esta feature também estabelece
`app/main.py`, `app/config.py`, `app/database.py` e `.env.example`.

## Technical Context

**Language/Version**: Python 3.14 (`requires-python = ">=3.11"`, conforme `AGENTS.md`)

> Divergência registrada em 2026-08-11: o plano original fixava Python 3.12, mas o ambiente
> de desenvolvimento tem apenas 3.14 instalado. `psycopg2-binary` 2.9.12 publica wheel
> `cp314`, então a stack planejada permanece válida sem substituições.

**Primary Dependencies**: FastAPI, Uvicorn, SQLAlchemy 2.x (core + sync engine para ping),
psycopg2-binary (driver PostgreSQL), pydantic-settings (configuração tipada por env)

**Storage**: PostgreSQL 16 (container Docker local); nenhuma tabela nova nesta feature

**Testing**: pytest, pytest-asyncio (se routers async), httpx (TestClient ASGI), testes
unitários com repository mockado e testes de integração com banco real ou substituto controlado

**Target Platform**: Linux/macOS/Windows dev; API HTTP local

**Project Type**: web-service (API REST)

**Performance Goals**: sucesso em ≤ 2 s (SC-001, medido 0,20 s); falha em ≤ 3 s (SC-002,
medido 2,02 s); ping de banco com timeout padrão 1 s

**Constraints**: configuração exclusivamente por variável de ambiente; `.env.example` lista
nomes sem valores; sem autenticação no endpoint; sem log de conteúdo sensível; sem integração
PMS/mensageria/IA; Alembic presente no projeto mas sem migração nesta feature

**Scale/Scope**: um endpoint, dois cenários de teste obrigatórios, bootstrap inicial do
monólito API

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Artigo | Aplicável? | Verificação |
|--------|------------|-------------|
| I — Sem integração PMS | Sim | Health check não consulta PMS nem serviços externos |
| VIII — Minimização de dados | Sim | Endpoint não expõe PII; logs só códigos de erro de conexão |
| IX — Garantias no banco | N/A | Sem persistência nem alteração de esquema |
| X — Portas trocáveis | Parcial | Ping usa `database.py` diretamente; não exige nova porta de domínio |
| XI — Complexidade mínima | Sim | Um módulo, um endpoint, sem Redis/Celery/cache |
| XII — Teste primeiro | Sim | Dois testes automatizados antes da implementação |
| XIII — Sem número mágico | Sim | Timeout de banco via env `HEALTH_DB_TIMEOUT_SECONDS` |
| XIV — Multi-tenant | N/A | Endpoint global de infraestrutura, sem `id_hotel` |
| XV — Honestidade | Sim | Não verifica worker, fila, ordem de mensagens nem HA |

**Gate pré-Phase 0**: PASS — nenhuma violação.

**Gate pós-Phase 1**: PASS — contrato limitado a conectividade; sem superpromessa.

## Project Structure

### Documentation (this feature)

```text
specs/001-health-check/
├── plan.md              # Este arquivo
├── research.md          # Decisões técnicas Phase 0
├── data-model.md        # Sem entidades persistentes
├── quickstart.md        # Validação manual e pytest
├── contracts/
│   └── health.openapi.yaml
└── tasks.md             # Gerado por /speckit-tasks
```

### Source Code (repository root)

```text
app/
├── main.py                          # FastAPI app, monta routers
├── config.py                        # Settings via pydantic-settings / env
├── database.py                      # Engine SQLAlchemy, session factory, helper de ping
├── modulos/
│   └── sistema/
│       ├── router.py                # GET /health
│       ├── service.py               # Orquestra verificação app + banco
│       ├── repository.py            # SELECT 1 com timeout
│       └── schema.py                # HealthResponse (Pydantic)
├── portas/                          # vazio nesta feature (estrutura reservada)
├── adaptadores/                     # vazio nesta feature
└── comum/
    └── log.py                       # setup mínimo de logging (sem conteúdo de mensagem)

testes/
├── unitarios/
│   └── modulos/
│       └── sistema/
│           └── test_health_service.py   # banco mockado: ok e falha
├── integracao/
│   └── test_health_endpoint.py          # TestClient + PostgreSQL disponível
└── conftest.py                          # fixtures compartilhadas

alembic/                             # inicializado; sem revisão nesta feature
.env.example
docker-compose.yml                   # PostgreSQL 16 local (somente se ainda não existir)
pyproject.toml                       # dependências e entrypoint pytest
```

**Structure Decision**: Monólito API conforme `AGENTS.md`, com módulo `sistema` para
endpoints de infraestrutura transversais (health hoje; métricas futuras se necessário).
Camadas router/service/repository respeitam regra de fronteira do projeto.

## Complexity Tracking

> Nenhuma violação constitucional a justificar.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
