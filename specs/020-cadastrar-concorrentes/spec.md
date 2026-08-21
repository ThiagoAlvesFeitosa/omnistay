# Feature Specification: Cadastro de Concorrentes

**Feature Branch**: `020-cadastrar-concorrentes`

**Created**: 2026-08-20

**Status**: Draft

**Input**: User description: "O hotel cadastra os concorrentes que deseja acompanhar,
informando nome e endereço da fonte pública de consulta. Fontes podem ser
desativadas sem serem apagadas."
(backlog F5.1)

Restrições já decididas no projeto (entrada do specify): o sistema **não** se
integra ao sistema de gestão do hotel nem promete alterar tarifa — a lista
define o que o hotel quer observar, não o que cobra; cada propriedade vê só
os próprios concorrentes; desativar não apaga; fonte desativada não entra
na consulta que a coleta posterior usará; esta fatia **não** visita a fonte,
**não** grava preço e **não** monta o painel de mercado; conteúdo de
mensagem de hóspede nunca vai para log.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cadastrar concorrente com nome e fonte (Priority: P1)

Como gestão do hotel, quero registrar cada concorrente que a casa deseja
acompanhar, com o nome da propriedade e o endereço da fonte pública onde o
preço e a avaliação aparecem sem login, para o hotel deixar de depender de
alguém lembrar de abrir o site na mão — e para a coleta automática da fatia
seguinte ter o que consultar.

**Why this priority**: Sem lista cadastrada, a inteligência de mercado não
tem alvo. Esta fatia é o depósito do “quem acompanhar”; coletar e exibir
preço vêm depois e não inventam concorrente.

**Independent Test**: Pode ser testado autenticando como gestão, cadastrando
um concorrente com nome e endereço de fonte pública, e verificando que ele
nasce ativo na propriedade da sessão e aparece na consulta seguinte, com os
dois campos gravados.

**Acceptance Scenarios**:

1. **Given** uma sessão autenticada de perfil de gestão, **When** a pessoa
   informa nome e endereço de fonte pública de consulta, **Then** o
   concorrente é gravado na propriedade da sessão, nasce ativo e fica
   disponível na consulta seguinte.
2. **Given** uma sessão de gestão, **When** a pessoa tenta gravar sem nome,
   sem endereço, com nome ou endereço só de espaços, ou com um texto que
   não é um endereço da web público e completo, **Then** o concorrente não
   é criado e a recusa deixa claro o que está inválido.
3. **Given** um concorrente já cadastrado na propriedade, **When** a gestão
   tenta cadastrar outro com o mesmo endereço de fonte, **Then** o segundo
   não é criado e a recusa indica que aquela fonte já existe na casa.

---

### User Story 2 - Corrigir e desativar sem apagar (Priority: P1)

Como gestão do hotel, quero corrigir nome ou endereço de um concorrente já
cadastrado e desativá-lo quando a casa deixar de acompanhá-lo — sem
apagá-lo — para atualizar a lista sem perder o rastro do que já foi
monitorado e sem deixar fonte morta na consulta futura.

**Why this priority**: Concorrente muda de marca, de site ou deixa de
interessar. Apagar destruiria o histórico que a coleta posterior vai
pendurar nessa ficha; desativar retira a fonte da consulta sem apagar a
linha. É o critério de aceite da fatia.

**Independent Test**: Pode ser testado criando um concorrente, alterando
nome e endereço, desativando-o e reativando-o, e verificando que a edição
persiste, a ficha continua recuperável na manutenção e some da lista de
fontes ativas enquanto estiver desativado.

**Acceptance Scenarios**:

1. **Given** um concorrente ativo da propriedade da sessão, **When** a
   gestão altera nome e/ou endereço da fonte, **Then** a consulta seguinte
   devolve os valores novos e o concorrente permanece ativo.
2. **Given** um concorrente ativo, **When** a gestão o desativa, **Then**
   ele deixa de aparecer na lista de fontes ativas e continua visível na
   manutenção, marcado como inativo — a ficha **não** é apagada.
3. **Given** um concorrente desativado, **When** a gestão o reativa,
   **Then** ele volta a constar na lista de fontes ativas com o nome e o
   endereço que tinha ao ser reativado.
4. **Given** um concorrente existente, **When** a gestão tenta removê-lo de
   forma permanente, **Then** a operação não é oferecida — o caminho
   suportado é desativar.
5. **Given** um concorrente ativo na propriedade, **When** a gestão tenta
   mudar o endereço da fonte para um que já pertence a outro concorrente
   da mesma casa, **Then** a alteração é recusada e o endereço anterior
   permanece.

---

### User Story 3 - Só fonte ativa entra na consulta de acompanhamento (Priority: P1)

Como hotel, quero uma consulta única das fontes **ativas** da propriedade —
nome, endereço e identificador — para a coleta da fatia seguinte consultar
somente o que a gestão ainda quer acompanhar, e para uma fonte desativada
nunca ser tratada como alvo.

**Why this priority**: “Fonte desativada não é consultada” só é testável se
existir o conjunto que a coleta vai ler. Sem essa consulta, a fatia
seguinte teria de adivinhar a regra, ou consultaria inativo por engano.

**Independent Test**: Pode ser testado com uma propriedade que tenha
concorrentes ativos e inativos, pedindo a lista de fontes ativas, e
verificando que vêm todos os ativos, nenhum inativo, e nenhum concorrente
de outro hotel. Esta fatia **não** acessa as fontes.

**Acceptance Scenarios**:

1. **Given** uma propriedade com ao menos um concorrente ativo e um
   desativado, **When** se consulta a lista de fontes ativas daquela
   propriedade, **Then** a resposta contém todos os ativos (nome,
   endereço e identificador) e omite os desativados.
2. **Given** uma propriedade sem nenhum concorrente ativo, **When** se
   consulta a lista de fontes ativas, **Then** a resposta é vazia e
   explícita — não é erro; o hotel ainda não escolheu quem acompanhar.
3. **Given** a lista de fontes ativas, **When** esta fatia é exercitada,
   **Then** nenhuma fonte é visitada, nenhum preço é gravado e nenhum
   painel de mercado é montado — a consulta devolve o cadastro, não o
   resultado da coleta.
4. **Given** a manutenção da lista (ativos e inativos), **When** a gestão
   consulta, **Then** vê todos os concorrentes da própria propriedade com
   indicação distinguível de ativo ou inativo.

---

### User Story 4 - Isolar a lista por hotel e por perfil (Priority: P1)

Como responsável pelos dados da propriedade, quero que o concorrente de um
hotel nunca apareça para outro, que só a gestão crie, edite, desative e
reative, e que recepção e operação sejam recusadas, para a casa vizinha não
ver a estratégia de acompanhamento e o balcão não virar editor de mercado.

**Why this priority**: Multi-tenant e autorização já existem; esta é a
primeira fatia que grava o depósito de mercado e precisa herdar essas
fronteiras. Inteligência de mercado é processo da gestão, não do balcão nem
da manutenção.

**Independent Test**: Pode ser testado criando concorrentes em dois hotéis
e tentando listar, criar, editar e desativar com cada perfil, verificando
isolamento e recusas.

**Acceptance Scenarios**:

1. **Given** concorrentes cadastrados no hotel A, **When** uma sessão do
   hotel B consulta a própria lista (manutenção ou fontes ativas),
   **Then** nenhum concorrente do hotel A aparece.
2. **Given** uma sessão de perfil de gestão, **When** ela cria, edita,
   desativa, reativa ou consulta concorrentes da própria propriedade,
   **Then** a operação é permitida.
3. **Given** uma sessão de perfil de recepção, **When** tenta ler ou
   alterar concorrentes, **Then** a operação é recusada.
4. **Given** uma sessão de perfil operacional, **When** tenta ler ou
   alterar concorrentes, **Then** a operação é recusada.
5. **Given** uma sessão de gestão do hotel A, **When** tenta alterar um
   concorrente que pertence ao hotel B, **Then** a alteração é recusada
   sem revelar que o concorrente existe.

---

### Edge Cases

- Propriedade recém-instalada: nasce sem concorrentes; a lista de fontes
  ativas devolve conjunto vazio; não há concorrente de exemplo na
  instalação.
- Nome repetido na mesma propriedade: permitido (duas casas podem ter
  nome parecido e fontes diferentes). A gestão distingue pelo
  identificador. Não há deduplicação silenciosa pelo nome.
- Mesmo endereço de fonte na mesma propriedade: recusado, inclusive se o
  já cadastrado estiver desativado — o caminho é reativar ou editar, não
  criar ficha duplicada. Diferença só de maiúsculas ou de espaços nas
  pontas conta como o mesmo endereço.
- Dois hotéis com o mesmo endereço de fonte: cada um vê só o seu; não há
  lista global de concorrentes.
- Edição de concorrente já desativado: permitida; ele permanece inativo
  até ser reativado.
- Nome ou endereço só com espaços: recusado como campo ausente.
- Endereço que não é da web público e completo (texto solto, caminho
  interno, endereço de e-mail): recusado, sem criar nem alterar.
- Reativação de concorrente que nunca existiu ou de outro hotel: recusada
  sem revelar existência alheia.
- Esta fatia **não** visita a fonte, **não** lê diretivas de acesso,
  **não** verifica termos de uso sozinha e **não** coleta preço nem
  avaliação. Quem cadastra escolhe fonte pública; a coleta honesta fica
  para a fatia seguinte.
- Coleta agendada, painel de preços com data, periodicidade da coleta e
  tela visual de manutenção **não** fazem parte desta fatia.
- Remoção permanente não é oferecida: a ficha precisa permanecer para o
  histórico de coletas da fatia seguinte se apoiar nela.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A gestão MUST poder criar um concorrente informando nome e
  endereço da fonte pública de consulta, vinculado à propriedade da
  sessão.
- **FR-002**: Nome e endereço MUST ser obrigatórios e MUST ter texto
  visível (não apenas espaços). Ausência MUST impedir a criação ou a
  edição.
- **FR-003**: O endereço da fonte MUST ser um endereço da web público e
  completo. Texto que não seja esse tipo de endereço MUST ser recusado.
- **FR-004**: Concorrente recém-criado MUST nascer ativo.
- **FR-005**: A gestão MUST poder alterar nome e endereço de um
  concorrente da própria propriedade, esteja ele ativo ou inativo.
- **FR-006**: A gestão MUST poder desativar um concorrente da própria
  propriedade. Desativar MUST NOT apagar a ficha.
- **FR-007**: A gestão MUST poder reativar um concorrente desativado da
  própria propriedade.
- **FR-008**: O sistema MUST NOT oferecer remoção permanente de
  concorrente.
- **FR-009**: A mesma propriedade MUST NOT ter dois concorrentes com o
  mesmo endereço de fonte. A segunda criação ou a edição que colida MUST
  ser recusada, mesmo que a ficha já existente esteja desativada.
- **FR-010**: A gestão MUST poder listar todos os concorrentes da própria
  propriedade, ativos e inativos, com indicação distinguível de
  ativo/inativo, nome e endereço.
- **FR-011**: O sistema MUST oferecer uma consulta das fontes ativas de
  uma propriedade: todos os concorrentes ativos, e somente os ativos,
  com identificador, nome e endereço. Fonte desativada MUST ser omitida
  dessa consulta.
- **FR-012**: A consulta de fontes ativas é o conjunto que a coleta
  posterior MAY usar. Esta fatia MUST NOT visitar fonte, MUST NOT gravar
  preço nem avaliação, MUST NOT disparar coleta e MUST NOT montar painel
  de mercado.
- **FR-013**: Toda leitura e toda escrita de concorrente MUST considerar
  o hotel da sessão. Concorrente de um hotel MUST NOT ser visível nem
  alterável por outro.
- **FR-014**: Criar, editar, desativar, reativar e consultar concorrentes
  MUST ser exclusivos do perfil de gestão.
- **FR-015**: Recepção e perfil operacional MUST receber recusa ao tentar
  ler ou alterar concorrentes.
- **FR-016**: Tentativa de alterar concorrente de outro hotel MUST ser
  recusada sem confirmar que a ficha existe.
- **FR-017**: Logs de manutenção MUST registrar identificador do
  concorrente, hotel e ação (criar, editar, desativar, reativar). MUST
  NOT registrar conteúdo de mensagem de hóspede. Nome e endereço da fonte
  MUST NOT ser o conteúdo principal do log.
- **FR-018**: Esta fatia MUST NOT alterar tarifa da casa, MUST NOT
  consultar o sistema de gestão do hotel e MUST NOT tratar a lista como
  dado cadastral de hóspede.
- **FR-019**: Nome repetido na mesma propriedade MUST ser permitido.
  Distinção entre fichas é pelo identificador e pelo endereço da fonte.

### Key Entities

- **Concorrente**: propriedade que o hotel deseja acompanhar, com nome,
  endereço da fonte pública de consulta e indicação de ativo ou inativo.
  Pertence a um único hotel. Não é apagado; deixa de ser consultado quando
  inativo.
- **Fonte pública de consulta**: o endereço da web, informado pela
  gestão, onde preço e avaliação do concorrente aparecem sem autenticação.
  Nesta fatia a fonte é cadastrada, não visitada.
- **Lista de fontes ativas**: o conjunto de concorrentes ativos de uma
  propriedade, obtido por uma consulta única. Contrato que a coleta
  posterior deve respeitar — inativo não entra.
- **Manutenção da lista**: a lista completa da propriedade, incluindo
  inativos, usada pela gestão para criar, corrigir, desativar e reativar.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das criações com nome e endereço de fonte pública
  válidos, o concorrente nasce ativo na propriedade da sessão e aparece
  na consulta seguinte.
- **SC-002**: Em 100% das tentativas com nome ausente, endereço ausente
  ou endereço que não é da web público e completo, a ficha não é criada
  e a recusa identifica o problema.
- **SC-003**: Em 100% das desativações, o concorrente desaparece da lista
  de fontes ativas e permanece recuperável na manutenção como inativo; 0
  fichas são apagadas.
- **SC-004**: Em 100% das consultas de fontes ativas de uma propriedade
  com fichas mistas (ativas e inativas), a resposta contém todos os
  ativos e 0 inativos.
- **SC-005**: Em verificação com dois hotéis, 0% dos concorrentes de um
  hotel aparecem na lista (manutenção ou fontes ativas) do outro.
- **SC-006**: Em verificação com sessão de recepção ou operacional, 100%
  das tentativas de ler ou alterar concorrentes são recusadas. Em sessão
  de gestão da própria propriedade, 100% das consultas e alterações
  previstas são permitidas.
- **SC-007**: Em 100% das tentativas de cadastrar ou alterar para um
  endereço de fonte já existente na mesma propriedade, a segunda ficha
  não é gravada.
- **SC-008**: A gestão conclui o cadastro de um concorrente (nome e
  endereço) em uma única interação, sem etapas intermediárias
  obrigatórias e sem visitar a fonte.
- **SC-009**: O caminho criar → editar → desativar → consultar fontes
  ativas (ausente) → reativar → consultar fontes ativas (presente) é
  verificável de ponta a ponta sem rede externa, sem coleta de preço e
  sem tela visual nova.
- **SC-010**: Em 100% das execuções desta fatia, 0 fontes são visitadas e
  0 preços ou avaliações são gravados.

## Assumptions

- A fatia F0.3 (autenticação e perfis) está concluída. Isolamento por
  propriedade vale mesmo com uma única propriedade cadastrada.
- **Quem cadastra é a gestão.** Inteligência de mercado é processo da
  gestão, não do balcão. A recusa da gestão a alterar dado de domínio
  vale para reserva, hóspede, solicitação, consumo e avaliação — não para
  a lista de concorrentes. “Somente leitura” do painel de mercado (fatia
  posterior) continua valendo para preço e avaliação coletados: esta fatia
  não dá à gestão o poder de inventar número; só de dizer quem acompanhar.
  Recepção e operação não leem nem alteram a lista. Revisitável só com
  decisão registrada.
- Superfície de uso: comportamento observável pela manutenção da lista e
  pela consulta de fontes ativas. Ligar o protótipo visual continua fora
  do critério de pronto, no mesmo padrão das fatias já entregues.
- A propriedade nasce sem concorrentes. Não há ficha de exemplo na
  instalação.
- **Coleta, painel e periodicidade ficam fora.** F5.2 visita as fontes
  ativas, respeita diretivas de acesso, identifica-se com honestidade e
  grava preço ou falha com data. F5.3 exibe os números com a data da
  coleta. A periodicidade já é configuração da propriedade e será lida
  na F5.2. Incluir visita à fonte agora inflaria esta fatia sem
  consumidor e misturaria cadastro com coleta.
- **Termos de uso não são verificados automaticamente nesta fatia.** A
  gestão escolhe fonte pública ao cadastrar. Onde houver proibição
  expressa de coleta, a fonte não deve entrar na lista — é responsabilidade
  de quem cadastra, cobrada em banca, não um exame automático do sistema
  neste momento. A fatia seguinte é que recusa coleta desonesta.
- Duplicata de nome é permitida; duplicata de endereço de fonte na mesma
  propriedade não é. Não há consolidação automática de “mesmo hotel em
  duas fontes”: duas fontes são duas fichas, com nomes iguais se a gestão
  quiser.
- Endereço da fonte é dado operacional, não dado pessoal de hóspede. Não
  há anexo, captura de tela nem dado de avaliador individual nesta fatia.
- Esta fatia não muda tarifa da casa e não consulta o outro sistema do
  hotel. O OmniStay observa; a decisão de preço continua fora.
