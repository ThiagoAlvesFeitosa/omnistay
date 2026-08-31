# Implementation Plan: Fila do dia e cadastro de reserva

**Branch**: `029-fila-dia-reserva` | **Date**: 2026-08-31 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/029-fila-dia-reserva/spec.md`

## Summary

A recepção passa a **ver e operar o turno** na casa que a F8.1 só
nomeava: lista de hoje / hospedados / entrada vencida, cadastro com
três campos e confirmação de chegada num botão rotulado da linha.
Gestão e staff continuam recusados.

Decisões em [research.md](./research.md): reuso de `GET /fila-do-dia`,
`POST /reservas` e `POST /reservas/{id}/chegada`; resumo do turno
calculado na tela (partição das linhas, sem rota nova); elegibilidade
do botão pelo `status` já devolvido; depois de gravar, um `GET` da
fila — não recarregar a página. **Sem** tabela, **sem** operação nova
na matriz, **sem** Playwright, **sem** lib de estado.

## Technical Context

**Language/Version**: Python 3.11+ (intocado nas regras de hospedagem);
TypeScript no `frontend/` já existente

**Primary Dependencies**: FastAPI (rotas de reserva/fila/chegada
intactas). Frontend: Vite + React 19 + React Router + Tailwind +
shadcn copiado (campo, botão, rótulo). Sem Redux, sem React Query, sem
Playwright

**Storage**: PostgreSQL 16. **Nenhuma tabela nova.** `vw_fila_do_dia`
e `reserva` como estão (`0001`…`0023` intactos). Sem revisão Alembic

**Testing**: pytest — regressão das rotas já verdes (fila, reserva,
chegada, perfis). Vitest + Testing Library — lista, resumo em
partição, cadastro, botão rotulado vs clique no restante da linha,
falha de leitura ≠ fila vazia. `fetch` falso. **Nenhum** teste abre
navegador nem chama rede externa

**Target Platform**: Servidor Linux; desenvolvimento Windows. SPA em
`/app`; proxy Vite já aponta `/fila-do-dia` e `/reservas`. Recepção no
computador do balcão

**Project Type**: Serviço web + worker (intocado) + telas React no
`frontend/` existente, no lugar de `TelaNomeada` em `fila` e `reserva`

**Performance Goals**: um hotel no MVP; um `GET /fila-do-dia` ao abrir
a casa e outro após cadastro/chegada aceitos. Sem meta de throughput.
Identificar o turno < 30 s; cadastro válido < 1 min (SC-001, SC-003)

**Constraints**: tela nunca lê o token; nome/telefone fora do log e do
`console`; `id_hotel` só na API; sem PMS; sem e-mail no cadastro; sem
clique de saída; botão de chegada só em estado que a máquina admite;
clicar nome/telefone não confirma; F7.4 não filtra

**Scale/Scope**: 0 tabelas, 0 operações novas na matriz, 3 rotas
reusadas, 2 destinos deixam de ser só título (`fila`, `reserva`), 1
função pura de partição do resumo, 1 função pura de elegibilidade do
botão. Worker intocado

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Chegada continua sendo clique da recepção. A tela não infere entrada pelo calendário nem pelo PMS |
| II — Na dúvida, humano vê | Intocado. A fila não classifica mensagem |
| III — Gravar antes de enviar | Cadastro reusa `POST /reservas`: a reserva grava antes da coleta (já F1.2). A tela não envia mensagem |
| IV — Fila como verdade | Sem push. Recarregar e “tentar de novo” consultam `GET /fila-do-dia` |
| V — Ausência humana visível | **É esta fatia.** Chegada vencida, recado não enviado e ficha parcial com sinais distintos; resumo em partição para o atraso não se misturar com o movimento do dia |
| VI — Confirmação antes de tramitar | Intocado (hóspede). Confirmar chegada no balcão é um clique no botão, sem segundo “tem certeza?” — decisão da spec |
| VII — Não ser intrusivo | Sem recado proativo novo |
| VIII — Minimização | Só recepção vê a lista nominada. Staff e gestão recusados na casca e na API. Log sem nome, telefone, senha, conteúdo |
| IX — Garantias no banco | Transição de chegada e UNIQUE de boas-vindas permanecem no banco. A tela não inventa atalho `aguardando_cadastro → hospedado` |
| X — Portas trocáveis | Intocado. A tela não instancia LLM nem mensageria |
| XI — Complexidade exige problema | Sem rota nova, sem lib de estado, sem Playwright. Dois componentes de tela e funções puras (resumo, botão, telefone) são o problema presente |
| XII — Teste primeiro | Cada FR com teste que falha por ausência (Vitest na tela; pytest só se o HTTP mudar — e não muda) |
| XIII — Parâmetro não é constante | Prazos de boas-vindas e silêncio continuam em `parametro_hotel`; a tela não os lê |
| XIV — Multi-tenant | `id_hotel` da sessão; a tela não pede hotel. Reserva alheia continua `404` na chegada |
| XV — Honestidade | Sem ficha, sem checkout, sem editar recado. Falha de leitura não se disfarça de turno vazio. Clique em nome/telefone não confirma |

**Ponto de atenção 1 — resumo ≠ `GET /indicadores/chegadas-do-dia`.**
A contagem da F1.1 inclui quem tem entrada *hoje*, já hospedado ou
não, e **não** isola entrada vencida. Usá-la no topo da fila quebraria
a partição da spec. O resumo deriva só de `itens`.

**Ponto de atenção 2 — “hoje” é o do banco.** A visão já corta futura
com `CURRENT_DATE`. A tela **não** refiltra. Depois de um cadastro,
um `GET` decide se a reserva entrou na lista ou se a mensagem é
“registrada, entra no dia da entrada” — evita calendário do navegador
divergir do servidor.

**Ponto de atenção 3 — testes da casca.** `Casca.test.tsx` abre
`/app/fila` e hoje a API operacional 404 no `fetch` falso. Ao nascer
`TelaFila`, o mock precisa responder `GET /fila-do-dia` (`200` com
`itens: []` no mínimo). Senão a casca “regressa” com estado de falha.

**Ponto de atenção 4 — botão, não a linha.** A spec fecha clique no
rótulo. `<tr onClick>` (ou linha com `role="button"`) viola FR-016
mesmo com o `POST` certo.

## Project Structure

### Documentation (this feature)

```text
specs/029-fila-dia-reserva/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-reusada.md
│   ├── superficie-da-recepcao.md
│   ├── resumo-do-turno.md
│   ├── politica-de-autorizacao.md
│   └── logs.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks
```

### Source Code (repository root)

```text
app/                                 # intocado nas regras
└── modulos/hospedagem/              # GET /fila-do-dia, POST /reservas,
                                     # POST /reservas/{id}/chegada — reuso

frontend/src/painel/
├── destinos.ts                      # intacto (fila e reserva já no mapa)
├── Casca.tsx                        # fila → TelaFila; reserva → TelaNovaReserva
├── TelaFila.tsx                     # lista, resumo, botão, falha ≠ vazio
├── TelaNovaReserva.tsx              # três campos; cancela volta à fila
├── fila.ts                          # tipos, partição do resumo, elegibilidade
├── telefone.ts                      # dígitos / DDD (espelho da regra Python)
├── TelaFila.test.tsx
├── TelaNovaReserva.test.tsx
└── fila.test.ts                     # partição e botão, sem DOM

testes/                              # regressão já verde; sem arquivo novo
                                     # salvo se algum contrato HTTP mudar
```

**Structure Decision**: estende o `frontend/` da F8.1. Sem módulo
Python novo, sem worker, sem segundo app. As duas telas nomeadas da
recepção deixam de ser `TelaNomeada`.

## Complexity Tracking

> Nenhum item: o Constitution Check passou nas duas passagens. Vitest
> e dois componentes estão justificados no Artigo XI (problema
> presente: a casa da recepção ainda é só um título).
