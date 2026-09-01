---
description: "Task list for feature implementation"
---

# Tasks: Consumos a lançar e saída do hóspede

**Input**: Design documents from `/specs/032-consumos-saida-hospede/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md),
[research.md](./research.md), [data-model.md](./data-model.md),
[contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma
linha de produção sem teste que falhe antes pelo motivo certo. Nenhum
teste abre navegador (Playwright fora). Nenhum teste chama PMS,
WhatsApp ou IA. `fetch` é falso no Vitest. pytest só como regressão
já verde (consumo, lançamento, dispensa, saída, pedidos, fila,
sessão).

**Organization**: Tarefas agrupadas por história (US1–US7), na ordem
da spec. Tipos + total pendente + aviso da estadia + prefixo `/saida/`
entram na Foundational. US1 é o MVP (recepção vê a fila financeira).
US2 lança. US3 dispensa. US4 é a tela de saída com lista e aviso.
US5 confirma o checkout. US6 liga a fila do dia. US7 isolamento.
Sem migração. Sem operação nova na matriz. Sem alterar backend.
Worker intocado. Python de atendimento e hospedagem intocado.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US7)

## Como ver os testes falharem nesta fatia

**Total e aviso.** Sem `totalPendente` / `pendentesDaEstadia`,
`consumos.test.ts` falha com módulo ausente. Soma errada ou recorte
que devolve item de outra reserva: falha.

**Lista financeira.** Sem `TelaConsumos`, `/app/consumos` continua o
`<h1>` da `TelaNomeada`. Vitest que procura valor, tempo e **Ver
ficha** não acha. Nome do hóspede na linha: falha da clarificação.
`GET` 500 mostrando “nada a lançar”: falha da US1.

**Lançar / dispensar.** Clique na descrição ou em **Ver ficha** que
dispara POST: falha da US2/US3. Sem segundo diálogo: o teste não
deve procurar “tem certeza”. `200` sem `GET` seguinte (item continua
na tela): falha. `409` que some o item: falha. Um botão que dispara
o outro: falha.

**Saída.** Sem `TelaSaida`, `/app/saida` é só título. Lista chamada
“extrato”/“conta”: falha. Coluna de status por item: falha.
`/saida` sem id que busca ficha: falha. Aviso que filtra Consumos a
lançar por reserva: falha da clarificação. **Confirmar saída** na
fila do dia (POST no mesmo gesto): falha da US6.

**Perfil.** Staff em `/app/consumos` ou `/app/saida/1` que dispara
`GET /consumos/pendentes` ou GET de ficha: falha da US7.

**Casca.** Ao ligar as telas, `Casca.test.tsx` precisa do mock
`GET /consumos/pendentes` `200 {itens:[]}`. Sem isso a US1 “quebra”
a casca com estado de falha — T001 existe para isso.

---

## Phase 1: Setup

**Purpose**: o `frontend/` da F8.1–F8.4 já tem router, Tailwind,
Vitest e proxy `/consumos` e `/reservas`. Esta fase só evita
regressão da casca quando Consumos a lançar passar a buscar dados.
Sem npm novo. Sem Python.

- [X] T001 Em `frontend/src/painel/Casca.test.tsx`, o `fetch` falso
      de `fetchPorPerfil` responde `GET /consumos/pendentes` com
      `200` e `{itens:[]}` (além do que já responde para fila,
      solicitações e ficha). Rodar `npm test` em `frontend/` —
      permanece verde com `TelaNomeada` em `consumos` e `saida`.
      Sem implementar `TelaConsumos` nem `TelaSaida`
      ([plan.md](./plan.md) ponto de atenção 2)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: tipo do item pendente, total, aviso da estadia e
prefixo de destino `/saida/:id`, testáveis sem DOM das telas novas.
**Nenhuma tela operacional ainda.** Reusar `tempoDecorrido` de
`frontend/src/painel/solicitacoes.ts` — não copiar.

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase.

- [X] T002 Unitários em `frontend/src/painel/consumos.test.ts`:
      `totalPendente` soma os `valor_praticado` (número ou string)
      e devolve 0 em lista vazia; `pendentesDaEstadia(itens, id)`
      devolve só os daquela reserva; tempo do mais antigo usa o
      primeiro item (já ordenado) com `tempoDecorrido` importado
      de `solicitacoes.ts`; o arquivo **não** contém as palavras
      “extrato” nem “conta”. Rodar `npm test` em `frontend/` e
      **ver falhar**
      ([data-model.md](./data-model.md),
      [contracts/api-reusada.md](./contracts/api-reusada.md))
- [X] T003 Criar `frontend/src/painel/consumos.ts`: tipo
      `ItemConsumoPendente` com os campos de
      [contracts/api-reusada.md](./contracts/api-reusada.md),
      `totalPendente`, `pendentesDaEstadia` até T002 verde. Sem
      JSX. Sem `fetch`. Sem `sort`. Sem reimplementar
      `tempoDecorrido`
- [X] T004 [P] Em `frontend/src/painel/destinos.test.ts`:
      `destinoPorCaminho` trata `/app/saida`, `/app/saida/12` e
      `/saida/12` como destino `saida`; `perfilPode("recepcao",
      "/app/saida/12")` verdadeiro; staff e gestão em
      `/app/saida/12` falso. Rodar e **ver falhar**
      ([plan.md](./plan.md) ponto de atenção 7)
- [X] T005 Em `frontend/src/painel/destinos.ts`, o mesmo padrão da
      ficha para o prefixo `/saida/`. Até T004 verde. Sem mudar
      títulos nem perfis da tabela `DESTINOS`

**Checkpoint**: `npm test` verde nas funções puras e no prefixo.
Destinos `consumos` e `saida` ainda são título.

---

## Phase 3: User Story 1 - A recepção vê o que falta lançar (Priority: P1) 🎯 MVP

**Goal**: Consumos a lançar lista o `GET /consumos/pendentes`:
descrição do item, valor, tempo, total no topo, mais antigos
primeiro, sem nome, **Ver ficha** para `/ficha/{id_reserva}`
inclusive sem quarto. Vazio ≠ falha de leitura. Sem lançar nem
dispensar ainda.

**Independent Test**: Vitest — mock com dois pendentes de valores
e idades diferentes; a tela mostra os dois, o primeiro do array
no topo, resumo com quantidade, soma e tempo do mais antigo,
**Ver ficha** em cada um, nenhum nome/telefone/documento.
`itens:[]` é vazio explícito com total zero. `GET` 500 não usa o
estado vazio.

### Tests for User Story 1

- [X] T006 [US1] Vitest em `frontend/src/painel/TelaConsumos.test.tsx`:
      ao montar, `GET /consumos/pendentes` com `credentials:
      "include"`; renderiza `descricao_item`, quarto (ou ausência
      perceptível), valor, `tempoDecorrido` com `agora` fixo;
      primeiro item do JSON aparece antes do último; resumo com
      quantidade, `totalPendente` e tempo do mais antigo; **Ver
      ficha** com `href` terminando em `/ficha/{id_reserva}`; item
      sem `numero_quarto` **ainda** tem esse link; **nenhum**
      texto de nome/telefone/documento; zero “extrato”/“conta”.
      Sem botões Marcar lançado / Dispensar nesta história.
      `MemoryRouter` basename `/app` + `fetch` falso. Rodar e
      **ver falhar**
      ([contracts/superficie-consumos.md](./contracts/superficie-consumos.md),
      [contracts/api-reusada.md](./contracts/api-reusada.md))
- [X] T007 [US1] No mesmo `frontend/src/painel/TelaConsumos.test.tsx`:
      `200` + `itens:[]` → estado de lista vazia, total zero, sem
      copiar o recado de falha; `GET` 500 (ou rede) → declara que
      a lista não carregou, oferece tentar de novo, **não** mostra
      o estado vazio nem total zero como turno limpo; segundo
      `GET` 200 recupera a lista. Rodar e **ver falhar**

### Implementation for User Story 1

- [X] T008 [US1] Criar `frontend/src/painel/TelaConsumos.tsx`: no
      mount chama `pedirAutenticado("/consumos/pendentes")`; lista
      na ordem do array; **Ver ficha** (`Link` para
      `/ficha/{id_reserva}`); resumo; estados vazio, carregando e
      falha como o contrato. Sem `POST`. Sem nome inventado.
      Título **Consumos a lançar**. Até T006 e T007 verdes
- [X] T009 [US1] Em `frontend/src/painel/Casca.tsx`,
      `destino.id === "consumos"` renderiza `TelaConsumos` em vez
      de `TelaNomeada`. Casos de `Casca.test.tsx` que abrem a
      recepção continuam verdes (T001). Rodar `npm test` em
      `frontend/`

**Checkpoint**: recepção vê a fila financeira e abre a ficha.
Lançar, dispensar e saída ainda não.

---

## Phase 4: User Story 2 - Marcar como lançado (Priority: P1)

**Goal**: botão rotulado **Marcar lançado**; um clique, sem diálogo,
`POST .../lancamento` corpo vazio; depois `GET` de novo; clique
fora não POST; 409 visível e item não some por otimismo.

**Independent Test**: Vitest — **Marcar lançado** faz POST com
`credentials: "include"`; GET seguinte sem o id; totais baixam;
clique em **Ver ficha** ou na descrição zero POST; 409 mostra
motivo e o id permanece até o GET dizer o contrário.

### Tests for User Story 2

- [X] T010 [US2] Em `frontend/src/painel/TelaConsumos.test.tsx`:
      cada item tem **exatamente um** botão **Marcar lançado**;
      clique nele → `POST /solicitacoes/{id}/lancamento` corpo
      vazio; em `200` um novo `GET /consumos/pendentes` e o id
      some, totais recalculam; clique em **Ver ficha** ou na
      descrição → zero POST; 409 (já lançado) mostra o detalhe da
      API, não afirma sucesso, refaz GET. Sem texto “tem certeza”.
      Rodar e **ver falhar**
      ([contracts/api-reusada.md](./contracts/api-reusada.md))

### Implementation for User Story 2

- [X] T011 [US2] Em `frontend/src/painel/TelaConsumos.tsx`, botão
      **Marcar lançado** (`<button>`), disable enquanto o POST
      daquele id não volta, depois GET. Até T010 verde. **Ver
      ficha** permanece `Link`. Rodar `npm test` em `frontend/`

**Checkpoint**: lançar tira da fila. Dispensar ainda não.

---

## Phase 5: User Story 3 - Dispensar (Priority: P1)

**Goal**: botão rotulado **Dispensar**, distinto do lançar; mesmo
padrão de um clique, GET seguinte, 409; um não dispara o outro.

**Independent Test**: Vitest — **Dispensar** faz `POST
.../dispensa`; `200` some o id; clique em **Marcar lançado** não
chama `/dispensa` e vice-versa.

### Tests for User Story 3

- [X] T012 [US3] Em `frontend/src/painel/TelaConsumos.test.tsx`:
      cada item tem **Dispensar** além de **Marcar lançado**;
      clique em **Dispensar** → `POST /solicitacoes/{id}/dispensa`
      corpo vazio; `200` → GET de novo e o id some; clique em
      **Marcar lançado** zero chamada a `/dispensa`; 409 (já
      dispensado) visível, GET de novo. Rodar e **ver falhar**
      ([contracts/superficie-consumos.md](./contracts/superficie-consumos.md))

### Implementation for User Story 3

- [X] T013 [US3] Em `frontend/src/painel/TelaConsumos.tsx`, botão
      **Dispensar** até T012 verde. Os dois botões não compartilham
      o mesmo `onClick`. Rodar `npm test` em `frontend/`

**Checkpoint**: a fila financeira lança e dispensa. Saída ainda é
título.

---

## Phase 6: User Story 4 - Lista da saída e aviso de pendência (Priority: P1)

**Goal**: Saída do hóspede com id mostra identidade, **Pedidos
feitos pelo chat** (descrição + valor + total, sem status por
item) e aviso se `pendentesDaEstadia` não for vazio, apontando
para `/consumos` da casa. Sem id: estado honesto, zero fetch. Sem
**Confirmar saída** ainda.

**Independent Test**: Vitest — `/saida` sem id não chama ficha nem
pedidos; `/saida/42` chama ficha, pedidos, pendentes e fila;
lista sem “extrato”/“conta” e sem status por linha; aviso presente
só se houver pendente daquela reserva; o aviso é link para
`/consumos` (não `/consumos?reserva=`).

### Tests for User Story 4

- [X] T014 [US4] Vitest em `frontend/src/painel/TelaSaida.test.tsx`:
      rota `/saida` (sem id) — título **Saída do hóspede**, texto
      apontando à fila, **zero** `fetch` para `/ficha`,
      `pedidos-feitos-pelo-chat`, `/consumos/pendentes` e
      `/fila-do-dia`; sem botão Confirmar saída. `MemoryRouter`
      basename `/app`. Rodar e **ver falhar**
      ([contracts/superficie-saida.md](./contracts/superficie-saida.md))
- [X] T015 [US4] No mesmo `frontend/src/painel/TelaSaida.test.tsx`,
      rota `/saida/42`: `GET /reservas/42/ficha`,
      `GET /reservas/42/pedidos-feitos-pelo-chat`,
      `GET /consumos/pendentes` e `GET /fila-do-dia` com
      `credentials: "include"`; mostra nome da ficha, lista
      rotulada **Pedidos feitos pelo chat** com descrição e valor,
      total do envelope; **não** mostra `status_lancamento` por
      linha; zero “extrato”/“conta”; se pendentes da casa tiverem
      item com `id_reserva: 42`, aviso visível com link para
      `/consumos` (href **sem** recorte de reserva); se só houver
      pendente de outra reserva, **sem** aviso. Sem botão
      Confirmar saída nesta história. Rodar e **ver falhar**
- [X] T016 [US4] No mesmo `frontend/src/painel/TelaSaida.test.tsx`:
      pedidos `itens:[]` → lista vazia honesta, sem aviso; GET
      500 de pedidos ou ficha → declara que não carregou, tentar
      de novo, **não** usa lista vazia nem afirma checkout; 404
      genérico, sem nome. Rodar e **ver falhar**

### Implementation for User Story 4

- [X] T017 [US4] Criar `frontend/src/painel/TelaSaida.tsx`: sem id,
      vazio honesto e zero fetch; com id, os quatro GET do
      [research.md](./research.md) §6; lista cobrável; aviso via
      `pendentesDaEstadia`; link do aviso para `/consumos`. Sem
      POST. Até T014–T016 verdes
- [X] T018 [US4] Em `frontend/src/painel/Casca.tsx`, destino
      `saida` usa rota `/saida/:idReserva?` e renderiza
      `TelaSaida`. Em `Casca.test.tsx`, `fetchPorPerfil` responde
      `GET` de ficha e de `pedidos-feitos-pelo-chat` com lista
      vazia se algum teste montar recepção nessa rota. Rodar
      `npm test` em `frontend/`

**Checkpoint**: a recepção vê os pedidos e o aviso. Checkout ainda
não.

---

## Phase 7: User Story 5 - Confirmar a saída (Priority: P1)

**Goal**: botão **Confirmar saída** só se `status_reserva ===
hospedado`; um clique, `POST .../saida` corpo vazio; aviso não
trava; clique fora não POST; 409 visível; `200` some o botão.

**Independent Test**: Vitest — hospedada com pendente ainda
oferece o botão; POST `200` some o botão; clique na lista ou no
aviso zero POST; 409 (já encerrada) visível.

### Tests for User Story 5

- [X] T019 [US5] Em `frontend/src/painel/TelaSaida.test.tsx`:
      ficha `status_reserva: "hospedado"` → um botão **Confirmar
      saída**; clique → `POST /reservas/42/saida` corpo vazio;
      `200` → botão some; com aviso de pendência o POST **ainda**
      ocorre; clique na lista ou no aviso → zero POST; ficha
      `encerrado` → sem botão; 409 mostra detalhe da API e não
      afirma encerrado. Sem “tem certeza”. Rodar e **ver falhar**
      ([contracts/api-reusada.md](./contracts/api-reusada.md))

### Implementation for User Story 5

- [X] T020 [US5] Em `frontend/src/painel/TelaSaida.tsx`, botão
      **Confirmar saída**, disable enquanto o POST não volta. Até
      T019 verde. Rodar `npm test` em `frontend/`

**Checkpoint**: o checkout existe na tela de saída. A fila ainda
não aponta para ela.

---

## Phase 8: User Story 6 - Fila do dia leva à saída e destaca vencida (Priority: P1)

**Goal**: hospedado tem link **Saída** (não **Confirmar saída**)
para `/saida/{id}`; não dispara POST; `saida_nao_confirmada`
ganha destaque distinto; `resumirTurno` permanece com três contas.

**Independent Test**: Vitest — hospedado tem `getByRole("link",
{ name: "Saída" })` com href `/saida/{id}`; não hospedado sem
esse link; clique no link zero POST `/saida`; linha com
`saida_nao_confirmada` tem rótulo distinto de chegada vencida.

### Tests for User Story 6

- [X] T021 [P] [US6] Em `frontend/src/painel/fila.test.ts`:
      `saidaAdmiteCaminho("hospedado")` verdadeiro; demais status
      da fila (ficha recebida, parcial, aguardando, encerrado)
      falso; `resumirTurno` **não** ganha quarta conta (regressão
      das três partições). Rodar e **ver falhar**
      ([contracts/acrescimo-na-fila.md](./contracts/acrescimo-na-fila.md))
- [X] T022 [US6] Em `frontend/src/painel/TelaFila.test.tsx`:
      hospedado mostra link **Saída** com href terminando em
      `/saida/{id_reserva}` e **não** mostra botão Confirmar
      saída; não hospedado omite o link; `saida_nao_confirmada:
      true` tem sinal distinto de `chegada_nao_confirmada`; o
      resumo continua só com hoje / hospedados / entrada vencida.
      Rodar e **ver falhar**

### Implementation for User Story 6

- [X] T023 [US6] Em `frontend/src/painel/fila.ts`, tipo
      `ItemFila` ganha `saida_nao_confirmada` e
      `saidaAdmiteCaminho`. Em `frontend/src/painel/TelaFila.tsx`,
      o `<Link>` **Saída** e o destaque. Até T021 e T022 verdes.
      Ajustar o helper `item()` de `TelaFila.test.tsx` com o
      campo novo. Rodar `npm test` em `frontend/`

**Checkpoint**: a fila abre a saída sem encerrar. Isolamento de
perfil ainda.

---

## Phase 9: User Story 7 - Isolamento e estados que não se confundem (Priority: P2)

**Goal**: gestão e equipe não operam Consumos a lançar nem Saída
do hóspede; zero fetch alheio.

**Independent Test**: Vitest — `staff` e `gestor` em `/app/consumos`
e `/app/saida` / `/app/saida/1` não vêem os títulos operacionais e
**não** chamam `/consumos/pendentes`, ficha, pedidos nem POST de
saída/lançamento.

### Tests for User Story 7

- [X] T024 [US7] Estender `frontend/src/painel/Casca.test.tsx`:
      perfis `staff` e `gestor` em `/app/consumos`, `/app/saida` e
      `/app/saida/1` — nenhum título **Consumos a lançar** nem
      **Saída do hóspede**; **zero** GET `/consumos/pendentes`,
      URL contendo `pedidos-feitos-pelo-chat`, `/reservas/.../ficha`
      (além do que a casa de cada perfil já busca) e **zero** POST
      `/lancamento`, `/dispensa` ou `/saida`. Rodar e **ver falhar**
      se montar a tela alheia antes do `Navigate`
      ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))

### Implementation for User Story 7

- [X] T025 [US7] Ajustar `frontend/src/painel/Casca.tsx` se T024
      falhar por montar `TelaConsumos` / `TelaSaida` antes do
      redirecionamento. Não mudar `politica.py`. Até T024 verde

**Checkpoint**: os três perfis só vêem a superfície que a spec
permite.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: log, palavras proibidas, estado do projeto, suíte.

- [X] T026 [P] Varredura em `frontend/src/painel/TelaConsumos.tsx`,
      `frontend/src/painel/TelaSaida.tsx`,
      `frontend/src/painel/TelaFila.tsx` e
      `frontend/src/painel/consumos.ts`: zero `console.log` de
      `itens`, descrição ou valor; zero ocorrência de “extrato” e
      “conta”; o controle da fila é **Saída**, não **Confirmar
      saída**
      ([contracts/logs.md](./contracts/logs.md))
- [X] T027 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F8.5
      concluída quando o quickstart passar; próxima fatia F8.6.
      Sem inventar integração PMS. Registrar que status por item
      na lista da saída ficou para depois da semana
- [X] T028 Rodar `npm test` em `frontend/` e, na raiz,
      `pytest testes/unitarios -q` mais
      `pytest testes/integracao -q -k "consumo or lancamento or dispensa or saida or pedidos or fila or sessao"`.
      Tudo verde. Conferir o roteiro de
      [quickstart.md](./quickstart.md) (casos Vitest cobertos;
      browser só como checagem humana, não tarefa de Playwright)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: começa agora — mock da casca
- **Foundational (Phase 2)**: depende do Setup — **bloqueia** as histórias
- **US1 (Phase 3)**: depois da Foundational — MVP
- **US2 (Phase 4)**: depois da US1 (mesmo `TelaConsumos.tsx`)
- **US3 (Phase 5)**: depois da US2 (mesmo arquivo)
- **US4 (Phase 6)**: depois da Foundational (`pendentesDaEstadia`,
  prefixo `/saida/`); na prática depois da US1 para o aviso ligar
  a uma `TelaConsumos` já existente
- **US5 (Phase 7)**: depois da US4
- **US6 (Phase 8)**: depois da US4 (o link precisa do destino)
- **US7 (Phase 9)**: depois de T009 e T018
- **Polish**: depois das histórias desejadas

### User Story Dependencies

- **US1**: só Foundational
- **US2**: US1
- **US3**: US2
- **US4**: Foundational; melhor depois da US1
- **US5**: US4
- **US6**: US4
- **US7**: US1 + US4

### Within Each User Story

- Testes **primeiro**, ver falhar, depois o mínimo para verde
- Função pura antes do JSX que a usa
- História completa antes de avançar prioridade

### Parallel Opportunities

- T004 (destinos.test) em paralelo com T002 (consumos.test) na
  Foundational
- T021 (fila.test.ts) em paralelo com T014–T016 depois da
  Foundational, mas T022 espera `TelaFila` + destino `saida`
- T026 e T027 no polish
- T006 e T007 são o mesmo arquivo: **não** paralelizar entre si

---

## Parallel Example: depois da Foundational

```text
# US1 (sequencial no mesmo par teste/tela):
Task: T006 TelaConsumos.test.tsx lista + Ver ficha
Task: T007 TelaConsumos.test.tsx vazio ≠ falha
Task: T008 TelaConsumos.tsx
Task: T009 Casca.tsx consumos

# Destinos já verdes na Foundational; US4 depois da US1:
Task: T014 TelaSaida.test.tsx sem id
Task: T015 TelaSaida.test.tsx lista + aviso
```

T006 e T007 são o mesmo arquivo: **não** paralelizar entre si.
US2 e US3 não paralelizam com US1 — mesmo `TelaConsumos.tsx`.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: recepção vê Consumos a lançar e abre a ficha. Lançar,
   dispensar e checkout ainda não

### Incremental Delivery

1. Setup + Foundational
2. US1 → demo da fila financeira
3. US2 → demo do lançar
4. US3 → demo do dispensar
5. US4 → demo da lista da saída e do aviso
6. US5 → demo do checkout
7. US6 → caminho na fila + destaque vencida
8. US7 → isolamento
9. Polish + estado do projeto

### Parallel Team Strategy

Um desenvolvedor (prazo da semana): ordem US1 → US2 → US3 → US4 →
US5 → US6 → US7. Não paralelizar US1–US3 (mesmo arquivo).

---

## Notes

- [P] só com arquivos distintos e dependência já verde
- Sem Playwright, sem `politica.py`, sem Alembic, sem worker, sem
  campo novo nas APIs
- Não reordenar `itens`; não filtrar Consumos a lançar por reserva
- Não mostrar nome na fila financeira; **Ver ficha** só na recepção
- **Saída** na fila; **Confirmar saída** só em `TelaSaida`
- Commit por história (não por tarefa) salvo o usuário pedir o
  contrário — o ciclo TDD da casa é teste → falha → código → verde
