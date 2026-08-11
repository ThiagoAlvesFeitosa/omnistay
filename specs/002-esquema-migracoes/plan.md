# Implementation Plan: Esquema e Migrações

**Branch**: `002-esquema-migracoes` | **Date**: 2026-08-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-esquema-migracoes/spec.md`

## Summary

Levar um banco vazio ao esquema completo do OmniStay com uma única operação, criando junto as
garantias que o próprio banco impõe — domínio de valor, transição de estado da reserva e
unicidade do identificador de evento de webhook.

A abordagem técnica tem três decisões centrais, detalhadas em [research.md](./research.md):

1. **Uma única revisão do Alembic executa o SQL do documento de referência**, carregado de uma
   cópia congelada em `alembic/versions/sql/`. Ninguém reescreve o esquema em chamadas de
   `op.create_table()`: a trigger, a função `plpgsql`, a visão e os índices parciais não têm
   representação natural nessa forma, e a transcrição seria uma segunda descrição a manter à mão.
2. **A conformidade entre documento e banco é verificada por máquina**, comparando inventários
   estruturais extraídos do catálogo do PostgreSQL de dois bancos descartáveis — um que recebeu as
   migrações e outro que recebeu o documento. Comparação por texto de SQL falharia por indentação
   e por normalização de expressões, não por divergência real.
3. **A verificação de versão do servidor roda em `alembic/env.py`**, antes de qualquer comando de
   esquema, e por isso vale para toda migração futura sem ser repetida em cada revisão. A decisão
   em si é uma função pura, para ser exercitada sem precisar de um servidor antigo que o projeto
   não provisiona.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Alembic 1.14+, SQLAlchemy 2.0+, psycopg2-binary. Nenhuma dependência
nova é introduzida por esta fatia.

**Storage**: PostgreSQL 16, versão mínima verificada em tempo de migração

**Testing**: pytest, com marcador `postgres` para o que exige banco real

**Target Platform**: Servidor Linux; desenvolvimento em Windows com PostgreSQL em contêiner

**Project Type**: Serviço web (API FastAPI com worker), estrutura já estabelecida pela fatia F0.1

**Performance Goals**: Não se aplica. A migração roda em implantação, não em requisição

**Constraints**: A aplicação é atômica — falha não deixa estrutura pela metade. A suíte de testes
precisa continuar rápida sem banco, sem que isso permita confundir suíte verde com entrega
verificada

**Scale/Scope**: 16 tabelas de domínio, ~40 restrições `CHECK`, 7 restrições de unicidade,
1 trigger com função, 1 visão de apoio

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas duas passagens, sem
violações.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Nenhuma estrutura de importação, sincronização ou espelho de reserva do PMS. `numero_quarto` é texto livre justamente porque o inventário de quartos vive fora |
| VIII — Minimização de dados | O esquema não tem campo de foto de documento nem coluna de idade. Nenhum dado é inserido pela migração |
| IX — Garantias no banco | **É a razão de ser da fatia.** Idempotência como `UNIQUE`, transição de estado como trigger, domínio de valor como `CHECK` |
| XI — Complexidade exige problema | Nenhuma dependência nova. A verificação de conformidade usa `pg_catalog`, já disponível, em vez de ferramenta externa de comparação de esquema |
| XII — Teste primeiro | Cada garantia tem teste escrito antes, que falha contra banco sem migração e passa depois. A ordem das tarefas na Fase 2 precisa preservar isso |
| XIII — Parâmetro não é constante | `parametro_hotel` é criada aqui, com as chaves previstas registradas em comentário. A versão mínima do PostgreSQL é constante de código legítima: é dependência de plataforma, não parâmetro operacional de propriedade |
| XIV — Multi-tenant desde a primeira linha | `id_hotel` presente nas tabelas de domínio desde a criação, e não acrescentado depois |
| XV — Honestidade | Reversão de migração não é entregue e a spec declara isso, em vez de sugerir que existe |

**Ponto de atenção, não violação**: a decisão de a revisão carregar uma cópia congelada do SQL
cria duas cópias do esquema no repositório. Isso seria um risco sob o Artigo IX se dependesse de
disciplina humana, mas a FR-018 põe a conferência na suíte de testes. A alternativa — a revisão ler
o arquivo vivo — foi rejeitada porque quebraria toda migração futura, conforme
[research.md](./research.md) seção 1.

## Project Structure

### Documentation (this feature)

```text
specs/002-esquema-migracoes/
├── plan.md              # Este arquivo
├── spec.md              # Especificação, já esclarecida
├── research.md          # Fase 0: decisões técnicas e divergências encontradas
├── data-model.md        # Fase 1: entidades, garantias e ciclo de vida
├── quickstart.md        # Fase 1: como validar a entrega do zero
├── contracts/
│   └── inventario-de-esquema.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Fase 2, gerada por /speckit-tasks
```

### Source Code (repository root)

```text
alembic/
├── env.py                              # Recebe a verificação de versão do servidor
└── versions/
    ├── 0001_esquema_inicial.py         # A revisão: lê e executa o SQL companheiro
    └── sql/
        └── 0001_esquema_inicial.sql    # Cópia congelada de docs/04-schema.sql

app/
└── comum/
    └── versao_do_banco.py              # Decide se a versão do servidor atende ao mínimo

testes/
├── conftest.py                         # Perde a URL embutida; chama a política de banco
├── suporte/
│   ├── banco_descartavel.py            # Cria e remove bancos de teste
│   ├── inventario.py                   # Extrai e compara inventários
│   └── politica_de_banco.py            # Decide entre pular e falhar
├── unitarios/
│   ├── test_guarda_de_versao.py        # FR-020
│   └── test_politica_de_banco_exigido.py  # FR-019
└── integracao/
    ├── test_inventario.py              # Verifica a própria ferramenta de verificação
    ├── test_garantias_do_banco.py      # FR-012, FR-013, FR-014
    ├── test_conformidade_do_esquema.py # FR-017, FR-018
    └── test_aplicacao_da_migracao.py   # FR-001, FR-008, FR-009, FR-010

docs/
└── 04-schema.sql                       # Corrigido: sem BEGIN/COMMIT, PostgreSQL 16
```

**Structure Decision**: a estrutura já foi estabelecida pela fatia F0.1 e esta fatia não a altera.
O que se acrescenta é a pasta `alembic/versions/` — que ainda não existia, porque não havia
nenhuma revisão — e a pasta `testes/suporte/`, para o que os testes de banco compartilham. Não há
módulo novo em `app/`: a fatia cria estrutura de banco, e nenhum serviço de domínio ainda lê essas
tabelas. Por isso também não há contrato HTTP; o único contrato publicado é interno e está em
`contracts/inventario-de-esquema.md`.

## Correções no documento de referência

A spec exige (FR-015) que divergências entre o documento e o comportamento real sejam corrigidas
no documento na mesma entrega. Duas foram encontradas na Fase 0 e precisam virar tarefa:

| Divergência | Correção |
| --- | --- |
| `docs/04-schema.sql` abre `BEGIN;` e fecha `COMMIT;` | Remover ambos e registrar no cabeçalho que o controle de transação é de quem aplica, indicando `psql --single-transaction` para aplicação manual. O `COMMIT` fecharia a transação da migração antes do registro de versão, produzindo o estado parcial que a FR-010 proíbe |
| O cabeçalho declara `SGBD: PostgreSQL 14+` | Trocar por `PostgreSQL 16`. Não é contradição: é compatibilidade não verificada. O documento passa a declarar apenas a versão que o teste exercita |

Uma terceira divergência é entre código existente e a spec, não dentro do documento:
`testes/conftest.py` traz uma URL de conexão com senha embutida, contra a FR-011. A correção está
descrita em [research.md](./research.md) seção 7 e entra nesta entrega, porque é a fatia que mexe
na configuração de acesso ao banco.

## Levantamento do ambiente a partir do zero

A entrega inclui uma execução real do ambiente partindo do nada: `docker compose down -v` seguido
de `docker compose up -d`, confirmando que o contêiner reconstrói o banco vazio sem intervenção, e
então a migração e a suíte completa sobre esse volume recém-criado. O roteiro está no
[quickstart.md](./quickstart.md), como Cenário 0 e como verificação final.

Isso fecha uma pendência aberta desde a fatia F0.1: o ambiente sempre foi exercitado sobre um
volume que já existia, então a promessa de reprodutibilidade da SC-001 nunca chegou a ser
verificada de ponta a ponta. É a fatia certa para fechá-la, porque é a primeira em que existe algo
para reconstruir.

## Complexity Tracking

Sem violações constitucionais a justificar. Nenhuma dependência, serviço ou camada de abstração é
introduzida por esta fatia.
