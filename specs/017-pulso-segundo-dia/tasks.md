---
description: "Task list for feature implementation"
---

# Tasks: Pulso do Segundo Dia

**Input**: Design documents from `/specs/017-pulso-segundo-dia/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de produção
antes de um teste que falhe pela ausência dela, e pelo motivo certo.

**Organization**: Tarefas agrupadas por história (US1–US11 e US6b), na ordem da spec.
Esquema (`enviar_pulso` / `registrar_resposta_pulso`), porta, fila, módulo `feedback`,
listagens e esqueleto do agendador entram na Foundational. A varredura que **agenda**
o pulso é a US1 (MVP). O gancho nos processadores F3.3–F3.5 é a US6b — não inverter
os recados operacionais já verdes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1–US11, US6b)

## Como ver os testes falharem nesta fatia

**Esquema.** `testes/integracao/test_conformidade_do_esquema.py` compara o banco
migrado com `docs/04-schema.sql`. Editar o documento **antes** da revisão deixa a
conformidade vermelha. A revisão `0016` a devolve ao verde.

**Garantias.** `testes/integracao/test_garantias_do_banco.py` prova tipo aceito e
unicidade. Sem a migração, o segundo `enviar_pulso` da mesma reserva entra — o
teste fica vermelho pelo motivo certo.

**CLI.** Hoje `--verificar-pulsos` não existe: o parser recusa. O unitário da US1
falha até a flag existir. `--uma-passagem` já é testado; esta fatia **estende** o
teste para também não chamar a varredura de pulso.

**Textos / feedback / varredura.** Unitários falham por `ImportError` /
`AttributeError` / `NotImplementedError` até o módulo existir.

**Gancho operacional.** Os testes da F3.3–F3.5 **permanecem**. Os da US6b usam
uma estadia **com** pulso já enviado; sem o gancho, nasce o recado operacional e
**não** nasce `avaliacao` — é isso que deve ficar vermelho.

---

## Phase 1: Setup

**Purpose**: constantes de teste, semeadura do prazo nas duas propriedades de
integração, esqueleto dos textos puros

- [X] T001 [P] Criar `testes/suporte/pulso.py` com constantes estáveis: chave
      `horas_minimas_para_pulso`, valor padrão `24`, `proibicoes_da_pergunta()`
      (`extrato`, `conta`, oferta, consentimento), `proibicoes_do_reconhecimento()`
      (afirmação de satisfação: `gostando`, `que bom`), `proibicoes_da_confirmacao_negativa()`
      (pergunta de horário de visita, `extrato`, `conta`, prazo de conserto). Sem
      segredo, sem rede
- [X] T002 [P] Em `testes/suporte/ambiente_de_acesso.py`, semear
      `horas_minimas_para_pulso=24` nas duas propriedades (junto das chaves já
      existentes). Sem isso, a varredura das integrações cai em `prazo_ausente` e
      afirma o caminho errado
- [X] T003 [P] Criar `app/modulos/conversa/texto_pulso.py` com docstring e as
      assinaturas `montar_pergunta_pulso(*, nome_completo: str) -> str`,
      `montar_reconhecimento_pulso() -> str` e
      `montar_confirmacao_pulso_negativo() -> str` levantando
      `NotImplementedError` até as histórias de recado
      ([contracts/mensageria-pulso.md](./contracts/mensageria-pulso.md))

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: revisão `0016`, porta `enviar_pulso`, fila dos dois tipos, módulo
`feedback`, `tem_reclamacao_aberta`, `listar_hospedados_sem_pulso`, bootstrap do
prazo, esqueleto da varredura e da allowlist. **Nenhuma rota HTTP nova.** A
varredura ainda não decide elegibilidade completa (isso é US1–US3/US8).

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. Ordem do esquema:
T004 → T005 → T007 → T008 (teste vermelho no documento, depois migração verde).

- [X] T004 Estender `testes/integracao/test_garantias_do_banco.py`: `INSERT` de
      trabalho `enviar_pulso` aceito pelo `ck_trabalho_tipo`; segundo `INSERT`
      da mesma reserva recusado por `uq_trabalho_enviar_pulso_reserva`;
      `registrar_resposta_pulso` aceito; segundo da mesma `id_mensagem` recusado
      por `uq_trabalho_registrar_resposta_pulso_mensagem`; segundo
      `avaliacao` `pulso_segundo_dia` da mesma reserva recusado por
      `uq_avaliacao_reserva_origem`. Rodar e **ver falhar** (FR-006, FR-016,
      Artigo IX, [data-model.md](./data-model.md))
- [X] T005 Aplicar o delta em `docs/04-schema.sql`: `enviar_pulso` e
      `registrar_resposta_pulso` em `ck_trabalho_tipo`; os dois índices únicos
      parciais; `horas_minimas_para_pulso` no `COMMENT` de `parametro_hotel`.
      **Não** alterar `vw_fila_do_dia`. Rodar
      `testes/integracao/test_conformidade_do_esquema.py` e **ver falhar**
- [X] T006 [P] Alinhar `docs/04-modelagem-de-dados.md`: primeiro escritor de
      `avaliacao` é o pulso; nota nula nesta fatia; `horas_minimas_para_pulso`
      semeado 24; unicidade de `enviar_pulso` por reserva. Pesquisa de checkout
      continua F4.1
- [X] T007 Criar `alembic/versions/sql/0016_pulso_segundo_dia.sql` — cópia
      congelada do delta da T005 **e** `INSERT` idempotente de
      `horas_minimas_para_pulso=24` para todo `hotel` que ainda não a tenha
- [X] T008 Criar `alembic/versions/0016_pulso_segundo_dia.py`
      (`down_revision = "0015_consumo_faturavel"`), `upgrade` executa o SQL
      congelado, `downgrade` restaura o `CHECK` da `0015` e derruba os dois
      índices (não apagar o parâmetro já semeado, ou documentar o recuo). T004
      e a conformidade verdes
- [X] T009 [P] Unitário em `testes/unitarios/portas/test_mensageria.py` (ou
      arquivo existente da porta): o Protocol declara `enviar_pulso` com
      `telefone_destino`, `primeiro_nome`, `corpo`, `id_mensagem`,
      `id_reserva`. **Ver falhar**
      ([contracts/mensageria-pulso.md](./contracts/mensageria-pulso.md))
- [X] T010 Acrescentar `enviar_pulso` ao Protocol em `app/portas/mensageria.py`.
      T009 verde. **Não** alterar `enviar_boas_vindas` nem `enviar_texto_sessao`
- [X] T011 [P] Estender `testes/unitarios/adaptadores/test_mensageria_falsa.py`:
      sucesso registra `tipo=pulso` distinguível de `boas_vindas` e `sessao`;
      modo falha levanta `FalhaDeEnvio` sem eco do corpo. **Ver falhar**
- [X] T012 Implementar `enviar_pulso` em `app/adaptadores/mensageria_falsa.py`.
      T011 verde. **Nunca** abre rede
- [X] T013 [P] Unitário em `testes/unitarios/fila/test_enfileirar_pulso.py`
      (criar): `enfileirar_enviar_pulso` e `enfileirar_registrar_resposta_pulso`
      existem e usam os tipos novos. **Ver falhar**
      ([contracts/fila-e-worker.md](./contracts/fila-e-worker.md))
- [X] T014 Acrescentar constantes, `enfileirar_enviar_pulso` e
      `enfileirar_registrar_resposta_pulso` em `app/fila/repository.py` e
      `app/fila/service.py`; incluir os dois tipos em `TIPOS_CONSUMIVEIS`. T013
      verde
- [X] T015 Unitário em `testes/unitarios/modulos/feedback/test_encerrar_pulso.py`
      (criar): `encerrar_pulso` grava `origem=pulso_segundo_dia`, nota nula,
      comentário informado; segunda chamada da mesma reserva não explode —
      trata unicidade como já encerrado. **Ver falhar**
      ([contracts/avaliacao-e-feedback.md](./contracts/avaliacao-e-feedback.md))
- [X] T016 Criar `app/modulos/feedback/repository.py` e
      `app/modulos/feedback/service.py` com `encerrar_pulso`,
      `encerrar_pulso_em_silencio` (mesmo INSERT) e `tem_avaliacao_de_pulso`.
      Sem import de `conversa`. T015 verde. Log só com ids
- [X] T017 [P] Unitário em `testes/unitarios/modulos/atendimento/test_reclamacao_aberta.py`
      (criar): `tem_reclamacao_aberta` verdadeiro só para `tipo=reclamacao` em
      `aberta`/`em_andamento`; falso para serviço, consumo, reclamação
      `resolvida`. **Ver falhar**
- [X] T018 Implementar `tem_reclamacao_aberta` em
      `app/modulos/atendimento/repository.py` e expor em
      `app/modulos/atendimento/service.py`. T017 verde
- [X] T019 [P] Unitário em `testes/unitarios/modulos/hospedagem/test_listar_sem_pulso.py`
      (criar): `listar_hospedados_sem_pulso` devolve hospedado com `checkin_em`
      e **sem** trabalho `enviar_pulso`; reserva com o trabalho não entra.
      **Ver falhar**
- [X] T020 Implementar `listar_hospedados_sem_pulso` em
      `app/modulos/hospedagem/repository.py` (espelho de
      `listar_hospedados_sem_boas_vindas`, incluindo
      `data_checkout_prevista`) e expor no service. T019 verde
- [X] T021 [P] Estender `testes/integracao/test_bootstrap.py`: propriedade nova
      nasce com `horas_minimas_para_pulso=24`. **Ver falhar**
- [X] T022 Acrescentar `PARAMETROS_PULSO_PADRAO` e a semeadura em
      `app/modulos/propriedade/service.py` (junto dos demais blocos). T021 verde
- [X] T023 Criar `verificar_pulsos_pendentes` em `worker/agendador.py` com
      assinatura de [contracts/agendador-de-pulso.md](./contracts/agendador-de-pulso.md)
      (`agora` instante ou callable, `CHAVE_MINIMO_PULSO`) levantando
      `NotImplementedError` até a US1
- [X] T024 Estender `testes/unitarios/worker/test_cli_worker.py`:
      `--uma-passagem` **não** chama a varredura de pulso; `--verificar-pulsos`
      chama e encerra. **Ver falhar**
- [X] T025 Em `worker/__main__.py`: flag `--verificar-pulsos`; loop horário
      chama `_rodar_verificacao_pulsos` depois de cadastros e boas-vindas;
      `--uma-passagem` inalterado. T024 verde. A função da T023 ainda pode
      levantar `NotImplementedError` neste passo — a US1 a implementa
- [X] T026 [P] Acrescentar ramos `enviar_pulso` e `registrar_resposta_pulso` em
      `worker/consumidor.py` delegando a funções nomeadas em `conversa.service`
      que ainda levantam `NotImplementedError` (processadores nas histórias).
      Sem isso o claim marcaria `tipo_desconhecido`

**Checkpoint**: esquema, porta falsa, fila, `feedback`, listagens e CLI
prontos. Nenhuma pergunta foi enviada ainda.

---

## Phase 3: User Story 1 - Uma pergunta no segundo dia (Priority: P1) 🎯 MVP

**Goal**: estadia hospedada no dia civil seguinte ao check-in real, com tempo
restante e sem reclamação, recebe exatamente uma pergunta gravada antes do
envio

**Independent Test**: `checkin_em` ontem UTC, checkout ≥ amanhã, prazo 24,
sem reclamação → `--verificar-pulsos` agenda um; `--uma-passagem` envia via
falsa (`tipo=pulso`); o texto é uma pergunta, só com prenome, sem oferta

### Tests for User Story 1

- [X] T027 [P] [US1] Unitário em `testes/unitarios/modulos/conversa/test_texto_pulso.py`
      (criar): `montar_pergunta_pulso` contém uma pergunta, só o primeiro nome
      como dado pessoal, passa em `proibicoes_da_pergunta()`, sem quebra de
      linha/tabulação/>4 espaços/vazio. **Ver falhar**
- [X] T028 [P] [US1] Unitário em `testes/unitarios/worker/test_verificar_pulsos.py`
      (criar): com relógio no dia seguinte ao `checkin_em`, prazo 24, checkout
      daqui a ≥1 dia, sem reclamação, a varredura agenda exatamente um
      `enviar_pulso` + mensagem pendente; no mesmo dia do check-in, zero.
      **Ver falhar** (FR-001, FR-002, FR-007)
- [X] T029 [P] [US1] Integração em `testes/integracao/test_pulso_segundo_dia.py`
      (criar): varredura **não** chama a porta; `--uma-passagem` envia
      `tipo=pulso`. **Ver falhar**

### Implementation for User Story 1

- [X] T030 [US1] Implementar `montar_pergunta_pulso` em
      `app/modulos/conversa/texto_pulso.py`. T027 verde
- [X] T031 [US1] Implementar `verificar_pulsos_pendentes` em
      `worker/agendador.py`: listar, filtrar segundo dia + prazo (mínimo só o
      caminho feliz da US1; reclamação/prazo ausente entram nas US2/US8),
      montar texto, INSERT mensagem + `enfileirar_enviar_pulso`. Colisão de
      único → já agendado. T028 verde
- [X] T032 [US1] Implementar `processar_trabalho_enviar_pulso` em
      `app/modulos/conversa/service.py`: reavaliar elegibilidade mínima (ainda
      hospedado, ainda sem avaliação); chamar `enviar_pulso`; marcar enviada.
      Ligar o ramo da T026. T029 verde. Log só ids

**Checkpoint**: pergunta única no segundo dia, ponta a ponta com portas falsas

---

## Phase 4: User Story 2 - Reclamação aberta suprime (Priority: P1)

**Goal**: reclamação não resolvida bloqueia o pulso; toalha, consumo e leitura
humana não; reclamação resolvida libera se ainda elegível

**Independent Test**: mesma estadia da US1 + reclamação `aberta` → 0 pulsos;
só serviço aberto → pulso sai; depois de resolver a reclamação, o pulso sai

- [X] T033 [P] [US2] Estender `testes/unitarios/worker/test_verificar_pulsos.py`:
      reclamação aberta → 0; serviço/consumo/flag humano → agenda; reclamação
      resolvida → agenda. **Ver falhar** (FR-005)
- [X] T034 [US2] Na varredura, chamar `atendimento.tem_reclamacao_aberta` e
      pular a reserva se verdadeiro. T033 verde. **Não** usar
      `precisa_atendimento_humano` como trava

**Checkpoint**: só conserto em aberto suprime

---

## Phase 5: User Story 3 - Sem tempo hábil não sai (Priority: P1)

**Goal**: horas restantes abaixo do mínimo da propriedade impedem o envio;
estadia de uma noite (saída prevista = hoje no segundo dia) é suprimida

**Independent Test**: checkout hoje → 0; checkout amanhã e mínimo 24 → agenda;
duas propriedades com mínimos diferentes divergem no mesmo par de datas

- [X] T035 [P] [US3] Estender `testes/unitarios/worker/test_verificar_pulsos.py`:
      `24 * (checkout − hoje)` abaixo do mínimo → 0; uma noite no segundo dia
      → 0; checkout amanhã com mínimo 24 → 1. **Ver falhar** (FR-004)
- [X] T036 [US3] Aplicar o cálculo de horas restantes na varredura e no
      reavaliar do processador. T035 verde

**Checkpoint**: pulso só com janela de correção

---

## Phase 6: User Story 4 - Nunca duas vezes (Priority: P1)

**Goal**: verificação nova, concorrência e silêncio do hóspede não geram
segunda pergunta nem lembrete

**Independent Test**: pulso já gravado + nova varredura → 0; dois INSERTs →
um no banco; silêncio → 0 lembretes

- [X] T037 [P] [US4] Estender `testes/integracao/test_pulso_segundo_dia.py` e
      `test_garantias_do_banco.py`: segunda varredura 0 extras; silêncio não
      cria `enviar_lembrete` nem segundo `enviar_pulso`. **Ver falhar**
      (FR-006, FR-013)
- [X] T038 [US4] Garantir que a varredura não tenta “compensar” pulso gravado
      e não enviado; nenhum tipo `enviar_lembrete` de pulso. T037 verde
      (unicidade da T008 já é a garantia durável)

**Checkpoint**: um recado de pulso por estadia, inclusive sob concorrência

---

## Phase 7: User Story 5 - Resposta negativa vira chamado (Priority: P1)

**Goal**: no dono do turno, sentimento negativo grava avaliação, confirma o
que vai acontecer (sem horário) **antes** de abrir uma reclamação

**Independent Test**: pulso enviado + resposta negativa classificada, intenção
fora de dúvida/pedido/reclamação → 1 avaliação, 1 chamado, confirmação no
histórico antes do INSERT, texto sem pergunta de visita

- [X] T039 [P] [US5] Unitário em `testes/unitarios/modulos/conversa/test_texto_pulso.py`:
      `montar_confirmacao_pulso_negativo` informa próximo passo (recepção /
      alguém vai falar), passa em `proibicoes_da_confirmacao_negativa()`.
      **Ver falhar**
- [X] T040 [P] [US5] Unitário em
      `testes/unitarios/modulos/conversa/test_registrar_resposta_pulso.py`
      (criar): negativo → enviada **depois** avaliação+chamado na mesma TX
      com enviada **antes** do INSERT da solicitação; 0 pergunta de horário;
      0 segundo chamado. **Ver falhar** (FR-010, FR-011)
- [X] T041 [P] [US5] Integração em `testes/integracao/test_pulso_segundo_dia.py`:
      classificar enfileira `registrar_resposta_pulso` (não executa o chamado
      no classificar); o processador abre 1 `reclamacao` visível em
      `GET /solicitacoes`. **Ver falhar**
- [X] T042 [US5] Implementar `montar_confirmacao_pulso_negativo`. T039 verde
- [X] T043 [US5] Em `processar_trabalho_classificar_mensagem`, se pulso
      aguardando e intenção **não** é dúvida/pedido/reclamação, enfileirar
      `registrar_resposta_pulso`. **Não** abrir chamado aqui
- [X] T044 [US5] Implementar `processar_trabalho_registrar_resposta_pulso` no
      ramo negativo: INSERT enviada → `feedback.encerrar_pulso` →
      `abrir_reclamacao` (janela nula) → `enviar_texto_sessao`. T040 e T041
      verdes. Idempotência se a enviada já existe

**Checkpoint**: recuperação com confirmação antes de tramitar, sem horário

---

## Phase 8: User Story 6 - Positivo, neutro ou silêncio (Priority: P1)

**Goal**: positivo e neutro gravam avaliação, mandam o **mesmo** reconhecimento
sem afirmar satisfação, zero chamado; silêncio não cria nada

**Independent Test**: positivo e neutro → mesmo corpo, 0 chamados, 1 avaliação;
sem resposta do hóspede → 0 avaliações, 0 lembretes

- [X] T045 [P] [US6] Unitário em `testes/unitarios/modulos/conversa/test_texto_pulso.py`:
      `montar_reconhecimento_pulso` passa em `proibicoes_do_reconhecimento()`;
      positivo e neutro usam a **mesma** função (um só texto). **Ver falhar**
      (FR-012)
- [X] T046 [P] [US6] Estender
      `testes/unitarios/modulos/conversa/test_registrar_resposta_pulso.py`:
      positivo e neutro → 1 avaliação, 0 `solicitacao`, mesmo corpo enviado.
      **Ver falhar**
- [X] T047 [US6] Implementar `montar_reconhecimento_pulso` e o ramo
      positivo/neutro do processador. T045 e T046 verdes. Silêncio: nenhum
      trabalho `registrar_resposta_pulso` sem mensagem do hóspede (já coberto
      pela US4)

**Checkpoint**: neutro = positivo no recado; só negativo chama equipe

---

## Phase 9: User Story 6b - Pedido ou dúvida não é engolido (Priority: P1)

**Goal**: na janela do pulso, F3.3–F3.5 correm; no máximo um recado; o pulso
fecha em silêncio; reclamação técnica não ganha segundo chamado

**Independent Test**: pulso enviado + toalha → confirmação de pedido, 0
“obrigado”, avaliação gravada; + dúvida coberta → resposta do catálogo, 0
obrigado; + reclamação técnica → 1 chamado e a confirmação da F3.5

- [X] T048 [P] [US6b] Unitário em
      `testes/unitarios/modulos/conversa/test_encerrar_pulso_operacional.py`
      (criar): após processar pedido/dúvida/reclamação **com** pulso
      aguardando, existe avaliação e **não** existe enviada de reconhecimento
      de pulso; reclamação técnica → 1 solicitação. **Ver falhar** (FR-009,
      FR-009b)
- [X] T049 [P] [US6b] Integração em `testes/integracao/test_pulso_segundo_dia.py`
      (ou estender `test_registrar_pedido` / `test_resolver` só com pulso
      pré-enviado): um recado ao hóspede. **Ver falhar**
- [X] T050 [US6b] No fim de `processar_trabalho_responder_duvida`,
      `processar_trabalho_registrar_pedido` e
      `processar_trabalho_abrir_chamado_reclamacao`, chamar
      `feedback.encerrar_pulso_em_silencio`; se sentimento `negativo` e a
      mensagem ainda não originou reclamação, `abrir_reclamacao` sem recado
      novo. Sem pulso aguardando, no-op. T048 e T049 verdes. Testes F3.3–F3.5
      **permanecem**

**Checkpoint**: toalha e café não morrem no pulso; um recado por mensagem

---

## Phase 10: User Story 7 - Irreconhecível vai para humano (Priority: P1)

**Goal**: polaridade falha na janela do pulso preserva a mensagem, sinaliza a
recepção, encerra o pulso (avaliação nota nula), sem chamado e sem segunda
pergunta

**Independent Test**: classificar indisponível / formato inválido / sentimento
ausente com pulso aguardando → `precisa_atendimento_humano`, 0 chamado
automático, 0 segundo pulso, próxima mensagem já segue a estadia normal

- [X] T051 [P] [US7] Unitário em
      `testes/unitarios/modulos/conversa/test_pulso_irreconhecivel.py` (criar):
      falha de classificação com pulso aguardando chama `encerrar_pulso` e
      **não** enfileira `registrar_resposta_pulso` nem chamado. **Ver falhar**
      (FR-014, FR-015)
- [X] T052 [US7] No desfecho humano de `classificar_mensagem`, se pulso
      aguardando, encerrar avaliação (nota nula, comentário) e reusar o sinal
      já existente na fila do dia. T051 verde. Neutro classificado **não**
      entra neste ramo (US6)

**Checkpoint**: na dúvida, humano vê; a interceptação fecha

---

## Phase 11: User Story 8 - Mínimo é da propriedade (Priority: P1)

**Goal**: alterar `horas_minimas_para_pulso` muda o desfecho na verificação
seguinte; chave ausente/inválida não envia e não inventa 24

**Independent Test**: mínimo 48 com checkout amanhã → 0; apagar a chave → 0 e
log `prazo_ausente`; hotel novo via bootstrap já tem 24 (já T021)

- [X] T053 [P] [US8] Estender `testes/unitarios/worker/test_verificar_pulsos.py`:
      dois hotéis, mínimos 24 e 48, mesmo par de datas → só o de 24 agenda;
      chave ausente ou `"abc"` → 0 e log `prazo_ausente` sem o texto da
      pergunta. **Ver falhar** (FR-003)
- [X] T054 [US8] Cache de prazo por hotel na varredura (`_inteiro_positivo` ≥ 1,
      padrão F1.4). T053 verde. **Nenhum** `24` no verificador

**Checkpoint**: Artigo XIII cumprido

---

## Phase 12: User Story 9 - Falha de envio não duplica (Priority: P1)

**Goal**: falha depois de gravar retoma o mesmo trabalho se ainda elegível;
janela fechada → conclui sem enviar; falha de gravação → zero pergunta ao
hóspede

**Independent Test**: `FalhaDeEnvio` com estadia ainda elegível → 1 recado, 2ª
tentativa do mesmo id; depois reclamação aberta ou horas esgotadas → 0 envio
novo, reserva intacta

- [X] T055 [P] [US9] Unitário em
      `testes/unitarios/modulos/conversa/test_enviar_pulso.py` (criar): falha
      de porta não apaga o trabalho; reprocessar ainda elegível chama a porta
      de novo; inelegível marca `concluido` **sem** chamar a porta. **Ver
      falhar** (FR-008)
- [X] T056 [US9] No processador `enviar_pulso`, reavaliar elegibilidade
      completa (US2+US3+hospedado) antes da porta; inelegível → `concluido`
      sem envio, log sem texto. T055 verde. Reagendar só `FalhaDeEnvio`

**Checkpoint**: perda tolerável fora da janela; nenhum segundo pulso distinto

---

## Phase 13: User Story 10 - Hotel A não pulsa hotel B (Priority: P1)

**Goal**: prazo, reclamação e trabalho não atravessam propriedade

**Independent Test**: duas propriedades, uma estadia elegível em cada;
reclamação só em A não suprime B; avaliação/chamado de A invisíveis em B

- [X] T057 [P] [US10] Integração em `testes/integracao/test_pulso_segundo_dia.py`
      usando `ambiente_de_acesso` (dois hotéis): isolamento de varredura,
      avaliação e chamado. **Ver falhar** (FR-017)
- [X] T058 [US10] Conferir que listagem, prazo e `abrir_reclamacao` usam
      `id_hotel` da reserva/trabalho. T057 verde

**Checkpoint**: Artigo XIV

---

## Phase 14: User Story 11 - Conteúdo não vaza em log (Priority: P2)

**Goal**: pergunta, resposta, reconhecimento e confirmação nunca aparecem no
log operacional

**Independent Test**: capturar logs nos desfechos enviar, suprimir, responder e
falhar — só ids, hotel, códigos

- [X] T059 [P] [US11] Estender os unitários da varredura, do envio e do
      registrar resposta: o handler de log não contém o corpo. **Ver falhar**
      se algum `logger.info` interpolar texto (FR-018)
- [X] T060 [US11] Trocar qualquer log restante por identificadores
      (`id_reserva`, `id_trabalho`, `prazo_ausente`). T059 verde

**Checkpoint**: Artigo VIII no pulso

---

## Phase 15: Polish & Cross-Cutting Concerns

**Purpose**: estado do projeto, inventário F3.2 inalterado, quickstart

- [X] T061 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F3.8 concluída;
      próxima F4.1; decisões (agendador sem APScheduler, módulo `feedback`,
      um recado por mensagem, neutro = positivo, só reclamação suprime,
      `horas_minimas_para_pulso=24`). Sem inventar tela
- [X] T062 [P] Confirmar que os testes da F3.2 (classificar não executa
      dúvida/pedido/reclamação) e os caminhos felizes F3.3–F3.5 **sem** pulso
      aguardando continuam verdes
- [X] T063 Percorrer [quickstart.md](./quickstart.md) contra a suíte
      (`pytest testes/unitarios -q` e `pytest testes/integracao -q -k pulso`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: depende do Setup — **bloqueia** todas as histórias
- **US1**: depois da Foundational — MVP
- **US2, US3, US8**: filtros da mesma varredura; podem seguir US1 em sequência
  (mesmo `worker/agendador.py`)
- **US4**: unicidade já na Foundational; testes de silêncio depois da US1
- **US5 → US6**: processador `registrar_resposta_pulso` (ramos negativo depois
  positivo/neutro)
- **US6b**: depois da US5 (precisa `encerrar_pulso` e `abrir_reclamacao` sem
  segundo recado); gancho nos três processadores existentes
- **US7**: depois da US5 (classificar já sabe “pulso aguardando”)
- **US9**: depois de US2+US3 (reavaliar elegibilidade completa no envio)
- **US10, US11**: depois dos caminhos felizes
- **Polish**: no fim

### User Story Dependencies

- **US1**: nenhuma outra história
- **US2 / US3 / US8**: US1 (a varredura existe)
- **US4**: US1 + índices da Foundational
- **US5**: US1 (pulso enviado)
- **US6**: US5 (mesmo processador)
- **US6b**: US1 + US5 (avaliação e regra de um recado)
- **US7**: US1 + US5
- **US9**: US1 + US2 + US3
- **US10 / US11**: caminhos de envio e resposta já existem

### Within Each User Story

- Teste primeiro; **ver falhar pelo motivo certo**; implementar o mínimo;
  verde; só então a próxima

### Parallel Opportunities

- T001, T002, T003
- T009 // T011 // T013 // T015 // T017 // T019 // T021
- T027 // T028 // T029
- T039 // T040 // T041
- T045 // T046
- T048 // T049
- T061 // T062

Não paralelizar tarefas no mesmo arquivo (`worker/agendador.py`,
`conversa/service.py`, `texto_pulso.py`).

---

## Parallel Example: User Story 1

```bash
# Testes da US1 (arquivos distintos):
Task: "test_texto_pulso.py pergunta"
Task: "test_verificar_pulsos.py segundo dia"
Task: "test_pulso_segundo_dia.py integração envio"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Setup + Foundational
2. US1 (varredura + envio da pergunta)
3. **Parar e validar** com o Independent Test da US1

### Incremental Delivery

1. US2 + US3 + US8 — a pergunta só sai na janela certa
2. US4 — teto de um
3. US5 + US6 — resposta dona do turno
4. US6b + US7 — operacional e humano
5. US9 + US10 + US11 — falha, isolamento, log
6. Polish e estado do projeto

### Suggested MVP scope

Só US1: o hotel pergunta uma vez no segundo dia. Sem isso o resto não tem
mensagem para responder. US2/US3 são o que impede o pulso de virar deboche —
tratar em seguida, antes de abrir chamado na US5.
