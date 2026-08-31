---
description: "Task list for feature implementation"
---

# Tasks: Casca do painel e login

**Input**: Design documents from `/specs/028-casca-painel-login/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md),
[research.md](./research.md), [data-model.md](./data-model.md),
[contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de
produção sem teste que falhe antes pelo motivo certo. Nenhum teste abre
navegador (Playwright fora). Nenhum teste chama PMS. `fetch` da casca é
falso no Vitest; pytest cobre cookie, mount e redirect.

**Organization**: Tarefas agrupadas por história (US1–US6), na ordem da spec.
Dependências npm, mapa `destinos.ts`, cookie `Secure` e o esqueleto do
router entram na Foundational. US1 é o MVP (entrar e cair na casa do
papel). US2–US4 fecham recusa, recarga e sair (P1). US5 é o menu e o
simulador como rota (P2). US6 é sessão vencida sem tela morta (P2).
Sem migração. Sem operação nova na matriz. Worker intocado.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US6)

## Como ver os testes falharem nesta fatia

**Mapa.** `destinoInicial("recepcao")` ainda não existe:
`destinos.test.ts` falha com `ReferenceError` / módulo ausente. Depois
do arquivo vazio, falha porque `staff` não cai em `/app/chamados`.

**Cookie.** `POST /sessoes` em `base_url="http://testserver"` ainda manda
`Secure` no `Set-Cookie`: o caso novo em
`testes/integracao/test_cookie_sessao_secure.py` falha até
`_definir_cookie` em `app/modulos/acesso/router.py` olhar o esquema.
O caso HTTPS continua exigindo `Secure`.

**Entrada.** Vitest com `fetch` falso: sem `TelaEntrada`, o teste não
acha o formulário. Sem `POST /sessoes`, não chama a URL. Sem redirect,
recepção não vê o título **Fila do dia**.

**Recusa.** Dois 401 (e-mail inexistente vs senha errada) com textos
diferentes: o teste da US2 falha. Campos em branco que disparam POST e
mostram “Credenciais inválidas” também falham — o aviso tem que ser de
campo, não de credencial.

**Sair.** Sem `DELETE /sessoes/atual`, o teste da US4 não vê a chamada.
Remount com `GET /sessoes/atual` 401 ainda mostrando a casa: falha.

**Menu.** Recepção com item **Meus chamados** ou staff com **Simulador**:
`Casca.test.tsx` falha. Navegar para `/app/chamados` autenticado como
recepção e ver o título da equipe: falha da US5.

**401 no meio.** `fetch` de um destino devolvendo 401 e a tela da casa
permanecer: falha da US6.

**Mount.** Sem `frontend/dist`, a API não pode 500. Com dist temporário,
`GET /app/` ausente é `404` até `app/main.py` montar `/app`.
`PREFIXOS_IGNORADOS` em `testes/integracao/test_rotas_protegidas.py`
ainda só tem `/demo`: o mount `/app` pode aparecer como rota “desprotegida”
— incluir `/app` no ignore **no mesmo commit** do mount.

---

## Phase 1: Setup

**Purpose**: o `frontend/` já existe (F6.2). Acrescentar o que a casca
precisa para testar e desenhar. Sem mudar `TelaSimulacao` ainda (a banca
não pode perder o login embutido antes da US1+US5). Sem montar `/app`
ainda.

- [X] T001 Acrescentar em `frontend/package.json` as dependências
      `react-router-dom`, `vitest`, `@testing-library/react`,
      `@testing-library/jest-dom`, `jsdom`, `tailwindcss` e o plugin
      Vite do Tailwind (versão compatível com Vite 6). Script `"test":
      "vitest run"`. Rodar `npm install` em `frontend/`. Sem Playwright
      ([research.md](./research.md) §4 e §7)
- [X] T002 Em `frontend/vite.config.ts`: `base: "/app/"`; `test`
      (environment `jsdom`); proxy das raízes de API já usadas e das
      que faltam (`/solicitacoes`, `/catalogo`, `/indicadores`,
      `/propriedade`, `/consumos`, `/concorrentes`, `/mercado`,
      `/retencao`, `/usuarios`, `/webhook`). Não proxiar `/app`
      ([contracts/casca-e-rotas.md](./contracts/casca-e-rotas.md))
- [X] T003 [P] Ligar Tailwind em `frontend/src/index.css` e importar
      em `frontend/src/main.tsx`. Sem tema extra
- [X] T004 [P] Copiar para `frontend/src/components/ui/` só `button`,
      `input` e `label` (shadcn, sem runtime). Helper `cn` em
      `frontend/src/lib/utils.ts` se o recorte exigir. Sem CLI shadcn
      a cada build

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: mapa de destinos, cookie que gruda em HTTP local, cliente
de sessão sem token em script, esqueleto do router. **Nenhuma tela de
entrada ainda. Não apagar o login do simulador.**

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase.

- [X] T005 Unitários em `frontend/src/painel/destinos.test.ts`:
      `destinoInicial` — `recepcao` → `/app/fila`, `staff` →
      `/app/chamados`, `gestor` → `/app/indicadores`; `itensMenu`
      — recepção vê `fila` e `simulador` e não vê `chamados` nem
      `indicadores`; staff vê só `chamados`; gestão vê `indicadores` e
      `simulador` e não vê `fila` nem `chamados`. Rodar `npm test` em
      `frontend/` e **ver falhar**
      ([contracts/destinos-por-perfil.md](./contracts/destinos-por-perfil.md))
- [X] T006 Criar `frontend/src/painel/destinos.ts` com o mapa completo
      do contrato (casas + destinos nomeados + simulador) até T005
      verde. Sem JSX
- [X] T007 [P] Integração em
      `testes/integracao/test_cookie_sessao_secure.py`: `POST /sessoes`
      com credencial válida, `TestClient(..., base_url="http://testserver")`
      — `Set-Cookie` de `omnistay_sessao` **sem** `Secure`, **com**
      `HttpOnly` e `SameSite=strict`; o mesmo com
      `base_url="https://testserver"` **com** `Secure`. Corpo sem o
      token. Rodar e **ver falhar**
      ([contracts/sessao-no-navegador.md](./contracts/sessao-no-navegador.md))
- [X] T008 Em `app/modulos/acesso/router.py`, `_definir_cookie` usa
      `secure=(pedido.url.scheme == "https")` até T007 verde. Não mudar
      nome, `HttpOnly`, `SameSite` nem `Path`
- [X] T009 [P] Unitários em `frontend/src/painel/sessao.test.ts`:
      `entrar` faz `POST /sessoes` com `credentials: "include"` e JSON
      `{email, senha}` — **não** grava nada em `localStorage` /
      `sessionStorage`; `obterAtual` faz `GET /sessoes/atual` com
      `credentials: "include"`; `sair` faz `DELETE /sessoes/atual`.
      `fetch` mockado. Rodar e **ver falhar**
- [X] T010 Criar `frontend/src/painel/sessao.ts` até T009 verde. Sem
      UI. Sem ler `document.cookie`
- [X] T011 Em `frontend/src/main.tsx`, `BrowserRouter` com
      `basename="/app"` e rotas para cada `caminho` de `destinos.ts`
      mais `/entrar`, apontando para um placeholder (`<p>casca</p>`).
      Título do documento em `frontend/index.html`: painel, não só
      “simulador”. Sem formulário ainda

**Checkpoint**: `npm test` e o pytest do cookie verdes. O simulador
antigo em `/demo/` **quebra no Vite** (base mudou) — esperado; a US5
restaura o fio em `/app/simulador`.

---

## Phase 3: User Story 1 - Entrar e cair na tela do próprio papel (Priority: P1) 🎯 MVP

**Goal**: e-mail e senha válidos levam cada perfil à casa identificável
pelo título, sem seletor. Quem já tem sessão e abre a entrada vai à
casa.

**Independent Test**: Vitest — `fetch` de `POST /sessoes` 201 com
`perfil: "recepcao"` renderiza **Fila do dia**; `staff` → **Meus
chamados**; `gestor` → **Painel**. `GET /sessoes/atual` 200 em `/entrar`
redireciona à casa.

### Tests for User Story 1

- [X] T012 [P] [US1] Vitest em
      `frontend/src/painel/TelaEntrada.test.tsx`: formulário e-mail,
      senha e Entrar; campos em branco **não** chamam `fetch`; submit
      válido chama `POST /sessoes`. Rodar e **ver falhar**
- [X] T013 [P] [US1] Vitest em `frontend/src/painel/Casca.test.tsx`:
      depois de sessão com cada perfil, a casa mostra o título do
      contrato; autenticado em `/entrar` não permanece na entrada.
      `MemoryRouter` + `fetch` falso. Rodar e **ver falhar**

### Implementation for User Story 1

- [X] T014 [US1] Criar `frontend/src/painel/TelaEntrada.tsx` (campos
      shadcn, chama `entrar` de `sessao.ts`) até T012 verde
- [X] T015 [US1] Criar `frontend/src/painel/Casca.tsx` e
      `frontend/src/painel/TelaNomeada.tsx`: no carregamento chama
      `obterAtual`; sem sessão mostra a entrada; com sessão navega à
      `destinoInicial(perfil)` e renderiza o `titulo`. Staff em
      `/app/chamados` usa layout compacto (sem menu lateral longo).
      Ligar as rotas em `frontend/src/main.tsx` até T013 verde
      ([contracts/casca-e-rotas.md](./contracts/casca-e-rotas.md))

**Checkpoint**: três perfis entram e vêem o título da casa. Recusa e
menu ainda não são desta história.

---

## Phase 4: User Story 2 - Credencial inválida não ensina quem existe (Priority: P1)

**Goal**: e-mail inexistente, senha errada e usuário desativado produzem
o mesmo aviso; a pessoa permanece na entrada. Branco não se disfarça de
“não encontrado”.

**Independent Test**: Vitest — dois `POST` 401 (corpos idênticos) mostram
o mesmo texto; não há “e-mail não cadastrado”; branco não dispara POST.

### Tests for User Story 2

- [X] T016 [US2] Estender `frontend/src/painel/TelaEntrada.test.tsx`:
      401 → permanece em `/entrar`, um único texto de recusa; dois 401
      seguidos (mensagens de servidor distintas, se houver) **não**
      mudam o texto visível; `staff` desativado (401) usa o mesmo
      texto. Rodar e **ver falhar**
      ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))

### Implementation for User Story 2

- [X] T017 [US2] Em `frontend/src/painel/TelaEntrada.tsx`, tratar todo
      401 como o mesmo aviso (“Credenciais inválidas.” ou equivalente
      único). Não interpolar `detail` da API. T016 verde. Não logar
      senha em `console` ([contracts/logs.md](./contracts/logs.md))

**Checkpoint**: a tela de entrada não vaza existência de e-mail.

---

## Phase 5: User Story 3 - Continuar reconhecido no mesmo dispositivo (Priority: P1)

**Goal**: recarregar (remount) com sessão válida mantém a casa, sem
código de sessão em armazenamento de script.

**Independent Test**: Vitest — montar a casca, `GET /sessoes/atual`
200, desmontar e montar de novo: continua na casa, zero chave de token
em `localStorage`/`sessionStorage`.

### Tests for User Story 3

- [X] T018 [US3] Estender `frontend/src/painel/Casca.test.tsx` (ou
      `frontend/src/painel/sessao.test.ts`): remount com `obterAtual`
      200 permanece na casa sem segundo `POST /sessoes`; depois das
      chamadas, `localStorage` e `sessionStorage` não contêm
      `omnistay_sessao` nem `token`. Rodar e **ver falhar**

### Implementation for User Story 3

- [X] T019 [US3] Garantir em `frontend/src/painel/Casca.tsx` e
      `frontend/src/painel/sessao.ts` que a persistência é só o cookie
      (`credentials: "include"`). Qualquer estado de perfil vive em
      memória e é reobtido no mount. T018 verde

**Checkpoint**: F5. recarga = `GET /sessoes/atual`, não “lembrar-me”
paralelo.

---

## Phase 6: User Story 4 - Sair encerra de verdade (Priority: P1)

**Goal**: Sair chama o servidor, volta à entrada, recarga não restaura.

**Independent Test**: Vitest — clique Sair dispara `DELETE /sessoes/atual`;
o `GET` seguinte 401 mostra a entrada, não a casa.

### Tests for User Story 4

- [X] T020 [US4] Estender `frontend/src/painel/Casca.test.tsx`:
      autenticado vê Sair; clicar chama `DELETE /sessoes/atual` com
      `credentials: "include"`; em seguida a entrada aparece; remount
      com `GET` 401 não mostra título de casa. Rodar e **ver falhar**

### Implementation for User Story 4

- [X] T021 [US4] Ação Sair em `frontend/src/painel/Casca.tsx` chama
      `sair()` de `sessao.ts`, limpa estado em memória e navega a
      `/entrar`. T020 verde. Não encerrar outras sessões (a API já
      só invalida a atual)

**Checkpoint**: sair não é esconder a tela.

---

## Phase 7: User Story 5 - O menu só oferece o que o papel pode usar (Priority: P2)

**Goal**: menu filtrado por perfil; endereço alheio não mostra o conteúdo
alheio; simulador é rota da casca (sem login embutido); destinos futuros
são tela nomeada só com título.

**Independent Test**: Vitest — recepção não vê Meus chamados nem Painel;
staff não vê Fila nem Simulador; gestão não vê Fila nem Meus chamados.
`/app/chamados` como recepção não renderiza **Meus chamados**.
`/app/catalogo` como recepção mostra **Catálogo** e nenhum hóspede
inventado.

### Tests for User Story 5

- [X] T022 [P] [US5] Estender `frontend/src/painel/Casca.test.tsx`:
      itens visíveis = `itensMenu(perfil)` (títulos do contrato);
      staff sem Simulador; gestão sem Fila e sem Meus chamados;
      recepção com Simulador. Rodar e **ver falhar**
- [X] T023 [P] [US5] Vitest em
      `frontend/src/painel/TelaNomeada.test.tsx` (ou na Casca):
      recepção em `/app/chamados` **não** vê o título Meus chamados
      (cai na casa ou recusa visível); recepção em `/app/catalogo`
      vê só o título **Catálogo**, sem lista fictícia. Rodar e **ver
      falhar**
- [X] T024 [P] [US5] Vitest: rota `/app/simulador` com sessão de
      recepção renderiza a tela de simulação **sem** campos e-mail/
      senha; sessão staff nessa rota não mostra o fio. Rodar e **ver
      falhar** (arquivo
      `frontend/src/painel/Casca.test.tsx` ou
      `frontend/src/TelaSimulacao.test.tsx`)

### Implementation for User Story 5

- [X] T025 [US5] Menu em `frontend/src/painel/Casca.tsx` a partir de
      `itensMenu`. Destino fora do mapa do perfil: `Navigate` para a
      casa, sem renderizar `TelaNomeada` alheia. T022 e T023 verdes
- [X] T026 [US5] Rotas nomeadas em `frontend/src/main.tsx` usam
      `TelaNomeada` com o `titulo` de `destinos.ts`. Zero `fetch`
      operacional nessas rotas
- [X] T027 [US5] Em `frontend/src/TelaSimulacao.tsx`, remover o
      formulário de login e o estado `precisaLogin` de entrada;
      401 deve subir (rethrow / callback) para a casca. Registrar a
      rota `/simulador` na casca. T024 verde. **Não** alterar
      `/simulador/conversas`
      ([research.md](./research.md) §8)

**Checkpoint**: o mapa do papel é visível; o simulador voltou a ser
alcançável pela casca.

---

## Phase 8: User Story 6 - Sessão vencida devolve à entrada, sem tela morta (Priority: P2)

**Goal**: 401 no meio do uso (expirada ou revogada) volta à entrada com
aviso, sem página em branco e sem dado residual.

**Independent Test**: Vitest — casca na casa, próximo `fetch` 401 →
entrada visível, títulos da casa ausentes, aviso de sessão.

### Tests for User Story 6

- [X] T028 [US6] Estender `frontend/src/painel/Casca.test.tsx` (e
      `sessao.ts` se houver wrapper): com sessão, um `fetch` 401
      (`{"detail":"Sessao ausente ou invalida."}`) navega a `/entrar`,
      não deixa a casa montada, não deixa tela vazia sem mensagem.
      Rodar e **ver falhar**

### Implementation for User Story 6

- [X] T029 [US6] Wrapper em `frontend/src/painel/sessao.ts` (ou
      tratamento na `Casca`) para 401: limpar estado e ir à entrada
      com aviso único de sessão (distinto da recusa de senha da US2).
      T028 verde. Não distinguir expiração de revogação na tela

**Checkpoint**: sessão morta ≠ tela branca.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: a API serve o SPA; o atalho `/demo` não some; a suíte HTTP
não trata `/app` como furo de sessão; estado do projeto.

- [X] T030 Integração em `testes/integracao/test_casca_painel.py`: com
      um `frontend/dist` temporário (index.html mínimo), `criar_aplicacao`
      (ou equivalente) responde `GET /app/` e `GET /app/entrar` com HTML,
      **não** 500 se `dist` ausente. Rodar e **ver falhar**. Acrescentar
      `/app` a `PREFIXOS_IGNORADOS` em
      `testes/integracao/test_rotas_protegidas.py` no mesmo passo em
      que o mount existir — senão o teste de rotas protegidas quebra
      pelo motivo errado
- [X] T031 Em `app/main.py`, montar `frontend/dist` em `/app`
      (`StaticFiles`, `html=True`) no lugar de `/demo`. Redirect
      `GET /demo` e `GET /demo/` → `/app/simulador`. T030 verde.
      Dist ausente: a API sobe igual
      ([contracts/casca-e-rotas.md](./contracts/casca-e-rotas.md))
- [X] T032 [P] Estender `testes/integracao/test_casca_painel.py`:
      `GET /demo` → 307/308 (ou 302) com `Location` contendo
      `/app/simulador`. Sem cookie
- [X] T033 [P] Atualizar o atalho em
      `specs/024-simulador-conversa/quickstart.md` (e o contrato de
      tela, se citar `/demo/` como casa) para `/app/simulador`,
      registrando o redirect
- [X] T034 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F8.1 em
      implementação/concluída conforme o ponto da entrega; painel
      deixa de ser “só `/docs`”; simulador não é mais a única página
- [X] T035 Confirmar que `app/modulos/acesso/politica.py` **não** ganhou
      operação nova; `pytest testes/unitarios/modulos/acesso/test_politica.py`
      continua verde
- [X] T036 Rodar `pytest testes/unitarios -q`, `pytest testes/integracao -q
      -k "sessao or sessoes or casca or cookie or rotas_protegidas"`,
      `npm test` em `frontend/`, e o roteiro de
      [quickstart.md](./quickstart.md) (Vite + três perfis no
      navegador — único passo manual; a CI não abre Chrome)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: começa agora
- **Foundational (Phase 2)**: depois do Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: depois da Foundational — MVP
- **US2 (Phase 4)**: depois da US1 (mesmo `TelaEntrada.tsx`)
- **US3 (Phase 5)**: depois da US1 (`Casca` já consulta `obterAtual`)
- **US4 (Phase 6)**: depois da US1 (Sair no chrome)
- **US5 (Phase 7)**: depois da US1 (menu + simulador). **Não** remover
  o login do simulador antes da US1 estar verde
- **US6 (Phase 8)**: depois da US1 (wrapper 401). Melhor depois da US4
  para o aviso de sessão não se misturar com Sair
- **Polish (Phase 9)**: depois das histórias desejadas; T030/T031 podem
  esperar o Vite já provar as USs

### User Story Dependencies

- **US1**: só Foundational
- **US2**: US1 (formulário existe)
- **US3**: US1 (casca com `obterAtual`)
- **US4**: US1 (chrome autenticado)
- **US5**: US1; TelaSimulacao só depois da entrada da casca
- **US6**: US1; idealmente US4 (Sair vs 401)

US2, US3 e US4 tocam os **mesmos** arquivos (`TelaEntrada.tsx`,
`Casca.tsx`, `sessao.ts`): um desenvolvedor as faz em série.

### Parallel Opportunities

- T003 e T004 depois de T001
- T005, T007 e T009 depois da Foundational começar
- T012 e T013 depois da US1 começar
- T022, T023 e T024 depois da US5 começar
- T032, T033 e T034 no Polish

### Parallel Example: Foundational

```text
T005  frontend/src/painel/destinos.test.ts
T007  testes/integracao/test_cookie_sessao_secure.py
T009  frontend/src/painel/sessao.test.ts
```

Depois, em série por arquivo: T006 → (T011 usa destinos); T008; T010.

### Parallel Example: User Story 5

```text
T022  Casca.test.tsx (menu)
T023  TelaNomeada / endereço alheio
T024  simulador sem login
```

Depois: T025 → T026 → T027.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: os três perfis entram e vêem o título da casa no Vite
4. Recusa indistinguível, Sair e menu ainda não existem — a banca já
   vê *algum* painel

### Incremental Delivery

1. Setup + Foundational
2. US1 → entrar / casa (MVP)
3. US2 → recusa honesta
4. US3 → recarga
5. US4 → sair de verdade
6. US5 → menu + simulador como rota (a F6.2 volta a ser demonstrável)
7. US6 → sessão morta
8. Polish → `/app` no uvicorn e redirect `/demo`

### Notas para o implementador

- Um desenvolvedor: ordem US1 → US2 → US3 → US4 → US5 → US6
- Commit por história, se o usuário pedir — não commitar sozinho
- Não criar `ver_painel` em `politica.py`
- Não montar o SPA em `/` (quebra `GET /fila-do-dia`)
- Não antecipar `GET /fila-do-dia` na casa da recepção (é F8.2)
- Não inventar hóspede/chamado/KPI nas telas nomeadas
- Cookie `Secure` incondicional faz o quickstart no browser mentir
  “não entra” com pytest verde — T007/T008 existem por isso
- Vitest: `fetch` mockado; `MemoryRouter` com `basename="/app"`
- `npm test` é o portão da casca; `pytest` continua o portão da API
