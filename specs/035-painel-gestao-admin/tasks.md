---
description: "Task list for feature implementation"
---

# Tasks: Painel da gestão, mercado e administração

**Input**: Design documents from `/specs/035-painel-gestao-admin/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md),
[research.md](./research.md), [data-model.md](./data-model.md),
[contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma
linha de produção sem teste que falhe antes pelo motivo certo. Nenhum
teste abre navegador (Playwright fora). Nenhum teste chama PMS,
WhatsApp, IA ou fonte pública. `fetch` é falso no Vitest. pytest cobre
os COUNT/SUM, `GET /indicadores`, `GET /usuarios` e prazos no
`GET /retencao`. Sem migração. Sem operação nova na matriz. Worker
intocado.

**Organization**: Tarefas agrupadas por história (US1–US5), na ordem
da spec. Funções puras de superfície entram na Foundational. US1 é o
MVP (Painel com quatro números). US2 Mercado só leitura. US3 Usuários
sem reativar. US4 Retenção. US5 recepção/staff recusados sem fetch.
Proxy Vite já encaminha os quatro prefixos — não mexer.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US5)

## Como ver os testes falharem nesta fatia

**Funções puras.** Sem `indicadores.ts` / `mercado.ts` /
`usuarios.ts` / `retencao.ts`, os unitários falham com módulo
ausente. Rótulo que inventa “atual” para `so_falha`, prazo `null`
virando 12, ou perfil `staff` sem rótulo: falha.

**Painel.** Sem `TelaPainel`, `/app/indicadores` continua o `<h1>`
da `TelaNomeada`. Vitest que procura os quatro rótulos e zeros
honestos não acha. Tabela com nome de hóspede, gráfico, fichas
antecipadas ou nota média: falha. `GET /fila-do-dia` ou
`GET /solicitacoes` disparado por esta tela: falha. `GET` 500
mostrando zeros como “sem movimento”: falha da US1.

**Números no servidor.** `chamados_abertos` que conta `tipo =
consumo`: falha. `consumo_a_lancar` como COUNT em vez de SUM:
falha. JSON com `itens` ou `id_reserva`: falha. Alterar
`GET /indicadores/chegadas-do-dia`: falha da regressão F1.1.

**Mercado.** Linha “você”, coluna de % 7 dias, `POST /concorrentes`:
falha. Falha recente apresentada como preço de agora: falha.
Histórico com falha virando preço 0: falha.

**Usuários.** Controle **Reativar**, `PATCH`, `GET /sessoes` ou
revogar: falha. Senha na lista: falha. Desativar a própria linha
oferecido: falha. POST com e-mail de desativado que afirma criado:
falha.

**Retenção.** Botão expurgar agora: falha. Nome de hóspede: falha.
Prazo `null` desenhado como 12 ou 5: falha.

**Perfil.** Recepção ou staff em `/app/indicadores` (e irmãos) que
dispara `GET /indicadores` / `/mercado` / `/usuarios` / `/retencao`:
falha da US5.

**Casca.** Ao ligar as telas, `Casca.test.tsx` precisa dos mocks
dos quatro GET. Sem isso a US1 “quebra” a casca com estado de
falha — T001 existe para isso. O teste da gestão em `/indicadores`
que só acha o heading **Painel** continua válido; passa a haver
números (ou zeros) além do título.

---

## Phase 1: Setup

**Purpose**: o `frontend/` da F8.1–F8.6 já tem router, Tailwind,
Vitest e proxy `/indicadores`, `/mercado`, `/usuarios`, `/retencao`.
Esta fase evita regressão da casca quando as quatro telas passarem
a buscar dados. Sem npm novo. Sem Python. Sem linha nova no Vite.

- [X] T001 Em `frontend/src/painel/Casca.test.tsx`, o `fetch` falso
      de `fetchPorPerfil` responde `GET /indicadores` com `200` e
      `{chegadas_hoje:0,hospedados:0,chamados_abertos:0,consumo_a_lancar:0}`,
      `GET /mercado` com `200` e `{periodicidade_horas:24,concorrentes:[]}`,
      `GET /usuarios` com `200` e `{usuarios:[]}` e `GET /retencao`
      com `200` e `{execucoes:[],meses_retencao_conteudo_livre:null,anos_retencao_ficha:null}`.
      Rodar `npm test` em `frontend/` — permanece verde com
      `TelaNomeada` nos quatro destinos. Sem implementar as telas
      novas
      ([plan.md](./plan.md) ponto de atenção 4)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: tipos e funções puras de superfície, testáveis sem
DOM das telas novas. **Nenhuma tela operacional ainda.** Backend
de COUNT ainda não existe (US1). Destinos já são só `gestor`.

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase.

- [X] T002 Unitários em `frontend/src/painel/indicadores.test.ts`:
      tipo com os quatro campos de
      [contracts/api-indicadores.md](./contracts/api-indicadores.md);
      objeto de zeros é válido; **não** há `itens`, nome nem
      `id_reserva` no tipo. Rodar `npm test` em `frontend/` e
      **ver falhar**
- [X] T003 Criar `frontend/src/painel/indicadores.ts`: tipo
      `IndicadoresOperacao` até T002 verde. Sem JSX. Sem `fetch`
- [X] T004 [P] Unitários em `frontend/src/painel/mercado.test.ts`:
      `linhaComFalha` verdadeiro para `so_falha` e para
      `ultima_falha` presente; `linhaAtual` só para `situacao ===
      "atual"`; `semColeta` para `sem_coleta`; preço zero de
      sucesso **não** é tratado como vazio. Rodar e **ver falhar**
      ([contracts/superficie-mercado.md](./contracts/superficie-mercado.md),
      [research.md](./research.md) §3)
- [X] T005 Criar `frontend/src/painel/mercado.ts`: tipo da visão
      atual (campos de `GET /mercado`) e as funções de T004 até
      verde. Sem JSX. Sem `fetch`. Sem variação percentual
- [X] T006 [P] Unitários em `frontend/src/painel/usuarios.test.ts`:
      `rotuloPerfil` para `recepcao` · `staff` · `gestor`;
      `contarSituacao` devolve ativos e desativados (0/0 em lista
      vazia); tipo **sem** senha. Rodar e **ver falhar**
      ([contracts/superficie-usuarios.md](./contracts/superficie-usuarios.md))
- [X] T007 Criar `frontend/src/painel/usuarios.ts`: tipo
      `UsuarioLista`, `rotuloPerfil`, `contarSituacao` até T006
      verde. Sem JSX. Sem `fetch`
- [X] T008 [P] Unitários em `frontend/src/painel/retencao.test.ts`:
      `prazoVisivel(null)` não devolve `12` nem `5`; inteiro ≥ 1
      aparece como número. Rodar e **ver falhar**
      ([contracts/superficie-retencao.md](./contracts/superficie-retencao.md))
- [X] T009 Criar `frontend/src/painel/retencao.ts`: `prazoVisivel`
      até T008 verde. Sem JSX. Sem `fetch`

**Checkpoint**: `npm test` verde nas funções puras. Destinos da
gestão ainda são título.

---

## Phase 3: User Story 1 - Ver números da operação, nunca pessoas (Priority: P1) 🎯 MVP

**Goal**: `GET /indicadores` devolve quatro números puros;
`GET /indicadores/chegadas-do-dia` intacto; Painel mostra os
quatro rótulos, zeros ≠ falha, sem lista nominada.

**Independent Test**: pytest — hospedado conta `status =
hospedado`; chamado aberto não inclui `consumo`; soma pendente ≠
COUNT; JSON sem `itens`/nome; staff `403`. Vitest — gestão em
`/app/indicadores` vê os quatro números via `GET /indicadores`;
não dispara fila/solicitações/consumos; GET 500 não usa o estado
de zeros.

### Tests for User Story 1

- [X] T010 [US1] Unitários em
      `testes/unitarios/modulos/hospedagem/test_indicadores_agregados.py`:
      `contar_hospedados` devolve 1 com uma reserva `hospedado` e
      0 com só `aguardando_cadastro` / `encerrado`; `id_hotel`
      isola o outro hotel. Repositório falso. Rodar `pytest -k
      indicadores_agregados` e **ver falhar**
      ([data-model.md](./data-model.md))
- [X] T011 [P] [US1] Unitários em
      `testes/unitarios/modulos/atendimento/test_indicadores_chamados.py`:
      `contar_chamados_abertos` soma `reclamacao` e `servico` em
      `aberta`/`em_andamento`; **não** conta `tipo=consumo` nem
      `resolvida`/`cancelada`. Rodar e **ver falhar**
- [X] T012 [P] [US1] Unitários em
      `testes/unitarios/modulos/atendimento/test_indicadores_consumo.py`:
      `somar_consumo_pendente` soma `valor_praticado` com
      `status_lancamento = pendente`; `lancado`/`dispensado` fora;
      lista vazia → `0`; dois itens 10 e 20 → `30`. Rodar e **ver
      falhar**
- [X] T013 [US1] Integração em
      `testes/integracao/test_indicadores.py`: gestão `GET
      /indicadores` → `200` com os quatro campos, sem `itens` nem
      nome/telefone/`id_reserva`; hotel vazio → quatro zeros;
      staff → `403`; `GET /indicadores/chegadas-do-dia` continua
      `{quantidade}` (regressão). Rodar e **ver falhar**
      ([contracts/api-indicadores.md](./contracts/api-indicadores.md))
- [X] T014 [P] [US1] Vitest em
      `frontend/src/painel/TelaPainel.test.tsx`: ao montar, `GET
      /indicadores` com `credentials: "include"`; quatro rótulos
      (Chegadas hoje, Hospedados, Chamados em aberto, Consumo a
      lançar) com os valores do mock; **nenhum** `GET
      /fila-do-dia`, `/solicitacoes`, `/consumos/pendentes` nem
      `/indicadores/chegadas-do-dia`; zeros honestos sem recado
      de falha; `GET` 500 → declara que não carregou, tentar de
      novo, **não** mostra zeros; sem gráfico; sem a palavra
      “hóspede” como dado. `MemoryRouter` basename `/app`. Rodar
      e **ver falhar**
      ([contracts/superficie-painel.md](./contracts/superficie-painel.md))

### Implementation for User Story 1

- [X] T015 [US1] Em `app/modulos/hospedagem/repository.py` e
      `service.py`, `contar_hospedados` até T010 verde. Sem
      alterar `contar_chegadas_do_dia`
- [X] T016 [US1] Em `app/modulos/atendimento/repository.py` e
      `service.py`, `contar_chamados_abertos` e
      `somar_consumo_pendente` até T011 e T012 verdes. Sem
      reusar `listar_pendentes` como lista na API de indicadores
- [X] T017 [US1] Em `app/modulos/hospedagem/schema.py` e
      `router.py`, `GET /indicadores` (`ler_indicadores`) monta o
      envelope chamando a contagem de chegadas já existente,
      `contar_hospedados` e as duas funções de atendimento
      (serviço, não repositório). Até T013 verde. Log sem dado
      de hóspede
      ([plan.md](./plan.md) ponto de atenção 2)
- [X] T018 [US1] Criar `frontend/src/painel/TelaPainel.tsx`: no
      mount `pedirAutenticado("/indicadores")`; quatro números;
      falha ≠ zeros; **Tentar de novo**. Título **Painel**. Sem
      tabela nominada. Até T014 verde
- [X] T019 [US1] Em `frontend/src/painel/Casca.tsx`,
      `destino.id === "indicadores"` renderiza `TelaPainel` em
      vez de `TelaNomeada`. Gestão em `/indicadores` continua a
      ver o heading **Painel** e passa a ver os números (ou
      zeros). Rodar `npm test` em `frontend/`

**Checkpoint**: gestão vê quatro números. Mercado, usuários e
retenção ainda são título.

---

## Phase 4: User Story 2 - Comparar o mercado com falha visível (Priority: P1)

**Goal**: Mercado lista `GET /mercado` com data em cada valor,
falha marcada, sem tarifa da casa, sem CRUD de concorrente;
histórico no clique.

**Independent Test**: Vitest — mock com sucesso, falha posterior,
só falha e sem coleta; marcas corretas; clique dispara `GET
/mercado/concorrentes/{id}`; falha no histórico ≠ preço 0; zero
POST/PATCH em `/concorrentes`.

### Tests for User Story 2

- [X] T020 [US2] Vitest em
      `frontend/src/painel/TelaMercado.test.tsx`: ao montar, `GET
      /mercado`; nome, preço/nota com data; `so_falha` e
      `ultima_falha` visíveis como falha; sucesso antigo não
      redatado; `sem_coleta` distinto de zero; **nenhuma** linha
      “você” nem texto de tarifa da casa; zero
      `POST`/`PATCH /concorrentes`. Rodar e **ver falhar**
      ([contracts/superficie-mercado.md](./contracts/superficie-mercado.md),
      [contracts/api-reusada.md](./contracts/api-reusada.md))
- [X] T021 [US2] No mesmo `frontend/src/painel/TelaMercado.test.tsx`:
      clique na linha (controle explícito) → `GET
      /mercado/concorrentes/{id}`; pontos de sucesso com valores;
      falha intercalada sem preço 0; `404` não apaga a visão
      atual. Rodar e **ver falhar**

### Implementation for User Story 2

- [X] T022 [US2] Criar `frontend/src/painel/TelaMercado.tsx`:
      `pedirAutenticado("/mercado")`; marcas via `mercado.ts`;
      histórico só no clique; vazio ≠ falha. Título **Mercado**.
      Sem cadastro de concorrente. Até T020 e T021 verdes
- [X] T023 [US2] Em `frontend/src/painel/Casca.tsx`,
      `destino.id === "mercado"` renderiza `TelaMercado`. Rodar
      `npm test` em `frontend/`

**Checkpoint**: comparativo visível. Usuários e retenção ainda
título.

---

## Phase 5: User Story 3 - Cadastrar e desligar funcionários, sem apagar (Priority: P1)

**Goal**: `GET /usuarios` lista ativos e desativados; POST cria
com perfil e senha ≥ 12; DELETE desativa sem apagar; sem
reativar; sem revogar sessão; sem desativar a si mesmo.

**Independent Test**: pytest — lista sem `senha`/`senha_hash`;
desativado permanece na lista `ativo:false`; e-mail de
desativado → POST `409`. Vitest — **Desativar** na linha alheia;
própria linha sem o controle; zero **Reativar**; zero
`GET /sessoes`.

### Tests for User Story 3

- [X] T024 [US3] Em `testes/integracao/test_usuarios.py` (e
      unitário em `testes/unitarios/modulos/acesso/` se a lista
      for serviço novo): gestão `GET /usuarios` → `200` com
      `usuarios[]` (`id_usuario`, `nome`, `email`, `perfil`,
      `ativo`), sem senha; inclui desativado; recepção/staff
      `403`; isolamento por hotel. Rodar e **ver falhar**
      ([contracts/api-usuarios.md](./contracts/api-usuarios.md))
- [X] T025 [P] [US3] Vitest em
      `frontend/src/painel/TelaUsuarios.test.tsx`: ao montar,
      `GET /usuarios`; colunas nome/e-mail/perfil/situação; linha
      `id_usuario` da sessão (mock `1`) **sem** Desativar; outra
      ativa com **Desativar** → `DELETE /usuarios/{id}` e GET;
      linha `ativo:false` **sem** Reativar; **+ Novo** POST com
      nome, e-mail, perfil, senha; `201` → GET; `422`/`409`
      visíveis; zero `GET /sessoes`; zero `PATCH`. Rodar e **ver
      falhar**
      ([contracts/superficie-usuarios.md](./contracts/superficie-usuarios.md))

### Implementation for User Story 3

- [X] T026 [US3] Em `app/modulos/acesso/repository.py`,
      `service.py`, `schema.py` e `router.py`: `GET /usuarios`
      (`administrar_usuario`), ordem nome+id, hotel da sessão.
      POST/DELETE intocados na regra. Até T024 verde. Log com
      `id_usuario`, sem senha
- [X] T027 [US3] Criar `frontend/src/painel/TelaUsuarios.tsx`:
      lista, criar, desativar; senha só no formulário de novo;
      sem reativar; sem sessões. Título **Usuários**. Até T025
      verde
- [X] T028 [US3] Em `frontend/src/painel/Casca.tsx`,
      `destino.id === "usuarios"` renderiza `TelaUsuarios`. Rodar
      `npm test` em `frontend/`

**Checkpoint**: quadro de acesso na tela. Retenção ainda título.

---

## Phase 6: User Story 4 - Mostrar que o expurgo aconteceu (Priority: P1)

**Goal**: Retenção mostra prazos vigentes (ou não configurado) e
execuções com data, espécie e quantidade; sem disparo; sem dado
de hóspede.

**Independent Test**: pytest — envelope com prazos `null` ou
inteiro, sem default 12/5 no servidor quando a chave falta.
Vitest — tabela de execuções; zeros visíveis; sem botão expurgar.

### Tests for User Story 4

- [X] T029 [US4] Em `testes/integracao/test_retencao.py` (ou
      arquivo da F6.1): gestão `GET /retencao` inclui
      `meses_retencao_conteudo_livre` e `anos_retencao_ficha`
      (`null` se inválidos); `execucoes` como antes; recepção
      `403`. Rodar e **ver falhar**
      ([contracts/api-reusada.md](./contracts/api-reusada.md))
- [X] T030 [P] [US4] Vitest em
      `frontend/src/painel/TelaRetencao.test.tsx`: `GET
      /retencao`; prazos via `prazoVisivel`; linhas com data e
      quantidades (inclusive 0); `execucoes:[]` vazio honesto;
      GET 500 ≠ vazio; **nenhum** controle de disparo; sem nome
      de hóspede. Rodar e **ver falhar**
      ([contracts/superficie-retencao.md](./contracts/superficie-retencao.md))

### Implementation for User Story 4

- [X] T031 [US4] Em `app/modulos/propriedade/schema.py`,
      `service.py` e `router.py`, acrescer os dois prazos ao
      `200` de `GET /retencao` lendo `parametro_hotel`. Sem rota
      de executar. Até T029 verde
- [X] T032 [US4] Criar `frontend/src/painel/TelaRetencao.tsx`.
      Título **Retenção de dados**. Até T030 verde
- [X] T033 [US4] Em `frontend/src/painel/Casca.tsx`,
      `destino.id === "retencao"` renderiza `TelaRetencao`. Rodar
      `npm test` em `frontend/`

**Checkpoint**: as quatro telas existem para a gestão.

---

## Phase 7: User Story 5 - Só a gestão chega (Priority: P1)

**Goal**: recepção e staff não vêem os quatro destinos no menu;
forçar o endereço redireciona **sem** disparar os GET; gestão vê
os quatro e cai em Painel; nenhuma tela mostra dado cadastral de
hóspede.

**Independent Test**: Vitest casca — recepção/staff em
`/app/indicadores`, `/mercado`, `/usuarios`, `/retencao` caem na
casa e o mock não registra esses GET; gestão tem os quatro links;
Painel/Mercado/Usuários/Retenção não renderizam nome/telefone/
documento de hóspede.

### Tests for User Story 5

- [X] T034 [US5] Em `frontend/src/painel/destinos.test.ts`:
      `perfilPode("gestor", …)` verdadeiro nos quatro caminhos;
      `recepcao` e `staff` falsos. Rodar e **ver falhar** só se a
      asserção ainda não existir — se já verde, manter o teste
      como âncora
      ([contracts/destinos-e-perfis.md](./contracts/destinos-e-perfis.md))
- [X] T035 [US5] Em `frontend/src/painel/Casca.test.tsx`:
      recepção e staff em cada um dos quatro paths caem na casa
      do papel; `fetchMock` **não** é chamado com `/indicadores`,
      `/mercado`, `/usuarios` nem `/retencao` (além de
      `/sessoes/atual` se já ocorrer). Gestão vê links Painel,
      Mercado, Usuários, Retenção de dados. Rodar e **ver falhar**
      até os redirecionamentos estarem cobertos
      ([plan.md](./plan.md) ponto de atenção 3)

### Implementation for User Story 5

- [X] T036 [US5] Ajustar `frontend/src/painel/Casca.tsx` e as
      quatro telas se algum GET vazar no redirect (o `Navigate`
      deve ocorrer **antes** de montar a tela). Confirmar que
      nenhum fixture de tela pinta ficha de hóspede. Até T034 e
      T035 verdes. `destinos.ts` **não** acrescenta recepção
      nestes `perfis`

**Checkpoint**: minimização visível no menu e no fetch.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: estado do projeto, suíte verde, quickstart.

- [X] T037 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F8.7
      concluída quando o quickstart passar; registrar os quatro
      números, Mercado só leitura, usuários sem reativar, prazos
      no `GET /retencao`. Sem inventar integração PMS. O mapa de
      telas com seis KPIs, gráfico, “você”, % 7 dias, aba
      Concorrentes e Reativar **não** foi seguido
- [X] T038 [P] Conferir [contracts/logs.md](./contracts/logs.md):
      nenhum teste novo loga senha, cookie ou texto de hóspede;
      se houver logger em `GET /indicadores` ou `GET /usuarios`,
      asserção de ausência desses campos no teste de log do
      módulo (padrão F0.3/F5.3)
- [X] T039 Rodar `npm test` em `frontend/` e, na raiz,
      `pytest testes/unitarios -q` mais
      `pytest testes/integracao -q -k "indicador or usuario or retencao or mercado or sessao or chegada"`.
      Tudo verde. Conferir o roteiro de
      [quickstart.md](./quickstart.md) (casos Vitest cobertos;
      `npm run dev`; browser só como checagem humana, não
      Playwright). Sem Alembic

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: começa agora — mock da casca
- **Foundational (Phase 2)**: depende do Setup — **bloqueia** as histórias
- **US1 (Phase 3)**: depois da Foundational — MVP (backend + Painel)
- **US2 (Phase 4)**: depois da Foundational; na prática depois da
  US1 para o `Casca.tsx` não conflitar
- **US3 (Phase 5)**: Foundational; `Casca.tsx` depois da US2
- **US4 (Phase 6)**: Foundational; `Casca.tsx` depois da US3
- **US5 (Phase 7)**: depois das quatro telas ligadas (T019, T023,
  T028, T033)
- **Polish**: depois das histórias desejadas

### User Story Dependencies

- **US1**: só Foundational (+ T001)
- **US2**: Foundational; Casca depois da US1
- **US3**: Foundational; Casca depois da US2; backend de lista
  independente do Painel
- **US4**: Foundational; Casca depois da US3; prazos independentes
  do Painel
- **US5**: US1–US4 ligadas na casca

### Within Each User Story

- Testes **primeiro**, ver falhar, depois o mínimo para verde
- COUNT/SUM no repositório antes da rota
- Função pura antes do JSX que a usa
- Ligar na `Casca.tsx` por último em cada história de tela
- História completa antes de avançar

### Parallel Opportunities

- T004, T006 e T008 em paralelo com T002 (arquivos distintos)
- T011 e T012 em paralelo com T010
- T014 (Vitest Painel) em paralelo com T010–T013 (pytest)
- T025 em paralelo com T024
- T030 em paralelo com T029
- T037 e T038 no polish
- T020 e T021 são o **mesmo** arquivo: **não** paralelizar
- US1–US4 não paralelizam o `Casca.tsx`

---

## Parallel Example: User Story 1

```text
# Pytest (arquivos distintos):
Task: T010 test_indicadores_agregados.py
Task: T011 test_indicadores_chamados.py
Task: T012 test_indicadores_consumo.py

# Vitest ao mesmo tempo:
Task: T014 TelaPainel.test.tsx

# Depois, implementação na ordem repositório → rota → tela → casca:
Task: T015 T016 T017 T018 T019
```

T020 e T021 são o mesmo arquivo: **não** paralelizar entre si.
US1–US4 não paralelizam o `Casca.tsx`.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: gestão vê os quatro números. Mercado, usuários e
   retenção ainda título

### Incremental Delivery

1. Setup + Foundational
2. US1 → demo do Painel
3. US2 → demo do comparativo com falha marcada
4. US3 → demo de criar/desativar usuário
5. US4 → demo do comprovante
6. US5 → recusa de recepção/staff sem fetch
7. Polish + estado do projeto

### Parallel Team Strategy

Um desenvolvedor (prazo da semana): ordem US1 → US2 → US3 → US4 →
US5. Não paralelizar a ligação na `Casca.tsx`. Backend da US1,
US3 e US4 pode adiantar-se às telas se os testes pytest já
falharem pelo motivo certo.

---

## Notes

- [P] só com arquivos distintos e dependência já verde
- Sem Playwright, sem operação nova em `politica.py`, sem
  Alembic, sem worker, sem CRUD de concorrente, sem reativar
  usuário, sem gráfico, sem tarifa da casa
- `GET /solicitacoes` e `GET /consumos/pendentes` **não** alimentam
  o Painel
- `ler_indicadores` continua permitindo recepção na API; a casca
  não dispara
- Commit por história (não por tarefa) salvo o usuário pedir o
  contrário — o ciclo TDD da casa é teste → falha → código → verde
