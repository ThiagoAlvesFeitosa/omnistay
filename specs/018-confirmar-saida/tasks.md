---
description: "Task list for feature implementation"
---

# Tasks: Confirmar Saída e Pesquisa

**Input**: Design documents from `/specs/018-confirmar-saida/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de
produção antes de um teste que falhe pela ausência dela, e pelo motivo certo.

**Organization**: Tarefas agrupadas por história (US1–US11), na ordem da spec.
Esquema (`enviar_pesquisa_saida` / `interpretar_pesquisa_saida`), portas, fila,
matriz de consentimento e semeadura do prazo entram na Foundational. O clique
`POST /reservas/{id}/saida` é a US1 (MVP). A pesquisa de ida é a US2. A
interpretação da resposta (US5) **não** passa por `classificar_mensagem`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1–US11)

## Como ver os testes falharem nesta fatia

**Esquema.** `testes/integracao/test_conformidade_do_esquema.py` compara o banco
migrado com `docs/04-schema.sql`. Editar o documento **antes** da revisão deixa
a conformidade vermelha. A revisão `0017` a devolve ao verde.

**Garantias.** `testes/integracao/test_garantias_do_banco.py` prova tipo aceito
e unicidade. Sem a migração, o segundo `enviar_pesquisa_saida` da mesma
reserva entra — o teste fica vermelho pelo motivo certo.

**Matriz.** Acrescentar `ler_consentimento` e `registrar_consentimento` em
`OPERACOES_ESPERADAS` **antes** de editar `politica.py` deixa
`test_matriz_completa_bate_com_o_contrato` vermelho.

**Rotas.** `testes/integracao/test_rotas_protegidas.py` varre o que está
registrado: cada rota nova passa a exigir `401` sem cookie. **Não** editar
`ROTAS_PUBLICAS`.

**Serviços / portas.** Unitários falham por `ImportError` / `AttributeError` /
`NotImplementedError` até a função existir.

**Webhook.** Os testes da F3.1 (`sem_reserva` sem estadia ativa) **permanecem**.
Os da US5 usam reserva **encerrada com pesquisa pendente**; sem o ramo novo,
continuam `sem_reserva` — é isso que deve ficar vermelho.

---

## Phase 1: Setup

**Purpose**: constantes de teste, semeadura do prazo nas duas propriedades de
integração, esqueleto do texto da pesquisa

- [X] T001 [P] Criar `testes/suporte/pesquisa_saida.py` com constantes estáveis:
      chave `horas_atribuicao_pesquisa_saida`, valor padrão `24`,
      `proibicoes_da_pesquisa()` (`extrato`, `conta`, oferta, desconto, lista
      de pedidos). Sem segredo, sem rede
- [X] T002 [P] Em `testes/suporte/ambiente_de_acesso.py`, semear
      `horas_atribuicao_pesquisa_saida=24` nas duas propriedades (junto das
      chaves já existentes). Sem isso, a US5 das integrações cai em
      `prazo_ausente` e afirma o caminho errado
- [X] T003 [P] Criar `app/modulos/conversa/texto_pesquisa_saida.py` com
      docstring e a assinatura
      `montar_texto_pesquisa_saida(*, nome_completo: str) -> str` levantando
      `NotImplementedError` até a US2
      ([contracts/portas-pesquisa.md](./contracts/portas-pesquisa.md))

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: revisão `0017`, portas, fila dos dois tipos, duas operações de
consentimento, bootstrap do prazo, esqueleto dos processadores e contratos
HTTP. Nenhuma rota de saída ainda confirma. A visão ganha as colunas; o
mapeamento JSON entra aqui para a US4 não reinventar o schema.

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. Ordem do esquema:
T004 → T005 → T007 → T008 (teste vermelho no documento, depois migração verde).

- [X] T004 Estender `testes/integracao/test_garantias_do_banco.py`: `INSERT` de
      trabalho `enviar_pesquisa_saida` aceito pelo `ck_trabalho_tipo`; segundo
      `INSERT` da mesma reserva recusado por
      `uq_trabalho_enviar_pesquisa_saida_reserva`; `interpretar_pesquisa_saida`
      aceito; segundo da mesma `id_mensagem` recusado por
      `uq_trabalho_interpretar_pesquisa_saida_mensagem`; `avaliacao` origem
      `checkout` **sem nota** recusada pelo CHECK novo; pulso com nota nula
      **continua** aceito. Rodar e **ver falhar** (FR-008, FR-021, Artigo IX,
      [data-model.md](./data-model.md))
- [X] T005 Aplicar o delta em `docs/04-schema.sql`: os dois tipos em
      `ck_trabalho_tipo`; os dois índices únicos parciais; CHECK
      `origem <> 'checkout' OR nota IS NOT NULL` em `avaliacao`; colunas
      `saida_nao_confirmada` e `pesquisa_saida_leitura_humana` na
      `vw_fila_do_dia`; filtro da visão mantém `encerrado` **só** com leitura
      humana da pesquisa; `horas_atribuicao_pesquisa_saida` no `COMMENT` de
      `parametro_hotel`. Rodar
      `testes/integracao/test_conformidade_do_esquema.py` e **ver falhar**
- [X] T006 [P] Alinhar `docs/04-modelagem-de-dados.md`: primeiro escritor de
      `consentimento`; avaliação origem `checkout` com nota obrigatória;
      `horas_atribuicao_pesquisa_saida` semeado 24; comentário da visão
      (exceção F1.1). Lista de pedidos continua F4.2
- [X] T007 Criar `alembic/versions/sql/0017_confirmar_saida.sql` — cópia
      congelada do delta da T005 **e** `INSERT` idempotente de
      `horas_atribuicao_pesquisa_saida=24` para todo `hotel` que ainda não a
      tenha. Recriar a visão por inteiro (padrão `0008`/`0011`)
- [X] T008 Criar `alembic/versions/0017_confirmar_saida.py`
      (`down_revision = "0016_pulso_segundo_dia"`), `upgrade` executa o SQL
      congelado, `downgrade` restaura o `CHECK` da `0016`, derruba os dois
      índices, recria a visão da `0016` e remove o CHECK de nota do checkout
      (não apagar o parâmetro já semeado, ou documentar o recuo). T004 e a
      conformidade verdes
- [X] T009 Acrescentar em `testes/unitarios/modulos/acesso/test_politica.py`:
      `ler_consentimento` e `registrar_consentimento` para `recepcao` e
      `gestor`, recusados para `staff`; `confirmar_fase_da_reserva` continua
      só `recepcao`. Incluir as duas em `OPERACOES_ESPERADAS` e **ver falhar**
      ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))
- [X] T010 Acrescentar as duas operações a `OPERACOES` em
      `app/modulos/acesso/politica.py`. T009 verde
- [X] T011 [P] Unitário em `testes/unitarios/adaptadores/test_mensageria_falsa.py`
      (estender): o Protocol declara `enviar_pesquisa_saida` com
      `telefone_destino`, `primeiro_nome`, `corpo`, `id_mensagem`,
      `id_reserva`; sucesso registra `tipo=pesquisa_saida` distinguível de
      `pulso`/`boas_vindas`/`sessao`; modo falha levanta `FalhaDeEnvio` sem
      eco do corpo. **Ver falhar**
      ([contracts/portas-pesquisa.md](./contracts/portas-pesquisa.md))
- [X] T012 Acrescentar `enviar_pesquisa_saida` ao Protocol em
      `app/portas/mensageria.py` e implementar em
      `app/adaptadores/mensageria_falsa.py`. T011 verde. **Nunca** abre rede.
      Adaptador WhatsApp: método no Protocol (pode levantar
      `NotImplementedError` até haver template — nenhum teste o instancia)
- [X] T013 [P] Unitário em `testes/unitarios/adaptadores/test_llm_falso.py`
      (estender): `interpretar_pesquisa_saida` devolve
      `ResultadoPesquisaSaida` (desfecho, nota, comentario, aceite) conforme
      fixture; modo falha levanta `FalhaDeExtracao` sem eco do texto.
      **Ver falhar**
- [X] T014 Acrescentar `ResultadoPesquisaSaida` e
      `interpretar_pesquisa_saida` em `app/portas/llm.py`; implementar em
      `app/adaptadores/llm_falso.py`. T013 verde
- [X] T015 [P] Unitário em `testes/unitarios/fila/test_enfileirar_pesquisa_saida.py`
      (criar): `enfileirar_enviar_pesquisa_saida` e
      `enfileirar_interpretar_pesquisa_saida` existem e usam os tipos novos.
      **Ver falhar** ([contracts/fila-e-worker.md](./contracts/fila-e-worker.md))
- [X] T016 Acrescentar constantes, os dois `enfileirar_*` em
      `app/fila/repository.py` e `app/fila/service.py`; incluir os dois tipos
      em `TIPOS_CONSUMIVEIS` / `reclamar_proximo`. T015 verde
- [X] T017 [P] Estender `testes/integracao/test_bootstrap.py`: propriedade nova
      nasce com `horas_atribuicao_pesquisa_saida=24`. **Ver falhar**
- [X] T018 Acrescentar `PARAMETROS_PESQUISA_SAIDA_PADRAO` e a semeadura em
      `app/modulos/propriedade/service.py`. T017 verde
- [X] T019 [P] Contratos HTTP: `SaidaResposta` (`id_reserva`, `status`,
      `checkout_em`, `pesquisa`) e campos `saida_nao_confirmada` /
      `pesquisa_saida_leitura_humana` (default falso) em `ItemFilaDoDia` em
      `app/modulos/hospedagem/schema.py`
      ([contracts/api-de-saida.md](./contracts/api-de-saida.md))
- [X] T020 Mapear as duas colunas novas em
      `app/modulos/hospedagem/service.py` (`ler_fila_do_dia`) e no `SELECT`
      de `app/modulos/hospedagem/repository.py`. Sem isso a US4 quebra no
      schema Pydantic
- [X] T021 [P] Acrescentar ramos `enviar_pesquisa_saida` e
      `interpretar_pesquisa_saida` em `worker/consumidor.py` delegando a
      funções nomeadas em `conversa.service` que ainda levantam
      `NotImplementedError` (processadores nas US2/US5). Sem isso o claim
      marcaria `tipo_desconhecido`

**Checkpoint**: esquema, portas falsas, fila, matriz e CLI de consumo
prontos. Nenhuma saída foi confirmada ainda.

---

## Phase 3: User Story 1 - Confirmar a saída no painel (Priority: P1) 🎯 MVP

**Goal**: recepção confirma a saída de uma reserva hospedada da própria
propriedade; a reserva passa a `encerrado` e o instante real fica em
`checkout_em`; nasce a pendência durável da pesquisa

**Independent Test**: cookie de recepção + `POST /reservas/{id}/saida` numa
hospedada → `200`, `status=encerrado`, `checkout_em` ≈ agora (≠ data
prevista), `pesquisa=agendada`, 1 `trabalho` `enviar_pesquisa_saida` + 1
mensagem pendente. Reclamação aberta ou consumo pendente **não** mudam o 200

### Tests for User Story 1

- [X] T022 [P] [US1] Unitário em
      `testes/unitarios/modulos/hospedagem/test_confirmar_saida.py` (criar):
      hospedada → `encerrado` e `checkout_em` gravado; chamado aberto ou
      consumo pendente não impedem; agenda pesquisa (`agendada`). **Ver
      falhar** (FR-001, FR-002, FR-005, FR-006)
- [X] T023 [P] [US1] Integração em
      `testes/integracao/test_confirmar_saida.py` (criar): `POST` com cookie
      de recepção → 200 + linha de trabalho + mensagem; o `POST` **não**
      chama a porta de mensageria. **Ver falhar**
      ([contracts/api-de-saida.md](./contracts/api-de-saida.md))

### Implementation for User Story 1

- [X] T024 [US1] Implementar `confirmar_saida` em
      `app/modulos/hospedagem/repository.py` (`UPDATE … WHERE status =
      'hospedado'` + `checkout_em = now()`) e no service: titular, chamar
      `conversa.agendar_pesquisa_saida` (esqueleto que INSERT mensagem +
      `enfileirar_enviar_pesquisa_saida`, texto placeholder até a US2;
      colisão de único → `ja_agendada`). Exceções `ReservaNaoEncontrada` /
      `SaidaNaoPermitida` no padrão da chegada. T022 verde. Log só ids
- [X] T025 [US1] Rota `POST /reservas/{id_reserva}/saida` em
      `app/modulos/hospedagem/router.py` com
      `exigir_operacao("confirmar_fase_da_reserva")`, transação, 404/409.
      T023 verde. **Não** editar `ROTAS_PUBLICAS`

**Checkpoint**: clique encerra e grava a pesquisa; envio ainda não acontece

---

## Phase 4: User Story 2 - Disparar a pesquisa curta (Priority: P1)

**Goal**: o worker envia exatamente uma mensagem com nota, comentário
opcional e pergunta de aceite; sem oferta, sem “extrato”/“conta”, sem lista
de pedidos; só o prenome como dado pessoal

**Independent Test**: após US1, `--uma-passagem` envia via falsa
(`tipo=pesquisa_saida`); o corpo tem as três partes e passa em
`proibicoes_da_pesquisa()`

### Tests for User Story 2

- [X] T026 [P] [US2] Unitário em
      `testes/unitarios/modulos/conversa/test_texto_pesquisa_saida.py`
      (criar): `montar_texto_pesquisa_saida` pede nota 1–5, comentário
      opcional e aceite de comunicações futuras; só o primeiro nome; passa
      em `proibicoes_da_pesquisa()`. **Ver falhar** (FR-010, FR-011, FR-012)
- [X] T027 [P] [US2] Integração em `testes/integracao/test_confirmar_saida.py`:
      `--uma-passagem` (ou processador direto) marca enviada via falsa
      `tipo=pesquisa_saida`. **Ver falhar** (FR-013, FR-014)

### Implementation for User Story 2

- [X] T028 [US2] Implementar `montar_texto_pesquisa_saida` e usar no
      `agendar_pesquisa_saida` (substituir placeholder). T026 verde
- [X] T029 [US2] Implementar `processar_trabalho_enviar_pesquisa_saida` em
      `app/modulos/conversa/service.py`: chamar
      `gateway.enviar_pesquisa_saida`; marcar enviada. Ligar o ramo da T021.
      T027 verde. Log só ids. **Não** enviar agradecimento

**Checkpoint**: pesquisa única no canal, ponta a ponta com porta falsa

---

## Phase 5: User Story 3 - Recusar confirmação inválida (Priority: P1)

**Goal**: não-hospedada, já encerrada ou cancelada → 409, status intacto, 0
pesquisas; segundo clique não cria segundo trabalho

**Independent Test**: cada estado recusado via `POST` → 409, `checkout_em`
inalterado (ou nulo), 0 `enviar_pesquisa_saida` novos

### Tests for User Story 3

- [X] T030 [P] [US3] Estender
      `testes/unitarios/modulos/hospedagem/test_confirmar_saida.py` e
      `testes/integracao/test_confirmar_saida.py`: `aguardando_cadastro`,
      `ficha_recebida`, `ficha_parcial`, `sem_cadastro_previo`, `encerrado`,
      `cancelada` → recusa; segundo `POST` em já encerrada → 409 e um só
      trabalho. **Ver falhar** (FR-003, FR-004)

### Implementation for User Story 3

- [X] T031 [US3] Completar motivos de `409` no router (espelho da chegada) e
      garantir que ramo recusado **não** chama `agendar_pesquisa_saida`.
      T030 verde

**Checkpoint**: máquina de estados respeitada no clique e no banco

---

## Phase 6: User Story 4 - Destacar saída vencida na fila (Priority: P1)

**Goal**: hospedada com `data_checkout_prevista` anterior a hoje aparece com
`saida_nao_confirmada`; prevista hoje, não; depois do clique o destaque some
(encerrada limpa sai da fila)

**Independent Test**: três reservas na fila — vencida hospedada, checkout
hoje, já encerrada limpa — só a primeira com o flag; flag distinto de
`chegada_nao_confirmada` e `boas_vindas_nao_enviadas`

### Tests for User Story 4

- [X] T032 [P] [US4] Integração em `testes/integracao/test_confirmar_saida.py`
      (ou estender teste da fila do dia): `GET /fila-do-dia` com os três
      casos; após `POST …/saida` o flag some. **Ver falhar** (FR-015, FR-016,
      FR-017)

### Implementation for User Story 4

- [X] T033 [US4] Conferir a expressão SQL da visão (T005/T007) e o mapeamento
      (T019/T020) contra T032. Ajustar só se o teste apontar divergência.
      T032 verde

**Checkpoint**: omissão do clique fica visível; confirmação a desliga

---

## Phase 7: User Story 5 - Registrar nota, comentário e aceite (Priority: P1)

**Goal**: resposta reconhecida vira avaliação origem `checkout` e, se o
aceite for sim/não, um INSERT de consentimento do titular
(`pesquisa_checkout`); silêncio não consente; nota alta não é opt-in;
ficha/hospedado no mesmo telefone não são engolidos

**Independent Test**: pesquisa enviada + texto que o `LLMFalso` devolve como
nota 5 + aceite sim → 1 `avaliacao` checkout, 1 `consentimento` concedido;
só nota → avaliação, 0 consentimento; silêncio → 0 e 0; telefone com
`aguardando_cadastro` nova → ficha, não pesquisa

### Tests for User Story 5

- [X] T034 [P] [US5] Unitário em
      `testes/unitarios/modulos/feedback/test_avaliacao_checkout.py` (criar):
      `gravar_avaliacao_checkout` insere origem `checkout` com nota 1–5;
      segunda nota da mesma reserva não duplica (unicidade); comentário
      posterior completa a mesma linha. **Ver falhar** (FR-021)
- [X] T035 [P] [US5] Unitário em
      `testes/unitarios/modulos/hospedagem/test_consentimento.py` (criar):
      `registrar_consentimento_pesquisa` INSERT `origem=pesquisa_checkout`
      no titular; nunca UPDATE; silêncio/aceite nulo não insere. **Ver
      falhar** (FR-022, FR-023)
- [X] T036 [P] [US5] Unitário em
      `testes/unitarios/modulos/conversa/test_receber_mensagem.py` (estender):
      ordem ficha → hospedado → encerrada com pesquisa incompleta; encerrada
      sem pesquisa pendente grava mensagem sem trabalho. **Ver falhar**
      (FR-027)
- [X] T037 [P] [US5] Unitário em
      `testes/unitarios/modulos/conversa/test_interpretar_pesquisa_saida.py`
      (criar): completo / só nota / só aceite / silêncio da pergunta de
      aceite; nota fora de 1–5 descartada; 0 segunda pesquisa; 0 lembrete.
      **Ver falhar** (FR-024, FR-025, FR-032)
- [X] T038 [P] [US5] Integração em
      `testes/integracao/test_pesquisa_saida.py` (criar): webhook depois do
      checkout + fixture completo → avaliação + consentimento; prazo 24
      semeado. **Ver falhar**

### Implementation for User Story 5

- [X] T039 [US5] `gravar_avaliacao_checkout` em
      `app/modulos/feedback/repository.py` e `service.py`. Sem import de
      `conversa`. T034 verde
- [X] T040 [US5] `registrar_consentimento_pesquisa` + leitura do titular em
      `app/modulos/hospedagem/repository.py` e `service.py`. T035 verde
- [X] T041 [US5] `resolver_reserva_encerrada_pesquisa` em
      `app/modulos/conversa/repository.py`; ramo 3–4 em
      `receber_evento_entrada`. T036 verde. Testes F3.1 de `sem_reserva`
      **sem** pesquisa pendente permanecem
- [X] T042 [US5] Implementar
      `processar_trabalho_interpretar_pesquisa_saida`: ler prazo
      (`horas_atribuicao_pesquisa_saida`) com relógio injetável; chamar a
      porta; validar nota; orquestrar T039/T040; gravar
      `classificacao_bruta` (`tipo=pesquisa_saida`). Ligar o ramo da T021.
      T037 e T038 verdes. Sem backoff. Log só ids

**Checkpoint**: pesquisa respondida vira dado; silêncio não inventa opt-in

---

## Phase 8: User Story 6 - Irreconhecível vai para humano (Priority: P1)

**Goal**: extração falha / formato inválido / prazo ausente preserva a
mensagem, sinaliza `pesquisa_saida_leitura_humana`, encerrada permanece na
fila, zero nota/consentimento inventados, zero segunda pesquisa

**Independent Test**: `FalhaDeExtracao` ou desfecho `irreconhecivel` com
pesquisa incompleta → flag na fila, 0 avaliação checkout nova (se nada
válido), 0 consentimento; chave de prazo apagada → mesmo sinal + log
`prazo_ausente`

### Tests for User Story 6

- [X] T043 [P] [US6] Estender
      `testes/unitarios/modulos/conversa/test_interpretar_pesquisa_saida.py`
      e `testes/integracao/test_pesquisa_saida.py`: irreconhecível, IA caída,
      prazo ausente/inválido → humano na fila, sem inventar, trabalho
      `concluido`. **Ver falhar** (FR-026)
- [X] T044 [US6] No processador: desfechos humano; janela vencida conclui
      **sem** humano e sem gravar (pesquisa simplesmente expirou). T043
      verde. Neutro/parcial reconhecido **não** entra neste ramo (US5)

**Checkpoint**: na dúvida, humano vê; silêncio de prazo vencido não enche a
fila

---

## Phase 9: User Story 7 - Consultar consentimento em data passada (Priority: P1)

**Goal**: GET devolve o estado vigente em `em` (omisso = agora); zero linhas
→ `concedido=false` sem `momento`; recepção e gestão ok; staff 403

**Independent Test**: aceite depois recusa → GET no meio devolve aceite; GET
agora devolve recusa; GET antes do primeiro devolve ausência

### Tests for User Story 7

- [X] T045 [P] [US7] Unitário em
      `testes/unitarios/modulos/hospedagem/test_consentimento.py`: vigente em
      três instantes (antes / entre / depois). **Ver falhar** (FR-028)
- [X] T046 [P] [US7] Integração em
      `testes/integracao/test_consentimento.py` (criar): GET com cookie
      recepção/gestão 200; staff 403; `em` omitido = agora.
      **Ver falhar**
      ([contracts/api-de-consentimento.md](./contracts/api-de-consentimento.md))

### Implementation for User Story 7

- [X] T047 [US7] `consultar_consentimento_vigente` no repository/service de
      `hospedagem` (hóspede só via reserva do `id_hotel`). T045 verde
- [X] T048 [US7] Rota `GET /hospedes/{id_hospede}/consentimento` em
      `app/modulos/hospedagem/router.py` com
      `exigir_operacao("ler_consentimento")`. Schema de resposta no
      `schema.py`. T046 verde. 404 uniforme para outro hotel

**Checkpoint**: “aceitava em março?” tem resposta sem apagar história

---

## Phase 10: User Story 8 - Revogar depois, sem apagar (Priority: P1)

**Goal**: POST insere nova linha (`painel` ou `solicitacao_titular`); linha
anterior intacta; staff recusado; origem `pesquisa_checkout` recusada nesta
rota

**Independent Test**: aceite da US5 + POST recusa → duas linhas; GET histórico
da US7 continua passando

### Tests for User Story 8

- [X] T049 [P] [US8] Estender
      `testes/unitarios/modulos/hospedagem/test_consentimento.py` e
      `testes/integracao/test_consentimento.py`: POST 201 append-only;
      `origem` inválida 422; staff 403; segundo evento não UPDATE.
      **Ver falhar** (FR-029)

### Implementation for User Story 8

- [X] T050 [US8] `registrar_consentimento_painel` no service (INSERT; origem
      só `painel` | `solicitacao_titular`) e
      `POST /hospedes/{id_hospede}/consentimento` com
      `exigir_operacao("registrar_consentimento")`. T049 verde

**Checkpoint**: revogação é história, não interruptor

---

## Phase 11: User Story 9 - Isolar por hotel e perfil (Priority: P1)

**Goal**: só recepção do próprio hotel confirma saída; gestão/staff 403;
hotel B 404 uniforme; consentimento idem

**Independent Test**: `ambiente_de_acesso` com dois hotéis — 0 mudanças no A
por sessão do B; gestão não confirma saída e lê consentimento

### Tests for User Story 9

- [X] T051 [P] [US9] Integração em `testes/integracao/test_confirmar_saida.py`
      e `test_consentimento.py`: 403 gestão/staff no `POST …/saida`; 404
      cruzado; GET consentimento gestão 200 / staff 403. **Ver falhar**
      (FR-018, FR-019, FR-020)

### Implementation for User Story 9

- [X] T052 [US9] Conferir `id_hotel` da sessão em confirmar, fila e
      consentimento (já no padrão da chegada). T051 verde. Sem revelar
      existência no 404

**Checkpoint**: Artigo XIV no checkout

---

## Phase 12: User Story 10 - Falha de envio não desfaz nem duplica (Priority: P1)

**Goal**: `FalhaDeEnvio` reagenda o mesmo trabalho; reserva permanece
`encerrado`; índice impede segunda pesquisa distinta

**Independent Test**: porta em modo falha após o clique → status encerrado,
1 trabalho, 2ª passagem retoma o mesmo id; dois INSERTs manuais → um no banco

### Tests for User Story 10

- [X] T053 [P] [US10] Unitário em
      `testes/unitarios/modulos/conversa/test_enviar_pesquisa_saida.py`
      (criar): falha de porta não reabre hospedado; reprocessar chama a
      porta de novo no mesmo id. **Ver falhar** (FR-007, FR-008)
- [X] T054 [US10] No processador, reagendar só `FalhaDeEnvio`; unicidade da
      T008 é a garantia durável. T053 verde. Integração: segundo clique já
      coberto na US3

**Checkpoint**: perda de entrega tolerável; checkout intacto

---

## Phase 13: User Story 11 - Conteúdo não vaza em log (Priority: P2)

**Goal**: pesquisa, resposta, comentário e aceite nunca aparecem no log
operacional

**Independent Test**: capturar logs nos desfechos confirmar, enviar,
responder, recusar, revogar e falhar — só ids, hotel, códigos

### Tests for User Story 11

- [X] T055 [P] [US11] Estender
      `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py` (e/ou os
      unitários desta fatia): handler não contém o corpo nem o comentário.
      **Ver falhar** se algum `logger.info` interpolar texto (FR-030)

### Implementation for User Story 11

- [X] T056 [US11] Trocar qualquer log restante por identificadores
      (`id_reserva`, `id_trabalho`, `prazo_ausente`, `saida_recusada`).
      T055 verde

**Checkpoint**: Artigo VIII na saída

---

## Phase 14: Polish & Cross-Cutting Concerns

**Purpose**: estado do projeto, regressão F3.1/F3.8, quickstart, FR-031

- [X] T057 [P] Estender os testes da F3.1/F3.8 que usam reserva encerrada
      **sem** pesquisa pendente: continuam `sem_reserva` ou pulso inerte;
      pulso **não** dispara para `encerrado`. Confirmar F3.3–F3.5 sem
      checkout continuam verdes
- [X] T058 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F4.1 concluída;
      próxima F4.2; decisões (clique reusa `confirmar_fase_da_reserva`,
      interpretar sem classificar, consentimento append-only, exceção da
      visão para leitura humana, `horas_atribuicao_pesquisa_saida=24`,
      lista de pedidos fora). Sem inventar tela
- [X] T059 [P] Garantir que nenhum texto/rota desta fatia usa “extrato” ou
      “conta” (varredura nos arquivos tocados + `proibicoes_da_pesquisa`)
      (FR-031)
- [X] T060 Percorrer [quickstart.md](./quickstart.md) contra a suíte
      (`pytest testes/unitarios -q` e
      `pytest testes/integracao -q -k "saida or consentimento or pesquisa"`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: depende do Setup — **bloqueia** todas as histórias
- **US1**: depois da Foundational — MVP
- **US2**: depois da US1 (há trabalho para enviar)
- **US3**: depois da US1 (mesmo `POST`; ramos de recusa)
- **US4**: Foundational (visão) + US1 (o clique desliga o destaque)
- **US5**: US2 (pesquisa enviada) — interpretação e webhook
- **US6**: US5 (mesmo processador; desfechos humano)
- **US7**: Foundational (matriz) — pode em paralelo com US1 se o hóspede
  já existir; na prática depois da US5 para ter um aceite da pesquisa
- **US8**: US7 (consulta prova que a revogação não apagou)
- **US9**: US1 + US7 (rotas já existem)
- **US10**: US2 (processador de envio)
- **US11**: caminhos felizes já logam
- **Polish**: no fim

### User Story Dependencies

- **US1**: nenhuma outra história
- **US2 / US3 / US10**: US1
- **US4**: US1 + colunas da Foundational
- **US5**: US2
- **US6**: US5
- **US7**: Foundational; melhor depois da US5
- **US8**: US7
- **US9**: US1 + US7
- **US11**: US1 + US2 + US5

### Within Each User Story

- Teste primeiro; **ver falhar pelo motivo certo**; implementar o mínimo;
  verde; só então a próxima

### Parallel Opportunities

- T001, T002, T003
- T011 // T013 // T015 // T017 // T019 // T021
- T022 // T023
- T026 // T027
- T034 // T035 // T036 // T037 // T038
- T045 // T046
- T057 // T058 // T059

Não paralelizar tarefas no mesmo arquivo (`hospedagem/service.py`,
`conversa/service.py`, `hospedagem/router.py`, `docs/04-schema.sql`).

---

## Parallel Example: User Story 1

```bash
# Testes da US1 (arquivos distintos):
Task: "test_confirmar_saida.py unitário"
Task: "test_confirmar_saida.py integração POST"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Setup + Foundational
2. US1 (clique → encerrado + pesquisa gravada)
3. **Parar e validar** com o Independent Test da US1

### Incremental Delivery

1. US2 — o hóspede recebe a pesquisa
2. US3 + US4 — recusa e destaque (o clique esquecido fica visível)
3. US5 + US6 — resposta e humano
4. US7 + US8 — consulta e revogação LGPD
5. US9 + US10 + US11 — isolamento, falha de envio, log
6. Polish e estado do projeto

### Suggested MVP scope

Só US1: a recepção encerra a estadia no painel e a intenção de enviar a
pesquisa fica gravada. Sem o clique nada dispara. US2 é o valor visível
ao hóspede — tratar em seguida, antes da interpretação (US5).
