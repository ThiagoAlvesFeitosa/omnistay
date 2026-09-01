# Implementation Plan: Catálogo, itens vendáveis e recado de boas-vindas

**Branch**: `034-catalogo-vendaveis-recado` | **Date**: 2026-09-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/034-catalogo-vendaveis-recado/spec.md`

## Summary

A recepção passa a **manter o catálogo por categoria**, **cadastrar
e ajustar itens vendáveis com preço em campo próprio** e **editar
os quatro campos do recado de boas-vindas**, com recusa de formato
visível ao salvar. Gestão lê as três telas, sem controles de
alteração. Perfil operacional continua recusado, sem fetch.
Desativar no lugar de apagar. Sem campo “descrição” no item
vendável.

Decisões em [research.md](./research.md): reuso de `GET|POST
/catalogo`, `PATCH /catalogo/{id}`, `GET|POST /itens-vendaveis`,
`PATCH /itens-vendaveis/{id}`, `GET|PUT /propriedade/boas-vindas`;
abas de categoria no cliente; depois de gravar, um `GET` da lista
— não recarregar a página. Gestão entra no `perfis` dos três
destinos. Proxy Vite ganha `/itens-vendaveis`. **Sem** tabela,
**sem** operação nova na matriz, **sem** Playwright, **sem**
alterar backend.

## Technical Context

**Language/Version**: Python 3.11+ (intocado nas regras de
propriedade); TypeScript no `frontend/` já existente

**Primary Dependencies**: FastAPI — rotas de catálogo, item
vendável e boas-vindas intactas. Frontend: Vite + React 19 +
React Router + Tailwind + shadcn copiado. Sem Redux, sem React
Query, sem Playwright

**Storage**: PostgreSQL 16. **Nenhuma tabela nova.**
`catalogo_item`, `item_vendavel` e `parametro_hotel` como estão
(`0001`…`0024` intactos). Sem revisão Alembic

**Testing**: pytest — regressão das rotas já verdes (catálogo,
itens-vendáveis, boas-vindas, perfis). Vitest + Testing Library —
três telas, destinos da gestão, casca sem fetch alheio no staff.
`fetch` falso. **Nenhum** teste abre navegador nem chama
WhatsApp/IA/PMS

**Target Platform**: Servidor Linux; desenvolvimento Windows. SPA
em `/app`; proxy Vite já cobre `/catalogo` e `/propriedade`; esta
fatia acrescenta `/itens-vendaveis`. Recepção e gestão no
computador

**Project Type**: Serviço web + worker (intocado; atendimento
automático e envio do recado já existem) + telas React no
`frontend/` existente, no lugar de `TelaNomeada` em `catalogo`,
`vendaveis` e `boas-vindas`

**Performance Goals**: um hotel no MVP; um GET de manutenção ao
abrir cada tela e outro após gravar aceito. Completar um fato, um
preço e os quatro campos numa visita ao painel (SC-001). Sem meta
de throughput. Sem tique de relógio

**Constraints**: tela nunca lê o token; texto do fato, preço como
texto livre, senha e conteúdo de mensagem fora do log e do
`console`; `id_hotel` só na API; sem PMS; sem apagar; sem
descrição de item vendável; recusa de formato no salvar, não no
envio; F7.4 não filtra; aviso de assistente virtual não editável;
telas sem recorte compacto da equipe

**Scale/Scope**: 0 tabelas, 0 operações novas na matriz, 8 rotas
HTTP reusadas, 3 destinos deixam de ser só título, gestão passa a
ver os três no menu, funções puras (filtro por categoria, contagem
ativo/desativado, rótulos). Worker intocado

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Preço vigente mora no item vendável. Nenhum débito, nenhuma consulta ao sistema de gestão |
| II — Na dúvida, humano vê | Intocado. Catálogo inativo e item vendável inativo já saem da fonte do atendimento; a tela só dispara o `PATCH` de `ativo` |
| III — Gravar antes de enviar | Salvar o recado **não** envia mensagem. O envio continua no clique de chegada já existente |
| IV — Fila como verdade | Sem push. Recarregar e “tentar de novo” consultam os GET já existentes |
| V — Ausência humana visível | Campo vazio no recado continua bloqueando o envio na chegada (já na fila). Falha de leitura ≠ lista vazia |
| VI — Confirmação antes de tramitar | Intocado. Esta fatia não abre chamado nem consumo |
| VII — Não ser intrusivo | Sem recado proativo novo |
| VIII — Minimização | Operação recusada nas três telas, zero fetch. Log sem texto do fato, sem preço livre, sem valor do recado |
| IX — Garantias no banco | `DELETE` de catálogo continua `405`. Unique de nome ativo e CHECK de preço permanecem no servidor. A tela não inventa apagar |
| X — Portas trocáveis | Intocado. A tela não instancia LLM nem mensageria |
| XI — Complexidade exige problema | Sem rota nova, sem lib de estado, sem Playwright, sem campo `descricao`. Três componentes + destinos da gestão são o problema presente (ainda só título) |
| XII — Teste primeiro | Cada FR com teste que falha por ausência (Vitest na tela; pytest só regressão — HTTP não muda) |
| XIII — Parâmetro não é constante | Nenhum prazo novo. Os quatro textos já vivem em `parametro_hotel` |
| XIV — Multi-tenant | `id_hotel` da sessão; a tela não pede hotel. Item alheio continua `404` |
| XV — Honestidade | Salvar não afirma que o hóspede recebeu. Desativar não afirma apagamento. Sem prévia com nome inventado |

**Ponto de atenção 1 — gestão lê a tela; a matriz já permitia a
leitura.** `ler_catalogo` e `ler_texto_de_boas_vindas` incluem
`gestor`. A casca **hoje** omite os três destinos da gestão. Esta
fatia acrescenta `gestor` em `perfis` e monta as telas em modo
leitura (`somenteLeitura`). Staff continua redirecionado; **zero**
fetch. Não “esconder com CSS”.

**Ponto de atenção 2 — testes da casca.** `Casca.test.tsx` hoje
afirma que `/catalogo` é só título, sem tabela. Essa asserção
**quebra de propósito**. `fetchPorPerfil` precisa responder `GET
/catalogo`, `GET /itens-vendaveis` e `GET /propriedade/boas-vindas`
(`200` com lista/campos vazios no mínimo). Staff nesses endereços:
casca redireciona; **zero** GET. Gestão: GET de leitura, **zero**
POST/PATCH/PUT.

**Ponto de atenção 3 — proxy Vite.** `/catalogo` e `/propriedade`
já estão no proxy. `/itens-vendaveis` **não**. Sem essa linha, a
tela de itens vendáveis no `npm run dev` fala com o Vite, não com
a API. É ajuste de frontend, não rota nova.

**Ponto de atenção 4 — formato do recado é da API.** A tela **não**
reimplementa quebra de linha / tabulação / cinco espaços. Envia o
`PUT` e mostra o `422`. Duplicar a regra no cliente arrisca recusar
o que a API aceita (FR-015).

**Ponto de atenção 5 — categoria na criação.** `POST /catalogo`
exige `categoria`. A tela envia a chave da aba visível
(`horario` · `cardapio` · `servico` · `programacao` · `regra`).
`PATCH` **não** manda `categoria` (a API recusa).

**Ponto de atenção 6 — worker e atendimento.** Desativar pela tela
é o mesmo `PATCH`/`ativo` que o atendimento já respeita. Esta
fatia **não** chama `GET /catalogo/ativo` nem a porta de LLM.
SC-003 não reabre a suíte de F2.1/F3.7.

**Ponto de atenção 7 — botões, não a linha.** Criar, salvar,
desativar e reativar só no `<button>` rotulado. Sem `DELETE`.
Gestão não vê esses botões.

## Project Structure

### Documentation (this feature)

```text
specs/034-catalogo-vendaveis-recado/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-reusada.md
│   ├── superficie-catalogo.md
│   ├── superficie-vendaveis.md
│   ├── superficie-boas-vindas.md
│   ├── destinos-e-perfis.md
│   └── logs.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks
```

### Source Code (repository root)

```text
app/                                 # intocado nas regras
└── modulos/propriedade/             # GET/POST/PATCH catálogo,
                                     # GET/POST/PATCH itens-vendáveis,
                                     # GET/PUT boas-vindas

frontend/vite.config.ts              # proxy + /itens-vendaveis
frontend/src/painel/
├── destinos.ts                      # catalogo, vendaveis, boas-vindas:
│                                    # perfis recepcao + gestor
├── Casca.tsx                        # três destinos → telas reais;
│                                    # somenteLeitura se gestor
├── TelaCatalogo.tsx
├── TelaVendaveis.tsx
├── TelaBoasVindas.tsx
├── catalogo.ts                      # tipos, categorias, filtro, contagem
├── vendaveis.ts                     # tipos, formatação de preço
├── TelaCatalogo.test.tsx
├── TelaVendaveis.test.tsx
├── TelaBoasVindas.test.tsx
├── Casca.test.tsx                   # mock GET; gestão lê; staff zero fetch
├── destinos.test.ts                 # gestor pode os três; staff não
├── catalogo.test.ts
└── vendaveis.test.ts

testes/                              # regressão já verde; sem arquivo novo
```

**Structure Decision**: estende o `frontend/` da F8.1–F8.5. Sem
módulo Python novo, sem worker, sem segundo app. Os destinos
`catalogo`, `vendaveis` e `boas-vindas` deixam de ser
`TelaNomeada`. `TelaNomeada` permanece em indicadores, mercado,
usuários e retenção (F8.7).

## Complexity Tracking

> Nenhum item: o Constitution Check passou nas duas passagens.
> Vitest e três componentes estão justificados no Artigo XI
> (problema presente: Catálogo, Itens vendáveis e Recado de
> boas-vindas ainda são só título).
