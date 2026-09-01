# Specification Quality Checklist: Consumos a lançar e saída do hóspede

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-31
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
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

## Notes

Validação em 2026-08-31 (1ª passagem): todos os itens passaram.

- Sem marcadores `[NEEDS CLARIFICATION]`. Ambiguidades de escopo
  foram fechadas em Assumptions com os defaults do backlog F8.5, da
  constituição e das fatias já entregues: fila de pendentes, lançar,
  dispensar, confirmar saída e lista cobrável são reusados, não
  reabertos; o mapa de telas que mostra nome na fila financeira,
  coluna de lançamento por item e checkout na própria fila é
  rascunho — esta fatia segue as operações já existentes (lista sem
  cadastral, aviso de pendência na estadia, caminho na fila que abre
  a tela de saída); aviso não trava o checkout; gestão não opera
  estas telas (F8.7); catálogo e itens vendáveis são F8.6.
- Linguagem de negócio: Consumos a lançar, Saída do hóspede,
  pedidos feitos pelo chat, valor praticado, tempo de espera, total
  pendente, lançado, dispensado, aviso de pendência, destaque de
  saída não confirmada. Sem stack, sem rotas, sem nomes de arquivo.
- Os cinco critérios de aceite do backlog F8.5 têm cenário
  correspondente (US1, US2, US4, US4/US5, US4).
- Pronto para `/speckit-plan`. O plano da semana recomenda pular
  `/speckit-clarify` nas fatias de tela, porque o mapa de telas e
  as operações já entregues cobrem o recorte. Se o default de não
  mostrar nome na fila financeira, o de não travar o checkout ou o
  de confirmar só na tela de saída (não na fila) não forem aceitos,
  aí sim esclarecer antes de planejar.
