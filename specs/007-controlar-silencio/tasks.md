---
description: "Task list for feature implementation"
---

# Tasks: Controlar o Silêncio

**Input**: Design documents from `/specs/007-controlar-silencio/`

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

**DDL / visão / parâmetros.** Atualizar `docs/04-schema.sql` **antes** de criar a revisão
`0007` deixa o teste de conformidade da F0.2 vermelho. A revisão o devolve ao verde. Ordem
inversa passa de primeira sem provar nada.

**Texto, verificador, porta.** Unitários com relógio/repositório/porta falsos falham por
`ImportError` / `AttributeError` / `NotImplementedError` até existir a implementação.

**Lembrete ponta a ponta.** Integração prova: `--verificar-cadastros` (ou a função) grava
mensagem + trabalho **sem** chamar a mensageria; só `--uma-passagem` envia; segunda
verificação não duplica.

---

## Phase 1: Setup

**Purpose**: Pacotes de teste e módulo de agendador que o plano prevê e ainda não existem

- [X] T001 [P] Criar pacote `testes/unitarios/worker/` (`__init__.py`) para
      `test_verificar_cadastros.py` e `test_cli_worker.py`
- [X] T002 [P] Criar `worker/agendador.py` com docstring e função nomeada
      `verificar_cadastros_pendentes` levantando `NotImplementedError` até as histórias

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: DDL do tipo `enviar_lembrete` + `estado_cadastro` + backfill dos prazos, porta
`enviar_lembrete`, fila, esqueletos de conversa/hospedagem/agendador/CLI e `enviada_em` no
sucesso — tudo o que as histórias usam e nenhuma deve reinventar

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. T008–T009 dependem de T006→T008→T009
na ordem documento → falha → congelar → migração.

- [X] T003 [P] Acrescentar `enviar_lembrete` ao Protocol em `app/portas/mensageria.py`
      (mesma forma de `enviar_coleta`) conforme
      [contracts/mensageria-e-fila.md](./contracts/mensageria-e-fila.md)
- [X] T004 [P] Implementar `enviar_lembrete` em `app/adaptadores/mensageria_falsa.py`
      (registrar `tipo=lembrete`; reusar falha determinística; **nunca** abre rede)
- [X] T005 Estender `testes/unitarios/adaptadores/test_mensageria_falsa.py`: sucesso de
      lembrete distinguível da coleta; modo falha levanta erro tipado. Rodar e ver falhar
      até T004; depois verde
- [X] T006 Ampliar `docs/04-schema.sql`: `ck_trabalho_tipo` com `enviar_lembrete`; índice
      único parcial `uq_trabalho_enviar_lembrete_reserva`; ramo
      `estado_cadastro = sem_cadastro_previo`; comentário de `mensagem.enviada_em` (sucesso
      do envio) — exatamente [data-model.md](./data-model.md). Rodar a suíte e **ver o teste
      de conformidade da F0.2 ficar vermelho**
- [X] T007 [P] Alinhar narrativa em `docs/04-modelagem-de-dados.md` (lembrete único,
      `reenvio_realizado`, `sem_cadastro_previo`, os dois prazos) conforme research §5–§7 e
      §9
- [X] T008 Congelar o SQL em `alembic/versions/sql/0007_controlar_silencio.sql`, idêntico ao
      bloco alterado do documento **e** com `INSERT` das chaves `horas_ate_reenvio=24` e
      `horas_corte_antes_checkin=12` para todo `hotel` que ainda não as tenha
- [X] T009 Criar a revisão `alembic/versions/0007_controlar_silencio.py` com
      `down_revision = "0006_interpretar_ficha"`, executando o SQL congelado; `downgrade`
      restaura `CHECK`/visão anteriores (sem apagar parâmetros já semeados, ou documentar o
      recuo). Rodar até conformidade verde
- [X] T010 [P] Ampliar `app/fila/repository.py` + `app/fila/service.py` com
      `TIPO_ENVIAR_LEMBRETE` / `enfileirar_enviar_lembrete` (payload só `id_reserva`,
      `id_mensagem`) conforme [contracts/mensageria-e-fila.md](./contracts/mensageria-e-fila.md)
- [X] T011 [P] Criar `app/modulos/conversa/texto_lembrete.py` (função pura
      `montar_texto_lembrete`; reusar `primeiro_nome` de `texto_coleta.py`)
- [X] T012 [P] Ampliar `app/modulos/conversa/repository.py` + `service.py` com funções
      nomeadas: instante da coleta `enviada`, existe mensagem `recebida`,
      `agendar_lembrete`, atualizar `enviada_em` no sucesso de envio —
      `NotImplementedError` onde a história ainda não chegou; **não** importar
      `hospedagem`
- [X] T013 [P] Ampliar `app/modulos/hospedagem/repository.py` + `service.py` com
      `listar_reservas_aguardando_cadastro` (sempre `id_hotel`),
      `marcar_reenvio_realizado`, `marcar_sem_cadastro_previo` — esqueleto até US1/US2
- [X] T014 Semeiar `horas_ate_reenvio=24` e `horas_corte_antes_checkin=12` no bootstrap em
      `app/modulos/propriedade/service.py` (ausência da chave **não** vira default no
      verificador)
- [X] T015 Acrescentar `enviar_lembrete` em `app/adaptadores/mensageria_whatsapp.py` (mesmo
      padrão de `enviar_coleta`; suíte **não** instancia)
- [X] T016 Completar esqueleto de `worker/agendador.py`: assinatura
      `verificar_cadastros_pendentes(conexao, *, agora=relogio.agora)` orquestrando
      hospedagem + conversa + propriedade; **sem** ciclo `conversa` → `hospedagem`
- [X] T017 Ampliar `worker/consumidor.py` para despachar `enviar_lembrete` via
      `conversa` + `MensageriaGateway.enviar_lembrete` (backoff igual à coleta)
- [X] T018 Acrescentar `--verificar-cadastros` em `worker/__main__.py`; `--uma-passagem`
      continua **sem** chamar o agendador; modo contínuo chama o agendador na cadência
      (~1 h, injetável) após passagens da fila

**Checkpoint**: DDL/visão/prazos no documento e no banco; porta falsa de lembrete;
agendador e worker reconhecem o tipo; `--uma-passagem` intacto. Histórias podem começar.

---

## Phase 3: User Story 1 - Um único lembrete quando o hóspede não responde (Priority: P1) 🎯 MVP

**Goal**: Silêncio após `horas_ate_reenvio` desde a coleta **enviada** → exatamente uma
mensagem de lembrete (opcionalidade + preenchimento na recepção; só o primeiro nome);
segunda verificação não duplica; envio pela porta, não na verificação.

**Independent Test**: Reserva `aguardando_cadastro`, coleta `enviada`, check-in longe o
bastante para ficar fora da corte, relógio ≥ prazo, sem mensagem recebida → 1 lembrete no
histórico e 1 envio na porta falsa após uma passagem do worker; verificar de novo → 0
extras; `reenvio_realizado = true`; status ainda `aguardando_cadastro`.

### Tests for User Story 1 ⚠️

> Escrever primeiro; rodar; ver falhar pelo motivo certo antes de implementar.

- [X] T019 [P] [US1] Unitários de texto em
      `testes/unitarios/modulos/conversa/test_texto_lembrete.py`: opcionalidade, recepção,
      só primeiro nome; sem lista numerada, telefone, documento, endereço
- [X] T020 [P] [US1] Unitários do verificador em
      `testes/unitarios/worker/test_verificar_cadastros.py`: após o prazo agenda um
      lembrete; segunda chamada não agenda outro; silêncio menor que o prazo não agenda;
      coleta ainda não `enviada` não agenda
- [X] T021 [P] [US1] Unitários de `agendar_lembrete` / `enviada_em` em
      `testes/unitarios/modulos/conversa/test_service_coleta.py` (ou arquivo irmão
      `test_agendar_lembrete.py`): mensagem pendente + trabalho; sucesso de envio grava
      `enviada_em`
- [X] T022 [US1] Integração em `testes/integracao/test_controlar_silencio.py`: relógio
      avançado → `--verificar-cadastros` (ou função) cria mensagem+trabalho sem chamar a
      porta; `--uma-passagem` envia um lembrete; segunda verificação não duplica

### Implementation for User Story 1

- [X] T023 [US1] Implementar `montar_texto_lembrete` em
      `app/modulos/conversa/texto_lembrete.py` até T019 verde
- [X] T024 [US1] Implementar predicado de coleta enviada, `agendar_lembrete` (mensagem +
      `enfileirar_enviar_lembrete` + `marcar_reenvio_realizado` na mesma TX) e
      `enviada_em` no sucesso em `app/modulos/conversa/` + `app/modulos/hospedagem/` até
      T021 verde
- [X] T025 [US1] Implementar no agendador as regras 3–5 de
      [contracts/agendador-e-prazos.md](./contracts/agendador-e-prazos.md) (fora da corte;
      check-in futuro) até T020 verde
- [X] T026 [US1] Completar consumo `enviar_lembrete` em `worker/consumidor.py` +
      `processar_trabalho` em `app/modulos/conversa/service.py` (retry não cria segunda
      mensagem)
- [X] T027 [US1] Fechar integração T022 verde; `reenvio_realizado=true`; status permanece
      `aguardando_cadastro`

**Checkpoint**: US1 entregável sozinha — um lembrete, nunca dois, com porta falsa.

---

## Phase 4: User Story 2 - Silêncio persistente visível na fila, sem bloquear a chegada (Priority: P1)

**Goal**: Janela de corte (ou data de entrada já passada) sem resposta →
`sem_cadastro_previo` na reserva e na fila; zero mensagem nova cobrando cadastro; transição
para `hospedado` continua permitida no banco.

**Independent Test**: Reserva silenciosa (com ou sem lembrete já feito), relógio na corte
→ `GET /fila-do-dia` com `estado_cadastro=sem_cadastro_previo`; `UPDATE` de teste para
`hospedado` aceito pela trigger.

### Tests for User Story 2 ⚠️

- [X] T028 [P] [US2] Unitário em
      `testes/unitarios/modulos/hospedagem/test_marcar_sem_cadastro.py`: só a partir de
      `aguardando_cadastro`; não cancela; `id_hotel` na atualização
- [X] T029 [P] [US2] Unitário em `testes/unitarios/worker/test_verificar_cadastros.py`:
      corte atingido marca e **não** agenda lembrete; data de entrada vencida idem;
      reserva já na corte na criação não lembra
- [X] T030 [P] [US2] Integração em `testes/integracao/test_fila_do_dia.py`: item com
      `status`/`estado_cadastro = sem_cadastro_previo` distinguível de `aguardando`,
      `completa`, `parcial`, `leitura_humana`
- [X] T031 [US2] Integração em `testes/integracao/test_controlar_silencio.py` (ou
      `test_garantias_do_banco.py`): corte → status + fila; zero mensagem de cobrança
      nova; `aguardando_cadastro|sem_cadastro_previo` → `hospedado` aceito

### Implementation for User Story 2

- [X] T032 [US2] Implementar `marcar_sem_cadastro_previo` em `app/modulos/hospedagem/` até
      T028 verde
- [X] T033 [US2] Implementar regras 2 (corte / data vencida) no agendador
      `worker/agendador.py` até T029 verde — corte **antes** do lembrete
- [X] T034 [US2] Confirmar ramo da visão já migrado em T006 e o mapeamento em
      `app/modulos/hospedagem/schema.py` / leitura da fila; T030/T031 verdes

**Checkpoint**: US1 e US2 independentes; silêncio visível; check-in não bloqueado.

---

## Phase 5: User Story 3 - Resposta no meio do caminho cancela o lembrete (Priority: P1)

**Goal**: Qualquer mensagem `recebida` cancela lembrete ainda não enviado e impede
`sem_cadastro_previo`. Ficha completa/parcial não é sobrescrita quando os prazos vencem.
Irreconhecível conta como resposta.

**Independent Test**: (a) resposta antes do primeiro prazo → 0 lembretes; (b) resposta após
o lembrete, antes da corte → status o da F1.3, não `sem_cadastro_previo`.

### Tests for User Story 3 ⚠️

- [X] T035 [P] [US3] Unitário em `testes/unitarios/worker/test_verificar_cadastros.py`:
      há `recebida` → não agenda, não marca; `ficha_recebida`/`ficha_parcial` fora da
      listagem de candidatos
- [X] T036 [US3] Integração em `testes/integracao/test_controlar_silencio.py`: webhook
      (qualquer desfecho F1.3) antes do prazo → 0 `enviar_lembrete`; após lembrete +
      resposta + corte → não transiciona para `sem_cadastro_previo`

### Implementation for User Story 3

- [X] T037 [US3] Implementar predicado `tem_mensagem_recebida` em
      `app/modulos/conversa/repository.py` e regra 1 do agendador até T035 verde
- [X] T038 [US3] Garantir `listar_reservas_aguardando_cadastro` só retorna
      `aguardando_cadastro` (completa/parcial/hospedado/cancelada fora); fechar T036 verde

**Checkpoint**: Resposta (inclusive irreconhecível) encerra o ciclo de silêncio.

---

## Phase 6: User Story 4 - Prazos da propriedade, não do produto (Priority: P2)

**Goal**: Ritmo do lembrete e da marcação segue `horas_ate_reenvio` e
`horas_corte_antes_checkin` daquele hotel. Chave ausente ou inválida: nenhum efeito, log
explícito, **sem** 24/12 no verificador.

**Independent Test**: Mesmo hotel, valor A → silêncio menor que A não lembra; valor B →
lembra em B. Hotel sem chave: 0 lembretes e 0 marcações.

### Tests for User Story 4 ⚠️

- [X] T039 [P] [US4] Estender `testes/unitarios/modulos/propriedade/test_bootstrap.py` e
      `testes/integracao/test_bootstrap.py`: instalação nova grava as duas chaves 24 e 12
- [X] T040 [P] [US4] Unitários em
      `testes/unitarios/modulos/propriedade/test_prazos_de_silencio.py` (e/ou
      `test_verificar_cadastros.py`): prazo A vs B muda o instante; chave ausente/inválida
      não dispara e não usa constante de código
- [X] T041 [US4] Integração em `testes/integracao/test_controlar_silencio.py`: alterar o
      parâmetro do hotel muda o momento do lembrete/marcação na verificação seguinte

### Implementation for User Story 4

- [X] T042 [US4] Fechar bootstrap T014/T039 se ainda faltar cobertura de integração
- [X] T043 [US4] Leitura dos prazos no agendador via
      `app/modulos/propriedade/repository.py` (`ler_parametro` + `id_hotel`); pular hotel
      com log `prazo_ausente`/`prazo_invalido`; T040/T041 verdes

**Checkpoint**: Artigo XIII cumprido; dois hotéis (ou dois valores) não compartilham ritmo
embutido.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edges da spec, logs, documentação de estado, fronteiras e roteiro do quickstart

- [X] T044 [P] Estender `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py` (e
      logs do agendador/worker): verificação, agendamento e envio do lembrete sem corpo,
      telefone ou nome
- [X] T045 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md` (F1.4; prazos semeados; APScheduler
      adiado de novo em favor de `worker/agendador.py`; `enviada_em` no sucesso)
- [X] T046 Edge integração: coleta `pendente`/`falha` não gera lembrete; corte ainda pode
      marcar — em `testes/integracao/test_controlar_silencio.py`
- [X] T047 Edge: falha transitória de `enviar_lembrete` reusa o mesmo trabalho/mensagem
      (estender `testes/integracao/test_worker_coleta.py` ou o teste da fatia)
- [X] T048 [P] Unitário em `testes/unitarios/worker/test_cli_worker.py`: `--uma-passagem`
      não chama `verificar_cadastros_pendentes`; `--verificar-cadastros` chama
- [X] T049 Revisar fronteiras de import: `conversa` não importa `hospedagem`; agendador no
      worker orquestra
- [X] T050 Rodar o roteiro de [quickstart.md](./quickstart.md) (ou equivalente
      automatizado) e `pytest testes/unitarios -q` + integrações da fatia; tudo verde sem
      rede Meta

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: após Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: após Foundational — MVP
- **US2 (Phase 4)**: após Foundational; na prática reusa o agendador da US1 (ramo de corte)
- **US3 (Phase 5)**: após Foundational; reusa o mesmo verificador (predicado de resposta)
- **US4 (Phase 6)**: após pelo menos US1 (precisa haver caminho que lê prazo)
- **Polish (Phase 7)**: após as histórias desejadas

### User Story Dependencies

- **US1**: só Foundational — MVP isolado (use check-in futuro para não entrar na corte)
- **US2**: logicamente independente no aceite; implementação acrescenta o ramo de corte
- **US3**: independente no aceite; compartilha listagem + predicado de `mensagem`
- **US4**: transversal; validar sobre US1 (e idealmente US2)

### Within Each User Story

1. Testes escritos e vermelhos
2. Implementação mínima
3. Verde
4. Só então próxima história

### Parallel Opportunities

- T001–T002 em paralelo
- T003–T005, T007, T010–T015 em paralelo após o desenho; T006→T008→T009 sequenciais com o
  teste de conformidade
- T019–T021 em paralelo dentro da US1
- T028–T030 em paralelo na US2
- T035 em paralelo com a preparação da T036 na US3
- T039–T040 em paralelo na US4
- T044–T045 e T048 em paralelo no polish

---

## Parallel Example: User Story 1

```text
# Testes em paralelo (antes da implementação):
T019 test_texto_lembrete.py
T020 test_verificar_cadastros.py (caminho lembrete único)
T021 test_agendar_lembrete.py / enviada_em

# Depois, implementação na ordem:
T023 → T024 → T025 → T026 → T027 (T022)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: validar quickstart cenário 1
4. Demo: relógio avançado → um lembrete, nunca dois

### Incremental Delivery

1. US1 → lembrete único
2. US2 → `sem_cadastro_previo` na fila
3. US3 → resposta cancela o ciclo
4. US4 → prazos por propriedade
5. Polish → estado do projeto + edges + quickstart

### Suggested MVP scope

**Só US1** (T001–T027): prova o valor principal (não ser intrusivo com um único reenvio).
US2 e US3 são aceites obrigatórios da spec antes de marcar F1.4 concluída no backlog —
completar na mesma entrega; não abrir F2.1 sem US2/US3.

---

## Notes

- [P] = arquivos distintos, sem depender de tarefa incompleta da mesma sequência
- Worker/agendador orquestra; **proibido** `conversa` importar `hospedagem`
- `--uma-passagem` não dispara verificação (não quebrar F1.2/F1.3)
- Sem APScheduler; sem tela de parâmetros; sem clique de check-in
- Commit por tarefa ou grupo lógico (só se o usuário pedir commit)
- Evitar: segundo lembrete; número mágico no verificador; lembrar coleta não enviada;
  marcar quem já respondeu
