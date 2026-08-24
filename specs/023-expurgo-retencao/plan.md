# Implementation Plan: Expurgo por Retenção

**Branch**: `023-expurgo-retencao` | **Date**: 2026-08-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/023-expurgo-retencao/spec.md`

## Summary

Passagem automática aplica a política já declarada: conteúdo livre da
estadia é **substituído** doze meses após a saída confirmada (a linha
fica, o volume permanece); a ficha cadastral é **apagada** cinco anos
após a última saída vinculada. Cada hotel ganha um comprovante do dia —
quantidades por tipo, sem o texto tratado — consultável só pela gestão.

Decisões em [research.md](./research.md): `verificar_retencao` no
agendador existente, sem APScheduler e sem fila; SQL em cada módulo dono;
tabela `execucao_retencao` (uma por hotel por dia civil UTC); marcas
`[anonimizado]` / `{"anonimizado": true}`; prazos semeados
`meses_retencao_conteudo_livre=12` e `anos_retencao_ficha=5`;
`GET /retencao` com operação `ler_retencao`; revisão `0021`. Sem botão
de disparo, sem mensagem ao hóspede, sem módulo novo.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic,
psycopg2-binary (já no projeto). Aritmética de prazo em
`make_interval` do PostgreSQL e `calendar` da biblioteca padrão.
**Nenhuma dependência nova.** Sem APScheduler, sem dateutil, sem fila
nova para o expurgo

**Storage**: PostgreSQL 16. Tabela nova `execucao_retencao`. Reuso de
`mensagem`, `evento_webhook`, `solicitacao`, `avaliacao`, `hospede`,
`consentimento`, `reserva`, `reserva_hospede`, `parametro_hotel`.
Revisão `0021_expurgo_retencao`: tabela + UNIQUE do dia, semente das
duas chaves, comentário de `parametro_hotel`. `0001` permanece congelado

**Testing**: pytest. Unitários com relógio injetável e portas/repositórios
falsos onde já é o padrão. Integração com PostgreSQL real: UPDATE que
mantém a linha, DELETE da ficha, UNIQUE do comprovante no dia, isolamento
entre hotéis, `--uma-passagem` não dispara a varredura

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL
em contêiner. Worker + API já existentes. Sem frontend

**Project Type**: Serviço web + worker. Uma rota GET nova. Sem tela

**Performance Goals**: Um hotel no MVP; varredura diária efetiva (a
cadência horária só pergunta “já rodou hoje?”). UPDATEs em conjunto por
hotel, sem carregar o texto para a aplicação

**Constraints**: Prazos só de `parametro_hotel`; ausência falha alto;
relógio = `checkout_em`, nunca data prevista; `id_hotel` em toda consulta
via reserva; log e comprovante sem conteúdo, nome, telefone ou documento;
sem disparo HTTP de expurgo

**Scale/Scope**: 1 função no agendador, 1 tabela, 2 chaves, 1 operação na
matriz, 1 GET, 1 revisão Alembic. Sem React, sem porta nova, sem tipo
novo na fila `trabalho`

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Relógio é o clique de saída já gravado. Data prevista e PMS intocados |
| II — Na dúvida, humano vê | Não classifica. Conteúdo vencido some; não se inventa texto no lugar |
| III — Gravar antes de enviar | Não envia mensagem. Trabalho é só banco, na própria passagem |
| IV — Fila como verdade | O comprovante durável é o rastro; não há notificação de “expurgo ok” |
| V — Ausência humana visível | Sem clique de saída o relógio não anda. A fila de saída atrasada já existe (F4.1); esta fatia não inventa a partida |
| VI — Confirmação antes de tramitar | Não se aplica (não há hóspede neste fluxo) |
| VII — Não ser intrusivo | Zero mensagem ao hóspede |
| VIII — Minimização | É a fatia: DPC anonimizado, DP/DPS apagados no prazo; log sem texto |
| IX — Garantias no banco | UNIQUE `(id_hotel, dia UTC)` do comprovante; CHECKs de quantidade ≥ 0 |
| X — Portas trocáveis | Sem porta nova: não há I/O externo |
| XI — Complexidade exige problema | Sem lib, sem APScheduler, sem módulo, sem tipo de fila. Uma tabela porque log efêmero não demonstra cumprimento |
| XII — Teste primeiro | Cada FR com teste que falha por ausência |
| XIII — Parâmetro não é constante | `meses_retencao_conteudo_livre`, `anos_retencao_ficha`; ausência não usa default |
| XIV — Multi-tenant | Filtro `reserva.id_hotel` / `execucao_retencao.id_hotel`; ficha só cai se **todas** as reservas vinculadas (qualquer hotel) já venceram |
| XV — Honestidade | Sem React, sem pedido avulso de esquecimento, sem expurgo de quem ainda não teve saída confirmada |

**Ponto de atenção 1 — cadência diária na passagem horária.** O Artefato 5
cita APScheduler e “expurgo diário”. Continua recusado (Artigo XI), no
padrão F1.4–F5.2. A passagem horária chama a função; o UNIQUE do dia e o
teste “já rodou hoje?” fazem a efetividade ser uma vez por dia civil UTC.

**Ponto de atenção 2 — `evento_webhook` sem FK de reserva.** O vínculo é
`evento_webhook.id_externo = mensagem.id_externo`. Payload órfão (sem
mensagem) não entra nesta fatia — limitação honesta, não silêncio.

**Ponto de atenção 3 — conformidade do esquema.** Tabela, índice, chaves e
comentário entram na revisão **e** em `docs/04-schema.sql`; `0001`
congelado.

## Project Structure

### Documentation (this feature)

```text
specs/023-expurgo-retencao/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── agendador-e-retencao.md
│   ├── anonimizacao-e-exclusao.md
│   ├── api-de-comprovante.md
│   └── politica-de-autorizacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
alembic/versions/
├── 0021_expurgo_retencao.py
└── sql/
    └── 0021_expurgo_retencao.sql

app/
├── comum/
│   └── retencao.py                      # marcas + vencimento civil (calendar)
├── modulos/
│   ├── acesso/
│   │   └── politica.py                  # ler_retencao
│   ├── propriedade/
│   │   ├── service.py                   # semente + registrar/listar comprovante
│   │   ├── repository.py                # execucao_retencao
│   │   ├── router.py                    # GET /retencao
│   │   └── schema.py                    # resposta do comprovante
│   ├── conversa/
│   │   ├── service.py                   # anonimizar mensagens + payloads
│   │   └── repository.py
│   ├── atendimento/
│   │   ├── service.py                   # anonimizar descricao
│   │   └── repository.py
│   ├── feedback/
│   │   ├── service.py                   # anonimizar comentario
│   │   └── repository.py
│   └── hospedagem/
│       ├── service.py                   # apagar ficha + consentimento + telefone
│       └── repository.py
└── worker/
    ├── agendador.py                     # verificar_retencao
    └── __main__.py                      # --verificar-retencao; loop horário

testes/
├── unitarios/
│   ├── comum/
│   │   └── test_retencao.py             # marcas e vencimento civil
│   ├── worker/
│   │   └── test_verificar_retencao.py
│   └── modulos/
│       ├── acesso/test_politica.py      # estende
│       ├── propriedade/
│       ├── conversa/test_log_sem_conteudo.py  # estende
│       ├── atendimento/
│       ├── feedback/
│       └── hospedagem/
└── integracao/
    ├── test_retencao.py
    ├── test_bootstrap.py                # estende chaves
    └── test_inventario.py               # tabela nova no documento

docs/
├── 04-schema.sql                        # execucao_retencao + chaves no comentário
└── 00-ESTADO-DO-PROJETO.md              # F6.1
```

**Structure Decision**: monolito modular existente. Orquestração no
agendador (lição da F0.3: ciclo entre módulos não se resolve com import
local). Cada módulo só escreve nas tabelas que já governa.
`execucao_retencao` fica em `propriedade` (comprovante por hotel, não por
estadia). Sem frontend. Sem porta. Worker existente ganha uma flag.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Pedido avulso de esquecimento / portabilidade | Só o calendário automático | Fora (spec FR-021) |
| Botão “expurgar agora” | Só a passagem periódica | Fora |
| Tela React / edição dos prazos no painel | Chaves no banco; bootstrap 12 e 5 | Fatia de UI |
| Expurgo de funcionário, sessão ou mercado | Fora da política do hóspede | Fora |
| Payload de webhook sem mensagem correspondente | Não é da estadia identificável | Fora (Artigo XV) |
| Mensagem ao hóspede ou confirmação de fase | P6 transversal, sem canal | Fora |
| Inventar `checkout_em` a partir da data prevista | Relógio parado até o clique | Já visível na F4.1 |

## Complexity Tracking

> Sem violações a justificar. A tabela nova é o comprovante que a spec
> exige durável e consultável — log de aplicação não demonstra cumprimento.
> Tabela omitida.
