# Implementation Plan: Confirmar Saída e Pesquisa

**Branch**: `018-confirmar-saida` | **Date**: 2026-08-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/018-confirmar-saida/spec.md`

## Summary

A recepção confirma a saída no painel: a reserva passa para `encerrado`, o
instante real fica em `checkout_em`, e nasce **uma** pendência durável de
pesquisa curta — nota 1–5, comentário opcional e pergunta de comunicações
futuras. O worker envia; falha de envio não desfaz o checkout. A resposta
não passa pelo classificador de estadia: trabalho `interpretar_pesquisa_saida`
grava avaliação (`feedback`, origem `checkout`) e consentimento
(`hospedagem`, append-only). Silêncio não consente. Revogação posterior é
INSERT no painel. Fila destaca hospedada com saída prevista vencida; encerrada
só permanece se a pesquisa precisar de leitura humana.

Decisões em [research.md](./research.md): `confirmar_fase_da_reserva` reusada;
`POST /reservas/{id}/saida`; unicidade de `enviar_pesquisa_saida` por reserva;
porta nova de extração e de envio; prazo
`horas_atribuicao_pesquisa_saida=24`; exceção estreita da F1.1 na visão;
duas operações novas só para consentimento. Sem APScheduler, sem tabela nova,
sem React, sem lista de pedidos (F4.2).

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary
(já no projeto). Portas `MensageriaGateway` (`enviar_pesquisa_saida`) e
`LLMProvider` (`interpretar_pesquisa_saida`). **Nenhuma biblioteca nova.** Sem
Redis, Celery, APScheduler ou provedor real na suíte

**Storage**: PostgreSQL 16. Reuso de `reserva.checkout_em`, `avaliacao`,
`consentimento`, `mensagem`, `trabalho`, `parametro_hotel`, trigger de
status. Revisão `0017_confirmar_saida`: dois tipos no `ck_trabalho_tipo`,
dois índices únicos parciais, colunas derivadas na `vw_fila_do_dia`, CHECK
`avaliacao` (checkout exige nota), semeadura de
`horas_atribuicao_pesquisa_saida`. **Nenhuma tabela nova**

**Testing**: pytest. Unitários sem rede: recusa de estado, texto da pesquisa
(sem extrato/conta/oferta), validação de nota, silêncio ≠ opt-in, consulta
vigente em data passada, log sem conteúdo, prazo ausente. Integração com
PostgreSQL real: transição aceita e recusada, segundo clique, índice recusa
segunda pesquisa, worker envia, resposta completa, parcial, irreconhecível,
revogação append-only, fila de vencida, isolamento entre hotéis, bootstrap
semeia 24

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em
contêiner. API e worker; sem frontend

**Project Type**: Serviço web + worker existente. Sem React

**Performance Goals**: Confirmação é um `UPDATE` por chave primária mais dois
`INSERT`. Interpretação é uma mensagem. Consulta de consentimento é índice
`(id_hospede, finalidade, momento DESC)` já existente

**Constraints**: `id_hotel` da sessão em toda consulta; log sem texto de
pesquisa, resposta, comentário ou aceite; nenhum teste chama provedor real;
checkout nunca desfeito por falha de envio; prazo só de `parametro_hotel`;
encerrada não gera `classificar_mensagem`

**Scale/Scope**: 3 rotas HTTP (saída + GET/POST consentimento), 2 operações
novas na matriz, 1 chave nova de parâmetro, 1 método na porta de mensageria,
1 método na porta de LLM, 2 tipos de trabalho, 1 revisão Alembic, delta na
visão. Sem React, sem F4.2, sem oferta de retorno, sem agendador novo

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas
duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Saída existe porque a recepção clicou. Nada detectado |
| II — Na dúvida, humano vê | Extração falha / prazo ausente → `pesquisa_saida_leitura_humana`, sem inventar |
| III — Gravar antes de enviar | Transição, mensagem pendente e trabalho na mesma TX; envio no worker |
| IV — Fila como verdade | Destaque de vencida; encerrada com leitura humana permanece no turno |
| V — Ausência humana visível | Clique esquecido = `saida_nao_confirmada`; não elimina a dependência |
| VI — Confirmação antes de tramitar | Não há chamado nesta fatia; a pesquisa não tramita serviço |
| VII — Não ser intrusivo | Uma pesquisa; zero lembrete; zero agradecimento extra; zero oferta |
| VIII — Minimização | Prenome no corpo; log com identificadores; comentário DPC |
| IX — Garantias no banco | UNIQUE da pesquisa e da avaliação; trigger; consentimento append-only |
| X — Portas trocáveis | `enviar_pesquisa_saida` + `interpretar_pesquisa_saida`; falsos na suíte |
| XI — Complexidade exige problema | Sem tabela, sem lib, sem agendador, sem bot de descadastro |
| XII — Teste primeiro | Cada FR com teste que falha por ausência |
| XIII — Parâmetro não é constante | `horas_atribuicao_pesquisa_saida`; ausência falha alto |
| XIV — Multi-tenant | `id_hotel` no UPDATE, na fila, no hóspede do consentimento |
| XV — Honestidade | Sem React; sem F4.2; sem inferir checkout por mensagem; janela 24 h semeada |

**Ponto de atenção 1 — permissão do clique já existia.** Igual à F2.2:
`confirmar_fase_da_reserva` ganha o segundo consumidor (encerrar). As duas
operações novas cobrem **só** consentimento.

**Ponto de atenção 2 — não classificar encerrada.** Webhook da F3.1 hoje
cai em `sem_reserva` depois de ficha e hospedado. Esta fatia acrescenta o
ramo 3 (pesquisa) **antes** de desistir. Testes da F3.1 que descrevem
`sem_reserva` para encerrada precisam ser atualizados quando houver pesquisa
pendente — isso é a fatia, não regressão.

**Ponto de atenção 3 — fronteira dos módulos.** `feedback` escreve
`avaliacao` origem `checkout`. `hospedagem` escreve `consentimento`.
`conversa` orquestra e não importa o inverso. Worker chama os dois. Sem
ciclo.

**Ponto de atenção 4 — allowlist na mesma revisão do CHECK.** Padrão
F3.1–F3.8. `--uma-passagem` consome os tipos novos; nenhuma flag de
agendador.

**Ponto de atenção 5 — divergência da F1.1 na visão.** F1.1 excluía todo
`encerrado` da fila. Sem exceção, a resposta irreconhecível some do turno.
A visão passa a manter `encerrado` **somente** com
`pesquisa_saida_leitura_humana`. Correção proposta em `docs/04-schema.sql`
(comentário da visão), não reabertura da F1.1. Registrado em
[research.md](./research.md) §7.

**Ponto de atenção 6 — falha de extração não copia o backoff da ficha.**
Primeira falha conclui o trabalho e vai a humano. Reagendar só mensageria
da pesquisa de ida.

**Ponto de atenção 7 — F4.2 fora.** O recado **não** lista pedidos. A
jornada cita os dois no mesmo momento do checkout; o backlog separou. Misturar
reintroduz “extrato”.

## Project Structure

### Documentation (this feature)

```text
specs/018-confirmar-saida/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-de-saida.md
│   ├── api-de-consentimento.md
│   ├── fila-e-worker.md
│   ├── portas-pesquisa.md
│   └── politica-de-autorizacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
alembic/versions/
├── 0017_confirmar_saida.py
└── sql/
    └── 0017_confirmar_saida.sql

app/
├── portas/mensageria.py · llm.py
├── adaptadores/mensageria_falsa.py · llm_falso.py
├── fila/repository.py · service.py
├── bootstrap / propriedade/service.py   # semeadura 24
├── modulos/
│   ├── acesso/politica.py               # ler/registrar_consentimento
│   ├── hospedagem/                      # confirmar_saida, consentimento, fila
│   ├── conversa/                        # texto, agendar, processadores, webhook
│   └── feedback/                        # gravar_avaliacao_checkout
worker/
└── consumidor.py                        # dois ramos novos

docs/04-schema.sql                       # CHECK, índices, visão, comentário

testes/
├── unitarios/modulos/hospedagem/
├── unitarios/modulos/conversa/
├── unitarios/modulos/feedback/
├── unitarios/modulos/acesso/
└── integracao/                          # transição, unicidade, worker, isolamento
```

**Structure Decision:** monolito modular vigente. Checkout é o segundo uso de
`confirmar_fase_da_reserva`. Consentimento nasce em `hospedagem`. Avaliação de
saída entra no `feedback` que a F3.8 já abriu. Sem processo novo.

## Complexity Tracking

> Sem violações a justificar. APScheduler continua de fora (Artigo XI). A
> exceção da visão para `encerrado` com leitura humana é o mínimo que
> reconcilia F1.1 com os Artigos II, IV e V — não é tabela, fila ou serviço
> novo.
