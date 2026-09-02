# Implementation Plan: A recepção responde ao hóspede

**Branch**: `036-resposta-recepcao` | **Date**: 2026-09-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/036-resposta-recepcao/spec.md`

## Summary

A recepção lê a **conversa da estadia** e envia **texto livre**
enquanto a janela de 24 horas do canal estiver aberta. O envio
grava a mensagem `pendente` e enfileira trabalho; o worker envia
pelo `MensageriaGateway`. A tela que hoje se chama Ficha do hóspede
passa a **Estadia**: conversa no topo, ficha recolhida. Responder
não resolve chamado. Fora da janela, o campo permanece com o
motivo.

Decisões em [research.md](./research.md): `GET /reservas/{id}/conversa`
e `POST /reservas/{id}/respostas`; tipo `enviar_resposta_recepcao`;
`tipo=resposta_recepcao` no JSON da enviada; visão da fila apaga
`precisa_atendimento_humano` depois da resposta humana. Revisão
`0025`. Worker **ganha um ramo**. Sem Playwright, sem PMS, sem
modelo aprovado.

## Technical Context

**Language/Version**: Python 3.11+ (`conversa` grava e enfileira;
`acesso` ganha duas operações; visão em `hospedagem`); TypeScript
no `frontend/` já existente

**Primary Dependencies**: FastAPI. Frontend: Vite + React 19 +
React Router + Tailwind + shadcn copiado. Sem Redux, sem React
Query, sem Playwright. Porta `MensageriaGateway` já existente
(`enviar_texto_sessao`)

**Storage**: PostgreSQL 16. **Nenhuma tabela nova.** Revisão
`0025`: `ck_trabalho_tipo` ganha `enviar_resposta_recepcao`;
índice único por `id_mensagem`; `vw_fila_do_dia` recalcula
`precisa_atendimento_humano`. `mensagem` e `trabalho` como estão.
`docs/04-schema.sql` no mesmo commit

**Testing**: pytest — POST grava+enfileira sem enviar; janela;
vazio; hotel alheio; perfil; GET com origens; visão da fila;
worker envia o texto já gravado; log sem corpo. Vitest — Estadia
(conversa no topo, ficha recolhida, envio, janela fechada);
fila destaca atendimento humano; atalhos **Estadia**; casca sem
fetch alheio. Relógio injetável. **Nenhum** teste abre navegador
nem chama WhatsApp/IA/PMS

**Target Platform**: Servidor Linux; desenvolvimento Windows. SPA
em `/app`; proxy Vite ganha as rotas novas sob `/reservas` (já
coberto). Recepção no computador

**Project Type**: Serviço web + worker (um tipo novo no
consumidor, mesmo `enviar_texto_sessao`) + tela React no destino
`ficha` já existente

**Performance Goals**: um hotel no MVP; `GET /conversa` ao abrir
a Estadia; `GET /ficha` só ao expandir dados cadastrais; POST não
espera o worker (SC-002: escrever em < 2 min). Sem meta de
throughput

**Constraints**: tela nunca lê o token; conteúdo de mensagem,
nome, telefone e documento fora do log e do `console`; `id_hotel`
só na API; 24 h são a janela do **canal**, não
`parametro_hotel`; sem PMS; sem modelo aprovado; palavras
“extrato” e “conta” fora; staff/gestão zero conversa

**Scale/Scope**: 0 tabelas, 2 operações novas na matriz, 2 rotas
HTTP, 1 tipo de trabalho, 1 revisão Alembic, 1 destino
renomeado/expandido, fila do dia ganha distintivo. Worker ganha
um `elif`

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Copiar ficha permanece no bloco cadastral. Enviar ao hóspede não lança consumo nem fala com o outro sistema |
| II — Na dúvida, humano vê | É o fecho: o humano **escreve**. Automático intocado |
| III — Gravar antes de enviar | POST insere `mensagem` `pendente` e `trabalho`; responde sem esperar o canal. Worker só envia o já gravado |
| IV — Fila como verdade | Falha de envio fica `falha`/`pendente` no histórico. Sem push. Recarregar a Estadia recupera |
| V — Ausência humana visível | Distintivo na fila do dia; some depois da resposta humana; pergunta nova reacende |
| VI — Confirmação antes de tramitar | Intocado na abertura de chamado. Esta resposta é humana, não tramitação |
| VII — Não ser intrusivo | Sem disparo automático novo. Texto livre só na janela do canal (clarificação) |
| VIII — Minimização | Payload do trabalho só IDs. Log sem corpo. Staff/gestão não lêem conversa |
| IX — Garantias no banco | UNIQUE do trabalho por `id_mensagem`. CHECK do tipo. Transição de chamado intocada |
| X — Portas trocáveis | Worker usa `MensageriaGateway`. Testes com falsa / simulada. Sem SDK |
| XI — Complexidade exige problema | Sem fila extra, sem Redis, sem lib de chat. Um tipo de trabalho e duas rotas são o buraco presente |
| XII — Teste primeiro | Cada FR com teste que falha por ausência |
| XIII — Parâmetro não é constante | 24 h são a janela **do canal**, não da propriedade (spec). Constante nomeada num módulo, testes com relógio. Hotel não pode alargar o que o canal recusa |
| XIV — Multi-tenant | `id_hotel` da sessão em GET e POST. Reserva alheia `404` |
| XV — Honestidade | Janela fechada declara o motivo. Pendente não se apresenta como entregue. Sem prometter entrega fora da janela |

**Ponto de atenção 1 — worker não fica intocado.** Allowlist e
`elif` no consumidor mudam juntos. Sem o ramo, `tipo_desconhecido`
destruiria o gancho (padrão F3.6).

**Ponto de atenção 2 — GET ficha atrasado.** Abrir a Estadia
dispara `GET /conversa`. `GET /ficha` e consentimento **só** ao
acionar **ver dados cadastrais**. Casca com id na rota precisa
mockar conversa; senão “regressa” em falha.

**Ponto de atenção 3 — 24 h não vão para `parametro_hotel`.** A
spec proíbe. Constante `JANELA_SESSAO_CANAL_HORAS = 24` em
`conversa`, usada pelo serviço e pelos testes com
`app.comum.relogio`. A tela **não** calcula a janela.

**Ponto de atenção 4 — origem no JSON, sem coluna nova.** Enviadas
já marcam `classificacao_bruta.tipo` (ex.: `confirmacao_resolucao`).
Resposta humana: `tipo=resposta_recepcao`. GET mapeia para
`hospede` / `automatico` / `recepcao`. Sem terceira direção em
`ck_mensagem_direcao`.

**Ponto de atenção 5 — visão, não flag persistida.**
`precisa_atendimento_humano` continua derivado. A `0025` só exige
mensagem humana **depois** da última `resposta_recepcao`. Alternativa
(coluna em `reserva`) já foi recusada na F3.2.

**Ponto de atenção 6 — POST não resolve.** Zero `UPDATE`
em `solicitacao`. Teste com chamado aberto depois do POST.

**Ponto de atenção 7 — botão Enviar, não Enter solto na ficha.**
O envio é o controle rotulado. Duplo clique: botão inerte enquanto
o POST não volta (padrão Resolvido).

**Ponto de atenção 8 — testes da casca e da fila.** `Casca.test.tsx`
abre `/app/ficha/:id`. Mock de `GET .../conversa`. `TelaFila`: o
tipo `ItemFila` ganha `precisa_atendimento_humano` (já vem no GET).
Atalhos **Ver ficha** → **Estadia** (fila, alertas, consumos).

## Project Structure

### Documentation (this feature)

```text
specs/036-resposta-recepcao/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-conversa.md
│   ├── api-resposta.md
│   ├── api-reusada.md
│   ├── fila-e-worker.md
│   ├── mensageria-sessao.md
│   ├── superficie-estadia.md
│   ├── superficie-fila.md
│   ├── destinos-e-perfis.md
│   ├── politica-de-autorizacao.md
│   └── logs.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks
```

### Source Code (repository root)

```text
app/modulos/conversa/        # GET conversa, POST respostas, janela,
                             # origem, processar_trabalho_enviar_resposta_recepcao
app/modulos/acesso/politica.py   # ler_conversa_da_estadia,
                                 # enviar_resposta_recepcao
app/fila/                    # tipo, enfileirar, TIPOS_CONSUMIVEIS
worker/consumidor.py         # elif enviar_resposta_recepcao
alembic/versions/0025_resposta_recepcao.py
docs/04-schema.sql           # CHECK, índice, visão

frontend/src/painel/
├── destinos.ts              # título Estadia (id e path intactos)
├── Casca.tsx                # TelaEstadia no destino ficha
├── TelaEstadia.tsx          # conversa + ficha recolhida
├── TelaEstadia.test.tsx
├── TelaFila.tsx             # distintivo + atalho Estadia
├── TelaAlertas.tsx          # atalho Estadia
├── TelaConsumos.tsx         # atalho Estadia
├── fila.ts                  # precisa_atendimento_humano
└── Casca.test.tsx           # mock GET conversa
```

**Structure Decision**: módulos já existentes. `conversa` governa
mensagem e o envio; a tela reusa o destino `ficha`. Sem app nova.

## Complexity Tracking

> Nenhum artigo violado. A constante 24 h está justificada no
> Artigo XIII da tabela (canal, não propriedade).
