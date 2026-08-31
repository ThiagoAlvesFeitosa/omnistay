# Implementation Plan: Ficha do hóspede e transcrição para o PMS

**Branch**: `030-ficha-hospede-pms` | **Date**: 2026-08-31 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/030-ficha-hospede-pms/spec.md`

## Summary

A recepção passa a **abrir, completar e copiar** a ficha do titular
que a F8.2 só sinalizava como parcial: nove campos, ausentes
nomeados, copiar tudo em texto rotulado, consentimento vigente com
data e revogação no painel. Gestão e staff continuam recusados.
Nenhuma integração com o sistema de gestão do hotel.

Decisões em [research.md](./research.md): reuso de `GET .../ficha` e
de consentimento; **uma** rota nova `PUT /reservas/{id}/ficha` na
operação `alterar_ficha_de_hospede` já existente; gatilho admite
`ficha_parcial` ↔ `ficha_recebida` para a fila deixar de mentir
parcial; texto de cópia montado no cliente. **Sem** tabela nova,
**sem** operação nova na matriz, **sem** Playwright, **sem** e-mail,
**sem** PMS.

## Technical Context

**Language/Version**: Python 3.11+ (gravação da ficha no módulo
`hospedagem`); TypeScript no `frontend/` já existente

**Primary Dependencies**: FastAPI — `GET /reservas/{id}/ficha` e
consentimento intactos; `PUT` novo. Frontend: Vite + React 19 +
React Router + Tailwind + shadcn copiado. Sem Redux, sem React Query,
sem Playwright, sem lib de clipboard além da API do navegador

**Storage**: PostgreSQL 16. **Nenhuma tabela nova.** Revisão Alembic
`0024` só no gatilho `fn_valida_transicao_reserva` (e `04-schema.sql`).
`hospede`, `reserva_hospede`, `consentimento` como estão

**Testing**: pytest — `PUT`, transição `ficha_parcial` ↔
`ficha_recebida`, recusas, isolamento, log sem dado pessoal;
conformidade do esquema com o gatilho novo. Vitest + Testing Library
— tela, ausentes, cópia, consentimento, `Ver ficha` na fila, menu
vazio sem fetch. `fetch` e `clipboard` falsos. **Nenhum** teste abre
navegador nem chama PMS/WhatsApp/IA

**Target Platform**: Servidor Linux; desenvolvimento Windows. SPA em
`/app`; proxy Vite já cobre `/reservas` e `/hospedes`. Recepção no
computador do balcão

**Project Type**: Serviço web + worker (intocado) + telas React no
`frontend/` existente, no lugar de `TelaNomeada` em `ficha`

**Performance Goals**: um hotel no MVP; um `GET` da ficha e um do
consentimento ao abrir; `PUT` ao gravar. Identificar completa/parcial
e ausentes < 20 s (SC-001). Sem meta de throughput

**Constraints**: tela nunca lê o token; nome, telefone, documento e
endereço fora do log e do `console`; `id_hotel` só na API; sem PMS;
sem e-mail; sem foto; idade não persistida; completar não atravessa
chegada/saída; F7.4 não filtra

**Scale/Scope**: 0 tabelas, 0 operações novas na matriz, 1 rota HTTP
nova, 1 revisão de gatilho, 3 rotas reusadas, 1 destino deixa de ser
só título (`ficha`), 1 controle novo na fila (`Ver ficha`), funções
puras (ausentes, texto de cópia, idade). Worker intocado

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Copiar é texto no cliente. Nenhum envio ao sistema de gestão. A spec e o plano não afirmam que o cadastro lá foi atualizado |
| II — Na dúvida, humano vê | Leitura humana (irreconhecível) aparece na ficha sem reproduzir a mensagem. Completar é no balcão |
| III — Gravar antes de enviar | `PUT` só persiste. Zero mensagem enfileirada |
| IV — Fila como verdade | Sem push. A pendência de parcial some no próximo `GET /fila-do-dia` depois da transição de status |
| V — Ausência humana visível | Completar no balcão **remove** a pendência de ficha incompleta. Consentimento sem registro aparece como nunca registrado, não como aceite |
| VI — Confirmação antes de tramitar | Intocado (hóspede). Gravar ficha não é tramitação de chamado |
| VII — Não ser intrusivo | Completar **não** dispara coleta nem correção |
| VIII — Minimização | Só recepção vê a ficha. Staff e gestão recusados na casca e na API de ficha. Sem foto. Idade só derivada. Log sem dado cadastral |
| IX — Garantias no banco | UNIQUE de documento permanece. Gatilho passa a admitir só o vai-e-vem `ficha_parcial` ↔ `ficha_recebida`; o resto da máquina permanece recusado |
| X — Portas trocáveis | Intocado. A tela não instancia LLM nem mensageria |
| XI — Complexidade exige problema | Uma rota, um gatilho, uma tela, funções puras. Sem lib de clipboard, sem segunda lista, sem módulo Python novo |
| XII — Teste primeiro | Cada FR com teste que falha por ausência (Vitest na tela; pytest no `PUT` e no gatilho) |
| XIII — Parâmetro não é constante | Intocado. Consentimento não ganha prazo novo |
| XIV — Multi-tenant | `id_hotel` da sessão; a tela não pede hotel. Ficha alheia continua `404` |
| XV — Honestidade | Não promete fim da digitação no PMS. Menu sem reserva não inventa ficha. Falha de leitura não se disfarça de ficha vazia de outro hóspede. Sem e-mail |

**Ponto de atenção 1 — `estado_cadastro` na visão.** Continua
derivado de `status`. Por isso completar os nove campos em
`ficha_parcial` **precisa** ir a `ficha_recebida`. Só virar
`ficha_completa` deixa a fila dizendo parcial.

**Ponto de atenção 2 — gestão lê consentimento e não lê ficha.** Não
embutir consentimento no JSON da ficha. A tela da recepção faz dois
GETs. Gestão nesta fatia: casca redireciona; zero fetch de ficha.

**Ponto de atenção 3 — ciclo de import.** `PUT` não importa
`conversa.service`. Validação pura: ver [research.md](./research.md) §3.

**Ponto de atenção 4 — testes da casca e da fila.** `Casca.test.tsx`
hoje 404 em URL desconhecida. `/ficha` vazio **não** deve disparar
`GET /reservas/…/ficha`. `TelaFila` ganha `Ver ficha`; testes da F8.2
precisam continuar verdes (chegada só no botão rotulado).

**Ponto de atenção 5 — conformidade do esquema.** `test_conformidade_do_esquema`
e `test_inventario` comparam o corpo de `fn_valida_transicao_reserva`
com `04-schema.sql`. A revisão `0024` e o documento saem juntos.

**Ponto de atenção 6 — clipboard no jsdom.** Mock de
`navigator.clipboard.writeText`. O fallback selecionável é o que
prova FR-017 quando o mock rejeita.

## Project Structure

### Documentation (this feature)

```text
specs/030-ficha-hospede-pms/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-reusada.md
│   ├── api-alterar-ficha.md
│   ├── superficie-da-recepcao.md
│   ├── politica-de-autorizacao.md
│   └── logs.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks
```

### Source Code (repository root)

```text
docs/04-schema.sql                       # gatilho: ficha_parcial ↔ ficha_recebida
alembic/versions/0024_ficha_parcial_completa.py
alembic/versions/sql/0024_ficha_parcial_completa.sql

app/modulos/hospedagem/
├── router.py          # PUT /reservas/{id}/ficha
├── service.py         # completar_ficha_titular (sem enfileirar mensagem)
├── schema.py          # FichaTitularEntrada
├── repository.py      # reuso de atualizar_hospede_titular / marcar_ficha_completa
└── validacao_ficha.py # se o import puro da conversa criar ciclo

frontend/src/painel/
├── destinos.ts        # prefixo /app/ficha
├── Casca.tsx          # ficha → TelaFicha; path opcional :idReserva
├── TelaFila.tsx       # controle Ver ficha (F8.2 permanece)
├── TelaFicha.tsx      # leitura, edição, cópia, consentimento
├── ficha.ts           # ausentes, texto de cópia, idade derivada
├── TelaFicha.test.tsx
└── ficha.test.ts      # funções puras, sem DOM

testes/unitarios/modulos/hospedagem/   # PUT / regras de completar
testes/integracao/                     # rota, gatilho, perfis, isolamento
```

**Structure Decision**: estende `hospedagem` e o `frontend/` da F8.1/F8.2.
Sem módulo Python novo, sem worker, sem segundo app. O destino `ficha`
deixa de ser `TelaNomeada`.

## Complexity Tracking

> Nenhum item: o Constitution Check passou nas duas passagens. A
> revisão de gatilho está justificada no Artigo IX (SC-004). Vitest e
> uma tela estão justificados no Artigo XI (a casa da ficha ainda é
> só um título).
