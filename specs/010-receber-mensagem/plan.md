# Implementation Plan: Receber Mensagem com Segurança

**Branch**: `010-receber-mensagem` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/010-receber-mensagem/spec.md`

## Summary

O mesmo `POST /webhook` da F1.3 passa a aceitar texto de reserva **hospedada**: grava o
evento (idempotente), a mensagem recebida e um trabalho `classificar_mensagem` na mesma
transação, e responde ao provedor sem classificar nem enviar. Notificação sem assinatura,
com assinatura inválida ou sem segredo configurado é recusada — falha fechada. O worker
**não consome** o tipo novo nesta fatia (allowlist), para o item permanecer `pendente` até
a F3.2. O caminho de ficha (`aguardando_cadastro` → `interpretar_ficha`) permanece.

Decisões em [research.md](./research.md): reuso do canal; falha fechada no segredo;
resolução `aguardando_cadastro` depois `hospedado`; tipo `classificar_mensagem` com
unicidade por mensagem; `reclamar_proximo` só reclama tipos já despacháveis.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary, hashlib/
hmac da biblioteca padrão (já no projeto). **Nenhuma dependência nova.** Sem Redis, Celery,
APScheduler ou fila externa

**Storage**: PostgreSQL 16. Reuso de `evento_webhook`, `mensagem`, `reserva`, `trabalho`.
Revisão `0009_receber_mensagem`: ampliar `ck_trabalho_tipo` com `classificar_mensagem`;
índice único parcial `uq_trabalho_classificar_mensagem_mensagem`. **Nenhuma tabela e
nenhuma coluna nova**

**Testing**: pytest. Unitários sem rede: resolução hospedado vs. ficha, recusa de
autenticidade (função pura / router), idempotência, log sem conteúdo, worker não reclama
o tipo novo. Integração com PostgreSQL real: webhook de estadia grava mensagem+trabalho;
assinatura ausente/inválida/segredo vazio recusam; reenvio inócuo; F1.3 intacta; passagem
do worker deixa `classificar_mensagem` `pendente`; isolamento entre hotéis

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em contêiner.
API + worker já existentes. Sem frontend

**Project Type**: Serviço web + worker. Sem React

**Performance Goals**: Webhook grava e responde em milissegundos (sem IA, sem envio).
Volume do MVP: dezenas de notificações por minuto

**Constraints**: Assinatura **antes** de qualquer INSERT; interpretação/classificação/
envio **nunca** na thread HTTP; `id_hotel` em toda resolução de reserva; conteúdo de
mensagem nunca em log nem em `evento_webhook.payload`; testes sem Meta nem LLM real;
check-in nunca inferido de mensagem; worker desta fatia não marca o tipo novo como
`falha`

**Scale/Scope**: 0 rotas HTTP novas (estende `GET`/`POST /webhook`), 0 operações novas na
matriz, 1 tipo de trabalho, 1 revisão Alembic, 1 filtro no claim da fila. Sem React, sem
classificação, sem resposta ao hóspede

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas duas passagens,
sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Mensagem de quem ainda não fez check-in **não** confirma chegada |
| II — Na dúvida, humano vê | Esta fatia não classifica; o que não é reserva hospedada/ficha vira só evento, sem resposta inventada |
| III — Gravar antes de processar | Webhook grava evento + (mensagem + trabalho se elegível) e responde; classificação é F3.2 |
| IV — Fila como verdade | O trabalho `classificar_mensagem` `pendente` é o registro; sobrevive à queda |
| V — Ausência humana visível | Não se aplica a clique de fase; omissão de check-in continua na fila do dia (F2.2) |
| VI — Confirmação antes de tramitar | Não tramita solicitação/reclamação nesta fatia; não envia confirmação ao hóspede |
| VII — Não ser intrusivo | Zero mensagem de saída |
| VIII — Minimização | Log e payload do evento sem texto; foto de documento não vira cadastro |
| IX — Garantias no banco | `UNIQUE` em `evento_webhook.id_externo`; `CHECK` do tipo; índice único do trabalho por mensagem |
| X — Portas trocáveis | Nenhuma porta nova; LLM e mensageria de saída não entram no POST |
| XI — Complexidade exige problema | Sem fila nova, sem endpoint novo, sem lib nova |
| XII — Teste primeiro | Cada FR com teste que falha por ausência |
| XIII — Parâmetro não é constante | Sem prazo novo; segredo do canal já é configuração de plataforma |
| XIV — Multi-tenant | Resolução de reserva sempre com `id_hotel` do canal |
| XV — Honestidade | Sem classificação, sem resposta, sem React, sem ordem entre mensagens |

**Ponto de atenção 1 — o worker destruiria a fila se reclamasse o tipo novo.**
`reclamar_proximo` hoje pega qualquer `pendente`. O `else` do consumidor marca
`tipo_desconhecido` como `falha`. Sem allowlist, a primeira `--uma-passagem` apagaria a
garantia da spec (FR-009). Esta fatia **filtra o claim**; não despacha `classificar_mensagem`.

**Ponto de atenção 2 — falha fechada aperta um furo da F1.3.** O router atual só verifica
assinatura quando `WHATSAPP_APP_SECRET` está preenchido. Segredo vazio aceita qualquer
corpo — o oposto de FR-005. Esta fatia corrige: sem segredo, recusa. Divergência da
execução da F1.3, não da constituição.

**Ponto de atenção 3 — `conversa` já lê `reserva`.** `resolver_reserva_aguardando_cadastro`
vive no repositório de `conversa` desde a F1.3. Acrescentar `resolver_reserva_hospedada`
no mesmo lugar. **Não** importar `hospedagem` (ciclo). Não é dono da tabela; é correlação
de entrada pelo telefone, com `id_hotel`.

**Ponto de atenção 4 — F1.3 tem prioridade no mesmo telefone.** Se existirem duas reservas
do mesmo número — uma `aguardando_cadastro` e outra `hospedado` — a mensagem segue o
caminho da ficha. Choque raro (mesmo telefone, duas estadias); documentado, não “resolvido”
com heurística extra.

## Project Structure

### Documentation (this feature)

```text
specs/010-receber-mensagem/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── webhook-e-entrada.md
│   ├── fila-e-worker.md
│   └── politica-de-autorizacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
alembic/versions/
├── 0009_receber_mensagem.py
└── sql/
    └── 0009_receber_mensagem.sql

app/
├── fila/
│   ├── repository.py          # + tipo, enfileirar, allowlist no claim
│   └── service.py             # + enfileirar_classificar_mensagem
└── modulos/
    └── conversa/
        ├── router.py          # falha fechada; status de entrega ≠ mensagem
        ├── service.py         # + ramo hospedado; F1.3 intacto
        ├── repository.py      # + resolver_reserva_hospedada
        └── schema.py          # EventoEntrada (reuso; timestamp opcional)

worker/
└── consumidor.py              # sem ramo novo; depende da allowlist do claim

testes/
├── unitarios/
│   ├── fila/
│   │   └── test_claim_nao_consome_classificar_mensagem.py
│   └── modulos/conversa/
│       ├── test_receber_mensagem.py      # estende: hospedado, ordem de resolução
│       └── test_log_sem_conteudo.py      # estende: desfechos novos
└── integracao/
    ├── test_webhook_estadia.py           # novo: happy path, recusas, idempotência
    ├── test_webhook_coleta.py            # regressão F1.3
    └── test_garantias_do_banco.py        # tipo + índice único

docs/
├── 04-schema.sql                         # CHECK + índice
├── 04-modelagem-de-dados.md              # tipo de trabalho (se a narrativa listar os tipos)
└── 00-ESTADO-DO-PROJETO.md               # na implementação: F3.1; falha fechada
```

**Structure Decision**: monolito modular existente. Toda a mudança mora em `conversa` +
`fila`. Worker não ganha branch. Sem porta nova, sem React, sem módulo `atendimento`.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Classificar intenção / sentimento / urgência | Trabalho fica `pendente` | F3.2 |
| Resposta automática a partir do catálogo | Hóspede não recebe resposta | F3.3 |
| Pedido, reclamação, consumo, pulso | Mensagem só está gravada | F3.4–F3.8 |
| Consumo do tipo pelo worker | `--uma-passagem` ignora o item | F3.2 (entra na allowlist) |
| `GET` HTTP do histórico da conversa | Teste lê `mensagem` no banco | Fatia de UI / conversa no painel |
| Destaque “possível chegada não registrada” | Reserva não hospedada não abre conversa | Mitigação da jornada §9.1, spec própria |
| Inferência de check-in por mensagem | Artigo I | Nunca nesta fatia |
| Webhook de status virando `mensagem.entregue` | Envelope de status não vira conversa | Fatia de status de entrega |
| Limite de taxa por origem | Recusa é por autenticidade, não por volume | Fora (Artigo XI) |
| Ordem estrita entre mensagens | Cada evento é independente | Fora (Artigo XV) |
| Segundo endereço de webhook | Reusa `/webhook` | — |
| Tela React | Estado via banco / suíte | Fatia de UI |
| Adaptador Meta real na suíte | Envelope assinado de teste | Operação |

## Complexity Tracking

> Sem violações a justificar. Tabela omitida.
