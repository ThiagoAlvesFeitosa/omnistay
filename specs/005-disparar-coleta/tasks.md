---
description: "Task list for feature implementation"
---

# Tasks: Disparar Coleta de Dados

**Input**: Design documents from `/specs/005-disparar-coleta/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhum código de produção sem
teste que falhe antes pelo motivo certo.

**Organization**: Tarefas agrupadas por história de usuário (US1–US4), na ordem de prioridade
da spec.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US4)

## Como ver os testes falharem nesta fatia

**Tabela `trabalho` e visão ampliada.** O teste de conformidade da F0.2 é o "ver falhar" da
migração: atualizar `docs/04-schema.sql` **antes** de criar a revisão `0005` deixa a suíte
vermelha (banco migrado diverge do documento). A revisão a devolve ao verde. Ordem inversa
passa de primeira sem provar nada.

**Texto da coleta, fila e porta.** Funções puras e serviços com repositório/porta falsos:
unitário falha por `ImportError` / `AttributeError` até existir a implementação.

**Independência estrutural.** Integração prova que `POST /reservas` cria `mensagem` +
`trabalho` **sem** chamar a mensageria; só o worker (uma passagem) muda `status_envio`.

---

## Phase 1: Setup

**Purpose**: Pacotes previstos no plano que ainda não existem no repositório

- [X] T001 [P] Criar pacotes vazios `app/portas/__init__.py`, `app/adaptadores/__init__.py`,
      `app/fila/__init__.py`, `app/modulos/conversa/__init__.py`, `worker/__init__.py`
- [X] T002 [P] Criar pacotes de teste `testes/unitarios/fila/__init__.py`,
      `testes/unitarios/modulos/conversa/__init__.py`,
      `testes/unitarios/adaptadores/__init__.py` (ou equivalente alinhado à árvore do
      [plan.md](./plan.md))

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: DDL da fila, visão com status de coleta, porta de mensageria, esqueletos de
`fila`/`conversa`/worker e parâmetros de bootstrap — tudo o que as histórias usam e nenhuma
deve reinventar

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. T010/T011 dependem de T007→T009 na
ordem documento → falha → congelar → migração.

- [X] T003 [P] Definir o Protocol `MensageriaGateway` em `app/portas/mensageria.py` conforme
      [contracts/mensageria-e-fila.md](./contracts/mensageria-e-fila.md) (assinatura de envio de
      coleta + resultado sucesso/falha tipado, sem importar adaptador concreto)
- [X] T004 [P] Implementar `app/adaptadores/mensageria_falsa.py`: registra envios em memória;
      permite configurar falha determinística; **nunca** abre rede
- [X] T005 Escrever testes da porta falsa em
      `testes/unitarios/adaptadores/test_mensageria_falsa.py` (sucesso registra um envio; modo
      falha levanta/devolver erro tipado). Rodar e ver falhar até T004 existir; depois verde
- [X] T006 Ampliar `docs/04-schema.sql` com a tabela `trabalho` (campos, `CHECK` de `status`/
      `tipo`, índice único parcial de `enviar_coleta` por `id_reserva` no payload, índices de
      claim) e com `status_envio_coleta` em `vw_fila_do_dia`, exatamente como em
      [data-model.md](./data-model.md). Rodar a suíte e **ver o teste de conformidade da F0.2
      ficar vermelho**
- [X] T007 [P] Documentar a fila de trabalho e o disparo pós-reserva em
      `docs/04-modelagem-de-dados.md` (pesquisa §2 e §10); mencionar chaves novas
      `contato_responsavel_dados` e `tentativas_max_envio_mensagem`
- [X] T008 Congelar o SQL em `alembic/versions/sql/0005_trabalho_e_coleta.sql`, idêntico ao
      bloco do documento (tabela + `DROP`/`CREATE` da visão + comentários)
- [X] T009 Criar a revisão `alembic/versions/0005_trabalho_e_coleta.py` com `down_revision =
      "0004_fila_sem_futuro"`, executando o SQL congelado; `downgrade` remove `trabalho` e
      recria a visão **anterior** (sem `status_envio_coleta`). Rodar até o teste de
      conformidade voltar ao verde
- [X] T010 [P] Criar esqueleto `app/fila/repository.py` + `app/fila/service.py` com funções
      nomeadas (enfileirar `enviar_coleta`, claim com `SKIP LOCKED`, concluir, reagendar,
      falhar definitivo, reclaim de `processando` expirado) levantando `NotImplementedError`
- [X] T011 [P] Criar esqueleto `app/modulos/conversa/texto_coleta.py`,
      `app/modulos/conversa/repository.py` e `app/modulos/conversa/service.py` (montar texto,
      inserir mensagem pendente, agendar coleta, atualizar `status_envio`) com
      `NotImplementedError` onde couber — só para fixar fronteiras
- [X] T012 [P] Acrescentar `status_envio_coleta` a `ItemFilaDoDia` em
      `app/modulos/hospedagem/schema.py` conforme
      [contracts/api-de-hospedagem.md](./contracts/api-de-hospedagem.md)
- [X] T013 Semear no bootstrap (`app/modulos/propriedade/service.py` / `app/bootstrap.py`) as
      chaves `contato_responsavel_dados` (default = telefone do hotel) e
      `tentativas_max_envio_mensagem` (`"5"`); garantir hotel já bootstrapado em teste de
      integração recebe as chaves (ajuste mínimo no ambiente de acesso se necessário)
- [X] T014 Criar `worker/consumidor.py` e `worker/__main__.py` com ponto de entrada
      `python -m worker` capaz de rodar **uma passagem** de consumo (loop contínuo pode
      existir, mas a suíte precisa de modo one-shot)

**Checkpoint**: DDL e visão no documento e no banco; porta falsa utilizável; esqueletos no
lugar; parâmetros no bootstrap. Histórias podem começar.

---

## Phase 3: User Story 1 - Disparar a coleta ao cadastrar a reserva (Priority: P1) 🎯 MVP

**Goal**: Cadastro bem-sucedido cria exatamente uma pendência de coleta; o worker, com porta
falsa em sucesso, entrega uma mensagem com lista numerada/opcionalidade; a fila do dia mostra
o status; a requisição HTTP não chama a mensageria.

**Independent Test**: `POST /reservas` → no banco 1 `mensagem` pendente + 1 `trabalho`
`enviar_coleta`; porta falsa ainda vazia; rodar uma passagem do worker → envio registrado,
`status_envio_coleta = enviada` no `GET /fila-do-dia`.

### Tests for User Story 1 ⚠️

> Escrever primeiro; rodar; ver falhar pelo motivo certo antes de implementar.

- [X] T015 [P] [US1] Escrever testes unitários de montagem do texto em
      `testes/unitarios/modulos/conversa/test_texto_coleta.py`: lista numerada dos nove
      campos; opcionalidade; finalidade; contato configurável; saudação só com primeiro nome
      (FR-007, FR-008, FR-009, FR-010 — núcleo necessário ao MVP; privacidade completa em US3)
- [X] T016 [P] [US1] Escrever testes unitários de agendamento em
      `testes/unitarios/modulos/conversa/test_service_coleta.py` com repos falsos: agenda
      cria mensagem `pendente` + enfileira `enviar_coleta` com `id_hotel`/`id_reserva`/
      `id_mensagem`; não chama `MensageriaGateway` (FR-001, FR-002)
- [X] T017 [P] [US1] Acrescentar em
      `testes/unitarios/modulos/hospedagem/test_service_de_reserva.py`: após criar reserva
      válida, o serviço de hospedagem dispara exatamente um agendamento de coleta (colaborador
      falso); validação falha → zero agendamentos (FR-001, FR-016)
- [X] T018 [US1] Escrever integração em `testes/integracao/test_disparo_coleta.py`: `POST
      /reservas` como recepção cria `mensagem` + `trabalho`; contagem de envios na porta falsa
      da API permanece 0 até o worker; `GET /fila-do-dia` traz `status_envio_coleta =
      pendente`. Rodar e ver falhar
- [X] T019 [US1] Escrever integração worker em `testes/integracao/test_worker_coleta.py`: após
      cadastro, uma passagem do consumidor com porta falsa em sucesso marca trabalho
      `concluido`, mensagem `enviada`, fila `status_envio_coleta = enviada`, exatamente um
      envio na falsa. Rodar e ver falhar

### Implementation for User Story 1

- [X] T020 [US1] Implementar `montar_texto_coleta` em `app/modulos/conversa/texto_coleta.py`
      até T015 passar
- [X] T021 [US1] Implementar repositório/serviço de conversa + enfileiramento em
      `app/modulos/conversa/repository.py`, `service.py` e `app/fila/repository.py` /
      `service.py` (insert mensagem + insert trabalho na conexão/transação recebida) até T016
      passar
- [X] T022 [US1] Ligar `criar_reserva` em `app/modulos/hospedagem/service.py` para agendar a
      coleta na **mesma** transação após os três inserts; garantir que o router/transação não
      chama a mensageria; atualizar leitura da fila em `repository.py` para devolver
      `status_envio_coleta` — até T017 e T018 passarem
- [X] T023 [US1] Implementar uma passagem do consumidor em `worker/consumidor.py` (claim →
      gateway → atualizar mensagem/trabalho via conversa/fila) injetando `MensageriaGateway`;
      composição usa a falsa nos testes — até T019 passar (FR-006, FR-012, FR-013, FR-014 no
      caminho feliz)

**Checkpoint**: MVP observável — cadastrar, ver pendente na fila, worker envia, status
`enviada`.

---

## Phase 4: User Story 2 - Reserva sobrevive a falha de envio (Priority: P1)

**Goal**: Falha na mensageria mantém a reserva; status visível; retry não cria segunda
mensagem nem segundo pedido ao hóspede; esgotadas as tentativas → `falha` definitiva.

**Independent Test**: Porta falsa em falha → reserva na fila com status de coleta
`pendente`/`falha`; após sucesso no retry, uma única mensagem e um único envio bem-sucedido.

### Tests for User Story 2 ⚠️

- [X] T024 [P] [US2] Escrever unitários de fila/worker em
      `testes/unitarios/fila/test_service_da_fila.py` e/ou
      `testes/unitarios/modulos/conversa/test_service_coleta.py`: falha incrementa tentativas e
      reagenda; no teto (`tentativas_max_envio_mensagem`) marca trabalho `falha` e mensagem
      `falha`; sucesso no retry atualiza a **mesma** `id_mensagem` (FR-003, FR-004, FR-005)
- [X] T025 [US2] Acrescentar em `testes/integracao/test_worker_coleta.py`: falha forçada não
      apaga reserva nem altera status de ciclo de vida; fila mostra estado de entrega; com
      max=1 fica `falha`; com falha-depois-sucesso, um único envio ok na falsa e uma única
      linha `mensagem` de coleta. Rodar e ver falhar
- [X] T026 [P] [US2] Acrescentar caso de unicidade: segundo enfileiramento `enviar_coleta` para
      a mesma reserva viola o único parcial (integração SQL ou unitário de repositório) —
      FR-001/FR-005 no banco (Artigo IX)

### Implementation for User Story 2

- [X] T027 [US2] Completar reagendar / falha definitiva / leitura do parâmetro
      `tentativas_max_envio_mensagem` em `app/fila/service.py` e no consumidor até T024 e T025
      passarem; `erro_ultima_tentativa` sem PII (FR-011)
- [X] T028 [US2] Implementar reclaim de `processando` expirado em `app/fila/repository.py` /
      `service.py` e exercitar no unitário (worker “morreu” no meio) — research §8
- [X] T029 [US2] Confirmar que T026 passa com o índice único da migração; ajustar payload/
      insert só se a restrição não estiver sendo atingida

**Checkpoint**: falha de rede não desfaz o trabalho da recepção; retry idempotente.

---

## Phase 5: User Story 3 - Histórico e privacidade da primeira mensagem (Priority: P1)

**Goal**: Mensagem de coleta no histórico da reserva; corpo só com primeiro nome como PII do
hóspede; logs sem conteúdo pessoal.

**Independent Test**: Após envio, existe `mensagem` de saída com status; unitário do texto
reprova se telefone/documento/endereço/sobrenome completo do titular vazarem no corpo; logs
de worker/serviço sem `conteudo`/telefone/nome.

### Tests for User Story 3 ⚠️

- [X] T030 [P] [US3] Ampliar `testes/unitarios/modulos/conversa/test_texto_coleta.py`: corpo
      não contém telefone canônico do hóspede, CPF/RG de exemplo, endereço, nem o sobrenome
      completo quando o nome tem dois tokens — só o primeiro nome na saudação (FR-010)
- [X] T031 [P] [US3] Teste unitário/integração leve de histórico: após agendar (e/ou após
      worker), repositório de conversa lista a mensagem de saída da reserva com
      `status_envio` atualizado (FR-006) — arquivo
      `testes/unitarios/modulos/conversa/test_historico_mensagem.py` ou extensão de
      `test_service_coleta.py`
- [X] T032 [US3] Teste de log em
      `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py` (ou no worker): ao processar
      sucesso/falha, a saída de log capturada não contém o texto da mensagem nem o telefone
      (FR-011). Rodar e ver falhar se ainda logar payload cru

### Implementation for User Story 3

- [X] T033 [US3] Ajustar `texto_coleta.py` até T030 passar (rótulos da lista ≠ dados preenchidos
      do titular)
- [X] T034 [US3] Expor leitura mínima de mensagens da reserva em
      `app/modulos/conversa/repository.py` / `service.py` para T031 (sem rota HTTP nova, se o
      plano mantiver histórico só no banco — o teste pode ler via repositório)
- [X] T035 [US3] Revisar logs em `worker/consumidor.py` e serviços de conversa/fila: só
      identificadores e códigos — até T032 passar

**Checkpoint**: telefone errado não vaza ficha; trilha auditável existe.

---

## Phase 6: User Story 4 - Transparência LGPD no primeiro contato (Priority: P2)

**Goal**: Texto declara finalidade e contato do responsável pelos dados **da propriedade**
(parâmetro do hotel), não genérico do produto.

**Independent Test**: Mensagem montada com `contato_responsavel_dados` do hotel A ≠ hotel B;
ambos trazem finalidade explícita de cadastro antecipado / evitar espera.

### Tests for User Story 4 ⚠️

- [X] T036 [P] [US4] Acrescentar em `test_texto_coleta.py`: finalidade explícita presente;
      contato injetado aparece literalmente; contato de outro hotel não aparece (FR-009,
      SC-006)
- [X] T037 [US4] Integração: bootstrap/ambiente com contato conhecido; após `POST` + worker,
      `mensagem.conteudo` no banco contém esse contato e a finalidade. Rodar e ver falhar se
      o agendamento não ler `parametro_hotel`

### Implementation for User Story 4

- [X] T038 [US4] Garantir que `conversa.service` lê `contato_responsavel_dados` por `id_hotel`
      ao montar o texto (via repositório de propriedade ou consulta pontual na mesma
      conexão) até T036 e T037 passarem; sem fallback para e-mail/marca OmniStay

**Checkpoint**: primeiro contato com transparência LGPD observável.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Adaptador real opcional, docs de estado, quickstart, varredura final

- [X] T039 [P] Implementar esqueleto `app/adaptadores/mensageria_whatsapp.py` (template Utility
      via `httpx`) selecionável por configuração de ambiente; **nenhum** teste automatizado o
      instancia (research §4 / SC-008)
- [X] T040 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F1.2 concluída (quando a suíte
      estiver verde), F1.3 como próxima; registrar decisões novas (tabela `trabalho`, módulo
      `conversa`, porta falsa)
- [X] T041 Rodar o roteiro de [quickstart.md](./quickstart.md) (ou equivalente automatizado) e
      corrigir lacunas de comando/`python -m worker` one-shot
- [X] T042 Rodar `pytest testes/unitarios -q` e `pytest testes/integracao -q`; garantir zero
      chamada de rede nos testes (grep/assert na falsa); commit único descritivo quando o
      usuário pedir

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências
- **Foundational (Phase 2)**: depende do Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: após Foundational — MVP
- **US2 (Phase 4)**: após US1 (reusa worker/fila; acrescenta falha/retry)
- **US3 (Phase 5)**: após US1 (texto/histórico); pode sobrepor US2 em arquivos de teste
      distintos
- **US4 (Phase 6)**: após US1 (parâmetro de contato no texto); idealmente após T013
- **Polish (Phase 7)**: após as histórias desejadas

### User Story Dependencies

- **US1**: base — enfileirar + enviar sucesso + status na fila
- **US2**: depende do caminho do worker da US1
- **US3**: depende da mensagem existir (US1); reforça privacidade/log
- **US4**: depende da montagem de texto (US1) + parâmetro (T013)

### Within Each User Story

- Testes primeiro → ver falhar → implementar o mínimo → verde
- Sem chamar a Meta em nenhum teste

### Parallel Opportunities

- T001 ∥ T002
- T003 ∥ T004 (depois T005)
- T007 ∥ preparação de esqueletos T010–T012 enquanto T006–T009 seguem a ordem do DDL
- T015 ∥ T016 ∥ T017 (testes US1)
- T024 ∥ T026 (testes US2)
- T030 ∥ T031 (testes US3)
- T039 ∥ T040 (polish)

---

## Parallel Example: User Story 1

```text
# Testes em paralelo (arquivos distintos):
T015 test_texto_coleta.py
T016 test_service_coleta.py
T017 test_service_de_reserva.py (extensão)

# Depois implementação sequencial na transação:
T020 texto → T021 conversa+fila → T022 hospedagem → T023 worker
```

---

## Parallel Example: User Story 2

```text
T024 unitários de retry/falha
T026 unicidade no banco
# Depois:
T027–T029 implementação e reclaim
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2  
2. Phase 3 (US1)  
3. **STOP**: validar quickstart cenários 1–2  
4. Só então US2 (falha) — sem isso o Artigo III/V fica incompleto na prática

### Incremental Delivery

1. Fundação (DDL + porta falsa)  
2. US1 — disparo feliz  
3. US2 — sobrevivência à falha (recomendado antes de demo)  
4. US3 — privacidade/log  
5. US4 — LGPD explícita (pode colapsar com T015 se já coberto; manter testes T036–T038)  
6. Polish  

### Suggested MVP scope

**US1 + fundação**, com US2 na mesma entrega se possível (critérios de aceite do backlog
incluem falha sem desfazer reserva). US3/US4 são baratas se o texto já nasceu certo na US1 —
ainda assim mantenha os testes explícitos.

---

## Notes

- [P] = arquivos distintos, sem dependência pendente
- Nenhuma tarefa de tela React ou webhook de entrada (F1.3+)
- `entregue` via webhook do provedor fica de fora (Artigo XV)
- Commit só quando o usuário pedir (regra do repositório)
