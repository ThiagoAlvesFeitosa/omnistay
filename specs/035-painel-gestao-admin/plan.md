# Implementation Plan: Painel da gestão, mercado e administração

**Branch**: `035-painel-gestao-admin` | **Date**: 2026-09-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/035-painel-gestao-admin/spec.md`

## Summary

A gestão passa a ver, no painel, **quatro números da operação**
(sem lista de hóspede), o **comparativo de mercado** com coleta
falhada marcada, a **relação de usuários** (criar e desativar, sem
reativar e sem revogar sessão) e o **comprovante de retenção**.
Recepção e equipe operacional não montam estas telas.

Decisões em [research.md](./research.md): `GET /indicadores` com
quatro números puros (`GET /indicadores/chegadas-do-dia` intacto);
`GET /usuarios` novo; `POST`/`DELETE /usuarios` reusados; Mercado
só `GET /mercado` e histórico; `GET /retencao` ganha prazos no
envelope. **Sem** CRUD de concorrente, **sem** reativar usuário,
**sem** gráfico, **sem** tarifa da casa, **sem** Playwright,
**sem** revisão Alembic.

## Technical Context

**Language/Version**: Python 3.11+ (hospedagem chama atendimento
para dois números; acesso lista usuários; propriedade acrescenta
prazos no comprovante); TypeScript no `frontend/` já existente

**Primary Dependencies**: FastAPI. Frontend: Vite + React 19 +
React Router + Tailwind + shadcn copiado. Sem Redux, sem React
Query, sem Playwright

**Storage**: PostgreSQL 16. **Nenhuma tabela nova.** Contagens e
somas em `reserva`, `solicitacao`, `consumo`; lista em `usuario`;
comprovante em `execucao_retencao` + duas chaves de
`parametro_hotel`. Sem revisão Alembic

**Testing**: pytest — COUNT/SUM, `GET /indicadores` sem campos
nominados, `GET /usuarios`, prazos no `GET /retencao`. Vitest +
Testing Library — quatro telas e casca sem fetch alheio.
`fetch` falso. **Nenhum** teste abre navegador nem chama
WhatsApp/IA/fonte/PMS

**Target Platform**: Servidor Linux; desenvolvimento Windows. SPA
em `/app`; proxy Vite já cobre `/indicadores`, `/mercado`,
`/usuarios`, `/retencao`. Gestão no computador

**Project Type**: Serviço web + worker (intocado; coleta de
mercado e passagem de retenção já existem) + telas React no
`frontend/` existente, no lugar de `TelaNomeada` em `indicadores`,
`mercado`, `usuarios` e `retencao`

**Performance Goals**: um hotel no MVP; um GET ao abrir cada
tela; GET extra de histórico só no clique; GET da lista depois de
criar/desativar. Completar as quatro consultas numa visita
(SC-001). Sem meta de throughput

**Constraints**: tela nunca lê o token; senha, hash, cookie,
conteúdo de mensagem e dado cadastral de hóspede fora do log e do
`console`; `id_hotel` só na API; sem PMS; sem reativar usuário;
sem CRUD de concorrente nestas telas; sem disparo de expurgo; F7.4
não filtra; telas sem recorte compacto da equipe

**Scale/Scope**: 0 tabelas, 0 operações novas na matriz, 1 rota
nova de indicadores, 1 rota nova de lista de usuários, 1 envelope
de retenção alargado, 4 destinos deixam de ser só título. Worker
intocado

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Sem tarifa da casa. Consumo a lançar é soma do que o OmniStay já marcou pendente, não débito no outro sistema |
| II — Na dúvida, humano vê | Intocado. Sem resposta a hóspede |
| III — Gravar antes de enviar | Intocado. Telas não enviam mensagem |
| IV — Fila como verdade | Sem push. Recarregar e “tentar de novo” consultam os GET |
| V — Ausência humana visível | Falha de leitura ≠ zeros / lista vazia. Consumo a lançar zero é honesto |
| VI — Confirmação antes de tramitar | Intocado |
| VII — Não ser intrusivo | Sem recado proativo |
| VIII — Minimização | Números sem lista nominada. Operação e recepção: zero fetch nestes destinos. Log sem senha, sem texto de hóspede, sem hash |
| IX — Garantias no banco | Unique de e-mail e CHECK de perfil permanecem no servidor. A tela não inventa apagar usuário nem reativar |
| X — Portas trocáveis | Intocado. Sem LLM, sem fonte, sem mensageria |
| XI — Complexidade exige problema | Sem lib de estado, sem Playwright, sem aba de cadastro de concorrente, sem reativar. Quatro componentes + dois GET novos são o problema presente (ainda só título; três números e a lista não existem) |
| XII — Teste primeiro | Cada FR com teste que falha por ausência (pytest nos números/lista; Vitest na tela) |
| XIII — Parâmetro não é constante | Prazos de retenção vêm de `parametro_hotel`; `null` se inválidos — sem 12/5 no cliente |
| XIV — Multi-tenant | `id_hotel` da sessão; a tela não pede hotel. Usuário/concorrente/comprovante alheio continua recusado |
| XV — Honestidade | Falha de coleta não se apresenta como preço de agora. Desativar não afirma apagamento. Painel não promete gráfico nem nota média |

**Ponto de atenção 1 — não contar no cliente.** `GET /solicitacoes`
e `GET /consumos/pendentes` existem e a gestão até lê o primeiro
pela matriz. A tela Painel **não** os usa. Os números nascem no
servidor (FR-002).

**Ponto de atenção 2 — hospedagem chama atendimento.** Dois dos
quatro números moram em tabelas de atendimento. O serviço de
hospedagem chama o serviço de atendimento; **não** escreve SQL
em `solicitacao`/`consumo`.

**Ponto de atenção 3 — `ler_indicadores` inclui recepção.** A
matriz não muda. Recepção **pode** `GET /indicadores` pela API
(como já pode chegadas-do-dia). A casca **não** monta Painel nem
dispara o GET. Staff: `403`.

**Ponto de atenção 4 — testes da casca.** `Casca.test.tsx` afirma
heading Painel só com título. Essa asserção **quebra de propósito**.
`fetchPorPerfil` precisa responder `GET /indicadores`,
`GET /mercado`, `GET /usuarios`, `GET /retencao` no mínimo com
zeros / listas vazias. Recepção e staff nesses endereços: casca
redireciona; **zero** GET.

**Ponto de atenção 5 — sem reativar, e-mail fica ocupado.** DELETE
já desativa. A tela não oferece Reativar. Criar com o e-mail do
desativado continua `409`. Teste de superfície e de API.

**Ponto de atenção 6 — Mercado sem escrita.** Botões de criar
concorrente não existem. `405` em escrita de coleta permanece. A
tela não chama `/concorrentes`.

**Ponto de atenção 7 — botões, não a linha.** Criar e desativar
usuário só no `<button>` rotulado. Sem DELETE visível como
“apagar”. Sem revogar sessão.

## Project Structure

### Documentation (this feature)

```text
specs/035-painel-gestao-admin/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-indicadores.md
│   ├── api-usuarios.md
│   ├── api-reusada.md
│   ├── superficie-painel.md
│   ├── superficie-mercado.md
│   ├── superficie-usuarios.md
│   ├── superficie-retencao.md
│   ├── destinos-e-perfis.md
│   └── logs.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks
```

### Source Code (repository root)

```text
app/modulos/hospedagem/          # GET /indicadores; COUNT hospedados;
                                 # chegadas-do-dia intocado
app/modulos/atendimento/         # COUNT chamados abertos (sem consumo);
                                 # SUM consumo pendente — chamados pelo
                                 # serviço de hospedagem
app/modulos/acesso/              # GET /usuarios; POST/DELETE intactos
app/modulos/propriedade/         # GET /retencao + prazos no envelope
app/modulos/mercado/             # GET /mercado e histórico intocados

frontend/src/painel/
├── Casca.tsx                    # quatro destinos → telas reais
├── TelaPainel.tsx
├── TelaMercado.tsx
├── TelaUsuarios.tsx
├── TelaRetencao.tsx
├── indicadores.ts
├── mercado.ts
├── usuarios.ts
├── retencao.ts
├── TelaPainel.test.tsx
├── TelaMercado.test.tsx
├── TelaUsuarios.test.tsx
├── TelaRetencao.test.tsx
├── Casca.test.tsx               # mock GET; recepção/staff zero fetch
└── destinos.ts                  # perfis já só gestor nestes quatro

testes/unitarios/                # COUNT/SUM e lista sem hash
testes/integracao/               # GET /indicadores, GET /usuarios,
                                 # envelope de /retencao
```

**Structure Decision**: estende o `frontend/` da F8.1–F8.6 e os
módulos Python que já governam cada tabela. Sem módulo novo, sem
worker, sem segundo app. Os destinos `indicadores`, `mercado`,
`usuarios` e `retencao` deixam de ser `TelaNomeada`. `TelaNomeada`
só permanece se ainda houver destino só com título (não há).

## Complexity Tracking

> Nenhum item: o Constitution Check passou nas duas passagens.
> Vitest, quatro componentes e dois GET novos estão justificados
> no Artigo XI (problema presente: as quatro telas ainda são só
> título; três números e a lista de usuários não existem como
> consulta pura).
