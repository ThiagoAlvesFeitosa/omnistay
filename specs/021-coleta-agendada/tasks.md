---
description: "Task list for feature implementation"
---

# Tasks: Coleta Agendada de Mercado

**Input**: Design documents from `/specs/021-coleta-agendada/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de
produção sem teste que falhe antes pelo motivo certo.

**Organization**: Tarefas agrupadas por história (US1–US4), na ordem da spec.
Esquema (`coletar_mercado` + unicidade do trabalho **aberto**), porta
`FontePublica`, fila, semente da periodicidade e esqueleto do agendador entram
na Foundational. A varredura que **enfileira** e o consumo que **grava sucesso**
são a US1 (MVP). Allowlist e ramo no consumidor nascem **no mesmo passo**
(lição F3.1/F3.2). Zero rota HTTP nova.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US4)

## Como ver os testes falharem nesta fatia

**Esquema.** `testes/integracao/test_conformidade_do_esquema.py` compara o banco
migrado com `docs/04-schema.sql`. Editar o documento **antes** da revisão deixa
a conformidade vermelha. A `0020` a devolve ao verde.

**Garantias.** `testes/integracao/test_garantias_do_banco.py`: sem a migração, o
`INSERT` de `coletar_mercado` cai no `ck_trabalho_tipo`; dois trabalhos abertos
do mesmo concorrente entram — o teste do índice único fica vermelho pelo motivo
certo.

**CLI.** Hoje `--verificar-mercado` não existe: o parser recusa. O unitário da
US1 falha até a flag existir. `--uma-passagem` já é testado; esta fatia
**estende** o teste para também não chamar a varredura de mercado.

**Porta / serviço / varredura.** Unitários falham por `ImportError` /
`AttributeError` / `NotImplementedError` até existir a implementação.

**Allowlist.** Se o tipo entrar em `TIPOS_CONSUMIVEIS` sem ramo no consumidor,
o claim marca `tipo_desconhecido` e destrói o gancho — por isso allowlist e
ramo são a mesma tarefa.

---

## Phase 1: Setup

**Purpose**: constantes de teste, semente da periodicidade nas duas
propriedades de integração, protocolo e falsa em esqueleto

- [X] T001 [P] Criar `testes/suporte/coleta_mercado.py` com constantes
      estáveis: chave `periodicidade_coleta_mercado`, valor padrão `24`,
      preço de fixture (`150.00`), nota (`4.50`), identidade esperada do
      coletor (`OmniStay-Coletor`). Reusar `NOME`/`URL_FONTE` de
      `testes/suporte/concorrentes.py`. Sem segredo, sem rede
- [X] T002 [P] Em `testes/suporte/ambiente_de_acesso.py`, semear
      `periodicidade_coleta_mercado=24` nas duas propriedades (junto das
      chaves já existentes). Sem isso, a varredura das integrações cai em
      `periodicidade_ausente` e afirma o caminho errado
- [X] T003 [P] Criar `app/portas/fonte_publica.py` com `DiretivaAcesso`
      (`permite` · `recusa` · `ausente`), `ResultadoPublico` (`desfecho`,
      `preco`, `nota_media`) e protocolo `FontePublica` com
      `consultar_diretiva` e `coletar_publico` conforme
      [contracts/fonte-publica.md](./contracts/fonte-publica.md). Sem
      `urllib` neste arquivo
- [X] T004 [P] Criar `app/adaptadores/fonte_falsa.py` com `FonteFalsa`
      configurável por URL (diretiva + resultado), registrando a última
      identidade usada; métodos podem devolver `permite` + `encontrado`
      por omissão até as histórias. Sem rede

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: revisão `0020`, tipo na fila, semente da periodicidade, SQL
nomeado de coleta, esqueleto de agendar/processar. **Nenhuma rota HTTP
nova. Tipo ainda fora da allowlist** (o consumidor não o reclama até a
US1).

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. Ordem do esquema:
T005 → T006 → T008 → T009 (teste vermelho no documento, depois migração
verde).

- [X] T005 Estender `testes/integracao/test_garantias_do_banco.py`: `INSERT`
      de trabalho `coletar_mercado` aceito pelo `ck_trabalho_tipo`; segundo
      `INSERT` **aberto** (`pendente` ou `processando`) do mesmo
      `id_concorrente` recusado por
      `uq_trabalho_coletar_mercado_concorrente_aberto`; segundo trabalho
      `concluido` do mesmo concorrente **passa**; payload só com
      `id_concorrente`. Rodar e **ver falhar** (FR-016, Artigo IX,
      [data-model.md](./data-model.md))
- [X] T006 Aplicar o delta em `docs/04-schema.sql`: `coletar_mercado` em
      `ck_trabalho_tipo`; índice único parcial do trabalho aberto por
      `(payload->>'id_concorrente')::bigint` com
      `status IN ('pendente', 'processando')`. **Não** alterar `0001` nem
      recriar `coleta_mercado`. Rodar
      `testes/integracao/test_conformidade_do_esquema.py` e **ver falhar**
- [X] T007 [P] Alinhar `docs/04-modelagem-de-dados.md` §6.6: F5.2 **escreve**
      `coleta_mercado` (série, INSERT only); periodicidade semeada 24 h;
      unicidade do trabalho aberto (não da história). Painel continua F5.3
- [X] T008 Criar `alembic/versions/sql/0020_coleta_agendada.sql` — cópia
      congelada do delta da T006 **mais** `INSERT` idempotente de
      `periodicidade_coleta_mercado = 24` por hotel (padrão da `0016`)
- [X] T009 Criar `alembic/versions/0020_coleta_agendada.py`
      (`down_revision = "0019_cadastrar_concorrentes"`), `upgrade` executa o
      SQL congelado, `downgrade` remove o índice, restaura o CHECK da
      `0018`/`0019` e **não** apaga a chave já semeada. T005 e a
      conformidade verdes
- [X] T010 [P] Unitário em
      `testes/unitarios/modulos/propriedade/test_bootstrap.py`: instalação
      inicial grava `periodicidade_coleta_mercado` = `24`. Rodar e **ver
      falhar** (FR-002)
- [X] T011 Acrescentar `PARAMETROS_MERCADO_PADRAO =
      {"periodicidade_coleta_mercado": "24"}` e semear em
      `criar_instalacao_inicial` em `app/modulos/propriedade/service.py`
      até T010 verde
- [X] T012 [P] Unitário em `testes/unitarios/fila/test_enfileirar_coleta_mercado.py`:
      `enfileirar_coletar_mercado` grava tipo, `id_hotel` na coluna, payload
      só `id_concorrente` (sem URL, sem preço). Rodar e **ver falhar**.
      **Não** exigir o tipo em `TIPOS_CONSUMIVEIS` ainda
      ([contracts/agendador-e-fila.md](./contracts/agendador-e-fila.md))
- [X] T013 Implementar `enfileirar_coletar_mercado` em
      `app/fila/repository.py` e `app/fila/service.py` até T012 verde.
      Colisão do índice único aberto deve ser ignorada pelo serviço
      (ciclo já em voo). **Não** incluir o tipo em `TIPOS_CONSUMIVEIS`
      nem no `IN` de `reclamar_proximo`
- [X] T014 [P] Acrescentar em `app/modulos/mercado/repository.py` as funções
      nomeadas `inserir_coleta`, `ultima_coleta` (`id_concorrente`,
      `coletado_em DESC LIMIT 1`) e `listar_ativos_de_todos` (devolve
      `id_hotel`, `id_concorrente`, `url_fonte`; só `ativo`) — esqueleto
      com `NotImplementedError` até as histórias. Todo SQL considera
      `id_hotel` (coluna ou JOIN)
- [X] T015 [P] Acrescentar em `app/modulos/mercado/service.py` as funções
      `agendar_coletas_devidas` e `processar_trabalho_coletar_mercado`
      levantando `NotImplementedError` até as histórias
- [X] T016 [P] Acrescentar `verificar_coletas_mercado` em
      `worker/agendador.py` com `agora` injetável e
      `NotImplementedError` até a US1 (padrão de
      `verificar_pulsos_pendentes`)
- [X] T017 [P] Unitário em `testes/unitarios/portas/test_fonte_publica.py`:
      o protocolo declara `consultar_diretiva` e `coletar_publico`
      (inspect da assinatura, padrão de
      `testes/unitarios/portas/test_mensageria.py`)

**Checkpoint**: tipo e índice no banco; enqueue existe e **não** é
consumido; porta e falsa compilam; periodicidade semeada. Histórias podem
começar.

---

## Phase 3: User Story 1 - Preço e avaliação entram sozinhos, com data (Priority: P1) 🎯 MVP

**Goal**: Fonte ativa devida vira um trabalho; o consumidor grava **um**
registro novo de sucesso com data, preço e/ou nota; o anterior permanece;
inativo e lista vazia não geram linha.

**Independent Test**: Concorrente ativo, periodicidade 24, sem coleta
anterior → `--verificar-mercado` cria 1 `coletar_mercado`; `--uma-passagem`
com `FonteFalsa` (`permite` + preço/nota) insere 1 linha `sucesso=true`
com `coletado_em`; segunda varredura na mesma janela → 0 extras; inativo →
0 trabalhos.

### Tests for User Story 1 ⚠️

> Escrever primeiro; rodar; ver falhar pelo motivo certo antes de implementar.

- [X] T018 [P] [US1] Unitários em
      `testes/unitarios/worker/test_verificar_coletas_mercado.py`: fonte
      ativa nunca coletada enfileira 1; inativo não enfileira; hotel sem
      ativo devolve 0 sem erro; segunda chamada na mesma janela devolve 0
      (FR-001, FR-003, FR-014, FR-021,
      constantes de `testes/suporte/coleta_mercado.py`)
- [X] T019 [P] [US1] Unitários em
      `testes/unitarios/modulos/mercado/test_coleta.py`: processar com
      falsa `permite` + `encontrado` insere sucesso com preço/nota e data;
      segundo ciclo (relógio avançado) insere **outra** linha e não altera
      a primeira; payload/log sem URL (FR-004, FR-005)
- [X] T020 [US1] Integração em `testes/integracao/test_coleta_mercado.py`:
      gestão cadastra concorrente ativo (reuso F5.1); `verificar_coletas_mercado`
      + `processar_uma_passagem` com `FonteFalsa` grava 1 `coleta_mercado`
      sucesso; `SELECT` da linha anterior depois de um segundo ciclo
      (relógio) permanece idêntico. Usar
      `testes/suporte/ambiente_de_acesso.py`. Rodar e ver falhar
- [X] T021 [P] [US1] Estender `testes/unitarios/worker/test_cli_worker.py`:
      `--verificar-mercado` chama a varredura e encerra. Rodar e **ver
      falhar** (parser recusa a flag)

### Implementation for User Story 1

- [X] T022 [US1] Implementar `inserir_coleta`, `ultima_coleta` e
      `listar_ativos_de_todos` em `app/modulos/mercado/repository.py`
      (só INSERT; `id_hotel` via concorrente;
      [contracts/registro-de-coleta.md](./contracts/registro-de-coleta.md))
- [X] T023 [US1] Implementar `agendar_coletas_devidas` em
      `app/modulos/mercado/service.py` (periodicidade por hotel, janela
      pela última coleta, enqueue; colisão = já em voo) e
      `verificar_coletas_mercado` em `worker/agendador.py` até T018 verde
- [X] T024 [US1] Implementar `processar_trabalho_coletar_mercado` em
      `app/modulos/mercado/service.py` no caminho feliz: relê ficha ativa;
      diretiva `permite`; `coletar_publico`; INSERT sucesso; trabalho
      `concluido`. Inativa no claim → `concluido` sem INSERT. Reclaim com
      coleta `coletado_em >= criado_em` do trabalho → sem segunda visita.
      Até T019 verde
- [X] T025 [US1] Incluir `coletar_mercado` em `TIPOS_CONSUMIVEIS` e no `IN`
      de `reclamar_proximo` em `app/fila/repository.py` **e** o ramo em
      `worker/consumidor.py` **no mesmo passo**; injetar `FontePublica`
      em `processar_uma_passagem` / `processar_uma_passagem_na_engine`
      (default `FonteFalsa`). Sem allowlist sem ramo
- [X] T026 [US1] Acrescentar `--verificar-mercado` e
      `_rodar_verificacao_mercado` em `worker/__main__.py`; no modo
      contínuo, chamar junto com cadastros/boas-vindas/pulsos. T020 e
      T021 verdes. `--uma-passagem` ainda **não** dispara a varredura

**Checkpoint**: US1 entregável sozinha — ciclo devido grava série datada
sem sobrescrever. Falha explícita, diretiva recusada e isolamento fino
ainda podem faltar.

---

## Phase 4: User Story 2 - Falha fica registrada e não se mistura com valor (Priority: P1)

**Goal**: Tentativa que não obtém dado público vira linha `sucesso=false`
com data, sem preço/nota encontrados. O sucesso anterior permanece.
Preço **zero** é sucesso. Só preço ou só nota também.

**Independent Test**: Fonte com sucesso antigo; ciclo seguinte
`indisponivel` → nova linha falha, primeira intacta. Falsa devolvendo
`preco=0` → `sucesso=true`. Só nota 4.5 sem preço → sucesso.

### Tests for User Story 2 ⚠️

- [X] T027 [P] [US2] Unitários em
      `testes/unitarios/modulos/mercado/test_coleta.py`: `sem_dado`,
      `indisponivel` e `exige_autenticacao` inserem falha sem valor
      encontrado e **não** alteram a linha anterior; `preco=0` é sucesso;
      só preço ou só nota é sucesso (FR-006, FR-007, FR-008)
- [X] T028 [US2] Integração em `testes/integracao/test_coleta_mercado.py`:
      sucesso depois falha; `id_coleta` antigo, valores e `coletado_em`
      inalterados; CHECK `ck_coleta_sucesso_tem_dado` já existente recusa
      sucesso sem preço nem nota se alguém inserir direto
      ([contracts/registro-de-coleta.md](./contracts/registro-de-coleta.md))

### Implementation for User Story 2

- [X] T029 [US2] Completar o mapeamento de desfechos em
      `processar_trabalho_coletar_mercado` em
      `app/modulos/mercado/service.py`: falha da porta → INSERT
      `sucesso=false` + trabalho `concluido` (**sem** `falha`/backoff da
      fila). T027–T028 verdes

**Checkpoint**: Falha é primeiro registro; zero ≠ falha; série preservada.

---

## Phase 5: User Story 3 - Coletor honesto (Priority: P1)

**Goal**: Diretiva lida antes do conteúdo; `recusa`/`ausente` não recolhem
página e gravam falha; identidade OmniStay, não navegador; nenhum dado de
avaliador persistido. Adaptador HTTP só com fixture local.

**Independent Test**: Falsa em `recusa` ou `ausente` → 0 chamadas a
`coletar_publico`, 1 falha datada. Identidade da falsa contém OmniStay e
não imita Chrome. Fixture HTTP: `robots.txt` proibindo o caminho →
`recusa`; arquivo ausente → `ausente`.

### Tests for User Story 3 ⚠️

- [X] T030 [P] [US3] Unitários em
      `testes/unitarios/modulos/mercado/test_coleta.py`: diretiva `recusa`
      e `ausente` não chamam `coletar_publico` e inserem falha; log
      `diretiva_recusada` / `diretiva_ausente` (FR-009, FR-011)
- [X] T031 [P] [US3] Unitários em
      `testes/unitarios/adaptadores/test_fonte_falsa.py`: última identidade
      é reconhecível como coletor OmniStay e **não** imita navegador;
      resultado **não** carrega nome/texto de avaliador (FR-010, FR-012)
- [X] T032 [P] [US3] Unitários em
      `testes/unitarios/adaptadores/test_fonte_http.py` com **fixture
      local** (HTTP de teste, sem OTA): diretiva que proíbe o caminho →
      `recusa`; sem corpo de diretiva → `ausente` (não trata como
      permissão); JSON-LD `Offer`+`AggregateRating` → `encontrado`; página
      sem dado estruturado → `sem_dado`. **Proibido** bater em URL viva
      (FR-020)

### Implementation for User Story 3

- [X] T033 [US3] Garantir em `processar_trabalho_coletar_mercado`
      (`app/modulos/mercado/service.py`) que `coletar_publico` só corre
      após `permite`. T030 verde
- [X] T034 [US3] Fechar identidade e mapa da `FonteFalsa` em
      `app/adaptadores/fonte_falsa.py` até T031 verde
- [X] T035 [US3] Implementar `app/adaptadores/fonte_http.py` com biblioteca
      padrão (`urllib.request`, `urllib.robotparser`, `json`): User-Agent
      `OmniStay-Coletor/1.0`; ausência de diretiva = `ausente`; extração
      só de JSON-LD/schema.org. Sem `httpx`, sem BeautifulSoup, sem LLM.
      T032 verde. A suíte de integração **não** instancia este adaptador
      contra rede

**Checkpoint**: Coleta desonesta recusada; testes sem site alheio.

---

## Phase 6: User Story 4 - Periodicidade, isolamento e fora do hóspede (Priority: P1)

**Goal**: Cadência por propriedade; hotel A não coleta B; chave ausente
não inventa intervalo; zero mensagem ao hóspede; `--uma-passagem` não
varre mercado.

**Independent Test**: Dois hotéis, periodicidades 24 e 48; avançar 24 h →
só o primeiro enfileira. Apagar a chave → 0 trabalhos e log
`periodicidade_ausente`. Cookie/hóspede: 0 mensagens novas. CLI
`--uma-passagem` não chama `_rodar_verificacao_mercado`.

### Tests for User Story 4 ⚠️

- [X] T036 [P] [US4] Unitários em
      `testes/unitarios/worker/test_verificar_coletas_mercado.py`: dois
      hotéis com periodicidades diferentes; chave ausente/zero/não
      numérica → 0 enqueue daquele hotel e log `periodicidade_ausente`;
      mudar a chave vale na verificação **seguinte**, sem replay
      (FR-002, FR-022, Artigo XIII)
- [X] T037 [P] [US4] Integração em `testes/integracao/test_coleta_mercado.py`:
      dois hotéis via `ambiente_de_acesso`; mesma URL em ambos gera
      **duas** séries; ciclo de B não lê/grava coleta de A (FR-015,
      FR-013)
- [X] T038 [P] [US4] Estender
      `testes/unitarios/worker/test_cli_worker.py`: `--uma-passagem` não
      chama a varredura de mercado (além de cadastros/pulsos já
      cobertos) (FR-018)
- [X] T039 [US4] Unitário em
      `testes/unitarios/modulos/mercado/test_coleta.py`: processar **não**
      chama `MensageriaGateway` e **não** altera `item_vendavel`/tarifa
      (FR-017)

### Implementation for User Story 4

- [X] T040 [US4] Completar leitura da periodicidade em
      `worker/agendador.py` / `agendar_coletas_devidas` (`inteiro ≥ 1`,
      cache por hotel, `periodicidade_ausente`) até T036 verde — se já
      nasceu na US1, só fechar os casos novos
- [X] T041 [US4] Garantir `id_hotel` em todo SQL de coleta e no
      `WHERE` do claim (`app/modulos/mercado/repository.py`). T037 verde
- [X] T042 [US4] Fechar T038–T039: `__main__.py` não dispara mercado em
      `--uma-passagem`; processador sem import de mensageria. Se já
      estiver assim, só os testes

**Checkpoint**: Multi-tenant, parâmetro e “não é fluxo do hóspede”
exercitados. Painel ainda não existe (F5.3).

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: logs, estado do projeto, fronteiras, confirmação de que nada
vaze para HTTP/política/React

- [X] T043 [P] Estender
      `testes/unitarios/modulos/mercado/test_log_sem_conteudo.py`:
      desfechos de coleta registram `id_concorrente`, `id_hotel` e código
      (`sucesso`, `falha`, `diretiva_recusada`, `periodicidade_ausente`);
      **não** registram URL, HTML, preço, nota nem texto de avaliador
      (FR-019)
- [X] T044 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F5.2 em andamento /
      concluída na entrega; quarta porta `FontePublica`; diretiva ausente
      **não** é permissão (divergência do default de `robots.txt`);
      APScheduler continua recusado; próxima fatia F5.3; sem React, sem
      disparo manual, revisão `0020`
- [X] T045 Confirmar que `app/modulos/mercado/service.py` **não** importa
      `urllib.request` / `httpx`; HTTP só em
      `app/adaptadores/fonte_http.py`; `app/modulos/acesso/politica.py`
      **não** ganha operação nova; nenhuma rota nova em
      `app/modulos/mercado/router.py` (`testes/integracao/test_rotas_protegidas.py`
      permanece verde sem acréscimo em `ROTAS_PUBLICAS`)
- [X] T046 Revisar fronteiras: SQL de `coleta_mercado` só em
      `app/modulos/mercado/repository.py`; `conversa` e `hospedagem` **não**
      importam coleta; agendador orquestra (parâmetro em `propriedade`,
      enqueue via `mercado`)
- [X] T047 Percorrer [quickstart.md](./quickstart.md) (ou equivalente
      automatizado): `pytest testes/unitarios -q`,
      `pytest testes/integracao/test_coleta_mercado.py -q`,
      `test_garantias_do_banco.py`, `test_conformidade_do_esquema.py` e
      `test_rotas_protegidas.py`; tudo verde **sem** rede externa

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: após Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: após Foundational — MVP
- **US2 (Phase 4)**: após o processador da US1 (mapeia desfechos de falha)
- **US3 (Phase 5)**: após US1 (precisa visitar); na prática depois da US2
  para a falha por diretiva reusar o INSERT de falha
- **US4 (Phase 6)**: após a varredura existir (US1); casos de chave/isolamento
  podem ser preenchidos se a US1 já leu o parâmetro
- **Polish (Phase 7)**: após as histórias desejadas

### User Story Dependencies

- **US1**: só Foundational — MVP isolado (sucesso datado + enqueue)
- **US2**: depende do processador da US1; aceite independente se o teste
  gravar um sucesso e depois falhar o ciclo
- **US3**: independente no aceite da diretiva; reusa INSERT de falha da US2
- **US4**: transversal sobre varredura e SQL

### Within Each User Story

1. Testes escritos e vermelhos
2. Implementação mínima
3. Verde
4. Só então próxima história

### Parallel Opportunities

- T001–T004 em paralelo
- T007, T010, T012, T014, T015, T016, T017 em paralelo após T009 (esquema
  no banco) — T010/T011 não dependem da fila
- T018, T019, T021 em paralelo
- T027 e T028 em paralelo
- T030, T031, T032 em paralelo
- T036, T037, T038 em paralelo
- T043 e T044 em paralelo

---

## Parallel Example: User Story 1

```text
T018 Unitários da varredura em testes/unitarios/worker/test_verificar_coletas_mercado.py
T019 Unitários do processador em testes/unitarios/modulos/mercado/test_coleta.py
T021 CLI --verificar-mercado em testes/unitarios/worker/test_cli_worker.py
```

Depois, em sequência: T022 → T023 → T024 → T025 (allowlist+ramo juntos) → T026.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup
2. Phase 2: Foundational (bloqueia)
3. Phase 3: US1 — fonte devida → trabalho → linha de sucesso datada
4. **STOP and VALIDATE**: `--verificar-mercado` + `--uma-passagem` com falsa
5. US2–US4 e polish em fatias seguintes da mesma entrega

### Incremental Delivery

1. Setup + Foundational → tipo no banco, enqueue mudo
2. US1 → demo: preço entra sozinho com data
3. US2 → falha visível, zero ≠ vazio
4. US3 → banca: diretiva e identidade
5. US4 → periodicidade e isolamento
6. Polish → estado do projeto e suíte cheia

### Parallel Team Strategy

Um desenvolvedor, prazo fixo: ordem US1 → US2 → US3 → US4. Não paralelizar
histórias no mesmo processador (`processar_trabalho_coletar_mercado`).

---

## Notes

- [P] = arquivos distintos, sem dependência pendente
- Allowlist e ramo do consumidor são **uma** tarefa (T025)
- `FonteHttp` não entra na suíte de integração contra rede — só fixture
- Sem rota nova, sem operação nova na matriz, sem React
- Próximo: `/speckit-implement`
