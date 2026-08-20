# Feature Specification: Lista de Pedidos Feitos pelo Chat

**Feature Branch**: `019-lista-pedidos-chat`

**Created**: 2026-08-20

**Status**: Draft

**Input**: User description: "No encerramento da estadia, o hóspede pode consultar a
lista dos consumos que solicitou pelo chat, com valores. A lista inclui somente o
que gera cobrança — pedidos de serviço sem custo não aparecem. Em nenhum ponto da
interface ou das mensagens essa lista é chamada de extrato ou de conta."
(backlog F4.2)

Restrições já decididas no projeto (entrada do specify): o sistema **não** se
integra ao sistema de gestão do hotel — a lista cobre só o que passou pelo chat,
nunca o consumo lançado direto no outro sistema; a pesquisa de saída já existe e
**não** incorpora esta lista (permanece curta); gravar antes de enviar; a fila do
painel é a fonte da verdade e a notificação é conveniência; ausência de mensagem
não pode ser o único lugar onde a lista existe; nenhuma mensagem proativa nova
sem necessidade — esta lista já está na jornada de encerramento; as palavras
"extrato" e "conta" não existem neste produto; o rótulo é **"pedidos feitos pelo
chat"**; valores são os praticados no instante de cada pedido; conteúdo de
mensagem nunca vai para log.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hóspede recebe a lista no encerramento (Priority: P1)

Como hóspede que acaba de fazer o checkout no balcão, quero receber no celular a
lista do que pedi pelo chat, com o valor de cada item na hora em que pedi, para
conferir o que será cobrado **desse canal** enquanto ainda estou no hotel — sem
achar que aquilo é a fatura inteira da casa.

**Why this priority**: É o objetivo da fatia. Sem este recado, o hóspede só viu
cada valor isolado na confirmação do pedido e não consegue conferir o conjunto
na saída. Misturar com a pesquisa de avaliação reintroduz o formulário longo
que a pesquisa curta existe para evitar.

**Independent Test**: Pode ser testado confirmando a saída de uma reserva
hospedada que tenha ao menos um consumo faturável, inspecionando a mensagem
entregue (via canal falso de mensageria) e verificando: exatamente uma lista
daquela reserva; itens com descrição e valor praticado; rótulo "pedidos feitos
pelo chat"; pesquisa de saída intacta e em mensagem distinta.

**Acceptance Scenarios**:

1. **Given** uma confirmação de saída bem-sucedida de reserva que possui ao
   menos um consumo faturável, **When** o envio da lista é processado, **Then**
   o hóspede recebe exatamente uma mensagem com a lista dos pedidos feitos pelo
   chat no telefone de contato da reserva.
2. **Given** essa mensagem, **When** ela é inspecionada, **Then** cada item
   faturável daquela reserva aparece com a descrição do que foi pedido e o
   valor praticado naquele pedido; o rótulo visível é "pedidos feitos pelo
   chat"; as palavras "extrato" e "conta" não aparecem.
3. **Given** a mesma confirmação de saída, **When** se observam as mensagens
   ao hóspede, **Then** a lista e a pesquisa de saída são mensagens distintas:
   a pesquisa permanece curta (nota, comentário opcional, aceite) e **não**
   incorpora a lista.
4. **Given** uma reserva cuja saída já foi confirmada e cuja lista já foi
   disparada, **When** ninguém altera aquela reserva, **Then** o sistema não
   dispara uma segunda lista distinta para a mesma reserva.

---

### User Story 2 - Só o que gera cobrança entra na lista (Priority: P1)

Como hóspede, quero ver na lista apenas o que o hotel vai cobrar do que pedi
pelo chat — cerveja, impressão, lavanderia — e **não** a toalha extra nem o
item que a recepção dispensou como cortesia, para eu não achar que o grátis
também vai para a cobrança.

**Why this priority**: A lista existe para conferir o que será cobrado. Listar
serviço operacional ao lado de consumo faturável induz a dúvida que o produto
existe para remover. Cortesia marcada como “lançada” mentiria; omitir o
dispensado da lista de cobrança é a forma honesta.

**Independent Test**: Pode ser testado com uma reserva que misture consumo
pendente, consumo já lançado, consumo dispensado e pedido de serviço sem
cobrança, confirmando a saída e verificando o conteúdo da lista (mensagem e
consulta no painel): só pendente e lançado; zero serviço sem custo; zero
dispensado.

**Acceptance Scenarios**:

1. **Given** uma reserva com um consumo faturável pendente de lançamento e um
   pedido de serviço sem cobrança (toalha extra), **When** a lista é montada
   no encerramento, **Then** o consumo aparece com valor e o pedido sem
   cobrança **não** aparece.
2. **Given** uma reserva com um consumo já lançado e um consumo ainda
   pendente, **When** a lista é montada, **Then** os dois aparecem, cada um
   com o valor praticado no respectivo pedido — o status interno de lançamento
   **não** é exibido ao hóspede.
3. **Given** uma reserva cujo único consumo faturável foi dispensado
   (cortesia ou pedido desfeito), **When** a lista é montada, **Then** esse
   item **não** aparece — não será cobrado.
4. **Given** a lista montada, **When** ela é inspecionada, **Then** não há
   item sem valor a cobrar e não há serviço operacional misturado.

---

### User Story 3 - Recepção consulta a lista no painel (Priority: P1)

Como recepcionista no balcão, quero consultar os pedidos feitos pelo chat de
uma reserva da casa — com valores — mesmo se a mensagem ao hóspede falhar ou
ainda não tiver saído, para eu conferir com a pessoa na saída e para a lista
não existir só na notificação.

**Why this priority**: A fila do painel é a fonte da verdade; a mensagem é
conveniência. Sem consulta no painel, um envio falho apaga a conferência do
checkout. A jornada fala em tela **e** mensagem: as duas mostram o mesmo
conjunto.

**Independent Test**: Pode ser testado autenticando como recepção, consultando
a lista de uma reserva da propriedade com consumos mistos, e verificando o
mesmo recorte da mensagem (só faturáveis cobráveis, valores praticados),
inclusive quando o envio ao hóspede ainda não ocorreu ou falhou.

**Acceptance Scenarios**:

1. **Given** uma sessão autenticada de recepção e uma reserva da propriedade
   com consumos faturáveis, **When** a recepção consulta a lista de pedidos
   feitos pelo chat daquela reserva, **Then** vê os mesmos itens cobráveis e
   os mesmos valores que o hóspede receberia, independentemente de a mensagem
   já ter sido entregue.
2. **Given** uma reserva sem nenhum consumo cobrável, **When** a recepção
   consulta a lista, **Then** a consulta é permitida e devolve lista vazia —
   não inventa item.
3. **Given** uma reserva do hotel A, **When** a recepção do hotel B consulta
   a lista, **Then** a operação é recusada sem revelar que a reserva existe.
4. **Given** uma sessão de perfil operacional, **When** tenta consultar a
   lista, **Then** a operação é recusada.

---

### User Story 4 - Sem consumo cobrável, nenhuma mensagem extra (Priority: P1)

Como hóspede que só pediu toalha ou que não pediu nada cobrado pelo chat,
quero sair do hotel sem receber uma lista vazia no celular. Como hotel, não
quero pagar nem parecer cobrador de quem não tem o que conferir.

**Why this priority**: Não ser intrusivo é requisito. Uma mensagem “você não
pediu nada pelo chat” depois do checkout não ajuda a conferir cobrança e
compete com a pesquisa de avaliação.

**Independent Test**: Pode ser testado confirmando a saída de reserva sem
consumo cobrável (nenhum consumo, só serviço operacional, ou só dispensado) e
verificando: zero mensagem de lista; pesquisa de saída segue o fluxo já
existente; o painel ainda permite consultar a lista vazia.

**Acceptance Scenarios**:

1. **Given** uma reserva hospedada sem nenhum consumo faturável cobrável,
   **When** a recepção confirma a saída, **Then** não nasce pendência de
   envio de lista e o hóspede não recebe mensagem de pedidos feitos pelo
   chat.
2. **Given** o cenário 1, **When** a pesquisa de saída é observada, **Then**
   ela continua sendo disparada como já definido no encerramento — a ausência
   da lista não suprime a pesquisa.
3. **Given** uma reserva que ganha um consumo cobrável **depois** de já
   encerrada (não é o caminho desta fatia), **When** ninguém reprocessa o
   encerramento, **Then** esta fatia **não** dispara lista retroativa por
   conta própria.

---

### User Story 5 - Valor na lista é o do momento do pedido (Priority: P1)

Como hotel, quero que a lista mostre o valor gravado quando o hóspede pediu,
não o preço atual do cardápio depois de um reajuste, para a conferência na
saída bater com a confirmação que ele já recebeu no chat.

**Why this priority**: Sem valor histórico, o reajuste reescreve o que será
cobrado na cara de quem está saindo. O critério de aceite da fatia é
explicitamente o valor praticado no momento de cada pedido.

**Independent Test**: Pode ser testado registrando um consumo, alterando o
preço atual do item vendável, confirmando a saída e verificando que a lista
(mensagem e painel) exibe o valor original do consumo, não o preço novo.

**Acceptance Scenarios**:

1. **Given** um consumo gravado com um valor praticado e, depois, um reajuste
   do preço atual daquele item, **When** a lista é montada, **Then** o item
   aparece com o valor praticado original.
2. **Given** dois consumos do mesmo item em instantes diferentes, com valores
   praticados distintos, **When** a lista é montada, **Then** cada linha
   conserva o próprio valor — não há média nem preço único atual.
3. **Given** a lista, **When** se compara cada linha com a confirmação já
   enviada na hora do respectivo pedido, **Then** o valor informado na lista
   é o mesmo valor daquela confirmação.

---

### User Story 6 - Honestidade: a lista não é a fatura da casa (Priority: P1)

Como hotel, quero que a lista deixe claro que mostra só o que foi pedido pelo
chat — e não o frigobar, o restaurante nem o que a recepção lançou direto no
outro sistema — para o hóspede não confrontar esse recado com a fatura da
casa e gerar exatamente o atrito que a nomenclatura existe para evitar.

**Why this priority**: O sistema não se integra ao outro sistema de gestão.
Prometer conferência completa é o defeito mais caro numa defesa de produto.
A correção de uma palavra ("pedidos feitos pelo chat") só funciona se o
texto não desfizer isso por outro caminho.

**Independent Test**: Pode ser testado inspecionando todos os textos desta
fatia (mensagem ao hóspede, consulta no painel, rótulos visíveis) e
verificando: rótulo correto; zero ocorrências de "extrato" e de "conta";
presença de indicação de que a lista cobre somente o pedido pelo chat.

**Acceptance Scenarios**:

1. **Given** a mensagem da lista e a consulta no painel, **When** os textos
   são inspecionados, **Then** o conjunto se chama "pedidos feitos pelo
   chat" e **não** aparece a palavra "extrato" nem a palavra "conta".
2. **Given** a mensagem ao hóspede, **When** ela é lida, **Then** fica
   explícito que a lista abrange só o que foi solicitado pelo chat — não
   afirma ser a fatura da estadia nem o total a pagar no balcão.
3. **Given** a lista, **When** se observa o que ela pede do hóspede, **Then**
   **não** há pergunta ("está correto?"), **não** há pedido de confirmação e
   **não** há convite a pagar por aquele canal — é conferência, não cobrança.

---

### User Story 7 - Falha de envio não apaga a lista nem duplica o recado (Priority: P1)

Como hotel, quero que a intenção de enviar a lista fique gravada **antes** da
tentativa de entrega. Se a entrega falhar, quero retomar **a mesma** lista —
não uma segunda. O checkout já aconteceu e não se desfaz. A recepção continua
vendo a lista no painel.

**Why this priority**: Gravar antes de enviar vale para toda mensagem. Perder
o recado é tolerável; reabrir a estadia ou mandar duas listas não é. O painel
precisa continuar consultável no intervalo.

**Independent Test**: Pode ser testado confirmando a saída com consumo
cobrável, falhando o envio, consultando o painel (lista visível), retomando
(uma lista) e tentando processar em paralelo (ainda uma).

**Acceptance Scenarios**:

1. **Given** a saída confirmada, a intenção de lista gravada e o envio falho,
   **When** o trabalho é retomado, **Then** tenta-se de novo a mesma lista; a
   reserva permanece encerrada; o hóspede não recebe uma segunda lista
   distinta; a consulta no painel continua mostrando os itens.
2. **Given** duas execuções simultâneas do envio para a mesma reserva,
   **When** ambas tentam criar a lista, **Then** existe exatamente uma; a
   segunda é recusada pela garantia de unicidade do armazenamento.
3. **Given** falha na gravação da intenção de enviar, **When** o ciclo
   termina, **Then** o hóspede não recebe lista que ainda não foi gravada; se
   a confirmação da saída já persistiu, a reserva permanece encerrada e a
   recepção ainda consulta os pedidos no painel.

---

### User Story 8 - Isolar a lista por hotel e por perfil (Priority: P1)

Como responsável pelos dados da propriedade, quero que só recepção e gestão
do próprio hotel vejam a lista, que operação receba recusa, e que a reserva
de um hotel nunca vaze para sessão de outro.

**Why this priority**: Multi-tenant e autorização já existem; esta fatia
expõe valores de consumo da estadia e precisa herdar essas fronteiras.
Operação atende o quarto; não confere cobrança de saída. Gestão consulta;
não confirma saída no balcão.

**Independent Test**: Pode ser testado tentando consultar a lista e observar
o disparo no checkout com cada perfil e com sessão de outro hotel,
verificando recusas e isolamento.

**Acceptance Scenarios**:

1. **Given** uma reserva do hotel A, **When** uma sessão do hotel B tenta
   consultar a lista ou observa o encerramento, **Then** a operação é
   recusada sem revelar que a reserva existe, e nenhuma lista é enviada ao
   telefone daquela reserva por causa dessa sessão.
2. **Given** uma sessão de perfil operacional da própria propriedade,
   **When** tenta consultar a lista, **Then** a operação é recusada.
3. **Given** uma sessão de gestão da própria propriedade, **When** consulta
   a lista de uma reserva da casa, **Then** a consulta é permitida; **When**
   tenta confirmar a saída, **Then** a confirmação continua recusada — gestão
   não opera o balcão.
4. **Given** uma sessão de recepção, **When** confirma a saída de reserva
   hospedada da própria propriedade com consumo cobrável, **Then** a lista
   entra na pendência de envio.

---

### User Story 9 - Conteúdo da mensagem não vaza em log (Priority: P2)

Como titular dos dados, quero que a lista, as descrições dos itens e os
valores nunca apareçam em log operacional.

**Why this priority**: Minimização de dados pessoais. Log registra
identificadores e resultado, nunca o texto e nunca o valor por extenso.

**Independent Test**: Pode ser testado nos desfechos enviar, lista vazia
(não envia), falha de envio, consulta no painel e isolamento, inspecionando
logs: identificadores e código; zero texto de mensagem, zero descrição de
item, zero valor.

**Acceptance Scenarios**:

1. **Given** lista enviada, envio falho, consulta no painel ou reserva sem
   itens cobráveis, **When** o sistema registra log operacional, **Then** há
   identificadores, a propriedade e o resultado — e não o texto da lista,
   não a descrição do item e não o valor praticado por extenso.

---

### Edge Cases

- Reserva sem consumo faturável, só com serviço operacional, ou só com
  consumo dispensado: **não** dispara mensagem de lista; o painel devolve
  lista vazia; a pesquisa de saída segue.
- Consumo pendente de lançamento no encerramento: **entra** na lista. A
  lista é o que será cobrado do chat, não o que já foi clicado no outro
  sistema. Status de lançamento não aparece para o hóspede.
- Consumo lançado depois do encerramento: se já estava na lista (pendente
  na hora do envio), o valor não muda. Esta fatia **não** reenvia a lista
  quando a recepção lança ou dispensa depois.
- Consumo dispensado **depois** de a lista já ter sido enviada incluindo
  aquele item (ainda pendente): esta fatia **não** manda correção
  automática. A conferência posterior é humana, no balcão; mensagem
  proativa nova exigiria justificativa própria.
- Reajuste de preço após o pedido: a lista ignora o preço atual.
- Dois hóspedes na mesma reserva: a lista vai ao telefone de contato da
  reserva (titular), uma vez.
- Duas reservas distintas no mesmo telefone: cada confirmação de saída
  dispara a própria lista daquela reserva, se houver item cobrável.
- Pesquisa de saída incompleta na mesma janela: a lista **não** é pergunta
  e **não** pede resposta. Se o hóspede contestar a lista por escrito,
  esta fatia **não** interpreta isso como aceite da pesquisa nem como
  correção automática de item — na dúvida, um humano vê, no caminho já
  existente do encerramento.
- Oferta de retorno, convite a pagar pelo chat e débito automático
  **não** fazem parte desta fatia.
- Inferência de checkout por mensagem, confirmação em lote e tela React
  nova **não** fazem parte desta fatia.
- Consulta iniciada pelo hóspede durante a estadia (“me manda o que
  pedi”) **não** faz parte desta fatia — exigiria intenção nova na
  conversa. O momento especificado é o encerramento.
- Reserva já encerrada antes desta fatia existir: **não** há disparo
  retroativo em massa.
- Upsell que nunca virou consumo faturável no chat: **não** aparece. Só
  entra o que já existe como consumo cobrável da reserva.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Após confirmação de saída bem-sucedida de uma reserva que
  possua ao menos um consumo faturável cobrável, o sistema MUST registrar
  exatamente uma pendência de envio da lista de pedidos feitos pelo chat
  para o telefone de contato daquela reserva.
- **FR-002**: A lista enviada ao hóspede MUST ser uma mensagem distinta da
  pesquisa de saída. MUST NOT incorporar a lista no texto da pesquisa.
  MUST NOT alterar as três partes já definidas da pesquisa.
- **FR-003**: A mensagem da lista MUST usar o rótulo "pedidos feitos pelo
  chat" e MUST NOT usar as palavras "extrato" nem "conta" em nenhum texto
  desta funcionalidade (mensagem ao hóspede, consulta no painel, rótulos
  visíveis).
- **FR-004**: Cada item da lista MUST exibir a descrição do que foi pedido
  e o valor praticado no instante daquele pedido. MUST NOT exibir o preço
  atual do item vendável quando este divergir do valor praticado.
- **FR-005**: A lista MUST incluir somente consumos faturáveis daquela
  reserva cujo destino seja cobrança: pendente de lançamento ou já
  lançado. MUST NOT incluir pedido de serviço sem cobrança. MUST NOT
  incluir consumo dispensado.
- **FR-006**: A lista MUST NOT exibir ao hóspede o status interno de
  lançamento (pendente, lançado). MUST NOT afirmar que o valor já foi
  lançado no sistema de gestão do hotel.
- **FR-007**: A mensagem MUST deixar explícito que a lista cobre somente o
  que foi solicitado pelo chat. MUST NOT afirmar ser a fatura da estadia,
  o total a pagar no balcão, nem a conferência do que foi lançado no outro
  sistema da casa.
- **FR-008**: A lista MUST NOT pedir confirmação ao hóspede, MUST NOT
  perguntar se os itens estão corretos e MUST NOT convidar a pagar por
  aquele canal.
- **FR-009**: Reserva sem consumo faturável cobrável MUST NOT gerar
  pendência de envio nem mensagem de lista. A pesquisa de saída MUST
  continuar no fluxo já existente.
- **FR-010**: A intenção de envio MUST ser registrada de forma durável, e
  a entrega MUST acontecer em processamento posterior — não na mesma
  operação síncrona que confirma o clique de saída à recepção. Falha no
  envio MUST NOT desfazer o status encerrado.
- **FR-011**: O retry técnico de um envio falho MUST NOT resultar em uma
  segunda lista distinta para a mesma reserva — no máximo uma lista
  lógica por reserva neste fluxo. A unicidade MUST ser garantida pelo
  armazenamento, não por conferência prévia em código: duas execuções
  simultâneas MUST resultar em uma única lista.
- **FR-012**: Todo envio ao hóspede MUST passar por uma porta de
  mensageria substituível, de modo que sucesso e falha possam ser
  exercitados sem rede de provedor real.
- **FR-013**: A lista efetivamente enviada (ou tentada com registro) MUST
  aparecer no histórico de conversa da reserva como mensagem de saída,
  com estado de entrega observável (pendente, enviada, entregue ou falha).
- **FR-014**: Recepção e gestão da propriedade MUST poder consultar a
  lista de pedidos feitos pelo chat de uma reserva da casa, com o mesmo
  recorte e os mesmos valores da mensagem, inclusive quando o envio ainda
  não ocorreu, falhou ou a reserva não tem itens cobráveis (lista vazia).
- **FR-015**: Perfil operacional MUST ser recusado na consulta. Tentativa
  sobre reserva de outro hotel MUST ser recusada sem confirmar que a
  reserva existe.
- **FR-016**: Toda leitura e disparo MUST considerar o hotel da sessão.
  Consumo de um hotel MUST NOT aparecer na lista de outro.
- **FR-017**: Lançar ou dispensar consumo depois do envio MUST NOT
  disparar correção automática nem segunda lista. MUST NOT haver lembrete
  se o hóspede não responder — a lista não pede resposta.
- **FR-018**: Contestar a lista por mensagem MUST NOT corrigir item
  automaticamente e MUST NOT ser interpretado por esta fatia como resposta
  à pesquisa de saída. Na dúvida, um humano vê, no caminho já existente.
- **FR-019**: O único dado pessoal permitido no corpo da mensagem da lista
  é o primeiro nome. Conteúdo da lista, descrição de item e valor
  praticado NUNCA MUST aparecer em log; logs registram identificadores,
  hotel e resultado — nunca o texto nem o valor por extenso.
- **FR-020**: Esta fatia MUST NOT confirmar saída por conta própria, MUST
  NOT lançar nem dispensar consumo, MUST NOT alterar valor praticado, MUST
  NOT inferir checkout a partir de mensagem, MUST NOT enviar oferta de
  retorno e MUST NOT consultar o hóspede sobre a lista durante a estadia.
- **FR-021**: Consulta no painel e montagem da mensagem MUST ser possíveis
  sem o provedor real de mensagens: itens, exclusões, valores históricos,
  lista vazia e unicidade devolvem desfechos previsíveis, sem rede.

### Key Entities

- **Lista de pedidos feitos pelo chat**: conferência, no encerramento, do
  que a reserva solicitou pelo chat **e gera cobrança**. Uma por reserva,
  mensagem distinta da pesquisa de saída. Rótulo fixo; nunca "extrato" nem
  "conta".
- **Item cobrável da lista**: consumo faturável da reserva em estado
  pendente ou lançado, com a descrição do pedido e o valor praticado naquele
  instante. Serviço operacional e consumo dispensado não são item
  desta lista.
- **Valor praticado**: quantia gravada no momento do pedido; não acompanha
  reajuste posterior do cardápio.
- **Consulta no painel**: a mesma lista, recuperável pela recepção e pela
  gestão da propriedade, independentemente da entrega da mensagem.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das confirmações de saída de reserva hospedada da
  própria propriedade com ao menos um consumo cobrável, o hóspede fica com
  exatamente 1 lista de pedidos feitos pelo chat pendente ou enviada, em
  mensagem distinta da pesquisa de saída.
- **SC-002**: Em 100% das confirmações de saída sem consumo cobrável, 0
  mensagens de lista nascem; 100% das pesquisas de saída daqueles
  encerramentos continuam no fluxo já existente.
- **SC-003**: Em 100% das listas montadas a partir de reserva mista
  (consumo cobrável + serviço sem custo + consumo dispensado), 100% dos
  itens visíveis são cobráveis e 0 serviços sem custo ou dispensados
  aparecem.
- **SC-004**: Após reajuste do preço atual de um item já pedido, 100% das
  listas exibem o valor praticado original daquele pedido — 0 listas
  mostram o preço novo.
- **SC-005**: Em verificação com envio falho, 100% das reservas
  permanecem encerradas, o hóspede recebe no máximo 1 lista lógica (a
  mesma, retomada) e 100% das consultas no painel ainda devolvem os
  itens — 0 desfazimentos, 0 listas distintas extras.
- **SC-006**: Em 100% dos textos desta funcionalidade (mensagem e painel),
  as palavras "extrato" e "conta" não aparecem; 100% usam o rótulo
  "pedidos feitos pelo chat"; 0 mensagens afirmam ser a fatura da estadia
  ou pedem confirmação/pagamento.
- **SC-007**: Em verificação com dois hotéis, 100% das tentativas de
  consultar lista de reserva alheia são recusadas; 0 listas do hotel A
  são enviadas ou exibidas por sessão do hotel B.
- **SC-008**: Em verificação com sessão operacional, 100% das tentativas
  de consultar a lista são recusadas. Gestão consulta; 0 confirmações de
  saída partem desse perfil.
- **SC-009**: Hóspede com itens cobráveis consegue conferir a lista em
  uma única mensagem, compatível com o tempo de quem já saiu do balcão
  (sem pergunta extra, sem formulário).
- **SC-010**: Recepção conclui a conferência no painel em uma única
  consulta por reserva, inclusive quando a mensagem ao hóspede falhou.
- **SC-011**: O caminho checkout → lista (sucesso, falha, lista vazia) é
  verificável de ponta a ponta sem chamada à rede do provedor real de
  mensagens e sem tela visual nova.

## Assumptions

- As fatias até F4.1 estão concluídas. Consumo faturável já nasce com
  valor praticado e estados pendente / lançado / dispensado. A
  confirmação de saída já encerra a reserva e dispara a pesquisa curta
  **sem** a lista. Esta fatia acrescenta a lista nesse mesmo momento de
  encerramento, sem reinventar o clique nem o canal.
- **Independência estrutural (já decidida):** o envio não roda dentro da
  operação que confirma o clique. A confirmação registra a intenção de
  envio de forma durável e um processamento posterior entrega — o mesmo
  padrão da pesquisa de saída.
- **Porta de mensageria (já decidida):** todo envio passa pela interface
  substituível; testes usam implementação falsa; nenhum teste chama o
  provedor real.
- **Unicidade no armazenamento (já decidida):** “exatamente uma lista por
  reserva” é garantia de unicidade, no mesmo padrão da pesquisa de saída.
  Conferência prévia em código não satisfaz FR-011.
- A lista é **uma** mensagem informativa, não uma pergunta. Não há
  conversa de conferência item a item. Contestação escrita cai no
  caminho humano já existente do encerramento; esta fatia não cria
  intenção nova na classificação nem atendimento automático de cobrança
  depois do checkout.
- Ordem de chegada entre pesquisa de saída e lista **não** é prometida.
  São duas pendências independentes. O produto não garante qual mensagem
  o hóspede lê primeiro.
- **Lista vazia = silêncio.** Sem item cobrável, não se envia recado. O
  painel continua consultável. Não há disparo retroativo para reservas
  já encerradas antes desta fatia.
- **Dispensado fica de fora** porque não será cobrado. Pendente entra
  porque a lista é conferência do que o chat gerou para cobrança, não
  do clique no outro sistema — lançamento pode ocorrer depois da saída,
  decisão já tomada no consumo faturável.
- Lançar ou dispensar **depois** do envio não gera segunda mensagem
  (Artigo VII). A correção, se existir, é humana no balcão.
- Upsell citado nos artefatos só entra quando já tiver virado consumo
  faturável no chat. Não há transação de upsell à parte nesta fatia.
- Soma dos itens: a mensagem **pode** exibir o total **somente** desses
  pedidos feitos pelo chat, desde que o rótulo não sugira fatura da
  estadia. Omitir a soma também é aceitável se os itens individuais
  estiverem visíveis. Em nenhum caso a soma se chama "extrato" ou
  "conta".
- Superfície de uso: mensagem ao hóspede, histórico da conversa e
  consulta autenticada no painel. Ligar o protótipo React continua fora
  do critério de pronto, no mesmo padrão das fatias anteriores.
- Gestão consulta a lista (accountability); não confirma saída. Operação
  não confere cobrança. Isolamento por propriedade vale mesmo com uma
  única propriedade cadastrada.
- Permissão de confirmar a saída permanece a da recepção, já usada no
  encerramento. Esta fatia não cria um segundo clique no balcão para
  “liberar a lista”.
- Conteúdo de mensagem nunca vai para log; valor praticado tampouco vai
  por extenso, no padrão do consumo faturável.
- Consulta da lista pelo hóspede **durante** a estadia (pedido espontâneo
  no chat) fica fora — o backlog situa a conferência no encerramento, e
  uma intenção nova na conversa seria fatia própria.
