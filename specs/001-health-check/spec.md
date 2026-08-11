# Feature Specification: Verificação de Saúde da Aplicação

**Feature Branch**: `001-health-check`

**Created**: 2026-08-10

**Status**: Draft

**Input**: User description: "Um endpoint de verificação de saúde que informa se a aplicação
está no ar e se o banco de dados responde. Deve retornar sucesso quando ambos estão
disponíveis e indicar falha explícita quando o banco não responde, sem derrubar a
aplicação."

## Clarifications

### Session 2026-08-10

- Q: Quando a aplicação está no ar mas o banco não responde, a resposta HTTP do endpoint
  deve ser tratada como falha geral ou como sucesso HTTP com corpo indicando degradação?
  → A: Resposta HTTP de falha geral (indisponível), com corpo estruturado indicando
  aplicação ok e banco indisponível.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirmar que o sistema está operacional (Priority: P1)

Como responsável por operação ou implantação, quero consultar um ponto único de verificação
de saúde para saber se a aplicação está no ar e se consegue acessar o banco de dados,
para decidir com confiança se o ambiente está pronto para receber tráfego.

**Why this priority**: Sem essa confirmação positiva, nenhum monitoramento ou pipeline de
implantação consegue validar que o ambiente está funcional. É o caso de uso base.

**Independent Test**: Pode ser testado isoladamente simulando aplicação e banco disponíveis e
verificando que a resposta indica sucesso para ambos os componentes.

**Acceptance Scenarios**:

1. **Given** a aplicação está em execução e o banco de dados responde a uma verificação de
   conectividade, **When** o responsável consulta o endpoint de saúde, **Then** a resposta
   indica sucesso explícito para a aplicação e para o banco de dados.
2. **Given** a aplicação está em execução e o banco responde, **When** o endpoint é
   consultado, **Then** a resposta é obtida sem exigir autenticação nem contexto de hotel.

---

### User Story 2 - Detectar indisponibilidade do banco sem derrubar a aplicação (Priority: P1)

Como responsável por operação, quero que uma falha de conectividade com o banco seja reportada
de forma explícita pelo endpoint de saúde, mantendo a aplicação em execução, para que eu
identifique a causa sem perder a capacidade de diagnosticar o problema.

**Why this priority**: Igualmente crítico ao caso de sucesso — um health check que derruba a
aplicação ou omite a falha do banco anula o propósito da funcionalidade.

**Independent Test**: Pode ser testado isoladamente simulando banco indisponível e verificando
que o endpoint responde com falha explícita enquanto a aplicação continua atendendo a
consulta.

**Acceptance Scenarios**:

1. **Given** a aplicação está em execução e o banco de dados não responde, **When** o
   responsável consulta o endpoint de saúde, **Then** a resposta HTTP indica falha geral
   (serviço indisponível para tráfego) e o corpo indica falha explícita do banco de dados,
   com a aplicação reportada como no ar.
2. **Given** a aplicação está em execução e o banco de dados não responde, **When** o endpoint
   é consultado, **Then** a aplicação permanece em execução e continua capaz de responder a
   novas consultas ao endpoint de saúde.
3. **Given** o banco está indisponível, **When** o endpoint responde com falha, **Then** a
   resposta distingue claramente o estado da aplicação (no ar) do estado do banco
   (indisponível).

---

### Edge Cases

- O que acontece quando o banco responde lentamente além de um tempo limite razoável? A
  verificação deve tratar timeout como indisponibilidade do banco, sem travar a aplicação.
- O que acontece quando o endpoint é consultado repetidamente em sequência? Cada consulta
  deve retornar o estado atual sem efeitos colaterais no sistema.
- O endpoint verifica apenas conectividade com o banco, não a integridade de dados nem
  disponibilidade de serviços externos (mensageria, IA, PMS).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE expor um endpoint público de verificação de saúde acessível sem
  autenticação.
- **FR-002**: O endpoint DEVE reportar explicitamente se a aplicação está no ar.
- **FR-003**: O endpoint DEVE reportar explicitamente se o banco de dados responde a uma
  verificação de conectividade.
- **FR-004**: Quando a aplicação e o banco estão disponíveis, o endpoint DEVE responder com
  indicação de sucesso para ambos os componentes.
- **FR-005**: Quando o banco de dados não responde (incluindo timeout), o endpoint DEVE
  responder com status HTTP de falha geral (serviço indisponível), corpo estruturado com
  aplicação no ar e banco indisponível, mantendo o processo da aplicação em execução.
- **FR-010**: Quando a aplicação e o banco estão disponíveis, o endpoint DEVE responder com
  status HTTP de sucesso geral.
- **FR-006**: A verificação de saúde NÃO DEVE depender de integração com PMS, mensageria ou
  provedor de IA.
- **FR-007**: A verificação de saúde NÃO DEVE registrar conteúdo sensível em logs além de
  identificadores e códigos de erro (Artigo VIII da constituição).
- **FR-008**: DEVE existir teste automatizado que comprove resposta de sucesso com banco
  disponível.
- **FR-009**: DEVE existir teste automatizado que comprove resposta de falha explícita com
  banco indisponível, sem encerrar a aplicação.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em ambiente com banco disponível, 100% das consultas ao endpoint retornam
  indicação de sucesso em até 2 segundos.
- **SC-002**: Em ambiente com banco indisponível, 100% das consultas retornam status HTTP de
  falha geral e corpo com falha explícita do banco em até 3 segundos, e a aplicação
  permanece respondendo.

  > Corrigido em 2026-08-11 após medição real (antes: 2 segundos). O cliente PostgreSQL
  > eleva qualquer `connect_timeout` menor que 2 para 2 segundos, então o caminho de falha
  > não consegue responder abaixo desse piso. Medido: 2,02 s com o timeout padrão de 1 s.
- **SC-003**: Os dois cenários de aceite (banco disponível e indisponível) possuem teste
  automatizado que falha na ausência da funcionalidade e passa após implementação correta
  (Artigo XII da constituição).
- **SC-004**: Responsáveis por operação conseguem determinar o estado de saúde da aplicação
  e do banco em uma única consulta, sem acesso ao painel interno.

## Assumptions

- O endpoint é destinado a monitoramento interno e pipelines de implantação, não a hóspedes
  ou recepcionistas.
- "Banco disponível" significa que uma verificação leve de conectividade completa com sucesso;
  não inclui validação de esquema, migrações pendentes ou integridade de dados.
- "Falha explícita" combina status HTTP de falha geral (quando o banco está indisponível)
  com corpo estruturado que identifica claramente qual componente falhou (aplicação vs.
  banco), distinguível de sucesso por leitura humana ou por consumidor automatizado
  (balanceador, pipeline de deploy).
- Timeout de conectividade com o banco é configurável por `HEALTH_DB_TIMEOUT_SECONDS`, com
  padrão de 1 segundo. O piso de 2 segundos imposto pelo cliente PostgreSQL determina o
  tempo real do caminho de falha; valores configurados acima de 2 segundos passam a valer
  integralmente.
- Não há requisito de verificar worker, fila ou outros processos nesta funcionalidade —
  escopo limitado à API e ao banco de dados conforme descrição do usuário.
- O endpoint não expõe informações que permitam fingerprinting do ambiente além do necessário
  para diagnóstico operacional (estado da aplicação e do banco).
