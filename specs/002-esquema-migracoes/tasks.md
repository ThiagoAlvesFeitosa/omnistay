---

description: "Task list for feature implementation"
---

# Tasks: Esquema e Migrações

**Input**: Design documents from `/specs/002-esquema-migracoes/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. O Artigo XII da constituição não admite código de produção sem teste que
falhe antes, e a spec exige testes nomeados nas FR-012 a FR-014 e FR-017 a FR-019.

**Organization**: Tarefas agrupadas por história de usuário, para que cada uma seja implementável
e verificável por si.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1, US2, US3)

## Como ver os testes falharem nesta fatia

O ciclo TDD tem uma peculiaridade aqui que precisa ficar explícita, senão o Artigo XII vira
formalidade. As garantias da US2 não são código nosso: são `CHECK`, `UNIQUE` e trigger criados
pela migração. Depois que a US1 estiver pronta, um teste de garantia escrito agora passaria de
primeira — e um teste que passa de primeira não prova nada.

Por isso cada teste de garantia é exercitado **duas vezes**: primeiro contra um banco descartável
sem migração, onde precisa falhar; depois contra o banco migrado, onde precisa passar. É o que a
SC-003 pede ao dizer "falha na ausência da migração e passa após ela", e é a razão de o banco
descartável (T012) ser pré-requisito de tudo.

---

## Phase 1: Setup

**Purpose**: Ponto de partida limpo e lugar para o código de apoio dos testes

- [X] T001 Levantar o ambiente a partir do zero: `docker compose down -v` seguido de
      `docker compose up -d`, confirmando pelo `docker compose ps` que o banco sobe vazio e
      saudável sem intervenção (Cenário 0 do [quickstart.md](./quickstart.md))
- [X] T002 [P] Criar o pacote de apoio aos testes em `testes/suporte/__init__.py`
- [X] T003 [P] Registrar as chaves `DATABASE_URL` e `EXIGIR_POSTGRES` em `.env.example` **sem
      valor**, seguindo a convenção já existente no arquivo, cada uma com um comentário dizendo para
      que serve e qual o formato esperado. Nenhum valor de conexão entra em arquivo versionado,
      nem de desenvolvimento (FR-011)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Corrigir o documento de referência antes de congelá-lo, e construir as ferramentas
de teste das quais todas as histórias dependem

**⚠️ CRÍTICO**: T004 e T005 precisam estar prontas antes de qualquer tarefa que copie o SQL. Uma
cópia congelada a partir do documento errado carrega o erro para sempre.

- [X] T004 Remover `BEGIN;` e `COMMIT;` de `docs/04-schema.sql` e acrescentar ao cabeçalho o
      comentário de que o controle de transação é de quem aplica, indicando
      `psql --single-transaction -f docs/04-schema.sql` para aplicação manual
      (FR-015, [research.md](./research.md) seção 2)
- [X] T005 Trocar `SGBD: PostgreSQL 14+` por `SGBD: PostgreSQL 16` no cabeçalho de
      `docs/04-schema.sql` — compatibilidade não verificada não se declara (FR-021)
- [X] T006 [P] Escrever o teste da política de banco exigido em
      `testes/unitarios/test_politica_de_banco_exigido.py`, sobre uma **função pura** que recebe
      "há banco alcançável" e "o ambiente exige banco" e devolve a decisão: sem banco e sem
      exigência, pular com motivo declarado; sem banco e com exigência, falhar. Rodar e ver falhar.
      A função é testável de dentro da suíte; o hook do pytest não seria, sem plugin adicional
      (FR-019)
- [X] T007 Remover a URL de conexão embutida de `testes/conftest.py`, passando a exigir
      `DATABASE_URL` do ambiente (FR-011, [research.md](./research.md) seção 7)
- [X] T008 Implementar a função de decisão em `testes/suporte/politica_de_banco.py` e chamá-la de
      `pytest_runtest_setup` em `testes/conftest.py`, sobre o marcador `postgres`, lendo
      `EXIGIR_POSTGRES` do ambiente, até T006 passar. O hook fica com poucas linhas: toda a decisão
      mora na função testada (FR-019). *`pytest_runtest_setup` no lugar de
      `pytest_collection_modifyitems`: na coleção só é possível acrescentar um marcador de pular,
      e não fazer o teste falhar.*
- [X] T009 [P] Escrever o teste do extrator de inventário em
      `testes/integracao/test_inventario.py`: dois bancos com uma diferença deliberada em cada
      categoria — coluna, restrição, índice, corpo de função, corpo de visão e momento de trigger —
      produzem uma diferença detectada e nomeada. Rodar e ver falhar
- [X] T010 Implementar o banco descartável em `testes/suporte/banco_descartavel.py`: fixture que
      deriva a URL de manutenção da `DATABASE_URL` trocando o nome do banco por `postgres`, cria um
      banco vazio de nome único por execução, entrega a URL dele e o remove ao fim, inclusive quando
      o teste falha
- [X] T011 Implementar o extrator em `testes/suporte/inventario.py` conforme
      [contracts/inventario-de-esquema.md](./contracts/inventario-de-esquema.md), incluindo o corpo
      completo de funções e visões e a trigger decomposta em momento, evento, orientação, `WHEN` e
      função chamada, excluindo `alembic_version`, até T009 passar
- [X] T012 Implementar em `testes/suporte/inventario.py` a comparação que nomeia o que falta e o
      que sobra por categoria — uma mensagem que só diz "os esquemas diferem" não permite corrigir

**Checkpoint**: ferramentas de verificação prontas e confiáveis. As histórias podem começar.

---

## Phase 3: User Story 1 - Levantar um ambiente do zero (Priority: P1) 🎯 MVP

**Goal**: Um banco vazio chega ao esquema completo com uma operação, de forma atômica e
repetível.

**Independent Test**: apontar para um banco vazio, aplicar a migração e verificar que as
estruturas do documento de referência passam a existir.

### Tests for User Story 1 ⚠️

> Escrever primeiro. Rodar. Ver falhar — neste momento não existe nenhuma revisão, então a falha
> esperada é o esquema não ser criado.

- [X] T013 [P] [US1] Teste de aplicação em banco vazio em
      `testes/integracao/test_aplicacao_da_migracao.py`: sobre banco descartável, `upgrade head`
      termina sem erro e as tabelas passam a existir (FR-001, SC-001)
- [X] T014 [P] [US1] Teste de reaplicação em `testes/integracao/test_aplicacao_da_migracao.py`:
      aplicar duas vezes seguidas não altera nada nem reporta erro (FR-009, SC-004)
- [X] T015 [P] [US1] Teste de atomicidade em `testes/integracao/test_aplicacao_da_migracao.py`:
      aplicar sobre banco descartável uma cópia do SQL com uma instrução inválida acrescentada ao
      final e verificar que nenhuma tabela sobrou — a falha vem do próprio banco, sem simulação
      (FR-010)
- [X] T016 [P] [US1] Teste da guarda de versão em
      `testes/unitarios/test_guarda_de_versao.py`, sobre a **função pura** que recebe o número de
      versão do servidor e decide: `150004` aborta com mensagem que nomeia a versão encontrada e a
      exigida, `160000` em diante segue. Testar sem servidor antigo real, que o projeto não
      provisiona nem deve provisionar só para isto (FR-020)
- [X] T017 [P] [US1] Teste de presença de estruturas em
      `testes/integracao/test_conformidade_do_esquema.py`: nenhuma estrutura do documento falta no
      banco migrado (FR-017, SC-002)

### Implementation for User Story 1

- [X] T018 [US1] Congelar o SQL em `alembic/versions/sql/0001_esquema_inicial.sql` como cópia byte
      a byte de `docs/04-schema.sql` já corrigido por T004 e T005 (FR-016)
- [X] T019 [US1] Criar a revisão `alembic/versions/0001_esquema_inicial.py`, cuja `upgrade()` lê o
      arquivo companheiro e o executa por `op.get_bind().exec_driver_sql()`, sem passar parâmetros —
      a função `fn_valida_transicao_reserva` contém `%` na mensagem de exceção
      ([research.md](./research.md) seção 4). `downgrade()` levanta erro explícito de não suportado
      (FR-002 a FR-007, FR-022)
- [X] T020 [US1] Implementar a guarda de versão em `app/comum/versao_do_banco.py` como função pura
      que recebe o número de versão e levanta erro explícito abaixo de 160000, e chamá-la de
      `alembic/env.py` antes de `run_migrations()`, com a leitura de
      `current_setting('server_version_num')`, até T016 passar (FR-020)
- [X] T021 [US1] Rodar T013 a T017 e confirmar verde; registrar em
      [research.md](./research.md) qualquer divergência nova entre documento e comportamento real
      que apareça agora, e corrigi-la no documento (FR-015)

**Checkpoint**: um banco vazio chega ao esquema atual com um comando. A US1 está entregue.

---

## Phase 4: User Story 2 - O banco recusa dado inválido por conta própria (Priority: P1)

**Goal**: Domínio de valor, ciclo de vida e unicidade impostos pelo banco, não pela aplicação.

**Independent Test**: tentar gravar valores inválidos direto no banco migrado e verificar que
cada tentativa é recusada.

**Nota sobre a ordem**: as garantias já nascem com a migração da US1. Para que estes testes não
passem de primeira sem provar nada, cada um roda antes contra um banco descartável **sem**
migração, onde precisa falhar.

### Tests for User Story 2 ⚠️

- [X] T022 [P] [US2] Teste de domínio de valor em
      `testes/integracao/test_garantias_do_banco.py`: gravar `perfil` fora de
      (`recepcao`, `staff`, `gestor`) em `usuario` é recusado pelo banco (FR-012)
- [X] T023 [P] [US2] Teste de transição inválida em
      `testes/integracao/test_garantias_do_banco.py`: `aguardando_cadastro` → `hospedado`,
      `encerrado` → `hospedado` e `hospedado` → `cancelada` são recusadas pela trigger (FR-013,
      grafo em [data-model.md](./data-model.md))
- [X] T024 [P] [US2] Teste de transição válida em
      `testes/integracao/test_garantias_do_banco.py`: `aguardando_cadastro` → `ficha_recebida`,
      `ficha_recebida` → `hospedado` e `hospedado` → `encerrado` são aceitas — a trigger protege sem
      travar o caminho normal
- [X] T025 [P] [US2] Teste de idempotência em `testes/integracao/test_garantias_do_banco.py`:
      inserir o mesmo `id_externo` em `evento_webhook` duas vezes é recusado na segunda (FR-014)
- [X] T026 [US2] Executar T022 a T025 contra um banco descartável sem migração e confirmar que
      todos falham; só então aceitá-los como verdes contra o banco migrado (SC-003)

### Implementation for User Story 2

Nenhuma linha de código de produção nova: as garantias vêm do esquema aplicado pela US1. Se algum
teste revelar que a garantia documentada não é a que o banco impõe, a correção é no documento e na
cópia congelada, na mesma entrega (FR-015).

- [X] T027 [US2] Corrigir `docs/04-schema.sql` e `alembic/versions/sql/0001_esquema_inicial.sql`
      caso T022 a T025 revelem divergência entre a garantia documentada e a imposta, mantendo as
      duas cópias idênticas. Editar a cópia congelada só é legítimo aqui, dentro desta entrega,
      enquanto a revisão inicial não foi aplicada em nenhum ambiente durável; a partir da T031 ela
      é imutável e correção vira revisão nova

**Checkpoint**: as três garantias do Artigo IX estão provadas contra banco real.

---

## Phase 5: User Story 3 - Evoluir o esquema em ordem (Priority: P2)

**Goal**: O banco sabe em que versão está, e o documento não pode divergir do esquema aplicado
em nenhuma migração futura.

**Independent Test**: consultar a versão registrada antes e depois de aplicar; introduzir uma
divergência deliberada e verificar que a verificação a aponta.

### Tests for User Story 3 ⚠️

- [X] T028 [P] [US3] Teste de versionamento em
      `testes/integracao/test_aplicacao_da_migracao.py`: em banco migrado, a revisão corrente é
      identificável, e em banco vazio não há versão registrada (FR-008)
- [X] T029 [P] [US3] Teste de conformidade em
      `testes/integracao/test_conformidade_do_esquema.py`: partindo de banco limpo, aplicar todas as
      migrações, extrair o inventário e compará-lo nos dois sentidos com o inventário do banco que
      recebeu `docs/04-schema.sql` (FR-018, SC-005)
- [X] T030 [US3] Teste de proteção das migrações futuras em
      `testes/integracao/test_conformidade_do_esquema.py`: com uma alteração aplicada ao documento e
      ausente das migrações, a verificação falha nomeando a divergência — inclusive quando a
      alteração é apenas no corpo de `fn_valida_transicao_reserva`

### Implementation for User Story 3

- [X] T031 [US3] Registrar em `alembic/README` o procedimento para migrações futuras: escrever a
      nova revisão, atualizar `docs/04-schema.sql` para refletir o esquema completo resultante e
      nunca editar `alembic/versions/sql/0001_esquema_inicial.sql`, que é retrato congelado
- [X] T032 [US3] Rodar T028 a T030 e confirmar verde

**Checkpoint**: a conformidade entre documento e banco deixa de depender de vigilância humana.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T033 Executar o [quickstart.md](./quickstart.md) inteiro, do Cenário 0 ao final, partindo de
      `docker compose down -v`, e corrigir qualquer passo que não confira
- [X] T034 Executar a verificação completa com `EXIGIR_POSTGRES=1` e confirmar suíte verde sem
      nenhum teste pulado
- [X] T035 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md` com a conclusão da fatia F0.2 e as
      correções feitas no documento de referência
- [X] T036 [P] Marcar a fatia F0.2 como concluída em `docs/backlog.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Fase 1)**: sem dependências
- **Foundational (Fase 2)**: depende do Setup e **bloqueia todas as histórias**
- **US1 (Fase 3)**: depende da Fase 2. É o MVP
- **US2 (Fase 4)**: depende da US1, porque as garantias vêm do esquema que a US1 aplica
- **US3 (Fase 5)**: depende da US1; independe da US2
- **Polish (Fase 6)**: depende de tudo

### Dependências internas relevantes

- T018 depende de T004 e T005 — congelar antes de corrigir grava o erro para sempre
- T019 depende de T018
- T013, T014, T015 e T017 dependem de T010, que fornece o banco descartável
- T016 **não** depende de T010: é teste de unidade sobre função pura, e roda sem banco
- T017, T029 e T030 dependem de T011 e T012, que fornecem o inventário e a comparação
- T026 depende de T022 a T025 e é o que dá validade a todas elas
- T008 depende de T006 e T007; T020 depende de T016

### Ordem dentro de cada história

Testes escritos e vistos falhando antes da implementação, sem exceção. Nesta fatia, "ver falhar"
para as garantias significa rodar contra banco sem migração (T026).

### Parallel Opportunities

- T002 e T003 em paralelo no Setup
- T006 e T009 em paralelo na Fase 2, por serem arquivos distintos
- T013 a T017 em paralelo entre si: escrevem casos distintos e não dependem umas das outras
- T022 a T025 em paralelo entre si
- T035 e T036 em paralelo no Polish
- T004 e T005 **não** são paralelas: mesmo arquivo

---

## Parallel Example: User Story 1

```bash
# Escrever os testes da US1 juntos, antes de qualquer implementação:
Task: "Teste de aplicação em banco vazio em testes/integracao/test_aplicacao_da_migracao.py"
Task: "Teste de reaplicação em testes/integracao/test_aplicacao_da_migracao.py"
Task: "Teste de atomicidade em testes/integracao/test_aplicacao_da_migracao.py"
Task: "Teste da guarda de versão em testes/unitarios/test_guarda_de_versao.py"
Task: "Teste de presença de estruturas em testes/integracao/test_conformidade_do_esquema.py"
```

---

## Implementation Strategy

### MVP primeiro (apenas US1)

1. Fase 1: Setup
2. Fase 2: Foundational — bloqueia tudo, e é onde o documento é corrigido antes de ser congelado
3. Fase 3: US1
4. **PARAR E VALIDAR**: um banco vazio chega ao esquema atual com um comando, de forma atômica e
   repetível. É o que desbloqueia toda a Fase 1 do backlog
5. Seguir para US2 e US3

### Entrega incremental

1. Setup e Foundational → ferramentas de verificação confiáveis
2. US1 → o esquema existe e é reproduzível (MVP)
3. US2 → as garantias do Artigo IX estão provadas
4. US3 → a conformidade passa a se sustentar sozinha ao longo do tempo

### Estratégia com um só desenvolvedor

O projeto tem um desenvolvedor: as marcações [P] indicam ausência de dependência, e servem para
escolher a próxima tarefa sem esperar, não para trabalho simultâneo. A ordem numérica é uma
sequência válida do começo ao fim.

---

## O que a execução revelou

Registrado aqui porque contradiz o que o plano supunha, e a próxima pessoa precisa saber:

- **`exec_driver_sql` não serve para aplicar o script.** O SQLAlchemy 2.0 encaminha um dicionário
  vazio de parâmetros, o psycopg2 tenta interpolar o `%` da mensagem de `RAISE EXCEPTION` e a
  execução falha. A forma que funciona é o cursor cru do driver, sem coleção alguma de parâmetros.
  Corrigido no [research.md](./research.md) seção 4.
- **A guarda de versão precisa de conexão própria.** Consultar a versão pela conexão da migração
  abre a transação antes do Alembic, e nesse caso ele deixa de comitar por conta própria: o esquema
  era criado e desfeito no fechamento da conexão, com o log ainda dizendo que a migração rodou.
- **`str()` de uma URL do SQLAlchemy substitui a senha por asteriscos.** Custou uma falha de
  autenticação difícil de ler; o correto é `render_as_string(hide_password=False)`.
- **Foi preciso um módulo de apoio não previsto**, `testes/suporte/migracao.py`, para aplicar
  migrações a partir dos testes e ler o estado de versionamento.
- **T027 não gerou correção**: nenhuma garantia divergiu do que o documento declarava.
- **Um contêiner órfão de nome `omnistay-db`** impediu o `docker compose up` após o `down -v`, e
  teve de ser removido com `docker rm -f`. Vale saber antes de concluir que o ambiente não sobe.

## Notes

- Commit após cada tarefa ou grupo lógico, com mensagem descritiva
- Conteúdo de mensagem nunca vai para log, inclusive em teste
- `id_hotel` está presente nas tabelas de domínio desde a criação
- Nenhuma dependência nova entra no projeto nesta fatia
