---

description: "Task list for feature implementation"
---

# Tasks: Cadastrar Reserva

**Input**: Design documents from `/specs/004-cadastrar-reserva/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: ObrigatÃ³rios. Artigo XII e a regra TDD do projeto: nenhum cÃ³digo de produÃ§Ã£o sem teste
que falhe antes pelo motivo certo.

**Organization**: Tarefas agrupadas por histÃ³ria de usuÃ¡rio (US1â€“US4), na ordem de prioridade da
spec.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependÃªncia pendente)
- **[Story]**: A qual histÃ³ria a tarefa pertence (US1 a US4)

## Como ver os testes falharem nesta fatia

**A visÃ£o ampliada.** O teste de conformidade da F0.2 Ã© o "ver falhar" da migraÃ§Ã£o: atualizar
`docs/04-schema.sql` **antes** de criar a revisÃ£o `0003` deixa a suÃ­te vermelha (banco migrado
diverge do documento). A revisÃ£o a devolve ao verde. Ordem inversa passa de primeira sem provar
nada.

**Telefone e datas.** FunÃ§Ãµes e regras de serviÃ§o sÃ£o puras ou usam repositÃ³rio falso: o unitÃ¡rio
falha por `ImportError` / `AttributeError` atÃ© existir a implementaÃ§Ã£o.

**Rotas novas.** A varredura em `testes/integracao/test_rotas_protegidas.py` jÃ¡ pega qualquer rota
registrada fora da lista pÃºblica. Depois de registrar o roteador, a suÃ­te exige `401` sem cookie â€”
nÃ£o Ã© preciso editar a lista, sÃ³ confirmar que as trÃªs rotas novas entram no verde.

---

## Phase 1: Setup

**Purpose**: Lugar para o cÃ³digo e os testes do mÃ³dulo novo

- [X] T001 [P] Criar o pacote `app/modulos/hospedagem/__init__.py`
- [X] T002 [P] Criar o pacote `testes/unitarios/modulos/hospedagem/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Telefone canÃ´nico, operaÃ§Ã£o nova na matriz, visÃ£o ampliada e esqueleto do mÃ³dulo â€”
tudo o que as histÃ³rias usam e nenhuma delas deve reinventar

**âš ï¸ CRÃTICO**: nenhuma histÃ³ria comeÃ§a antes desta fase. T010/T011/T012 dependem de T009 na
ordem documento â†’ falha â†’ congelar â†’ migraÃ§Ã£o.

- [X] T003 Escrever o teste de normalizaÃ§Ã£o e validaÃ§Ã£o de telefone em
      `testes/unitarios/comum/test_telefone.py`: mÃ¡scara `(11) 98765-4321` e `11987654321` viram o
      mesmo canÃ´nico `5511987654321`; fixo 10 dÃ­gitos com DDD Ã© aceito; `123` e nÃºmero estrangeiro
      sem `55` vÃ¡lido sÃ£o recusados; saÃ­da Ã© sÃ³ dÃ­gitos com prefixo `55`. Rodar e ver falhar
      (FR-003, research Â§3)
- [X] T004 Implementar `app/comum/telefone.py` (normalizar / validar / exceÃ§Ã£o de formato) atÃ© T003
      passar â€” **nenhuma dependÃªncia nova**
- [X] T005 [P] Acrescentar casos em `testes/unitarios/modulos/acesso/test_politica.py`:
      `ler_fila_do_dia` permitida sÃ³ para `recepcao`; `staff` e `gestor` recusados; `ler_indicadores`
      continua permitido para `recepcao` e `gestor`. Rodar e ver falhar o caso da operaÃ§Ã£o nova
- [X] T006 Acrescentar `ler_fila_do_dia` a `OPERACOES` em `app/modulos/acesso/politica.py` (sÃ³
      `recepcao`) atÃ© T005 passar ([contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md))
- [X] T007 Ampliar `vw_fila_do_dia` em `docs/04-schema.sql` com `telefone_contato` e
      `data_checkout_prevista`, exatamente como em [data-model.md](./data-model.md). Rodar a suÃ­te
      e **ver o teste de conformidade da F0.2 ficar vermelho**
- [X] T008 [P] Registrar em `docs/04-modelagem-de-dados.md` que a criaÃ§Ã£o da reserva cria titular
      provisÃ³rio (`nome_completo` + `telefone`, `ficha_completa = false`) e que telefone repetido
      **sempre** cria hÃ³spede novo â€” consolidaÃ§Ã£o por pessoa, se existir, Ã© passo futuro explÃ­cito
      ([research.md](./research.md) Â§1 e Â§9)
- [X] T009 Congelar a definiÃ§Ã£o da visÃ£o em `alembic/versions/sql/0003_fila_do_dia.sql`, idÃªntica
      ao bloco do documento (incluindo `CREATE OR REPLACE VIEW` e `COMMENT`)
- [X] T010 Criar a revisÃ£o `alembic/versions/0003_fila_do_dia.py` com `down_revision =
      "0002_sessao"`, executando o SQL congelado por cursor cru; `downgrade` recria a visÃ£o
      **anterior** (sem as duas colunas novas). Rodar atÃ© o teste de conformidade voltar ao verde
- [X] T011 [P] Criar `app/modulos/hospedagem/schema.py` com os contratos de entrada/saÃ­da de
      `POST /reservas`, `GET /fila-do-dia` e `GET /indicadores/chegadas-do-dia` conforme
      [contracts/api-de-hospedagem.md](./contracts/api-de-hospedagem.md) â€” ainda sem rotas
- [X] T012 [P] Criar esqueleto `app/modulos/hospedagem/repository.py` com as funÃ§Ãµes nomeadas
      (inserir hÃ³spede, inserir reserva, inserir vÃ­nculo titular, listar fila do hotel, contar
      chegadas do dia) levantando `NotImplementedError` â€” sÃ³ para fixar a fronteira SQL

**Checkpoint**: telefone puro verde, matriz atualizada, visÃ£o ampliada em documento e banco, mÃ³dulo
com contratos. HistÃ³rias podem comeÃ§ar.

---

## Phase 3: User Story 1 - Registrar reserva com trÃªs campos (Priority: P1) ðŸŽ¯ MVP

**Goal**: RecepÃ§Ã£o autentica, envia nome + telefone + datas vÃ¡lidos, a reserva nasce em
`aguardando_cadastro` com titular provisÃ³rio e aparece na fila do dia do hotel.

**Independent Test**: SessÃ£o de recepÃ§Ã£o â†’ `POST /reservas` â†’ `201` com status
`aguardando_cadastro` â†’ `GET /fila-do-dia` devolve o item com nome, telefone canÃ´nico e datas.

### Tests for User Story 1 âš ï¸

> Escrever primeiro; rodar; ver falhar pelo motivo certo antes de implementar.

- [X] T013 [P] [US1] Escrever testes unitÃ¡rios do serviÃ§o de criaÃ§Ã£o em
      `testes/unitarios/modulos/hospedagem/test_service_de_reserva.py` com repositÃ³rio falso: campos
      vÃ¡lidos disparam insert de hÃ³spede, reserva (`id_hotel` da sessÃ£o, status
      `aguardando_cadastro`) e vÃ­nculo titular com `ficha_completa=false`; telefone repetido gera
      **segundo** hÃ³spede (nunca reutiliza id); nome/telefone em branco sÃ£o recusados sem chamar
      insert (FR-001, FR-002, FR-005, FR-012, FR-017)
- [X] T014 [P] [US1] Escrever testes unitÃ¡rios da fila em
      `testes/unitarios/modulos/hospedagem/test_service_da_fila.py`: serviÃ§o pede a lista sÃ³ com
      `id_hotel` da sessÃ£o; ordenaÃ§Ã£o por check-in previsto ascendente (FR-006, FR-009)
- [X] T015 [US1] Escrever testes de integraÃ§Ã£o em `testes/integracao/test_reservas.py`: recepÃ§Ã£o
      cria reserva vÃ¡lida (`201`, telefone canÃ´nico, status `aguardando_cadastro`); no banco existem
      as trÃªs linhas; segundo `POST` com o mesmo telefone cria segundo `hospede`. Usar
      `testes/suporte/ambiente_de_acesso.py` + cookie de sessÃ£o. Rodar e ver falhar
- [X] T016 [US1] Escrever testes de integraÃ§Ã£o da fila em `testes/integracao/test_fila_do_dia.py`:
      apÃ³s criar reserva com check-in hoje, `GET /fila-do-dia` como recepÃ§Ã£o devolve o item com
      nome, telefone, datas, `ficha_completa=false` e `chegada_nao_confirmada` coerente. Rodar e
      ver falhar (FR-006, FR-008)

### Implementation for User Story 1

- [X] T017 [US1] Implementar em `app/modulos/hospedagem/repository.py` os inserts atÃ´micos
      (hÃ³spede, reserva, `reserva_hospede` titular) e a leitura da fila filtrada por `id_hotel`
      via `vw_fila_do_dia`, ordenada por `data_checkin_prevista`, `id_reserva`
- [X] T018 [US1] Implementar criaÃ§Ã£o e listagem em `app/modulos/hospedagem/service.py` (hotel sÃ³ da
      sessÃ£o; telefone via `app/comum/telefone.py`; status fixo `aguardando_cadastro`; sem log de
      nome/telefone) atÃ© T013 e T014 passarem (FR-013)
- [X] T019 [US1] Implementar `POST /reservas` e `GET /fila-do-dia` em
      `app/modulos/hospedagem/router.py` com `exigir_operacao("alterar_reserva")` e
      `exigir_operacao("ler_fila_do_dia")` respectivamente
- [X] T020 [US1] Registrar o roteador de hospedagem em `app/main.py` e fazer T015 e T016
      passarem

**Checkpoint**: MVP observÃ¡vel â€” criar reserva e ver na fila como recepÃ§Ã£o.

---

## Phase 4: User Story 2 - Impedir telefone invÃ¡lido e datas inconsistentes (Priority: P1)

**Goal**: Telefone invÃ¡lido e checkout â‰¤ check-in sÃ£o recusados com mensagem clara; nada parcial
fica no banco.

**Independent Test**: `POST` com telefone `123` e `POST` com datas invertidas â†’ ambos `422`;
contagem de `reserva` do hotel nÃ£o aumenta.

### Tests for User Story 2 âš ï¸

- [X] T021 [P] [US2] Acrescentar em
      `testes/unitarios/modulos/hospedagem/test_service_de_reserva.py`: telefone invÃ¡lido e
      `data_checkout_prevista <= data_checkin_prevista` levantam erro de domÃ­nio **antes** de
      qualquer insert (FR-003, FR-004)
- [X] T022 [US2] Acrescentar em `testes/integracao/test_reservas.py`: os dois casos acima respondem
      `422` com mensagem utilizÃ¡vel; apÃ³s as tentativas, nÃ£o hÃ¡ linha nova em `reserva` nem em
      `hospede` para aquele hotel. Rodar e ver falhar se a rota ainda engolir a exceÃ§Ã£o

### Implementation for User Story 2

- [X] T023 [US2] Completar validaÃ§Ãµes e mapeamento para `HTTP 422` em
      `app/modulos/hospedagem/service.py` e `router.py` (mensagem distingue telefone vs datas vs
      campo ausente) atÃ© T021 e T022 passarem. O `CHECK` do banco permanece como rede de proteÃ§Ã£o
      â€” a borda nÃ£o depende dele para a mensagem (research Â§4)

**Checkpoint**: origem suja nÃ£o grava reserva.

---

## Phase 5: User Story 3 - Isolar a fila por hotel e por perfil (Priority: P1)

**Goal**: Fila e cadastro sÃ³ do hotel da sessÃ£o; `staff` e `gestor` nÃ£o cadastram nem leem a fila
nominada; sem sessÃ£o â†’ `401`.

**Independent Test**: Duas propriedades com reserva cada; cada recepÃ§Ã£o sÃ³ vÃª a prÃ³pria; gestor e
staff levam `403` em `POST /reservas` e `GET /fila-do-dia`.

### Tests for User Story 3 âš ï¸

- [X] T024 [P] [US3] Acrescentar em `testes/integracao/test_fila_do_dia.py`: isolamento entre
      `propriedade_a` e `propriedade_b` do ambiente de acesso (FR-007)
- [X] T025 [P] [US3] Acrescentar em `testes/integracao/test_reservas.py` e
      `testes/integracao/test_fila_do_dia.py`: `staff` e `gestor` recebem `403` no cadastro e na
      fila; nada gravado (FR-010)
- [X] T026 [US3] Confirmar em `testes/integracao/test_rotas_protegidas.py` (jÃ¡ existente) que
      `POST /reservas` e `GET /fila-do-dia` sem cookie devolvem `401` â€” rodar a varredura e
      corrigir sÃ³ se alguma rota nova tiver ficado pÃºblica por engano (FR-011)

### Implementation for User Story 3

- [X] T027 [US3] Garantir filtro `id_hotel` da sessÃ£o em toda consulta/escrita de
      `app/modulos/hospedagem/repository.py` e `service.py` (corpo nunca traz hotel) atÃ© T024
      passar â€” Artigo XIV
- [X] T028 [US3] Confirmar que as dependÃªncias `exigir_operacao` nas duas rotas cobrem T025; ajustar
      apenas se o status ou a mensagem divergirem do contrato

**Checkpoint**: multi-tenant e perfis fechados na primeira escrita de domÃ­nio.

---

## Phase 6: User Story 4 - Contagem de chegadas sem dado de hÃ³spede (Priority: P2)

**Goal**: GestÃ£o (e recepÃ§Ã£o) obtÃªm sÃ³ o nÃºmero de chegadas do dia; staff recusado; corpo sem
lista/nome/telefone.

**Independent Test**: N reservas com check-in = hoje â†’ gestÃ£o `GET /indicadores/chegadas-do-dia`
â†’ `{"quantidade": N}` e nada mais; `GET /fila-do-dia` como gestÃ£o continua `403`.

### Tests for User Story 4 âš ï¸

- [X] T029 [P] [US4] Escrever testes unitÃ¡rios em
      `testes/unitarios/modulos/hospedagem/test_service_de_contagem.py`: serviÃ§o devolve inteiro;
      repositÃ³rio falso Ã© chamado sÃ³ com `id_hotel` da sessÃ£o (FR-015)
- [X] T030 [US4] Escrever testes de integraÃ§Ã£o em `testes/integracao/test_contagem_chegadas.py`:
      gestÃ£o e recepÃ§Ã£o recebem `200` com **apenas** a chave `quantidade`; asserÃ§Ã£o explÃ­cita de
      ausÃªncia de `itens`/nome/telefone/`id_reserva`; `staff` â†’ `403`; isolamento por hotel; zero
      chegadas â†’ `quantidade: 0`. Rodar e ver falhar (FR-015, FR-016, SC-008)

### Implementation for User Story 4

- [X] T031 [US4] Implementar contagem em `app/modulos/hospedagem/repository.py` (`data_checkin_prevista
      = CURRENT_DATE`, status fora de `encerrado`/`cancelada`, filtro `id_hotel`) e em
      `service.py`
- [X] T032 [US4] Expor `GET /indicadores/chegadas-do-dia` em `app/modulos/hospedagem/router.py` com
      `exigir_operacao("ler_indicadores")` atÃ© T029 e T030 passarem
- [X] T033 [US4] Rodar `testes/integracao/test_rotas_protegidas.py` e confirmar `401` sem cookie
      tambÃ©m nesta rota

**Checkpoint**: gestÃ£o dimensiona equipe sem ver quem chega.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: DocumentaÃ§Ã£o viva, quickstart e estado do projeto

- [X] T034 [P] Atualizar a linha da F0.3 em `docs/00-ESTADO-DO-PROJETO.md` / tabela de decisÃµes se
      ainda disser que a tela viria â€œna F1.1â€: registrar que F1.1 entregou API sem painel React
      (research Â§2, Artigo XV)
- [X] T035 [P] Marcar F1.1 como concluÃ­da em `docs/backlog.md` **somente apÃ³s** a suÃ­te verde da
      entrega (deixar a marcaÃ§Ã£o por Ãºltimo, junto de T038)
- [X] T036 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: progresso 4/24, F1.1 concluÃ­da, decisÃµes
      (titular provisÃ³rio, telefone repetido = hÃ³spede novo, fila vs contagem, visÃ£o `0003`)
- [X] T037 Executar o [quickstart.md](./quickstart.md) (cenÃ¡rios 0â€“8) e corrigir qualquer passo que
      nÃ£o confira
- [X] T038 Executar a suÃ­te completa com `EXIGIR_POSTGRES=1` e confirmar verde sem teste pulado;
      entÃ£o aplicar T035

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Fase 1)**: sem dependÃªncias
- **Foundational (Fase 2)**: depende do Setup e **bloqueia todas as histÃ³rias**
- **US1 (Fase 3)**: depende da Fase 2 â€” MVP
- **US2 (Fase 4)**: depende da US1 (precisa do `POST` existindo para exercitar `422` de ponta a ponta)
- **US3 (Fase 5)**: depende da US1 (fila e cadastro jÃ¡ observÃ¡veis)
- **US4 (Fase 6)**: depende da US1 (precisa de reservas com check-in hoje); independente da US2/US3
  na lÃ³gica, mas na prÃ¡tica roda depois do MVP
- **Polish (Fase 7)**: depende de US1â€“US4

### User Story Dependencies

```text
Fase 2 â”€â”€â–º US1 (MVP) â”€â”€â–º US2
              â”œâ”€â”€â–º US3
              â””â”€â”€â–º US4
```

### DependÃªncias internas relevantes

- T009 â†’ T010 â†’ T011 (documento antes da migraÃ§Ã£o)
- T003 â†’ T004; T005 â†’ T006
- T013/T014 antes de T017â€“T018; T015/T016 verdes sÃ³ apÃ³s T019â€“T020
- T021/T022 antes de T023
- T029/T030 antes de T031â€“T032
- T026 e T033 sÃ£o verificaÃ§Ã£o da varredura existente, nÃ£o lista nova de rotas pÃºblicas

### Parallel Opportunities

- T001 e T002 no Setup
- T005 e T008 apÃ³s T003/T004 (arquivos distintos); T011 e T012 apÃ³s a migraÃ§Ã£o
- T013 e T014 juntos; T024 e T025 juntos; T029 paralelo a documentaÃ§Ã£o do Polish
- Um desenvolvedor: seguir a ordem numÃ©rica

---

## Parallel Example: User Story 1

```bash
# Testes da US1 antes de qualquer implementaÃ§Ã£o de serviÃ§o/rota:
Task: "test_service_de_reserva.py â€” criaÃ§Ã£o, titular, telefone repetido"
Task: "test_service_da_fila.py â€” hotel da sessÃ£o e ordenaÃ§Ã£o"
# Depois da implementaÃ§Ã£o do serviÃ§o, integraÃ§Ã£o:
Task: "test_reservas.py â€” POST 201 e trÃªs linhas no banco"
Task: "test_fila_do_dia.py â€” item visÃ­vel para a recepÃ§Ã£o"
```

---

## Implementation Strategy

### MVP primeiro (User Story 1)

1. Fase 1 + Fase 2 â€” telefone, matriz, visÃ£o `0003`
2. Fase 3: US1 â€” criar reserva e ver na fila
3. **PARAR E VALIDAR**: cenÃ¡rios 1 e 2 do [quickstart.md](./quickstart.md)
4. Seguir US2 â†’ US3 â†’ US4 â†’ Polish

### Entrega incremental

1. Setup + Foundational â†’ base sÃ³lida
2. US1 â†’ MVP da prÃ©-chegada
3. US2 â†’ porta fechada para lixo de origem
4. US3 â†’ isolamento e perfis
5. US4 â†’ indicador mÃ­nimo para a gestÃ£o
6. Polish â†’ docs e quickstart

### EstratÃ©gia com um sÃ³ desenvolvedor

As marcaÃ§Ãµes `[P]` indicam ausÃªncia de dependÃªncia entre arquivos, nÃ£o trabalho simultÃ¢neo. A
ordem T001â€¦T038 Ã© uma sequÃªncia vÃ¡lida do comeÃ§o ao fim.

---

## Notes

- Commit apÃ³s cada tarefa ou grupo lÃ³gico, com mensagem descritiva â€” **sÃ³ quando o usuÃ¡rio pedir**
- Nome e telefone nunca vÃ£o para log, inclusive em asserÃ§Ãµes de texto de log
- `id_hotel` sempre da sessÃ£o; corpo e query nÃ£o aceitam hotel
- Sem dependÃªncia nova; sem tela React; sem envio WhatsApp
- Telefone repetido = hÃ³spede novo, sempre
- Contagem e fila sÃ£o rotas separadas: gestÃ£o nunca recebe a lista â€œpara filtrar no frontendâ€
