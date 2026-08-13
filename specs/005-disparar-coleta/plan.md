# Implementation Plan: Disparar Coleta de Dados

**Branch**: `005-disparar-coleta` | **Date**: 2026-08-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-disparar-coleta/spec.md`

## Summary

Ao cadastrar a reserva, o sistema grava na mesma transação uma mensagem de coleta
(`status_envio = pendente`) e um trabalho `enviar_coleta` na fila PostgreSQL. A resposta HTTP
não chama o provedor. Um worker consome a fila via `MensageriaGateway` (falsa nos testes),
atualiza o status de envio e torna esse status visível em `GET /fila-do-dia`. Falha de envio
nunca desfaz a reserva; retry não duplica o pedido ao hóspede.

Onze decisões técnicas sustentam o desenho ([research.md](./research.md)): independência
estrutural; tabela `trabalho`; uma mensagem lógica por coleta; porta + falsa; módulo
`conversa`; texto/LGPD/contato por parâmetro; coluna na visão; tentativas/backoff/reclaim;
recorte sem React/webhook/`entregue`; correção da lacuna DDL; fora de escopo F1.3/F1.4.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary, httpx (já
no `pyproject.toml`). **Nenhuma dependência nova.** Porta falsa para a suíte; adaptador
WhatsApp Cloud pode reutilizar `httpx` no ambiente real — a suíte não o instancia (Artigo XI)

**Storage**: PostgreSQL 16. Nova tabela `trabalho`. Reuso de `mensagem`. Revisão Alembic para
DDL + `vw_fila_do_dia` com `status_envio_coleta`. Parâmetros novos em `parametro_hotel`

**Testing**: pytest. Unitários sem rede (texto da coleta, conversa, fila, worker + gateway
falso). Integração com PostgreSQL real: `POST /reservas` cria pendências; uma passagem do
consumidor; status na fila; falha não apaga reserva; unicidade da coleta

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em contêiner.
Processo extra: `worker` (além da API)

**Project Type**: Serviço web + worker. Sem frontend nesta fatia

**Performance Goals**: Enfileirar é custo de dois inserts na mesma transação curta da F1.1.
Worker processa dezenas de trabalhos por minuto — suficiente para o volume do MVP

**Constraints**: Envio nunca na requisição HTTP; `id_hotel` em `trabalho` e em toda consulta;
conteúdo de mensagem nunca em log; testes sem API Meta; template Utility na integração real;
máximo uma coleta lógica por reserva

**Scale/Scope**: 1 tabela nova, 1 módulo novo (`conversa`), pastas `portas` / `adaptadores` /
`fila` / `worker`, 1 revisão de visão, 2 parâmetros, acréscimo ao contrato da fila do dia.
Sem rota HTTP nova

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas duas passagens,
sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Disparo é interno ao OmniStay; recepção continua ponte humana |
| III — Gravar antes de enviar | Reserva + mensagem + trabalho no mesmo `COMMIT`; envio só no worker |
| IV — Fila como verdade | Status na fila do dia / `mensagem` recupera alerta perdido; notificação WhatsApp é conveniência |
| V — Ausência humana visível | Falha de entrega fica perceptível em `status_envio_coleta` |
| VII — Não ser intrusivo | Só a coleta inicial; lembrete é F1.4 |
| VIII — Minimização | Só primeiro nome como PII no corpo; log sem conteúdo |
| IX — Garantias no banco | `CHECK` de status/tipo; único parcial de coleta por reserva; `status_envio` obrigatório em saída |
| X — Portas trocáveis | `MensageriaGateway` + falsa; domínio sem adaptador concreto |
| XI — Complexidade exige problema | Fila no PG (já decidida); sem Redis/Celery; módulo `conversa` mínimo porque a tabela `mensagem` tem dono declarado |
| XII — Teste primeiro | Cada FR com teste que falha por ausência; ciclo nos unitários |
| XIII — Parâmetro não é constante | `contato_responsavel_dados`, `tentativas_max_envio_mensagem` |
| XIV — Multi-tenant | `trabalho.id_hotel`; visão e claim sempre filtráveis por hotel |
| XV — Honestidade | Sem `entregue` via webhook, sem React, sem interpretar resposta — tabela de ausências |

**Ponto de atenção 1 — lacuna DDL da fila.** O Artefato 5 descreveu a fila e o `04-schema.sql`
não a tinha. Esta fatia fecha o buraco; documento e migração saem juntos (padrão F0.2).

**Ponto de atenção 2 — adaptador Meta.** `httpx` já está no projeto. A falsa é suficiente
para o critério de pronto da spec (SC-008). Adaptador WhatsApp Cloud é desejável para o
sandbox e pode entrar na mesma entrega sem dependência nova; a suíte não o exercita.

**Ponto de atenção 3 — ciclo entre módulos.** `hospedagem` chama `conversa` (agendar);
`conversa` não chama `hospedagem`. Worker orquestra os dois + porta. Sem import local para
quebrar ciclo (lição F0.3).

## Project Structure

### Documentation (this feature)

```text
specs/005-disparar-coleta/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-de-hospedagem.md
│   ├── politica-de-autorizacao.md
│   └── mensageria-e-fila.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
app/
├── portas/
│   └── mensageria.py                 # Protocol MensageriaGateway
├── adaptadores/
│   ├── mensageria_falsa.py
│   └── mensageria_whatsapp.py        # Opcional / ambiente real
├── fila/
│   ├── __init__.py
│   ├── repository.py                 # enfileirar, claim, concluir, reclaim
│   └── service.py                    # Orquestra status do trabalho (sem texto)
├── comum/
│   └── telefone.py                   # Já existe; reusado
└── modulos/
    ├── hospedagem/
    │   ├── service.py                # Após criar reserva, agenda coleta na mesma TX
    │   ├── schema.py                 # ItemFilaDoDia + status_envio_coleta
    │   └── repository.py             # Lê visão ampliada
    ├── conversa/
    │   ├── __init__.py
    │   ├── service.py                # Montar texto, gravar mensagem, espelhar status
    │   ├── repository.py             # INSERT/UPDATE mensagem
    │   └── texto_coleta.py           # Função pura do corpo (unitário)
    └── propriedade/
        └── service.py                # Bootstrap: novos parametro_hotel

worker/
├── __init__.py
├── __main__.py                       # python -m worker
└── consumidor.py                     # Uma passagem ou loop

alembic/versions/
├── 0005_trabalho_e_coleta.py         # (número efetivo = próximo livre)
└── sql/
    └── 0005_trabalho_e_coleta.sql

testes/
├── unitarios/
│   ├── portas/ ou adaptadores/
│   ├── fila/
│   ├── comum/                        # se extrair primeiro_nome
│   └── modulos/
│       ├── conversa/
│       │   ├── test_texto_coleta.py
│       │   └── test_service_coleta.py
│       └── hospedagem/
│           └── test_service_de_reserva.py  # Acrescenta expectativa de agendamento
└── integracao/
    ├── test_disparo_coleta.py        # POST cria mensagem+trabalho
    ├── test_worker_coleta.py         # Sucesso / falha / retry sem duplicar
    └── test_fila_do_dia.py           # status_envio_coleta visível

docs/
├── 04-schema.sql                     # Tabela trabalho + visão + comentários
└── 04-modelagem-de-dados.md          # Fila de trabalho documentada
```

**Structure Decision**: monolito modular existente + pastas já previstas em `AGENTS.md`
(`portas`, `adaptadores`, `fila`, `worker`) que ainda estavam vazias. `conversa` nasce no
tamanho mínimo para governar `mensagem`. Sem frontend.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Interpretação da resposta / ficha completa | Hóspede pode responder; sistema ainda não consolida | F1.3 |
| Lembrete por silêncio | Um único disparo; sem segunda mensagem automática | F1.4 |
| Webhook de status → `entregue` | Painel vê `enviada` ou `falha`, não confirmação de leitura/entrega da Meta | Fatia de webhook / conversa entrada |
| Tela React | Status só via API / SQL | Fatia de UI |
| Aprovação do template na Meta como CI | Sandbox manual; suíte com porta falsa | Operação / implantação |
| APScheduler completo | Só consumidor da fila | F1.4+ (tarefas periódicas) |
| Endpoint HTTP de histórico de mensagens | Histórico existe no banco; leitura dedicada adiada | Painel / F1.3 |

## Complexity Tracking

> Sem violações a justificar. Tabela omitida.
