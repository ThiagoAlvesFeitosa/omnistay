---
description: "Task list for feature implementation"
---

# Tasks: Cadastro de Concorrentes

**Input**: Design documents from `/specs/020-cadastrar-concorrentes/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de
produção sem teste que falhe antes pelo motivo certo.

**Organization**: Tarefas agrupadas por história de usuário (US1–US4), na ordem
da spec. Tabela `concorrente` já existe na `0001`; a revisão `0019` só acrescenta
UNIQUE da fonte, CHECK de URL e índice parcial de ativos.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US4)

## Como ver os testes falharem nesta fatia

**Matriz.** Acrescentar `alterar_concorrentes` e `ler_concorrentes` em
`OPERACOES_ESPERADAS` **antes** de `politica.py` deixa
`test_matriz_completa_bate_com_o_contrato` vermelho. As duas operações novas
o devolvem ao verde.

**Esquema.** `testes/integracao/test_conformidade_do_esquema.py` compara o banco
migrado com `docs/04-schema.sql`. Editar o documento **antes** da revisão deixa
a conformidade vermelha apontando o UNIQUE / CHECK / índice. A `0019` a
devolve ao verde.

**Serviço.** Unitários com repositório falso falham por `ImportError` /
`AttributeError` / `DadosInvalidos` ausente até existir a implementação.

**Rotas.** `testes/integracao/test_rotas_protegidas.py` varre o que estiver
registrado: depois de ligar o roteador, cada rota nova exige `401` sem cookie —
não editar `ROTAS_PUBLICAS`.

**HTTP.** Hoje não existe `/concorrentes`. A integração falha com `404` de rota
até o roteador existir.

---

## Phase 1: Setup

**Purpose**: Arquivos que o plano prevê e ainda não existem no módulo `mercado`

- [X] T001 [P] Criar `app/modulos/mercado/__init__.py` vazio (pacote; camada
      `model` continua sem ORM)
- [X] T002 [P] Criar `app/modulos/mercado/schema.py` com docstring do módulo
      (modelos Pydantic entram na T014)
- [X] T003 [P] Criar `app/modulos/mercado/router.py` com
      `APIRouter(tags=["mercado"])` e sem rotas ainda
- [X] T004 [P] Criar `testes/suporte/concorrentes.py` com constantes estáveis:
      nome (`Hotel Praia Norte`), `url_fonte` válida
      (`https://www.exemplo.com/hotel-praia-norte`), detalhe `409` de fonte
      duplicada, detalhe `404` (`Concorrente nao encontrado.`). Sem segredo,
      sem rede

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: operações na matriz, delta de esquema, contratos Pydantic, SQL
nomeado em esqueleto e roteador montado — o que nenhuma história deve
reinventar. **Nenhuma rota HTTP ainda** (exceto o include vazio).

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. Ordem do esquema:
T007 → T008 → T010 → T011 (teste vermelho no documento, depois migração verde).

- [X] T005 Acrescentar casos em `testes/unitarios/modulos/acesso/test_politica.py`:
      `alterar_concorrentes` e `ler_concorrentes` permitidas **só** para
      `gestor`, recusadas para `recepcao` e `staff`; incluir as duas em
      `OPERACOES_ESPERADAS`. Rodar e **ver falhar** o caso das operações novas
      (FR-014, FR-015,
      [contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))
- [X] T006 Acrescentar `alterar_concorrentes` e `ler_concorrentes` a `OPERACOES`
      em `app/modulos/acesso/politica.py` (`gestor` somente) até T005 passar
- [X] T007 Estender `testes/integracao/test_garantias_do_banco.py`: `INSERT` em
      `concorrente` com `https://a.exemplo/x` aceito; texto sem esquema,
      `mailto:` e URL com espaço recusados por `ck_concorrente_url_fonte`;
      segundo insert no mesmo hotel com a mesma fonte (maiúsculas diferentes
      ou espaços nas pontas) viola `uq_concorrente_hotel_fonte` **mesmo com a
      primeira linha inativa**; dois hotéis com a mesma URL passam. Rodar e
      **ver falhar** (FR-003, FR-009, [data-model.md](./data-model.md))
- [X] T008 Aplicar o delta em `docs/04-schema.sql` na tabela `concorrente`:
      `ck_concorrente_url_fonte`, `uq_concorrente_hotel_fonte` em
      `(id_hotel, lower(btrim(url_fonte)))`, `ix_concorrente_hotel_ativo` em
      `(id_hotel) WHERE ativo`. **Não** alterar `0001` nem `coleta_mercado`.
      Rodar `testes/integracao/test_conformidade_do_esquema.py` e **ver falhar**
      pela divergência
- [X] T009 [P] Alinhar `docs/04-modelagem-de-dados.md` §6.6: unicidade da fonte
      por hotel inclusive inativo; CHECK de URL; desativar não apaga; índice
      parcial de ativos. Não dizer que esta fatia coleta preço
- [X] T010 Criar `alembic/versions/sql/0019_cadastrar_concorrentes.sql` — cópia
      congelada do delta da T008
- [X] T011 Criar `alembic/versions/0019_cadastrar_concorrentes.py`
      (`down_revision = "0018_lista_pedidos_chat"`), `upgrade` executa o SQL
      congelado, `downgrade` remove CHECK e os dois índices. T007 e a
      conformidade verdes
- [X] T012 [P] Criar em `app/modulos/mercado/schema.py` os contratos de
      `POST /concorrentes`, `PATCH /concorrentes/{id}`, `GET /concorrentes` e
      `GET /concorrentes/ativos` conforme
      [contracts/api-de-concorrentes.md](./contracts/api-de-concorrentes.md)
      (`extra="forbid"`; sem `id_hotel` no JSON; lista ativa sem campo `ativo`)
- [X] T013 [P] Criar `app/modulos/mercado/repository.py` com funções nomeadas
      `inserir`, `atualizar`, `listar_manutencao`, `listar_ativos` — todas
      recebem `id_hotel`; esqueleto com `NotImplementedError` até as histórias
- [X] T014 [P] Criar `app/modulos/mercado/service.py` com as funções
      `criar_concorrente`, `alterar_concorrente`, `listar_manutencao`,
      `listar_fontes_ativas` levantando `NotImplementedError` até as histórias
- [X] T015 Registrar o roteador de mercado em `app/main.py`
      (`include_router`). Sem rotas ainda, `test_rotas_protegidas` permanece
      verde

**Checkpoint**: matriz com as duas operações; esquema `0019` no banco; contratos
e SQL nomeado existem; ainda não grava pela API. Histórias podem começar.

---

## Phase 3: User Story 1 - Cadastrar concorrente com nome e fonte (Priority: P1) 🎯 MVP

**Goal**: Gestão autentica e cria um concorrente com nome e endereço de fonte
pública; nasce ativo no hotel da sessão. Campo vazio, URL inválida ou fonte já
cadastrada na casa são recusados sem gravar.

**Independent Test**: Sessão de gestão → `POST /concorrentes` com nome e
`https://…` → `201` com `ativo: true`; a linha existe em `concorrente` daquele
`id_hotel`. `mailto:`, texto sem esquema ou nome em branco → `422`, zero
insert. Segunda POST com a mesma URL → `409`.

### Tests for User Story 1 ⚠️

> Escrever primeiro; rodar; ver falhar pelo motivo certo antes de implementar.

- [X] T016 [P] [US1] Unitários em
      `testes/unitarios/modulos/mercado/test_concorrentes.py` com repositório
      falso: criar dispara insert com `id_hotel` da sessão e `ativo=true`; trim
      em nome/URL; só espaços, URL sem esquema, `mailto:`, URL com usuário/senha
      e nome com 121 caracteres recusam **sem** chamar insert; fonte já
      existente (casefold/trim) levanta colisão (FR-001 a FR-004, FR-009,
      constantes de `testes/suporte/concorrentes.py`)
- [X] T017 [US1] Integração em `testes/integracao/test_concorrentes.py`: gestão
      cria (`201`); no banco há a linha ativa; URL inválida e nome em branco →
      `422` e nada gravado; fonte duplicada → `409`; sem cookie → `401`. Usar
      `testes/suporte/ambiente_de_acesso.py`. Rodar e ver falhar

### Implementation for User Story 1

- [X] T018 [US1] Implementar `inserir` em `app/modulos/mercado/repository.py`
      (`INSERT … RETURNING`, `id_hotel` no SQL) conforme
      [data-model.md](./data-model.md)
- [X] T019 [US1] Implementar `criar_concorrente` em
      `app/modulos/mercado/service.py` (`urllib.parse.urlparse`, trim, tamanhos,
      colisão → exceção de fonte duplicada, log com id/hotel/ação **sem** nome
      nem URL) até T016 verde
- [X] T020 [US1] Implementar `POST /concorrentes` em
      `app/modulos/mercado/router.py` com
      `exigir_operacao("alterar_concorrentes")`, `id_hotel` só da sessão,
      `201` / `422` / `409`. Fechar T017 verde

**Checkpoint**: US1 entregável sozinha — criar concorrente, recusa clara,
persistido no hotel certo. Sem GET ainda.

---

## Phase 4: User Story 2 - Corrigir e desativar sem apagar (Priority: P1)

**Goal**: PATCH altera nome/URL e/ou `ativo`. Desativar some da consulta de
fontes ativas (quando ela existir) e permanece na manutenção. Não há `DELETE`.
Fonte desativada continua a ocupar o endereço.

**Independent Test**: Criar → PATCH nome → PATCH `ativo: false` →
`GET /concorrentes` ainda lista com `ativo: false`; `DELETE` → `405` e a linha
permanece; POST de outra ficha com a URL da desativada → `409`; PATCH de URL
para fonte de outro concorrente da casa → `409`.

### Tests for User Story 2 ⚠️

- [X] T021 [P] [US2] Unitários em
      `testes/unitarios/modulos/mercado/test_concorrentes.py`: PATCH nome/URL
      persiste e mantém `ativo`; `ativo=false` / `true`; corpo vazio recusa; id
      inexistente → `ConcorrenteNaoEncontrado`; colisão de URL no PATCH recusa
      (FR-005 a FR-009)
- [X] T022 [P] [US2] Integração em `testes/integracao/test_concorrentes.py`:
      PATCH `200`; `GET /concorrentes` lista ativos e inativos ordenados por
      nome, id; `DELETE /concorrentes/{id}` → `405` e a linha permanece; POST
      com URL de ficha inativa → `409`

### Implementation for User Story 2

- [X] T023 [US2] Implementar `atualizar` (`WHERE id_concorrente AND id_hotel`)
      e `listar_manutencao` (ordem `nome`, `id_concorrente`) em
      `app/modulos/mercado/repository.py`
- [X] T024 [US2] Implementar `alterar_concorrente` e `listar_manutencao` em
      `app/modulos/mercado/service.py` até T021 verde (log `editar` /
      `desativar` / `reativar`)
- [X] T025 [US2] Implementar `PATCH /concorrentes/{id_concorrente}` e
      `GET /concorrentes` (`ler_concorrentes`) em
      `app/modulos/mercado/router.py`; **não** registrar `DELETE`.
      `ConcorrenteNaoEncontrado` → `404`. T022 verde

**Checkpoint**: US1 e US2 independentes; desativar não apaga; manutenção vê
inativos; fonte inativa não pode ser recadastrada.

---

## Phase 5: User Story 3 - Só fonte ativa entra na consulta de acompanhamento (Priority: P1)

**Goal**: `GET /concorrentes/ativos` e `listar_fontes_ativas(id_hotel)` devolvem
só ativos (id, nome, URL), sem campo `ativo`. Vazio é `200` com `"fontes": []`.
Nenhuma fonte é visitada; `coleta_mercado` não ganha linha.

**Independent Test**: Propriedade com um ativo e um inativo → GET ativos contém
só o ativo. Propriedade vazia → `"fontes": []`. Contagem de `coleta_mercado`
inalterada.

### Tests for User Story 3 ⚠️

- [X] T026 [P] [US3] Unitários em
      `testes/unitarios/modulos/mercado/test_concorrentes.py`:
      `listar_fontes_ativas` omite inativos, hotel sem ativo devolve sequência
      vazia, **não** chama cliente HTTP (FR-010 a FR-012,
      [contracts/fontes-ativas.md](./contracts/fontes-ativas.md))
- [X] T027 [US3] Integração em `testes/integracao/test_concorrentes.py`: GET
      `/concorrentes/ativos` omite inativo; vazio → `"fontes": []` e `200`;
      após criar/desativar, `SELECT count(*) FROM coleta_mercado` permanece 0

### Implementation for User Story 3

- [X] T028 [US3] Implementar `listar_ativos` em
      `app/modulos/mercado/repository.py` (`ativo = true`, ordem nome, id;
      sempre `id_hotel`)
- [X] T029 [US3] Implementar `listar_fontes_ativas` em
      `app/modulos/mercado/service.py` até T026 verde
- [X] T030 [US3] Implementar `GET /concorrentes/ativos` em
      `app/modulos/mercado/router.py` com `exigir_operacao("ler_concorrentes")`.
      T027 verde. HTTP **não** abre a URL

**Checkpoint**: Consulta ativa é o contrato da F5.2; item desativado não vaza;
zero visita à fonte.

---

## Phase 6: User Story 4 - Isolar a lista por hotel e por perfil (Priority: P1)

**Goal**: Hotel A não aparece para B. Só gestão lê e altera. Recepção e operação
recebem `403`. PATCH em id alheio → `404`.

**Independent Test**: Dois hotéis com concorrentes; sessão B não lista A; PATCH
do id de A com sessão B → `404`. Gestão: GET e POST `200`/`201`. Recepção e
staff: GET e POST `403`. A mesma URL pode existir nos dois hotéis.

### Tests for User Story 4 ⚠️

- [X] T031 [P] [US4] Integração em `testes/integracao/test_concorrentes.py`:
      cookie de recepção e de `staff` → GET, POST e PATCH `403` (FR-015)
- [X] T032 [US4] Integração no mesmo arquivo: dois hotéis via
      `ambiente_de_acesso`; GET do hotel B não contém fichas de A; PATCH no id
      de A com sessão B → `404`; POST da mesma URL no hotel B → `201`
      (FR-013, FR-016)

### Implementation for User Story 4

- [X] T033 [US4] Garantir `id_hotel` em **todo** SQL de concorrente e
      `exigir_operacao` correto em cada rota (`alterar_concorrentes` vs
      `ler_concorrentes`) em `app/modulos/mercado/repository.py` e `router.py`.
      T031–T032 verdes — se a recusa já nasceu nas histórias anteriores, só
      fechar os testes

**Checkpoint**: Multi-tenant e matriz exercitados nas quatro rotas.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Logs, edges da spec, estado do projeto, fronteiras e roteiro do
quickstart

- [X] T034 [P] Unitários em
      `testes/unitarios/modulos/mercado/test_log_sem_conteudo.py`: criar,
      editar, desativar e reativar registram id, hotel e ação; **não**
      registram `nome` nem `url_fonte` (FR-017)
- [X] T035 [P] Integração em `testes/integracao/test_concorrentes.py`: dois
      concorrentes com o mesmo nome e URLs distintas são aceitos (ids
      distintos) (FR-019)
- [X] T036 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F5.1 em andamento /
      concluída na entrega; gestão **escreve** a lista (não contradiz “somente
      leitura” do painel de preços); próxima fatia F5.2; sem React, sem visita
      à fonte, revisão `0019`
- [X] T037 Confirmar que `app/modulos/mercado/` **não** importa `httpx` nem
      `urllib.request`; não existe porta nova em `app/portas/`; `DELETE`
      continua `405` (FR-008, FR-012, FR-018)
- [X] T038 Revisar fronteiras: SQL de `concorrente` só em
      `app/modulos/mercado/repository.py`; `propriedade`, `hospedagem` e
      `conversa` **não** importam `mercado.repository`
- [X] T039 Percorrer [quickstart.md](./quickstart.md) (ou equivalente
      automatizado), `pytest testes/unitarios -q`,
      `pytest testes/integracao/test_concorrentes.py -q`,
      `test_garantias_do_banco.py`, `test_conformidade_do_esquema.py` e
      `test_rotas_protegidas.py`; tudo verde sem rede externa

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: após Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: após Foundational — MVP
- **US2 (Phase 4)**: após US1 na prática (precisa haver ficha para PATCH); aceite
  independente se o teste inserir via repositório
- **US3 (Phase 5)**: após Foundational; na prática usa fichas da US1/US2
- **US4 (Phase 6)**: após as rotas existirem (US1–US3)
- **Polish (Phase 7)**: após as histórias desejadas

### User Story Dependencies

- **US1**: só Foundational — MVP isolado (assert no banco; GET manutenção é US2)
- **US2**: logicamente independente se o teste gravar a ficha; reusa `POST`
- **US3**: independente no aceite; reusa ativos/inativos
- **US4**: transversal sobre as quatro rotas

### Within Each User Story

1. Testes escritos e vermelhos
2. Implementação mínima
3. Verde
4. Só então próxima história

### Parallel Opportunities

- T001–T004 em paralelo
- T009, T012, T013 e T014 em paralelo após T011 (esquema no banco) — T012 não
  depende do banco; T013/T014 tampouco
- T016 em paralelo com a preparação de T017 na US1
- T021–T022 em paralelo na US2
- T031 em paralelo com a preparação de T032 na US4
- T034–T036 em paralelo no polish

---

## Parallel Example: User Story 1

```text
# Testes em paralelo (antes da implementação):
T016 test_concorrentes.py (serviço, repositório falso)
T017 test_concorrentes.py (integração POST)

# Depois, implementação na ordem:
T018 → T019 → T020
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: `POST /concorrentes` com URL válida, `422`/`409` no inválido
4. Demo: curl da gestão cria um concorrente

### Incremental Delivery

1. US1 → criar fichas
2. US2 → editar / desativar / manutenção
3. US3 → fontes ativas (contrato da F5.2)
4. US4 → hotel e perfil
5. Polish → estado do projeto + logs + quickstart

### Suggested MVP scope

**Só US1** (T001–T020) prova o valor de “o hotel passa a ter concorrentes
cadastráveis”. US2 e US3 são aceites obrigatórios da spec **antes** de marcar
F5.1 concluída — completar na mesma entrega; não abrir F5.2 sem a consulta de
fontes ativas.

---

## Notes

- [P] = arquivos distintos, sem depender de tarefa incompleta da mesma sequência
- Revisão `0019`; sem React; sem porta hexagonal; sem mensagem ao hóspede
- `id_hotel` só da sessão
- UNIQUE completo (não parcial `WHERE ativo`)
- Commit por tarefa ou grupo lógico **só se o usuário pedir commit**
- Evitar: `DELETE` real; vazar inativo no GET ativos; recepção lendo/escrevendo;
  SQL de `concorrente` fora de `mercado.repository`; visitar a fonte; gravar
  `coleta_mercado`
