# Implementation Plan: Cadastro de Concorrentes

**Branch**: `020-cadastrar-concorrentes` | **Date**: 2026-08-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/020-cadastrar-concorrentes/spec.md`

## Summary

A gestão cadastra e mantém os concorrentes da propriedade (nome + endereço da
fonte pública). A ficha nasce ativa; desativar não apaga; a consulta de
**fontes ativas** omite inativos e é o conjunto que a coleta posterior poderá
usar. Recepção e operação não acessam; hotel A não vê hotel B. Esta fatia
**não** visita a fonte, **não** grava preço e **não** monta painel.

Decisões em [research.md](./research.md): módulo `mercado` nasce; tabela
`concorrente` já existe; revisão `0019` só com UNIQUE da fonte, CHECK de URL e
índice parcial de ativos; API sem React; sem porta hexagonal (F5.2 é o mesmo
módulo); operações `alterar_concorrentes` e `ler_concorrentes` só para gestão;
PATCH único para texto e ativo.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary
(já no projeto). Validação de URL com `urllib.parse` (biblioteca padrão).
**Nenhuma dependência nova.** Sem `httpx`/cliente HTTP de saída no módulo

**Storage**: PostgreSQL 16. Reuso de `concorrente`. Revisão
`0019_cadastrar_concorrentes`: `uq_concorrente_hotel_fonte`,
`ck_concorrente_url_fonte`, `ix_concorrente_hotel_ativo`. **Nenhuma tabela
nova.** `coleta_mercado` intocada. Nenhum `parametro_hotel` novo

**Testing**: pytest. Unitários sem rede (URL, trim, política, log sem
nome/endereço). Integração com PostgreSQL real: CRUD, desativar/reativar,
fontes ativas omitem inativo, isolamento, recusas de perfil, `DELETE` → 405,
unicidade inclusive inativo, CHECK de URL, cadastro não insere coleta

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em
contêiner. API apenas nesta fatia

**Project Type**: Serviço web. Sem frontend, sem worker novo

**Performance Goals**: Listar concorrentes de uma propriedade (dezenas no MVP)
é consulta indexada por hotel. Sem paginação nesta fatia

**Constraints**: `id_hotel` só da sessão; nome e URL não são o conteúdo
principal do log; sem `DELETE`; sem visita à fonte; testes sem rede externa;
serviço não abre conexão própria além da da requisição

**Scale/Scope**: 4 rotas HTTP (+ `405` no DELETE), 2 operações novas na matriz,
módulo `mercado` (router/schema/service/repository), 1 revisão Alembic. Sem
React, sem porta, sem mensagem ao hóspede, sem agendador

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas
duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Lista de observação; nada lido nem escrito no PMS; tarifa da casa não muda |
| II — Na dúvida, humano vê | Não classifica mensagem; ToS da fonte é escolha de quem cadastra |
| III — Gravar antes de enviar | Não envia mensagem; gravação da ficha é o produto |
| IV — Fila como verdade | Não se aplica (não é alerta operacional) |
| V — Ausência humana visível | Lista vazia é 200 com `fontes: []`; F5.2 verá a omissão |
| VI — Confirmação antes de tramitar | Não se aplica |
| VII — Não ser intrusivo | Nenhuma mensagem ao hóspede |
| VIII — Minimização | Concorrente não é dado de hóspede; log sem nome/URL; URL com credencial recusada |
| IX — Garantias no banco | UNIQUE da fonte por hotel (inclusive inativo); CHECK de URL; aplicação não os substitui |
| X — Portas trocáveis | Sem porta nova: o consumidor da lista ativa é o próprio `mercado` (F5.2) |
| XI — Complexidade exige problema | Sem lib, sem tabela nova, sem porta, sem tela, sem visita à fonte, sem lock otimista |
| XII — Teste primeiro | Cada FR com teste que falha por ausência |
| XIII — Parâmetro não é constante | Periodicidade já existe; esta fatia não a inventa nem a lê |
| XIV — Multi-tenant | Toda query com `id_hotel` da sessão |
| XV — Honestidade | Sem React, sem coleta, sem ToS automático, sem painel de preço — ver seção própria |

**Ponto de atenção 1 — gestão escreve a lista.** Contrasta com “somente
leitura” do painel (Artefato 5 §11.2). A spec fechou: gestão cadastra quem
acompanhar; não inventa preço. Na implementação, registrar em
`docs/00-ESTADO-DO-PROJETO.md`.

**Ponto de atenção 2 — sem porta.** Catálogo teve `CatalogoRepository` porque
outro módulo lê. Aqui F5.2 permanece em `mercado`; extrair porta só se um
terceiro módulo precisar.

**Ponto de atenção 3 — UNIQUE completo, não parcial.** `item_vendavel` unique
parcial `WHERE ativo` permite reusar nome inativo. A spec de concorrente
proíbe reusar a fonte inativa — o caminho é reativar.

**Ponto de atenção 4 — conformidade do esquema.** Índice e CHECK entram na
revisão **e** em `docs/04-schema.sql`; `0001` congelado. Sem isso,
`test_conformidade_do_esquema` quebra num dos sentidos.

## Project Structure

### Documentation (this feature)

```text
specs/020-cadastrar-concorrentes/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-de-concorrentes.md
│   ├── fontes-ativas.md
│   └── politica-de-autorizacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
alembic/versions/
├── 0019_cadastrar_concorrentes.py
└── sql/
    └── 0019_cadastrar_concorrentes.sql

app/
├── main.py                              # include roteador de mercado
├── modulos/
│   ├── acesso/
│   │   └── politica.py                  # + alterar_concorrentes, ler_concorrentes
│   └── mercado/                         # novo
│       ├── router.py
│       ├── schema.py
│       ├── service.py                   # trim, URL, unicidade, log
│       └── repository.py                # SQL concorrente

testes/
├── unitarios/
│   └── modulos/
│       ├── acesso/
│       │   └── test_politica.py         # estende
│       └── mercado/
│           ├── test_concorrentes.py     # validação de URL, trim, duplicata
│           └── test_log_sem_conteudo.py
└── integracao/
    ├── test_concorrentes.py             # rotas, isolamento, perfis, 405, sem coleta
    └── test_garantias_do_banco.py       # UNIQUE + CHECK

docs/
├── 04-schema.sql                        # CHECK + índices
└── 00-ESTADO-DO-PROJETO.md              # F5.1; gestão escreve lista, não preço
```

**Structure Decision**: monolito modular existente. Mercado pertence a
`app/modulos/mercado/` (Artefato 5). Sem frontend. Sem worker. Sem pasta
`portas/` nesta fatia.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Coleta de preço/avaliação | Fontes ativas existem; ninguém as visita | F5.2 |
| Painel com data da coleta | Cadastro visível por API; sem série temporal na UI | F5.3 |
| Verificação automática de termos de uso | Quem cadastra escolhe fonte pública | Humana / F5.2 |
| Tela React de manutenção | Estado via API | Fatia de UI |
| Porta hexagonal de fontes | F5.2 chama o serviço do mesmo módulo | Só se outro módulo precisar |
| Semeadura no bootstrap | Lista nasce vazia | Fora |
| `DELETE` permanente | Histórico futuro de coletas precisa da ficha | Fora |
| Periodicidade nova | Chave já existe em `parametro_hotel` | F5.2 lê |

## Complexity Tracking

> Sem violações a justificar. Duas operações na matriz existem porque reusar
> `ler_catalogo` / `alterar_catalogo` daria a lista à recepção, contra a spec.
> O módulo `mercado` já estava no mapa do Artefato 5; não é serviço novo.
> Tabela omitida.
