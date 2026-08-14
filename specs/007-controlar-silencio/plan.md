# Implementation Plan: Controlar o Silêncio

**Branch**: `007-controlar-silencio` | **Date**: 2026-08-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-controlar-silencio/spec.md`

## Summary

Passado o prazo da propriedade sem resposta, o sistema envia **um** lembrete (cadastro
opcional; sem ele, ficha no balcão) e para. Persistindo o silêncio até a janela de corte —
ou com a data de entrada já vencida — a reserva vai para `sem_cadastro_previo`, visível na
fila do dia, sem bloquear o check-in futuro. Resposta no meio do caminho cancela o ciclo.
Prazos vêm de `parametro_hotel`, não do código.

Decisões em [research.md](./research.md): função `verificar_cadastros_pendentes` no worker
(sem APScheduler); orquestração no agendador sem ciclo `conversa`↔`hospedagem`; trabalho
`enviar_lembrete` com unicidade por reserva; `enviar_lembrete` na porta de mensageria;
`enviada_em` no sucesso do envio como t0; bootstrap+backfill de `horas_ate_reenvio` (24) e
`horas_corte_antes_checkin` (12).

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary (já no
projeto). **Nenhuma dependência nova.** Sem APScheduler nesta fatia (Artigo XI; divergência
com Artefato 5 registrada na pesquisa)

**Storage**: PostgreSQL 16. Reuso de `reserva`, `mensagem`, `trabalho`, `parametro_hotel`.
Revisão Alembic: `ck_trabalho_tipo` + `enviar_lembrete`; índice único do lembrete por
reserva; `estado_cadastro` na visão; backfill das duas chaves de prazo

**Testing**: pytest. Unitários sem rede (regras do verificador com relógio falso, texto do
lembrete, ausência de default mágico, log sem conteúdo). Integração com PostgreSQL real:
um lembrete / nunca dois; cancelamento por resposta; marcação na corte; coleta não enviada;
fila do dia; transição `sem_cadastro_previo` → `hospedado` permitida no banco

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em contêiner.
API + worker (já existentes)

**Project Type**: Serviço web + worker. Sem frontend nesta fatia

**Performance Goals**: Verificação percorre reservas em `aguardando_cadastro` do MVP
(dezenas/centenas). Envio do lembrete é assíncrono na fila, igual à coleta

**Constraints**: Prazos só de `parametro_hotel`; `id_hotel` em toda consulta; conteúdo nunca
em log; testes sem Meta; `--uma-passagem` não dispara a verificação; um lembrete no banco
(índice + `reenvio_realizado`)

**Scale/Scope**: 1 tipo de trabalho, 1 método na porta de mensageria, 1 arquivo
`worker/agendador.py`, ampliação da fila do dia, 2 chaves de parâmetro. Sem React, sem
endpoint novo, sem clique de check-in

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas duas passagens,
sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Marcação é interna; check-in continua clique humano (F2.2) |
| II — Na dúvida, humano vê | Silêncio vira fila visível; resposta irreconhecível já é F1.3 e cancela este ciclo |
| III — Gravar antes de enviar | Mensagem + trabalho + flag na mesma TX; gateway só no worker |
| IV — Fila como verdade | `sem_cadastro_previo` na fila do dia; WhatsApp é conveniência |
| V — Ausência humana visível | Hóspede que não cadastrou fica perceptível para a recepção |
| VI — Confirmação antes de tramitar | Não se aplica (não é solicitação/reclamação) |
| VII — Não ser intrusivo | Um lembrete; depois para; corte não lembra |
| VIII — Minimização | Lembrete só com primeiro nome; log sem conteúdo |
| IX — Garantias no banco | Único `enviar_lembrete` por reserva; trigger de transição já existente |
| X — Portas trocáveis | `enviar_lembrete` na porta; falsa na suíte |
| XI — Complexidade exige problema | Sem APScheduler, sem lib nova, sem tela de parâmetros |
| XII — Teste primeiro | Cada critério de aceite com teste que falha por ausência |
| XIII — Parâmetro não é constante | `horas_ate_reenvio` e `horas_corte_antes_checkin`; ausência falha alto |
| XIV — Multi-tenant | Listagem, prazos e `UPDATE` sempre com `id_hotel` |
| XV — Honestidade | Sem React; sem check-in; sem APScheduler; agendador que não rode degrada para o balcão |

**Ponto de atenção 1 — APScheduler.** O Artefato 5 nomeia a lib; o Artigo XI vence. O
arquivo `worker/agendador.py` nasce; a dependência não. Registrar no estado do projeto na
implementação.

**Ponto de atenção 2 — fronteira de módulos.** O agendador (worker) lê `hospedagem` +
`conversa` + `propriedade`. `conversa` não importa `hospedagem`.

**Ponto de atenção 3 — `enviada_em`.** Passa a significar o instante do sucesso do envio,
não só o INSERT da pendência. Necessário para o t0 do silêncio.

## Project Structure

### Documentation (this feature)

```text
specs/007-controlar-silencio/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── agendador-e-prazos.md
│   ├── mensageria-e-fila.md
│   ├── api-de-hospedagem.md
│   └── politica-de-autorizacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
app/
├── portas/
│   └── mensageria.py              # + enviar_lembrete
├── adaptadores/
│   ├── mensageria_falsa.py        # registra tipo lembrete
│   └── mensageria_whatsapp.py     # método no contrato; suíte não instancia
├── fila/
│   ├── repository.py              # + tipo enviar_lembrete + unicidade
│   └── service.py                 # + enfileirar_enviar_lembrete
├── comum/
│   └── relogio.py                 # reusado (agora injetável)
└── modulos/
    ├── conversa/
    │   ├── texto_lembrete.py      # montagem pura (opcionalidade + balcão)
    │   ├── service.py             # agendar_lembrete; predicados coleta/resposta; envio
    │   └── repository.py          # instante coleta enviada; existe recebida; enviada_em
    ├── hospedagem/
    │   ├── service.py             # listar aguardando; marcar reenvio; marcar sem cadastro
    │   ├── repository.py          # UPDATE reenvio_realizado / status
    │   └── schema.py              # estado_cadastro admite sem_cadastro_previo
    ├── propriedade/
    │   └── service.py             # defaults 24 e 12 no bootstrap
    └── acesso/
        └── politica.py            # sem operação nova

worker/
├── consumidor.py                  # branch enviar_lembrete
├── agendador.py                   # verificar_cadastros_pendentes
└── __main__.py                    # --verificar-cadastros; contínuo chama o agendador

alembic/versions/
├── 0007_controlar_silencio.py
└── sql/
    └── 0007_controlar_silencio.sql

testes/
├── unitarios/
│   ├── adaptadores/
│   │   └── test_mensageria_falsa.py   # se ainda não cobre lembrete
│   └── modulos/
│       ├── conversa/
│       │   ├── test_texto_lembrete.py
│       │   └── test_log_sem_conteudo.py  # estende
│       ├── hospedagem/
│       │   └── test_marcar_sem_cadastro.py
│       └── propriedade/
│           └── test_prazos_de_silencio.py
│   └── worker/  ou testes/unitarios/agendador/
│       └── test_verificar_cadastros.py
└── integracao/
    ├── test_controlar_silencio.py     # lembrete único, cancelamento, corte, coleta falha
    └── test_fila_do_dia.py            # estado_cadastro sem_cadastro_previo

docs/
├── 04-schema.sql                      # CHECK trabalho + visão + comentário enviada_em
└── 00-ESTADO-DO-PROJETO.md            # F1.4 em andamento; APScheduler adiado de novo
```

**Structure Decision**: monolito modular existente. Agendador no processo worker, como o
Artefato 5 já desenhava o *lugar* — sem a biblioteca. Sem frontend.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Clique de check-in / boas-vindas | Transição permitida no banco; sem botão | F2.2 |
| APScheduler | Verificação por função + flag CLI | Quando houver várias tarefas de calendário |
| Tela de `parametro_hotel` | SQL / bootstrap | Lacuna já registrada |
| Lista numerada no lembrete | Texto curto | Fora (não ser intrusivo) |
| Tela React | Estado via API | Fatia de UI |
| Adaptador WhatsApp na suíte | Porta falsa | Operação / sandbox |

## Complexity Tracking

> Sem violações a justificar. Tabela omitida.
