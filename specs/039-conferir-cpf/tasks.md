---
description: "Lista de tarefas para implementação da fatia"
---

# Tarefas: F9.2 Conferir o CPF antes de gravar

**Input**: documentos em `specs/039-conferir-cpf/`
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

1. **Um sítio, sem peça nova.** Conferência em
   `validar_campos_extraidos`. Sem lib, sem rota, sem operação na
   matriz, sem CHECK, sem mexer em `uq_hospede_documento`, sem
   algoritmo de CPF no TypeScript.
2. **Número fora do log.** Recusa e migração: identificadores e
   fato, nunca o CPF. Aviso no painel não ecoa o número em log.

**Organização**: US1 coleta; US2 painel; US3 onze iguais, demo e
migração. Setup e Foundational sem rótulo de história.

## Format: `[ID] [P?] [USx?] Descrição`

- **[P]**: paralelizable (arquivos diferentes, sem dependência incompleta)
- **[USn]**: história correspondente
- Caminho de arquivo em cada tarefa

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: constantes só de teste. O monólito já existe; não criar
pacote de produção.

- [X] T001 [P] Criar `testes/suporte/cpf_ficha.py` com `CPF_VALIDO`
  (onze dígitos que fecham, p.ex. `52998224725`),
  `CPF_VALIDO_PONTUADO` (`529.982.247-25`), `CPF_REPROVADO`
  (`12345678900` / `123.456.789-00`) e `CPF_ONZE_IGUAIS`
  (`11111111111`). Docstring: uso só em teste. Sem importar
  produção.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: a conferência pura, usada pela coleta e pelo painel.
**Nenhuma história começa antes desta fase.**

**Checkpoint**: `tipo=cpf` + número que fecha, com ou sem pontuação,
sai em onze dígitos; dígito errado ou tamanho errado some da saída;
RG `1234567` continua aceito; tipo `cpf` permanece se só o número
cair.

- [X] T002 [P] Estender
  `testes/unitarios/modulos/conversa/test_validacao_ficha.py`:
  (1) `tipo_documento=cpf` + `CPF_VALIDO_PONTUADO` → número onze
  dígitos; (2) `CPF_VALIDO` sem pontuação → os mesmos onze;
  (3) `CPF_REPROVADO` → `numero_documento` ausente e tipo `cpf`
  presente se informado; (4) nove campos com `tipo=rg` e
  `1234567` continuam completos. Uma asserção conceitual por
  teste. Nomes em português. Rodar e **ver falhar** (FR-001,
  FR-002, FR-007, [conferir-numero.md](./contracts/conferir-numero.md)).

- [X] T003 Em `app/modulos/conversa/validacao_ficha.py`, quando o
  tipo (informado ou já na saída) é `cpf`, só aceitar o número se
  houver onze dígitos após ignorar pontuação e os verificadores da
  Receita fecharem; gravar onze dígitos. MUST NOT rejeitar onze
  iguais ainda (US3). Sem lib. Rodar T002 até ficar **verde**.

**Checkpoint**: validador cobre aceite e dígito trocado. Coleta e
PUT ainda não têm teste de fatia. Onze iguais ainda passam se o
módulo 11 fechar.

---

## Phase 3: User Story 1 - CPF inválido na ficha do hóspede não entra na base (Priority: P1) 🎯 MVP

**Goal**: na coleta, CPF reprovado não grava o número; demais campos
ficam; ficha parcial; zero mensagem nova ao hóspede. CPF válido
grava onze dígitos.

**Independent Test**: interpretar/consolidar com os outros campos
preenchidos e `CPF_REPROVADO`: `numero_documento` vazio, status
`ficha_parcial`, gateway sem envio extra. Com `CPF_VALIDO_PONTUADO`:
onze dígitos gravados.

### Tests (escrever e ver falhar)

- [X] T004 [P] [US1] Estender
  `testes/unitarios/modulos/hospedagem/test_consolidar_ficha.py`
  e/ou `testes/unitarios/modulos/conversa/` da interpretação: ficha
  com tipo CPF e `CPF_REPROVADO` mais os outros oito utilizáveis —
  número **não** vai ao titular, desfecho/status parcial. Com
  `CPF_VALIDO_PONTUADO`, titular fica com onze dígitos. Nomes em
  português. Rodar e **ver falhar** se a consolidação ainda receber
  o número cru (FR-003, FR-010 coleta, [coleta.md](./contracts/coleta.md)).

- [X] T005 [P] [US1] Estender
  `testes/integracao/test_interpretar_ficha.py`: passagem com
  extração de CPF reprovado **não** dispara mensagem nova (gateway
  falso sem envio além do que a fatia de coleta já permite); reserva
  visível como parcial. Rodar e **ver falhar** (FR-005).

### Implementation

- [X] T006 [US1] Garantir que `refinar_resultado` /
  `consolidar_ficha_titular` em
  `app/modulos/conversa/` e `app/modulos/hospedagem/service.py`
  persistem só os campos já refinados (sem recado novo). Se T004 e
  T005 ficarem verdes só com T003, **não** reescrever o serviço —
  só o que faltar. Rodar T004 e T005 até **verde**. Log de
  consolidação inalterado (sem número).

**Checkpoint**: WhatsApp/simulador não grava CPF reprovado. Painel
ainda não tem aviso no campo nem formatação.

---

## Phase 4: User Story 2 - A recepção vê o recado na hora de salvar (Priority: P1)

**Goal**: PUT recusa o salvamento inteiro; `422` diz que o CPF não
confere, sem eco do número; o rascunho na tela permanece; aviso no
campo; leitura e cópia mostram `000.000.000-00`; CPF válido grava
onze dígitos.

**Independent Test**: PUT com endereço novo + `CPF_REPROVADO` →
`422`, banco igual ao antes, corpo sem o número. Na tela: recado no
campo, outros inputs iguais. PUT com `CPF_VALIDO_PONTUADO` → 200 e
onze dígitos; cópia pontuada.

### Tests (escrever e ver falhar)

- [X] T007 [P] [US2] Estender
  `testes/unitarios/modulos/hospedagem/test_completar_ficha.py`:
  tipo CPF + `CPF_REPROVADO` + outro campo alterado →
  `DadosInvalidos` cuja `str` deixa claro que o CPF não confere e
  **não** contém o número; `atualizar_hospede_titular` **não** é
  chamado. CPF válido pontuado grava onze dígitos. CEP/telefone
  inválidos continuam com a recusa atual. Rodar e **ver falhar**
  (FR-006, FR-011, [put-ficha.md](./contracts/put-ficha.md)).

- [X] T008 [P] [US2] Estender
  `testes/integracao/test_alterar_ficha.py`: PUT `422` não altera
  nenhum campo daquele salvamento; `200` com CPF pontuado válido
  persiste onze dígitos; log da recusa sem o número (`caplog` ou
  espião do logger). Rodar e **ver falhar** (FR-009, SC-003).

- [X] T009 [P] [US2] Estender
  `frontend/src/painel/TelaFicha.test.tsx`: após PUT `422` de CPF,
  o aviso aparece no campo número do documento; nome/endereço
  digitados **continuam** no formulário. Rodar e **ver falhar**.

- [X] T010 [P] [US2] Estender `frontend/src/painel/ficha.test.ts`:
  com tipo CPF e onze dígitos, `valor` visível / `montarTextoCopia`
  usam `000.000.000-00`; RG não pontua. Rodar e **ver falhar**
  (FR-002 superfície, [superficie-painel.md](./contracts/superficie-painel.md)).

### Implementation

- [X] T011 [US2] Em `app/modulos/hospedagem/service.py`, quando o
  inválido for o CPF, `DadosInvalidos` com recado de que o CPF não
  confere — MUST NOT interpolar o número. O aborto do lote **já
  existe**; não gravar o resto. Rodar T007 e T008 até **verde**.

- [X] T012 [P] [US2] Em `frontend/src/painel/ficha.ts`, formatar
  CPF na leitura e na cópia (`000.000.000-00`) só quando o tipo é
  CPF e há onze dígitos. Sem conferir dígito no cliente. Rodar T010
  até **verde**.

- [X] T013 [US2] Em `frontend/src/painel/TelaFicha.tsx`, amarrar o
  `422` de CPF ao campo número; **não** resetar o rascunho no erro
  (já não reseta — só garantir o recado no campo). Usar T012 na
  leitura. Rodar T009 até **verde**.

**Checkpoint**: painel recusa certo e mostra formatado. Onze iguais
e migração ainda não.

---

## Phase 5: User Story 3 - Sequências artificiais, demo e migração (Priority: P2)

**Goal**: onze dígitos iguais reprovados; massa de demonstração com
CPF que fecha; migração 0027 converte isolados, pula pares, loga ids
sem o número; UNIQUE intacto.

**Independent Test**: `CPF_ONZE_IGUAIS` ausente na validação e no
PUT. Duas linhas que colapsam na mesma forma de onze dígitos
permanecem; uma isolada vira onze dígitos; log `cpf_migracao_colisao`
com ids, sem CPF.

### Tests (escrever e ver falhar)

- [X] T014 [P] [US3] Estender
  `testes/unitarios/modulos/conversa/test_validacao_ficha.py`:
  `CPF_ONZE_IGUAIS` (com e sem pontuação) → número ausente. Rodar
  e **ver falhar** (FR-004).

- [X] T015 [P] [US3] Escrever
  `testes/unitarios/modulos/hospedagem/test_cpf_migracao.py`: função
  de planejamento recebe linhas `(id_hospede, numero)`; devolve ids
  a converter (grupo de um) e ids a pular (grupo ≥ 2). Casos: um
  pontuado isolado; um já em onze dígitos; par pontuado + dígitos
  iguais; três no mesmo grupo. Sem o número no que seria logado.
  Rodar e **ver falhar**.

### Implementation

- [X] T016 [US3] Em `app/modulos/conversa/validacao_ficha.py`,
  reprovar sequência de um só dígito. Rodar T014 até **verde**.

- [X] T017 [US3] Criar `app/modulos/hospedagem/cpf_migracao.py` com
  o planejamento da T015 (só ids; forma nova = dígitos). Rodar T015
  até **verde**.

- [X] T018 [US3] Revisão Alembic `0027` em
  `alembic/versions/0027_cpf_onze_digitos.py` (+ SQL se o padrão da
  casa pedir): lê `hospede` tipo `cpf` com número, aplica T017,
  `UPDATE` só os isolados, log `warning`
  `cpf_migracao_colisao pares=%s ids=%s` sem o CPF. MUST NOT
  dropar/recriar `uq_hospede_documento`. Comentário de
  `numero_documento` em `docs/04-schema.sql` se a forma canônica
  couber na frase (índice intocado). `0001` congelado. Teste de
  integração pontual em `testes/integracao/` se a suíte de migração
  já exercer upgrade — senão a T015 + aplicar 0027 no ambiente de
  teste basta. Rodar até **verde** (FR-012,
  [migracao-e-logs.md](./contracts/migracao-e-logs.md)).

- [X] T019 [P] [US3] Trocar `123.456.789-00` por `CPF_VALIDO`
  pontuado/onze dígitos em `docs/roteiro-de-teste.md` e
  `docs/wireframes-painel.html`. `scripts/semear_demo.py` não cria
  ficha — só ajustar se algum CPF inválido aparecer. FR-008.

**Checkpoint**: US3 fechada. Documentação de estado ainda na polish.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: estado do projeto e validação do quickstart.

- [X] T020 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: pendência
  “Validar `numero_documento`” desta fatia; o achado de 18/09 sobre
  CPF cru. Sem silenciar F9.3–F9.5.

- [X] T021 [P] Confirmar
  `testes/unitarios/modulos/acesso/test_politica.py` sem operação
  nova; nenhuma rota em `ROTAS_PUBLICAS`.

- [X] T022 Rodar a validação de [quickstart.md](./quickstart.md):
  `uv run pytest testes/unitarios/modulos/conversa/test_validacao_ficha.py
  testes/unitarios/modulos/hospedagem/test_completar_ficha.py
  testes/unitarios/modulos/hospedagem/test_cpf_migracao.py -q`;
  integração alterar_ficha e interpretar_ficha; `npm --prefix
  frontend test -- --run src/painel/TelaFicha.test.tsx
  src/painel/ficha.test.ts`. Tudo verde. Sem rede externa.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediato
- **Foundational (Phase 2)**: depois do Setup — **bloqueia** as histórias
- **US1 (Phase 3)**: depois da Foundational — MVP
- **US2 (Phase 4)**: depois da Foundational (o PUT já usa o
  validador); melhor depois da US1 se a mensagem de recusa
  reutilizar o mesmo critério
- **US3 (Phase 5)**: depois da Foundational; onze iguais podem
  seguir em paralelo com a US2; migração 0027 depois do planejamento
  (T015/T017)
- **Polish**: depois das histórias desejadas

### User Story Dependencies

- **US1 (P1)**: Foundational; sem dependência de US2–US3
- **US2 (P1)**: acoplada ao validador da Foundational
- **US3 (P2)**: acoplada ao validador; migração independente da
  superfície do painel

### Within Each User Story

- Teste vermelho **antes** da produção
- Uma asserção conceitual por teste
- História completa no checkpoint antes de avançar (salvo US2∥US3
  depois da Foundational)

### Parallel Opportunities

- T002 sozinha no Foundational (T003 depois)
- T004 ∥ T005
- T007 ∥ T008 ∥ T009 ∥ T010
- T012 ∥ T013 (depois dos testes da US2)
- T014 ∥ T015
- T019 ∥ T020 ∥ T021
- US2 e US3 (onze iguais) em paralelo após a Foundational, se duas
  pessoas

---

## Parallel Example: User Story 1

```text
T004 testes/unitarios/modulos/hospedagem/test_consolidar_ficha.py
T005 testes/integracao/test_interpretar_ficha.py
```

Depois, só T006 se ainda houver gap.

## Parallel Example: User Story 2

```text
T007 testes/unitarios/modulos/hospedagem/test_completar_ficha.py
T008 testes/integracao/test_alterar_ficha.py
T009 frontend/src/painel/TelaFicha.test.tsx
T010 frontend/src/painel/ficha.test.ts
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2
2. Phase 3 (US1)
3. **STOP**: coleta não grava CPF reprovado
4. Demo mínima: simulador com `CPF_REPROVADO` → ficha parcial

### Incremental Delivery

1. Setup + Foundational
2. US1 → hóspede não grava dígito trocado (MVP)
3. US2 → recepção vê o recado no campo
4. US3 → onze iguais, demo, migração
5. Polish

### Parallel Team Strategy

Um desenvolvedor: ordem US1 → US2 → US3. Dois: depois da
Foundational, um faz US1+coleta, o outro US2 na tela; US3 por último
(migração).

---

## Notes

- [P] = arquivos diferentes, sem dependência incompleta
- Sem Redis, Celery, PMS, foto de documento, CHECK de CPF, índice
  novo
- `0001` congelado
- Identidade de cadastros que colidem = F9.3 / F9.5
