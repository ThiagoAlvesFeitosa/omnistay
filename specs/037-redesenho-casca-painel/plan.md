# Implementation Plan: Redesenho da casca do painel e apresentação

**Branch**: `037-redesenho-casca-painel` | **Date**: 2026-09-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/037-redesenho-casca-painel/spec.md`

## Summary

A casca autenticada passa da faixa superior para **lateral com
identidade** (nome da casa, OmniStay discreto, pessoa + perfil +
Sair). O menu agrupa por área e **tira Nova reserva** (fica o botão
da fila). Em tela estreita o menu é overlay que fecha por botão,
fundo, destino ou Sair. Simulador e Estadia compartilham **dois
lados de bolha** e o horário (só hora hoje; data e hora noutro dia).
Moeda e datas lidas usam o padrão brasileiro.

Decisões em [research.md](./research.md): `nome_hotel` em
`POST /sessoes` e `GET /sessoes/atual` via `propriedade` (sem Alembic);
viewport `md` no lugar do `compacto` da equipe; `apresentacao.ts` com
`Intl`; `BolhaConversa` compartilhada; Enter só no simulador.
**Sem** Playwright, **sem** PMS, **sem** operação nova na matriz.

## Technical Context

**Language/Version**: Python 3.11+ (`acesso` + `propriedade` só no
JSON da sessão); TypeScript no `frontend/` já existente

**Primary Dependencies**: FastAPI. Frontend: Vite + React 19 +
React Router + Tailwind + shadcn copiado. Sem Redux, sem date-fns,
sem Playwright. `Intl` nativo para moeda/data

**Storage**: PostgreSQL 16. **Nenhuma tabela nova.** `hotel.nome` já
existe. Sem revisão Alembic. Worker intocado

**Testing**: pytest — `nome_hotel` na casa certa, isolamento entre
propriedades, regressão de cookie/401. Vitest — casca (grupos,
identidade, overlay, sem Nova reserva no menu), `apresentacao.ts`,
bolhas (simulador + Estadia), regressão das telas com grafia nova
no mesmo cenário. Relógio injetável. **Nenhum** teste abre
navegador nem chama rede externa

**Target Platform**: Servidor Linux; desenvolvimento Windows. SPA em
`/app`. Equipe no celular; recepção e gestão no computador; janela
estreita da recepção usa o mesmo overlay

**Project Type**: Serviço web (JSON de sessão) + casca React no
`frontend/` existente. Worker intocado

**Performance Goals**: um hotel no MVP; `GET /sessoes/atual` no
carregamento (já ocorre) passa a trazer o nome. Sem meta de
throughput. Overlay fecha em um gesto (SC-002)

**Constraints**: tela nunca lê o token; senha, cookie e conteúdo de
mensagem fora do log e do `console`; `id_hotel` só na API; sem PMS;
palavra “extrato” fora; Enter na Estadia não envia; F7.4 não filtra
menu; rótulos visíveis Recepção / Gestão / Equipe

**Scale/Scope**: 0 tabelas, 0 operações novas, 2 corpos JSON
ampliados, 1 função em `propriedade`, 1 mapa de destinos, 1 casca,
1 módulo de apresentação, 1 componente de bolha, ~10 telas só na
grafia. Worker 0

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Casca e formato não inferem chegada/saída. Zero clique operacional novo |
| II — Na dúvida, humano vê | Intocado. Sem classificar mensagem |
| III — Gravar antes de enviar | Intocado. Simulador e Estadia já gravam como nas fatias delas |
| IV — Fila como verdade | Sem push. Recarregar consulta `GET /sessoes/atual` |
| V — Ausência humana visível | Não inventa fila nova; listas existentes só mudam grafia |
| VI — Confirmação antes de tramitar | Intocado |
| VII — Não ser intrusivo | Sem recado proativo novo |
| VIII — Minimização | `id_hotel` não vai ao JSON. Log sem senha, token, corpo, `nome_hotel` como evento. Foto continua recusada |
| IX — Garantias no banco | Nenhuma regra nova de sessão; UNIQUE e prazo já existem |
| X — Portas trocáveis | Intocado. Casca não instancia LLM nem mensageria |
| XI — Complexidade exige problema | Sem app nova, sem date-fns, sem drawer lib, sem Playwright. `Intl` e overlay Tailwind são o problema presente |
| XII — Teste primeiro | Cada FR com teste que falha por ausência (pytest ou Vitest) |
| XIII — Parâmetro não é constante | 768 px é corte de apresentação, não prazo de hotel — não entra em `parametro_hotel`. Janela 24 h da Estadia continua a da F7.6 |
| XIV — Multi-tenant | `nome_hotel` só da propriedade da sessão; teste de isolamento |
| XV — Honestidade | Overlay e grafia não prometem PMS, alta disponibilidade nem fuso por hotel |

**Ponto de atenção 1 — fronteira `acesso` / `propriedade`.**
`acesso` não faz `SELECT` em `hotel`. Import local de
`ler_nome_hotel`, no mesmo espírito da duração da sessão.

**Ponto de atenção 2 — equipe sem menu hoje.** O `compacto` esconde
a `<nav>`. A US3 exige overlay com identidade. Testes da casca que
assumem zero link na equipe precisam passar a achar **Meus chamados**.

**Ponto de atenção 3 — `R$` duplicado.** Várias telas já prefixam
`R$` em número cru (`9.00`). A função compartilhada já traz o
símbolo; prefixar de novo vira `R$ R$ 9,00`. Troca e teste juntos.

**Ponto de atenção 4 — fuso no Vitest.** `formatarInstante` usa
`Date` local. Testes de unidade fixam `agora` e instantes sem
depender do fuso da máquina (calendário `YYYY-MM-DD` sem `Z`;
instante com parede conhecida ou offset explícito documentado no
teste).

**Ponto de atenção 5 — Enter.** Só o simulador. A Estadia continua
a impedir Enter (F7.6). Teste das duas telas no mesmo ciclo para
não unificar por acidente.

## Project Structure

### Documentation (this feature)

```text
specs/037-redesenho-casca-painel/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── sessao-nome-da-casa.md
│   ├── casca-navegacao.md
│   ├── destinos-e-grupos.md
│   ├── apresentacao-br.md
│   ├── conversa-bolhas.md
│   ├── politica-de-autorizacao.md
│   └── logs.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks
```

### Source Code (repository root)

```text
app/modulos/propriedade/
    repository.py            # ler nome do hotel por id_hotel
    service.py               # ler_nome_hotel (sem HTTP)
app/modulos/acesso/
    schema.py                # nome_hotel em SessaoCriada e SessaoAtualResposta
    router.py                # POST e GET atual preenchem o campo
                             # GET atual passa a receber Conexao

frontend/src/painel/
├── apresentacao.ts          # moeda, data, instante, bolha, decorrido
├── apresentacao.test.ts
├── destinos.ts              # grupo, noMenu; itensMenu agrupado
├── destinos.test.ts         # se ainda não cobrir grupos
├── sessao.ts                # nome_hotel nos tipos
├── Casca.tsx                # lateral / overlay; identidade; grupos
├── Casca.test.tsx
├── BolhaConversa.tsx        # dois lados + horário
├── TelaEstadia.tsx          # bolhas; horário; Enter intacto
├── TelaEstadia.test.tsx
├── TelaAlertas.tsx          # instante · decorrido; moeda
├── TelaChamados.tsx
├── TelaConsumos.tsx
├── TelaFila.tsx             # datas BR; botão Nova reserva permanece
├── TelaVendaveis.tsx / vendaveis.ts
├── TelaPainel.tsx
├── TelaMercado.tsx
├── TelaRetencao.tsx
└── ficha.ts                 # formatarDataVisivel delega
frontend/src/TelaSimulacao.tsx   # Tailwind, cartões, bolhas, Enter
```

**Structure Decision**: os módulos e a casca já existem. Sem app
nova, sem worker, sem migração. A leitura do nome da casa é o único
toque de backend.

## Complexity Tracking

> Nenhum artigo violado. O corte 768 px está justificado no Artigo
> XIII da tabela (apresentação, não parâmetro de hotel).
