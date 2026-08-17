# Implementation Plan: Catálogo da Propriedade

**Branch**: `008-catalogo-propriedade` | **Date**: 2026-08-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/008-catalogo-propriedade/spec.md`

## Summary

A recepção cadastra e mantém os fatos da propriedade nas cinco categorias (horários,
cardápio, serviços, programação, regras). Item nasce ativo; desativar não apaga; a
consulta do **catálogo ativo completo** omite inativos e é a única fonte que o
atendimento posterior poderá afirmar. Gestão consulta; operação não acessa; hotel A não
vê hotel B. Preço estruturado fica fora (F3.7).

Decisões em [research.md](./research.md): sem migração (`catalogo_item` já existe); API
sem React; SQL só em `propriedade`; porta `CatalogoRepository` para F2.2/F3.3; operação
nova `ler_catalogo`; categoria imutável; PATCH único para texto e ativo.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary (já no
projeto). **Nenhuma dependência nova.**

**Storage**: PostgreSQL 16. Reuso de `catalogo_item`. **Sem revisão Alembic.**
`atualizado_em` no `UPDATE` da aplicação

**Testing**: pytest. Unitários sem rede (validação, política, log, `CatalogoFalso`).
Integração com PostgreSQL real: CRUD, desativar/reativar, consulta ativa, isolamento,
recusas de perfil, `DELETE` → 405

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em contêiner.
API apenas nesta fatia

**Project Type**: Serviço web. Sem frontend, sem worker novo

**Performance Goals**: Listar o catálogo de uma propriedade (dezenas de itens no MVP) é
uma consulta indexada por hotel. Sem paginação nesta fatia

**Constraints**: `id_hotel` só da sessão; texto do fato não é o conteúdo principal do
log; sem preço; sem `DELETE`; testes sem provedor de IA; porta não abre conexão própria

**Scale/Scope**: 4 rotas HTTP, 1 operação nova na matriz, 1 porta + 2 adaptadores, módulo
`propriedade` ganha router/schema. Sem React, sem migração, sem mensagem ao hóspede

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas duas
passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Fatos digitados pela recepção; nada lido do PMS |
| II — Na dúvida, humano vê | Esta fatia só deposita fatos; pergunta fora do catálogo continua F3.3 |
| III — Gravar antes de enviar | Não envia mensagem; gravação é o produto |
| IV — Fila como verdade | Não se aplica (não é alerta operacional) |
| V — Ausência humana visível | Catálogo vazio é 200 com listas vazias; F2.2 verá a omissão |
| VI — Confirmação antes de tramitar | Não se aplica |
| VII — Não ser intrusivo | Nenhuma mensagem proativa |
| VIII — Minimização | Catálogo não é dado de hóspede; log sem texto do fato |
| IX — Garantias no banco | `CHECK` de categoria e default `ativo` já existem; aplicação não os substitui |
| X — Portas trocáveis | `CatalogoRepository` + falso + banco (mesma conexão) |
| XI — Complexidade exige problema | Sem lib, sem migração, sem tabela de preço, sem tela, sem lock otimista |
| XII — Teste primeiro | Cada FR com teste que falha por ausência |
| XIII — Parâmetro não é constante | Nenhum prazo novo |
| XIV — Multi-tenant | Toda query com `id_hotel` da sessão |
| XV — Honestidade | Sem React, sem boas-vindas, sem resposta a dúvida, sem preço — ver seção própria |

**Ponto de atenção 1 — porta vs dono da tabela.** HTTP de manutenção usa
`propriedade.repository`. A porta existe para *outros* módulos e reusa o mesmo `SELECT`
de ativos, com a conexão da transação — não um engine paralelo.

**Ponto de atenção 2 — `ler_catalogo`.** A matriz da F0.3 só previa escrita. Sem a
operação de leitura, a gestão não consulta. Acrescentar é cumprir a spec, não alargar
perfil.

**Ponto de atenção 3 — pendência de preços.** Fechada por adiamento na spec. Na
implementação, atualizar `docs/00-ESTADO-DO-PROJETO.md` para não deixar a caixa aberta
como se a F2.1 tivesse esquecido.

**Ponto de atenção 4 — clarify.** O comando de esclarecimento não concluiu a fila; o
planejamento usou a spec (preço fora) e esta pesquisa (categoria imutável, PATCH único).

## Project Structure

### Documentation (this feature)

```text
specs/008-catalogo-propriedade/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-de-catalogo.md
│   ├── catalogo-repository.md
│   └── politica-de-autorizacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
app/
├── main.py                              # include roteador de propriedade
├── portas/
│   └── catalogo.py                      # CatalogoRepository + ItemCatalogo
├── adaptadores/
│   ├── catalogo_falso.py
│   └── catalogo_banco.py                # Connection injetada; delega ao repositório
└── modulos/
    ├── acesso/
    │   └── politica.py                  # + ler_catalogo
    └── propriedade/
        ├── router.py                    # novo
        ├── schema.py                    # novo
        ├── service.py                   # criar, patch, listar, listar_ativos, log
        └── repository.py                # SQL catalogo_item

testes/
├── unitarios/
│   ├── adaptadores/
│   │   └── test_catalogo_falso.py
│   └── modulos/
│       ├── acesso/
│       │   └── test_politica.py         # estende
│       └── propriedade/
│           ├── test_catalogo.py         # validação, categoria imutável
│           └── test_log_sem_conteudo.py
└── integracao/
    └── test_catalogo.py                 # rotas, isolamento, perfis, 405

docs/
└── 00-ESTADO-DO-PROJETO.md              # F2.1 em andamento; preços adiados à F3.7
```

**Structure Decision**: monolito modular existente. Catálogo pertence a `propriedade`
(Artefato 5). Sem frontend. Sem pasta `alembic/versions` nesta fatia.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Pacote de boas-vindas | Consulta ativa existe; ninguém a envia ao hóspede | F2.2 |
| Resposta a dúvida a partir do catálogo | Porta pronta; prompt não montado | F3.3 |
| Preço / item vendável | Texto corrido nas categorias cardápio e serviço | F3.7 |
| Tela React de manutenção | Estado via API | Fatia de UI |
| Migração / coluna nova | Esquema `0001` basta | Só se F3.7 exigir |
| Troca de categoria no PATCH | Recategorizar = criar + desativar | Fora |
| Semeadura de itens no bootstrap | Catálogo nasce vazio | Fora |

## Complexity Tracking

> Sem violações a justificar. Tabela omitida.
