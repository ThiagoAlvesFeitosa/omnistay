---
description: "Task list for feature implementation"
---

# Tasks: Painel de Mercado

**Input**: Design documents from `/specs/022-painel-mercado/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de
produção sem teste que falhe antes pelo motivo certo.

**Organization**: Tarefas agrupadas por história (US1–US4), na ordem da spec.
Não há migração. A Foundational só acrescenta `ler_mercado` na matriz, os
contratos Pydantic e o SQL/serviço em esqueleto. A visão atual datada é a US1
(MVP). `situacao` completa (desatualizado, cadência, falha posterior) é a US2.
Histórico é a US3. Perfil, isolamento e `405` são a US4.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US4)

## Como ver os testes falharem nesta fatia

**Matriz.** Acrescentar `ler_mercado` em `OPERACOES_ESPERADAS` **antes** de
`politica.py` deixa `test_matriz_completa_bate_com_o_contrato` vermelho. A
operação nova o devolve ao verde.

**HTTP.** Hoje não existe `/mercado`. A integração falha com `404` de rota até
o roteador ganhar os GETs. `testes/integracao/test_rotas_protegidas.py` varre
o que estiver registrado: depois de ligar a rota, cada uma exige `401` sem
cookie — **não** editar `ROTAS_PUBLICAS`.

**Serviço.** Unitários com repositório falso falham por `AttributeError` /
`NotImplementedError` até existir `ler_painel` / `ler_historico`.

**Escrita.** `POST /mercado` já é `405` (método inexistente) assim que a rota
GET existir no mesmo path — o teste da US4 afirma isso de propósito.

**Worker.** GET **não** chama `verificar_coletas_mercado`. O teste conta
`trabalho`/`coleta_mercado` antes e depois; se o GET enfileirar, falha.

---

## Phase 1: Setup

**Purpose**: constantes e helper para gravar a série **sem** disparar o
coletor. O módulo `mercado` já existe; não criar pacote novo.

- [X] T001 [P] Estender `testes/suporte/coleta_mercado.py` com as constantes
      de `situacao` do contrato
      (`atual`, `desatualizado`, `cadencia_ausente`, `sem_coleta`,
      `so_falha`) e um instante âncora estável de teste (ex. 21/08/2026
      12:00 UTC). Reusar `PRECO_FIXTURE`, `NOTA_FIXTURE`,
      `CHAVE_PERIODICIDADE`. Sem segredo, sem rede
- [X] T002 [P] Criar `testes/suporte/painel_mercado.py` com
      `gravar_coleta(conexao, id_concorrente, *, sucesso, preco, nota_media,
      coletado_em)` — um `INSERT` em `coleta_mercado` e devolve a linha.
      Sem chamar worker, sem abrir URL. Docstring: uso só em teste

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: operação na matriz, contratos Pydantic, SQL nomeado e funções
de serviço em esqueleto. **Nenhuma rota HTTP nova ainda.** Sem migração,
sem view, sem alteração em `docs/04-schema.sql`.

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase.

- [X] T003 Acrescentar casos em
      `testes/unitarios/modulos/acesso/test_politica.py`: `ler_mercado`
      permitida **só** para `gestor`, recusada para `recepcao` e `staff`;
      incluir em `OPERACOES_ESPERADAS`. Rodar e **ver falhar**
      (FR-013, FR-014,
      [contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))
- [X] T004 Acrescentar `ler_mercado` a `OPERACOES` em
      `app/modulos/acesso/politica.py` (`gestor` somente) até T003 passar.
      **Não** nascer `alterar_coleta_mercado`
- [X] T005 [P] Acrescentar em `app/modulos/mercado/schema.py` os contratos de
      `GET /mercado` e `GET /mercado/concorrentes/{id}` conforme
      [contracts/api-de-painel.md](./contracts/api-de-painel.md)
      (`extra="forbid"` nas entradas se houver; sem `id_hotel` e sem
      `url_fonte` no JSON; `periodicidade_horas` opcional/`None`;
      `ultimo_sucesso` e `ultima_falha` opcionais)
- [X] T006 [P] Acrescentar em `app/modulos/mercado/repository.py` as funções
      nomeadas `ultimos_sucessos(id_hotel)`, `ultimas_linhas(id_hotel)`,
      `listar_serie(id_hotel, id_concorrente)` e `obter(id_hotel,
      id_concorrente)` (ficha ativa **ou** inativa) — esqueleto com
      `NotImplementedError` até as histórias. Todo SQL com
      `concorrente.id_hotel`. Reusar `listar_manutencao` para a lista de
      fichas; **não** reusar `ultima_coleta` sozinha como preço da visão
      atual ([research.md](./research.md) §3)
- [X] T007 [P] Acrescentar em `app/modulos/mercado/service.py` as funções
      `ler_painel` e `ler_historico` (e, se útil, `_classificar_situacao`
      pura) levantando `NotImplementedError` até as histórias. Assinatura
      de `ler_painel` com `agora` injetável e `ler_parametro` injetável
      (default `propriedade.repository.ler_parametro`). Sem SQL de
      `parametro_hotel` neste arquivo

**Checkpoint**: matriz com `ler_mercado`; contratos e nomes de SQL existem;
ainda não há GET `/mercado`. Histórias podem começar.

---

## Phase 3: User Story 1 - Comparar o mercado sem sair do sistema (Priority: P1) 🎯 MVP

**Goal**: Gestão autentica e vê, numa consulta, cada concorrente da casa com
o preço e/ou a nota do **último sucesso** e a **data daquela coleta**. Vazio
explícito. Zero encontrado ≠ campo vazio. Nunca coletado ≠ zero.

**Independent Test**: Sessão de gestão, dois concorrentes com sucessos em
datas diferentes → `GET /mercado` `200`; cada valor traz `coletado_em`;
nenhum número sem carimbo; `periodicidade_horas` é `24`. Hotel sem ficha →
`"concorrentes": []`. Sem cookie → `401`.

### Tests for User Story 1 ⚠️

> Escrever primeiro; rodar; ver falhar pelo motivo certo antes de implementar.

- [X] T008 [P] [US1] Unitários em
      `testes/unitarios/modulos/mercado/test_painel_mercado.py` com
      repositório falso e relógio injetável: painel devolve último sucesso
      (preço, nota, data); só preço ou só nota deixa o outro campo `None`
      (não `0`); preço `0` permanece zero; nunca coletado →
      `situacao=sem_coleta` e blocos nulos; lista vazia sem erro; **não**
      usa a última linha falha como preço (FR-001 a FR-005, FR-009,
      constantes de `testes/suporte/coleta_mercado.py`,
      [contracts/situacao-do-dado.md](./contracts/situacao-do-dado.md))
- [X] T009 [US1] Integração em `testes/integracao/test_painel_mercado.py`:
      via `ambiente_de_acesso` + `gravar_coleta`, gestão faz
      `GET /mercado` e recebe sucesso datado (`PRECO_FIXTURE` /
      `NOTA_FIXTURE`); hotel sem concorrente → `200` e lista vazia; sem
      cookie → `401`. **Não** chamar `--verificar-mercado`. Rodar e ver
      falhar (`404` de rota)

### Implementation for User Story 1

- [X] T010 [US1] Implementar `ultimos_sucessos`, `ultimas_linhas` e
      `obter` em `app/modulos/mercado/repository.py` (`JOIN` em
      `concorrente`, `id_hotel` da sessão, `ORDER BY coletado_em DESC,
      id_coleta DESC`). Reusar `ix_coleta_concorrente_data`. Sem UPDATE
- [X] T011 [US1] Implementar `ler_painel` em
      `app/modulos/mercado/service.py`: junta fichas + último sucesso +
      última linha; classifica pelo menos `sem_coleta`, `so_falha` e
      `atual` (sucesso recente dentro de `P`, sem falha posterior); log
      `painel` com `id_hotel` **sem** preço/nota/URL. Até T008 verde.
      `desatualizado` / `cadencia_ausente` podem ficar incompletos até a
      US2 **desde que** os fixtures da US1 usem sucesso recente e `P=24`
- [X] T012 [US1] Implementar `GET /mercado` em
      `app/modulos/mercado/router.py` com
      `exigir_operacao("ler_mercado")`, `id_hotel` só da sessão. T009
      verde. **Não** registrar POST/PATCH/DELETE

**Checkpoint**: US1 entregável sozinha — comparação datada pela API. Sinal
de dado velho e histórico ainda podem faltar.

---

## Phase 4: User Story 2 - Dado velho não se disfarça de atual (Priority: P1)

**Goal**: Sucesso mais antigo que a periodicidade, ou sucesso seguido de
falha, vem `desatualizado` com a **data do sucesso** intacta. Sem `P`
válido: `cadencia_ausente`, nada é `atual`. Só falhas: sem número
inventado.

**Independent Test**: Três concorrentes: sucesso há 1 h → `atual`; sucesso
há 48 h (`P=24`) → `desatualizado` com a data antiga; sucesso antigo +
falha depois → número do sucesso, `ultima_falha` datada, `desatualizado`.
Apagar a chave → `periodicidade_horas` nulo e `cadencia_ausente`.

### Tests for User Story 2 ⚠️

- [X] T013 [P] [US2] Unitários em
      `testes/unitarios/modulos/mercado/test_painel_mercado.py`: tabela de
      `_classificar_situacao` / `ler_painel` — janela `agora >= U+P` (mesmo
      `>=` da F5.2); falha posterior ⇒ `desatualizado` e preço do sucesso;
      `P` ausente/zero/não numérico ⇒ `cadencia_ausente` e **não** assume
      24; só falhas ⇒ `so_falha` sem preço (FR-006 a FR-008, FR-018,
      [contracts/situacao-do-dado.md](./contracts/situacao-do-dado.md))
- [X] T014 [US2] Integração em `testes/integracao/test_painel_mercado.py`:
      gravar sucesso há 48 h → `desatualizado`; gravar falha depois do
      sucesso → `ultimo_sucesso.coletado_em` inalterado e
      `ultima_falha` preenchida; `DELETE` da chave
      `periodicidade_coleta_mercado` → `cadencia_ausente`

### Implementation for User Story 2

- [X] T015 [US2] Completar a classificação em
      `app/modulos/mercado/service.py` (ordem do contrato: `sem_coleta` →
      `so_falha` → `cadencia_ausente` → `desatualizado` → `atual`).
      `ler_parametro` injetável; inválido ⇒ `periodicidade_horas=None`.
      T013–T014 verdes

**Checkpoint**: Dado velho sinalizado; falha não redata nem zera o sucesso.

---

## Phase 5: User Story 3 - Acompanhar a variação ao longo do tempo (Priority: P1)

**Goal**: `GET /mercado/concorrentes/{id}` devolve a série completa em ordem
cronológica crescente. Falha intercalada aparece como falha (`null`, não
`0`). Pontos antigos não são reescritos. Séries de dois concorrentes não
se misturam.

**Independent Test**: Três sucessos + uma falha no meio → quatro pontos
na ordem das datas; falha com `preco`/`nota_media` nulos; segundo GET após
nova linha acrescenta o ponto sem alterar os anteriores.

### Tests for User Story 3 ⚠️

- [X] T016 [P] [US3] Unitários em
      `testes/unitarios/modulos/mercado/test_painel_mercado.py`:
      `ler_historico` devolve pontos `coletado_em ASC, id_coleta ASC`;
      falha intercalada sem virar zero; id inexistente / outro hotel →
      `ConcorrenteNaoEncontrado` (FR-010, FR-011, FR-015)
- [X] T017 [US3] Integração em `testes/integracao/test_painel_mercado.py`:
      `GET /mercado/concorrentes/{id}` `200` com a série; inativo com
      histórico ainda aparece; id do hotel B com sessão A → `404`;
      cadastrado nunca coletado → `"coletas": []`

### Implementation for User Story 3

- [X] T018 [US3] Implementar `listar_serie` em
      `app/modulos/mercado/repository.py` (`WHERE` hotel + concorrente,
      ordem crescente; inclui falhas)
- [X] T019 [US3] Implementar `ler_historico` em
      `app/modulos/mercado/service.py` até T016 verde (log `historico` com
      ids, sem preço/nota)
- [X] T020 [US3] Implementar `GET /mercado/concorrentes/{id_concorrente}`
      em `app/modulos/mercado/router.py` com `ler_mercado`;
      `ConcorrenteNaoEncontrado` → `404`. T017 verde

**Checkpoint**: Histórico observa variação; falha não fabrica queda a zero.

---

## Phase 6: User Story 4 - Somente leitura, só a gestão, só a própria casa (Priority: P1)

**Goal**: Recepção e operação `403`. Hotel A não vê B (`404` no id alheio).
Gestão **não** tem caminho para alterar a série (`405`). GET não dispara
coleta nem mensagem.

**Independent Test**: Cookie recepção/staff → os dois GETs `403`. Gestão B
não lista concorrentes de A; GET do id de A → `404`. `POST /mercado` e
`DELETE` no histórico → `405`; contagem de `coleta_mercado` e de
`trabalho` `coletar_mercado` inalterada.

### Tests for User Story 4 ⚠️

- [X] T021 [P] [US4] Integração em `testes/integracao/test_painel_mercado.py`:
      cookie de recepção e de `staff` → `GET /mercado` e
      `GET /mercado/concorrentes/{id}` `403` (FR-013, FR-014)
- [X] T022 [US4] Integração no mesmo arquivo: dois hotéis via
      `ambiente_de_acesso`; GET do hotel B não contém fichas de A; GET no
      id de A com sessão B → `404` (FR-015)
- [X] T023 [US4] Integração no mesmo arquivo: `POST /mercado`,
      `PATCH`/`PUT`/`DELETE` em `/mercado` e em
      `/mercado/concorrentes/{id}` → `405`; `SELECT count(*)` de
      `coleta_mercado` e de `trabalho` tipo `coletar_mercado` iguais antes
      e depois do GET (FR-012, FR-019)

### Implementation for User Story 4

- [X] T024 [US4] Garantir `id_hotel` em **todo** SQL novo de painel e
      `exigir_operacao("ler_mercado")` nas duas rotas em
      `app/modulos/mercado/repository.py` e `router.py`. **Não** registrar
      escrita. T021–T023 verdes — se a recusa já nasceu nas histórias
      anteriores, só fechar os testes

**Checkpoint**: Multi-tenant, matriz e “somente leitura da série”
exercitados.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: logs, inativo visível, estado do projeto, fronteiras e
roteiro do quickstart

- [X] T025 [P] Estender
      `testes/unitarios/modulos/mercado/test_log_sem_conteudo.py`:
      `ler_painel` e `ler_historico` registram `id_hotel`,
      `id_concorrente` (quando houver) e ação `painel`/`historico`;
      **não** registram preço, nota, URL nem texto de hóspede (FR-021)
- [X] T026 [P] Integração em `testes/integracao/test_painel_mercado.py`:
      concorrente `ativo=false` aparece na visão atual com `ativo: false`
      e o último sucesso intacto (FR-016)
- [X] T027 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F5.3 em andamento /
      concluída na entrega; operação `ler_mercado`; visão atual = último
      **sucesso** (não `ultima_coleta` da F5.2); limiar = periodicidade;
      próxima fatia F6.1; sem React, sem disparo manual, sem migração nova
- [X] T028 Confirmar que `app/modulos/mercado/` **não** importa
      `urllib.request`/`httpx` nesta fatia; **não** há revisão Alembic
      `0021`; worker/`FontePublica` intocados; payload **sem** `url_fonte`
      e **sem** tarifa da casa; `test_rotas_protegidas.py` verde sem
      acréscimo em `ROTAS_PUBLICAS` (FR-017, FR-019, FR-020)
- [X] T029 Revisar fronteiras: SQL de `coleta_mercado` só em
      `app/modulos/mercado/repository.py`; `parametro_hotel` só via
      `propriedade.repository.ler_parametro`; `conversa` e `hospedagem`
      **não** importam o painel
- [X] T030 Percorrer [quickstart.md](./quickstart.md) (ou equivalente
      automatizado): `pytest testes/unitarios -q`,
      `pytest testes/integracao/test_painel_mercado.py -q`,
      `test_rotas_protegidas.py`, `test_concorrentes.py` e
      `test_coleta_mercado.py` (regressão); tudo verde **sem** rede
      externa e **sem** `--verificar-mercado` para provar o painel

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: após Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: após Foundational — MVP
- **US2 (Phase 4)**: após `ler_painel` da US1 (completa a classificação)
- **US3 (Phase 5)**: após Foundational; na prática usa fichas/coletas da US1
- **US4 (Phase 6)**: após as rotas existirem (US1 e US3)
- **Polish (Phase 7)**: após as histórias desejadas

### User Story Dependencies

- **US1**: só Foundational — MVP isolado (visão atual datada; GET)
- **US2**: depende do GET da US1; aceite independente se o teste gravar
  sucesso antigo / falha posterior
- **US3**: independente no aceite do histórico; reusa a série já inserida
- **US4**: transversal sobre as duas rotas

### Within Each User Story

1. Testes escritos e vermelhos
2. Implementação mínima
3. Verde
4. Só então próxima história

### Parallel Opportunities

- T001–T002 em paralelo
- T005, T006 e T007 em paralelo após T004 (matriz)
- T008 em paralelo com a preparação de T009 na US1
- T013 em paralelo com a preparação de T014 na US2
- T016 em paralelo com a preparação de T017 na US3
- T021 em paralelo com a preparação de T022/T023 na US4 (mesmo arquivo:
  não marcar T022/T023 como [P])
- T025, T026 e T027 em paralelo no polish

---

## Parallel Example: User Story 1

```text
# Testes em paralelo (antes da implementação):
T008 test_painel_mercado.py (serviço, repositório falso)
T009 test_painel_mercado.py (integração GET /mercado) — arquivo diferente
     do unitário, pode começar o esqueleto em paralelo

# Depois, implementação na ordem:
T010 → T011 → T012
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: `GET /mercado` com sucesso datado, lista vazia, `401`
4. Demo: curl da gestão vê preço e data sem abrir a fonte

### Incremental Delivery

1. US1 → comparação datada
2. US2 → sinal de desatualizado / cadência / falha posterior
3. US3 → histórico e variação
4. US4 → perfil, isolamento, `405`
5. Polish → estado do projeto + logs + quickstart

### Suggested MVP scope

**Só US1** (T001–T012) prova “a gestão consulta sem sair do sistema, com
data”. US2 é o critério D8 (dado velho visível) e **entra na mesma
entrega** antes de marcar F5.3 concluída. Não abrir F6.1 sem US2 e US4.

### Parallel Team Strategy

Um desenvolvedor, prazo fixo: ordem US1 → US2 → US3 → US4. Não paralelizar
histórias no mesmo `ler_painel`.

---

## Notes

- [P] = arquivos distintos, sem depender de tarefa incompleta da mesma sequência
- Sem revisão Alembic; sem React; sem worker; sem porta nova
- `id_hotel` só da sessão
- Visão atual lê o último **sucesso**, nunca `ultima_coleta` sozinha
- Commit por tarefa ou grupo lógico **só se o usuário pedir commit**
- Evitar: inventar `24` na leitura; tratar falha como preço zero; `url_fonte`
  no payload; tarifa da casa; disparar coleta no GET; SQL de
  `parametro_hotel` em `mercado.repository`; recepção lendo o painel
- Próximo: `/speckit-implement`
