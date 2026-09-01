---
description: "Task list for feature implementation"
---

# Tasks: Catálogo, itens vendáveis e recado de boas-vindas

**Input**: Design documents from `/specs/034-catalogo-vendaveis-recado/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md),
[research.md](./research.md), [data-model.md](./data-model.md),
[contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma
linha de produção sem teste que falhe antes pelo motivo certo. Nenhum
teste abre navegador (Playwright fora). Nenhum teste chama PMS,
WhatsApp ou IA. `fetch` é falso no Vitest. pytest só como regressão
já verde (catálogo, item vendável, boas-vindas, sessão).

**Organization**: Tarefas agrupadas por história (US1–US5), na ordem
da spec. Tipos + filtro de categoria + formatação de preço entram na
Foundational. US1 é o MVP (recepção mantém o catálogo). US2 itens
vendáveis. US3 recado. US4 gestão lê / operação recusada. US5
desativar sem apagar e sem chamar o catálogo ativo. Sem migração.
Sem operação nova na matriz. Sem alterar backend. Worker intocado.
Python de propriedade intocado.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US5)

## Como ver os testes falharem nesta fatia

**Funções puras.** Sem `catalogo.ts` / `vendaveis.ts`, os unitários
falham com módulo ausente. Filtro que mistura categoria, contagem
que inventa número, ou preço embutido no nome: falha.

**Catálogo.** Sem `TelaCatalogo`, `/app/catalogo` continua o `<h1>`
da `TelaNomeada`. Vitest que procura abas, título/conteúdo e
**Desativar** não acha. Botão **Apagar** ou `DELETE`: falha.
`POST` com categoria de outra aba: falha. `PATCH` com `categoria`:
falha. `GET` 500 mostrando “nenhum item”: falha da US1.

**Vendáveis.** Coluna ou campo “descrição”: falha. Editar preço
reescrevendo o nome no mesmo controle: falha. `409` que some o
item por otimismo: falha.

**Recado.** Três campos sem convite: falha. **Salvar** que dispara
`POST /reservas/.../chegada` ou afirma envio: falha. `422` que
substitui os valores já carregados: falha. Validar cinco espaços
no cliente de um jeito que recuse o que a API aceita: falha da
FR-015.

**Perfil.** Staff em `/app/catalogo` que dispara `GET /catalogo`:
falha da US4. Gestão com **+ Novo item** ou **Salvar**: falha.
Menu da gestão sem os três destinos: falha.

**Casca.** Ao ligar as telas, `Casca.test.tsx` precisa dos mocks
`GET /catalogo`, `GET /itens-vendaveis` e
`GET /propriedade/boas-vindas`. Sem isso a US1 “quebra” a casca
com estado de falha — T001 existe para isso. O teste “recepção em
/catalogo vê só o título” deixa de valer na T010.

---

## Phase 1: Setup

**Purpose**: o `frontend/` da F8.1–F8.5 já tem router, Tailwind,
Vitest e proxy `/catalogo` e `/propriedade`. Esta fase evita
regressão da casca quando as três telas passarem a buscar dados, e
liga o prefixo que o Vite ainda não encaminha. Sem npm novo. Sem
Python.

- [X] T001 Em `frontend/src/painel/Casca.test.tsx`, o `fetch` falso
      de `fetchPorPerfil` responde `GET /catalogo` com `200` e
      `{itens:[]}`, `GET /itens-vendaveis` com `200` e `{itens:[]}`
      e `GET /propriedade/boas-vindas` com `200` e os quatro
      campos (`cafe`, `wifi`, `checkout`, `convite`) como string
      vazia ou texto curto. Rodar `npm test` em `frontend/` —
      permanece verde com `TelaNomeada` nos três destinos. Sem
      implementar as telas novas
      ([plan.md](./plan.md) ponto de atenção 2)
- [X] T002 [P] Em `frontend/vite.config.ts`, acrescentar
      `"/itens-vendaveis"` no `server.proxy` apontando para a
      mesma `api` de `/catalogo`. Sem mudar `base`. Sem rota
      FastAPI nova
      ([research.md](./research.md) §7)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: chaves de categoria, filtro da aba, contagem
ativo/desativado e tipo/preço do item vendável, testáveis sem DOM
das telas novas. **Nenhuma tela operacional ainda.** Gestão ainda
não entra em `perfis` (isso é US4).

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase.

- [X] T003 Unitários em `frontend/src/painel/catalogo.test.ts`:
      as cinco chaves `horario` · `cardapio` · `servico` ·
      `programacao` · `regra` com rótulos Horários, Cardápio,
      Serviços, Programação, Regras; `itensDaCategoria` devolve
      só a chave pedida, na ordem do array (sem `sort`);
      `contarSituacao` devolve ativos e desativados daquele
      recorte (0/0 em lista vazia). Rodar `npm test` em
      `frontend/` e **ver falhar**
      ([data-model.md](./data-model.md),
      [contracts/superficie-catalogo.md](./contracts/superficie-catalogo.md))
- [X] T004 Criar `frontend/src/painel/catalogo.ts`: tipo
      `ItemCatalogo` com os campos de
      [contracts/api-reusada.md](./contracts/api-reusada.md),
      constante das categorias, `itensDaCategoria`,
      `contarSituacao` até T003 verde. Sem JSX. Sem `fetch`
- [X] T005 [P] Unitários em `frontend/src/painel/vendaveis.test.ts`:
      tipo com `id_item_vendavel`, `nome`, `preco_atual`, `ativo`
      — **sem** campo `descricao`; `formatarPreco` aceita número
      ou string e mostra duas casas; lista de teste **não** contém
      a palavra “descrição” como coluna. Rodar e **ver falhar**
      ([contracts/superficie-vendaveis.md](./contracts/superficie-vendaveis.md))
- [X] T006 Criar `frontend/src/painel/vendaveis.ts`: tipo
      `ItemVendavel` e `formatarPreco` até T005 verde. Sem JSX.
      Sem `fetch`

**Checkpoint**: `npm test` verde nas funções puras. Destinos
`catalogo`, `vendaveis` e `boas-vindas` ainda são título. Menu da
gestão ainda sem os três.

---

## Phase 3: User Story 1 - Manter o catálogo por categoria (Priority: P1) 🎯 MVP

**Goal**: Catálogo lista o `GET /catalogo` em cinco abas, com
título, conteúdo, situação, contagem da aba, criar na categoria
visível, editar sem mandar `categoria`, desativar/reativar sem
apagar. Vazio ≠ falha de leitura. Prop `somenteLeitura` existe e
defaulta falso (gestão ainda não monta esta tela).

**Independent Test**: Vitest — mock com itens em duas categorias,
ativos e inativos; abas com os cinco rótulos; só a aba visível
mostra seus itens; **+ Novo item** faz `POST /catalogo` com a
chave da aba; **Editar** faz `PATCH` sem `categoria`; **Desativar**
`{ativo:false}`; **Reativar** `{ativo:true}`; zero **Apagar** e
zero `DELETE`; `itens:[]` é vazio explícito; `GET` 500 não usa o
estado vazio.

### Tests for User Story 1

- [X] T007 [US1] Vitest em `frontend/src/painel/TelaCatalogo.test.tsx`:
      ao montar, `GET /catalogo` com `credentials: "include"`;
      cinco abas (Horários … Regras); itens da aba `horario`
      visíveis com título, conteúdo e situação; item de
      `cardapio` **não** aparece nessa aba até trocar; resumo da
      aba com `contarSituacao`; linha ativa tem **Editar** e
      **Desativar**; linha desativada tem **Reativar**; **nenhum**
      controle **Apagar**; `MemoryRouter` basename `/app` +
      `fetch` falso. Sem `somenteLeitura`. Rodar e **ver falhar**
      ([contracts/superficie-catalogo.md](./contracts/superficie-catalogo.md),
      [contracts/api-reusada.md](./contracts/api-reusada.md))
- [X] T008 [US1] No mesmo `frontend/src/painel/TelaCatalogo.test.tsx`:
      **+ Novo item** na aba Cardápio → `POST /catalogo` com
      `categoria: "cardapio"`, título e conteúdo; `201` → novo
      `GET /catalogo`; **Editar** → `PATCH /catalogo/{id}` **sem**
      `categoria`; **Desativar** → `{ativo:false}` e GET; clique
      no texto da linha → zero POST/PATCH; `200` + `itens:[]` →
      vazio da aba, sem recado de falha; `GET` 500 → declara que
      não carregou, tentar de novo, **não** mostra vazio;
      `422` no POST mostra o `detail` e nada some por otimismo.
      Rodar e **ver falhar**

### Implementation for User Story 1

- [X] T009 [US1] Criar `frontend/src/painel/TelaCatalogo.tsx`: no
      mount `pedirAutenticado("/catalogo")`; abas; filtro com
      `itensDaCategoria`; criar/editar/desativar/reativar como o
      contrato; `somenteLeitura?: boolean` default falso — quando
      verdadeiro, esconde novo/editar/desativar/reativar (US4
      usa; testes desta história não passam a prop). Sem
      `DELETE`. Sem `GET /catalogo/ativo`. Título **Catálogo**.
      Até T007 e T008 verdes
- [X] T010 [US1] Em `frontend/src/painel/Casca.tsx`,
      `destino.id === "catalogo"` renderiza `TelaCatalogo` em vez
      de `TelaNomeada`. Em `Casca.test.tsx`, substituir o caso
      “recepção em /catalogo vê só o título Catálogo” (sem
      tabela) por asserção de que o título **Catálogo** permanece
      e o destino deixou de ser tela nomeada vazia (lista ou
      estado vazio honesto). Gestão e staff ainda redirecionam
      neste checkpoint. Rodar `npm test` em `frontend/`

**Checkpoint**: recepção mantém o catálogo. Itens vendáveis e
recado ainda são título.

---

## Phase 4: User Story 2 - Itens vendáveis com preço próprio (Priority: P1)

**Goal**: Itens vendáveis lista nome, preço em campo próprio e
situação; cadastra; altera preço sem reescrever o nome; desativa
sem apagar; `409` visível.

**Independent Test**: Vitest — lista sem coluna descrição; **+
Novo item** POST `nome` + `preco_atual`; editar só o preço manda
PATCH sem `nome`; desativar/reativar; zero `DELETE`.

### Tests for User Story 2

- [X] T011 [US2] Vitest em `frontend/src/painel/TelaVendaveis.test.tsx`:
      ao montar, `GET /itens-vendaveis` com `credentials:
      "include"`; cada linha mostra `nome`, preço via
      `formatarPreco` e situação; **nenhuma** coluna ou campo
      `descrição`; linha ativa **Editar** + **Desativar**; linha
      inativa **Reativar**; zero **Apagar**. `200` + `itens:[]`
      vazio honesto; `GET` 500 ≠ vazio. `MemoryRouter` basename
      `/app`. Rodar e **ver falhar**
      ([contracts/superficie-vendaveis.md](./contracts/superficie-vendaveis.md))
- [X] T012 [US2] No mesmo `frontend/src/painel/TelaVendaveis.test.tsx`:
      novo item → `POST /itens-vendaveis` com `nome` e
      `preco_atual` em campos separados; `201` → GET de novo;
      editar só o preço → `PATCH` corpo **sem** `nome`; `409`
      mostra o detalhe da API e o item não some; `422` (preço
      negativo / nome vazio) visível ao salvar. Clique na linha
      zero POST/PATCH. Rodar e **ver falhar**

### Implementation for User Story 2

- [X] T013 [US2] Criar `frontend/src/painel/TelaVendaveis.tsx`:
      GET/POST/PATCH de
      [contracts/api-reusada.md](./contracts/api-reusada.md);
      `somenteLeitura` default falso; sem descrição; sem
      `DELETE`. Título **Itens vendáveis**. Até T011 e T012
      verdes
- [X] T014 [US2] Em `frontend/src/painel/Casca.tsx`,
      `destino.id === "vendaveis"` renderiza `TelaVendaveis`.
      Rodar `npm test` em `frontend/`

**Checkpoint**: recepção mantém fatos e preços. Recado ainda é
título.

---

## Phase 5: User Story 3 - Quatro campos do recado, recusa ao salvar (Priority: P1)

**Goal**: Recado de boas-vindas mostra café, wi-fi, horário de
saída e convite; um **Salvar** faz `PUT` dos quatro; `422` visível
sem alterar o já carregado; salvar não dispara chegada nem
mensagem.

**Independent Test**: Vitest — quatro rótulos; PUT com os quatro
chaves; `200` usa o corpo; `422` mantém valores anteriores; zero
`POST` de chegada; sem campo de aviso de assistente virtual.

### Tests for User Story 3

- [X] T015 [US3] Vitest em `frontend/src/painel/TelaBoasVindas.test.tsx`:
      ao montar, `GET /propriedade/boas-vindas` com
      `credentials: "include"`; quatro campos rotulados Café da
      manhã, Wi-fi, Horário de saída, Convite ligados a `cafe`,
      `wifi`, `checkout`, `convite`; um botão **Salvar**; clique →
      `PUT` com os quatro; `200` mostra os valores do corpo;
      **nenhum** `POST` contendo `/chegada`; nenhum rótulo de
      assistente virtual editável. `MemoryRouter` basename `/app`.
      Rodar e **ver falhar**
      ([contracts/superficie-boas-vindas.md](./contracts/superficie-boas-vindas.md),
      [contracts/api-reusada.md](./contracts/api-reusada.md))
- [X] T016 [US3] No mesmo `frontend/src/painel/TelaBoasVindas.test.tsx`:
      `422` (detail string) aparece visível, os quatro valores
      carregados no GET **permanecem**; GET 500 → declara que não
      carregou, tentar de novo, **não** trata campos vazios como
      recado da casa. A tela **não** precisa recusar cinco
      espaços no cliente — o `422` da API basta. Rodar e **ver
      falhar**

### Implementation for User Story 3

- [X] T017 [US3] Criar `frontend/src/painel/TelaBoasVindas.tsx`:
      GET + PUT atômico; `somenteLeitura` default falso esconde
      **Salvar**; sem prévia com nome; sem validar formato além
      do que a API devolve. Título **Recado de boas-vindas**. Até
      T015 e T016 verdes
- [X] T018 [US3] Em `frontend/src/painel/Casca.tsx`,
      `destino.id === "boas-vindas"` renderiza `TelaBoasVindas`.
      Rodar `npm test` em `frontend/`

**Checkpoint**: as três telas existem para a recepção. Gestão ainda
não as vê no menu.

---

## Phase 6: User Story 4 - Gestão lê; equipe operacional nem chega (Priority: P1)

**Goal**: os três destinos entram no menu da gestão em modo
leitura; staff continua recusado, com **zero** fetch destas rotas.

**Independent Test**: Vitest — `perfilPode("gestor", "/app/catalogo")`
verdadeiro; staff falso; gestão vê os três links, GET de leitura,
sem **+ Novo item** / **Editar** / **Desativar** / **Salvar**;
staff em `/app/catalogo` (e vendáveis, boas-vindas) cai na casa e
não chama esses GET.

### Tests for User Story 4

- [X] T019 [P] [US4] Em `frontend/src/painel/destinos.test.ts`:
      `perfilPode("gestor", …)` verdadeiro para `/app/catalogo`,
      `/app/vendaveis` e `/app/boas-vindas`;
      `perfilPode("staff", …)` falso nos três;
      `perfilPode("recepcao", …)` permanece verdadeiro. Rodar e
      **ver falhar**
      ([contracts/destinos-e-perfis.md](./contracts/destinos-e-perfis.md))
- [X] T020 [US4] Estender `frontend/src/painel/Casca.test.tsx`:
      gestão autenticada vê links **Catálogo**, **Itens
      vendáveis** e **Recado de boas-vindas**; em `/app/catalogo`
      dispara `GET /catalogo` e **não** vê **+ Novo item** nem
      **Desativar**; em `/app/boas-vindas` dispara o GET do recado
      e **não** vê **Salvar**; staff em `/app/catalogo`,
      `/app/vendaveis` e `/app/boas-vindas` — título da casa
      (Meus chamados), **zero** GET `/catalogo`,
      `/itens-vendaveis` e `/propriedade/boas-vindas`. Rodar e
      **ver falhar**

### Implementation for User Story 4

- [X] T021 [US4] Em `frontend/src/painel/destinos.ts`, os três
      destinos passam a `perfis: ["recepcao", "gestor"]`. Até
      T019 verde. Sem mudar casas nem destinos da F8.7
- [X] T022 [US4] Em `frontend/src/painel/Casca.tsx`, ao montar as
      três telas passar `somenteLeitura={sessao.perfil ===
      "gestor"}`. Staff continua no `Navigate` (não está em
      `perfis`). Até T020 verde. Não mudar `politica.py`. Rodar
      `npm test` em `frontend/`

**Checkpoint**: os três perfis só vêem a superfície que a spec
permite.

---

## Phase 7: User Story 5 - Desativar some do atendimento, não do histórico (Priority: P2)

**Goal**: a tela não oferece apagar; desativar é `PATCH` `ativo`;
nenhuma destas telas chama `GET /catalogo/ativo` (a omissão no
atendimento já é da F2.1/F3.7).

**Independent Test**: Vitest — após **Desativar**, o item segue na
lista de manutenção como desativado; zero chamada `DELETE` e zero
`GET /catalogo/ativo` em catálogo e vendáveis.

### Tests for User Story 5

- [X] T023 [US5] Em `frontend/src/painel/TelaCatalogo.test.tsx` e
      `frontend/src/painel/TelaVendaveis.test.tsx`: depois do
      PATCH `ativo: false` e do GET seguinte, o item permanece
      visível como desativado; o `fetch` mock **não** registra
      método `DELETE` nem URL `/catalogo/ativo`. Rodar e **ver
      falhar** se a implementação chamar essas rotas
      ([research.md](./research.md) §1 e §6)

### Implementation for User Story 5

- [X] T024 [US5] Ajustar `frontend/src/painel/TelaCatalogo.tsx`
      e/ou `frontend/src/painel/TelaVendaveis.tsx` só se T023
      falhar. Não acrescentar GET de catálogo ativo. Até T023
      verde. Rodar `npm test` em `frontend/`

**Checkpoint**: desativar é o único caminho visível. Suíte de
atendimento automático **não** é reescrita.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: log, nomenclatura, estado do projeto, suíte.

- [X] T025 [P] Varredura em `frontend/src/painel/TelaCatalogo.tsx`,
      `frontend/src/painel/TelaVendaveis.tsx`,
      `frontend/src/painel/TelaBoasVindas.tsx`,
      `frontend/src/painel/catalogo.ts` e
      `frontend/src/painel/vendaveis.ts`: zero `console.log` de
      `itens`, título, conteúdo, preço ou recado; zero controle
      **Apagar**; zero coluna “descrição” em vendáveis; telas sem
      `compacto` da equipe
      ([contracts/logs.md](./contracts/logs.md))
- [X] T026 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F8.6
      concluída quando o quickstart passar; próxima fatia F8.7
      (cortada como escopo da semana, se ainda for o caso). Sem
      inventar integração PMS. Registrar que o mapa de telas com
      “descrição” no item vendável não foi seguido
- [X] T027 Rodar `npm test` em `frontend/` e, na raiz,
      `pytest testes/unitarios -q` mais
      `pytest testes/integracao -q -k "catalogo or vendavel or boas_vindas or sessao"`.
      Tudo verde. Conferir o roteiro de
      [quickstart.md](./quickstart.md) (casos Vitest cobertos;
      `npm run dev` + proxy de itens vendáveis; browser só como
      checagem humana, não tarefa de Playwright)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: começa agora — mock da casca + proxy
- **Foundational (Phase 2)**: depende do Setup — **bloqueia** as histórias
- **US1 (Phase 3)**: depois da Foundational — MVP
- **US2 (Phase 4)**: depois da Foundational; na prática depois da
  US1 para o `Casca.tsx` não conflitar
- **US3 (Phase 5)**: depois da Foundational; `Casca.tsx` depois da
  US2
- **US4 (Phase 6)**: depois de T010, T014 e T018 (as três telas
  existem para receber `somenteLeitura`)
- **US5 (Phase 7)**: depois da US1 e da US2 (os PATCH de `ativo`)
- **Polish**: depois das histórias desejadas

### User Story Dependencies

- **US1**: só Foundational
- **US2**: Foundational; Casca depois da US1
- **US3**: Foundational; Casca depois da US2
- **US4**: US1 + US2 + US3
- **US5**: US1 + US2

### Within Each User Story

- Testes **primeiro**, ver falhar, depois o mínimo para verde
- Função pura antes do JSX que a usa
- História completa antes de avançar prioridade

### Parallel Opportunities

- T001 (Casca.test mocks) em paralelo com T002 (vite.config)
- T003 (catalogo.test) em paralelo com T005 (vendaveis.test)
- T007 e T008 são o mesmo arquivo: **não** paralelizar entre si
- T011 e T012 idem
- T015 e T016 idem
- T019 (destinos.test) em paralelo com T020 (Casca.test) depois das
  três telas, mas T021/T022 sequenciais
- T025 e T026 no polish

---

## Parallel Example: depois da Foundational

```text
# US1 (sequencial no mesmo par teste/tela):
Task: T007 TelaCatalogo.test.tsx abas + lista
Task: T008 TelaCatalogo.test.tsx criar/editar/desativar + vazio ≠ falha
Task: T009 TelaCatalogo.tsx
Task: T010 Casca.tsx catalogo

# Telas US2/US3 podem ser escritas em arquivos próprios;
# ligar na Casca só depois, em fila:
Task: T011 TelaVendaveis.test.tsx
Task: T013 TelaVendaveis.tsx
Task: T014 Casca.tsx vendaveis
```

T007 e T008 são o mesmo arquivo: **não** paralelizar entre si.
US1–US3 não paralelizam o `Casca.tsx`.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: recepção vê e mantém o Catálogo. Vendáveis, recado e
   menu da gestão ainda não

### Incremental Delivery

1. Setup + Foundational
2. US1 → demo do catálogo por categoria
3. US2 → demo do preço próprio
4. US3 → demo do recado (recusa ao salvar)
5. US4 → gestão lê; staff recusado
6. US5 → desativar sem apagar / sem catálogo ativo na tela
7. Polish + estado do projeto

### Parallel Team Strategy

Um desenvolvedor (prazo da semana): ordem US1 → US2 → US3 → US4 →
US5. Não paralelizar a ligação na `Casca.tsx`.

---

## Notes

- [P] só com arquivos distintos e dependência já verde
- Sem Playwright, sem `politica.py`, sem Alembic, sem worker, sem
  campo `descricao`, sem `GET /catalogo/ativo` na tela
- Formato do recado: a API é a fonte da verdade (não duplicar a
  regra no cliente)
- Gestão no menu só na US4; até lá os três destinos continuam só
  recepção
- Commit por história (não por tarefa) salvo o usuário pedir o
  contrário — o ciclo TDD da casa é teste → falha → código → verde
