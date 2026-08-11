# Data Model: Verificação de Saúde da Aplicação

**Feature**: 001-health-check | **Date**: 2026-08-10

## Persistência

Esta feature **não cria nem altera tabelas**. Nenhuma migração Alembic é necessária.

O endpoint executa apenas `SELECT 1` para verificar conectividade — leitura efêmera, sem
estado gravado.

## Entidades de resposta (contrato API, não persistidas)

### HealthStatus (valores de domínio da resposta)

| Valor | Significado |
|-------|-------------|
| `ok` | Componente disponível |
| `indisponivel` | Componente não respondeu (banco apenas, nesta feature) |

### HealthResponse

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `aplicacao` | enum (`ok`) | Sim | Processo da API em execução |
| `banco` | enum (`ok` \| `indisponivel`) | Sim | Resultado do ping PostgreSQL |

**Regras**:
- Se `banco = indisponivel`, HTTP status da resposta MUST ser 503.
- Se `banco = ok`, HTTP status MUST ser 200.
- `aplicacao` MUST ser `ok` em todas as respostas bem formadas desta feature.

## Configuração (variáveis de ambiente, não tabelas)

Ver [research.md](./research.md) R7. Não há entidade `parametro_hotel` envolvida.

## Relacionamentos

Nenhum. Endpoint não recebe `id_hotel` nem contexto de tenant.

## Validação constitucional

- **Artigo IX**: sem constraints de banco — nada a persistir.
- **Artigo XIV**: `id_hotel` não aplicável a endpoint de infraestrutura global.
