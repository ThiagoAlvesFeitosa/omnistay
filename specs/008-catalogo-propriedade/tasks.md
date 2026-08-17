---
description: "Task list for feature implementation"
---

# Tasks: Catálogo da Propriedade

**Input**: Design documents from `/specs/008-catalogo-propriedade/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhum código de produção sem
teste que falhe antes pelo motivo certo.

**Organization**: Tarefas agrupadas por história de usuário (US1–US4), na ordem da spec.
Sem migração Alembic — `catalogo_item` já existe na `0001`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US4)

## Como ver os testes falharem nesta fatia

**Matriz.** Acrescentar `ler_catalogo` em `OPERACOES_ESPERADAS` **antes** de
`politica.py` deixa `test_matriz_completa_bate_com_o_contrato` vermelho. A operação
nova o devolve ao verde.

**Serviço.** Unitários com repositório falso falham por `ImportError` /
`AttributeError` / `DadosInvalidos` ausente até existir a implementação.

**Rotas.** `testes/integracao/test_rotas_protegidas.py` varre o que estiver
registrado: depois de ligar o roteador, cada rota nova exige `401` sem cookie —
não editar `ROTAS_PUBLICAS`.

**Sem conformidade F0.2 vermelha.** Esta fatia **não** altera `docs/04-schema.sql`.

---

## Phase 1: Setup

**Purpose**: Arquivos que o plano prevê e ainda não existem no módulo `propriedade`
e na porta de catálogo

- [X] T001 [P] Criar `app/modulos/propriedade/schema.py` com docstring do módulo
      (modelos Pydantic entram na T008)
- [X] T002 [P] Criar `app/modulos/propriedade/router.py` com `APIRouter(tags=["propriedade"])`
      e sem rotas ainda
- [X] T003 [P] Criar `app/portas/catalogo.py` com `ItemCatalogo` (frozen) e o Protocol
      `CatalogoRepository.listar_ativos(id_hotel)` conforme
      [contracts/catalogo-repository.md](./contracts/catalogo-repository.md)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: `ler_catalogo` na matriz, contratos HTTP, SQL nomeado, porta falsa/banco
esqueleto e roteador montado — o que nenhuma história deve reinventar

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase.

- [X] T004 Acrescentar casos em `testes/unitarios/modulos/acesso/test_politica.py`:
      `ler_catalogo` permitida para `recepcao` e `gestor`, recusada para `staff`;
      `alterar_catalogo` continua só `recepcao`; incluir `ler_catalogo` em
      `OPERACOES_ESPERADAS`. Rodar e **ver falhar** o caso da operação nova
      (FR-014, FR-015, FR-016)
- [X] T005 Acrescentar `ler_catalogo` a `OPERACOES` em `app/modulos/acesso/politica.py`
      (`recepcao` + `gestor`) até T004 passar
      ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))
- [X] T006 [P] Criar em `app/modulos/propriedade/schema.py` os contratos de
      `POST /catalogo`, `PATCH /catalogo/{id}`, `GET /catalogo` e
      `GET /catalogo/ativo` (cinco chaves sempre presentes) conforme
      [contracts/api-de-catalogo.md](./contracts/api-de-catalogo.md)
- [X] T007 [P] Ampliar `app/modulos/propriedade/repository.py` com funções nomeadas
      `inserir_item`, `atualizar_item`, `listar_manutencao`, `listar_ativos` —
      todas recebem `id_hotel`; esqueleto com `NotImplementedError` até as histórias
- [X] T008 [P] Criar `app/adaptadores/catalogo_falso.py` (`CatalogoFalso` com
      `listar_ativos`; configurável pelo teste; **nunca** abre banco)
- [X] T009 [P] Criar `app/adaptadores/catalogo_banco.py` (`CatalogoBanco(conexao)`
      delega a `propriedade.repository.listar_ativos`; **não** chama
      `obter_engine`)
- [X] T010 Registrar o roteador de propriedade em `app/main.py`
      (`include_router`). Sem rotas ainda, `test_rotas_protegidas` permanece verde

**Checkpoint**: matriz com leitura; contratos e porta existem; SQL ainda não grava.
Histórias podem começar.

---

## Phase 3: User Story 1 - Cadastrar fatos da propriedade por categoria (Priority: P1) 🎯 MVP

**Goal**: Recepção autentica e cria um item com categoria, título e conteúdo; nasce
ativo no hotel da sessão. Categoria inválida, título/conteúdo vazios ou título > 160
são recusados sem gravar.

**Independent Test**: Sessão de recepção → `POST /catalogo` nas cinco chaves
(`horario`, `cardapio`, `servico`, `programacao`, `regra`) → `201` com `ativo: true`;
as cinco linhas existem em `catalogo_item` daquele `id_hotel`. Categoria inventada →
`422`, zero insert.

### Tests for User Story 1 ⚠️

> Escrever primeiro; rodar; ver falhar pelo motivo certo antes de implementar.

- [X] T011 [P] [US1] Unitários em
      `testes/unitarios/modulos/propriedade/test_catalogo.py` com repositório falso:
      criar nas cinco categorias dispara insert com `id_hotel` da sessão e `ativo=true`;
      trim em título/conteúdo; só espaços, categoria fora das cinco e título com 161
      caracteres recusam **sem** chamar insert (FR-001 a FR-004)
- [X] T012 [US1] Integração em `testes/integracao/test_catalogo.py`: recepção cria
      item válido (`201`); no banco há a linha; categoria inválida e título em branco
      → `422` e nada gravado; sem cookie → `401`. Usar
      `testes/suporte/ambiente_de_acesso.py`. Rodar e ver falhar

### Implementation for User Story 1

- [X] T013 [US1] Implementar `inserir_item` em
      `app/modulos/propriedade/repository.py` (`INSERT … RETURNING`, `id_hotel` no
      SQL) conforme [data-model.md](./data-model.md)
- [X] T014 [US1] Implementar `criar_item` em `app/modulos/propriedade/service.py`
      (trim, categorias canônicas, título 1–160, log com id/hotel/categoria/ação
      **sem** texto do fato) até T011 verde
- [X] T015 [US1] Implementar `POST /catalogo` em
      `app/modulos/propriedade/router.py` com `exigir_operacao("alterar_catalogo")`,
      `id_hotel` só da sessão, `201` / `422`. Fechar T012 verde

**Checkpoint**: US1 entregável sozinha — criar fato por categoria, recusa clara,
persistido no hotel certo.

---

## Phase 4: User Story 2 - Corrigir um fato e desativar sem apagar (Priority: P1)

**Goal**: PATCH altera título/conteúdo e/ou `ativo`. Desativar some da consulta
ativa (quando ela existir) e permanece na manutenção. Não há `DELETE`. Categoria
não muda.

**Independent Test**: Criar item → PATCH título → PATCH `ativo: false` →
`GET /catalogo` ainda lista com `ativo: false`; `DELETE` → `405`; PATCH com
`categoria` → `422`.

### Tests for User Story 2 ⚠️

- [X] T016 [P] [US2] Unitários em
      `testes/unitarios/modulos/propriedade/test_catalogo.py`: PATCH título/conteúdo
      persiste e mantém `ativo`; `ativo=false` / `true`; corpo vazio e campo
      `categoria` recusam; id inexistente → `ItemNaoEncontrado` (FR-005 a FR-008)
- [X] T017 [P] [US2] Integração em `testes/integracao/test_catalogo.py`: PATCH
      `200`; `GET /catalogo` lista ativos e inativos ordenados por categoria, id;
      `DELETE /catalogo/{id}` → `405` e a linha permanece

### Implementation for User Story 2

- [X] T018 [US2] Implementar `atualizar_item` (SET `atualizado_em = now()`,
      `WHERE id_catalogo_item AND id_hotel`) e `listar_manutencao` em
      `app/modulos/propriedade/repository.py`
- [X] T019 [US2] Implementar `alterar_item` e `listar_manutencao` em
      `app/modulos/propriedade/service.py` até T016 verde
- [X] T020 [US2] Implementar `PATCH /catalogo/{id_catalogo_item}` e
      `GET /catalogo` (`ler_catalogo`) em `app/modulos/propriedade/router.py`;
      **não** registrar `DELETE`. `ItemNaoEncontrado` → `404`. T017 verde

**Checkpoint**: US1 e US2 independentes; desativar não apaga; manutenção vê inativos.

---

## Phase 5: User Story 3 - Consultar o catálogo ativo completo (Priority: P1)

**Goal**: `GET /catalogo/ativo` devolve as cinco categorias sempre, só itens
ativos, arrays vazios quando não há fato. A porta `CatalogoRepository` lê a mesma
fonte, na mesma transação.

**Independent Test**: Propriedade com ativos nas cinco categorias + um inativo →
GET ativo contém todos os ativos, zero inativos, cinco chaves. Propriedade vazia
→ cinco `[]`, HTTP 200. `CatalogoBanco(conexao).listar_ativos(id_hotel)` bate com
o que o repositório devolve.

### Tests for User Story 3 ⚠️

- [X] T021 [P] [US3] Unitários em
      `testes/unitarios/modulos/propriedade/test_catalogo.py`: `ler_catalogo_ativo`
      omite inativos, agrupa nas cinco chaves, vazio não é erro (FR-010, FR-011)
- [X] T022 [P] [US3] Unitários em
      `testes/unitarios/adaptadores/test_catalogo_falso.py`: `CatalogoFalso`
      devolve só o que o teste configurou como ativo daquele `id_hotel`; hotel
      sem itens → tupla vazia
- [X] T023 [US3] Integração em `testes/integracao/test_catalogo.py`: GET
      `/catalogo/ativo` agrupado; inativo omitido; `CatalogoBanco` com a conexão
      do teste devolve os mesmos ids que `listar_ativos` do repositório

### Implementation for User Story 3

- [X] T024 [US3] Implementar `listar_ativos` em
      `app/modulos/propriedade/repository.py` (`ativo = true`, ordem categoria,
      id; sempre `id_hotel`)
- [X] T025 [US3] Implementar `ler_catalogo_ativo` em
      `app/modulos/propriedade/service.py` (agrupa; cinco chaves sempre) até T021
      verde
- [X] T026 [US3] Implementar `GET /catalogo/ativo` em
      `app/modulos/propriedade/router.py` com `exigir_operacao("ler_catalogo")`
- [X] T027 [US3] Completar `CatalogoFalso` e `CatalogoBanco` até T022 e T023
      verdes. HTTP **não** precisa passar pela porta

**Checkpoint**: Consulta ativa é o contrato da F2.2; item desativado não vaza.

---

## Phase 6: User Story 4 - Isolar o catálogo por hotel e por perfil (Priority: P1)

**Goal**: Hotel A não aparece para B. Gestão lê e não altera. Operação não lê nem
altera. PATCH em id alheio → `404`.

**Independent Test**: Dois hotéis com itens; sessão B não lista A; PATCH do id de
A com sessão B → `404`. Gestão: GET `200`, POST `403`. Staff: GET e POST `403`.

### Tests for User Story 4 ⚠️

- [X] T028 [P] [US4] Integração em `testes/integracao/test_catalogo.py`: cookie
      de gestão → GET `/catalogo` e `/catalogo/ativo` `200`; POST e PATCH `403`
      (FR-015)
- [X] T029 [P] [US4] Integração no mesmo arquivo: cookie `staff` → GET e POST
      `403` (FR-016)
- [X] T030 [US4] Integração: dois hotéis via `ambiente_de_acesso`; GET do hotel
      B não contém itens de A; PATCH no id de A com sessão B → `404` (FR-013,
      FR-017)

### Implementation for User Story 4

- [X] T031 [US4] Garantir `id_hotel` em **todo** SQL de catálogo e
      `exigir_operacao` correto em cada rota (`alterar_catalogo` vs
      `ler_catalogo`) em `app/modulos/propriedade/repository.py` e `router.py`.
      T028–T030 verdes — se a recusa já nasceu nas histórias anteriores, só
      fechar os testes

**Checkpoint**: Multi-tenant e matriz exercitados nas quatro rotas.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Logs, edges da spec, estado do projeto, fronteiras e roteiro do
quickstart

- [X] T032 [P] Unitários em
      `testes/unitarios/modulos/propriedade/test_log_sem_conteudo.py`: criar,
      editar, desativar e reativar registram id, hotel, categoria e ação; **não**
      registram `titulo` nem `conteudo` (FR-018)
- [X] T033 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F2.1 em andamento /
      concluída na entrega; pendência “catálogo e preços” **adiada para F3.7**,
      não esquecida; próxima fatia F2.2
- [X] T034 [P] Integração: dois itens com o mesmo título na mesma categoria são
      aceitos (ids distintos) em `testes/integracao/test_catalogo.py`
- [X] T035 Integração de repositório: `INSERT` com categoria inválida é rejeitado
      pelo `ck_catalogo_categoria` (Artigo IX) em
      `testes/integracao/test_catalogo.py` ou `test_garantias_do_banco.py`
- [X] T036 Confirmar que não há rota, coluna nem campo JSON de preço (FR-019);
      `DELETE` continua `405`
- [X] T037 Revisar fronteiras: `conversa` e `hospedagem` **não** importam
      `propriedade.repository` de catálogo; SQL de `catalogo_item` só em
      `app/modulos/propriedade/repository.py`
- [X] T038 Rodar [quickstart.md](./quickstart.md) (ou equivalente automatizado),
      `pytest testes/unitarios -q`, `pytest testes/integracao/test_catalogo.py -q`
      e `test_rotas_protegidas.py`; tudo verde sem rede

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: após Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: após Foundational — MVP
- **US2 (Phase 4)**: após US1 na prática (precisa haver item para PATCH); aceite
  independente se o teste inserir via repositório
- **US3 (Phase 5)**: após Foundational; na prática usa itens da US1/US2
- **US4 (Phase 6)**: após as rotas existirem (US1–US3)
- **Polish (Phase 7)**: após as histórias desejadas

### User Story Dependencies

- **US1**: só Foundational — MVP isolado (assert no banco; GET manutenção é US2)
- **US2**: logicamente independente se o teste gravar o item; reusa `POST`
- **US3**: independente no aceite; reusa itens ativos/inativos
- **US4**: transversal sobre as quatro rotas

### Within Each User Story

1. Testes escritos e vermelhos
2. Implementação mínima
3. Verde
4. Só então próxima história

### Parallel Opportunities

- T001–T003 em paralelo
- T006–T009 em paralelo após T005 (matriz)
- T011 em paralelo com a preparação de T012 na US1
- T016–T017 em paralelo na US2
- T021–T022 em paralelo na US3
- T028–T029 em paralelo na US4
- T032–T034 em paralelo no polish

---

## Parallel Example: User Story 1

```text
# Testes em paralelo (antes da implementação):
T011 test_catalogo.py (serviço, repositório falso)
T012 test_catalogo.py (integração POST)

# Depois, implementação na ordem:
T013 → T014 → T015
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: `POST /catalogo` nas cinco categorias, `422` no inválido
4. Demo: curl da recepção cria um horário

### Incremental Delivery

1. US1 → criar fatos
2. US2 → editar / desativar / manutenção
3. US3 → catálogo ativo + porta
4. US4 → hotel e perfil
5. Polish → estado do projeto + logs + quickstart

### Suggested MVP scope

**Só US1** (T001–T015) prova o valor de “o hotel passa a ter fatos cadastráveis”.
US2 e US3 são aceites obrigatórios da spec **antes** de marcar F2.1 concluída —
completar na mesma entrega; não abrir F2.2 sem a consulta ativa.

---

## Notes

- [P] = arquivos distintos, sem depender de tarefa incompleta da mesma sequência
- Sem revisão Alembic; sem React; sem preço; sem mensagem ao hóspede
- Porta não abre conexão própria; HTTP de manutenção não passa pela porta
- `id_hotel` só da sessão
- Commit por tarefa ou grupo lógico **só se o usuário pedir commit**
- Evitar: `DELETE` real; vazar inativo no GET ativo; gestão escrevendo; SQL de
  catálogo fora de `propriedade.repository`
