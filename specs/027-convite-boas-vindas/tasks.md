---
description: "Task list for feature implementation"
---

# Tasks: Linha de convite no recado de boas-vindas

**Input**: Design documents from `/specs/027-convite-boas-vindas/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de
produção sem teste que falhe antes pelo motivo certo. Nenhum teste chama a
Graph/WhatsApp nem o PMS.

**Organization**: Tarefas agrupadas por história (US1–US4). Esquema
(`COMMENT` + semente nos hotéis já instalados) entra na Foundational.
US1 é o MVP (recepção grava o convite). US2 monta o recado e a tupla
de cinco. US3 prova omissão na fila e a recuperação. US4 fecha
bootstrap de propriedade nova.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US4)

## Como ver os testes falharem nesta fatia

**Esquema.** `test_comentario_de_parametro_hotel_cita_personalidade`
(ou o caso novo desta fatia) fica vermelho quando o `COMMENT` pede
`boas_vindas_convite` e a revisão `0023` ainda não rodou (ou o inverso).

**PUT de três campos.** `testes/integracao/test_boas_vindas_slots.py`
usa `_corpo()` sem `convite`. Assim que `BoasVindasEntrada` exigir o
campo, esses PUTs tomam `422` — vermelho certo até `_corpo` ganhar a
linha.

**Montagem.** `montar_texto_boas_vindas(...)` hoje tem quatro
parâmetros e termina com a frase fixa. O unitário novo exige parâmetro
`convite`, última linha igual a ele, aviso imediatamente antes, e a
frase `Quer saber mais alguma coisa da sua estadia?` **ausente**. Até
a assinatura mudar: `TypeError` ou asserção da frase antiga.

**Tupla.** `len(envio["variaveis"]) == 4` em
`test_boas_vindas_envio.py` e `test_ia_real_aviso.py` fica vermelho
quando o worker passar cinco valores — ou o contrário, se o teste já
exigir cinco e a porta ainda mandar quatro.

**Agendamento.** `SLOTS_OK` com três chaves: quando
`CHAVES_SLOTS_BOAS_VINDAS` em `conversa/service.py` incluir convite,
`test_slots_validos_inserem_mensagem_e_enfileiram` passa a devolver
`nao_enviada_slot_ausente` até o dict ganhar a quarta chave.

**Log.** `caplog` com o texto do convite no PUT ou no agendamento: se o
serviço logar o valor, o teste novo falha pelo motivo certo.

---

## Phase 1: Setup

**Purpose**: constantes. O monólito já existe; não criar pacote Python
novo. Sem tela React. Sem lib nova. Sem mudar a assinatura da porta
ainda (isso quebra o worker inteiro).

- [X] T001 [P] Acrescentar em `app/modulos/propriedade/service.py` as
      constantes `CHAVE_BOAS_VINDAS_CONVITE = "boas_vindas_convite"` e
      `SEMENTE_CONVITE_BOAS_VINDAS = "Pode perguntar por aqui sobre servicos, cardapio e horarios."`
      Sem validar, sem gravar, sem alterar `CHAVES_SLOTS_BOAS_VINDAS`
      ([research.md](./research.md) §1)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: semente nos hotéis já instalados e `COMMENT` alinhado ao
documento. Sem rota nova, sem mudar a montagem, sem tupla de cinco.

**⚠️ CRÍTICO**: US1 integração em hotel recém-criado pelo fixture ainda
precisa da semente no `_semear` (US1). Esta fase cobre quem já existia
na hora do `upgrade`. US2 não começa até o COMMENT estar verde — senão
o documento mente.

- [X] T002 Estender
      `testes/integracao/test_conformidade_do_esquema.py`: o
      `COMMENT` de `parametro_hotel` no banco migrado contém
      `boas_vindas_convite` (mesmo molde de
      `test_comentario_de_parametro_hotel_cita_personalidade`). Rodar e
      **ver falhar** ([data-model.md](./data-model.md))
- [X] T003 Incluir `boas_vindas_convite` no `COMMENT ON TABLE
      parametro_hotel` em `docs/04-schema.sql`, depois de
      `boas_vindas_checkout`. T002 continua vermelho até a migração
      (banco ≠ documento)
- [X] T004 Criar
      `alembic/versions/sql/0023_convite_boas_vindas.sql`: `INSERT`
      da chave com `SEMENTE_CONVITE_BOAS_VINDAS` por hotel no molde
      `WHERE NOT EXISTS` da `0022`; `COMMENT` igual ao documento.
      Cópia congelada do delta da T003
- [X] T005 Criar `alembic/versions/0023_convite_boas_vindas.py`
      (`down_revision = "0022_personalidade_assistente"`), `upgrade`
      executa o SQL, `downgrade` apaga a chave e restaura o COMMENT
      da 0022. T002 verde depois de `alembic upgrade head` na suíte

**Checkpoint**: documento e banco citam a chave; hotéis pré-existentes
têm a semente. US1 pode começar.

---

## Phase 3: User Story 1 - A casa escreve o convite (Priority: P1) 🎯 MVP

**Goal**: recepção lê e grava os **quatro** textos pela rota já
existente; formato recusado na hora; gestão lê e não grava; staff
recusado nos dois; gravação atômica.

**Independent Test**: cookie de recepção → PUT com os quatro → GET
devolve o convite (com strip); PUT sem `convite` ou com quebra de linha
→ `422` e valor anterior intacto; gestão GET `200` / PUT `403`; staff
GET e PUT `403`.

### Tests for User Story 1

- [X] T006 [US1] Em
      `testes/unitarios/modulos/propriedade/test_slots_boas_vindas.py`:
      `gravar_textos_de_boas_vindas` exige `convite=`; recusa vazio /
      `\n` / tab / 256 caracteres no convite sem gravar nenhum dos
      quatro (estender `test_valor_invalido_nao_grava_nenhum_dos_tres`);
      aceita strip. Rodar e **ver falhar** (FR-001, FR-003, FR-004)
      ([contracts/api-de-boas-vindas.md](./contracts/api-de-boas-vindas.md))
- [X] T007 [P] [US1] Em
      `testes/integracao/test_boas_vindas_slots.py`: `_corpo()` inclui
      `convite`; GET/PUT assertam o campo; PUT só com os três antigos
      → `422`; PUT de convite com `\n` → `422` e GET inalterado;
      hotel B não vê o convite do hotel A. Rodar e **ver falhar**
      (FR-002, FR-005, FR-016)
- [X] T008 [P] [US1] Em
      `testes/suporte/ambiente_de_acesso.py` (`_semear_boas_vindas`):
      teste que o GET da recepção devolve `convite` não nulo no hotel
      do fixture — se o caso da T007 já cobre, acrescer a semente no
      `_semear` só na implementação. Escrever o assert em T007 e deixar
      este item para o fixture se o GET vier `null`

### Implementation for User Story 1

- [X] T009 [US1] Campo `convite: str` em `BoasVindasEntrada` e
      `BoasVindasResposta` em `app/modulos/propriedade/schema.py`
      (`min_length=1`, `max_length=255` na entrada, `extra="forbid"`
      intacto)
      ([contracts/api-de-boas-vindas.md](./contracts/api-de-boas-vindas.md))
- [X] T010 [US1] Incluir `"convite": CHAVE_BOAS_VINDAS_CONVITE` em
      `CHAVES_SLOTS_BOAS_VINDAS` e `convite=` em
      `gravar_textos_de_boas_vindas` em
      `app/modulos/propriedade/service.py`. Reusar
      `validar_texto_de_boas_vindas("convite", …)`. T006 verde
- [X] T011 [US1] Passar `convite=entrada.convite` em
      `app/modulos/propriedade/router.py`. T007 verde. Log continua
      `textos_de_boas_vindas_gravados id_hotel=` **sem** o valor
      ([contracts/logs.md](./contracts/logs.md))
- [X] T012 [US1] Semear `boas_vindas_convite` em
      `testes/suporte/ambiente_de_acesso.py` (`_semear_boas_vindas`)
      com a semente da T001, para o GET do fixture não devolver `null`

**Checkpoint**: recepção configura o convite pela API. US2 pode
começar.

---

## Phase 4: User Story 2 - O hóspede lê o convite no recado (Priority: P1)

**Goal**: o recado montado termina com a linha da casa; o aviso fica
antes; a frase fixa some; a porta leva cinco variáveis, na ordem
`(prenome, cafe, wifi, checkout, convite)`.

**Independent Test**: `montar_texto_boas_vindas(..., convite="Pode perguntar sobre o spa.")`
→ última linha igual; aviso na linha anterior; frase antiga ausente.
Depois do worker: `len(variaveis) == 5` e `variaveis[4]` igual ao
gravado. MockTransport do WhatsApp: cinco parâmetros no POST, zero rede.

### Tests for User Story 2

- [X] T013 [US2] Reescrever
      `testes/unitarios/modulos/conversa/test_texto_boas_vindas.py`:
      a função exige `convite=`; última linha = convite; aviso
      imediatamente antes; `Quer saber mais alguma coisa da sua estadia?`
      ausente; sem `?` obrigatório; ainda sem parâmetros `aviso` /
      `tom` / `catalogo`. Rodar e **ver falhar** (FR-008, FR-009)
      ([contracts/montagem-e-porta.md](./contracts/montagem-e-porta.md))
- [X] T014 [P] [US2] Em
      `testes/integracao/test_boas_vindas_envio.py` e
      `testes/integracao/test_ia_real_aviso.py`: `len(variaveis) == 5`;
      `conteudo` termina com o convite vigente; frase antiga ausente;
      aviso permanece; coleta continua sem aviso. Rodar e **ver falhar**
      (FR-010, FR-015)
- [X] T015 [P] [US2] Criar
      `testes/unitarios/adaptadores/test_mensageria_whatsapp.py`:
      `enviar_boas_vindas` com tupla de cinco, `httpx.MockTransport`,
      assertir cinco `parameters` na ordem e
      `template.name == "boas_vindas"`. Sem rede (FR-019)

### Implementation for User Story 2

- [X] T016 [US2] Parâmetro `convite` em
      `app/modulos/conversa/texto_boas_vindas.py`; última linha = valor;
      remover a frase fixa; constante de aviso **intocada**. T013 verde
- [X] T017 [US2] Incluir `("convite", "boas_vindas_convite")` em
      `CHAVES_SLOTS_BOAS_VINDAS` de
      `app/modulos/conversa/service.py`; passar `convite=` à montagem;
      tupla de envio com cinco valores. Atualizar `SLOTS_OK` em
      `testes/unitarios/modulos/conversa/test_agendar_boas_vindas.py`
      para o caminho feliz não regressar. T014 começa a ficar verde
- [X] T018 [US2] Assinatura
      `variaveis: tuple[str, str, str, str, str]` em
      `app/portas/mensageria.py`,
      `app/adaptadores/mensageria_falsa.py` (registrar `convite` no
      dict), `app/adaptadores/mensageria_simulada.py` e
      `app/adaptadores/mensageria_whatsapp.py`. Ajustar a tupla de 4
      em `testes/unitarios/adaptadores/test_mensageria_simulada.py`.
      T015 verde

**Checkpoint**: hóspede do simulador e do histórico lê a linha da casa.
O adaptador WhatsApp manda cinco parâmetros. US3 pode começar.

---

## Phase 5: User Story 3 - Convite vazio não envia e sinaliza (Priority: P1)

**Goal**: convite ausente ou inválido = mesmo desfecho dos outros
slots: check-in ocorre, recado não sai, fila acende
`boas_vindas_nao_enviadas`; completar na janela recupera um recado;
alterar depois de enviado não duplica.

**Independent Test**: apagar `boas_vindas_convite`, confirmar chegada →
`hospedado`, zero trabalho, fila sinaliza. PUT do convite +
`--verificar-boas-vindas` na janela → exatamente um recado. PUT depois
de enviado → zero segundo trabalho.

### Tests for User Story 3

- [X] T019 [US3] Em
      `testes/unitarios/modulos/conversa/test_agendar_boas_vindas.py`:
      `SLOTS_OK` sem `boas_vindas_convite` (ou valor inválido) →
      `nao_enviada_slot_ausente`, zero mensagem, zero fila; log
      `chave=boas_vindas_convite` **sem** o valor. Rodar e **ver falhar**
      se a T017 ainda não cobrir este caso (FR-011, FR-012, FR-017)
      ([contracts/logs.md](./contracts/logs.md))
- [X] T020 [P] [US3] Em
      `testes/integracao/test_boas_vindas_envio.py` (ou extensão):
      `_apagar_slot` na chave `boas_vindas_convite`; confirmar chegada;
      assertir `boas_vindas_nao_enviadas` na fila e zero trabalho.
      Rodar e **ver falhar** se o caminho genérico ainda não ler a
      quarta chave (FR-011)
- [X] T021 [US3] Integração de recuperação: reserva hospedada sem
      recado por convite ausente, `checkin_em` dentro da janela; PUT
      do convite; `python -m worker --verificar-boas-vindas` (ou a
      função já usada no quickstart da F2.2) → exatamente um recado
      com a linha da casa; segunda passagem → zero extra; reserva fora
      da janela → zero envio. Em
      `testes/integracao/test_boas_vindas_envio.py` (ou o arquivo de
      recuperação já existente). Rodar e **ver falhar** (FR-013,
      FR-014)

### Implementation for User Story 3

- [X] T022 [US3] Se T019–T021 falharem: o loop de
      `CHAVES_SLOTS_BOAS_VINDAS` em `agendar_boas_vindas` e
      `processar_trabalho_enviar_boas_vindas`
      (`app/modulos/conversa/service.py`) já deve incluir o convite
      (T017). Não criar ramo novo — só completar a chave que faltar.
      Se os três testes já estiverem verdes depois da US2, **não**
      inventar processador paralelo; anotar no commit da história
- [X] T023 [US3] PUT de convite após recado já enviado: asserção em
      T021 (zero segundo trabalho). Sem `UPDATE` de `mensagem.conteudo`
      antigo

**Checkpoint**: omissão do convite é visível na fila. Recuperação
reusa o agendador existente.

---

## Phase 6: User Story 4 - Propriedade nova já nasce com convite (Priority: P2)

**Goal**: bootstrap semeia a chave com o texto padrão; propriedade
nova não depende de alguém lembrar o campo.

**Independent Test**: bootstrap → GET de recepção devolve convite
não vazio, uma linha, sentido serviços/cardápio/horários. Hotel criado
pelo comando, não só pela migração `0023`.

### Tests for User Story 4

- [X] T024 [US4] Estender
      `testes/unitarios/modulos/propriedade/test_bootstrap.py` e
      `testes/integracao/test_bootstrap.py`: o conjunto de chaves
      inclui `boas_vindas_convite`; o valor passa em
      `validar_texto_de_boas_vindas("convite", …)` e contém os termos
      de serviços, cardápio e horários (ASCII da semente). Rodar e
      **ver falhar** (FR-007)
- [X] T025 [P] [US4] Após `alembic upgrade head` num hotel que já
      existia (fixture ou integração de conformidade): a linha
      `boas_vindas_convite` está presente. Se T002+T005 já cobrirem
      o COMMENT, este caso lê o **valor** semeado. Rodar e **ver falhar**
      só se a T004 não tiver o `INSERT`

### Implementation for User Story 4

- [X] T026 [US4] Incluir `CHAVE_BOAS_VINDAS_CONVITE:
      SEMENTE_CONVITE_BOAS_VINDAS` em `PARAMETROS_BOAS_VINDAS_PADRAO`
      em `app/modulos/propriedade/service.py`. T024 verde. Não
      alterar `horas_validade_boas_vindas`

**Checkpoint**: propriedade nova e já instalada têm convite padrão.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: log, estado do projeto, suíte alheia, quickstart.

- [X] T027 [P] Em
      `testes/unitarios/modulos/conversa/test_log_sem_conteudo.py`
      (`test_eventos_de_boas_vindas_nao_levam_conteudo`): incluir
      `boas_vindas_convite` no fake de parâmetros; assertir que o
      valor da semente **não** aparece no `caplog`. Rodar; se já
      verde, manter como âncora (FR-017)
- [X] T028 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: F7.3
      concluída quando os testes desta lista estiverem verdes; linha
      de convite deixa de constar como “o que continua faltando da
      Fase 7”
- [X] T029 Percorrer [quickstart.md](./quickstart.md) com
      `pytest testes/unitarios -q` e
      `pytest testes/integracao/test_boas_vindas_slots.py
      testes/integracao/test_boas_vindas_envio.py
      testes/integracao/test_ia_real_aviso.py
      testes/integracao/test_bootstrap.py
      testes/integracao/test_conformidade_do_esquema.py -q`.
      Sem Graph, sem PMS
- [X] T030 Confirmar que `testes/unitarios/modulos/acesso/test_politica.py`
      permanece verde: `alterar_texto_de_boas_vindas` só recepção;
      nenhuma operação nova; nenhuma operação com `parametro` no nome
      ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: pode começar agora
- **Foundational (Phase 2)**: depende do Setup — **bloqueia** US4
  (semente em hotel antigo) e alinha o documento
- **US1 (Phase 3)**: depois da Foundational recomendada (GET do
  fixture precisa da semente da T012 mesmo sem 0023)
- **US2 (Phase 4)**: depois da US1 (precisa do convite gravável e da
  chave no `CHAVES` de propriedade)
- **US3 (Phase 5)**: depois da US2 (a quarta chave tem que entrar no
  agendar)
- **US4 (Phase 6)**: Foundational (0023) + `PARAMETROS` da T026;
  pode interpolar com US1 se o bootstrap for o único caminho novo
- **Polish (Phase 7)**: depois das histórias desejadas

### User Story Dependencies

- **US1**: Foundational opcional para hotel antigo; fixture T012 é
  o que destrava o GET no teste
- **US2**: US1 (campo existe e é validado)
- **US3**: US2 (montagem e lista de chaves)
- **US4**: Foundational para `INSERT`; T026 para hotel novo

### Parallel Opportunities

- T001 sozinha no Setup
- T007 e T008 depois de T006 escrito (integração vs suporte)
- T014 e T015 depois de T013 escrito
- T020 em paralelo com T019
- T025 em paralelo com T024
- T027, T028 e T030 no Polish

### Parallel Example: User Story 1

```text
T006  unitário test_slots_boas_vindas.py
T007  integração test_boas_vindas_slots.py
```

Depois, em série: T009 schema → T010 serviço → T011 rota → T012 fixture.

### Parallel Example: User Story 2

```text
T013  test_texto_boas_vindas.py
T014  test_boas_vindas_envio.py + test_ia_real_aviso.py
T015  test_mensageria_whatsapp.py (arquivo novo)
```

Depois: T016 montagem → T017 worker → T018 porta e adaptadores.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: recepção grava/lê o convite pela API
4. O hóspede **ainda** lê a frase fixa — isso é a US2

### Incremental Delivery

1. Setup + Foundational
2. US1 → API dos quatro textos (MVP operacional)
3. US2 → recado e canal com a linha da casa
4. US3 → omissão visível e recuperação (pode ser só teste se a US2
   já tiver colocado a chave no agendar)
5. US4 → semente no bootstrap
6. Polish

### Notas para o implementador

- Um desenvolvedor: ordem US1 → US2 → US3 → US4
- Commit por história ou por checkpoint, se o usuário pedir
- Não criar `alterar_parametro_hotel` nem rota nova
- Não mexer em `AVISO_ASSISTENTE_VIRTUAL` além de sua posição
- Aprovar o template de cinco variáveis na Meta é passo humano,
  fora desta lista; a T015 só prova o payload
- Se T019–T021 ficarem verdes na primeira execução depois da US2:
  o caminho genérico de slot cobriu. Não inventar ramo. Anotar
