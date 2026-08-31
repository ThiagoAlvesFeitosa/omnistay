# Implementation Plan: Chamados, pedidos e a tela da equipe

**Branch**: `031-chamados-pedidos-equipe` | **Date**: 2026-08-31 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/031-chamados-pedidos-equipe/spec.md`

## Summary

A recepção passa a **acompanhar** Chamados e pedidos, e a equipe a
**resolver** em Meus chamados no celular: lista aberta com as três
naturezas, tempo decorrido, mais antigos primeiro, um botão
Resolvido que confirma ao hóspede. Sem nome na lista; a recepção
chega à ficha por **Ver ficha**. Staff continua recusado na ficha.

Decisões em [research.md](./research.md): reuso de
`GET /solicitacoes` e `POST /solicitacoes/{id}/resolucao`; navegação
já existente para `/app/ficha/:idReserva`; tempo decorrido e rótulo
de natureza no cliente; depois de gravar, um `GET` da lista — não
recarregar a página. **Sem** tabela, **sem** operação nova na
matriz, **sem** Playwright, **sem** lib de estado, **sem** lançar
consumo.

## Technical Context

**Language/Version**: Python 3.11+ (intocado nas regras de
atendimento); TypeScript no `frontend/` já existente

**Primary Dependencies**: FastAPI — `GET /solicitacoes` e
`POST .../resolucao` intactos. Frontend: Vite + React 19 + React
Router + Tailwind + shadcn copiado. Sem Redux, sem React Query, sem
Playwright

**Storage**: PostgreSQL 16. **Nenhuma tabela nova.** `solicitacao` e
`consumo` como estão (`0001`…`0024` intactos). Sem revisão Alembic

**Testing**: pytest — regressão das rotas já verdes (lista,
resolução, perfis, isolamento). Vitest + Testing Library — duas
telas, naturezas, ordem, tempo decorrido, Ver ficha vs Resolvido,
equipe sem cadastral, falha de leitura ≠ lista vazia, casca sem
fetch alheio. `fetch` falso. **Nenhum** teste abre navegador nem
chama WhatsApp/IA/PMS

**Target Platform**: Servidor Linux; desenvolvimento Windows. SPA em
`/app`; proxy Vite já cobre `/solicitacoes`. Recepção no computador;
equipe no celular (desenho compacto da F8.1)

**Project Type**: Serviço web + worker (intocado; confirmação de
resolução já é trabalho existente) + telas React no `frontend/`
existente, no lugar de `TelaNomeada` em `alertas` e `chamados`

**Performance Goals**: um hotel no MVP; um `GET /solicitacoes` ao
abrir a tela e outro após resolver aceito. Identificar naturezas e
a mais antiga < 30 s; resolver no celular em um gesto < 15 s
(SC-001, SC-005). Sem meta de throughput. Sem tique de relógio

**Constraints**: tela nunca lê o token; descrição, nome, telefone e
documento fora do log e do `console`; `id_hotel` só na API; sem PMS;
sem lançar consumo; sem fila pessoal; clique fora do botão não
resolve; staff sem Ver ficha; F7.4 não filtra; palavras “extrato” e
“conta” fora da UI

**Scale/Scope**: 0 tabelas, 0 operações novas na matriz, 2 rotas
HTTP reusadas + navegação à ficha já existente, 2 destinos deixam
de ser só título (`alertas`, `chamados`), funções puras (natureza,
tempo decorrido). Worker intocado

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Resolver o quarto não lança consumo. Nenhum envio ao sistema de gestão |
| II — Na dúvida, humano vê | Intocado. Dúvida fora do catálogo não entra nesta lista |
| III — Gravar antes de enviar | O `POST` de resolução já grava e agenda o recado (F3.6). A tela não envia mensagem |
| IV — Fila como verdade | Sem push. Recarregar e “tentar de novo” consultam `GET /solicitacoes` |
| V — Ausência humana visível | **É esta fatia.** Pendência aberta visível; se ninguém clica, permanece. Falha de leitura ≠ lista vazia |
| VI — Confirmação antes de tramitar | Intocado na abertura. Na resolução, a ordem já é gravar depois avisar — a tela não inverte |
| VII — Não ser intrusivo | Sem recado proativo novo; o recado de conclusão já existe |
| VIII — Minimização | Listas sem cadastral. Staff recusado na ficha (casca + API). Log sem descrição nem dado pessoal |
| IX — Garantias no banco | Transição de resolução e `409` de segunda tentativa permanecem no servidor. A tela não inventa reabrir |
| X — Portas trocáveis | Intocado. A tela não instancia LLM nem mensageria |
| XI — Complexidade exige problema | Sem rota nova, sem lib de estado, sem Playwright. Dois componentes e funções puras são o problema presente (os destinos ainda são só título) |
| XII — Teste primeiro | Cada FR com teste que falha por ausência (Vitest na tela; pytest só regressão — HTTP não muda) |
| XIII — Parâmetro não é constante | `horas_destaque_chamado_aberto` continua no hotel; a tela só lê o booleano já calculado |
| XIV — Multi-tenant | `id_hotel` da sessão; a tela não pede hotel. Item alheio continua `404` na resolução |
| XV — Honestidade | Sem atribuir, sem resolvidos do dia, sem inferir conserto. Consumo resolvido não é lançado. Sem notificação empurrada |

**Ponto de atenção 1 — gestão tem a operação e não tem a tela.**
`ler_solicitacao_atribuida` inclui `gestor`. A casca **não** monta
Chamados e pedidos nem Meus chamados para gestão; zero fetch. Não
“esconder com CSS”.

**Ponto de atenção 2 — testes da casca.** `Casca.test.tsx` abre
`/app/chamados` e `/app/alertas`. Ao nascerem as telas, o mock
precisa responder `GET /solicitacoes` (`200` com `itens: []` no
mínimo). Senão a casca “regressa” com estado de falha. Staff em
`/ficha/:id` continua sem GET de ficha.

**Ponto de atenção 3 — botão, não a linha.** A spec fecha clique no
rótulo. `<article onClick>` (ou linha com `role="button"`) que
dispare `POST` viola FR-009 mesmo com o endpoint certo. **Ver ficha**
é `<Link>`, não o mesmo controle de **Resolvido**.

**Ponto de atenção 4 — não reordenar.** O GET já vem `aberta_em ASC`.
`Array.sort` por destaque quebraria a clarificação.

**Ponto de atenção 5 — TelaFicha vazia.** Menu sem id continua
apontando à fila (F8.3). Ajustar a frase para citar também Chamados
e pedidos como origem do **Ver ficha** com id.

**Ponto de atenção 6 — worker.** Confirmação ao hóspede já é
`enviar_confirmacao_resolucao`. Esta fatia não toca o consumidor.
Quickstart manual com worker no ar é opcional; Vitest não espera a
mensagem.

## Project Structure

### Documentation (this feature)

```text
specs/031-chamados-pedidos-equipe/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-reusada.md
│   ├── superficie-da-recepcao.md
│   ├── superficie-da-equipe.md
│   ├── politica-de-autorizacao.md
│   └── logs.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks
```

### Source Code (repository root)

```text
app/                                 # intocado nas regras
└── modulos/atendimento/             # GET /solicitacoes,
                                     # POST /solicitacoes/{id}/resolucao — reuso

frontend/src/painel/
├── destinos.ts                      # intacto (alertas e chamados já no mapa)
├── Casca.tsx                        # alertas → TelaAlertas; chamados → TelaChamados
├── TelaAlertas.tsx                  # recepção: lista, Ver ficha, Resolvido
├── TelaChamados.tsx                 # equipe: cartões, um botão, compacto
├── TelaFicha.tsx                    # frase do vazio: dois caminhos de origem
├── solicitacoes.ts                  # tipos, natureza, tempo decorrido
├── TelaAlertas.test.tsx
├── TelaChamados.test.tsx
└── solicitacoes.test.ts             # funções puras, sem DOM

testes/                              # regressão já verde; sem arquivo novo
                                     # salvo se algum contrato HTTP mudar
```

**Structure Decision**: estende o `frontend/` da F8.1–F8.3. Sem
módulo Python novo, sem worker, sem segundo app. Os destinos
`alertas` e `chamados` deixam de ser `TelaNomeada`.

## Complexity Tracking

> Nenhum item: o Constitution Check passou nas duas passagens.
> Vitest e dois componentes estão justificados no Artigo XI
> (problema presente: Alert Center e casa da equipe ainda são só
> título).
