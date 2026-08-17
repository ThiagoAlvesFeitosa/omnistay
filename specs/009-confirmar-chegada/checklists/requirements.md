# Specification Quality Checklist: Confirmar Chegada e Boas-vindas

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-17
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

- Validação 2026-08-17: todos os itens passaram na primeira iteração.
- Revalidação 2026-08-17 após `/speckit-clarify` (4 perguntas): 16/16 mantidos.
- Máquina de estados, catálogo ativo, fila do dia e “chegada não confirmada” são
  vocabulário de domínio já modelado, não stack.
- **Mudança de escopo na clarificação:** o pacote de boas-vindas deixou de ser “o catálogo
  ativo das quatro categorias” e passou a ser mensagem curta — chegada + três informações de
  entrada (café, wi-fi, checkout) + convite a perguntar. Motivo técnico: variável de template
  não aceita quebra de linha, tabulação nem mais de quatro espaços seguidos, então catálogo
  inteiro numa variável não é enviável. O catálogo completo responde sob demanda na F3.3.
- Três slots obrigatórios em `parametro_hotel`, validados na gravação, semeados na instalação.
  Slot vazio: check-in ocorre, mensagem não sai, fila sinaliza.
- Recuperação limitada à janela de validade contada do instante do check-in, para completar a
  configuração não virar rajada de template pago (inclusive para quem já saiu).
- **Correção no planejamento (17/08/2026):** a janela era `data_checkin_prevista` igual ao dia
  corrente. Chegada às 23h30, slots preenchidos às 23h40 e varredura às 00h05 saíam da
  elegibilidade pela virada do dia civil, e o pacote nunca saía — falha silenciosa, justamente
  o que a fatia combate. O eixo passou a ser `checkin_em`, com duração em `parametro_hotel`
  (`horas_validade_boas_vindas`, padrão 12) por causa do Artigo XIII. Requisitos novos:
  FR-031a, FR-031b, FR-032a; critério novo: SC-016a.
- Unicidade do pacote é restrição de armazenamento, no padrão da idempotência de webhook.
- Permissão por grupo de chaves (`alterar_texto_de_boas_vindas`), nunca genérica sobre
  `parametro_hotel` — parâmetro de comportamento continua fora do alcance da recepção.
- Chaves de configuração e nome de operação aparecem em Clarifications/Assumptions como
  vocabulário de domínio já existente; os requisitos e critérios permanecem comportamentais.
- Tela React permanece fora do critério de pronto, no padrão das fatias anteriores.
- Pronto para `/speckit-plan`.
