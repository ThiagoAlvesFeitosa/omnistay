# Implementation Plan: Pulso do Segundo Dia

**Branch**: `017-pulso-segundo-dia` | **Date**: 2026-08-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/017-pulso-segundo-dia/spec.md`

## Summary

No segundo dia civil após o check-in real, o worker dispara **uma** pergunta
sobre a experiência — se ainda houver tempo hábil (`horas_minimas_para_pulso`)
e nenhuma reclamação aberta. A pergunta é recado iniciado pelo hotel; a
unicidade mora no índice de `enviar_pulso`. Resposta: operacional (dúvida,
pedido, reclamação) corre como já existe e o pulso fecha **em silêncio**; se
nada operacional respondeu, sai o reconhecimento único (positivo = neutro) ou
a confirmação negativa (o que acontece em seguida, sem horário) **antes** do
chamado. Um recado por mensagem. Silêncio do hóspede não lembra.

Decisões em [research.md](./research.md): varredura no agendador já existente;
módulo `feedback` dono de `avaliacao`; dois tipos de trabalho; gancho no fim
dos processadores F3.3–F3.5; sem APScheduler, sem coluna na fila do dia, sem
rota HTTP.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary
(já no projeto). Portas `MensageriaGateway` (método novo `enviar_pulso` +
`enviar_texto_sessao` existente) e `LLMProvider` (classificar já existente).
**Nenhuma biblioteca nova.** Sem Redis, Celery, APScheduler ou provedor real na
suíte

**Storage**: PostgreSQL 16. Reuso de `avaliacao`, `reserva`, `mensagem`,
`trabalho`, `solicitacao`, `parametro_hotel`. Revisão `0016_pulso_segundo_dia`:
dois tipos em `ck_trabalho_tipo`, dois índices únicos parciais, semeadura de
`horas_minimas_para_pulso`. **Nenhuma tabela nova.** `vw_fila_do_dia` sem
coluna nova

**Testing**: pytest. Unitários sem rede: elegibilidade (segundo dia, mínimo,
reclamação, prazo ausente), unicidade de pergunta, textos (reconhecimento
idêntico e sem satisfação; negativa sem horário), encerrar pulso, um recado
quando há toalha/café, log sem texto. Integração com PostgreSQL real: varredura
agenda um; índice recusa o segundo; worker envia; resposta negativa abre um
chamado; operacional na janela não empilha “obrigado”; hotel B isolado;
bootstrap semeia 24

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em
contêiner. Worker existente. Sem frontend

**Project Type**: Serviço web + worker. Sem React

**Performance Goals**: varredura percorre hospedados sem pulso (dezenas por
propriedade); filtros de dia/prazo/reclamação em Python por hotel. Envio
assíncrono na fila

**Constraints**: prazos só de `parametro_hotel`; `id_hotel` em toda consulta;
conteúdo nunca em log; testes sem Meta nem LLM real; `--uma-passagem` não
varre pulso; um pulso no banco; um recado por mensagem de entrada; reserva não
muda de status; sem horário de visita no recado de pulso

**Scale/Scope**: 0 tabelas novas, 2 tipos de trabalho, 1 método na porta de
mensageria, 1 módulo `feedback` mínimo, 1 função no agendador, 1 revisão
Alembic, 0 rotas HTTP. Sem React, sem checkout, sem janela noturna

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas duas
passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Checkout previsto é data da reserva; nada lido do PMS |
| II — Na dúvida, humano vê | Polaridade irreconhecível / IA caída → fila humana, sem chamado inventado |
| III — Gravar antes de enviar | Pergunta, reconhecimento e confirmação persistem antes da porta |
| IV — Fila como verdade | Chamado de recuperação no Alert Center; pulso perdido é tolerável |
| V — Ausência humana visível | Reclamação em aberto (já visível) suprime; leitura humana **não** suprime (clarify) |
| VI — Confirmação antes de tramitar | No dono do turno, enviada **antes** do INSERT da reclamação |
| VII — Não ser intrusivo | Um pulso; zero lembrete; um recado por mensagem; sem horário de visita |
| VIII — Minimização | Prenome na pergunta; log sem texto; comentário DPC |
| IX — Garantias no banco | UNIQUE de `enviar_pulso`, de resposta por mensagem e de `avaliacao` |
| X — Portas trocáveis | `enviar_pulso` + sessão; `LLMFalso` / `MensageriaFalsa` na suíte |
| XI — Complexidade exige problema | Sem APScheduler, sem tabela, sem React, sem coluna na visão |
| XII — Teste primeiro | Cada FR com teste que falha por ausência |
| XIII — Parâmetro não é constante | `horas_minimas_para_pulso`; ausência falha alto |
| XIV — Multi-tenant | Varredura, prazo e chamado pelo hotel da reserva |
| XV — Honestidade | Sem React; sem horário nobre; perda do pulso se a janela fechar após gravar |

**Ponto de atenção 1 — não executar operacional dentro de classificar.** Com
pulso aguardando, o classificar só **enfileira** (como hoje) ou enfileira
`registrar_resposta_pulso`. Os testes da F3.2 que proíbem execução permanecem.

**Ponto de atenção 2 — gancho inerte sem pulso.** Os processadores F3.3–F3.5
chamam `encerrar_pulso_em_silencio` no fim. Sem avaliação pendente, no-op. Não
inverter recados de toalha/café/chamado.

**Ponto de atenção 3 — `atendimento` não envia.** Recado de pulso é `conversa`.
Chamado de recuperação é `abrir_reclamacao` já existente. Worker orquestra.

**Ponto de atenção 4 — caminho humano também INSERT `avaliacao`.** Senão FR-015
quebra (a próxima mensagem continua interceptável). Nota nula; sem polaridade
inventada.

**Ponto de atenção 5 — não copiar backoff de `interpretar_ficha` na polaridade.**
Falha de classificar na janela do pulso encerra a micro-pesquisa e vai a humano.
Reagendar só mensageria da pergunta / do recado dono do turno.

**Ponto de atenção 6 — módulo `feedback` sem ciclo.** Não importa `conversa`.
SQL de `avaliacao` não vaza para `hospedagem`.

**Ponto de atenção 7 — `--uma-passagem` e allowlist no mesmo passo.** Consumir
os tipos novos na revisão que o CHECK aceita. Varredura só nas flags / loop
horário.

## Project Structure

### Documentation (this feature)

```text
specs/017-pulso-segundo-dia/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── agendador-de-pulso.md
│   ├── fila-e-worker.md
│   ├── roteamento-resposta.md
│   ├── mensageria-pulso.md
│   ├── avaliacao-e-feedback.md
│   └── politica-de-autorizacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
alembic/versions/
├── 0016_pulso_segundo_dia.py
└── sql/
    └── 0016_pulso_segundo_dia.sql

app/
├── portas/mensageria.py              # + enviar_pulso
├── adaptadores/mensageria_falsa.py
├── fila/repository.py · service.py   # dois tipos + allowlist
├── bootstrap / propriedade/service.py  # semeadura 24
├── modulos/
│   ├── feedback/                     # nasce: service, repository
│   ├── conversa/                     # textos, processadores, gancho
│   ├── atendimento/                  # tem_reclamacao_aberta
│   └── hospedagem/                   # listar_hospedados_sem_pulso
worker/
├── agendador.py                      # verificar_pulsos_pendentes
├── consumidor.py
└── __main__.py                       # --verificar-pulsos; loop horário

testes/
├── unitarios/modulos/feedback/
├── unitarios/modulos/conversa/       # textos e processadores
├── unitarios/worker/                 # elegibilidade da varredura
└── integracao/                       # unicidade, worker, isolamento
```

**Structure Decision:** monolito modular vigente. `feedback` é o dono de
`avaliacao` previsto na arquitetura e ainda sem código. Worker e `conversa`
orquestram; HTTP inalterado.

## Complexity Tracking

> Sem violações a justificar. APScheduler continua de fora (Artigo XI), como
> nas F1.4 e F2.2.
