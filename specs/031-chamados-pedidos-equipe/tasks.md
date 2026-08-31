---
description: "Task list for feature implementation"
---

# Tasks: Chamados, pedidos e a tela da equipe

**Input**: Design documents from `/specs/031-chamados-pedidos-equipe/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md),
[research.md](./research.md), [data-model.md](./data-model.md),
[contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma
linha de produção sem teste que falhe antes pelo motivo certo. Nenhum
teste abre navegador (Playwright fora). Nenhum teste chama PMS,
WhatsApp ou IA. `fetch` é falso no Vitest. pytest só como regressão
já verde (solicitação, resolução, sessão, casca).

**Organization**: Tarefas agrupadas por história (US1–US6), na ordem
da spec. Tipos + natureza + tempo decorrido entram na Foundational.
US1 é o MVP (recepção vê a lista). US2 é a casa da equipe. US3 liga
Resolvido. US4 trava a ficha. US5 compacto e sessão. US6 isolamento
e falha ≠ vazio na equipe (a recepção já cobre na US1). Sem
migração. Sem operação nova na matriz. Worker intocado. Python de
atendimento intocado.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US6)

## Como ver os testes falharem nesta fatia

**Natureza e tempo.** Sem `rotuloNatureza` / `tempoDecorrido`,
`solicitacoes.test.ts` falha com módulo ausente. `tipo: "servico"`
rotulado igual a reclamação: falha até os três rótulos distintos.
Item de 3 h atrás sem “há 3 h”: falha.

**Lista da recepção.** Sem `TelaAlertas`, `/app/alertas` continua o
`<h1>` da `TelaNomeada`. Vitest que procura “reclamação” e **Ver
ficha** não acha. Nome do hóspede na linha (se o mock não o envia,
não deve aparecer texto inventado). `GET` 500 mostrando “nada
aberto”: falha da US1.

**Casa da equipe.** Sem `TelaChamados`, o título existe mas não há
cartão nem **Resolvido**. Link **Ver ficha** na equipe: falha da
US2/US4. Consumo omitido: falha da clarificação.

**Resolver.** Clique em **Ver ficha** ou na descrição que dispara
`POST .../resolucao`: falha da US3. Sem segundo diálogo: o teste
não deve procurar “tem certeza”. `200` sem `GET` seguinte (item
continua na tela): falha. `409` que some o item: falha.

**Perfil.** Staff em `/app/alertas` que dispara `GET /solicitacoes`
(tela da recepção montada): falha da US6. Staff em `/app/ficha/1`
que dispara GET de ficha: falha da US4 (já coberto na F8.3; não
regredir).

**Casca.** Ao ligar as telas, `Casca.test.tsx` que abre `/app/chamados`
ou `/app/alertas` precisa do mock `GET /solicitacoes` `200 {itens:[]}`.
Sem isso a US1/US2 “quebra” a casca com estado de falha — T001 existe
para isso.

---

## Phase 1: Setup

**Purpose**: o `frontend/` da F8.1–F8.3 já tem router, Tailwind,
Vitest e proxy `/solicitacoes`. Esta fase só evita regressão da
casca quando as duas telas passarem a buscar dados. Sem npm novo.
Sem Python.

- [x] T001 Em `frontend/src/painel/Casca.test.tsx`, o `fetch` falso
      de `fetchPorPerfil` responde `GET /solicitacoes` com `200` e
      `{itens:[]}` (além do que já responde para fila/ficha). Rodar
      `npm test` em `frontend/` — permanece verde com `TelaNomeada`
      nesses destinos. Sem implementar `TelaAlertas` nem
      `TelaChamados`
      ([plan.md](./plan.md) ponto de atenção 2)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: tipo do item, rótulo de natureza e tempo decorrido,
testáveis sem DOM. **Nenhuma tela operacional ainda.**

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase.

- [x] T002 Unitários em `frontend/src/painel/solicitacoes.test.ts`:
      `rotuloNatureza("reclamacao")` / `"servico"` / `"consumo"`
      devolvem três strings distintas em português (reclamação,
      serviço, consumo); valor desconhecido não inventa rótulo de
      outra natureza. `tempoDecorrido(abertaEm, agora)` — 30 s →
      fala em menos de 1 min; 3 min → contém “3” e “min”; 3 h →
      contém “3” e “h”; 2 d → contém “2” e “d”; não usa as palavras
      “extrato” nem “conta”. Rodar `npm test` em `frontend/` e
      **ver falhar**
      ([data-model.md](./data-model.md),
      [contracts/superficie-da-recepcao.md](./contracts/superficie-da-recepcao.md))
- [x] T003 Criar `frontend/src/painel/solicitacoes.ts`: tipo
      `ItemSolicitacao` com os campos de
      [contracts/api-reusada.md](./contracts/api-reusada.md),
      `rotuloNatureza` e `tempoDecorrido(abertaEm, agora)` até T002
      verde. Sem JSX. Sem `fetch`. Sem `sort`

**Checkpoint**: `npm test` verde nas funções puras. Destinos
`alertas` e `chamados` ainda são título.

---

## Phase 3: User Story 1 - A recepção vê o que está aberto (Priority: P1) 🎯 MVP

**Goal**: Chamados e pedidos lista o `GET /solicitacoes`: três
naturezas, tempo decorrido, mais antigos primeiro, sem nome,
**Ver ficha** para `/ficha/{id_reserva}` inclusive sem quarto.
Vazio ≠ falha de leitura. Sem **Resolvido** ainda.

**Independent Test**: Vitest — mock com reclamação, serviço e
consumo + um resolvido ausente do JSON; a tela mostra os três, o
primeiro do array no topo, **Ver ficha** em cada um (href
`/ficha/{id}`), nenhum nome/telefone/documento, consumo com valor,
reclamação destacada só se `destaque_tempo_excedido`. `itens:[]`
é vazio explícito. `GET` 500 não usa o estado vazio.

### Tests for User Story 1

- [x] T004 [US1] Vitest em `frontend/src/painel/TelaAlertas.test.tsx`:
      ao montar, `GET /solicitacoes` com `credentials: "include"`;
      renderiza os três `rotuloNatureza`, descrição, quarto (ou
      ausência perceptível), `tempoDecorrido` com `agora` fixo no
      teste; primeiro item do JSON aparece antes do último;
      **Ver ficha** com `href` terminando em `/ficha/{id_reserva}`;
      item sem `numero_quarto` **ainda** tem esse link; **nenhum**
      texto de nome/telefone/documento; consumo mostra valor; item
      com `destaque_tempo_excedido: true` tem sinal distinto; serviço
      antigo sem a flag **não** usa esse sinal. Sem botão Resolvido
      nesta história. `MemoryRouter` basename `/app` + `fetch`
      falso. Rodar e **ver falhar**
      ([contracts/superficie-da-recepcao.md](./contracts/superficie-da-recepcao.md),
      [contracts/api-reusada.md](./contracts/api-reusada.md))
- [x] T005 [US1] No mesmo `frontend/src/painel/TelaAlertas.test.tsx`:
      `200` + `itens:[]` → estado de lista vazia, sem copiar o recado
      de falha; `GET` 500 (ou rede) → declara que a lista não
      carregou, oferece tentar de novo, **não** mostra o estado
      vazio; segundo `GET` 200 recupera a lista. Rodar e **ver
      falhar**

### Implementation for User Story 1

- [x] T006 [US1] Criar `frontend/src/painel/TelaAlertas.tsx`: no
      mount chama `pedirAutenticado("/solicitacoes")`; lista na
      ordem do array; natureza, tempo, **Ver ficha** (`Link` para
      `/ficha/{id_reserva}`); estados vazio, carregando e falha
      como o contrato. Sem `POST`. Sem nome inventado. Título
      **Chamados e pedidos**. Até T004 e T005 verdes
- [x] T007 [US1] Em `frontend/src/painel/Casca.tsx`,
      `destino.id === "alertas"` renderiza `TelaAlertas` em vez de
      `TelaNomeada`. Casos de `Casca.test.tsx` que abrem `/app/alertas`
      como recepção continuam achando o título (T001). Rodar
      `npm test` em `frontend/`

**Checkpoint**: recepção vê a lista de verdade e abre a ficha. A
equipe ainda é título. Resolver ainda não.

---

## Phase 4: User Story 2 - A equipe vê o trabalho no celular, sem ficha (Priority: P1)

**Goal**: Meus chamados (casa do staff) lista as três naturezas,
incluindo consumo, um cartão por item, sem cadastral e sem **Ver
ficha**. Sem `POST` ainda.

**Independent Test**: Vitest — mock com as três naturezas; cartões
com natureza, tempo, quarto, descrição, valor no consumo; query
por nome/telefone/documento vazia; nenhum `link` para `/ficha/`;
`itens:[]` ≠ GET 500.

### Tests for User Story 2

- [x] T008 [US2] Vitest em `frontend/src/painel/TelaChamados.test.tsx`:
      ao montar, `GET /solicitacoes` com `credentials: "include"`;
      as três naturezas visíveis (consumo incluso); ordem do array;
      `tempoDecorrido`; **nenhum** `getByRole("link")` para ficha;
      nenhum nome/telefone/documento; consumo com valor. Compacto:
      cada item é um bloco com a descrição (não exige tabela). Sem
      `POST` nesta história. `MemoryRouter` basename `/app` +
      `fetch` falso. Rodar e **ver falhar**
      ([contracts/superficie-da-equipe.md](./contracts/superficie-da-equipe.md))
- [x] T009 [US2] No mesmo `frontend/src/painel/TelaChamados.test.tsx`:
      vazio ≠ falha de leitura, iguais aos critérios de T005
      (recado distinto, tentar de novo, segundo GET recupera).
      Rodar e **ver falhar**

### Implementation for User Story 2

- [x] T010 [US2] Criar `frontend/src/painel/TelaChamados.tsx`: GET
      no mount; cartões; sem `Link` de ficha; sem `id_reserva`
      visível; estados vazio/carregando/falha. Título **Meus
      chamados**. Padding compacto (`p-4` ou equivalente da
      `TelaNomeada` compacta). Até T008 e T009 verdes
- [x] T011 [US2] Em `frontend/src/painel/Casca.tsx`,
      `destino.id === "chamados"` renderiza `TelaChamados`. Casa do
      staff em `Casca.test.tsx` continua achando o título. Rodar
      `npm test` em `frontend/`

**Checkpoint**: equipe vê a lista sem ficha. Resolver ainda não.

---

## Phase 5: User Story 3 - Resolver confirma e some da lista (Priority: P1)

**Goal**: botão rotulado **Resolvido** nas duas telas; um clique,
sem diálogo, `POST .../resolucao` corpo vazio; depois `GET` de
novo; clique fora não POST; 409 visível e item não some por
otimismo.

**Independent Test**: Vitest — **Resolvido** faz POST com
`credentials: "include"`; GET seguinte sem o id; clique em
descrição ou **Ver ficha** (recepção) zero POST; 409 mostra
motivo e o id permanece até o GET dizer o contrário.

### Tests for User Story 3

- [x] T012 [P] [US3] Em `frontend/src/painel/TelaAlertas.test.tsx`:
      cada item tem **exatamente um** botão **Resolvido**; clique
      nele → `POST /solicitacoes/{id}/resolucao` corpo vazio; em
      `200` um novo `GET /solicitacoes` e o id some; clique em
      **Ver ficha** ou na descrição → zero POST; 409 (já resolvida)
      mostra o detalhe da API, não afirma sucesso, refaz GET.
      Sem texto “tem certeza”. Rodar e **ver falhar**
      ([contracts/api-reusada.md](./contracts/api-reusada.md))
- [x] T013 [P] [US3] Em `frontend/src/painel/TelaChamados.test.tsx`:
      os mesmos critérios de T012 **sem** Ver ficha (não existe);
      clique na descrição zero POST; consumo também tem
      **Resolvido** (não chama `/consumos` nem lançamento). Rodar
      e **ver falhar**

### Implementation for User Story 3

- [x] T014 [US3] Em `frontend/src/painel/TelaAlertas.tsx`, botão
      **Resolvido** (`<button>`), disable enquanto o POST daquele
      id não volta, depois GET. Até T012 verde. **Ver ficha**
      permanece `Link`
- [x] T015 [US3] Em `frontend/src/painel/TelaChamados.tsx`, o mesmo
      gesto até T013 verde. Zero chamada a `/consumos` ou
      `/reservas/.../ficha`. Rodar `npm test` em `frontend/`

**Checkpoint**: as duas telas fecham pendência. Lançar consumo
continua fora.

---

## Phase 6: User Story 4 - A equipe não abre ficha por caminho nenhum (Priority: P1)

**Goal**: Meus chamados sem atalho à ficha; endereço `/ficha/:id` e
`/alertas` recusados ao staff sem GET de ficha nem da lista da
recepção.

**Independent Test**: Vitest — `TelaChamados` sem links `/ficha/`;
`Casca` perfil staff em `/app/ficha/1` e `/app/alertas` não chama
`/reservas/.../ficha` nem monta `TelaAlertas` (logo o GET de
solicitacoes, se ocorrer, é só o da casa `/chamados` após
redirect — em `/alertas` **zero** GET `/solicitacoes` antes do
Navigate).

### Tests for User Story 4

- [x] T016 [US4] Estender `frontend/src/painel/Casca.test.tsx`:
      perfil `staff` em `/app/ficha/1` **não** chama URL contendo
      `/reservas/` e `/ficha` (regressão F8.3); em `/app/alertas`
      **não** monta o título **Chamados e pedidos** e **não** chama
      `GET /solicitacoes` (redirect à casa). Rodar e **ver falhar**
      se `TelaAlertas` montar antes do `Navigate`
      ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))
- [x] T017 [US4] Em `frontend/src/painel/TelaChamados.test.tsx`
      (ou asserção extra): `queryByRole("link", { name: /ficha/i })`
      ausente; `container` sem `href` `/ficha/`. Já deve valer por
      T008; se T015 tiver introduzido link, **ver falhar** e
      corrigir só em `TelaChamados.tsx`

### Implementation for User Story 4

- [x] T018 [US4] Ajustar `frontend/src/painel/Casca.tsx` se T016
      falhar por montar `TelaAlertas` antes do redirecionamento.
      Não mudar `politica.py`. Até T016 e T017 verdes

**Checkpoint**: staff não alcança ficha nem a lista nominada da
recepção por estas telas.

---

## Phase 7: User Story 5 - No celular, sem autenticar a cada chamado (Priority: P1)

**Goal**: Meus chamados utilizável no compacto da casca; recarregar
não pede senha; segundo Resolvido na mesma sessão não chama
`POST /sessoes`.

**Independent Test**: Vitest — casca staff recarrega `/chamados` com
sessão e vê o título sem `/entrar`; dois Resolvidos seguidos só
`POST .../resolucao` (zero `POST /sessoes`); botão visível no
cartão (não depende de célula fora da vista).

### Tests for User Story 5

- [x] T019 [US5] Estender `frontend/src/painel/Casca.test.tsx`:
      perfil `staff`, sessão válida, rota `/app/chamados` — título
      **Meus chamados**, **Sair** visível, menu de destinos da
      recepção **ausente** (compacto já F8.1). Não deve ir a
      `/entrar`. Rodar — se já verde, manter; se a `TelaChamados`
      quebrar o título, **ver falhar** e corrigir
- [x] T020 [US5] Em `frontend/src/painel/TelaChamados.test.tsx`:
      dois cliques **Resolvido** em ids distintos na mesma montagem
      → dois POST de resolução, **zero** `POST /sessoes`. Rodar e
      **ver falhar** se a tela reautenticar

### Implementation for User Story 5

- [x] T021 [US5] Ajustes só em `frontend/src/painel/TelaChamados.tsx`
      ou `frontend/src/painel/Casca.tsx` se T019 ou T020 falharem.
      Não alterar prazo de sessão nem `politica.py`. Até T019 e
      T020 verdes

**Checkpoint**: sessão longa da F8.1 intacta no fluxo de resolver.

---

## Phase 8: User Story 6 - Isolamento e estados que não se confundem (Priority: P2)

**Goal**: gestão não opera estas telas; recepção não vê Meus
chamados; falha da equipe já coberta na US2 — reforçar gestão.

**Independent Test**: Vitest — `gestor` em `/app/alertas` e
`/app/chamados` não vê as listas e **não** chama `GET /solicitacoes`;
recepção em `/app/chamados` não vê **Meus chamados** como tela da
equipe.

### Tests for User Story 6

- [x] T022 [US6] Estender `frontend/src/painel/Casca.test.tsx`:
      perfil `gestor` em `/app/alertas` e `/app/chamados` — nenhum
      título das duas listas operacionais, **zero** `GET
      /solicitacoes`; perfil `recepcao` em `/app/chamados` — não
      mostra a lista compacta da equipe (casa = fila). Rodar e
      **ver falhar** se montar tela alheia antes do Navigate
      ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))

### Implementation for User Story 6

- [x] T023 [US6] Ajustar `frontend/src/painel/Casca.tsx` se T022
      falhar. Não dar tela de gestão nesta fatia. Até T022 verde

**Checkpoint**: os três perfis só vêem a superfície que a spec
permite.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: frase da ficha, log, palavras proibidas, estado do
projeto, suíte.

- [x] T024 [P] Em `frontend/src/painel/TelaFicha.tsx` (e o teste
      correspondente em `TelaFicha.test.tsx`): o vazio sem id cita
      a fila do dia **e** Chamados e pedidos como origens; continua
      **zero** GET de ficha sem id
      ([research.md](./research.md) § divergências)
- [x] T025 [P] Varredura em `frontend/src/painel/TelaAlertas.tsx`,
      `frontend/src/painel/TelaChamados.tsx` e
      `frontend/src/painel/solicitacoes.ts`: zero `console.log` de
      `itens` ou `descricao`; zero ocorrência de “extrato” e “conta”
      ([contracts/logs.md](./contracts/logs.md))
- [x] T026 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F8.4
      concluída quando o quickstart passar; próxima fatia F8.5.
      Sem inventar integração PMS
- [x] T027 Rodar `npm test` em `frontend/` e, na raiz,
      `pytest testes/unitarios -q` mais
      `pytest testes/integracao -q -k "solicitacao or resolver or sessao or casca"`.
      Tudo verde. Conferir o roteiro de
      [quickstart.md](./quickstart.md) (casos Vitest cobertos;
      browser só como checagem humana, não tarefa de Playwright)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: começa agora — mock da casca
- **Foundational (Phase 2)**: depende do Setup — **bloqueia** as histórias
- **US1 (Phase 3)**: depois da Foundational — MVP
- **US2 (Phase 4)**: depois da Foundational (arquivo distinto de US1);
  na prática um desenvolvedor faz depois da US1 para a casca não
  ligar as duas telas ao mesmo tempo sem mock estável
- **US3 (Phase 5)**: depois de US1 e US2 (precisa dos dois componentes)
- **US4 (Phase 6)**: depois de T011 (TelaChamados montada) e T007
- **US5 (Phase 7)**: depois da US3 (dois Resolvidos na sessão)
- **US6 (Phase 8)**: depois de T007 e T011
- **Polish**: depois das histórias desejadas

### User Story Dependencies

- **US1**: só Foundational
- **US2**: só Foundational (independente da lista da recepção)
- **US3**: US1 + US2
- **US4**: US2 (e casca da US1 para `/alertas`)
- **US5**: US3
- **US6**: US1 + US2

### Within Each User Story

- Testes **primeiro**, ver falhar, depois o mínimo para verde
- Função pura antes do JSX que a usa
- História completa antes de avançar prioridade, salvo US1 e US2 em
  paralelo após a Foundational (arquivos distintos)

### Parallel Opportunities

- T012 e T013 (dois arquivos de teste) depois de US1 e US2
- T024, T025 e T026 no polish
- US1 e US2 em paralelo só com dois implementadores; um
  desenvolvedor: US1 → US2

---

## Parallel Example: depois da Foundational

```text
# US1 (sequencial no mesmo par teste/tela):
Task: T004 TelaAlertas.test.tsx lista + Ver ficha
Task: T005 TelaAlertas.test.tsx vazio ≠ falha
Task: T006 TelaAlertas.tsx
Task: T007 Casca.tsx alertas

# US2, arquivos distintos — pode paralelizar com US1 se houver gente:
Task: T008 TelaChamados.test.tsx
Task: T009 TelaChamados.test.tsx vazio ≠ falha
```

T012 e T013 após as duas telas existirem. T004 e T005 são o mesmo
arquivo: **não** paralelizar entre si.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: recepção vê Chamados e pedidos e abre a ficha. Equipe
   ainda é título até a US2

### Incremental Delivery

1. Setup + Foundational
2. US1 → demo da lista da recepção
3. US2 → demo da casa da equipe
4. US3 → demo do Resolvido
5. US4 → trava da ficha
6. US5 → compacto/sessão
7. US6 → isolamento da gestão
8. Polish + estado do projeto

### Parallel Team Strategy

Um desenvolvedor (prazo da semana): ordem US1 → US2 → US3 → US4 →
US5 → US6. US1 e US2 só em paralelo com duas pessoas (arquivos
distintos depois da Foundational).

---

## Notes

- [P] só com arquivos distintos e dependência já verde
- Sem Playwright, sem `politica.py`, sem Alembic, sem worker
- Não reordenar `itens`; não chamar `/consumos/pendentes`
- Não mostrar nome na lista; **Ver ficha** só na recepção
- Commit por história (não por tarefa) salvo o usuário pedir o
  contrário — o ciclo TDD da casa é teste → falha → código → verde
