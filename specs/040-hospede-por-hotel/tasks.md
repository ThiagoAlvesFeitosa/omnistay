---
description: "Lista de tarefas para implementação da fatia"
---

# Tarefas: F9.3 Cada hóspede pertence a um hotel

**Input**: documentos em `specs/040-hospede-por-hotel/`
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
Portas falsas; sem Gemini nem WhatsApp.

**Duas guardas (não negociar):**

1. **Sem peça nova de produto.** Sem rota nova, sem operação na
   matriz, sem F9.4 (telefone) nem F9.5 (vincular). `0001`
   congelado. Conferência de CPF (F9.2) intocada. Sem lib.
2. **Documento fora do aviso e do log.** Recusa e migração:
   identificadores e fato, nunca o número. O aviso nomeia e liga
   para `/ficha/{id_reserva}`; não mostra o documento.

**Organização**: US1 dois hotéis sem atropelo (coluna + UNIQUE);
US2 aviso nomeado no balcão; US3 consentimento e expurgo. Walker
Artigo XIV e planejamento da `0028` no Foundational. Setup e
Foundational sem rótulo de história.

## Format: `[ID] [P?] [USx?] Descrição`

- **[P]**: paralelizable (arquivos diferentes, sem dependência incompleta)
- **[USn]**: história correspondente
- Caminho de arquivo em cada tarefa

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: exceções nomeadas do teste estrutural. O monólito já
existe; não criar pacote de produção.

- [x] T001 [P] Criar `testes/suporte/artigo_xiv.py` com o mapa
  `EXCECOES` (`alembic_version` → versionamento; `evento_webhook` →
  idempotência do canal) e docstring. Sem walker ainda. Sem
  importar produção.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: walker Artigo XIV, planejamento da migração, coluna
`id_hotel`, UNIQUE por hotel, `inserir_hospede` com dono.
**Nenhuma história começa antes desta fase.**

**Checkpoint**: `hospede` tem `id_hotel` NOT NULL; UNIQUE é
`(id_hotel, tipo, número)` parcial; criar reserva grava o hotel no
hóspede; dois hotéis aceitam o mesmo documento; o walker no `head`
não lista `hospede`; órfão com ≥2 hotéis aborta a revisão.

### Tests (escrever e ver falhar)

- [x] T002 [P] Escrever
  `testes/unitarios/test_artigo_xiv.py`: walker recebe inventário
  falso — tabela sem `id_hotel` e só referenciada (como `hospede`
  hoje) entra na lista; tabela com `id_hotel` ou FK NOT NULL para
  quem tem **não** entra; `evento_webhook` e `alembic_version`
  ausentes da lista porque estão em `EXCECOES`. Uma asserção
  conceitual por teste. Nomes em português. Rodar e **ver falhar**
  (FR-008, [artigo-xiv.md](./contracts/artigo-xiv.md)).

- [x] T003 [P] Escrever
  `testes/unitarios/modulos/hospedagem/test_hospede_migracao.py`:
  `planejar_hospede_por_hotel` — um hotel nas reservas → atribuir;
  dois hotéis → original no menor `id_hotel`, ids a copiar, vínculos
  a repontar, consentimento **não** na cópia; sem reserva + 1 hotel
  → atribuir; sem reserva + ≥2 → `orfaos` preenchido, nada atribuído.
  Texto de log sem documento. Rodar e **ver falhar** (FR-007,
  [migracao-e-logs.md](./contracts/migracao-e-logs.md)).

- [x] T004 [P] Estender
  `testes/integracao/test_alterar_ficha.py`: PUT do mesmo
  tipo+número em **dois** hotéis → os dois `200`. Rodar e **ver
  falhar** no UNIQUE global (FR-002).

- [x] T005 [P] Estender
  `testes/unitarios/modulos/hospedagem/test_service_de_reserva.py`:
  `inserir_hospede` é chamado com `id_hotel` da reserva. Rodar e
  **ver falhar** (FR-001).

### Implementation

- [x] T006 Em `testes/suporte/artigo_xiv.py`, implementar
  `tabelas_sem_dono(inventario)` (filho→pai, FK obrigatória;
  ser referenciado **não** conta). Rodar T002 até **verde**.

- [x] T007 Criar `app/modulos/hospedagem/hospede_migracao.py` com o
  planejamento da T003 (só ids; sem I/O). Rodar T003 até **verde**.

- [x] T008 Revisão Alembic `0028` em
  `alembic/versions/0028_hospede_id_hotel.py` + `docs/04-schema.sql`:
  coluna `id_hotel`, DML via T007, órfãos com ≥2 hotéis → log
  `hospede_migracao_orfao n=%s ids=%s` e **abortar**; senão NOT NULL
  + dropar UNIQUE antigo + criar
  `(id_hotel, tipo_documento, numero_documento)` parcial. `0001`
  congelado. `inserir_hospede` / `criar_reserva` em
  `app/modulos/hospedagem/repository.py` e `service.py` passam
  `id_hotel`. Fakes dos testes unitários acompanham. Rodar T004 e
  T005 até **verde**. MUST NOT copiar consentimento. MUST NOT
  interpolar documento no log (FR-001, FR-002, FR-003, FR-007,
  FR-009).

- [x] T009 Estender ou criar
  `testes/integracao/test_artigo_xiv.py`: no `head`, `hospede`
  **não** está em `tabelas_sem_dono`; `evento_webhook` continua
  exceção. Rodar até **verde** (FR-008, SC-006).

**Checkpoint**: schema e criação de reserva com dono. Aviso 409
ainda é string genérica. Expurgo ainda pode ser só o JOIN.

---

## Phase 3: User Story 1 - O mesmo documento em dois hotéis não se atropela (Priority: P1) 🎯 MVP

**Goal**: cada hóspede pertence a um hotel; o mesmo documento em
casas diferentes grava; na mesma casa continua único.

**Independent Test**: PUT do mesmo tipo+número em dois hotéis →
`200` nos dois (T004). No mesmo hotel, o segundo PUT continua
`409` (teste já existente `test_documento_duplicado_nao_funde`).

### Tests (escrever e ver falhar se T008 não filtrou a leitura)

- [x] T010 [P] [US1] Estender
  `testes/integracao/test_alterar_ficha.py` (ou GET ficha): hotel B
  **não** lê a ficha do hotel A. `test_documento_duplicado_nao_funde`
  permanece `409` no mesmo hotel. Rodar (FR-002, FR-003, FR-005).

### Implementation

- [x] T011 [US1] Em `app/modulos/hospedagem/repository.py`,
  `ler_titular_da_reserva` exige `h.id_hotel = r.id_hotel`. Se T010
  já estiver verde só com T008, **não** reescrever — só o que
  faltar. Rodar T004, T010 e o duplicado no mesmo hotel até
  **verde**.

**Checkpoint**: dois hotéis não se atropelam. Painel ainda não
nomeia nem liga para a ficha conflitante.

---

## Phase 4: User Story 2 - A recepção vê quem já tem aquele documento na casa (Priority: P1)

**Goal**: `409` nomeia o hóspede desta casa e oferece
`/ficha/{id_reserva}`; sem documento no aviso; só recepção; nunca
o outro hotel.

**Independent Test**: PUT colidindo no hotel A → `409` com `nome` e
`id_reserva` do titular A; link na tela; corpo e log sem número;
hóspede do B não aparece.

### Tests (escrever e ver falhar)

- [x] T012 [P] [US2] Estender
  `testes/unitarios/modulos/hospedagem/test_completar_ficha.py`:
  colisão → `DocumentoEmUso` com `nome` e `id_reserva`; `str` sem o
  número. Rodar e **ver falhar** (FR-004, FR-009,
  [put-ficha.md](./contracts/put-ficha.md)).

- [x] T013 [P] [US2] Estender
  `testes/integracao/test_alterar_ficha.py`: `409` com
  `codigo=documento_em_uso`, `nome`, `id_reserva`; GET da segunda
  ficha inalterada; caplog/espião sem o número e sem o nome do
  hotel B. Rodar e **ver falhar** (FR-004, FR-005, SC-002, SC-003,
  SC-007).

- [x] T014 [P] [US2] Estender
  `frontend/src/painel/TelaFicha.test.tsx`: PUT `409` com o objeto
  do contrato → recado com o nome e link para `/ficha/{id_reserva}`;
  rascunho conservado; número do documento **não** no aviso. Rodar
  e **ver falhar** ([superficie-painel.md](./contracts/superficie-painel.md)).

### Implementation

- [x] T015 [US2] Em `app/modulos/hospedagem/service.py` e
  `router.py`, `DocumentoEmUso` carrega nome e `id_reserva` (maior
  id não cancelada deste hotel; senão maior id). `409` `detail`
  objeto do contrato. Log `ficha_alterada_recusada … codigo=409`
  só com ids. Rodar T012 e T013 até **verde**.

- [x] T016 [P] [US2] Em `frontend/src/painel/TelaFicha.tsx`,
  amarrar o `409` de documento ao recado + `Link` `/ficha/{id}`
  (como a fila). Não resetar o rascunho. Sem eco do número. Rodar
  T014 até **verde**.

**Checkpoint**: balcão nomeia e abre a ficha desta casa. Expurgo
ainda não foi reafirmado pela coluna.

---

## Phase 5: User Story 3 - Consentimento e expurgo param no controlador (Priority: P1)

**Goal**: aceite e apagamento da ficha do hotel A não alcançam o B.

**Independent Test**: dois cadastros (mesmo documento permitido):
revogar/expurgar no A deixa o B intacto; GET consentimento do B
com sessão A → `404`.

### Tests (escrever e ver falhar)

- [x] T017 [P] [US3] Estender testes de consentimento
  (`testes/integracao/` da ficha/consentimento): sessão do hotel A
  + `id_hospede` do B → `404`; revogar no A não muda o vigente do
  B. Rodar e **ver falhar** se `hospede_do_hotel` ainda for só o
  JOIN (FR-006, [consentimento-e-expurgo.md](./contracts/consentimento-e-expurgo.md)).

- [x] T018 [P] [US3] Estender
  `testes/unitarios/modulos/hospedagem/test_apagar_ficha_retencao.py`
  e/ou `testes/integracao/test_retencao.py`: passagem do hotel A
  **não** apaga hóspede com `id_hotel` do B. Rodar e **ver falhar**
  (FR-006, SC-004).

### Implementation

- [x] T019 [US3] Em `app/modulos/hospedagem/repository.py`,
  `hospede_do_hotel` lê `hospede.id_hotel`; `apagar_fichas_vencidas`
  restringe `hospede.id_hotel = :id_hotel`. Rodar T017 e T018 até
  **verde**. Sem mudar prazos.

**Checkpoint**: US3 fechada. Estado do projeto ainda na polish.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: estado, política e suíte do quickstart.

- [x] T020 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: pendência
  `id_hotel` em `hospede` desta fatia. Sem silenciar F9.4–F9.5.

- [x] T021 [P] Confirmar
  `testes/unitarios/modulos/acesso/test_politica.py` sem operação
  nova; nenhuma rota em `ROTAS_PUBLICAS`.
  `testes/integracao/test_conformidade_do_esquema.py` verde
  (`04-schema.sql` = banco migrado).

- [x] T022 Rodar a validação de [quickstart.md](./quickstart.md):
  `uv run pytest testes/unitarios/modulos/hospedagem/test_completar_ficha.py
  testes/unitarios/modulos/hospedagem/test_hospede_migracao.py
  testes/unitarios/test_artigo_xiv.py -q`; integração
  `test_alterar_ficha`, `test_artigo_xiv`, `test_retencao`;
  `npm --prefix frontend test -- --run src/painel/TelaFicha.test.tsx`.
  Tudo verde. Sem rede externa.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: depois do Setup — **bloqueia** as histórias
- **US1 (Phase 3)**: depois da Foundational — MVP (dois hotéis)
- **US2 (Phase 4)**: depois da Foundational (UNIQUE já por hotel)
- **US3 (Phase 5)**: depois da Foundational (coluna já existe)
- **Polish**: depois das histórias desejadas

### User Story Dependencies

- **US1 (P1)**: Foundational; T004 é o teste independente
- **US2 (P1)**: acoplada ao UNIQUE da Foundational
- **US3 (P1)**: acoplada à coluna; independente do texto do 409

### Within Each User Story

- Teste vermelho **antes** da produção
- Uma asserção conceitual por teste
- História completa no checkpoint antes de avançar (salvo US2∥US3
  depois da Foundational)

### Parallel Opportunities

- T002 ∥ T003 ∥ T004 ∥ T005 (depois de T001)
- T006 depois de T002; T007 depois de T003
- T008 depois de T004–T007
- T012 ∥ T013 ∥ T014
- T016 ∥ T015 (depois dos testes da US2)
- T017 ∥ T018
- T020 ∥ T021
- US2 e US3 em paralelo após a Foundational, se duas pessoas

---

## Parallel Example: User Story 2

```text
T012 testes/unitarios/modulos/hospedagem/test_completar_ficha.py
T013 testes/integracao/test_alterar_ficha.py
T014 frontend/src/painel/TelaFicha.test.tsx
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2 (coluna, UNIQUE, dois hotéis)
2. Phase 3 (US1) se T010/T011 ainda faltarem
3. **STOP**: mesmo documento em duas casas, único na mesma

### Incremental Delivery

1. Setup + Foundational
2. US1 → dois hotéis (MVP)
3. US2 → aviso com nome e caminho
4. US3 → consentimento e expurgo
5. Polish

### Parallel Team Strategy

Um desenvolvedor: US1 → US2 → US3. Dois: depois da Foundational,
um faz US2 na tela, o outro US3 no expurgo.

---

## Notes

- [P] = arquivos diferentes, sem dependência incompleta
- Sem Redis, Celery, PMS, foto, operação nova, F9.4, F9.5
- `0001` congelado
- Identidade no balcão além do 409 nomeado = F9.5
