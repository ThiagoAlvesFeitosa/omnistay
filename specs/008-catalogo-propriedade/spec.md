# Feature Specification: Catálogo da Propriedade

**Feature Branch**: `008-catalogo-propriedade`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "O hotel cadastra e mantém os fatos da propriedade organizados
por categoria: horários, cardápio, serviços, programação e regras. Esse conteúdo é a única
fonte a partir da qual o atendimento automatizado pode responder ao hóspede. Itens podem ser
desativados sem serem apagados."
(backlog F2.1)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cadastrar fatos da propriedade por categoria (Priority: P1)

Como recepcionista, quero registrar os fatos da propriedade — horários, cardápio, serviços,
programação e regras — cada um com um título e o texto do fato, para o hotel passar a ter uma
fonte única do que pode ser afirmado em nome da casa.

**Why this priority**: Sem catálogo cadastrado, o pacote de boas-vindas e o atendimento
automatizado não têm o que dizer. Esta fatia é o depósito de controle de alucinação: o que
não estiver aqui não pode ser inventado depois.

**Independent Test**: Pode ser testado autenticando como recepção, criando um item em cada
uma das cinco categorias e verificando que os cinco passam a constar no catálogo daquela
propriedade, com título, conteúdo, categoria e indicação de ativo.

**Acceptance Scenarios**:

1. **Given** uma sessão autenticada de perfil de recepção, **When** a pessoa informa
   categoria válida, título e conteúdo, **Then** o item é gravado no catálogo da propriedade
   da sessão, nasce ativo e fica disponível na consulta seguinte.
2. **Given** uma sessão de recepção, **When** a pessoa cadastra itens nas cinco categorias
   previstas (horários, cardápio, serviços, programação e regras), **Then** cada item fica
   associado à categoria informada e todos aparecem no catálogo daquela propriedade.
3. **Given** uma sessão de recepção, **When** a pessoa tenta gravar sem título, sem conteúdo
   ou com categoria fora das cinco previstas, **Then** o item não é criado e a recusa deixa
   claro o que está inválido.

---

### User Story 2 - Corrigir um fato e desativar sem apagar (Priority: P1)

Como recepcionista, quero editar o título e o conteúdo de um item já cadastrado e desativá-lo
quando deixar de valer — sem apagá-lo — para o hotel atualizar o que afirma sem perder o
histórico do que já foi publicado.

**Why this priority**: Cardápio, horário e regra mudam. Apagar destruiria o rastro do que o
hotel já afirmou; desativar retira o fato da fonte usada pelo atendimento sem apagar a linha.

**Independent Test**: Pode ser testado criando um item, alterando título e conteúdo, depois
desativando-o, e verificando que a edição persiste, o item continua recuperável pela recepção
e deixa de constar na consulta do catálogo ativo.

**Acceptance Scenarios**:

1. **Given** um item ativo da propriedade da sessão, **When** a recepção altera título e/ou
   conteúdo, **Then** a consulta seguinte devolve o texto novo e o item permanece ativo.
2. **Given** um item ativo, **When** a recepção o desativa, **Then** o item deixa de aparecer
   na consulta do catálogo ativo e continua visível para a recepção na manutenção, marcado
   como inativo.
3. **Given** um item desativado, **When** a recepção o reativa, **Then** ele volta a constar
   na consulta do catálogo ativo com o conteúdo que tinha ao ser reativado.
4. **Given** um item existente, **When** a recepção tenta removê-lo de forma permanente,
   **Then** a operação não é oferecida — o caminho suportado é desativar.

---

### User Story 3 - Consultar o catálogo ativo completo da propriedade (Priority: P1)

Como operação do hotel (e, nas fatias seguintes, o atendimento automatizado), quero obter de
uma só vez todos os fatos **ativos** da propriedade, organizados pelas cinco categorias, para
essa consulta ser a única fonte a partir da qual se pode afirmar algo em nome da casa.

**Why this priority**: O critério de aceite da fatia exige a consulta do catálogo ativo
completo. Sem ela, boas-vindas (F2.2) e resposta a dúvida (F3.3) não têm de onde ler. Item
desativado não pode vazar para essa consulta — senão o atendimento afirmaria o que o hotel
já retirou.

**Independent Test**: Pode ser testado com uma propriedade que tenha itens ativos e inativos
em categorias distintas, pedindo o catálogo ativo completo, e verificando que vêm todos os
ativos, nenhum inativo, e nenhum item de outro hotel.

**Acceptance Scenarios**:

1. **Given** uma propriedade com itens ativos nas cinco categorias e pelo menos um item
   desativado, **When** se consulta o catálogo ativo completo daquela propriedade, **Then** a
   resposta contém todos os itens ativos, agrupados por categoria, e omite os desativados.
2. **Given** uma propriedade sem nenhum item ativo, **When** se consulta o catálogo ativo
   completo, **Then** a resposta é vazia e explícita — não é erro; o hotel ainda não publicou
   fatos.
3. **Given** o catálogo ativo de uma propriedade, **When** ele é inspecionado, **Then** cada
   item traz identificador, categoria, título e conteúdo — o suficiente para uma fatia
   posterior afirmar o fato sem reler a manutenção.

---

### User Story 4 - Isolar o catálogo por hotel e por perfil (Priority: P1)

Como responsável pelos dados da propriedade, quero que o catálogo de um hotel nunca apareça
para outro, que só a recepção crie, edite e desative itens, e que a gestão consulte sem
alterar, para um hotel não falar pelos fatos do vizinho e o perfil de consulta não virar
editor.

**Why this priority**: Multi-tenant e autorização já existem; esta fatia é a primeira que
grava o depósito de fatos e precisa herdar essas fronteiras. A matriz da autenticação já
reservou a alteração do catálogo à recepção.

**Independent Test**: Pode ser testado criando itens em dois hotéis e tentando listar, criar,
editar e desativar com cada perfil, verificando isolamento e recusas.

**Acceptance Scenarios**:

1. **Given** itens cadastrados no hotel A, **When** uma sessão do hotel B consulta o próprio
   catálogo (manutenção ou ativo), **Then** nenhum item do hotel A aparece.
2. **Given** uma sessão de perfil de gestão, **When** ela consulta o catálogo da própria
   propriedade, **Then** a leitura é permitida; **When** tenta criar, editar, desativar ou
   reativar, **Then** a alteração é recusada.
3. **Given** uma sessão de perfil operacional, **When** tenta ler ou alterar o catálogo,
   **Then** a operação é recusada.
4. **Given** uma sessão de recepção do hotel A, **When** tenta alterar um item que pertence
   ao hotel B, **Then** a alteração é recusada sem revelar que o item existe.

---

### Edge Cases

- Catálogo vazio na instalação: a propriedade nasce sem itens; a consulta ativa devolve
  conjunto vazio; não há semeadura de cardápio ou horário de exemplo.
- Título repetido na mesma categoria: permitido; a recepção distingue pelo identificador. Não
  há deduplicação silenciosa.
- Edição de item já desativado: permitida; o item permanece inativo até ser reativado.
- Tentativa de gravar categoria fora de horários, cardápio, serviços, programação e regras:
  recusada, sem criar o item.
- Título ou conteúdo só com espaços: recusado como campo ausente.
- Dois hotéis com o mesmo título de item: cada um vê só o seu; não há catálogo global.
- Reativação de item que nunca existiu ou de outro hotel: recusada sem revelar existência
  alheia.
- Conteúdo de mensagem de hóspede não se aplica a esta fatia; logs de manutenção registram
  identificador do item, categoria, hotel e ação — não precisam repetir o texto completo do
  fato.
- Pacote de boas-vindas, resposta automática a dúvida do hóspede, pedido faturável e tela
  React de manutenção **não** fazem parte desta fatia.
- Preço estruturado de item vendável **não** faz parte desta fatia (ver Assumptions).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A recepção MUST poder criar um item de catálogo informando categoria, título e
  conteúdo, vinculado à propriedade da sessão.
- **FR-002**: A categoria MUST ser uma das cinco previstas: horários, cardápio, serviços,
  programação e regras. Qualquer outro valor MUST ser recusado.
- **FR-003**: Título e conteúdo MUST ser obrigatórios e MUST ter texto visível (não apenas
  espaços). Ausência MUST impedir a criação ou a edição.
- **FR-004**: Item recém-criado MUST nascer ativo.
- **FR-005**: A recepção MUST poder alterar título e conteúdo de um item da própria
  propriedade, esteja ele ativo ou inativo.
- **FR-006**: A recepção MUST poder desativar um item da própria propriedade. Desativar MUST
  NOT apagar o item.
- **FR-007**: A recepção MUST poder reativar um item desativado da própria propriedade.
- **FR-008**: O sistema MUST NOT oferecer remoção permanente de item de catálogo.
- **FR-009**: A recepção MUST poder listar todos os itens da própria propriedade, ativos e
  inativos, com indicação distinguível de ativo/inativo e da categoria.
- **FR-010**: O sistema MUST oferecer uma consulta do catálogo ativo completo de uma
  propriedade: todos os itens ativos, e somente os ativos, nas cinco categorias.
- **FR-011**: Item desativado MUST ser omitido da consulta do catálogo ativo. Essa consulta é
  a única fonte que o atendimento automatizado posterior MAY usar para afirmar fato da
  propriedade.
- **FR-012**: Esta fatia MUST NOT responder pergunta de hóspede, MUST NOT enviar pacote de
  boas-vindas e MUST NOT registrar consumo. Ela entrega a manutenção e a consulta; o uso
  conversacional fica para as fatias que dependem dela.
- **FR-013**: Toda leitura e toda escrita de catálogo MUST considerar o hotel da sessão.
  Catálogo de um hotel MUST NOT ser visível nem alterável por outro.
- **FR-014**: Criar, editar, desativar e reativar MUST ser exclusivos do perfil de recepção.
  Gestão e perfil operacional MUST receber recusa ao tentar alterar.
- **FR-015**: A gestão MUST poder consultar o catálogo da própria propriedade (manutenção e
  catálogo ativo) e MUST NOT poder alterá-lo.
- **FR-016**: O perfil operacional MUST receber recusa ao tentar ler ou alterar o catálogo.
- **FR-017**: Tentativa de alterar item de outro hotel MUST ser recusada sem confirmar que o
  item existe.
- **FR-018**: Logs de manutenção MUST registrar identificador do item, hotel, categoria e
  ação (criar, editar, desativar, reativar). MUST NOT registrar conteúdo de mensagem de
  hóspede. Texto completo do fato MUST NOT ser o conteúdo principal do log.
- **FR-019**: Esta fatia MUST NOT introduzir preço, identificador vendável separado, nem
  qualquer estrutura cujo propósito seja cobrar o hóspede. Item de catálogo nesta fatia é
  fato afirmável, não item de cobrança.

### Key Entities

- **Item de catálogo**: um fato da propriedade (título + conteúdo) em uma categoria, com
  indicação de ativo ou inativo. É o que delimita o que o atendimento automatizado poderá
  afirmar.
- **Categoria**: um de cinco valores fechados — horários, cardápio, serviços, programação,
  regras. Não há categoria livre nesta fatia.
- **Catálogo ativo**: o conjunto de todos os itens ativos de uma propriedade, obtido por uma
  consulta única. Fonte exclusiva para afirmações posteriores em nome do hotel.
- **Catálogo de manutenção**: a lista completa da propriedade, incluindo inativos, usada pela
  recepção (e consultada pela gestão) para criar, corrigir, desativar e reativar.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das criações com categoria válida, título e conteúdo preenchidos, o
  item nasce ativo no catálogo da propriedade da sessão e aparece na consulta seguinte.
- **SC-002**: Em 100% das tentativas com categoria inválida, título ausente ou conteúdo
  ausente, o item não é criado e a recusa identifica o problema.
- **SC-003**: Em 100% das desativações, o item desaparece da consulta do catálogo ativo e
  permanece recuperável na manutenção como inativo; 0 itens são apagados.
- **SC-004**: Em 100% das consultas do catálogo ativo de uma propriedade com itens mistos
  (ativos e inativos), a resposta contém todos os ativos e 0 inativos.
- **SC-005**: Em verificação com dois hotéis, 0% dos itens de um hotel aparecem no catálogo
  (manutenção ou ativo) do outro.
- **SC-006**: Em verificação com sessão de gestão, 100% das tentativas de criar, editar,
  desativar ou reativar são recusadas, e 100% das consultas da própria propriedade são
  permitidas.
- **SC-007**: Em verificação com sessão operacional, 100% das tentativas de ler ou alterar o
  catálogo são recusadas.
- **SC-008**: A recepção conclui o cadastro de um fato (categoria, título e conteúdo) em uma
  única interação, sem etapas intermediárias obrigatórias.
- **SC-009**: O caminho criar → editar → desativar → consultar ativo (item ausente) →
  reativar → consultar ativo (item presente) é verificável de ponta a ponta sem depender de
  canal de mensagens nem de atendimento automatizado.

## Assumptions

- A fatia F0.3 (autenticação e perfis) está concluída. Esta fatia passa a exercitar a
  operação já reservada à recepção na matriz de autorização (`alterar_catalogo`) e confirma
  a escolha de a gestão consultar sem alterar — revisitável só com decisão registrada, não
  nesta spec.
- Superfície de uso: comportamento observável pela manutenção do catálogo e pela consulta do
  catálogo ativo. Ligar o protótipo React continua fora do critério de pronto, no mesmo
  padrão das fatias de hospedagem já entregues.
- As cinco categorias são o domínio fechado já modelado. Não há categoria “outros” nem
  categoria definida pelo hotel no MVP.
- A propriedade nasce com catálogo vazio. Não há item de exemplo no bootstrap.
- **Preço estruturado fica fora.** O estado do projeto registrava um desenho a fechar antes
  desta fatia: item vendável com preço em campo próprio, para a cobrança não depender de a
  automação extrair número do texto. Esta spec **fecha essa pendência por adiamento**: F2.1
  entrega fatos em texto por categoria, que é o que o pacote de boas-vindas precisa. Item
  vendável com preço, identificação no pedido e `valor_praticado` como retrato do momento
  pertencem à fatia de consumo faturável (F3.7), quando a cobrança existir. Incluir preço
  agora inflaria esta fatia sem consumidor. Reabrir o desenho na F3.7, se o texto corrido
  for insuficiente para cobrar, é mudança de esquema explícita — não desta entrega.
- A consulta do catálogo ativo completo é o contrato que F2.2 (boas-vindas) e F3.3
  (responder dúvida) vão consumir. Esta fatia não monta mensagem ao hóspede.
- Duplicata de título na mesma categoria é permitida; não há consolidação automática.
- Conteúdo do item é texto do fato (horário, prato, regra). Não há anexo, imagem nem
  documento de identidade — o catálogo não é dado cadastral de hóspede.
- Isolamento por propriedade vale mesmo com uma única propriedade cadastrada.
