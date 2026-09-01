# Implementation Plan: Consumos a lançar e saída do hóspede

**Branch**: `032-consumos-saida-hospede` | **Date**: 2026-08-31 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/032-consumos-saida-hospede/spec.md`

## Summary

A recepção passa a **lançar ou dispensar** na fila financeira e a
**confirmar a saída** vendo os pedidos feitos pelo chat, avisada se
ainda houver pendência. Sem nome em Consumos a lançar; cada linha
leva à ficha. O controle na fila do dia **só abre** Saída do
hóspede; encerrar é o botão dessa tela. Sem status por item na
lista da saída.

Decisões em [research.md](./research.md): reuso de
`GET /consumos/pendentes`, `POST .../lancamento`, `POST .../dispensa`,
`GET .../pedidos-feitos-pelo-chat`, `POST .../saida`,
`GET .../ficha` e `GET /fila-do-dia`; tempo decorrido já existente;
depois de gravar, um `GET` da lista — não recarregar a página.
**Sem** tabela, **sem** operação nova na matriz, **sem** Playwright,
**sem** alterar backend.

## Technical Context

**Language/Version**: Python 3.11+ (intocado nas regras de
atendimento e hospedagem); TypeScript no `frontend/` já existente

**Primary Dependencies**: FastAPI — rotas de pendentes, lançamento,
dispensa, pedidos do chat, saída e ficha intactas. Frontend: Vite +
React 19 + React Router + Tailwind + shadcn copiado. Sem Redux, sem
React Query, sem Playwright

**Storage**: PostgreSQL 16. **Nenhuma tabela nova.** `consumo`,
`solicitacao` e `reserva` como estão (`0001`…`0024` intactos). Sem
revisão Alembic

**Testing**: pytest — regressão das rotas já verdes (pendentes,
lançamento, dispensa, saída, pedidos, fila, perfis). Vitest +
Testing Library — Consumos a lançar, Saída do hóspede, acréscimo na
fila (caminho **Saída**, destaque vencida), casca sem fetch alheio.
`fetch` falso. **Nenhum** teste abre navegador nem chama
WhatsApp/IA/PMS

**Target Platform**: Servidor Linux; desenvolvimento Windows. SPA em
`/app`; proxy Vite já cobre `/consumos` e `/reservas`. Recepção no
computador

**Project Type**: Serviço web + worker (intocado; pesquisa e lista
ao hóspede já são trabalho do `POST /saida`) + telas React no
`frontend/` existente, no lugar de `TelaNomeada` em `consumos` e
`saida`, e acréscimo em `TelaFila`

**Performance Goals**: um hotel no MVP; um `GET /consumos/pendentes`
ao abrir a fila financeira e outro após lançar/dispensar aceito. Na
saída, ficha + pedidos + pendentes (+ fila para datas). Identificar
total e mais antigo < 30 s; lançar em um gesto < 15 s (SC-001,
SC-004). Sem meta de throughput. Sem tique de relógio

**Constraints**: tela nunca lê o token; descrição, nome, telefone,
documento e valor como texto livre fora do log e do `console`;
`id_hotel` só na API; sem PMS; sem status por item na lista da
saída; aviso não trava o checkout; clique fora do botão não lança
nem encerra; F7.4 não filtra; palavras “extrato” e “conta” fora da
UI

**Scale/Scope**: 0 tabelas, 0 operações novas na matriz, 6 rotas
HTTP reusadas + navegação à ficha já existente, 2 destinos deixam
de ser só título (`consumos`, `saida`), acréscimo na fila do dia,
funções puras (total pendente, aviso da estadia). Worker intocado

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Marcar lançado é o clique da ponte. Nenhum débito, nenhuma consulta ao sistema de gestão |
| II — Na dúvida, humano vê | Intocado. Fila financeira é a omissão visível do lançamento |
| III — Gravar antes de enviar | O `POST /saida` já grava e agenda pesquisa/lista (F4.1–F4.2). A tela não envia mensagem. Lançar/dispensar não geram recado |
| IV — Fila como verdade | Sem push. Recarregar e “tentar de novo” consultam os GET já existentes |
| V — Ausência humana visível | **É esta fatia** na quarta travessia e no checkout. Falha de leitura ≠ lista vazia. Destaque de saída vencida na fila |
| VI — Confirmação antes de tramitar | Intocado na abertura do consumo. Lançar não inventa recado novo |
| VII — Não ser intrusivo | Sem recado proativo novo; pesquisa e lista ao hóspede já existem no clique de saída |
| VIII — Minimização | Consumos a lançar sem cadastral (consulta compartilhada com equipe/gestão). Staff recusado nestas telas. Log sem descrição, nome nem valor livre |
| IX — Garantias no banco | Transição de lançamento/dispensa/`409` e de saída permanecem no servidor. A tela não inventa reabrir |
| X — Portas trocáveis | Intocado. A tela não instancia LLM nem mensageria |
| XI — Complexidade exige problema | Sem rota nova, sem lib de estado, sem Playwright, sem GET de reserva novo. Dois componentes + acréscimo na fila são o problema presente (destinos ainda só título) |
| XII — Teste primeiro | Cada FR com teste que falha por ausência (Vitest na tela; pytest só regressão — HTTP não muda) |
| XIII — Parâmetro não é constante | Nenhum prazo novo. Tempo de espera deriva de `aberta_em` já na resposta |
| XIV — Multi-tenant | `id_hotel` da sessão; a tela não pede hotel. Item alheio continua `404` |
| XV — Honestidade | Aviso não trava. Marcar lançado não afirma que o outro sistema cobrou. Sem status por item nesta fase. Sem notificação empurrada |

**Ponto de atenção 1 — gestão tem algumas operações e não tem a tela.**
`ler_solicitacao_atribuida` (pendentes) e `ler_pedidos_feitos_pelo_chat`
incluem `gestor`. A casca **não** monta Consumos a lançar nem Saída
do hóspede para gestão; zero fetch. Não “esconder com CSS”.

**Ponto de atenção 2 — testes da casca.** `Casca.test.tsx` e
`fetchPorPerfil` precisam responder `GET /consumos/pendentes`
(`200` com `itens: []` no mínimo) quando a recepção abrir
`/app/consumos`. Staff/gestão em `/consumos` e `/saida/:id`: casca
redireciona; **zero** GET de pendentes, ficha, pedidos e saída.

**Ponto de atenção 3 — botão, não a linha.** Lançar, dispensar e
confirmar saída só no `<button>` rotulado. **Ver ficha** e **Saída**
na fila são `<Link>`. `<tr onClick>` que dispare POST viola FR-008
e FR-018.

**Ponto de atenção 4 — não reordenar.** O GET de pendentes já vem
`aberta_em ASC`. `Array.sort` quebraria SC-001.

**Ponto de atenção 5 — rótulo na fila.** O caminho do hospedado é
**Saída**, não **Confirmar saída**. Encerrar no mesmo gesto viola
a clarificação.

**Ponto de atenção 6 — worker.** Pesquisa e lista ao hóspede já
nascem no `POST /saida`. Esta fatia não toca o consumidor.
Quickstart manual com worker no ar é opcional; Vitest não espera a
mensagem.

**Ponto de atenção 7 — destino com id.** `/app/saida/:idReserva?`
como a ficha. `destinoPorCaminho` precisa reconhecer o prefixo;
senão staff cola `/saida/1` e a casca não recusa o destino.

## Project Structure

### Documentation (this feature)

```text
specs/032-consumos-saida-hospede/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-reusada.md
│   ├── superficie-consumos.md
│   ├── superficie-saida.md
│   ├── acrescimo-na-fila.md
│   ├── politica-de-autorizacao.md
│   └── logs.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks
```

### Source Code (repository root)

```text
app/                                 # intocado nas regras
├── modulos/atendimento/             # GET /consumos/pendentes,
│                                    # POST .../lancamento, .../dispensa
└── modulos/hospedagem/              # GET pedidos, POST /saida,
                                     # GET ficha, GET /fila-do-dia

frontend/src/painel/
├── destinos.ts                      # destinoPorCaminho: prefixo /saida/
├── Casca.tsx                        # consumos → TelaConsumos;
│                                    # saida → TelaSaida em /saida/:id?
├── TelaConsumos.tsx                 # fila financeira, lançar, dispensar
├── TelaSaida.tsx                    # lista cobrável, aviso, confirmar
├── TelaFila.tsx                     # Link Saída + destaque vencida
├── fila.ts                          # saida_nao_confirmada; caminho
├── consumos.ts                      # tipos, total, aviso da estadia
├── TelaConsumos.test.tsx
├── TelaSaida.test.tsx
├── TelaFila.test.tsx                # acréscimo
├── Casca.test.tsx                   # mock pendentes; recusa alheia
├── destinos.test.ts                 # prefixo /saida/:id
└── consumos.test.ts                 # funções puras, sem DOM

testes/                              # regressão já verde; sem arquivo novo
```

**Structure Decision**: estende o `frontend/` da F8.1–F8.4. Sem
módulo Python novo, sem worker, sem segundo app. Os destinos
`consumos` e `saida` deixam de ser `TelaNomeada`. A fila do dia
ganha o caminho e o destaque já definidos em F4.1/F8.2.

## Complexity Tracking

> Nenhum item: o Constitution Check passou nas duas passagens.
> Vitest e dois componentes estão justificados no Artigo XI
> (problema presente: Consumos a lançar e Saída do hóspede ainda
> são só título; o checkout na fila ainda não existe).
