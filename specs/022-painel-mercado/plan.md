# Implementation Plan: Painel de Mercado

**Branch**: `022-painel-mercado` | **Date**: 2026-08-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/022-painel-mercado/spec.md`

## Summary

A gestão consulta preço e nota já coletados, **sempre com a data**, vê o
histórico da série e recebe sinal explícito quando o dado envelheceu. Falha
posterior não apaga nem redata o último sucesso. Ninguém altera a série —
nem a gestão. Sem visita à fonte, sem disparo de coleta, sem tarifa da casa.

Decisões em [research.md](./research.md): `GET /mercado` (visão atual) e
`GET /mercado/concorrentes/{id}` (histórico); operação `ler_mercado` só
gestão; `situacao` derivada no serviço com o mesmo limiar da F5.2; zero
migração; zero escrita em `coleta_mercado`.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, psycopg2-binary
(já no projeto). Relógio de `app.comum.relogio`. **Nenhuma dependência
nova.** Sem worker novo, sem porta nova, sem cliente HTTP nesta fatia

**Storage**: PostgreSQL 16. Reuso de `concorrente`, `coleta_mercado`,
`parametro_hotel` e `ix_coleta_concorrente_data`. **Nenhuma tabela, coluna,
índice, view nem revisão Alembic**

**Testing**: pytest. Unitários sem banco de coletor (situação, janela,
cadência ausente, zero vs vazio, log). Integração com PostgreSQL real:
GETs, isolamento, `403`/`404`/`405`, inativo visível, GET não insere
coleta nem trabalho. Relógio e parâmetro injetáveis

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em
contêiner. API apenas nesta fatia

**Project Type**: Serviço web. Sem frontend, sem alteração de worker

**Performance Goals**: Dezenas de concorrentes no MVP; histórico sem
paginação (cadência ~1 ponto/dia). Duas consultas SQL por visão atual
(fichas + últimos pontos) bastam; sem view

**Constraints**: `id_hotel` só da sessão; preço/nota/URL fora do log; sem
default de periodicidade na leitura; testes sem worker e sem rede; serviço
não escreve `coleta_mercado`

**Scale/Scope**: 2 rotas GET, 1 operação na matriz, extensões em
`mercado` (router/schema/service/repository) e `acesso.politica`. 0
migrações, 0 portas, 0 flags de worker, 0 telas React

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas
duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Só lê a série pública já gravada; tarifa da casa não entra no payload |
| II — Na dúvida, humano vê | Não classifica mensagem; não inventa número quando a coleta falhou |
| III — Gravar antes de enviar | Não se aplica (não envia mensagem; não coleta) |
| IV — Fila como verdade | O painel **é** o lugar do número; não há notificação de coleta nova |
| V — Ausência humana visível | Lista vazia e `sem_coleta` são explícitas; não dependem de clique de balcão |
| VI — Confirmação antes de tramitar | Não se aplica |
| VII — Não ser intrusivo | Zero mensagem ao hóspede; não dispara coleta |
| VIII — Minimização | Sem avaliador, sem URL no payload do painel, log sem preço/nota/texto |
| IX — Garantias no banco | CHECKs da série já na `0001`; esta fatia não os enfraquece e não dá UPDATE |
| X — Portas trocáveis | Sem porta nova: não há I/O externo nesta fatia |
| XI — Complexidade exige problema | Sem lib, sem tabela, sem view, sem React, sem paginação, sem Δ% |
| XII — Teste primeiro | Cada FR com teste que falha por ausência |
| XIII — Parâmetro não é constante | Limiar = `periodicidade_coleta_mercado`; ausência não usa 24 |
| XIV — Multi-tenant | JOIN/`WHERE` em `concorrente.id_hotel` da sessão |
| XV — Honestidade | Sem React, sem tarifa da casa, sem cobertura de OTA, sem “coletar agora” |

**Ponto de atenção 1 — `ler_mercado` ≠ `ler_concorrentes`.** A matriz da
F5.1 já é só gestão nas duas. Operação nova mesmo assim: cadastrar quem
acompanhar e ler o número coletado são recursos distintos, e a F5.1
reservou o nome. Reusar `ler_indicadores` abriria o painel à recepção.

**Ponto de atenção 2 — último sucesso, não última linha.** `ultima_coleta`
da F5.2 (qualquer desfecho) **não** alimenta o preço da visão atual.
Reusá-la sozinha viola FR-003/FR-007. O repositório desta fatia precisa
do último sucesso **e** da última linha, separados.

**Ponto de atenção 3 — limiar igual ao da coleta.** `agora >= U + P` é o
mesmo critério de “devido” da F5.2. Dois limiares (calendário, chave nova)
foram recusados. Registrar no estado do projeto na implementação.

**Ponto de atenção 4 — sem migração.** `04-schema.sql` e as revisões
congeladas não mudam. Comentário de `coleta_mercado` já menciona o painel.
Atualizar só `docs/00-ESTADO-DO-PROJETO.md`.

## Project Structure

### Documentation (this feature)

```text
specs/022-painel-mercado/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-de-painel.md
│   ├── situacao-do-dado.md
│   └── politica-de-autorizacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
app/
├── modulos/
│   ├── acesso/
│   │   └── politica.py                  # + ler_mercado
│   └── mercado/
│       ├── router.py                    # GET /mercado e GET .../concorrentes/{id}
│       ├── schema.py                    # visão atual + histórico
│       ├── service.py                   # situacao, relógio, parâmetro injetável
│       └── repository.py                # SELECT último sucesso, última linha, série

testes/
├── unitarios/
│   └── modulos/
│       ├── acesso/
│       │   └── test_politica.py         # estende
│       └── mercado/
│           ├── test_painel_mercado.py   # situacao, janela, zero vs vazio
│           └── test_log_sem_conteudo.py # estende
└── integracao/
    └── test_painel_mercado.py           # rotas, perfis, 404/405, isolamento

docs/
└── 00-ESTADO-DO-PROJETO.md              # F5.3; ler_mercado; último sucesso
```

**Structure Decision**: monolito modular existente. O painel pertence a
`app/modulos/mercado/` (já dono de `concorrente` e `coleta_mercado`). Sem
frontend. Sem worker. Sem `alembic/`. Periodicidade via
`propriedade.repository.ler_parametro` injetável — SQL de `parametro_hotel`
não entra em `mercado.repository`.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Tela React / gráfico de variação | Comparação observável pela API | Fatia de UI |
| Disparo manual “coletar agora” | Só a varredura da F5.2 | Fora |
| Tarifa da própria casa na comparação | Gestão decide fora, no PMS/OTA | Fora (Artigo I e XV) |
| Percentual ou índice de mercado | Série datada basta para ver movimento | Fora |
| Paginação do histórico | Dezenas de pontos/ano no MVP | Fora |
| Edição da periodicidade no painel | Chave no banco; bootstrap 24 | Fatia de UI |
| Notificação à gestão quando coleta nova | Persona consulta o painel | Fora |
| Worker / visita à fonte | Série já existe; testes inserem linha | F5.2 (já entregue) |

## Complexity Tracking

> Sem violações a justificar. Uma operação nova na matriz existe porque
> reusar `ler_concorrentes` ou `ler_indicadores` misturaria recursos ou
> daria o número à recepção. Tabela omitida.
