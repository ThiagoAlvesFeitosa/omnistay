# Specification Quality Checklist: Autenticação e Perfis

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-11
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — com duas exceções deliberadas,
      registradas nas notas
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Cobertura dos critérios de aceite do backlog (F0.3)

| Critério do backlog | Onde está coberto |
| --- | --- |
| Usuário sem credencial válida não acessa recurso protegido | FR-008, US2 cenário 2, SC-002 |
| Perfil operacional recusado ao ler dado cadastral de hóspede | FR-018, US3 cenário 1, SC-003 |
| Perfil de gestão recusado ao alterar dado de domínio | FR-019, US3 cenário 2, SC-004 |
| Sessão do perfil operacional válida por período longo no dispositivo | FR-011, US4 cenário 1, SC-006 |
| Sessão pode ser revogada pela recepção | FR-014, US5 cenário 1, SC-005 |
| Senha nunca armazenada em texto legível | FR-002, SC-007 |
| *(acrescentado)* Comando de bootstrap | FR-025 a FR-029, US1, SC-001 |

## Notas

**Duas exceções deliberadas ao item "no implementation details":**

1. **Transporte do token de sessão** (FR-006). Fechado na spec por decisão explícita: é contrato
   entre backend e painel, e a escolha de sessão longa no celular da equipe depende dele. Deixá-lo
   para o `/plan` faria a F1.1 herdar uma escolha feita por acidente.
2. **Exigência de migração e atualização do `04-schema.sql`** (FR-031). A regra do projeto é que
   toda alteração de modelo gere migração e atualização do documento na mesma entrega. Omitir isso
   da spec deixaria a mudança de esquema invisível até o `/plan`.

**Correções de artefato exigidas por esta fatia:**

- `docs/backlog.md`, F0.3: o critério "Perfil de gestão recebe recusa ao tentar alterar qualquer
  dado" era ambíguo o bastante para tornar impossível a administração de usuários. Reescrito para
  "qualquer dado de domínio", com a lista explícita. **Feito nesta entrega.**
- `docs/00-ESTADO-DO-PROJETO.md`: registrar as decisões desta fatia — administração de usuários na
  gestão, revogação de sessão na recepção, tabela de sessão, transporte por cookie e ausência de
  auditoria de criação de usuário. **Pendente, junto do commit da fatia.**

**Escolhas de escopo registradas como escolha, não como lacuna:** ausência de contenção de
tentativa repetida de senha, ausência de troca e redefinição de senha, ausência de registro de
último uso da sessão, alteração dos parâmetros por SQL. Todas justificadas em Assumptions.

- Items marked incomplete require spec updates before `/speckit-clarify` or `/speckit-plan`
