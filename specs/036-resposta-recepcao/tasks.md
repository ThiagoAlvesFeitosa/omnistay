---
description: "Lista de tarefas para implementação da fatia"
---

# Tarefas: F7.6 A recepção responde ao hóspede

**Input**: documentos em `specs/036-resposta-recepcao/`
**Pré-requisitos**: [plan.md](./plan.md), [spec.md](./spec.md),
[research.md](./research.md), [data-model.md](./data-model.md),
[contracts/](./contracts/), [quickstart.md](./quickstart.md)

**TDD (obrigatório)**: nenhuma linha de produção antes de um teste que
falhe pela ausência dela. Em cada tarefa de teste: escrever, rodar,
**ver falhar pelo motivo certo**. Só então a implementação. Um teste
que passa de primeira é suspeito.

**pytest**: `uv run pytest testes/unitarios -q` no ciclo;
`uv run pytest -k nome` para um só.
**Vitest**: `npm --prefix frontend test -- --run`. Sem Playwright.

**Esquema que esta fatia usa (não inventar coluna):**

- `mensagem` **não tem** `id_usuario` nem `erro_envio`.
- `enviada_em` é `NOT NULL DEFAULT now()` (instante do registro; no
  sucesso do envio o worker atualiza). Entrega na API **não** se
  infere por nulo — usa `status_envio`.
- Origem na API: `direcao=recebida` → `hospede`; `enviada` com
  `classificacao_bruta.tipo = resposta_recepcao` → `recepcao`; demais
  enviadas → `automatico`. Sem terceira direção no CHECK.
- `status_envio`: `pendente` → entrega `enviando`; `enviada`/`entregue`
  → `enviada`; `falha` → `falhou`.
- `trabalho.status` é `falha` (não `falhou`). Erro de canal:
  `trabalho.erro_ultima_tentativa`.
- POST janela fechada: `409` `janela_fechada` (não `janela_canal_fechada`).
  JSON: `janela.aberta`, `janela.motivo`.

**Duas guardas (não negociar):**

1. **Estado de entrega na conversa.** Cada resposta da recepção mostra
   **enviando**, **enviada** ou **falhou** com **nova tentativa marcada**
   quando o trabalho ainda não está `concluido`. Sem isso a recepcionista
   acha que respondeu quando o envio falhou.
2. **Clique duplo sem UNIQUE por reserva.** Várias respostas por reserva
   são legítimas. Guarda: botão **Enviar** inerte durante o POST **e**
   servidor recusa texto idêntico (strip) ao da última
   `resposta_recepcao` da reserva se o `enviada_em` **do registro** está
   dentro de `SEGUNDOS_ANTI_DUPLO` (5s) — `409` `texto_repetido`.
   Texto diferente em seguida = 201. Mesmo texto depois de 5s = 201.
   **Proibido** `UNIQUE (id_reserva, tipo)` em `enviar_resposta_recepcao`.
   UNIQUE do trabalho: **só** `(payload->>'id_mensagem')`. Art. IX:
   idempotência do **trabalho** no banco; anti-duplo do **gesto** na
   aplicação + botão inerte.

**Organização**: fases por história (US1–US5). Setup e Foundational
não levam rótulo de história.

## Format: `[ID] [P?] [USx?] Descrição`

- **[P]**: paralelizable (arquivos diferentes, sem dependência incompleta)
- **[USn]**: história correspondente
- Caminho de arquivo em cada tarefa

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: a casca autenticada não quebra quando a Estadia passar a
pedir `GET /reservas/{id}/conversa`.

- [X] T001 [P] Estender `frontend/src/painel/Casca.test.tsx` com
  `GET /reservas/{id}/conversa` nas respostas falsas de `fetch` (recepção
  autenticada), **antes** de `TelaEstadia` chamar esse GET. Rodar
  `npm --prefix frontend test -- --run src/painel/Casca.test.tsx` e ver
  o teste **passar** (ainda não há chamada nova).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: política, constantes, funções puras, rótulo Estadia e
revisão 0025 — sem UNIQUE por reserva. **Nenhuma história começa
antes desta fase terminar.**

**Checkpoint**: `test_politica` inclui as duas operações; destinos
mostram Estadia; funções puras verdes; 0025 existe e o UNIQUE de
`enviar_resposta_recepcao` é só por `id_mensagem`.

- [X] T002 [P] Estender `testes/unitarios/modulos/acesso/test_politica.py`
  para exigir `ler_conversa_da_estadia` e `enviar_resposta_recepcao` só
  em `{"recepcao"}`. Rodar
  `uv run pytest testes/unitarios/modulos/acesso/test_politica.py -q`
  e **ver falhar**.

- [X] T003 Acrescentar `ler_conversa_da_estadia` e
  `enviar_resposta_recepcao` em `app/modulos/acesso/politica.py`
  (somente `recepcao`). Rodar T002 até ficar **verde**.

- [X] T004 [P] Estender `frontend/src/painel/destinos.test.ts` para
  exigir título **Estadia** no destino `ficha` (id e path `/app/ficha`
  intactos). Rodar
  `npm --prefix frontend test -- --run src/painel/destinos.test.ts`
  e **ver falhar**.

- [X] T005 Trocar o título do destino `ficha` para **Estadia** em
  `frontend/src/painel/destinos.ts`. Em `frontend/src/painel/Casca.test.tsx`,
  onde a recepção afirma heading **Ficha do hóspede**, passar a **Estadia**;
  no teste de staff/gestão em `/app/ficha`, garantir que **Estadia** também
  não aparece. Rodar T004 e o Casca até ficarem **verdes**.

- [X] T006 [P] Escrever `testes/unitarios/modulos/conversa/test_janela_canal.py`:
  janela aberta se existe `mensagem` `direcao=recebida` da reserva com
  `enviada_em >= agora - JANELA_SESSAO_CANAL_HORAS` (24); nunca escreveu →
  fechada `motivo=nunca_escreveu`; escreveu há mais de 24h →
  `sem_mensagem_recente`; `agora` de `app.comum.relogio`; **não** lê
  `parametro_hotel`. Rodar e **ver falhar**.

- [X] T007 Implementar `app/modulos/conversa/janela.py`
  (`JANELA_SESSAO_CANAL_HORAS = 24`,
  `TAMANHO_MAXIMO_TEXTO_CANAL = 4096`). Rodar T006 até ficar **verde**.

- [X] T008 [P] Escrever `testes/unitarios/modulos/conversa/test_origem_e_entrega.py`
  (funções puras, sem banco): `direcao=recebida` → origem `hospede`;
  `enviada` + `tipo=resposta_recepcao` → `recepcao`; demais enviadas →
  `automatico`. Entrega: `status_envio=pendente` → `enviando`;
  `enviada`/`entregue` → `enviada`; `falha` → `falhou`. `nova_tentativa`
  verdadeiro **somente** quando entrega é `falhou` e o trabalho
  `enviar_resposta_recepcao` daquela `id_mensagem` **não** está
  `concluido`. Sem `id_usuario`, sem `enviada_em` nulo, sem `erro_envio`.
  Rodar e **ver falhar**.

- [X] T009 Implementar `app/modulos/conversa/origem_e_entrega.py`.
  Rodar T008 até ficar **verde**.

- [X] T010 [P] Escrever `testes/unitarios/modulos/conversa/test_anti_duplo.py`:
  texto idêntico (strip) à última enviada `tipo=resposta_recepcao` da
  reserva cujo `enviada_em` (instante do **registro**, sempre preenchido)
  está há menos de `SEGUNDOS_ANTI_DUPLO` (5) é duplicata; texto diferente
  não é; mesmo texto depois de 5s não é. Relógio injetável
  (`app.comum.relogio.agora`). Rodar e **ver falhar**.

- [X] T011 Implementar `app/modulos/conversa/anti_duplo.py` com
  `SEGUNDOS_ANTI_DUPLO = 5`. Rodar T010 até ficar **verde**.

- [X] T012 [P] Estender `testes/integracao/test_fila_do_dia.py` (e, se o
  padrão do repositório pedir, consulta a `pg_indexes`): depois da 0025,
  `precisa_atendimento_humano` é verdadeiro só com reserva `hospedado` +
  recebida com desfecho humano **e** `enviada_em` dessa recebida
  **posterior** à última enviada `tipo=resposta_recepcao` (se não houver
  resposta humana, a condição vale). Assertiva explícita: **não existe**
  índice `UNIQUE (id_reserva, …)` para `tipo = enviar_resposta_recepcao`;
  existe UNIQUE só em `(payload->>'id_mensagem')`. Rodar e **ver falhar**.

- [X] T013 Criar `alembic/versions/0025_resposta_recepcao.py` (down
  `0024_ficha_parcial_completa`): `ck_trabalho_tipo` ganha
  `enviar_resposta_recepcao`; índice
  `uq_trabalho_enviar_resposta_recepcao_mensagem`; recriar
  `vw_fila_do_dia` na regra de T012. Atualizar `docs/04-schema.sql` no
  mesmo sentido (senão `testes/integracao/test_conformidade_do_esquema.py`
  fica vermelho). Aplicar no banco de desenvolvimento. Rodar T012 e a
  conformidade até ficarem **verdes**.

---

## Phase 3: User Story 1 - A recepção lê a conversa e o hóspede recebe a resposta (Priority: P1) 🎯 MVP

**Goal**: GET da conversa ao abrir Estadia; POST grava `status_envio=pendente`
+ trabalho; worker envia; conversa **antes** dos cadastrais; cadastrais
atrás de **ver dados cadastrais**; atalho **Ver ficha** vira **Estadia**;
fila do dia some o aviso depois da resposta humana.

**Independent Test**: recepção autenticada abre `/app/ficha/:id`, vê o
fio, envia texto, o hóspede recebe pelo gateway falso, e a reserva deixa
de ter `precisa_atendimento_humano` por aquelas mensagens já encaminhadas.

### Tests (escrever e ver falhar)

- [X] T014 [P] [US1] Escrever
  `testes/unitarios/modulos/conversa/test_ler_conversa_da_estadia.py`:
  serviço devolve mensagens da reserva no `id_hotel` da sessão, ordenadas
  por `enviada_em`; conteúdo fora do log. Reserva `encerrado` continua
  legível (FR-017). Rodar e **ver falhar**.

- [X] T015 [P] [US1] Escrever
  `testes/unitarios/modulos/conversa/test_enviar_resposta_recepcao.py`:
  texto válido insere `direcao=enviada`, `status_envio=pendente`,
  `classificacao_bruta={"tipo":"resposta_recepcao"}`, `enviada_em`
  preenchido pelo default do banco (não nulo), trabalho
  `enviar_resposta_recepcao` `pendente` com UNIQUE por `id_mensagem`.
  HTTP 201. Sem coluna `id_usuario`. Rodar e **ver falhar**.

- [X] T016 [P] [US1] Escrever
  `testes/integracao/test_resposta_recepcao.py`: `GET /reservas/{id}/conversa`
  200 para recepção; `POST /reservas/{id}/respostas` 201; worker com
  gateway falso entrega o texto e `status_envio` vira `enviada`. Rodar e
  **ver falhar**.

- [X] T017 [P] [US1] Criar `frontend/src/painel/TelaEstadia.test.tsx`
  (partir de `frontend/src/painel/TelaFicha.test.tsx`): ao montar,
  `GET /reservas/{id}/conversa` **antes** de qualquer `GET .../ficha`;
  conversa visível sem expandir cadastrais; **ver dados cadastrais**
  dispara o GET da ficha; copiar para o sistema de gestão permanece no
  bloco cadastral. Rodar Vitest e **ver falhar**.

- [X] T018 [P] [US1] Estender `frontend/src/painel/TelaFila.test.tsx` e
  o tipo em `frontend/src/painel/fila.ts`: linha com
  `precisa_atendimento_humano` mostra distintivo distinto das pendências
  já existentes; depois de resposta humana (campo falso) o aviso some.
  Rodar Vitest e **ver falhar**.

### Implementation

- [X] T019 [US1] Estender `app/modulos/conversa/repository.py`: listar
  conversa da reserva com `id_hotel` obrigatório (JOIN `reserva`);
  inserir enviada pendente com JSON `tipo=resposta_recepcao` e trabalho
  na mesma transação. Reusar `listar_mensagens_da_reserva` só se ganhar
  o filtro de hotel — hoje ele não tem `id_hotel`.

- [X] T020 [US1] Implementar `ler_conversa_da_estadia` e
  `enviar_resposta_recepcao` em `app/modulos/conversa/service.py`
  (sem SQL, sem HTTP). Rodar T014 e T015 até ficarem **verdes**.

- [X] T021 [P] [US1] Acrescentar contratos Pydantic em
  `app/modulos/conversa/schema.py` conforme
  `specs/036-resposta-recepcao/contracts/api-conversa.md` e
  `api-resposta.md` (`janela.aberta` / `janela.motivo`; em enviadas,
  `entrega` e `nova_tentativa`). Recusas: `detail={"codigo": ...}`.

- [X] T022 [US1] Expor `GET /reservas/{id}/conversa` e
  `POST /reservas/{id}/respostas` em `app/modulos/conversa/router.py`
  com `exigir_operacao`; router só traduz protocolo. Rodar GET/POST de
  T016 até ficarem **verdes** (worker pode ainda falhar).

- [X] T023 [US1] Incluir `enviar_resposta_recepcao` em
  `TIPOS_CONSUMIVEIS` e `enfileirar_*` em `app/fila/repository.py` e
  `app/fila/service.py`. `elif` em `worker/consumidor.py` delegando a
  `processar_trabalho_enviar_resposta_recepcao` em
  `app/modulos/conversa/service.py` (espelhar
  `processar_trabalho_enviar_boas_vindas`: `enviar_texto_sessao`,
  `status_envio=enviada`, trabalho `concluido`). Allowlist e `elif`
  juntos. Rodar a parte de worker de T016 até ficar **verde**.

- [X] T024 [US1] Substituir `TelaFicha` por `TelaEstadia` em
  `frontend/src/painel/TelaEstadia.tsx` e
  `frontend/src/painel/Casca.tsx` (path `/app/ficha` intacto). Conversa
  primeiro; cadastrais recolhidos. Rodar T017 até ficar **verde**.

- [X] T025 [US1] Atualizar atalhos **Ver ficha** → **Estadia**
  (mesmo `to`) em `frontend/src/painel/TelaFila.tsx`,
  `frontend/src/painel/TelaAlertas.tsx`,
  `frontend/src/painel/TelaConsumos.tsx` e o tipo/consumo em
  `frontend/src/painel/fila.ts`. Atualizar os testes desses atalhos
  (`TelaFila.test.tsx`, `TelaAlertas.test.tsx`, `TelaConsumos.test.tsx`).
  Rodar T018 e esses testes até ficarem **verdes**.

**Checkpoint**: recepção lê e envia; worker entrega; fila do dia
reflete a resposta humana.

---

## Phase 4: User Story 2 - A resposta fica no histórico, junto das automáticas (Priority: P1)

**Goal**: origens `hospede` / `automatico` / `recepcao` na API; na tela,
rótulos distinguíveis (hóspede × automático × recepção). Enviadas
automáticas **podem** detalhar o `tipo` já conhecido (boas-vindas,
pulso, coleta) como distintivo visual — a origem da API permanece
`automatico`. Nas respostas da recepção: **enviando / enviada / falhou**
e **nova tentativa marcada** só no ramo `falhou` com trabalho não
`concluido`.

**Independent Test**: GET devolve `origem` e `entrega`; a Estadia mostra
os rótulos; `status_envio=pendente` aparece como **enviando**, não como
sucesso silencioso.

### Tests (escrever e ver falhar)

- [X] T026 [P] [US2] Estender
  `testes/integracao/test_resposta_recepcao.py`: GET lista as três
  origens do contrato; item enviado inclui `entrega`
  `enviando|enviada|falhou` e `nova_tentativa` booleano. Rodar e **ver
  falhar** se o GET ainda não serializa isso.

- [X] T027 [P] [US2] Estender `frontend/src/painel/TelaEstadia.test.tsx`:
  cada origem tem rótulo visível (hóspede / automático / recepção);
  `entrega=enviando` mostra **enviando**; `enviada` mostra **enviada**;
  `falhou` + `nova_tentativa=true` mostra **falhou** e **nova tentativa
  marcada**. Rodar Vitest e **ver falhar**.

### Implementation

- [X] T028 [US2] Fazer o GET em `app/modulos/conversa/service.py` e
  `app/modulos/conversa/schema.py` usar `origem_e_entrega.py` (T009).
  Rodar T026 até ficar **verde**.

- [X] T029 [US2] Renderizar origens e estados de entrega em
  `frontend/src/painel/TelaEstadia.tsx` com os rótulos literais da
  superfície (`enviando`, `enviada`, `falhou`, `nova tentativa marcada`).
  Rodar T027 até ficar **verde**.

**Checkpoint**: a recepcionista vê se a resposta saiu.

---

## Phase 5: User Story 3 - Falha no envio não perde o que foi escrito (Priority: P1)

**Goal**: gateway falso que falha deixa a mensagem no banco,
`status_envio=falha`, trabalho `falha`; conversa mostra **falhou** +
nova tentativa; retry do agendador reenvia a **mesma** `id_mensagem`.
Clique duplo: botão inerte no POST **e** `409` `texto_repetido`. Sem
UNIQUE por reserva. Enter no campo não dispara o POST.

**Independent Test**: falha preserva texto; segundo POST idêntico em
menos de 5s = 409 e uma mensagem só; texto diferente = 201; mesmo texto
após 5s = 201; duas respostas distintas na mesma reserva = dois
trabalhos.

### Tests (escrever e ver falhar)

- [X] T030 [P] [US3] Estender
  `testes/unitarios/modulos/conversa/test_enviar_resposta_recepcao.py`
  (ou `testes/unitarios` do processador): worker com gateway que falha
  **não** apaga a mensagem; `status_envio` vira `falha` (ou permanece
  `pendente` enquanto a fila retenta — então entrega `enviando`); no
  esgotamento, `status_envio=falha` e trabalho `falha`;
  `erro_ultima_tentativa` preenchido; conteúdo fora do log. Sem
  `erro_envio` em `mensagem`. Rodar e **ver falhar**.

- [X] T031 [P] [US3] Estender
  `testes/integracao/test_resposta_recepcao.py`: segundo POST com o
  **mesmo** texto (strip) em menos de 5s → 409 `codigo: texto_repetido`
  e **uma** mensagem só; POST seguinte com texto **diferente** → 201;
  mesmo texto com relógio avançado 6s → 201; duas respostas diferentes
  na mesma reserva → dois `id_mensagem` e dois trabalhos. Rodar e **ver
  falhar**.

- [X] T032 [P] [US3] Estender `frontend/src/painel/TelaEstadia.test.tsx`:
  enquanto o POST está em voo, **Enviar** está `disabled` e um segundo
  clique não dispara segundo `fetch`; Enter no campo **não** dispara
  POST (o gesto é o botão). Rodar e **ver falhar**.

- [X] T033 [P] [US3] Estender `frontend/src/painel/TelaEstadia.test.tsx`:
  GET com `entrega: falhou` e `nova_tentativa: true` mostra **falhou** e
  **nova tentativa marcada** (texto permanece). Falha de POST **antes**
  de gravar (fetch 500): recado de que não gravou; o texto digitado
  permanece no campo; nenhuma bolha nova. Rodar e **ver falhar**.

### Implementation

- [X] T034 [US3] Tratar falha em
  `processar_trabalho_enviar_resposta_recepcao`
  (`app/modulos/conversa/service.py`) via `registrar_falha_de_envio`
  já existente (`app/fila/service.py`): mensagem permanece; no
  esgotamento `status_envio=falha` e trabalho `falha`; retry pela regra
  do agendador, mesma `id_mensagem`. Rodar T030 até ficar **verde**.

- [X] T035 [US3] Recusar duplicata temporal em
  `app/modulos/conversa/service.py` usando `anti_duplo.py` (T011)
  **antes** de gravar. **Não** criar UNIQUE `(id_reserva, tipo)`.
  Rodar T031 até ficar **verde**.

- [X] T036 [US3] Desabilitar **Enviar** durante o POST em
  `frontend/src/painel/TelaEstadia.tsx`; Enter não envia; manter texto
  no campo se o POST falhar ao gravar; bolha **falhou** quando o GET
  devolver isso. Rodar T032 e T033 até ficarem **verdes**.

**Checkpoint**: falha visível e recuperável; duplo clique não duplica;
várias respostas distintas na mesma reserva continuam possíveis.

---

## Phase 6: User Story 4 - Só a recepção escreve; responder não fecha o chamado (Priority: P1)

**Goal**: staff e gestão: GET e POST `403`; casca **não monta** Estadia
e **não** dispara GET de conversa (sem fio somente leitura). POST
**não** altera `solicitacao` e **não** enfileira
`enviar_confirmacao_resolucao`. Resolver chamado permanece o gesto já
existente (não alterar o processador de confirmação de resolução).

**Independent Test**: token staff/gestor no POST → 403; chamado aberto
permanece aberto após resposta no chat.

### Tests (escrever e ver falhar)

- [X] T037 [P] [US4] Estender
  `testes/integracao/test_resposta_recepcao.py`: GET e POST com sessão
  staff → 403; GET e POST com gestão → 403; GET de conversa para
  recepção continua 200. Rodar e **ver falhar**.

- [X] T038 [P] [US4] Estender o mesmo arquivo: reserva com chamado
  aberto; POST 201; `solicitacao.status` inalterado; nenhum trabalho
  `enviar_confirmacao_resolucao` novo. Rodar e **ver falhar**.

- [X] T039 [P] [US4] Estender `frontend/src/painel/Casca.test.tsx`:
  perfil staff e gestão em `/app/ficha` e `/app/ficha/1` **não** chamam
  `GET /reservas/{id}/conversa` (além de não chamarem ficha, já
  coberto). Rodar e **ver falhar**.

### Implementation

- [X] T040 [US4] Garantir `exigir_operacao("enviar_resposta_recepcao")`
  no POST e `exigir_operacao("ler_conversa_da_estadia")` no GET em
  `app/modulos/conversa/router.py`; o serviço de envio **não** chama
  atualização de solicitação nem enfileira confirmação de resolução.
  Rodar T037 e T038 até ficarem **verdes**.

- [X] T041 [US4] Staff/gestão continuam sem o destino `ficha` em
  `frontend/src/painel/destinos.ts` (já é só `recepcao`). **Não**
  montar conversa somente leitura. Rodar T039 até ficar **verde**.

**Checkpoint**: só recepção lê e escreve; chamado não se resolve pelo
chat; recado padrão de resolução intocado.

---

## Phase 7: User Story 5 - Quem não deve falar por esta casa não fala (Priority: P1)

**Goal**: 404 cruzando hotel; 422 texto vazio ou > 4096; 409
`janela_fechada` com campo **visível** e motivo; chamado resolvido
**não** impede complementar; reserva encerrada permanece legível.

**Independent Test**: os três códigos HTTP e a UI da janela fechada
(campo visível, botão inerte, motivo na tela).

### Tests (escrever e ver falhar)

- [X] T042 [P] [US5] Estender
  `testes/integracao/test_resposta_recepcao.py`: GET/POST de reserva de
  outro `id_hotel` → 404 (não 403). Rodar e **ver falhar**.

- [X] T043 [P] [US5] Estender o mesmo arquivo: POST `{"texto":"   "}`
  → 422; POST acima de 4096 → 422. Rodar e **ver falhar**.

- [X] T044 [P] [US5] Estender integração +
  `frontend/src/painel/TelaEstadia.test.tsx`: GET com
  `janela.aberta: false` e `janela.motivo` (`nunca_escreveu` |
  `sem_mensagem_recente`); POST → 409 `codigo: janela_fechada`; UI
  mantém o campo visível, Enviar inerte, motivo visível; chamado
  resolvido **não** fecha a janela; reserva `encerrado` com janela
  fechada: GET 200, POST 409. Rodar e **ver falhar**.

### Implementation

- [X] T045 [US5] Aplicar `id_hotel` em GET/POST, validação de
  tamanho/vazio e janela via `janela.py` em
  `app/modulos/conversa/service.py` e `schema.py`. Campo visível com
  motivo em `frontend/src/painel/TelaEstadia.tsx`. Rodar T042–T044 até
  ficarem **verdes**.

**Checkpoint**: erros honestos; janela fechada não esconde o campo;
complementar após chamado resolvido permanece possível.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T046 Verificar em `app/modulos/conversa/service.py` e no
  processador da fila que logs usam só identificadores (`id_mensagem`,
  `id_reserva`, `id_trabalho`) — nunca o texto. Asserção nos testes de
  T014/T015/T030 se ainda não houver.

- [X] T047 [P] Conferir `docs/04-schema.sql` e a revisão 0025:
  comentário explícito de que `enviar_resposta_recepcao` **não** tem
  UNIQUE por reserva; UNIQUE só `(id_mensagem)`.

- [X] T048 [P] Atualizar `docs/roteiro-de-teste.md` com o fluxo da
  Estadia: envio, estados **enviando / enviada / falhou**, falha
  visível, duplo clique, janela fechada com campo visível. Sem a
  palavra “extrato”.

- [X] T049 Rodar `uv run pytest testes/unitarios testes/integracao -q`
  e `npm --prefix frontend test -- --run`. Tudo verde. Nenhum teste
  desta fatia chama LLM nem WhatsApp reais.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: T001 imediatamente
- **Phase 2 (Foundational)**: T002–T013 bloqueiam as histórias.
  Pares teste→código: T003 após T002; T005 após T004; T007 após T006;
  T009 após T008; T011 após T010; T013 após T012
- **Phase 3 (US1)**: após Phase 2. T019–T025 após T014–T018
- **Phase 4 (US2)**: após GET da US1 (T022)
- **Phase 5 (US3)**: após POST/worker da US1 (T022–T023) e T009/T011
- **Phase 6 (US4)**: após router da US1
- **Phase 7 (US5)**: após serviço da US1 e janela (T007)
- **Phase 8**: depois das histórias do incremento

### User Story Dependencies

- **US1 (P1)**: após Foundational — MVP
- **US2 (P1)**: após GET da US1 — estados de entrega na conversa
- **US3 (P1)**: após POST/worker da US1 — falha + anti-duplo
- **US4 (P1)**: após router da US1
- **US5 (P1)**: após serviço da US1

### Parallel Opportunities

- T002, T004, T006, T008, T010, T012 em paralelo
- T014, T015, T016, T017, T018 em paralelo
- T026 e T027 em paralelo
- T030, T031, T032, T033 em paralelo
- T037, T038, T039 em paralelo
- T042, T043, T044 em paralelo
- T047 e T048 em paralelo

---

## Parallel Example: User Story 1

```text
T014 testes/unitarios/modulos/conversa/test_ler_conversa_da_estadia.py
T015 testes/unitarios/modulos/conversa/test_enviar_resposta_recepcao.py
T016 testes/integracao/test_resposta_recepcao.py
T017 frontend/src/painel/TelaEstadia.test.tsx
T018 frontend/src/painel/TelaFila.test.tsx
```

---

## Parallel Example: User Story 3

```text
T030 falha do worker (status_envio=falha, trabalho falha)
T031 409 texto_repetido + duas respostas distintas na mesma reserva
T032 botão Enviar disabled; Enter não posta
T033 rótulos falhou + POST 500 preserva o campo
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: T001
2. Phase 2: T002–T013 (0025 **sem** UNIQUE por reserva)
3. Phase 3: T014–T025
4. **STOP and VALIDATE**: lê, envia, worker entrega, fila atualiza

### Incremental Delivery

1. Foundation → US1 → validar
2. US2 → **enviando / enviada / falhou** na conversa
3. US3 → falha não perde texto; botão inerte + 409 `texto_repetido`
4. US4 → só recepção; chamado intacto
5. US5 → 404 / 422 / 409 `janela_fechada` com campo visível
6. Polish T046–T049

---

## Notes

- [P] = arquivos diferentes, sem depender de tarefa incompleta
- Commit por história, não por tarefa
- **Nunca** UNIQUE `(id_reserva, tipo)` para `enviar_resposta_recepcao`
- Relógio: `app.comum.relogio.agora`
- 24h da janela **não** vai para `parametro_hotel`
- A palavra "extrato" não existe neste produto
- Sem Playwright; fetch falso no Vitest; gateway e LLM falsos no pytest
