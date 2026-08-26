---
description: "Task list for feature implementation"
---

# Tasks: Simulador de Conversa

**Input**: Design documents from `/specs/024-simulador-conversa/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de
produção sem teste que falhe antes pelo motivo certo.

**Organization**: Tarefas agrupadas por história (US1–US4), na ordem da spec.
Configuração `MENSAGERIA_MODO`, fábrica, `MensageriaSimulada`, worker sem
`MensageriaFalsa` e operação `usar_simulador` entram na Foundational. Ver o
fio no GET é a US1 (MVP). Turno do hóspede no POST é a US2. Regras idênticas
nos dois modos é a US3. Isolamento (modo real, hotel B, staff) é a US4. A
página React é polish — o critério automatizado das histórias é o HTTP.
Sem migração. Sem tipo novo na fila. Sem WebSocket.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US4)

## Como ver os testes falharem nesta fatia

**Fábrica.** Sem `MENSAGERIA_MODO` (ou valor lixo) `construir_mensageria`
deve falhar alto. O unitário falha com `ImportError` / `AttributeError` até
existir a função; depois falha por não levantar até a validação existir.

**Worker.** `testes/unitarios/worker/test_cli_worker.py`: `--uma-passagem`
ainda injeta `MensageriaFalsa()` no `__main__` até a fábrica ser usada. O
caso novo captura o `gateway=` passado a `processar_uma_passagem_na_engine`
e exige instância de `MensageriaSimulada` quando o modo é `demonstracao`.

**HTTP.** Sem `/simulador/conversas` a integração falha com `404` de rota.
Depois de ligar a rota, `testes/integracao/test_rotas_protegidas.py` exige
`401` sem cookie — **não** editar `ROTAS_PUBLICAS`.

**Matriz.** Acrescentar `usar_simulador` em `OPERACOES_ESPERADAS` **antes**
de `politica.py` deixa `test_matriz_completa_bate_com_o_contrato` vermelho.

**Modo `real`.** Integração com `mensageria_modo=real` espera `409` e
`codigo=modo_real`. Sem o ramo, vem `200`/`201` — falha pelo motivo certo.

**Serviço.** Unitários falham por `AttributeError` / `NotImplementedError`
até existir `listar_conversas_simulador`, `obter_conversa_simulador` e
`enviar_turno_hospede_simulador`.

---

## Phase 1: Setup

**Purpose**: chave documentada, `httpx` na dependência principal, helper de
teste. O monólito já existe; não criar pacote Python novo.

- [X] T001 [P] Documentar `MENSAGERIA_MODO=` (sem valor) em `.env.example`,
      com as duas opções `demonstracao` e `real` no comentário, no padrão
      das chaves WhatsApp. Sem segredo
- [X] T002 [P] Promover `httpx` de extra `dev` para
      `project.dependencies` em `pyproject.toml` (o adaptador WhatsApp já
      o importa; modo `real` precisa subir). Manter `httpx` em `dev` só se
      ainda for útil ao pytest; não adicionar outra lib
- [X] T003 [P] Criar `testes/suporte/simulador.py` com: prefixo
      `ID_EXTERNO_SIM = "sim:"`, helper `modo_demonstracao(monkeypatch)` /
      `modo_real(monkeypatch)` que define `MENSAGERIA_MODO` e chama
      `obter_configuracao.cache_clear()`, e `id_externo_sim(sufixo)` estável.
      Docstring: uso só em teste. Sem chamar worker

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: modo na config, adaptador de demonstração, fábrica, worker
deixa a falsa, matriz `usar_simulador`, DTOs e nomes do serviço.
**Nenhuma rota `/simulador` ainda.**

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase.

- [X] T004 Unitários em
      `testes/unitarios/adaptadores/test_fabrica_mensageria.py`:
      `construir_mensageria` com modo `demonstracao` devolve
      `MensageriaSimulada`; com `real` devolve `MensageriaWhatsapp` **sem**
      chamar rede; ausente/vazio/`whatsapp`/`teste` levantam erro de
      configuração. Rodar e **ver falhar**
      ([contracts/modo-e-fabrica.md](./contracts/modo-e-fabrica.md), FR-001)
- [X] T005 Acrescentar `mensageria_modo: str = ""` em `app/config.py`
      (mapeia `MENSAGERIA_MODO`). Não falhar no Settings — a fábrica é
      quem recusa. Default vazio para o restante da suíte que não chama
      a fábrica
- [X] T006 [P] Unitários em
      `testes/unitarios/adaptadores/test_mensageria_simulada.py`: a classe
      implementa os sete `enviar_*` do Protocol; sucesso devolve
      `id_externo` `sim-{id_mensagem}`; **não** tem `falhar_sempre`. Rodar
      e **ver falhar**
- [X] T007 Criar `app/adaptadores/mensageria_simulada.py` até T006 verde.
      Sem HTTP. Sem ganchos de falha da falsa
- [X] T008 Criar `app/adaptadores/fabrica_mensageria.py` com
      `construir_mensageria(config)` até T004 verde. **Não** importar
      adaptador em `app/modulos/conversa/service.py`
- [X] T009 Estender `testes/unitarios/worker/test_cli_worker.py`: com
      config `mensageria_modo="demonstracao"`, `--uma-passagem` passa a
      `processar_uma_passagem_na_engine` um `gateway` que é
      `MensageriaSimulada` (não `MensageriaFalsa`). Rodar e **ver falhar**
- [X] T010 Trocar `MensageriaFalsa()` em `worker/__main__.py` pela fábrica.
      Em `worker/consumidor.py`, default de `gateway` omitido = fábrica
      (não `MensageriaFalsa()`). Suíte que injeta `gateway=` permanece.
      T009 verde
- [X] T011 [P] Acrescentar casos em
      `testes/unitarios/modulos/acesso/test_politica.py`: `usar_simulador`
      permitida para `recepcao` e `gestor`, recusada para `staff`; incluir
      em `OPERACOES_ESPERADAS`. Rodar e **ver falhar**
      ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md),
      FR-013)
- [X] T012 Acrescentar `usar_simulador` a `OPERACOES` em
      `app/modulos/acesso/politica.py` até T011 passar. **Não** nascer
      `ler_simulador` / `enviar_simulador` separados
- [X] T013 [P] Acrescentar em `app/modulos/conversa/schema.py` os DTOs de
      [contracts/api-do-simulador.md](./contracts/api-do-simulador.md):
      lista (`modo`, `conversas`), fio (`mensagens` com `direcao`,
      `conteudo`, `status_envio`, `enviada_em`), POST (`texto`,
      `id_externo`). Sem `id_hotel`. `extra="forbid"` na entrada
- [X] T014 Nomes em esqueleto (`NotImplementedError`) em
      `app/modulos/conversa/service.py`: `listar_conversas_simulador`,
      `obter_conversa_simulador`, `enviar_turno_hospede_simulador`; e
      função pura `exigir_modo_demonstracao(modo)` que recusa tudo que
      não for `demonstracao`. Sem rota ainda

**Checkpoint**: fábrica e adaptador existem; worker de processo usa a
simulada em demo; matriz com `usar_simulador`; ainda **não** há
`/simulador`. Histórias podem começar.

---

## Phase 3: User Story 1 - Ver a conversa na tela, sem telefone (Priority: P1) 🎯 MVP

**Goal**: Em modo `demonstracao`, GET autenticado lista reservas da casa
e devolve o fio (`mensagem`) em ordem. Recado processado pelo worker com
`MensageriaSimulada` aparece como `direcao=enviada` — coleta, lembrete,
boas-vindas, sessão, pulso, pesquisa de saída e lista de pedidos feitos
pelo chat. Zero Graph API.

**Independent Test**: Sessão recepção, modo demo, cadastrar reserva,
`--uma-passagem` com fábrica/simulada, `GET /simulador/conversas/{id}`
mostra a coleta `enviada`. Sem cookie → `401`. Staff → `403`. Modo real
→ `409 modo_real`. Hotel B não vê a reserva de A (`404` no id de A).

### Tests for User Story 1 ⚠️

> Escrever primeiro; rodar; ver falhar pelo motivo certo antes de implementar.

- [X] T015 [P] [US1] Unitários em
      `testes/unitarios/modulos/conversa/test_simulador_listar.py` com
      repositório falso: lista só reservas do `id_hotel` da sessão, ordem
      `id_reserva` desc; fio ordenado por `enviada_em`/`id_mensagem`
      inclui `pendente`; modo `real` levanta recusa de canal **antes** de
      ler banco; log sem `conteudo`. Rodar e **ver falhar** (FR-002,
      FR-003, FR-008, FR-009, FR-014, FR-017)
- [X] T016 [P] [US1] Integração em
      `testes/integracao/test_simulador_conversa.py`: `GET /simulador/conversas`
      sem cookie → `401` (e `test_rotas_protegidas` continua verde sem
      meter a rota em `ROTAS_PUBLICAS`); staff logado → `403`; recepção
      em `real` → `409`; recepção em demo com hotel vazio → `200`
      `conversas: []`. Rodar e **ver falhar** (`404` de rota)

### Implementation for User Story 1

- [X] T017 [US1] Em `app/modulos/hospedagem/repository.py` e
      `app/modulos/hospedagem/service.py`, `listar_rotulos_para_simulador(id_hotel)`
      devolve `id_reserva`, `status`, `telefone_contato`, nome do titular.
      `conversa` **não** lê tabela `hospede`. Sem nova operação na matriz
      (quem autoriza é `usar_simulador`)
- [X] T018 [US1] Em `app/modulos/conversa/repository.py`,
      `listar_mensagens_da_reserva(conexao, *, id_hotel, id_reserva)` com
      filtro de hotel via `reserva`. Sem `conteudo` em log
- [X] T019 [US1] Implementar `listar_conversas_simulador` e
      `obter_conversa_simulador` em `app/modulos/conversa/service.py`
      (chama T014 `exigir_modo_demonstracao`, T017 e T018) até T015 verde
- [X] T020 [US1] Ligar `GET /simulador/conversas` e
      `GET /simulador/conversas/{id_reserva}` em
      `app/modulos/conversa/router.py` com `exigir_operacao("usar_simulador")`,
      hotel da sessão, `404` unificado. T016 verde
- [X] T021 [US1] Estender
      `testes/integracao/test_simulador_conversa.py`: cadastrar reserva
      (coleta), `processar_uma_passagem` com `MensageriaSimulada`, GET do
      fio mostra coleta `enviada`; repetir o padrão para ao menos um
      recado de sessão (dúvida já existente no suporte) **ou** boas-vindas
      se o fixture de chegada estiver à mão. Demais tipos (lembrete, pulso,
      pesquisa, lista de pedidos feitos pelo chat) cobertos no mesmo
      arquivo com um caso cada, reusando os apoios das fatias anteriores.
      Rodar e **ver falhar** o que ainda não aparecer; completar serviço
      só se faltar leitura — **não** criar tipo novo de envio
      (FR-015, SC-001)

**Checkpoint**: GET prova a conversa sem telefone. POST ainda não existe.
Página React ainda não.

---

## Phase 4: User Story 2 - Falar como o hóspede na mesma tela (Priority: P1)

**Goal**: POST autenticado grava o turno como o webhook gravaria
(`receber_evento_entrada`), responde na hora, e o worker faz o resto.
Confirmação de pedido/reclamação no GET **antes** do chamado. Ficha
continua ficha. Sem conversa escolhida / texto vazio / `id_externo`
ausente → recusa. Idempotência pelo UNIQUE de `evento_webhook`.

**Independent Test**: Reserva hospedada, POST dúvida coberta, `--uma-passagem`,
GET mostra resposta de catálogo. POST pedido: confirmação no fio e
`solicitacao` só depois. Mesmo `id_externo` → `200` e uma mensagem.

### Tests for User Story 2 ⚠️

- [X] T022 [P] [US2] Unitários em
      `testes/unitarios/modulos/conversa/test_simulador_turno.py`:
      modo `real` recusa sem chamar `receber_evento_entrada`; texto vazio
      e `id_externo` ausente recusam; reserva de outro hotel recusa;
      caminho feliz monta `EventoEntrada` com telefone da reserva e
      `id_hotel` da **sessão** (não `whatsapp_id_hotel`) e delega;
      duplicata devolve status `duplicado` sem segundo insert; log sem
      texto. Rodar e **ver falhar**
      ([contracts/entrada-simulada.md](./contracts/entrada-simulada.md),
      FR-004, FR-010, FR-011)
- [X] T023 [P] [US2] Integração em
      `testes/integracao/test_simulador_conversa.py` (ou arquivo irmão
      `test_simulador_turno.py` se o da US1 crescer demais): POST sem
      cookie `401`; staff `403`; modo `real` `409`; texto `""` `400`
      `texto_vazio`; sem `id_externo` `400`; id de reserva de B com
      sessão de A `404`. Rodar e **ver falhar** (`404`/`405` de rota)

### Implementation for User Story 2

- [X] T024 [US2] Implementar `enviar_turno_hospede_simulador` em
      `app/modulos/conversa/service.py`: valida, carrega reserva do hotel
      da sessão, chama `receber_evento_entrada`. **Não** copiar o
      resolver. **Não** classificar neste passo. T022 verde
- [X] T025 [US2] Ligar `POST /simulador/conversas/{id_reserva}/mensagens`
      em `app/modulos/conversa/router.py`: `201` primeira vez, `200`
      duplicado. T023 verde
- [X] T026 [US2] Integração em
      `testes/integracao/test_simulador_conversa.py`: reserva
      `hospedado`, POST dúvida coberta + worker (`LLMFalso` +
      `MensageriaSimulada` + catálogo da casa) → GET tem resposta fiel;
      POST pedido de serviço → GET tem confirmação **e** `solicitacao`
      só depois da passagem que a cria (FR-005, FR-006). Rodar;
      completar só `app/modulos/conversa/service.py` se o POST não
      enfileirar
- [X] T027 [US2] Integração em
      `testes/integracao/test_simulador_conversa.py`: reserva
      `aguardando_cadastro`, POST com texto de ficha → trabalho
      `interpretar_ficha` (não `classificar_mensagem`); POST do mesmo
      `id_externo` → uma `mensagem`. FR-004 cenário 4, FR-011

**Checkpoint**: apresentador fala como hóspede pelo HTTP. Regras de
negócio ainda não retestadas de ponta a ponta na US3.

---

## Phase 5: User Story 3 - O sistema demonstrado é o mesmo sistema (Priority: P1)

**Goal**: Trocar o modo é configuração. Pulso continua suprimido com
chamado aberto; pergunta fora do catálogo continua humana; não há
`if modo` em regra de hotel dentro de `conversa.service`.

**Independent Test**: Mesmo texto de hóspede, reserva equivalente, desfecho
igual com `MensageriaFalsa` (suíte antiga) e com `MensageriaSimulada`.
Varredura de pulso em demo **não** dispara se há reclamação aberta.

### Tests for User Story 3 ⚠️

- [X] T028 [P] [US3] Unitário em
      `testes/unitarios/modulos/conversa/test_simulador_nao_ramifica_dominio.py`
      (ou inspeção em `test_fabrica_mensageria.py`):
      `app/modulos/conversa/service.py` **não** importa
      `mensageria_simulada`, `mensageria_whatsapp` nem
      `mensageria_falsa`. Rodar e **ver falhar** se alguém tiver
      importado; senão já passa — **não** “consertar” com import
      (Artigo X, FR-007, FR-019)
- [X] T029 [P] [US3] Integração em
      `testes/integracao/test_simulador_conversa.py`: pergunta fora do
      catálogo via POST da tela + worker → **não** há resposta inventada
      no GET; sinal de humano como na F3.3 (FR-006, FR-007)
- [X] T030 [P] [US3] Integração em
      `testes/integracao/test_simulador_conversa.py`: reclamação aberta +
      pulso elegível no relógio, modo demo, `verificar_pulsos` em
      `worker/agendador.py` (caminho da F3.8) → **zero** recado de pulso
      no fio (FR-007, SC-002)

### Implementation for User Story 3

- [X] T031 [US3] Só se T029/T030 falharem por motivo **errado**, corrigir
      `app/modulos/conversa/service.py` (enfileiramento), **não** atalho
      de palco. Se já verdes depois da US2, não apagar os testes em
      `testes/integracao/test_simulador_conversa.py` — travam regressão

**Checkpoint**: a banca vê o mesmo hotel. Isolamento de modo/hotel ainda
é a US4.

---

## Phase 6: User Story 4 - Um modo não contamina o outro (Priority: P2)

**Goal**: Modo `real` recusa GET e POST da tela (`409`). Demonstração não
instancia WhatsApp. Hotel A não lê nem escreve conversa de B. Staff
continua `403`.

**Independent Test**: `MENSAGERIA_MODO=real`, recepção autenticada, POST
e GET `/simulador/...` → `409`, zero `mensagem` nova. GET do id de A com
sessão de B → `404`.

### Tests for User Story 4 ⚠️

- [X] T032 [P] [US4] Integração em
      `testes/integracao/test_simulador_conversa.py`: os **três** métodos
      em modo `real` → `409` `modo_real`; contar `mensagem` antes/depois
      do POST = igual (FR-008, FR-009, SC-005)
- [X] T033 [P] [US4] Integração em
      `testes/integracao/test_simulador_conversa.py`: sessão da
      propriedade B + `id_reserva` da A → `404` no GET do fio e no POST;
      lista de B não contém A (FR-014, SC-006)
- [X] T034 [P] [US4] Unitário em
      `testes/unitarios/adaptadores/test_fabrica_mensageria.py`: modo
      `demonstracao` **não** devolve `MensageriaWhatsapp`. Pode já estar
      verde na T004 — manter o assert explícito (FR-002, SC-001)

### Implementation for User Story 4

- [X] T035 [US4] Fechar buracos que T032–T033 encontrarem em
      `app/modulos/conversa/service.py` / `router.py` (filtro `id_hotel`,
      `exigir_modo_demonstracao` nos três verbos). Sem mudar o webhook
      da F3.1

**Checkpoint**: canais isolados. Página React ainda é polish.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: tela visível, mesmo origin, documentação de retomada, suíte
cheia. Não reabre regra de negócio.

- [X] T036 [P] Estender
      `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py` (ou o
      arquivo da US1/US2): listar, obter e turno **não** logam `conteudo`
      nem telefone em claro (FR-017, SC-008)
- [X] T037 Criar `frontend/` mínimo: `package.json`, `tsconfig.json`,
      `vite.config.ts` (proxy de `/sessoes`, `/simulador` e demais APIs
      já usadas no login para o uvicorn), `index.html`,
      `frontend/src/main.tsx`. Sem kit UI, sem React Router
      ([contracts/tela-de-simulacao.md](./contracts/tela-de-simulacao.md))
- [X] T038 Implementar `frontend/src/TelaSimulacao.tsx`: lista, escolha,
      fio com direção visível, `status_envio`, campo de texto, POST com
      `id_externo` gerado no cliente e reusado em retry, GET periódico
      ~1 s, recusa visível de `modo_real` / `401` / `403`. `credentials:
      'include'`
- [X] T039 Em `app/main.py`, montar estáticos de `frontend/dist` em
      `/demo/` **se** o diretório existir (banca sem `npm run dev`).
      Não colidir com `/simulador`. Não adicionar `/demo` a
      `ROTAS_PUBLICAS` se a montagem não for rota de domínio — se for
      `StaticFiles`, o teste de rotas protegidas não a varre; conferir
      depois de ligar
- [X] T040 Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F6.2 concluída
      (quando a implementação estiver verde), worker usa fábrica, pasta
      `frontend/` existe, próxima entrega = implantação em nuvem
      (ADR-008). Sem inventar F2.3/F3.9
- [X] T041 Marcar F6.2 concluída em `docs/backlog.md` no padrão das
      fatias anteriores (parágrafo **Status: concluída** com o recorte:
      tela + fábrica; sem painel operacional React; sem túnel)
- [X] T042 Rodar `pytest testes/unitarios -q` e
      `pytest testes/integracao -q -k simulador`; percorrer
      [quickstart.md](./quickstart.md) no navegador (login, escolher
      reserva, ver coleta, digitar dúvida). Se a tela falhar, corrigir
      `TelaSimulacao.tsx` / proxy — não a regra de hotel

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: começa agora
- **Foundational (Phase 2)**: depende do Setup — **bloqueia** as histórias
- **US1 (Phase 3)**: depende da Foundational — MVP
- **US2 (Phase 4)**: depende da US1 (precisa do GET para afirmar o fio
  depois do POST). Pode reusar o arquivo de integração
- **US3 (Phase 5)**: depende da US2 (POST + worker)
- **US4 (Phase 6)**: depende da US1+US2 (rotas existirem). Isolamento
  pode ser escrito em paralelo aos testes da US3
- **Polish (Phase 7)**: depende das quatro histórias (API estável)

### User Story Dependencies

- **US1 (P1)**: depois da Phase 2 — GET + worker simulada
- **US2 (P1)**: depois da US1 — POST reusa o GET
- **US3 (P1)**: depois da US2 — afirma regras já existentes
- **US4 (P2)**: depois da US1 (GET) e US2 (POST)

### Within Each User Story

- Testes primeiro; ver falhar pelo motivo certo
- Repositório/serviço antes do router
- Integração HTTP depois da rota
- Não importar adaptador no serviço de conversa

### Parallel Opportunities

- T001, T002, T003 em paralelo
- T006 com T004 (arquivos distintos); T011 com T006
- T015 e T016 em paralelo
- T022 e T023 em paralelo
- T028, T029, T030 em paralelo
- T032, T033, T034 em paralelo
- T036 em paralelo com o início do frontend (T037)

---

## Parallel Example: User Story 1

```text
T015 Unitários listar/obter em testes/unitarios/modulos/conversa/test_simulador_listar.py
T016 Integração GET em testes/integracao/test_simulador_conversa.py
```

Depois, em sequência: T017 → T018 → T019 → T020 → T021.

---

## Parallel Example: User Story 2

```text
T022 Unitários do turno em testes/unitarios/modulos/conversa/test_simulador_turno.py
T023 Integração POST (401/403/409/400/404) em testes/integracao/test_simulador_conversa.py
```

Depois: T024 → T025 → T026 → T027.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup
2. Phase 2: Foundational (bloqueia)
3. Phase 3: US1 — GET mostra a coleta sem Meta
4. **STOP and VALIDATE**: `pytest -k simulador` nos casos de GET
5. US2–US4 e a tela na mesma entrega (um desenvolvedor)

### Incremental Delivery

1. Setup + Foundational → fábrica + worker honesto
2. US1 → demo: banca vê a coleta no GET
3. US2 → demo: banca fala como hóspede
4. US3 → trava “não é outro produto”
5. US4 → trava vazamento de canal/hotel
6. Polish → página `/demo/` + estado do projeto

### Parallel Team Strategy

Um desenvolvedor. Se houvesse dois: um faz US1 GET, outro prepara
unitários da US2 contra o esqueleto T014 — o POST só liga depois do GET.

---

## Notes

- [P] = arquivos distintos, sem dependência pendente
- [USn] mapeia a spec
- **Não** adicionar `/simulador` a `ROTAS_PUBLICAS`
- **Não** instanciar `MensageriaWhatsapp` na suíte
- **Não** abrir navegador no pytest
- **Não** criar revisão Alembic
- Commit depois de cada tarefa ou grupo TDD (vermelho → verde)
- A palavra "extrato" não existe; a lista de consumos é "pedidos feitos
  pelo chat"
