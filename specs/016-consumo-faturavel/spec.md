# Feature Specification: Consumo Faturável e Fila de Lançamento

**Feature Branch**: `016-consumo-faturavel`

**Created**: 2026-08-18

**Status**: Draft

**Input**: User description: "Pedidos que geram cobrança — consumo do bar, impressão,
lavanderia — são registrados com o valor praticado no momento do pedido e nascem
pendentes de lançamento no sistema de gestão do hotel. Permanecem em fila destacada
no painel até que um funcionário confirme o lançamento. A fila de pendências aparece
também na passagem de turno."
(backlog F3.7)

Restrições já decididas no projeto (entrada do specify): o sistema **não** se
integra ao sistema de gestão do hotel — o lançamento é clique humano, nunca débito
automático; toda solicitação recebe confirmação de recebimento **antes** de qualquer
tramitação; gravar a mensagem de saída antes de enviá-la; a fila do painel é a fonte
da verdade e a notificação é conveniência; a ausência de ação humana precisa ser
visível (consumo não lançado é prejuízo silencioso); conteúdo de mensagem nunca vai
para log; o valor cobrado é o praticado no instante do pedido, não uma referência
que muda sozinha no reajuste; a palavra "extrato" e a palavra "conta" não existem
neste produto. Pedido de serviço sem cobrança (toalha, travesseiro) já é a fatia
anterior e **não** entra nesta fila. A lista de pedidos feitos pelo chat no
checkout, o pulso do segundo dia e a pesquisa de saída pertencem a fatias seguintes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pedido que gera cobrança nasce com valor e pendente de lançamento (Priority: P1)

Como hóspede já hospedado que pede algo que o hotel cobra (consumo do bar, impressão,
lavanderia), quero confirmação imediata de que o pedido foi recebido, com o valor
praticado naquele momento, e quero que a equipe saiba o que levar. Como hotel, quero
que esse pedido nasça **pendente de lançamento** no sistema de gestão da casa, para
o serviço não ser entregue de graça sem ninguém perceber.

**Why this priority**: É a fatia com consequência financeira. Sem valor no instante,
o histórico muda no reajuste. Sem pendência visível de lançamento, o hotel presta o
serviço e não cobra — e o hóspede não reclama de um item que não foi cobrado.

**Independent Test**: Pode ser testado partindo de uma mensagem já classificada como
pedido de serviço que corresponde a um item vendável ativo da propriedade,
verificando: confirmação ao hóspede com a descrição e o valor praticado; uma
solicitação do tipo consumo com esse valor; status de lançamento pendente; visível
na fila destacada de pendências; e zero efeito sobre pedidos de serviço sem cobrança.

**Acceptance Scenarios**:

1. **Given** uma mensagem de estadia já classificada como pedido de serviço que
   identifica de forma única um item vendável ativo daquela propriedade (por
   exemplo, consumo do bar cadastrado), **When** o sistema registra o pedido,
   **Then** nasce uma solicitação do tipo consumo, com a descrição do que foi
   pedido, o quarto informado na mensagem se houver, o valor praticado naquele
   instante e o lançamento pendente.
2. **Given** o desfecho do cenário anterior, **When** o hóspede consulta a
   conversa, **Then** há uma confirmação de que o pedido foi recebido, gravada no
   histórico da mesma reserva, informando o valor praticado — e essa confirmação
   não afirma que o valor já foi lançado no sistema de gestão do hotel, não
   promete horário e não usa as palavras "extrato" nem "conta".
3. **Given** o mesmo pedido, **When** a recepção consulta a fila de pendências de
   lançamento, **Then** o consumo aparece destacado como pendente, com descrição
   e valor praticado.

---

### User Story 2 - A confirmação chega antes de o pedido tramitar (Priority: P1)

Como hóspede, quero saber que o pedido foi recebido **antes** de ele tramitar como
tarefa da equipe e como pendência de lançamento, para eu não ficar no silêncio
enquanto alguém decide o que fazer.

**Why this priority**: Confirmação antes de tramitação é regra do produto, não
cortesia. Confirmar depois reproduz o telefone que ninguém atende. Informar o valor
depois de a equipe já ter saído com o pedido deixa o hóspede sem chance de
discordar do preço.

**Independent Test**: Pode ser testado observando a ordem no caminho feliz: a
confirmação já está no histórico da conversa, com o valor praticado, no instante em
que o consumo passa a existir como pendência operacional e como pendência de
lançamento.

**Acceptance Scenarios**:

1. **Given** um pedido de consumo identificado, **When** o registro conclui,
   **Then** a confirmação ao hóspede precede a tramitação — zero consumos tramitam
   em silêncio.
2. **Given** a confirmação do cenário 1, **When** se lê o texto enviado, **Then**
   o valor informado é o mesmo valor praticado gravado no consumo; não é um número
   inventado nem um preço lido depois de um reajuste.

---

### User Story 3 - A recepção marca como lançado, com quem e quando (Priority: P1)

Como recepcionista que acabou de lançar o item no sistema de gestão do hotel, quero
marcar o consumo como lançado em um único gesto, e quero que fique registrado quem
lançou e quando, para a pendência sair da fila e o próximo turno não relançar nem
esquecer o que já foi feito.

**Why this priority**: O clique é a quarta travessia humana. Sem ele, a fila nunca
esvazia com verdade. Sem autor e instante, a omissão continua invisível.

**Independent Test**: Pode ser testado com um consumo pendente da propriedade,
autenticando a recepção daquela propriedade, marcando como lançado e verificando:
sai da fila de pendências; constam autor e instante; o valor praticado não muda; a
mesma ação no mesmo consumo não produz segundo lançamento.

**Acceptance Scenarios**:

1. **Given** um consumo pendente de lançamento da propriedade, **When** a recepção
   daquela propriedade marca como lançado, **Then** o consumo deixa de ser
   pendência de lançamento, com a identificação de quem lançou e o instante.
2. **Given** o desfecho do cenário 1, **When** a recepção consulta a fila
   destacada, **Then** aquele consumo **não** aparece mais entre as pendências.
3. **Given** um consumo já lançado, **When** alguém tenta marcar como lançado de
   novo, **Then** a ação é recusada, o autor e o instante originais permanecem, e
   não nasce segundo lançamento.

---

### User Story 4 - Pendências aparecem destacadas e na passagem de turno (Priority: P1)

Como recepcionista na passagem de turno, quero ver os consumos ainda pendentes de
lançamento numa fila **destacada** — distinta dos pedidos de toalha e dos chamados
abertos — para o turno que chega não herdar prejuízo silencioso.

**Why this priority**: A mitigação desta fatia não elimina o clique humano: torna a
omissão perceptível. Fila misturada com toalha extra induz a tratar cerveja como
serviço gratuito.

**Independent Test**: Pode ser testado com um consumo pendente, um pedido de serviço
sem cobrança aberto e um chamado aberto, consultando a passagem de turno da
recepção e verificando que o consumo pendente aparece na fila destacada de
lançamento e que o pedido sem cobrança **não** aparece nela.

**Acceptance Scenarios**:

1. **Given** consumos pendentes na propriedade, **When** a recepção consulta a
   passagem de turno, **Then** todas as pendências de lançamento daquela
   propriedade aparecem na fila destacada, recuperáveis pela leitura do painel —
   inclusive sem ninguém as ter assumido.
2. **Given** um pedido de serviço sem cobrança aberto (toalha extra), **When** se
   observa a fila destacada de lançamento, **Then** esse pedido **não** aparece
   nela.
3. **Given** um consumo já lançado, **When** a recepção consulta a mesma fila,
   **Then** ele não consta mais como pendência de lançamento.
4. **Given** um consumo da propriedade A, **When** a recepção da propriedade B
   consulta a fila, **Then** esse consumo não aparece e a consulta não revela que
   ele existe.

---

### User Story 5 - Reajuste de preço não altera o que já foi pedido (Priority: P1)

Como hotel, quero que o valor gravado no consumo seja o praticado no momento do
pedido, para um reajuste posterior da lavanderia ou do bar não reescrever o
histórico nem divergir do que o hóspede já viu na confirmação.

**Why this priority**: Valor que "acompanha a tabela" corrompe o histórico e a
cobrança. É critério de aceite explícito da fatia.

**Independent Test**: Pode ser testado registrando um consumo, alterando o preço
atual do item vendável, e verificando que o valor praticado daquele consumo e o
valor da confirmação já enviada permanecem os do instante do pedido.

**Acceptance Scenarios**:

1. **Given** um consumo já registrado com valor praticado, **When** a recepção
   altera o preço atual do item vendável correspondente, **Then** o valor daquele
   consumo permanece o do momento do pedido.
2. **Given** o mesmo reajuste, **When** um **novo** pedido do mesmo item é
   registrado depois, **Then** o novo consumo nasce com o preço atual, sem
   alterar os anteriores.

---

### User Story 6 - Pedido sem cobrança continua fora desta fila (Priority: P1)

Como hotel, quero que toalha extra, travesseiro e cobertor continuem sendo serviço
operacional sem valor e **não** entrem na fila de lançamento, para ninguém lançar
no sistema de gestão o que não se cobra e para o hóspede não achar que a toalha
virará cobrança.

**Why this priority**: Misturar as duas naturezas é o defeito que o checkout
posterior precisa evitar. Esta fatia é o momento em que a distinção passa a
existir de fato.

**Independent Test**: Pode ser testado com um pedido classificado como serviço que
**não** corresponde a nenhum item vendável ativo (toalha extra), verificando
solicitação do tipo serviço, zero valor, zero pendência de lançamento, e
confirmação sem preço.

**Acceptance Scenarios**:

1. **Given** uma mensagem classificada como pedido de serviço que não identifica
   nenhum item vendável ativo da propriedade, **When** o sistema registra,
   **Then** o caminho permanece o do serviço operacional sem cobrança: sem valor,
   sem pendência de lançamento, fora da fila destacada.
2. **Given** um serviço operacional já aberto de fatias anteriores, **When** a
   recepção consulta a fila de lançamento, **Then** esse pedido não aparece nela.

---

### User Story 7 - A equipe vê o pedido para executar; só a recepção lança (Priority: P1)

Como profissional da equipe operacional, quero ver o consumo aberto da minha
propriedade — o que levar, o quarto quando conhecido, a urgência e o valor — sem
acessar ficha cadastral, para eu entregar o item. Como recepcionista, sou eu quem
marca o lançamento no sistema de gestão, porque sou a ponte humana. Como gestão,
quero ver a fila de pendências e **não** conseguir marcar lançamento nem alterar
o valor.

**Why this priority**: Quem executa no quarto não é quem lança no sistema de
gestão. Gestão consulta e não altera dado de domínio. Equipe operacional em
sessão longa nunca vê nome, telefone ou documento.

**Independent Test**: Pode ser testado com um consumo pendente: staff da
propriedade vê o pedido operacional sem ficha e **não** consegue marcar lançamento;
recepção marca lançamento; gestão vê a pendência e recebe recusa ao tentar lançar
ou alterar o valor.

**Acceptance Scenarios**:

1. **Given** um consumo aberto na propriedade, **When** um profissional
   operacional daquela propriedade consulta as solicitações abertas, **Then** o
   pedido aparece com tipo consumo, descrição, valor praticado, urgência, instante
   de abertura e quarto quando conhecido — sem nome, telefone, documento nem
   endereço do hóspede.
2. **Given** o mesmo consumo pendente, **When** o profissional operacional tenta
   marcar como lançado, **Then** a ação é recusada e a pendência permanece.
3. **Given** o mesmo consumo, **When** a gestão da propriedade consulta a fila de
   pendências de lançamento, **Then** a pendência é visível; **When** tenta marcar
   como lançado ou alterar o valor, **Then** a ação é recusada.
4. **Given** um consumo da propriedade A, **When** um profissional da propriedade
   B consulta, **Then** o pedido não aparece e a tentativa de lançar não revela
   que ele existe.

---

### User Story 8 - A recepção mantém os itens vendáveis e o preço atual (Priority: P1)

Como recepcionista, quero cadastrar, corrigir o preço e desativar os itens que o
hotel cobra pelo chat (bar, impressão, lavanderia), para o valor praticado no
pedido vir dessa lista — e nunca de um número inventado pelo atendimento
automatizado.

**Why this priority**: Sem item vendável com preço próprio, o sistema só teria o
texto corrido do catálogo de fatos ou o palpite do classificador. Os dois erram o
número; o número errado vira hóspede informado de um preço e cobrado de outro.

**Independent Test**: Pode ser testado autenticando a recepção, criando um item
vendável com preço, alterando o preço, desativando-o, e verificando que só itens
ativos daquela propriedade entram na identificação do pedido; gestão lê e não
altera; outro hotel não vê.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção, **When** a pessoa cadastra um item vendável
   com nome e preço atual válido (não negativo), **Then** o item nasce ativo na
   propriedade da sessão e passa a poder ser identificado num pedido.
2. **Given** um item ativo, **When** a recepção altera o preço atual, **Then** a
   consulta seguinte devolve o preço novo, e os consumos já registrados não
   mudam (User Story 5).
3. **Given** um item ativo, **When** a recepção o desativa, **Then** pedidos
   novos não o identificam mais como vendável; o item permanece recuperável na
   manutenção, sem apagamento permanente.
4. **Given** um item da propriedade A, **When** a recepção da propriedade B
   consulta os itens vendáveis, **Then** o item de A não aparece.
5. **Given** uma sessão de gestão, **When** a pessoa consulta os itens vendáveis
   da propriedade, **Then** a lista é visível; **When** tenta criar, editar preço
   ou desativar, **Then** a ação é recusada.

---

### User Story 9 - Identificação ambígua ou indisponível não inventa preço (Priority: P1)

Como hotel e como hóspede, quero que o sistema **não** invente item nem valor
quando não souber qual item vendável foi pedido, ou quando o serviço de
identificação estiver indisponível: uma pessoa vê, o pedido não some, e nenhum
preço inventado é confirmado.

**Why this priority**: Esta é a fatia em que um erro de leitura vira cobrança
errada. Na dúvida, um humano vê. Conhecimento geral sobre o preço de uma cerveja
não é fonte válida.

**Independent Test**: Pode ser testado com (a) pedido que não identifica um único
item vendável ativo, (b) serviço de identificação indisponível ou resposta
inválida, verificando: zero consumo com valor inventado, zero confirmação com
preço, mensagem original preservada, pendência visível para a recepção.

**Acceptance Scenarios**:

1. **Given** um pedido classificado como serviço em que nenhum item vendável
   ativo da propriedade é identificado de forma única, **When** o sistema decide,
   **Then** não nasce consumo com valor inventado e não se envia confirmação com
   preço. Se nada vendável foi identificado, o caminho é o do serviço
   operacional sem cobrança (User Story 6). Se a identificação for ambígua
   (dois itens igualmente plausíveis) ou o serviço estiver indisponível, a
   mensagem permanece e a recepção da propriedade vê que precisa de atendimento
   humano.
2. **Given** identificação indisponível ou em formato inválido, **When** se
   observa o canal do hóspede, **Then** nenhuma confirmação de consumo com valor
   é enviada, e o texto original não é descartado.

---

### User Story 10 - Entregar no quarto não é lançar no sistema de gestão (Priority: P1)

Como profissional da equipe que já levou o item ao quarto, quero poder marcar o
pedido como resolvido no painel **sem** que isso signifique que o valor foi
lançado no sistema de gestão. Como recepção, o lançamento continua pendente até
eu confirmar o clique próprio.

**Why this priority**: São dois ciclos. Confundir os dois esconde a pendência
financeira no mesmo gesto que fecha a toalha extra. A fatia de resolver chamado
deixou o tipo consumo de fora de propósito.

**Independent Test**: Pode ser testado com um consumo pendente, marcando a
solicitação como resolvida (recepção ou equipe operacional) e verificando que o
consumo permanece na fila destacada de lançamento, com o mesmo valor, até a
recepção marcar o lançamento.

**Acceptance Scenarios**:

1. **Given** um consumo aberto e pendente de lançamento, **When** a equipe
   operacional ou a recepção marca a solicitação como resolvida, **Then** o
   pedido deixa de aparecer como pendência operacional aberta, constam quem
   resolveu e quando, e o lançamento **permanece pendente** na fila destacada.
2. **Given** o desfecho anterior, **When** a recepção marca como lançado,
   **Then** a pendência de lançamento some, com autor e instante do lançamento
   distintos dos da resolução operacional.

---

### User Story 11 - Reprocessar o mesmo pedido não duplica cobrança nem recado (Priority: P1)

Como hotel e como hóspede, quero que a mesma mensagem gere no máximo uma
confirmação e um consumo, para um retrabalho não lançar duas cervejas nem mandar
dois recados com valor.

**Why this priority**: Duplicata aqui é prejuízo para o hóspede ou para o hotel.
Idempotência visível é critério desta fatia tanto quanto das anteriores.

**Independent Test**: Pode ser testado concluindo o registro uma vez e
disparando o mesmo trabalho de novo, verificando zero segunda confirmação e zero
segundo consumo para aquela mensagem.

**Acceptance Scenarios**:

1. **Given** uma mensagem cujo consumo já foi registrado e confirmado, **When**
   o mesmo trabalho é processado outra vez, **Then** o hóspede não recebe segunda
   confirmação e a fila não ganha segundo consumo daquela origem.
2. **Given** uma falha depois de gravar e antes de concluir o envio, **When** o
   trabalho é retomado, **Then** o consumo permanece único, o valor praticado não
   muda, e o envio pendente é retomado.

---

### User Story 12 - Falha ao gravar ou ao enviar não perde o pedido (Priority: P1)

Como hóspede e como hotel, quero que uma falha no envio da confirmação não apague
o consumo, e que uma falha ao gravar não envie recado com valor sobre um pedido
que não existe.

**Why this priority**: Pedido faturável perdido é prejuízo. Recado com preço
sobre registro inexistente é cobrança fantasma na cabeça do hóspede.

**Independent Test**: Pode ser testado (a) gravando com sucesso e falhando o
envio, e (b) falhando a gravação, verificando preservação do consumo no primeiro
caso, ausência de envio no segundo, e trabalho recuperável nos dois.

**Acceptance Scenarios**:

1. **Given** confirmação e consumo já gravados e o envio ao hóspede falhando,
   **When** o sistema trata a falha, **Then** o consumo permanece na fila de
   lançamento, a confirmação permanece no histórico, e o envio fica recuperável.
2. **Given** a gravação da confirmação ou do consumo falhando, **When** se
   observa o canal do hóspede, **Then** nenhum recado com valor é enviado, a
   mensagem original permanece, e o trabalho continua pendente de novo
   processamento.

---

### User Story 13 - Consumo que não deve ser cobrado sai da fila sem fingir lançamento (Priority: P2)

Como recepcionista, quero poder dispensar um consumo pendente (cortesia da casa,
pedido desfeito antes de entregar) **sem** marcá-lo como lançado no sistema de
gestão, para a fila esvaziar com honestidade e o histórico não mentir que houve
lançamento.

**Why this priority**: O único caminho para sair da fila não pode ser "lançado".
Marcar cortesia como lançada é o contrário da honestidade sobre o que o sistema
não faz.

**Independent Test**: Pode ser testado com um consumo pendente, autenticando a
recepção, dispensando-o e verificando: sai da fila de pendências; constam quem
dispensou e quando; **não** consta como lançado; gestão e staff não conseguem
dispensar.

**Acceptance Scenarios**:

1. **Given** um consumo pendente, **When** a recepção da propriedade o dispensa,
   **Then** ele sai da fila destacada, fica registrado quem dispensou e quando, e
   **não** aparece como lançado no sistema de gestão.
2. **Given** um consumo já lançado ou já dispensado, **When** se tenta lançar ou
   dispensar de novo, **Then** a ação é recusada e o estado original permanece.
3. **Given** o mesmo consumo pendente, **When** gestão ou equipe operacional
   tenta dispensar, **Then** a ação é recusada.

---

### User Story 14 - Conteúdo da mensagem não vaza em log (Priority: P2)

Como titular dos dados e responsável pelo hotel, quero que o texto do pedido e o
texto da confirmação nunca apareçam em log operacional.

**Why this priority**: Minimização de dados pessoais continua valendo no ramo
com valor. O log pode registrar identificadores, a propriedade, o tipo consumo e
o resultado; o texto não.

**Independent Test**: Pode ser testado nos desfechos feliz, lançamento,
reprocessamento e falha de envio, inspecionando os logs: há identificadores e
resultado; não há o texto do hóspede nem o da confirmação.

**Acceptance Scenarios**:

1. **Given** um consumo registrado e confirmado com sucesso, **When** o sistema
   registra log operacional, **Then** aparecem identificadores, a propriedade e a
   indicação de consumo registrado — e não o conteúdo do pedido nem o da
   confirmação.
2. **Given** lançamento, dispensa, falha de envio ou reprocessamento, **When** o
   sistema registra log operacional, **Then** há código de resultado e
   identificadores, sem o texto.

---

### Edge Cases

- Somente mensagem já classificada como pedido de serviço entra no ramo desta
  fatia. Dúvida geral, reclamação técnica, interesse comercial, pedido de
  checkout e fora de escopo não geram consumo aqui.
- A distinção serviço versus consumo **não** é uma intenção nova do
  classificador: o classificador continua dizendo "pedido de serviço". Esta
  fatia identifica se o pedido corresponde a um item vendável **ativo** da
  propriedade. Correspondência única → consumo. Nenhuma correspondência →
  serviço operacional sem cobrança (já existente). Correspondência ambígua ou
  serviço de identificação indisponível → humano, sem preço inventado.
- O valor praticado é lido do item vendável **depois** da identificação, no
  mesmo instante em que a confirmação e o consumo são gravados. O atendimento
  automatizado identifica *qual* item; **não** escreve o número.
- Itens vendáveis desativados não entram na identificação. Consumos antigos
  daquele item permanecem íntegros, com o valor que já tinham.
- Item vendável de outro hotel nunca é usado.
- Preço atual inválido (negativo) é recusado na manutenção do item. Consumo não
  nasce com valor negativo.
- Uma mensagem origina no máximo um consumo. Se o hóspede pedir mais de um item
  vendável na mesma mensagem e a identificação for única para um conjunto
  coerente, o consumo único registra a descrição do pedido e o valor praticado
  correspondente àquele conjunto no instante; se a identificação não for única,
  vale a User Story 9.
- O quarto da solicitação é o número que o hóspede informou na mensagem. O
  sistema não consulta o sistema de gestão do hotel e não inventa quarto.
  Ausência de quarto não impede o registro, a confirmação nem a pendência de
  lançamento.
- A urgência da solicitação é a já gravada na classificação. Esta fatia não
  reclassifica.
- A confirmação é recado padrão de recebimento **com o valor praticado**. Não
  promete prazo, não afirma que o lançamento no sistema de gestão já ocorreu,
  não cita fato da casa fora do item pedido, e não usa "extrato" nem "conta".
- Resolução operacional (User Story 10) avisa o hóspede da conclusão do
  atendimento no quarto, no mesmo espírito da fatia de resolver chamado, e
  **não** afirma lançamento. Lançamento não dispara recado novo ao hóspede
  nesta fatia — o hóspede já recebeu o valor na confirmação de recebimento.
- Consumo dispensado não gera recado automático de "não será cobrado" nesta
  fatia (mensagem proativa nova exigiria justificativa própria).
- Perfil operacional vê a solicitação aberta sem ficha cadastral e não lança.
  Gestão vê a fila de pendências e não lança, não dispensa, não altera valor nem
  item vendável. Recepção lança, dispensa e mantém itens vendáveis.
- Hotel A não registra consumo na conversa do hotel B e não exibe a fila do
  hotel B.
- Transição inválida de lançamento (lançar duas vezes, lançar o que já foi
  dispensado, dispensar o que já foi lançado) é recusada de forma durável — não
  só no caminho feliz da aplicação.
- Status da reserva (ainda hospedado, já encerrado) **não** impede lançar nem
  dispensar: o lançamento no sistema de gestão pode ocorrer depois da saída.
- A lista de "pedidos feitos pelo chat" apresentada ao hóspede no checkout está
  **fora** desta fatia (depende da confirmação de saída). Esta fatia só garante
  que o consumo exista, com valor histórico, para essa lista poder nascer
  depois.
- Esta fatia **não** classifica intenção, **não** responde dúvida pelo
  catálogo de fatos, **não** abre chamado de reclamação técnica, **não** altera
  o status da reserva, **não** dispara pulso, coleta nem lembrete, e **não**
  lança valor sozinha no sistema de gestão do hotel.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST identificar se uma mensagem de estadia já
  classificada como pedido de serviço corresponde a um item vendável ativo da
  propriedade da reserva. MUST NOT usar item de outro hotel. MUST NOT usar item
  desativado.
- **FR-002**: Correspondência única MUST registrar uma solicitação do tipo
  consumo vinculada à reserva e à mensagem de origem, com descrição do que foi
  pedido, quarto informado quando houver, urgência já classificada e valor
  praticado no instante. MUST NOT atribuir quarto a partir de inventário.
- **FR-003**: O valor praticado MUST ser o preço atual do item vendável
  identificado, lido no instante do registro — a mesma fonte do valor informado
  na confirmação ao hóspede. MUST NOT ser escrito pelo atendimento automatizado.
  MUST NOT ser referência viva a uma tabela: reajuste posterior MUST NOT alterar
  consumos já gravados.
- **FR-004**: Todo consumo MUST nascer pendente de lançamento no sistema de
  gestão do hotel. MUST NOT nascer já lançado nem já dispensado.
- **FR-005**: Pedido de serviço sem correspondência a item vendável ativo MUST
  permanecer serviço operacional sem cobrança: MUST NOT ter valor a cobrar e
  MUST NOT entrar na fila de lançamento.
- **FR-006**: Identificação ambígua, serviço de identificação indisponível ou
  resposta em formato inválido MUST preservar a mensagem, MUST NOT inventar
  item nem valor, MUST NOT enviar confirmação de consumo com preço, e MUST
  tornar visível à recepção da propriedade que aquela mensagem precisa de
  atendimento humano.
- **FR-007**: O hóspede MUST receber confirmação de que o pedido faturável foi
  recebido, informando o valor praticado, antes de o consumo existir como
  pendência operacional e como pendência de lançamento. A confirmação MUST ser
  recado padrão — MUST NOT afirmar que o lançamento no sistema de gestão já
  ocorreu, MUST NOT prometer prazo, MUST NOT usar as palavras "extrato" nem
  "conta".
- **FR-008**: A confirmação MUST ficar gravada no histórico da conversa da
  reserva antes de ser enviada ao hóspede.
- **FR-009**: Consumos pendentes de lançamento MUST aparecer em fila destacada
  da propriedade, distinta dos pedidos de serviço sem cobrança e recuperável na
  passagem de turno pela leitura do painel. MUST NOT depender de uma
  notificação ter chegado. Pedido de serviço sem cobrança MUST NOT aparecer
  nessa fila.
- **FR-010**: Recepção da propriedade MUST poder marcar consumo pendente como
  lançado. Marcar como lançado MUST registrar quem lançou (a pessoa autenticada)
  e o instante. MUST NOT deixar lançamento sem autor nem sem instante.
- **FR-011**: Consumo lançado MUST sair da fila destacada de pendências. MUST
  permanecer recuperável como fato histórico daquela reserva, com o valor
  praticado original.
- **FR-012**: Recepção da propriedade MUST poder dispensar consumo pendente
  (não será lançado). Dispensar MUST registrar quem dispensou e o instante, MUST
  sair da fila destacada, e MUST NOT constar como lançado.
- **FR-013**: Lançar ou dispensar consumo já lançado ou já dispensado MUST ser
  recusado. Transição inválida MUST ser rejeitada de forma durável.
- **FR-014**: Equipe operacional e gestão MUST NOT lançar nem dispensar
  consumo. Gestão MUST NOT alterar valor de consumo nem manter item vendável.
  Equipe operacional MUST NOT alcançar nome, telefone, documento, endereço nem
  demais dados da ficha cadastral.
- **FR-015**: Equipe operacional, recepção e gestão da propriedade MUST
  conseguir ver o consumo aberto como solicitação operacional daquela
  propriedade (descrição, valor, quarto quando conhecido, urgência, instante),
  sem ficha cadastral para quem não tem permissão de ficha.
- **FR-016**: Recepção e equipe operacional MUST poder marcar a solicitação de
  tipo consumo como resolvida (atendimento no quarto), registrando quem e
  quando. Essa resolução MUST NOT marcar o consumo como lançado nem como
  dispensado.
- **FR-017**: Recepção da propriedade MUST poder criar, editar o preço atual e
  desativar itens vendáveis daquela propriedade, sem apagamento permanente.
  Preço MUST ser não negativo. Gestão MAY consultar e MUST NOT alterar. Item
  de um hotel MUST NOT ser visível nem editável por outro.
- **FR-018**: Reprocessar mensagem cujo consumo já foi registrado MUST NOT
  produzir segunda confirmação nem segundo consumo daquela origem.
- **FR-019**: Se gravar a confirmação ou o consumo falhar, a mensagem original
  MUST permanecer, o trabalho MUST continuar recuperável, e MUST NOT enviar ao
  hóspede recado de consumo que ainda não foi gravado.
- **FR-020**: Se o envio da confirmação falhar depois de gravar, o consumo e a
  confirmação gravada MUST permanecer; o envio MUST continuar recuperável.
  Falha de envio MUST NOT apagar o consumo nem alterar o valor praticado.
- **FR-021**: Conteúdo do pedido, conteúdo da confirmação e demais dados
  pessoais NUNCA MUST aparecer em log operacional; logs registram
  identificadores, a propriedade e o resultado — nunca o texto.
- **FR-022**: Resolução MUST considerar a propriedade da reserva; consumo,
  confirmação, fila de lançamento e itens vendáveis de um hotel MUST NOT vazar
  para outro.
- **FR-023**: Esta fatia MUST NOT alterar o status da reserva, MUST NOT
  confirmar chegada ou saída, MUST NOT responder dúvida pelo catálogo de fatos,
  MUST NOT abrir chamado de reclamação técnica, MUST NOT disparar coleta,
  lembrete, pulso ou pesquisa, e MUST NOT lançar valor automaticamente no
  sistema de gestão do hotel.
- **FR-024**: A verificação desta fatia MUST ser possível sem o serviço real de
  mensageria e sem o serviço real de identificação: um envio controlado e uma
  identificação controlada devolvem sucesso, ambiguidade, indisponibilidade ou
  falha previsíveis, sem rede.

### Key Entities

- **Item vendável da propriedade**: o que o hotel cobra pelo chat (bar,
  impressão, lavanderia), com nome e preço **atual**, ativo ou desativado.
  Fonte do valor no instante do pedido. Distinto do catálogo de fatos que o
  atendimento pode afirmar (horários, regras, programação).
- **Pedido de serviço classificado**: mensagem de estadia já marcada com a
  intenção "pedido de serviço". Insumo desta fatia e da fatia de serviço
  operacional; a identificação do item vendável é o que as distingue.
- **Consumo**: especialização faturável de uma solicitação — descrição, quarto
  quando informado, urgência herdada, valor praticado no momento, status de
  lançamento, vínculo com a reserva e a mensagem de origem. Não é serviço
  operacional sem cobrança e não é reclamação técnica.
- **Valor praticado**: retrato histórico do preço no instante do pedido. Não
  acompanha reajuste posterior.
- **Status de lançamento**: pendente (nasce assim), lançado (recepção confirmou
  o lançamento no sistema de gestão) ou dispensado (não será lançado). Só sai
  da fila destacada nas duas últimas.
- **Confirmação de recebimento**: recado padrão ao hóspede de que o pedido
  faturável foi recebido, com o mesmo valor praticado gravado no consumo,
  antes da tramitação. Não afirma que o lançamento já ocorreu.
- **Fila destacada de pendências de lançamento**: lista recuperável no painel
  dos consumos ainda pendentes da propriedade, visível na passagem de turno à
  recepção e à gestão. Fonte da verdade da quarta travessia humana. Pedido sem
  cobrança não entra.
- **Resolução operacional do consumo**: o mesmo gesto de fechar atendimento no
  quarto já existente para reclamação e serviço; no consumo, não substitui o
  lançamento.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das mensagens classificadas como pedido de serviço com
  identificação única de item vendável ativo, o hóspede recebe uma confirmação
  com o valor praticado e nasce exatamente 1 consumo pendente de lançamento
  vinculado àquela mensagem.
- **SC-002**: Em 100% desses registros, a confirmação ao hóspede precede a
  tramitação; 0 consumos tramitam em silêncio.
- **SC-003**: Em 100% dos pedidos de serviço sem item vendável correspondente,
  há 0 valores a cobrar e 0 entradas na fila destacada de lançamento.
- **SC-004**: Em 100% das passagens de turno da recepção, 100% dos consumos
  pendentes daquela propriedade aparecem na fila destacada, e 0 pedidos de
  serviço sem cobrança aparecem nela.
- **SC-005**: Em 100% dos lançamentos, constam quem lançou e quando; 0
  lançamentos sem autor ou sem instante; 0 segundos lançamentos do mesmo
  consumo.
- **SC-006**: Após reajuste do preço atual de um item vendável, 100% dos
  consumos já registrados daquele item conservam o valor do instante do
  pedido; 0 históricos são reescritos.
- **SC-007**: Em verificação com dois hotéis, 0% dos consumos, confirmações,
  filas ou itens vendáveis de um hotel aparecem no outro.
- **SC-008**: Em 100% das consultas da equipe operacional, o consumo aberto da
  própria propriedade é recuperável e 0 dados da ficha cadastral são expostos a
  esse perfil; 100% das tentativas de lançar ou dispensar por esse perfil são
  recusadas.
- **SC-009**: Em 100% das tentativas da gestão de lançar, dispensar, alterar
  valor ou manter item vendável, a ação é recusada; a fila de pendências
  permanece visível a esse perfil.
- **SC-010**: Em 100% das resoluções operacionais de consumo, o lançamento
  permanece pendente até o clique próprio da recepção.
- **SC-011**: Reprocessar a mesma mensagem já concluída produz 0 segundas
  confirmações e 0 segundos consumos.
- **SC-012**: Em 100% das falhas de envio após gravação, o consumo permanece
  na fila e a confirmação permanece no histórico; em 100% das falhas de
  gravação, 0 recados com valor são enviados ao hóspede.
- **SC-013**: Em 100% das identificações ambíguas ou indisponíveis, 0 consumos
  com valor inventado nascem e 0 confirmações com preço são enviadas; a
  mensagem permanece visível para atendimento humano.
- **SC-014**: Em 100% dos desfechos, logs operacionais não contêm o conteúdo
  do pedido nem o da confirmação.
- **SC-015**: O caminho pedido identificado → confirmação com valor + consumo
  pendente na fila destacada → lançamento com autor e instante é verificável de
  ponta a ponta sem o serviço real de envio de mensagem e sem o serviço real de
  identificação.

## Assumptions

- A fatia F3.4 (pedido de serviço sem cobrança) está concluída e trata todo
  `pedido de serviço` classificado como serviço operacional. Esta fatia **altera
  esse roteamento**: passa a haver um passo de identificação contra os itens
  vendáveis ativos da propriedade. Sem correspondência, o comportamento da F3.4
  permanece.
- A fatia F3.6 (resolver chamado) fecha reclamação e serviço e **não** fecha
  consumo. Esta fatia estende o mesmo gesto de resolução operacional ao tipo
  consumo, sem implicar lançamento.
- A operação `lancar_consumo` já está na matriz de perfis: só recepção. Gestão
  consulta e não altera consumo. Equipe operacional não lança. Esta fatia é a
  primeira a exercê-la. Dispensar pendência segue a mesma autoridade — é
  disposição financeira, não execução no quarto.
- O desenho adiado na F2.1 permanece válido: item vendável com preço em campo
  próprio; identificação de *qual* item; preço lido depois, na mesma fonte da
  mensagem ao hóspede. O catálogo de fatos (F2.1) continua sendo a única fonte
  para **afirmar** horário, regra e programação; preço de cobrança não é extraído
  do texto corrido desse catálogo.
- Não há integração com o sistema de gestão do hotel. Marcar como lançado
  registra o clique humano; não verifica se o lançamento de fato ocorreu lá.
- Superfície de uso: comportamento observável no histórico da conversa, na
  confirmação recebida pelo hóspede, na fila destacada de pendências de
  lançamento (passagem de turno), na lista de solicitações abertas e na
  manutenção dos itens vendáveis. Ligar telas do painel visual de protótipo
  continua fora do critério de pronto.
- A verificação usa envio controlado e identificação controlada (sucesso,
  ambiguidade, indisponibilidade ou falha) e nunca chama serviço externo.
- Ordem entre mensagens consecutivas não é garantida. Cada pedido é tratado
  isoladamente.
- O hóspede acabou de escrever, então a confirmação ocorre dentro da janela de
  conversa já aberta; não se inicia conversa proativa nova. Lançamento e
  dispensa não disparam mensagem nova ao hóspede nesta fatia.
- A lista "pedidos feitos pelo chat" no checkout é a fatia F4.2 e só inclui
  consumo. Esta fatia não a apresenta ao hóspede.
- A palavra "extrato" e a palavra "conta" não aparecem em nenhum texto desta
  funcionalidade.
