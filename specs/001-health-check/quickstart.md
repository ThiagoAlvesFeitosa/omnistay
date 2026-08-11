# Quickstart: Verificação de Saúde da Aplicação

**Feature**: 001-health-check | **Contrato**: [health.openapi.yaml](./contracts/health.openapi.yaml)

## Pré-requisitos

- Python 3.12
- Docker (PostgreSQL 16 local)
- Dependências instaladas (`pip install -e ".[dev]"` ou equivalente após bootstrap)

## 1. Subir PostgreSQL

```bash
docker compose up -d postgres
```

Aguardar container healthy antes dos testes de integração.

## 2. Configurar ambiente

Copiar `.env.example` para `.env` e preencher valores localmente (não commitar `.env`):

```bash
cp .env.example .env
```

Variáveis necessárias — ver [research.md](./research.md) R7.

## 3. Rodar testes (TDD — Artigo XII)

Ordem esperada no ciclo de implementação:

```bash
# Deve falhar antes da implementação existir
pytest testes/unitarios/modulos/sistema/test_health_service.py -v
pytest testes/integracao/test_health_endpoint.py -v
```

| Cenário | Comando focal | Resultado esperado |
|---------|---------------|-------------------|
| Banco ok | `pytest -k "banco_disponivel" -v` | HTTP 200, corpo `{ "aplicacao": "ok", "banco": "ok" }` |
| Banco indisponível | `pytest -k "banco_indisponivel" -v` | HTTP 503, corpo `{ "aplicacao": "ok", "banco": "indisponivel" }`; segunda chamada ainda responde |

Suite completa:

```bash
pytest testes/unitarios -q
pytest testes/integracao -q
```

## 4. Subir API e validar manualmente

```bash
uvicorn app.main:app --reload
```

### Banco disponível

```bash
curl -s -o /tmp/health.json -w "%{http_code}" http://127.0.0.1:8000/health
cat /tmp/health.json
```

Esperado: código `200`, JSON com `"banco": "ok"`.

### Banco indisponível

Parar PostgreSQL ou apontar `DATABASE_URL` para porta inválida, reiniciar API:

```bash
docker compose stop postgres
curl -s -o /tmp/health.json -w "%{http_code}" http://127.0.0.1:8000/health
cat /tmp/health.json
```

Esperado: código `503`, JSON com `"banco": "indisponivel"`, `"aplicacao": "ok"`, em cerca de
2 segundos (piso do `connect_timeout` do cliente PostgreSQL).

Confirmar que a API ainda responde a uma segunda chamada:

```bash
curl -s -w "\n%{http_code}\n" http://127.0.0.1:8000/health
```

## 5. Critérios de aceite (spec)

- [ ] FR-004 / FR-010: banco ok → sucesso HTTP e corpo
- [ ] FR-005: banco down → HTTP 503, app no ar
- [ ] FR-008 / FR-009: testes automatizados para ambos os cenários
- [ ] SC-001 / SC-002: resposta em ≤ 2 s
- [ ] FR-007: logs sem credenciais nem conteúdo sensível

## Referências

- [spec.md](./spec.md) — requisitos funcionais
- [plan.md](./plan.md) — estrutura de código
- [data-model.md](./data-model.md) — campos da resposta

## Limitações explícitas (Artigo XV)

Este endpoint **não** verifica: worker, fila, mensageria, IA, PMS, ordem de mensagens,
alta disponibilidade ou migrações pendentes.
