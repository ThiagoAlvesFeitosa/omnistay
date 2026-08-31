---
description: "Task list for feature implementation"
---

# Tasks: Ficha do hóspede e transcrição para o PMS

**Input**: Design documents from `/specs/030-ficha-hospede-pms/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md),
[research.md](./research.md), [data-model.md](./data-model.md),
[contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma
linha de produção sem teste que falhe antes pelo motivo certo. Nenhum
teste abre navegador (Playwright fora). Nenhum teste chama PMS,
WhatsApp ou IA. `fetch` e `clipboard` são falsos no Vitest.

**Organization**: Tarefas agrupadas por história (US1–US5), na ordem da
spec. Prefixo de rota e funções puras da ficha entram na Setup /
Foundational. US1 é o MVP (abrir e ver o que falta). US2 grava no
balcão + gatilho. US3 copia. US4 consentimento. US5 trava perfil.
Uma rota HTTP nova (`PUT`). Uma revisão Alembic (`0024`). Sem
operação nova na matriz. Worker intocado. Sem e-mail.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US5)

## Como ver os testes falharem nesta fatia

**Rota.** `destinoPorCaminho("/app/ficha/12")` hoje é `undefined`;
`perfilPode("recepcao", "/ficha/12")` é falso. Sem o prefixo, a casca
manda a recepção de volta à fila ao abrir a ficha.

**Ausentes.** Sem `camposAusentes`, o Vitest que espera os rótulos
“Profissão” e “CEP” numa ficha só com nome e telefone não acha a
função.

**Abrir.** Sem `TelaFicha`, `/app/ficha` continua o `<h1>` da
`TelaNomeada`. Vitest que procura distintivo “parcial” ou “Falta:”
não acha. Menu `/ficha` que dispara `GET /reservas/…/ficha`: falha
da US1 (FR-002).

**Ver ficha.** Fila sem o controle rotulado: falha da US1. Clique no
nome que dispara `POST .../chegada`: regressão da F8.2, não é o
caminho da ficha.

**Gatilho.** `UPDATE` `ficha_parcial` → `ficha_recebida` hoje levanta
exceção. `test_garantias_do_banco` que inclui esse par **passa a
falhar** até a `0024` (é o motivo certo).

**PUT.** `PUT /reservas/{id}/ficha` hoje é `405`. Integração que
espera `200` e `ficha_completa: true` falha até existirem schema,
serviço e rota. `trabalho` novo após o PUT: falha da US2.

**Cópia.** Sem `montarTextoCopia`, não há nove linhas rotuladas. Botão
**Copiar tudo** que não chama `clipboard.writeText` (falso): falha da
US3. Texto com linha `Idade` ou `E-mail`: falha.

**Consentimento.** Sem o bloco, não há “nunca registrado” nem
**Revogar**. `POST` com `origem: "pesquisa_checkout"` vindo da tela:
falha da US4.

**Perfil.** Staff em `/app/ficha/1` que dispara GET de ficha: falha da
US5.

---

## Phase 1: Setup

**Purpose**: o `frontend/` já tem casca, fila e Vitest. Esta fase faz
`/app/ficha/:id` continuar sendo o destino ficha (prefixo), ainda sem
a tela operacional. Sem npm novo.

- [X] T001 Unitários em `frontend/src/painel/destinos.test.ts`:
      `destinoPorCaminho` de `/app/ficha` e de `/app/ficha/12` (e o
      pathname relativo `/ficha/12`) devolve o destino `ficha`;
      `perfilPode("recepcao", …)` verdadeiro; `perfilPode("staff", …)`
      e `perfilPode("gestor", …)` falsos. Rodar `npm test` em
      `frontend/` e **ver falhar**
      ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))
- [X] T002 Em `frontend/src/painel/destinos.ts`, matching por prefixo
      `/app/ficha`. Em `frontend/src/painel/Casca.tsx`, a rota do
      destino `ficha` aceita `:idReserva?` (`/ficha/:idReserva?`).
      Continua `TelaNomeada` nesta tarefa. Até T001 verde. `Casca.test.tsx`
      permanece verde

**Checkpoint**: colar `/app/ficha/12` como recepção não redireciona à
fila por “destino desconhecido”. Ainda só o título.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: ausentes e idade derivada, testáveis sem DOM.
**Nenhuma tela operacional ainda. Sem PUT. Sem Alembic.**

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase.

- [X] T003 Unitários em `frontend/src/painel/ficha.test.ts`:
      `camposAusentes` — ficha com os nove preenchidos → `[]`;
      só nome+telefone → ausentes incluem pelo menos Profissão, Data
      de nascimento, Tipo de documento, Número do documento, Endereço,
      CEP, Cidade (rótulos em português, não chaves cruas); um campo
      `null` ou `""` conta como ausente. `idadeDerivada("1992-03-14",
      "2026-08-31")` → 34; sem data → `null`. Sem linha de e-mail.
      Rodar e **ver falhar**
      ([data-model.md](./data-model.md))
- [X] T004 Criar `frontend/src/painel/ficha.ts` com os nove rótulos na
      ordem da coleta, `camposAusentes` e `idadeDerivada` até T003
      verde. Sem JSX. Sem `fetch`
      ([contracts/superficie-da-recepcao.md](./contracts/superficie-da-recepcao.md))

**Checkpoint**: `npm test` verde nas funções puras. Destino ficha ainda
é título.

---

## Phase 3: User Story 1 - Abrir a ficha e ver o que falta (Priority: P1) 🎯 MVP

**Goal**: a recepção abre a ficha do titular pela fila, distingue
completa/parcial com ausentes **nomeados**, sem e-mail, idade só
derivada, menu sem reserva sem fetch. Leitura humana sem corpo da
mensagem. Falha de GET ≠ ficha de outra pessoa.

**Independent Test**: Vitest — mock de `GET /reservas/1042/ficha`
parcial nomeia cada ausente; completa não lista falta; `/ficha` sem
id **não** chama GET; `Ver ficha` na fila navega para `/ficha/1042`;
idade não é `<input>`; GET 500 declara que não carregou.

### Tests for User Story 1

- [X] T005 [US1] Vitest em `frontend/src/painel/TelaFicha.test.tsx`:
      em `/ficha` (sem id) **zero** chamadas a `/reservas/`; texto de
      que a ficha se abre pela fila; atalho de volta à fila. Em
      `/ficha/1042`, `GET /reservas/1042/ficha` com
      `credentials: "include"`; distintivo completa vs parcial;
      ausentes nomeados via `camposAusentes`; **nenhum** campo e-mail;
      com `data_nascimento` a idade aparece como texto, não como
      input gravável. `MemoryRouter` basename `/app` + `fetch` falso.
      Rodar e **ver falhar**
      ([contracts/superficie-da-recepcao.md](./contracts/superficie-da-recepcao.md),
      [contracts/api-reusada.md](./contracts/api-reusada.md))
- [X] T006 [US1] No mesmo `frontend/src/painel/TelaFicha.test.tsx`:
      `estado_cadastro === "leitura_humana"` mostra aviso de leitura
      humana e **não** renderiza o conteúdo de mensagem; `GET` 500
      (ou rede) declara que a ficha não carregou, oferece tentar de
      novo e voltar à fila, **não** usa o estado vazio do menu; 404
      não inventa nome. Rodar e **ver falhar**
- [X] T007 [US1] Estender `frontend/src/painel/TelaFila.test.tsx`:
      cada linha tem controle rotulado **Ver ficha** que navega para
      `/ficha/{id_reserva}`; clique no nome **não** dispara
      `POST .../chegada` (regressão F8.2). Rodar e **ver falhar**

### Implementation for User Story 1

- [X] T008 [US1] Criar `frontend/src/painel/TelaFicha.tsx`: lê
      `idReserva` de `useParams`; sem id → estado vazio (T005);
      com id → `pedirAutenticado("/reservas/{id}/ficha")`; nove
      campos, distintivo, lista de ausentes, idade derivada, aviso
      de leitura humana, falha/carregando. Sem PUT, sem copiar, sem
      consentimento, sem e-mail. Título **Ficha do hóspede**. Até
      T005 e T006 verdes
- [X] T009 [US1] Em `frontend/src/painel/Casca.tsx`,
      `destino.id === "ficha"` renderiza `TelaFicha`. Em
      `frontend/src/painel/TelaFila.tsx`, **Ver ficha** (link) na
      coluna ação. Em `Casca.test.tsx`, `fetchPorPerfil` pode
      responder `GET /reservas/`…`/ficha` com 200 mínimo **só se**
      algum caso abrir `/ficha/…`; `/ficha` vazio não deve GET.
      Até T007 verde. Rodar `npm test` em `frontend/`

**Checkpoint**: recepção abre e lê a ficha. Gravar, copiar e
consentimento ainda não.

---

## Phase 4: User Story 2 - Completar no balcão o que o canal não trouxe (Priority: P1)

**Goal**: `PUT /reservas/{id}/ficha` grava os nove campos, sem
mensagem ao hóspede; `ficha_parcial` ↔ `ficha_recebida` no gatilho;
hospedado não muda de fase; a tela edita e grava; fila deixa de
mostrar parcial ao voltar.

**Independent Test**: pytest — PUT completo em reserva `ficha_parcial`
vira `ficha_recebida`, `ficha_completa true`, zero linha em `trabalho`;
PUT em `hospedado` mantém status; staff 403; telefone ilegível 422;
documento duplicado não funde. Vitest — Gravar chama PUT com os nove
campos; 422 nomeia o campo; Cancelar não PUT; nenhum fetch de
webhook/simulador.

### Tests for User Story 2

- [X] T010 [P] [US2] Em
      `testes/integracao/test_garantias_do_banco.py`, incluir
      `("ficha_parcial", "ficha_recebida")` e
      `("ficha_recebida", "ficha_parcial")` em `TRANSICOES_ACEITAS`
      (e o caminho `CAMINHO_ATE` que o arquivo exigir). Rodar
      `pytest testes/integracao/test_garantias_do_banco.py -q` e
      **ver falhar** no UPDATE recusado pelo gatilho atual
      ([data-model.md](./data-model.md))
- [X] T011 [P] [US2] Unitários em
      `testes/unitarios/modulos/hospedagem/test_completar_ficha.py`:
      nove campos válidos em titular `ficha_parcial` →
      `atualizar_hospede_titular` + `marcar_ficha_completa(true)` +
      `atualizar_status_reserva("ficha_recebida")`; incompleto
      permanece parcial; `hospedado` atualiza campos/flag e **não**
      muda status; corpo com `idade` ignora idade; telefone da ficha
      não chama update de `telefone_contato`. Repo falso, sem SQL.
      Rodar e **ver falhar**
      ([contracts/api-alterar-ficha.md](./contracts/api-alterar-ficha.md))
- [X] T012 [P] [US2] Integração em
      `testes/integracao/test_alterar_ficha.py`: recepção
      `PUT /reservas/{id}/ficha` com nove campos numa
      `ficha_parcial` → `200`, `ficha_completa true`,
      `status_reserva` `ficha_recebida`, `estado_cadastro`
      `completa`, GET da fila **sem** sinal parcial nessa linha;
      `SELECT COUNT(*) FROM trabalho` igual ao de antes do PUT;
      `hospedado` permanece `hospedado`; staff e gestão `403`; outro
      hotel `404`; CEP/telefone/nascimento inválidos `422`; documento
      já de outro hóspede recusa sem fundir. Capturar log: sem nome,
      documento, telefone. Rodar e **ver falhar** (`405` até a rota)

### Implementation for User Story 2

- [X] T013 [US2] Em `docs/04-schema.sql`, no corpo de
      `fn_valida_transicao_reserva`, admitir
      `ficha_parcial` ↔ `ficha_recebida`. Criar
      `alembic/versions/sql/0024_ficha_parcial_completa.sql` e
      `alembic/versions/0024_ficha_parcial_completa.py`
      (`down_revision = "0023_convite_boas_vindas"`) com
      `CREATE OR REPLACE FUNCTION` equivalente. Até T010 verde.
      `pytest testes/integracao/test_conformidade_do_esquema.py -q`
      e `test_inventario.py` verdes
      ([plan.md](./plan.md) ponto de atenção 5)
- [X] T014 [US2] Implementar `completar_ficha_titular` em
      `app/modulos/hospedagem/service.py` (validação = funções puras
      de `app/modulos/conversa/validacao_ficha.py`; se o import
      puxar `conversa.service`, mover o arquivo puro para
      `app/modulos/hospedagem/validacao_ficha.py` e ajustar o import
      da conversa — um arquivo, dois chamadores). Reusar
      `atualizar_hospede_titular` e `marcar_ficha_completa` em
      `app/modulos/hospedagem/repository.py`. **Não** enfileirar
      trabalho. Até T011 verde
      ([research.md](./research.md) §3)
- [X] T015 [US2] `FichaTitularEntrada` em
      `app/modulos/hospedagem/schema.py` (nove campos, sem idade, sem
      e-mail). `PUT` em `app/modulos/hospedagem/router.py` com
      `exigir_operacao("alterar_ficha_de_hospede")`, `200` no mesmo
      shape do GET, `422`/`404`/`409`. Não alterar `politica.py`.
      Até T012 verde
- [X] T016 [US2] Estender `frontend/src/painel/TelaFicha.test.tsx`:
      Gravar faz `PUT /reservas/1042/ficha` com os nove campos do
      formulário; `422` mostra o detalhe e não afirma completa;
      Cancelar não PUT; após `200` o distintivo segue o JSON; nenhum
      `fetch` para `/webhook` nem `/simulador`. Rodar e **ver falhar**
- [X] T017 [US2] Em `frontend/src/painel/TelaFicha.tsx`, Editar /
      Gravar / Cancelar até T016 verde. Recusa de telefone na
      digitação pode reusar `frontend/src/painel/telefone.ts`. Sem
      copiar, sem consentimento

**Checkpoint**: completar no balcão grava e a fila deixa de mentir
parcial. Copiar e consentimento ainda não.

---

## Phase 5: User Story 3 - Copiar a ficha para colar no sistema de gestão (Priority: P1)

**Goal**: **Copiar tudo** gera o bloco rotulado das nove linhas no
cliente; clipboard falso é chamado; fallback selecionável se a cópia
automática falhar. Sem idade, sem e-mail, sem PMS.

**Independent Test**: Vitest — `montarTextoCopia` tem os nove
rótulos; campo vazio entra sem valor inventado; acionar Copiar tudo
chama `writeText` com esse texto; mock rejeitado → o texto continua
na tela selecionável.

### Tests for User Story 3

- [X] T018 [P] [US3] Estender `frontend/src/painel/ficha.test.ts`:
      `montarTextoCopia` — nove linhas na ordem da coleta;
      `Nome completo:` com valor; campo `null` → rótulo sem valor;
      **não** contém `Idade` nem `E-mail` nem corpo de mensagem.
      Data visível `dd/mm/aaaa`. Rodar e **ver falhar**
      ([contracts/superficie-da-recepcao.md](./contracts/superficie-da-recepcao.md))
- [X] T019 [US3] Estender `frontend/src/painel/TelaFicha.test.tsx`:
      controle visível **Copiar tudo**; clique chama
      `navigator.clipboard.writeText` com o retorno de
      `montarTextoCopia`; se `writeText` rejeitar, o mesmo texto
      aparece em elemento selecionável (ex. `pre`). Rodar e **ver
      falhar**

### Implementation for User Story 3

- [X] T020 [US3] Em `frontend/src/painel/ficha.ts`, exportar
      `montarTextoCopia` até T018 verde. Sem `fetch`
- [X] T021 [US3] Em `frontend/src/painel/TelaFicha.tsx`, gesto
      principal **Copiar tudo** até T019 verde. Sem rota nova. Sem
      afirmar que o sistema de gestão gravou

**Checkpoint**: uma variação de cópia na tela. Consentimento ainda não.

---

## Phase 6: User Story 4 - Ver o consentimento com data e poder revogar (Priority: P1)

**Goal**: bloco na ficha com vigente datado, nunca registrado, revogar
e aceite no balcão via `POST` `origem: "painel"`. Sem mensagem nova.

**Independent Test**: Vitest — GET consentimento após a ficha;
aceite mostra data; `concedido: false` sem `momento` ≠ recusa
datada; Revogar POST `{concedido:false, origem:"painel"}`; aceite
POST `{concedido:true, origem:"painel"}`.

### Tests for User Story 4

- [X] T022 [US4] Estender `frontend/src/painel/TelaFicha.test.tsx`:
      depois do GET da ficha, `GET /hospedes/{id_hospede}/consentimento`;
      três estados (aceite+momento, recusa+momento, sem momento);
      **Revogar** no aceite; registrar aceite no nunca registrado;
      origem **sempre** `painel`; nenhum POST com
      `pesquisa_checkout`. Rodar e **ver falhar**
      ([contracts/api-reusada.md](./contracts/api-reusada.md))

### Implementation for User Story 4

- [X] T023 [US4] Em `frontend/src/painel/TelaFicha.tsx`, bloco
      Consentimento até T022 verde. Usar o `id_hospede` do GET da
      ficha. Não criar tela de gestão. Não alterar rotas de
      consentimento em `app/modulos/hospedagem/router.py` (já F4.1)

**Checkpoint**: consentimento visível e revogável na ficha.

---

## Phase 7: User Story 5 - Só a recepção vê e edita esta ficha (Priority: P1)

**Goal**: staff e gestão não montam a ficha (com ou sem id) e não
disparam GET/PUT de ficha nem consentimento. API continua 403/404
como T012.

**Independent Test**: Vitest — sessão `staff` ou `gestor` em
`/app/ficha` e `/app/ficha/1` cai na casa do papel; `fetch` não é
chamado para `/reservas/`…`/ficha` nem `/hospedes/`…`/consentimento`.

### Tests for User Story 5

- [X] T024 [US5] Estender `frontend/src/painel/Casca.test.tsx`: com
      perfil `staff` e `gestor`, abrir `/ficha` e `/ficha/1` **não**
      renderiza nome, documento nem telefone de hóspede e **não**
      chama GET/PUT de ficha nem GET/POST de consentimento. Rodar e
      **ver falhar** se `TelaFicha` montar antes do `Navigate`
      ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))

### Implementation for User Story 5

- [X] T025 [US5] Ajustar `frontend/src/painel/Casca.tsx` se T024
      falhar por montar `TelaFicha` antes do redirecionamento (o
      `Navigate` por perfil deve ganhar; T002 já trata o prefixo).
      Não mudar `app/modulos/acesso/politica.py`. Até T024 verde

**Checkpoint**: minimização na superfície. PUT 403 de T012 continua o
portão HTTP.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: log, estado do projeto, suíte inteira.

- [X] T026 [P] Varredura em `frontend/src/painel/TelaFicha.tsx` e
      `ficha.ts`: zero `console.log` de ficha, texto de cópia,
      consentimento ou corpo do PUT. Em
      `app/modulos/hospedagem/service.py`, o `PUT` loga só
      identificadores, status e contagem — como
      [contracts/logs.md](./contracts/logs.md)
- [X] T027 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F8.3
      concluída quando o quickstart passar; registrar que **copiar
      tudo** (uma variação) entrou nesta fatia e que ordem
      configurável / cópia campo a campo continuam fora; próxima
      fatia F8.4. Sem inventar integração PMS. Sinalizar a
      divergência da linha “auxílios de transcrição = evolução
      futura” ([research.md](./research.md) divergência 2)
- [X] T028 Rodar `npm test` em `frontend/` e, na raiz,
      `pytest testes/unitarios -q` mais
      `pytest testes/integracao -q -k "ficha or consentimento or transicao or inventario or conformidade or sessao or casca"`.
      Tudo verde. Conferir o roteiro de
      [quickstart.md](./quickstart.md) (casos Vitest/pytest cobertos;
      browser só como checagem humana, não tarefa de Playwright)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: começa agora — prefixo do destino ficha
- **Foundational (Phase 2)**: depende do Setup — **bloqueia** as histórias
- **US1 (Phase 3)**: depois da Foundational — MVP
- **US2 (Phase 4)**: depois da US1 (grava na tela que a US1 abriu);
  T010–T012 podem escrever-se em paralelo antes da implementação
- **US3 (Phase 5)**: depois da US1 (precisa da tela). Pode em paralelo
  com o fim da US2 se TelaFicha já existir — o botão Copiar não
  depende do PUT
- **US4 (Phase 6)**: depois da US1 (`id_hospede` na tela)
- **US5 (Phase 7)**: depois de T009 (TelaFicha montada)
- **Polish**: depois das histórias desejadas

### User Story Dependencies

- **US1**: só Foundational (+ Setup de rota)
- **US2**: US1 para a UI; gatilho/serviço/rota são o miolo novo
- **US3**: US1. Independente de US2 (copia o que o GET já mostrou)
- **US4**: US1. Independente de US2/US3
- **US5**: US1 (tela ligada)

### Within Each User Story

- Testes **primeiro**, ver falhar, depois o mínimo para verde
- Função pura / gatilho / serviço antes da rota / JSX que os usa
- História completa antes de avançar prioridade, salvo US3 em
  paralelo após US1

### Parallel Opportunities

- T010, T011 e T012 (três arquivos de teste) depois da US1, antes
  do código de T013–T015
- T018 (`ficha.test.ts`) em paralelo com T016 se T004 já verde —
  **não** paralelizar T018 com T003 incompleto
- T026 e T027 no polish

---

## Parallel Example: depois da US1

```text
# Testes da US2 em paralelo (arquivos distintos):
Task: T010 test_garantias_do_banco.py
Task: T011 test_completar_ficha.py
Task: T012 test_alterar_ficha.py

# US3 pode começar na tela sem esperar o PUT:
Task: T018 montarTextoCopia em ficha.test.ts
```

T016 e T019 e T022 estendem o mesmo `TelaFicha.test.tsx`: **não**
paralelizar entre si.

T013 e T014 tocam regras diferentes (SQL vs service) e podem
seguir em sequência curta, não no mesmo commit se o gatilho ainda
não passou — T014 depende da transição ser legal no banco só no
teste de integração (T012), não no unitário (T011).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: recepção abre a ficha e vê o que falta. Sem gravar, o
   balcão ainda não completa; sem copiar, a transcrição não tem o
   gesto principal

### Incremental Delivery

1. Setup + Foundational
2. US1 → demo da leitura
3. US2 → demo do completar (é a que precisa da `0024`)
4. US3 → demo do copiar tudo
5. US4 → demo do consentimento
6. US5 → trava de perfil
7. Polish + estado do projeto

### Parallel Team Strategy

Um desenvolvedor (prazo da semana): ordem US1 → US2 → US3 → US4 → US5.
US3 pode entrar logo após US1 se a demo da banca precisar do botão
copiar antes da gravação.

---

## Notes

- [P] só com arquivos distintos e dependência já verde
- Sem Playwright, sem operação nova em `politica.py`, sem worker
- Sem e-mail, sem foto, sem idade persistida, sem PMS
- Não usar `onClick` na linha da fila para abrir a ficha — rótulo
  **Ver ficha**; nome/telefone não confirmam chegada
- `PUT` não enfileira coleta
- Telefone da ficha ≠ `reserva.telefone_contato`
- Commit por história (não por tarefa) salvo o usuário pedir o
  contrário — o ciclo TDD da casa é teste → falha → código → verde
