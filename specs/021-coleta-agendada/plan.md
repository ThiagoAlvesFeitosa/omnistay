# Implementation Plan: Coleta Agendada de Mercado

**Branch**: `021-coleta-agendada` | **Date**: 2026-08-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/021-coleta-agendada/spec.md`

## Summary

Na periodicidade da propriedade, o sistema visita só as fontes **ativas**,
grava preço e nota agregada **com data**, e trata falha como registro — nunca
como silêncio nem como preço zero. O coletor obedece a diretiva publicada,
identifica-se com honestidade e não guarda dado de avaliador. Painel de
mercado fica para a F5.3.

Decisões em [research.md](./research.md): varredura `verificar_coletas_mercado`
sem APScheduler; trabalho `coletar_mercado` com unicidade só enquanto aberto;
porta `FontePublica` (falsa na suíte, HTTP + `robotparser` no adaptador);
semente `periodicidade_coleta_mercado=24`; INSERT em `coleta_mercado` já
existente; zero rota HTTP nova.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary
(já no projeto). Visita real com biblioteca padrão (`urllib.request`,
`urllib.robotparser`, `json`). **Nenhuma dependência nova.** Sem APScheduler,
sem `httpx`, sem parser HTML de terceiro, sem LLM na extração

**Storage**: PostgreSQL 16. Reuso de `coleta_mercado`, `concorrente`,
`parametro_hotel`, `trabalho`. Revisão `0020_coleta_agendada`: tipo
`coletar_mercado` no CHECK, índice único do trabalho **aberto** por
concorrente, backfill da periodicidade. **Nenhuma tabela nova**

**Testing**: pytest. Unitários sem rede (janela, diretiva, falha vs zero,
inativo, chave ausente, log, identidade da falsa). Integração com PostgreSQL
real: unicidade do aberto, série sem UPDATE, CHECKs, isolamento, varredura
não dispara em `--uma-passagem`. Adaptador HTTP só com fixture local

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em
contêiner. Worker + API já existentes. Sem frontend

**Project Type**: Serviço web + worker. Sem tela, sem rota nova

**Performance Goals**: Dezenas de fontes ativas no MVP; um claim por vez
(sequencial). Varredura horária só enfileira devidos; não abre URL

**Constraints**: Periodicidade só de `parametro_hotel`; `id_hotel` em toda
consulta via concorrente; diretiva ausente = não visita; testes sem site
alheio; trabalho de coleta sempre `concluido` (sem backoff contra a fonte);
log sem URL/HTML/avaliador

**Scale/Scope**: 1 função no agendador, 1 tipo de trabalho, 1 porta nova, 1
revisão Alembic, 0 rotas HTTP, 0 operações na matriz. Sem React, sem painel,
sem disparo manual

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas
duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Observa fonte pública; tarifa da casa não muda; PMS intocado |
| II — Na dúvida, humano vê | Sem LLM na página; sem dado → falha datada, não número inventado |
| III — Gravar antes de enviar | Trabalho na fila **antes** da visita; analogia correta para I/O de rede |
| IV — Fila como verdade | Não é alerta operacional; a série com data é o rastro; F5.3 exibe |
| V — Ausência humana visível | Não se aplica (não depende de clique de balcão). Lista vazia já é F5.1 |
| VI — Confirmação antes de tramitar | Não se aplica (não há hóspede neste fluxo) |
| VII — Não ser intrusivo | Zero mensagem ao hóspede; frequência baixa (24 h) |
| VIII — Minimização | Só preço e nota agregada; 0 dado de avaliador; log sem página |
| IX — Garantias no banco | UNIQUE do trabalho aberto; CHECKs de `coleta_mercado` já na `0001` |
| X — Portas trocáveis | Quarta porta `FontePublica` — mesmo princípio, I/O que não existia na F0 |
| XI — Complexidade exige problema | Sem lib nova, sem tabela nova, sem rota, sem APScheduler, sem tela |
| XII — Teste primeiro | Cada FR com teste que falha por ausência |
| XIII — Parâmetro não é constante | `periodicidade_coleta_mercado`; ausência falha alto |
| XIV — Multi-tenant | JOIN/`WHERE` em `concorrente.id_hotel`; séries isoladas |
| XV — Honestidade | Sem React, sem painel, sem ToS jurídico automático, sem cobertura de todas as OTAs, diretiva ausente não é licença |

**Ponto de atenção 1 — quarta porta.** O Artigo X nomeia três interfaces. A
visita a sítio de terceiro é o mesmo tipo de I/O que a mensageria e não
tinha porta na ratificação. Sem ela o domínio importaria `urllib`. Não é
serviço novo (Redis/Celery). Na implementação, registrar em
`docs/00-ESTADO-DO-PROJETO.md`.

**Ponto de atenção 2 — `robots.txt` vs spec.** O default histórico (arquivo
ausente = permite) contradiz FR-009. Esta fatia trata ausência/ilegível como
**não visita**. Registrar no estado; não silenciar.

**Ponto de atenção 3 — APScheduler.** O Artefato 5 ainda cita a lib para
`coletar_mercado`. Continua recusada (Artigo XI), no padrão F1.4–F3.8.

**Ponto de atenção 4 — conformidade do esquema.** Tipo, índice e comentário
da chave entram na revisão **e** em `docs/04-schema.sql`; `0001` congelado.

## Project Structure

### Documentation (this feature)

```text
specs/021-coleta-agendada/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── fonte-publica.md
│   ├── agendador-e-fila.md
│   ├── registro-de-coleta.md
│   └── politica-de-autorizacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
alembic/versions/
├── 0020_coleta_agendada.py
└── sql/
    └── 0020_coleta_agendada.sql

app/
├── portas/
│   └── fonte_publica.py                 # novo protocolo
├── adaptadores/
│   ├── fonte_falsa.py                   # mapa url → diretiva/resultado
│   └── fonte_http.py                    # urllib + robotparser + JSON-LD
├── fila/
│   ├── repository.py                    # tipo + allowlist + unique enqueue
│   └── service.py                       # enfileirar_coletar_mercado
├── modulos/
│   ├── propriedade/
│   │   └── service.py                   # semente periodicidade_coleta_mercado
│   └── mercado/
│       ├── service.py                   # agendar + processar coleta
│       └── repository.py                # INSERT coleta; última coleta
└── worker/
    ├── agendador.py                     # verificar_coletas_mercado
    ├── __main__.py                      # --verificar-mercado
    └── consumidor.py                    # ramo coletar_mercado

testes/
├── unitarios/
│   ├── portas/
│   │   └── test_fonte_publica.py
│   ├── adaptadores/
│   │   └── test_fonte_http.py           # fixture local, sem rede
│   ├── worker/
│   │   └── test_verificar_coletas_mercado.py
│   └── modulos/mercado/
│       ├── test_coleta.py
│       └── test_log_sem_conteudo.py     # estende
└── integracao/
    ├── test_coleta_mercado.py
    └── test_garantias_do_banco.py       # CHECK série + UNIQUE trabalho aberto

docs/
├── 04-schema.sql                        # tipo, índice, chave semeada no comentário
└── 00-ESTADO-DO-PROJETO.md              # F5.2; quarta porta; diretiva ausente
```

**Structure Decision**: monolito modular existente. Coleta pertence a
`app/modulos/mercado/` (já dono de `concorrente`). Porta nova em `app/portas/`
porque é I/O externo. Sem frontend. Sem rota. Worker existente ganha uma
flag e um ramo.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Painel com data, variação e dado velho | Série existe; gestão não a consulta por HTTP | F5.3 |
| Disparo manual “coletar agora” | Só a varredura periódica | Fora |
| Exame automático de contrato jurídico | Diretiva publicada sim; ToS em prosa continua humano | Humana |
| Tela React / edição da periodicidade no painel | Chave no banco; bootstrap 24 | Fatia de UI |
| Cobertura de todas as OTAs / contorno de bloqueio | Bloqueio vira falha datada | Fora (Artigo XV) |
| LLM lendo a página | Sem dado estruturado → falha | Fora |
| Mensagem ao hóspede ou mudança de tarifa | P5 paralelo ao fluxo da estadia | Fora |

## Complexity Tracking

> Sem violações a justificar. A quarta porta está no ponto de atenção 1:
> não é serviço novo nem biblioteca nova; é o Artigo X aplicado a um I/O
> que a constituição original ainda não tinha. Tabela omitida.
