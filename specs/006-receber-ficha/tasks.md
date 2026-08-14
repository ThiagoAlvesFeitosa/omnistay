---
description: "Task list for feature implementation"
---

# Tasks: Receber e Interpretar a Ficha

**Input**: Design documents from `/specs/006-receber-ficha/`

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

**DDL / visão.** Atualizar `docs/04-schema.sql` **antes** de criar a revisão `0006` deixa o
teste de conformidade da F0.2 vermelho. A revisão o devolve ao verde. Ordem inversa passa de
primeira sem provar nada.

**Porta LLM, validação e consolidação.** Unitários com falsa/repositório falso falham por
`ImportError` / `AttributeError` / `NotImplementedError` até existir a implementação.

**Webhook + worker.** Integração prova: `POST /webhook` grava evento + mensagem + trabalho
**sem** chamar o LLM; só o worker (uma passagem) consolida e muda `estado_cadastro`.

---

## Phase 1: Setup

**Purpose**: Pacotes e stubs de teste que o plano prevê e ainda não existem

- [X] T001 [P] Criar `testes/unitarios/modulos/conversa/` stubs se faltarem e
      `testes/unitarios/adaptadores/` (já pode existir da F1.2); garantir
      `testes/integracao/` pronto para `test_webhook_coleta.py` /
      `test_interpretar_ficha.py`
- [X] T002 [P] Acrescentar chaves de configuração de webhook/LLM de teste em
      `app/config.py` e `.env.example` (`WHATSAPP_APP_SECRET`, `WHATSAPP_VERIFY_TOKEN`, e
      o que for mínimo para o hotel/WABA do MVP) — **sem valores secretos versionados**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: DDL do tipo `interpretar_ficha` + `estado_cadastro`, porta LLM + falsa,
esqueletos de recebimento/consolidação/worker e política de leitura — tudo o que as
histórias usam e nenhuma deve reinventar

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. T008–T010 dependem de T006→T007→T009
na ordem documento → falha → congelar → migração.

- [X] T003 [P] Definir o Protocol `LLMProvider` em `app/portas/llm.py` conforme
      [contracts/llm-e-fila.md](./contracts/llm-e-fila.md) (`extrair_ficha` +
      `ResultadoExtracao` sem campo idade; sinal de falha/indisponibilidade tipado)
- [X] T004 [P] Implementar `app/adaptadores/llm_falso.py`: desfechos configuráveis
      (completa / parcial / irreconhecivel / falha); **nunca** abre rede
- [X] T005 Escrever testes da porta falsa em
      `testes/unitarios/adaptadores/test_llm_falso.py`. Rodar e ver falhar até T004; depois
      verde
- [X] T006 Ampliar `docs/04-schema.sql`: `ck_trabalho_tipo` com `interpretar_ficha`; índice
      único parcial `uq_trabalho_interpretar_ficha_mensagem`; coluna/expressão
      `estado_cadastro` em `vw_fila_do_dia` — exatamente [data-model.md](./data-model.md).
      Rodar a suíte e **ver o teste de conformidade da F0.2 ficar vermelho**
- [X] T007 [P] Alinhar narrativa em `docs/04-modelagem-de-dados.md` (tipo de trabalho,
      desfecho em `classificacao_bruta`, `estado_cadastro`) conforme research §5–§6 e §11
- [X] T008 Congelar o SQL em `alembic/versions/sql/0006_interpretar_ficha.sql`, idêntico ao
      bloco alterado do documento
- [X] T009 Criar a revisão `alembic/versions/0006_interpretar_ficha.py` com
      `down_revision = "0005_trabalho_e_coleta"`, executando o SQL congelado; `downgrade`
      restaura `CHECK`/visão anteriores. Rodar até conformidade verde
- [X] T010 [P] Ampliar `app/fila/repository.py` + `app/fila/service.py` com
      `TIPO_INTERPRETAR_FICHA` / `enfileirar_interpretar_ficha` (payload só com IDs) conforme
      [contracts/llm-e-fila.md](./contracts/llm-e-fila.md)
- [X] T011 [P] Criar `app/modulos/conversa/validacao_ficha.py` (funções puras: data,
      tipo/número documento, CEP/telefone; **sem idade**) e esqueleto de
      `app/modulos/conversa/schema.py` para evento interno normalizado do webhook
- [X] T012 [P] Ampliar `app/modulos/conversa/repository.py` + `service.py` com funções
      nomeadas: inserir `evento_webhook`, inserir mensagem `recebida`, resolver reserva por
      telefone+`id_hotel`, gravar `classificacao_bruta`, `extrair_campos_via_llm` —
      `NotImplementedError` onde ainda não houver história; **não** importar
      `hospedagem`
- [X] T013 [P] Ampliar `app/modulos/hospedagem/repository.py` + `service.py` com
      `consolidar_ficha_titular` / leitura de ficha (UPDATE `hospede`,
      `reserva_hospede.ficha_completa`, `reserva.status`) — esqueleto ou implementação
      mínima com `NotImplementedError` até US1
- [X] T014 [P] Acrescentar `estado_cadastro` a `ItemFilaDoDia` e criar
      `FichaTitularResposta` (sem idade) em `app/modulos/hospedagem/schema.py` conforme
      [contracts/api-de-hospedagem.md](./contracts/api-de-hospedagem.md)
- [X] T015 Registrar operação `ler_ficha_de_hospede` (só recepção) em
      `app/modulos/acesso/politica.py` conforme
      [contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md)
- [X] T016 Criar `app/modulos/conversa/router.py` (GET desafio + POST webhook) e montar em
      `app/main.py`; validação de assinatura/token via config; **sem** chamar LLM na
      thread HTTP — [contracts/webhook-e-entrada.md](./contracts/webhook-e-entrada.md)
- [X] T017 Ampliar `worker/consumidor.py` para despachar `interpretar_ficha`: orquestra
      `conversa` (extração) → `hospedagem` (consolidação quando completa/parcial); injetar
      `LLMProvider` (padrão falsa no teste)

**Checkpoint**: DDL/visão no documento e no banco; LLM falso utilizável; webhook montado;
worker reconhece o tipo; fronteiras sem ciclo de import. Histórias podem começar.

---

## Phase 3: User Story 1 - Resposta completa vira ficha pronta (Priority: P1) 🎯 MVP

**Goal**: Texto com os nove campos utilizáveis → ficha completa, `ficha_recebida`,
`estado_cadastro = completa`, ficha legível na API da recepção; webhook não interpreta na
requisição; nenhuma mensagem pedindo correção.

**Independent Test**: Criar reserva + coleta enviada; `POST /webhook` com texto completo →
mensagem+trabalho pendentes e status ainda `aguardando_cadastro`; uma passagem do worker com
LLM falso “completa” → `GET /fila-do-dia` com `estado_cadastro=completa` e
`GET /reservas/{id}/ficha` com os campos e sem idade.

### Tests for User Story 1 ⚠️

> Escrever primeiro; rodar; ver falhar pelo motivo certo antes de implementar.

- [X] T018 [P] [US1] Unitários de validação em
      `testes/unitarios/modulos/conversa/test_validacao_ficha.py` (data válida/inválida;
      tipo documento; ausência de idade no resultado)
- [X] T019 [P] [US1] Unitários de recebimento em
      `testes/unitarios/modulos/conversa/test_receber_mensagem.py`: evento novo grava
      mensagem+enfileira; `id_externo` repetido não duplica; sem LLM na função de
      recebimento
- [X] T020 [P] [US1] Unitários de consolidação completa em
      `testes/unitarios/modulos/hospedagem/test_consolidar_ficha.py` (titular atualizado;
      `ficha_completa=true`; status `ficha_recebida`)
- [X] T021 [P] [US1] Integração `testes/integracao/test_webhook_coleta.py`: assinatura
      inválida rejeitada; evento válido cria `evento_webhook`+mensagem+trabalho sem mudar
      status; reenvio idempotente
- [X] T022 [US1] Integração caminho feliz em
      `testes/integracao/test_interpretar_ficha.py`: worker + LLM falso completa → status/
      fila/ficha; zero mensagem de saída nova de cobrança

### Implementation for User Story 1

- [X] T023 [US1] Implementar `validacao_ficha.py` até os unitários T018 verdes
- [X] T024 [US1] Implementar gravação idempotente de webhook + resolução por telefone +
      enfileiramento em `conversa` (`repository`/`service`/`router`) até T019/T021 verdes
- [X] T025 [US1] Implementar `extrair_campos_via_llm` + gravação de `classificacao_bruta`
      (`desfecho=completa`) em `app/modulos/conversa/service.py`
- [X] T026 [US1] Implementar `consolidar_ficha_titular` (caminho completo) em
      `app/modulos/hospedagem/` até T020 verde
- [X] T027 [US1] Completar branch do worker para desfecho completo (orquestração sem ciclo
      de import)
- [X] T028 [US1] Expor `estado_cadastro` na leitura da fila (`repository` da visão /
      mapeamento do schema) e implementar `GET /reservas/{id_reserva}/ficha` no
      `app/modulos/hospedagem/router.py` com política de recepção
- [X] T029 [US1] Fechar integração T022 verde; garantir que parcial/irreconhecível ainda
      podem falhar (fora do MVP) sem quebrar o completo

**Checkpoint**: US1 entregável sozinha — caminho feliz ponta a ponta com portas falsas.

---

## Phase 4: User Story 2 - Resposta parcial sem nova cobrança (Priority: P1)

**Goal**: Subconjunto de campos → `ficha_parcial`, `ficha_completa=false`,
`estado_cadastro=parcial`; **nenhuma** mensagem ao hóspede pedindo o restante; nenhum
`enviar_coleta` novo.

**Independent Test**: Webhook + LLM falso parcial → status `ficha_parcial` na fila; contagem
de mensagens `enviada` da reserva inalterada; ficha mostra só o reconhecido.

### Tests for User Story 2 ⚠️

- [X] T030 [P] [US2] Unitário em
      `testes/unitarios/modulos/hospedagem/test_consolidar_ficha.py`: parcial grava campos
      reconhecidos, `ficha_completa=false`, status `ficha_parcial`
- [X] T031 [P] [US2] Unitário em
      `testes/unitarios/modulos/conversa/test_extracao_ficha.py`: campos inválidos não
      contam como utilizáveis (reduzem para parcial ou irreconhecível)
- [X] T032 [US2] Integração em `testes/integracao/test_interpretar_ficha.py`: parcial →
      `estado_cadastro=parcial`; assert explícito de **zero** novo `trabalho`
      `enviar_coleta` e zero mensagem de saída de cobrança

### Implementation for User Story 2

- [X] T033 [US2] Estender consolidação/extração para desfecho parcial (T030/T031 verdes)
- [X] T034 [US2] Garantir no worker que parcial **não** chama `MensageriaGateway` nem
      enfileira envio; fechar T032 verde
- [X] T035 [US2] Confirmar `estado_cadastro=parcial` na visão/API da fila do dia

**Checkpoint**: US1 e US2 independentes; parcial visível e sem cobrança no WhatsApp.

---

## Phase 5: User Story 3 - Texto irreconhecível preservado para humano (Priority: P1)

**Goal**: Zero campos utilizáveis (ou mídia sem texto / falha do extrator) → texto
preservado, nada inventado no titular, status permanece `aguardando_cadastro`,
`estado_cadastro=leitura_humana`, sem mensagem ao hóspede.

**Independent Test**: Webhook com LLM falso irreconhecível (e caso de falha do extrator) →
mensagem intacta; fila com `leitura_humana`; `GET /ficha` sem campos inventados.

### Tests for User Story 3 ⚠️

- [X] T036 [P] [US3] Unitário: irreconhecível grava `classificacao_bruta.desfecho` e **não**
      chama consolidação que altere `hospede`/status — em
      `testes/unitarios/modulos/conversa/test_extracao_ficha.py` (e/ou consolidação)
- [X] T037 [P] [US3] Unitário/integração de mídia sem texto: trata como irreconhecível para
      ficha; não aceita foto de documento como fonte
- [X] T038 [US3] Integração: irreconhecível → `leitura_humana`; falha do LLM até esgotar
      tentativas → `falha_extrator` + `leitura_humana`; mensagem nunca apagada — em
      `testes/integracao/test_interpretar_ficha.py`
- [X] T039 [US3] Integração/fila: `testes/integracao/test_fila_do_dia.py` distingue
      `aguardando` vs `leitura_humana` vs `completa` vs `parcial`

### Implementation for User Story 3

- [X] T040 [US3] Implementar caminhos irreconhecível e `falha_extrator` no worker/conversa
      (preservar mensagem; marcar desfecho; sem UPDATE inventado de ficha)
- [X] T041 [US3] Implementar derivação `leitura_humana` na visão/`estado_cadastro` conforme
      [data-model.md](./data-model.md)
- [X] T042 [US3] Tratar `tem_texto_utilizavel=false` no recebimento do webhook (evento
      gravado; sem consolidação falsa)
- [X] T043 [US3] Fechar T038/T039 verdes; edge: mensagem após ficha já consolidada não
      sobrescreve

**Checkpoint**: Quatro desfechos distinguíveis na fila; humano vê o irreconhecível.

---

## Phase 6: User Story 4 - Privacidade: idade e logs (Priority: P2)

**Goal**: Data de nascimento pode persistir; idade nunca; logs de recebimento/interpretação
só com identificadores e códigos.

**Independent Test**: Caminho completo com data de nascimento + `caplog` / asserts de log
sem conteúdo nem campos pessoais.

### Tests for User Story 4 ⚠️

- [X] T044 [P] [US4] Estender
      `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py` (ou arquivo irmão) para
      recebimento e interpretação: log sem `conteudo`, sem telefone, sem nome, sem payload
- [X] T045 [P] [US4] Assert de integração/ficha: resposta de `GET .../ficha` e UPDATE de
      `hospede` **não** incluem idade; schema rejeita se alguém tentar expor

### Implementation for User Story 4

- [X] T046 [US4] Revisar pontos de log em `conversa`, `hospedagem` e `worker` do fluxo de
      entrada até T044 verde
- [X] T047 [US4] Garantir `FichaTitularResposta` / consolidação sem qualquer campo idade;
      T045 verde

**Checkpoint**: Minimização e trilha limpa cobertas por teste.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Fechar documentação de estado, autorização e roteiro do quickstart

- [X] T048 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md` (F1.3 concluída / decisões novas:
      `estado_cadastro`, webhook, `LLMProvider`, worker orquestra)
- [X] T049 [P] Teste de autorização: operacional/gestão recebem `403` em
      `GET /reservas/{id}/ficha` — em integração existente de acesso ou
      `testes/integracao/test_interpretar_ficha.py`
- [X] T050 Edge: telefone sem reserva elegível grava só evento (quando novo) e responde
      `200` — cobrir em `test_webhook_coleta.py`
- [X] T051 Rodar o roteiro de [quickstart.md](./quickstart.md) (ou equivalente automatizado)
      e a suíte `pytest testes/unitarios -q` + integrações da fatia; tudo verde sem rede
      Meta/LLM real
- [X] T052 Revisar fronteiras de import: `conversa` não importa `hospedagem`; worker é o
      orquestrador

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: após Setup — **bloqueia** todas as histórias
- **US1 (Phase 3)**: após Foundational — MVP
- **US2 (Phase 4)**: após Foundational; na prática reusa pipeline da US1 (desfecho parcial)
- **US3 (Phase 5)**: após Foundational; reusa pipeline (desfechos sem consolidação)
- **US4 (Phase 6)**: após pelo menos US1 (precisa haver caminho que loga/persiste)
- **Polish (Phase 7)**: após as histórias desejadas

### User Story Dependencies

- **US1**: só Foundational — MVP isolado
- **US2**: logicamente independente no aceite; implementação estende o mesmo worker
- **US3**: independente no aceite; compartilha webhook/visão
- **US4**: transversal; validar sobre US1 (e idealmente US3)

### Within Each User Story

1. Testes escritos e vermelhos  
2. Implementação mínima  
3. Verde  
4. Só então próxima história  

### Parallel Opportunities

- T001–T002 em paralelo  
- T003–T004, T007, T010–T015 em paralelo após o desenho; T006→T008→T009 sequenciais com o
  teste de conformidade  
- T018–T021 em paralelo dentro da US1  
- T030–T031 em paralelo na US2  
- T036–T037 em paralelo na US3  
- T044–T045 em paralelo na US4  
- T048–T049 em paralelo no polish  

---

## Parallel Example: User Story 1

```text
# Testes em paralelo (antes da implementação):
T018 test_validacao_ficha.py
T019 test_receber_mensagem.py
T020 test_consolidar_ficha.py (caminho completo)
T021 test_webhook_coleta.py

# Depois, implementação na ordem:
T023 → T024 → T025 → T026 → T027 → T028 → T029 (T022)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2  
2. Phase 3 (US1)  
3. **STOP**: validar quickstart cenários 1–2  
4. Demo: webhook → worker → fila `completa` + GET ficha  

### Incremental Delivery

1. US1 → ficha completa  
2. US2 → parcial sem cobrança  
3. US3 → leitura humana / falha extrator  
4. US4 → privacidade  
5. Polish → estado do projeto + quickstart  

### Suggested MVP scope

**Só US1** (T001–T029): prova o valor principal da fatia. US2–US4 são aceites obrigatórios
da spec antes de marcar F1.3 concluída no backlog — completar na mesma entrega se o prazo
permitir; não abrir F1.4 sem US2/US3.

---

## Notes

- [P] = arquivos distintos, sem depender de tarefa incompleta da mesma sequência  
- Worker orquestra; **proibido** `conversa` importar `hospedagem`  
- Commit por tarefa ou grupo lógico (só se o usuário pedir commit)  
- Evitar: interpretar no HTTP; quinto status de reserva; idade persistida; cobrar campos no
  WhatsApp após parcial  
