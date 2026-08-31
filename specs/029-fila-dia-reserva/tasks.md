---
description: "Task list for feature implementation"
---

# Tasks: Fila do dia e cadastro de reserva

**Input**: Design documents from `/specs/029-fila-dia-reserva/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md),
[research.md](./research.md), [data-model.md](./data-model.md),
[contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma
linha de produção sem teste que falhe antes pelo motivo certo. Nenhum
teste abre navegador (Playwright fora). Nenhum teste chama PMS nem
muda regra HTTP. `fetch` é falso no Vitest. pytest só como regressão
já verde (fila, reserva, chegada).

**Organization**: Tarefas agrupadas por história (US1–US5), na ordem da
spec. Tipos + partição do resumo entram na Foundational. US1 é o MVP
(ver o turno). US2 cadastra. US3 confirma no botão rotulado. US4
distingue as três pendências. US5 trava que staff/gestão não vêem a
lista. Sem migração. Sem operação nova na matriz. Worker intocado.
Python de hospedagem intocado.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US5)

## Como ver os testes falharem nesta fatia

**Resumo.** `resumirTurno` ainda não existe: `fila.test.ts` falha com
módulo ausente. Depois, um item `hospedado` + `chegada_nao_confirmada:
true` (caso impossível no backend, mas o teste de partição usa só os
casos reais) ou vencida contada também em “hoje” — falha até a função
seguir [resumo-do-turno.md](./contracts/resumo-do-turno.md).

**Fila.** Sem `TelaFila`, a casa da recepção continua só o `<h1>`.
Vitest que procura o nome do hóspede ou as três contas não acha.
`GET /fila-do-dia` 500 mostrando o estado de “ninguém no turno”:
falha da US1.

**Cadastro.** Sem `TelaNovaReserva`, não há campos nome/telefone/datas.
Telefone `123` que dispara `POST /reservas`: falha da US2. Sucesso
futuro com a linha aparecendo na lista: falha — o id não veio no GET.

**Chegada.** Botão visível em `aguardando_cadastro`: falha da US3.
Clique no nome que chama `POST .../chegada`: falha. Sem segundo
diálogo: o teste não deve procurar “tem certeza”.

**Pendências.** Mesmo texto para vencida e recado não enviado: falha
da US4.

**Perfil.** Staff em `/app/fila` que dispara `GET /fila-do-dia`: falha
da US5.

**Casca.** Ao ligar `TelaFila`, `Casca.test.tsx` que abre `/app/fila`
precisa do mock `GET /fila-do-dia` `200 {itens:[]}`. Sem isso a US1
“quebra” a casca com estado de falha — T001 existe para isso.

---

## Phase 1: Setup

**Purpose**: o `frontend/` da F8.1 já tem router, Tailwind, Vitest e
proxy. Esta fase só evita regressão da casca quando a fila passar a
buscar dados. Sem npm novo. Sem Python.

- [x] T001 Em `frontend/src/painel/Casca.test.tsx`, o `fetch` falso
      de `fetchPorPerfil` responde `GET /fila-do-dia` com `200` e
      `{itens:[]}` e não quebra os casos que abrem `/app/fila`. Rodar
      `npm test` em `frontend/` — permanece verde com `TelaNomeada`.
      Sem implementar `TelaFila`
      ([plan.md](./plan.md) ponto de atenção 3)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: tipo da linha e partição do resumo, testáveis sem DOM.
**Nenhuma tela operacional ainda.**

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase.

- [x] T002 Unitários em `frontend/src/painel/fila.test.ts`:
      `resumirTurno` — lista vazia → `{hoje:0, hospedados:0, vencidas:0}`;
      um `hospedado` só na conta hospedados; um com
      `chegada_nao_confirmada: true` só em vencidas; um não hospedado
      com flag falsa só em hoje; a soma das três é `itens.length`;
      hospedado com `boas_vindas_nao_enviadas` continua em hospedados.
      Rodar `npm test` em `frontend/` e **ver falhar**
      ([contracts/resumo-do-turno.md](./contracts/resumo-do-turno.md))
- [x] T003 Criar `frontend/src/painel/fila.ts`: tipo `ItemFila` com os
      campos do contrato de API reusada e `resumirTurno(itens)` até
      T002 verde. Sem JSX. Sem `fetch`
      ([contracts/api-reusada.md](./contracts/api-reusada.md),
      [data-model.md](./data-model.md))

**Checkpoint**: `npm test` verde na partição. Casa da recepção ainda é
título.

---

## Phase 3: User Story 1 - Ver o turno inteiro na fila do dia (Priority: P1) 🎯 MVP

**Goal**: a casa da recepção lista o que `GET /fila-do-dia` devolve
(hoje, hospedados, vencidas), com nome, telefone, datas, situação e
resumo em partição. Vazio ≠ falha de leitura.

**Independent Test**: Vitest — mock com três famílias + ausência de
futura/encerrada no JSON; a tela mostra as três, as contas somam as
linhas, e não mostra quem não veio no `GET`. `itens:[]` mostra turno
vazio com cadastrar alcançável. `GET` 500 não usa o estado vazio.

### Tests for User Story 1

- [x] T004 [US1] Vitest em `frontend/src/painel/TelaFila.test.tsx`:
      ao montar, `GET /fila-do-dia` com `credentials: "include"`;
      renderiza nome, telefone e datas de cada item; o resumo mostra
      as três contas coerentes com `resumirTurno`; item que não está
      em `itens` não aparece. `MemoryRouter` + `fetch` falso. Rodar e
      **ver falhar**
- [x] T005 [US1] No mesmo `frontend/src/painel/TelaFila.test.tsx`:
      `200` + `itens:[]` → contas em zero e caminho visível para nova
      reserva (texto ou controle), sem copiar o recado de falha;
      `GET` 500 (ou rede) → declara que a lista não carregou, oferece
      tentar de novo, **não** mostra o estado vazio; segundo `GET`
      200 recupera a lista. Rodar e **ver falhar**
      ([contracts/superficie-da-recepcao.md](./contracts/superficie-da-recepcao.md))

### Implementation for User Story 1

- [x] T006 [US1] Criar `frontend/src/painel/TelaFila.tsx`: no mount
      chama `pedirAutenticado("/fila-do-dia")`; lista + resumo via
      `resumirTurno`; estados vazio, carregando e falha como o
      contrato. Sem botão de chegada. Sem e-mail. Título **Fila do
      dia**. Até T004 e T005 verdes
- [x] T007 [US1] Em `frontend/src/painel/Casca.tsx`, `destino.id ===
      "fila"` renderiza `TelaFila` em vez de `TelaNomeada`. Os casos
      de `Casca.test.tsx` que abrem a casa da recepção continuam
      achando o título (T001). Rodar `npm test` em `frontend/`

**Checkpoint**: recepção vê o turno de verdade. Cadastro e chegada
ainda não.

---

## Phase 4: User Story 2 - Cadastrar reserva sem sair do turno (Priority: P1)

**Goal**: da fila (e do menu), formulário só com nome, telefone e
datas; telefone recusado na digitação; sucesso volta à fila e o GET
decide se a linha é de hoje.

**Independent Test**: Vitest — três campos, sem e-mail; `123` não
dispara POST; checkout ≤ check-in não dispara POST; `201` + GET com
o id nos itens mostra a linha; `201` + GET sem o id mostra aviso de
entrada futura; Cancelar não POST.

### Tests for User Story 2

- [x] T008 [P] [US2] Unitários em `frontend/src/painel/telefone.test.ts`:
      `(11) 98765-4321` e `11987654321` são aceitos; `123` e número
      estrangeiro recusados; a mensagem fala em brasileiro com DDD.
      Espelho de `app/comum/telefone.py`, sem importar Python. Rodar
      e **ver falhar**
- [x] T009 [P] [US2] Vitest em
      `frontend/src/painel/TelaNovaReserva.test.tsx`: só nome,
      telefone, entrada, saída — **nenhum** campo e-mail; branco não
      POST; telefone ilegível na digitação não POST; datas invertidas
      não POST; submit válido faz `POST /reservas` com JSON ISO e
      `credentials: "include"`; Cancelar navega à fila sem POST.
      Rodar e **ver falhar**

### Implementation for User Story 2

- [x] T010 [US2] Criar `frontend/src/painel/telefone.ts` (`normalizar`
      / recusa) até T008 verde. Sem UI
- [x] T011 [US2] Criar `frontend/src/painel/TelaNovaReserva.tsx`
      (shadcn input/label/button, `type="date"`) até T009 verde.
      Sucesso: `GET /fila-do-dia`; se `id_reserva` está em `itens`,
      vai a `/fila`; se não, aviso de que entra no dia da entrada e
      vai a `/fila`
      ([contracts/api-reusada.md](./contracts/api-reusada.md))
- [x] T012 [US2] Em `frontend/src/painel/Casca.tsx`, `destino.id ===
      "reserva"` renderiza `TelaNovaReserva`. Em `TelaFila.tsx`,
      controle **Nova reserva** navega para `/reserva`. Estender
      `TelaFila.test.tsx` se o controle ainda não era clicável. Rodar
      `npm test` em `frontend/`

**Checkpoint**: cadastro de três campos funciona. Chegada ainda não.

---

## Phase 5: User Story 3 - Confirmar a chegada na própria lista (Priority: P1)

**Goal**: botão rotulado **Confirmar chegada** só em estado que admite;
um clique POST + GET; clicar nome/telefone não confirma; sem
“tem certeza?”; `409` não mente hospedado.

**Independent Test**: Vitest — botão só em `ficha_recebida`,
`ficha_parcial`, `sem_cadastro_previo`; ausente em
`aguardando_cadastro` e `hospedado`; clique no botão chama
`POST /reservas/{id}/chegada` e o GET seguinte mostra hospedado;
clique no nome não chama POST.

### Tests for User Story 3

- [x] T013 [P] [US3] Unitários em `frontend/src/painel/fila.test.ts`:
      `chegadaAdmiteBotao` verdadeiro só para `ficha_recebida`,
      `ficha_parcial`, `sem_cadastro_previo`; falso para
      `aguardando_cadastro`, `hospedado`, `encerrado`, `cancelada`.
      Rodar e **ver falhar**
      ([data-model.md](./data-model.md))
- [x] T014 [US3] Estender `frontend/src/painel/TelaFila.test.tsx`:
      botão com o nome **Confirmar chegada** só nas linhas elegíveis;
      acionar o botão faz `POST /reservas/{id}/chegada` (corpo vazio)
      e depois `GET /fila-do-dia`; a linha passa a hospedada sem
      diálogo extra; clique no nome ou no telefone **não** dispara
      POST; `409` mostra motivo e GET de novo — a linha não vira
      hospedada se o GET ainda não a trouxe assim. Rodar e **ver
      falhar**

### Implementation for User Story 3

- [x] T015 [US3] Em `frontend/src/painel/fila.ts`, exportar
      `chegadaAdmiteBotao` até T013 verde
- [x] T016 [US3] Em `frontend/src/painel/TelaFila.tsx`, botão
      `<button>` na coluna ação (não `onClick` na linha). Um clique,
      sem `confirm()`. Depois do POST, GET e substitui `itens`. Até
      T014 verde. Sem confirmar saída
      ([contracts/superficie-da-recepcao.md](./contracts/superficie-da-recepcao.md))

**Checkpoint**: o balcão confirma chegada na lista. Pendências ainda
podem compartilhar estilo.

---

## Phase 6: User Story 4 - Pendências distintas (Priority: P1)

**Goal**: chegada vencida, recado não enviado e ficha parcial têm
rótulos/destaques que um teste consegue distinguir. Completa /
aguardando / sem cadastro prévio não usam o destaque das três.

**Independent Test**: Vitest — três linhas (parcial; hospedado com
`boas_vindas_nao_enviadas`; `chegada_nao_confirmada`) expõem três
textos diferentes; nenhuma empresta o rótulo da outra.

### Tests for User Story 4

- [x] T017 [US4] Estender `frontend/src/painel/TelaFila.test.tsx`:
      os três sinais têm `getByText` (ou equivalente) com strings
      distintas; hospedado com ficha completa e recado enviado não
      mostra nenhum dos três. Rodar e **ver falhar**
      ([spec.md](./spec.md) US4)

### Implementation for User Story 4

- [x] T018 [US4] Em `frontend/src/painel/TelaFila.tsx`, aplicar os
      rótulos do contrato de superfície (vencida ≠ recado ≠ parcial)
      até T017 verde. Não reusar a mesma classe/texto para vencida e
      recado

**Checkpoint**: Artigo V visível na lista, sem colapsar os três
sinais.

---

## Phase 7: User Story 5 - Só a recepção opera esta tela (Priority: P1)

**Goal**: staff e gestão não montam a lista nominada nem o cadastro;
não disparam `GET /fila-do-dia` / `POST /reservas`.

**Independent Test**: Vitest — sessão `staff` ou `gestor` em
`/app/fila` e `/app/reserva` redireciona à casa; `fetch` não é chamado
para `/fila-do-dia` nem `/reservas`.

### Tests for User Story 5

- [x] T019 [US5] Estender `frontend/src/painel/Casca.test.tsx`: com
      perfil `staff` e `gestor`, abrir `/app/fila` e `/app/reserva`
      não renderiza nome de hóspede nem formulário de reserva e
      **não** chama `GET /fila-do-dia` nem `POST /reservas`. Rodar e
      **ver falhar** se a tela montar antes do `Navigate`
      ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))

### Implementation for User Story 5

- [x] T020 [US5] Ajustar `frontend/src/painel/Casca.tsx` se T019
      falhar por montar `TelaFila`/`TelaNovaReserva` antes do
      redirecionamento (o `Navigate` por perfil deve ganhar). Não
      mudar `politica.py`. Até T019 verde

**Checkpoint**: minimização na superfície. API continua 403 se alguém
chamar direto — já coberto na F1.1/F2.2.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: log, estado do projeto, suíte inteira.

- [x] T021 [P] Varredura em `frontend/src/painel/TelaFila.tsx`,
      `TelaNovaReserva.tsx` e `fila.ts`: zero `console.log` de
      `itens`, nome, telefone ou corpo de POST
      ([contracts/logs.md](./contracts/logs.md))
- [x] T022 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F8.2
      concluída quando o quickstart passar; próxima fatia F8.3 (ou a
      do plano da semana). Sem inventar integração PMS
- [x] T023 Rodar `npm test` em `frontend/` e, na raiz,
      `pytest testes/unitarios -q` mais
      `pytest testes/integracao -q -k "reserva or fila or chegada or sessao or casca"`.
      Tudo verde. Conferir o roteiro de
      [quickstart.md](./quickstart.md) (casos Vitest cobertos; browser
      só como checagem humana, não tarefa de Playwright)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: começa agora — mock da casca
- **Foundational (Phase 2)**: depende do Setup — **bloqueia** as histórias
- **US1 (Phase 3)**: depois da Foundational — MVP
- **US2 (Phase 4)**: depois da US1 (precisa da fila para voltar e do
  controle Nova reserva)
- **US3 (Phase 5)**: depois da US1 (botão na lista). Pode em paralelo
  com US2 se `TelaFila` já existir
- **US4 (Phase 6)**: depois da US1 (rótulos nas linhas)
- **US5 (Phase 7)**: depois de T007 e T012 (as duas telas montadas)
- **Polish**: depois das histórias desejadas

### User Story Dependencies

- **US1**: só Foundational
- **US2**: US1 (navegação fila ↔ cadastro + GET pós-201)
- **US3**: US1 (lista). Independente de US2
- **US4**: US1. Independente de US2/US3
- **US5**: US1 + o destino `reserva` ligado (T012)

### Within Each User Story

- Testes **primeiro**, ver falhar, depois o mínimo para verde
- Função pura antes do JSX que a usa
- História completa antes de avançar prioridade, salvo US3/US4 em
  paralelo após US1

### Parallel Opportunities

- T008 e T009 (arquivos distintos) depois da US1
- T013 (`fila.test.ts`) em paralelo com T010/T011 se a US2 estiver em
  `telefone.ts` / `TelaNovaReserva.tsx` — não paralelizar T013 com T003
  incompleto
- T021 e T022 no polish

---

## Parallel Example: depois da Foundational

```text
# US1 (sequencial no mesmo teste, depois implementação):
Task: T004 TelaFila.test.tsx lista + resumo
Task: T005 TelaFila.test.tsx vazio ≠ falha
Task: T006 TelaFila.tsx
Task: T007 Casca.tsx

# Depois da US1, em paralelo:
Task: T008 telefone.test.ts          (US2)
Task: T013 chegadaAdmiteBotao tests  (US3, fila.test.ts — espera T003)
```

T013 estende `fila.test.ts` (mesmo arquivo que T002/T003): **não**
paralelizar com T003 incompleto.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: recepção vê o turno. Sem cadastro ainda, o menu “Nova
   reserva” continua título até a US2

### Incremental Delivery

1. Setup + Foundational
2. US1 → demo da lista
3. US2 → demo do cadastro
4. US3 → demo do clique de chegada
5. US4 → sinais distintos
6. US5 → trava de perfil
7. Polish + estado do projeto

### Parallel Team Strategy

Um desenvolvedor (prazo da semana): ordem US1 → US2 → US3 → US4 → US5.
US3 e US4 podem inverter se o botão for mais urgente que o visual das
tags.

---

## Notes

- [P] só com arquivos distintos e dependência já verde
- Sem Playwright, sem `politica.py`, sem Alembic, sem worker
- Não usar `GET /indicadores/chegadas-do-dia` no resumo
- Não mascarar telefone da recepção
- Não oferecer confirmar saída
- Commit por história (não por tarefa) salvo o usuário pedir o
  contrário — o ciclo TDD da casa é teste → falha → código → verde
