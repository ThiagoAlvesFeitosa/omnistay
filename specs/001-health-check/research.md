# Research: Verificação de Saúde da Aplicação

**Feature**: 001-health-check | **Date**: 2026-08-10

## R1 — Caminho e método HTTP do endpoint

**Decision**: `GET /health`, sem autenticação, sem parâmetros.

**Rationale**: Convenção de facto para probes de load balancer e Docker/Kubernetes.
Alinha com FR-001 e assumption de monitoramento interno. Caminho único e previsível.

**Alternatives considered**:
- `/healthz` — equivalente, menos comum no ecossistema FastAPI brasileiro
- `/ready` separado de `/live` — rejeitado: spec exige endpoint único com ambos os estados
- POST com body — rejeitado: probes HTTP usam GET idempotente

## R2 — Semântica HTTP conforme clarificação

**Decision**:
- Banco ok → HTTP **200**
- Banco indisponível ou timeout → HTTP **503**
- Corpo JSON sempre presente com campos separados `aplicacao` e `banco`

**Rationale**: Clarificação Session 2026-08-10 (Opção A). Permite que balanceador trate
503 como “não rotear tráfego” enquanto corpo distingue app vs banco.

**Alternatives considered**:
- HTTP 200 + campo `status: degraded` — rejeitado na clarificação
- Dois endpoints — rejeitado na clarificação

## R3 — Verificação de conectividade com PostgreSQL

**Decision**: Executar `SELECT 1` via SQLAlchemy sync engine com `statement_timeout`
equivalente ao timeout configurável (env `HEALTH_DB_TIMEOUT_SECONDS`, default `1`).

**Rationale**: “Verificação leve de conectividade” da spec. Mais confiável que apenas abrir
socket TCP — confirma que PostgreSQL aceita queries. Sync evita complexidade async no
bootstrap; FastAPI pode chamar service sync em threadpool ou service async fino que delega.

**Alternatives considered**:
- `connection.ping()` TCP only — não valida autenticação/credenciais
- Verificar migrações pendentes — fora do escopo (assumption da spec)
- asyncpg direto — adiciona segunda stack de DB antes de necessidade

**Medição real (2026-08-11)**: contra host inalcançável, `connect_timeout=1` resulta em
2,02 s e `connect_timeout=2` em 4,03 s. O cliente PostgreSQL trata valores abaixo de 2 como
2 segundos, e um host com IPv6 e IPv4 é tentado em ambos. SC-002 foi corrigido de 2 para
3 segundos por causa disso.

## R4 — Tratamento de timeout e falha

**Decision**: Timeout capturado no repository; service retorna estado `banco: indisponivel`
sem propagar exceção ao processo. Router mapeia para HTTP 503. Log registra código de erro
(ex.: `DB_TIMEOUT`, `DB_CONNECTION_FAILED`), nunca string de conexão com credenciais.

**Rationale**: FR-005, FR-007, edge case de lentidão. Aplicação permanece no ar.

**Alternatives considered**:
- Deixar exceção subir → risco de 500 genérico ou crash em configuração errada
- Retry automático no health check — rejeitado: probe deve ser rápido e determinístico

## R5 — Formato do corpo de resposta

**Decision**:

```json
{
  "aplicacao": "ok",
  "banco": "ok"
}
```

Valores permitidos: `"ok"` | `"indisponivel"` para `banco`; `"ok"` para `aplicacao` nesta
feature (aplicação só falha se processo morrer — fora do escopo do endpoint).

**Rationale**: Atende FR-002/003, distingue componentes, parseável por humano e automação,
sem fingerprinting (sem versões, hostnames, stack traces).

**Alternatives considered**:
- `{ "status": "healthy", "checks": {...} }` — mais verboso, sem ganho para escopo atual
- Incluir latência em ms — útil mas não exigido; pode entrar depois sem quebrar contrato

## R6 — Estratégia de testes (Artigo XII)

**Decision**:
1. **Unitário** (`test_health_service.py`): mock do repository — cenários banco ok e banco
   falha/timeout; assert status HTTP lógico e corpo.
2. **Integração** (`test_health_endpoint.py`): TestClient contra app real; PostgreSQL
   disponível → 200; repository substituído ou DATABASE_URL inválida → 503, segunda
   chamada ainda responde (app no ar).

**Rationale**: FR-008/FR-009, SC-003. Unitário rápido no ciclo TDD; integração prova wiring.

**Alternatives considered**:
- Só E2E — lento demais para ciclo diário
- Só unitário — não prova que engine/config estão corretos

## R7 — Configuração por variável de ambiente

**Decision**: Variáveis mínimas:

| Variável | Obrigatória | Default | Uso |
|----------|-------------|---------|-----|
| `DATABASE_URL` | Sim | — | Conexão PostgreSQL |
| `HEALTH_DB_TIMEOUT_SECONDS` | Não | `1` | Timeout do ping |
| `LOG_LEVEL` | Não | `INFO` | Nível de log da API |

`.env.example` lista nomes sem valores.

**Rationale**: Input do usuário + Artigo XIII (timeout não hardcoded).

**Alternatives considered**:
- `parametro_hotel` para timeout — rejeitado: parâmetro operacional de hotel, não de infra
- Arquivo YAML de config — rejeitado: user exige env only

## R8 — Bootstrap vs feature isolada

**Decision**: Esta feature cria esqueleto mínimo (`main`, `config`, `database`, pytest,
docker-compose postgres, alembic init) necessário para implementar e testar health.

**Rationale**: Repositório greenfield; health é primeiro vertical slice utilizável.

**Alternatives considered**:
- Feature só com router em arquivo solto — violaria AGENTS.md e dificultaria próximas features
