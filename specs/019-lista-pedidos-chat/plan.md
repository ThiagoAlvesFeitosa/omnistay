# Implementation Plan: Lista de Pedidos Feitos pelo Chat

**Branch**: `019-lista-pedidos-chat` | **Date**: 2026-08-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/019-lista-pedidos-chat/spec.md`

## Summary

No mesmo clique de saída da F4.1, se a reserva tiver consumo faturável
**cobrável** (pendente ou lançado), nasce **uma** pendência durável de
mensagem distinta da pesquisa: a lista de **pedidos feitos pelo chat**, com
descrição e valor praticado. Sem item cobrável, silêncio — a pesquisa segue.
O worker envia; falha não desfaz o checkout nem duplica a lista. Recepção e
gestão consultam o mesmo recorte no painel, mesmo com envio falho. Staff não
vê. Palavras "extrato" e "conta" são recusadas no texto.

Decisões em [research.md](./research.md): `confirmar_saida` orquestra
`atendimento.listar` + `conversa.agendar`; tipo `enviar_lista_pedidos_chat`
único por reserva; porta `enviar_lista_pedidos_chat`; operação nova
`ler_pedidos_feitos_pelo_chat`; GET em `/reservas/{id}/pedidos-feitos-pelo-chat`;
snapshot do texto na `mensagem` no enfileiramento. Sem LLM, sem webhook
novo, sem React, sem parâmetro novo.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary
(já no projeto). Porta `MensageriaGateway` (`enviar_lista_pedidos_chat`).
**Nenhuma biblioteca nova.** Sem Redis, Celery, APScheduler, LLM extra ou
provedor real na suíte

**Storage**: PostgreSQL 16. Reuso de `consumo`, `solicitacao`, `mensagem`,
`trabalho`, `reserva`. Revisão `0018_lista_pedidos_chat`: um tipo no
`ck_trabalho_tipo`, um índice único parcial por reserva. **Nenhuma tabela
nova.** Nenhum `parametro_hotel` novo

**Testing**: pytest. Unitários sem rede: recorte cobrável (exclui serviço e
dispensado), valor histórico após reajuste, texto sem extrato/conta e com
rótulo certo, lista vazia não enfileira, log sem conteúdo/valor, isolamento.
Integração com PostgreSQL real: clique agenda pesquisa **e** lista quando há
item; clique sem item só pesquisa; unicidade do trabalho; worker envia;
GET do painel; 403 staff; 404 outro hotel; retry não duplica

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em
contêiner. API e worker; sem frontend

**Project Type**: Serviço web + worker existente. Sem React

**Performance Goals**: Consulta da lista é um `SELECT` por reserva e hotel.
Confirmação acrescenta, no máximo, um `INSERT` de mensagem + um `INSERT` de
trabalho além da pesquisa já existente

**Constraints**: `id_hotel` da sessão em toda consulta; log sem texto da
lista, sem descrição de item e sem valor por extenso; nenhum teste chama
provedor real; checkout nunca desfeito por falha de envio; `conversa` não
importa `atendimento` (atendimento já importa conversa)

**Scale/Scope**: delta em `POST /reservas/{id}/saida`, 1 GET novo, 1 operação
nova na matriz, 1 método na porta de mensageria, 1 tipo de trabalho, 1
revisão Alembic. Sem LLM, sem webhook, sem agendador, sem React

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas
duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Lista só o que o chat gerou; o texto admite o alcance parcial |
| II — Na dúvida, humano vê | Lista não é pergunta; contestação cai no caminho já existente da F4.1 |
| III — Gravar antes de enviar | Mensagem pendente + trabalho na mesma TX do checkout; envio no worker |
| IV — Fila como verdade | GET do painel funciona com envio falho ou ainda pendente |
| V — Ausência humana visível | Sem segundo clique; a lista nasce no checkout que já existia |
| VI — Confirmação antes de tramitar | Não há chamado novo; o hóspede já confirmou cada pedido na F3.7 |
| VII — Não ser intrusivo | Uma lista; zero se vazia; zero lembrete; zero “está correto?”; zero correção após lançar/dispensar |
| VIII — Minimização | Prenome no corpo; `descricao_item` (não o texto DPC da solicitação); log sem valor |
| IX — Garantias no banco | UNIQUE da lista por reserva; CHECK do tipo na mesma revisão da allowlist |
| X — Portas trocáveis | `enviar_lista_pedidos_chat`; falso na suíte |
| XI — Complexidade exige problema | Sem tabela, sem lib, sem LLM, sem agendador, sem intenção nova |
| XII — Teste primeiro | Cada FR com teste que falha por ausência |
| XIII — Parâmetro não é constante | Nenhum prazo novo; não se inventa janela |
| XIV — Multi-tenant | `id_hotel` no SELECT, no UPDATE/INSERT da fila e no GET |
| XV — Honestidade | Texto admite “só o chat”; sem React; sem fatura da casa |

**Ponto de atenção 1 — orquestração sem ciclo.** `atendimento` já importa
`conversa`. `conversa` **não** importa `atendimento`. `hospedagem.confirmar_saida`
lista os cobráveis via `atendimento` e, se houver item, agenda via `conversa`.
Worker só chama `conversa`.

**Ponto de atenção 2 — allowlist na mesma revisão do CHECK.** Padrão
F3.1–F4.1. `--uma-passagem` consome o tipo novo; nenhuma flag de agendador.

**Ponto de atenção 3 — testes da F4.1.** `POST /saida` sem consumo continua
com 1 trabalho (pesquisa) e ganha `lista=ausente`. Reserva **com** consumo
cobrável passa a ter 2 trabalhos. Isso é a fatia, não regressão — o mesmo
padrão da F3.2 invertendo a allowlist da F3.1.

**Ponto de atenção 4 — não reusar `ler_solicitacao_atribuida`.** Staff vê
pendências de lançamento; a spec recusa operação na lista de checkout.
Operação nova `ler_pedidos_feitos_pelo_chat` (recepção + gestão).

**Ponto de atenção 5 — snapshot na mensagem.** O corpo é gravado no
enfileiramento. Lançar/dispensar depois não reescreve nem reenvia (Artigo
VII). O GET do painel é consulta **ao vivo** do recorte cobrável.

## Project Structure

### Documentation (this feature)

```text
specs/019-lista-pedidos-chat/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-de-saida.md
│   ├── api-de-pedidos.md
│   ├── fila-e-worker.md
│   ├── portas-lista.md
│   └── politica-de-autorizacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
alembic/versions/
├── 0018_lista_pedidos_chat.py
└── sql/
    └── 0018_lista_pedidos_chat.sql

app/
├── portas/mensageria.py
├── adaptadores/mensageria_falsa.py · mensageria_whatsapp.py
├── fila/repository.py · service.py
├── modulos/
│   ├── acesso/politica.py               # ler_pedidos_feitos_pelo_chat
│   ├── atendimento/                     # listar cobráveis da reserva
│   ├── hospedagem/                      # confirmar_saida orquestra; GET
│   └── conversa/                        # texto, agendar, processar envio
worker/
└── consumidor.py                        # um ramo novo

docs/04-schema.sql                       # CHECK + índice único

testes/
├── unitarios/modulos/atendimento/
├── unitarios/modulos/hospedagem/
├── unitarios/modulos/conversa/
├── unitarios/modulos/acesso/
├── unitarios/fila/
└── integracao/                          # clique, unicidade, worker, GET, isolamento
```

**Structure Decision:** monolito modular vigente. A lista não ganha módulo.
`atendimento` lê `consumo`; `conversa` envia; `hospedagem` orquestra no
checkout que já era dela. Sem processo novo.

## Complexity Tracking

> Sem violações a justificar. A operação nova na matriz existe porque
> reusar `ler_solicitacao_atribuida` daria a lista ao staff, contra a spec.
> Não é biblioteca, fila externa nem serviço novo.
