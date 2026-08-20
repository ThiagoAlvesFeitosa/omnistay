# Feature Specification: Confirmar Saída e Pesquisa

**Feature Branch**: `018-confirmar-saida`

**Created**: 2026-08-20

**Status**: Draft

**Input**: User description: "A recepção confirma a saída do hóspede no painel, o
que encerra a estadia e envia a pesquisa de avaliação. A pesquisa é curta —
nota, comentário opcional e uma pergunta final sobre aceitar receber
comunicações futuras. A resposta a essa última pergunta é registrada como
consentimento, com data e hora, e pode ser revogada depois. Reservas com
saída prevista vencida e ainda não confirmadas são destacadas na fila."
(backlog F4.1)

Restrições já decididas no projeto (entrada do specify): a transição de fase
é disparada pelo clique da recepção, nunca por integração com o sistema de
gestão do hotel; não se faz checkout de quem não fez check-in; gravar antes
de enviar — falha de entrega não desfaz o encerramento; a ausência do clique
precisa ficar visível na fila; a pesquisa é curta (nota, comentário opcional,
aceite) e não inclui oferta de retorno; o consentimento é histórico (nunca se
apaga o registro anterior); silêncio após a estadia é a experiência esperada
— sem lembrete se o hóspede não responder; a lista de pedidos feitos pelo
chat pertence à fatia seguinte; as palavras "extrato" e "conta" não existem
neste produto.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirmar a saída no painel (Priority: P1)

Como recepcionista, quero confirmar no painel que o hóspede saiu, para o
sistema registrar o instante real da partida e encerrar a estadia — o hotel
passa a tratar aquela reserva como concluída, e o clique humano continua
sendo a única ponte com o que aconteceu no balcão.

**Why this priority**: Sem este clique, a pesquisa não sai e o sistema
continua achando que a pessoa está hospedada. É a travessia de fronteira da
partida: o produto não se integra ao sistema de gestão do hotel, então a
confirmação é ação da recepção, não detecção automática.

**Independent Test**: Pode ser testado autenticando como recepção,
confirmando a saída de uma reserva hospedada, e verificando que o status
passa a encerrado, que o momento real da partida fica registrado e é
distinto da data prevista, e que a reserva deixa de aparecer como saída
atrasada na fila do dia.

**Acceptance Scenarios**:

1. **Given** uma sessão autenticada de perfil de recepção e uma reserva da
   propriedade da sessão com entrada já confirmada (hospedada), **When** a
   recepção confirma a saída, **Then** a reserva passa a encerrada e o
   momento real da partida fica gravado.
2. **Given** uma confirmação de saída bem-sucedida, **When** se consulta o
   momento registrado, **Then** ele corresponde ao instante da confirmação —
   não à data prevista de saída.
3. **Given** uma reserva cuja data prevista de saída já passou e que estava
   destacada como saída não confirmada, **When** a recepção confirma a
   saída, **Then** o destaque desaparece na consulta seguinte da fila do dia.
4. **Given** uma reserva hospedada cuja data prevista de saída ainda não
   chegou, **When** a recepção confirma a saída, **Then** a confirmação é
   aceita: saída antecipada no balcão não espera o calendário.

---

### User Story 2 - Disparar a pesquisa curta de avaliação (Priority: P1)

Como hóspede que acabou de fazer o checkout no balcão, quero receber em
seguida uma pesquisa curta no celular — nota de 1 a 5, comentário se eu
quiser e uma pergunta final se aceito comunicações futuras — para eu
conseguir responder enquanto caminho até o carro, sem formulário longo, sem
oferta de volta e sem lista de gastos.

**Why this priority**: É o valor visível da saída para o hotel (última
impressão em canal privado) e a coleta de consentimento que substitui a
oferta de retorno retirada do produto. Pesquisa longa não é respondida;
oferta disfarçada de avaliação é marketing; lista de pedidos é fatia
seguinte.

**Independent Test**: Pode ser testado confirmando a saída, inspecionando a
mensagem entregue (via canal falso de mensageria) e verificando: exatamente
uma pesquisa, os três pedidos (nota, comentário opcional, aceite), ausência
de oferta, ausência de lista de pedidos, ausência das palavras "extrato" e
"conta", unicidade do disparo.

**Acceptance Scenarios**:

1. **Given** uma confirmação de saída bem-sucedida, **When** o envio da
   pesquisa é processado, **Then** o hóspede recebe exatamente uma mensagem
   de pesquisa no telefone de contato da reserva, com nota de 1 a 5,
   comentário opcional e uma pergunta final de aceite para comunicações
   futuras.
2. **Given** o texto da pesquisa montado para envio, **When** ele é
   inspecionado, **Then** não há oferta comercial, desconto, convite de
   retorno nem lista do que foi pedido pelo chat; não aparecem as palavras
   "extrato" nem "conta"; o único dado pessoal permitido no corpo é o
   primeiro nome.
3. **Given** a pergunta final de aceite, **When** ela é inspecionada,
   **Then** é específica para comunicações futuras (não vem pré-marcada, não
   está embutida na nota) e deixa claro que recusar é tão válido quanto
   aceitar.
4. **Given** uma reserva cuja saída já foi confirmada e cuja pesquisa já foi
   disparada, **When** ninguém altera aquela reserva, **Then** o sistema não
   dispara uma segunda pesquisa de saída para a mesma reserva.
5. **Given** uma reserva com reclamação ainda aberta, consumo pendente de
   lançamento ou pulso já enviado, **When** a recepção confirma a saída,
   **Then** a pesquisa de saída mesmo assim é disparada — o pulso é
   instrumento de recuperação durante a estadia; a pesquisa da saída não se
   suprime por chamado aberto.

---

### User Story 3 - Recusar confirmação inválida sem corromper o ciclo (Priority: P1)

Como recepcionista, quero que o sistema recuse confirmar saída de reserva
que ainda não está hospedada, já encerrada ou já cancelada, com recusa
clara, para um clique no lugar errado não encerrar quem não chegou, não
reabrir estadia e não pular a máquina de estados já vigente.

**Why this priority**: A garantia de transição mora no ciclo de vida da
reserva. Checkout de quem não fez check-in corromperia o histórico —
exatamente o que a regra de estados existe para impedir.

**Independent Test**: Pode ser testado tentando confirmar saída em cada
estado recusado e verificando que o status não muda, que o momento de
partida não é gravado (ou permanece o já existente, no caso de já
encerrada) e que nenhuma pesquisa de saída nasce.

**Acceptance Scenarios**:

1. **Given** uma reserva ainda não hospedada (aguardando cadastro, ficha
   recebida, ficha parcial ou chegará sem cadastro prévio), **When** a
   recepção tenta confirmar a saída, **Then** a operação é recusada, o
   status permanece e nenhuma pesquisa é disparada.
2. **Given** uma reserva já encerrada, **When** a recepção confirma de novo,
   **Then** a operação é recusada, o momento de partida já registrado
   permanece intacto e uma segunda pesquisa não é criada.
3. **Given** uma reserva cancelada, **When** a recepção tenta confirmar a
   saída, **Then** a operação é recusada — depois do cancelamento o caminho
   não é o checkout.
4. **Given** uma reserva hospedada com chamado aberto ou com consumo ainda
   pendente de lançamento, **When** a recepção confirma a saída, **Then** a
   confirmação é aceita: chamado e lançamento não bloqueiam o clique do
   balcão; esta fatia não fecha chamado nem lança consumo.

---

### User Story 4 - Destacar na fila quem deveria ter saído e não foi confirmado (Priority: P1)

Como recepcionista, quero ver destacadas na fila do dia as reservas cuja
data prevista de saída já passou e que ainda estão hospedadas, para o clique
esquecido não falhar em silêncio — o sistema não sabe se a pessoa foi
embora, mas sabe que deveria ter ido, e a ausência de uma pesquisa não gera
reclamação.

**Why this priority**: A ausência de ação humana precisa ser visível. Sem o
destaque, a pesquisa simplesmente não é enviada e ninguém percebe. Esta
fatia torna a omissão perceptível; não a elimina.

**Independent Test**: Pode ser testado consultando a fila do dia com uma
reserva hospedada com saída prevista vencida, uma com saída prevista hoje e
uma já encerrada, e verificando que só a vencida não confirmada aparece com
o destaque de saída.

**Acceptance Scenarios**:

1. **Given** uma reserva da propriedade da sessão ainda hospedada cuja data
   prevista de saída é anterior ao dia corrente, **When** a recepção
   consulta a fila do dia, **Then** aquela reserva aparece com destaque
   distinguível de saída não confirmada — distinto do destaque de chegada
   atrasada e do de boas-vindas que não saíram.
2. **Given** uma reserva hospedada cuja data prevista de saída é o dia
   corrente, **When** a recepção consulta a fila do dia, **Then** a reserva
   pode aparecer na fila, porém sem o destaque de saída vencida — o dia
   previsto ainda não venceu.
3. **Given** uma reserva já encerrada ou cancelada, **When** a fila do dia é
   consultada, **Then** ela não aparece como saída não confirmada
   (encerrada saiu da fila; cancelada não integra a fila).

---

### User Story 5 - Registrar nota, comentário e aceite a partir da resposta (Priority: P1)

Como hotel, quero que a resposta do hóspede à pesquisa vire nota, comentário
opcional e um registro de consentimento (aceite ou recusa) com data e hora,
sem inventar o que ele não disse e sem cobrar de novo se ele ficar em
silêncio.

**Why this priority**: Sem este registro a pesquisa é teatro. Inventar
aceite a partir do silêncio ou da nota viola a base legal das comunicações
futuras. Lembrete depois da estadia é intrusão e, no canal, vira
marketing.

**Independent Test**: Pode ser testado com resposta completa, com só a
nota, com recusa explícita, com silêncio e com texto irreconhecível,
verificando o que foi gravado, o que não foi inventado e a ausência de
segunda mensagem cobrando resposta.

**Acceptance Scenarios**:

1. **Given** uma pesquisa de saída enviada, **When** o hóspede responde com
   nota de 1 a 5, comentário e aceite explícito (sim ou não), **Then**
   existe exatamente uma avaliação de saída daquela reserva com a nota e o
   comentário, e existe um registro de consentimento do titular com o valor
   respondido, o instante e a origem na pesquisa de saída.
2. **Given** uma resposta que traz a nota e omite o comentário, **When** ela
   é interpretada, **Then** a avaliação de saída é gravada com a nota e sem
   comentário — comentário é opcional e não bloqueia o restante.
3. **Given** uma resposta que traz a nota mas não responde à pergunta de
   aceite, **When** ela é interpretada, **Then** a avaliação é gravada e
   **nenhum** consentimento é criado: silêncio na pergunta de aceite não é
   aceite nem recusa.
4. **Given** uma pesquisa enviada, **When** o hóspede não responde, **Then**
   não existe avaliação de saída daquela reserva, não existe registro de
   consentimento originado nessa pesquisa e não sai lembrete.
5. **Given** a pesquisa já respondida por completo (nota registrada e
   pergunta de aceite respondida), **When** o hóspede escreve de novo,
   **Then** essa mensagem **não** altera a avaliação de saída nem cria
   segundo consentimento da mesma pesquisa.

---

### User Story 6 - Texto irreconhecível vai para humano, sem inventar nota nem aceite (Priority: P1)

Como hotel, quando não for possível dizer qual é a nota ou se o hóspede
aceitou comunicações futuras, quero que um humano veja a mensagem, sem o
sistema fingir que entendeu e sem descartar o que chegou.

**Why this priority**: Na dúvida, um humano vê. Consentimento inventado ou
descarte silencioso são os dois erros que esta regra existe para impedir.

**Independent Test**: Pode ser testado com resposta ambígua e com serviço
de interpretação indisponível, verificando: mensagem preservada, visível
para a recepção, zero nota inventada, zero consentimento inventado, zero
segunda pesquisa.

**Acceptance Scenarios**:

1. **Given** uma resposta à pesquisa cuja nota ou cujo aceite não se
   reconhece, **When** o sistema a interpreta, **Then** a mensagem
   permanece, a recepção vê que precisa de leitura humana, e não nasce nota
   nem consentimento inventados.
2. **Given** o serviço de interpretação indisponível ou resposta em formato
   inválido, **When** chega a resposta à pesquisa, **Then** o mesmo
   desfecho: preservar, sinalizar humano, não inventar.
3. **Given** esse desfecho, **When** o hóspede consulta a conversa, **Then**
   não recebe pergunta nova de pesquisa nem recado que afirme ter
   entendido a avaliação.

---

### User Story 7 - Consultar o consentimento vigente em qualquer data passada (Priority: P1)

Como hotel, quero consultar se o titular aceitava comunicações futuras numa
data passada — e não só se aceita hoje — para poder demonstrar o estado em
cada momento, que é a pergunta de uma eventual fiscalização.

**Why this priority**: Consentimento não é um interruptor. Um único
"aceita/não aceita" apaga a história. O critério de aceite desta fatia é
devolver o estado vigente em qualquer data passada.

**Independent Test**: Pode ser testado gravando aceite, depois recusa, e
consultando uma data entre os dois eventos, uma data anterior ao primeiro e
uma data posterior ao último, conferindo o valor vigente em cada instante.

**Acceptance Scenarios**:

1. **Given** um titular sem nenhum registro de consentimento, **When** se
   consulta o estado em qualquer data, **Then** o resultado é "não
   concedido" — ausência de registro não é aceite.
2. **Given** um aceite na pesquisa e, depois, uma revogação, **When** se
   consulta uma data entre os dois registros, **Then** o estado vigente
   nessa data é o aceite; **When** se consulta uma data posterior à
   revogação, **Then** o estado vigente é a recusa.
3. **Given** a consulta, **When** ela é feita pela recepção ou pela gestão
   da própria propriedade, **Then** é permitida; **When** é feita por perfil
   operacional ou por sessão de outro hotel, **Then** é recusada sem revelar
   que o hóspede existe.

---

### User Story 8 - Revogar depois, sem apagar o que já foi gravado (Priority: P1)

Como titular, quero poder desistir das comunicações futuras depois de ter
aceito na pesquisa, e quero que o hotel registre essa desistência sem
apagar o aceite original — o histórico continua demonstrável.

**Why this priority**: Consentimento revogável é exigência da coleta, não
evolução. Apagar o registro anterior destruiria a prova de que, na data da
pesquisa, o aceite existia.

**Independent Test**: Pode ser testado com um aceite já gravado, registrando
uma revogação pelo painel, e verificando: novo registro com recusa, instante
e origem; registro anterior intacto; consulta "hoje" devolve recusa;
consulta na data do aceite ainda devolve aceite.

**Acceptance Scenarios**:

1. **Given** um titular que aceitou na pesquisa de saída, **When** a
   recepção ou a gestão da propriedade registra a revogação no painel,
   **Then** nasce um novo registro com recusa, instante e origem no painel
   (ou no pedido do titular, quando a revogação foi a pedido dele), e o
   registro do aceite permanece.
2. **Given** essa revogação, **When** se tenta alterar o registro do aceite
   original, **Then** ele permanece como estava — revogação não edita nem
   apaga linha anterior.
3. **Given** um titular que recusou na pesquisa, **When** a recepção tenta
   "revogar" de novo, **Then** ainda assim nasce um novo registro (o
   histórico continua append-only); o estado vigente continua recusado.
4. **Given** uma sessão de perfil operacional, **When** tenta registrar
   revogação, **Then** a operação é recusada.

---

### User Story 9 - Isolar a saída por hotel e por perfil (Priority: P1)

Como responsável pelos dados da propriedade, quero que só a recepção do
próprio hotel confirme saída, que gestão e operação recebam recusa no
clique, e que a reserva de um hotel nunca seja encerrada por sessão de
outro.

**Why this priority**: Multi-tenant e autorização já existem; esta fatia
dispara a transição para encerrado e precisa herdar essas fronteiras.
Gestão consulta; operação não opera o balcão.

**Independent Test**: Pode ser testado tentando confirmar saída com cada
perfil e com sessão de outro hotel, verificando recusas e isolamento, sem
disparar pesquisa nos caminhos recusados.

**Acceptance Scenarios**:

1. **Given** uma reserva do hotel A, **When** uma sessão do hotel B tenta
   confirmar a saída, **Then** a operação é recusada sem revelar que a
   reserva existe, e o status não muda.
2. **Given** uma sessão de perfil de gestão ou operacional, **When** tenta
   confirmar a saída de uma reserva da própria propriedade, **Then** a
   operação é recusada.
3. **Given** uma sessão de recepção, **When** confirma a saída de uma
   reserva hospedada da própria propriedade, **Then** a operação é aceita.

---

### User Story 10 - Falha de envio não desfaz o checkout nem duplica a pesquisa (Priority: P1)

Como hotel, quero que a intenção de enviar a pesquisa fique gravada **antes**
da tentativa de entrega. Se a entrega falhar, quero retomar **a mesma**
pesquisa — não uma segunda. O checkout já aconteceu no balcão e não se
desfaz.

**Why this priority**: Gravar antes de enviar vale para toda mensagem. Perder
a pesquisa é tolerável; reabrir a estadia ou mandar duas pesquisas não é.

**Independent Test**: Pode ser testado confirmando a saída, falhando o
envio, retomando (uma pesquisa) e tentando processar em paralelo (ainda uma).

**Acceptance Scenarios**:

1. **Given** a saída confirmada e o envio da pesquisa falho, **When** o
   trabalho é retomado, **Then** tenta-se de novo a mesma pesquisa; a
   reserva permanece encerrada; o hóspede não recebe uma segunda pesquisa
   distinta.
2. **Given** duas execuções simultâneas do envio para a mesma reserva,
   **When** ambas tentam criar a pesquisa, **Then** existe exatamente uma;
   a segunda é recusada pela garantia de unicidade do armazenamento.
3. **Given** falha na gravação da intenção de enviar, **When** o ciclo
   termina, **Then** o hóspede não recebe pesquisa que ainda não foi
   gravada; se a confirmação da saída já persistiu, a reserva permanece
   encerrada e a omissão fica visível para nova tentativa.

---

### User Story 11 - Conteúdo da mensagem não vaza em log (Priority: P2)

Como titular dos dados, quero que a pesquisa, a resposta, o comentário e a
pergunta de aceite nunca apareçam em log operacional.

**Why this priority**: Minimização de dados pessoais. Log registra
identificadores e resultado, nunca o texto.

**Independent Test**: Pode ser testado nos desfechos confirmar, enviar,
responder, recusar, revogar e falhar, inspecionando logs: identificadores e
código; zero texto de mensagem, zero comentário, zero resposta de aceite.

**Acceptance Scenarios**:

1. **Given** saída confirmada, pesquisa enviada, respondida, recusada,
   revogada ou com falha de envio, **When** o sistema registra log
   operacional, **Then** há identificadores, a propriedade e o resultado —
   e não o texto da pesquisa, da resposta, do comentário nem da pergunta de
   aceite.

---

### Edge Cases

- Saída antecipada (confirmação antes da data prevista de saída): permitida
  se a reserva estiver hospedada. O destaque de vencida não se aplica
  enquanto a data prevista não passar.
- Saída no mesmo dia da entrada (day use): permitida. A pesquisa segue o
  mesmo caminho. Esta fatia não exige estadia mínima.
- Reclamação aberta, pedido em andamento ou consumo pendente de lançamento:
  **não** bloqueiam o checkout e **não** suprimem a pesquisa. Chamado não é
  fechado automaticamente; lançamento não é marcado como feito. A lista de
  pedidos feitos pelo chat não entra nesta fatia.
- Pulso do segundo dia já enviado (ou ainda pendente): a avaliação de pulso
  permanece; a avaliação de saída é outro registro, da mesma reserva, com
  origem distinta. As duas podem coexistir. Esta fatia não reinterpreta o
  pulso.
- Hóspede que não recebeu boas-vindas e faz checkout: a saída é confirmada;
  boas-vindas atrasadas **não** saem depois do encerramento (já decidido na
  chegada). A pesquisa de saída é independente.
- Dois hóspedes na mesma reserva: a pesquisa vai ao telefone de contato da
  reserva (titular), uma vez. O consentimento gravado é o do titular.
  Acompanhante não recebe pesquisa própria nesta fatia.
- Duas reservas distintas no mesmo telefone: cada confirmação de saída
  dispara a própria pesquisa. Mensagem de entrada, nesse caso, segue a
  reserva ativa (cadastro em andamento ou hospedada) quando houver — a
  ficha ou a estadia em curso não pode ser engolida pela pesquisa de uma
  estadia já encerrada. Pesquisa incompleta da encerrada permanece
  incompleta até uma resposta atribuível a ela.
- Reserva encerrada com pesquisa ainda incompleta e nenhuma outra reserva
  no mesmo telefone: a mensagem de entrada é tratada como resposta à
  pesquisa enquanto a janela de atribuição da propriedade estiver aberta.
- Janela de atribuição vencida ou pesquisa já completa: mensagem posterior
  **não** vira nota nem consentimento. Na dúvida, um humano vê; não há
  atendimento operacional de toalha depois do checkout nesta fatia.
- Silêncio na pergunta de aceite: nenhum registro de consentimento.
  Ausência ≠ recusa ≠ aceite. Consulta posterior devolve "não concedido".
- Nota fora de 1 a 5, texto que não permite reconhecer a nota, ou serviço
  de interpretação indisponível: leitura humana, sem inventar.
- Retry técnico de um envio que eventualmente sucede: o hóspede recebe no
  máximo uma pesquisa de saída por reserva.
- Inferência de checkout por mensagem do hóspede ("já saí", "estou no
  aeroporto"), confirmação em lote e tela React do painel **não** fazem
  parte desta fatia.
- Oferta de retorno, mensagem promocional semanas depois e lista de
  pedidos feitos pelo chat **não** fazem parte desta fatia.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A recepção MUST poder confirmar a saída de uma reserva da
  própria propriedade que esteja hospedada (entrada já confirmada).
- **FR-002**: A confirmação bem-sucedida MUST alterar o status da reserva
  para encerrado e MUST gravar o momento real da partida (instante da
  confirmação, não a data prevista de saída).
- **FR-003**: Confirmação MUST ser recusada quando a reserva ainda não
  estiver hospedada, já estiver encerrada ou estiver cancelada. A recusa
  MUST deixar claro que a operação não ocorreu. Status e momento de
  partida MUST permanecer como estavam.
- **FR-004**: Tentativa recusada MUST NOT criar pendência de envio nem
  mensagem de pesquisa de saída.
- **FR-005**: Reclamação em aberto, pedido em andamento e consumo pendente
  de lançamento MUST NOT impedir a confirmação de saída e MUST NOT
  suprimir a pesquisa. Esta fatia MUST NOT resolver chamado e MUST NOT
  marcar lançamento.
- **FR-006**: A confirmação MUST concluir com a reserva persistida no novo
  estado. A intenção de envio da pesquisa MUST ser registrada de forma
  durável e a entrega MUST acontecer em processamento posterior — não na
  mesma operação síncrona que confirma o clique à recepção.
- **FR-007**: Falha no envio da pesquisa MUST NOT desfazer o status
  encerrado nem apagar o momento de partida já gravado.
- **FR-008**: O retry técnico de um envio falho MUST NOT resultar em uma
  segunda pesquisa distinta para a mesma reserva — no máximo uma pesquisa
  lógica por reserva neste fluxo. A unicidade MUST ser garantida pelo
  armazenamento, não por conferência prévia em código: duas execuções
  simultâneas MUST resultar em uma única pesquisa.
- **FR-009**: Ao confirmar a saída, o sistema MUST registrar exatamente uma
  pendência de envio da pesquisa para o telefone de contato daquela
  reserva.
- **FR-010**: A pesquisa MUST ser uma mensagem curta que pede (a) uma nota
  de 1 a 5, (b) um comentário opcional e (c) uma pergunta final, específica,
  sobre aceitar receber comunicações futuras. MUST haver exatamente essas
  três partes, nada além.
- **FR-011**: A pesquisa MUST NOT conter oferta comercial, desconto,
  convite de retorno, lista de pedidos feitos pelo chat, nem as palavras
  "extrato" ou "conta". O único dado pessoal permitido no corpo é o
  primeiro nome.
- **FR-012**: A pergunta de aceite MUST ser destacável da nota: aceitar a
  pesquisa ou dar nota alta MUST NOT ser interpretado como aceite de
  comunicação futura.
- **FR-013**: Todo envio ao hóspede MUST passar por uma porta de
  mensageria substituível, de modo que sucesso e falha possam ser
  exercitados sem rede de provedor real.
- **FR-014**: A pesquisa efetivamente enviada (ou tentada com registro)
  MUST aparecer no histórico de conversa da reserva como mensagem de
  saída, com estado de entrega observável (pendente, enviada, entregue ou
  falha).
- **FR-015**: A fila do dia da recepção MUST destacar de forma
  distinguível a reserva ainda hospedada cuja data prevista de saída é
  anterior ao dia corrente (saída não confirmada). O destaque MUST ser
  distinto do de chegada atrasada e do de boas-vindas não enviadas.
- **FR-016**: Após confirmação bem-sucedida, a reserva MUST deixar de
  constar como saída não confirmada na consulta seguinte da fila do dia.
- **FR-017**: Reserva hospedada com saída prevista no dia corrente MUST
  aparecer na fila sem o destaque de saída vencida.
- **FR-018**: Toda leitura, confirmação, consulta de consentimento e
  revogação MUST considerar o hotel da sessão. Reserva ou hóspede de um
  hotel MUST NOT ser visível como alterável por outro.
- **FR-019**: Confirmar saída MUST ser exclusivo do perfil de recepção.
  Gestão e perfil operacional MUST receber recusa no clique.
- **FR-020**: Tentativa de confirmar reserva de outro hotel MUST ser
  recusada sem confirmar que a reserva existe.
- **FR-021**: Resposta reconhecida à pesquisa MUST registrar no máximo uma
  avaliação de saída por reserva, com nota (1 a 5), comentário opcional e
  instante. Essa avaliação MUST distinguir-se da avaliação de pulso do
  segundo dia, que pode já existir na mesma reserva.
- **FR-022**: Quando a pergunta de aceite for respondida de forma
  reconhecível (sim ou não), o sistema MUST inserir um novo registro de
  consentimento do titular da reserva, com finalidade de comunicações
  futuras, valor (concedido ou recusado), instante e origem na pesquisa de
  saída. MUST NOT atualizar nem apagar registro anterior.
- **FR-023**: Silêncio do hóspede, ausência de resposta à pergunta de
  aceite e nota isolada MUST NOT criar registro de consentimento. Ausência
  de registro MUST ser consultada como não concedido.
- **FR-024**: MUST NOT haver lembrete nem segunda pesquisa se o hóspede não
  responder.
- **FR-025**: Respostas do hóspede MUST ser atribuídas à pesquisa de saída
  somente enquanto ela estiver incompleta (falta nota reconhecida ou falta
  resposta à pergunta de aceite) **e** dentro do prazo de atribuição
  configurado na propriedade, contado do instante real da saída. Propriedade
  nova MUST nascer com esse prazo já configurado. Ausência da chave MUST
  impedir a atribuição automática de forma explícita, sem assumir número
  embutido.
- **FR-026**: Nota irreconhecível, aceite irreconhecível, serviço de
  interpretação indisponível ou formato inválido MUST preservar a
  mensagem, MUST sinalizar atendimento humano à recepção da propriedade,
  MUST NOT inventar nota nem consentimento e MUST NOT enviar segunda
  pesquisa.
- **FR-027**: Quando o mesmo telefone tiver reserva encerrada com pesquisa
  incompleta e outra reserva em cadastro ou hospedada, a mensagem MUST
  seguir a reserva ativa. MUST NOT engolir ficha nem estadia em curso.
- **FR-028**: Recepção e gestão da propriedade MUST poder consultar o
  estado de consentimento vigente de um hóspede da casa em qualquer data
  passada: o registro mais recente daquela finalidade cujo instante seja
  menor ou igual à data consultada; nenhum registro MUST significar não
  concedido. Perfil operacional MUST ser recusado.
- **FR-029**: Recepção e gestão MUST poder registrar uma revogação (ou um
  novo aceite) posterior, que MUST inserir nova linha com instante e
  origem no painel ou no pedido do titular, sem alterar linhas anteriores.
  Perfil operacional MUST ser recusado.
- **FR-030**: Conteúdo de mensagem, comentário de avaliação e resposta de
  aceite NUNCA MUST aparecer em log; logs registram identificadores, hotel
  e resultado — nunca o texto.
- **FR-031**: Esta fatia MUST NOT confirmar chegada, MUST NOT cancelar
  reserva, MUST NOT enviar lista de pedidos feitos pelo chat, MUST NOT
  disparar oferta de retorno e MUST NOT inferir checkout a partir de
  mensagem do hóspede.
- **FR-032**: Interpretação da resposta MUST ser possível sem o serviço
  real de classificação: nota, comentário, aceite, recusa, silêncio
  parcial e irreconhecível controlados devolvem desfechos previsíveis,
  sem rede.

### Key Entities

- **Confirmação de saída**: clique da recepção que encerra a reserva
  hospedada, grava o instante real da partida e dispara a pesquisa. Única
  travessia para encerrado.
- **Pesquisa de saída**: uma mensagem curta por reserva encerrada — nota
  de 1 a 5, comentário opcional e pergunta final de comunicações futuras.
  Sem oferta, sem lista de pedidos, sem lembrete.
- **Avaliação de saída**: registro da resposta à pesquisa, distinto da
  avaliação do pulso do segundo dia; no máximo um por reserva nesta origem.
- **Consentimento**: histórico append-only por titular e finalidade
  (comunicações futuras). Cada evento tem valor (concedido ou recusado),
  instante e origem (pesquisa de saída, painel ou pedido do titular). O
  estado vigente numa data é o evento mais recente até aquele instante;
  sem evento, não concedido.
- **Saída não confirmada**: indicação na fila do dia de que a data prevista
  de saída já passou e a reserva ainda está hospedada.
- **Prazo de atribuição da propriedade**: janela, contada do instante real
  da saída, durante a qual uma mensagem do hóspede ainda pode completar a
  pesquisa. Semeado na instalação; ausência impede a atribuição automática.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das confirmações de saída de reserva hospedada da
  própria propriedade, a reserva fica encerrada com o instante real da
  partida gravado, e o hóspede fica com exatamente 1 pesquisa de saída
  pendente ou enviada.
- **SC-002**: Em 100% das tentativas de confirmar saída de reserva ainda
  não hospedada, já encerrada ou cancelada, a operação é recusada, o
  status não muda e 0 pesquisas nascem.
- **SC-003**: Em verificação com envio falho, 100% das reservas
  permanecem encerradas e o hóspede recebe no máximo 1 pesquisa lógica
  (a mesma, retomada) — 0 desfazimentos, 0 pesquisas distintas extras.
- **SC-004**: Em 100% das reservas hospedadas com data prevista de saída
  anterior ao dia corrente, a consulta da fila do dia as apresenta com o
  destaque de saída não confirmada; após a confirmação, 0% delas
  permanecem com esse destaque.
- **SC-005**: Reserva com saída prevista no dia corrente: 0% recebe o
  destaque de vencida antes da meia-noite daquele dia.
- **SC-006**: Em 100% das respostas completas reconhecidas (nota + aceite
  explícito), existem uma avaliação de saída e um registro de
  consentimento com instante e origem; 0 registros anteriores são
  apagados ou editados.
- **SC-007**: Em 100% dos silêncios e das respostas sem a pergunta de
  aceite, 0 consentimentos são criados; a consulta do estado vigente
  devolve não concedido.
- **SC-008**: Dado um aceite e uma revogação posterior, 100% das
  consultas a uma data entre os dois eventos devolvem aceite, e 100% das
  consultas após a revogação devolvem recusa; o registro do aceite
  permanece.
- **SC-009**: Em 100% dos textos da pesquisa e das telas desta fatia, as
  palavras "extrato" e "conta" não aparecem; 0 pesquisas incluem oferta
  de retorno ou lista de pedidos feitos pelo chat.
- **SC-010**: Em verificação com dois hotéis, 100% das tentativas de
  confirmar reserva alheia são recusadas; 0 reservas do hotel A mudam de
  status por sessão do hotel B.
- **SC-011**: Em verificação com sessão de gestão e com sessão
  operacional, 100% das tentativas de confirmar saída são recusadas.
- **SC-012**: A recepção conclui a confirmação de uma saída elegível em
  uma única interação, sem etapas intermediárias obrigatórias no painel.
- **SC-013**: Hóspede consegue responder a pesquisa com três partes (nota,
  comentário opcional, aceite) em uma única troca, compatível com o tempo
  de quem já saiu do balcão.
- **SC-014**: Em 100% dos casos de interpretação irreconhecível ou
  serviço indisponível, a mensagem é preservada, a recepção é sinalizada
  e 0 notas ou consentimentos são inventados.
- **SC-015**: O caminho confirmação → encerrado → pesquisa (sucesso e
  falha) é verificável de ponta a ponta sem chamada à rede do provedor
  real de mensagens e sem tela visual nova.

## Assumptions

- As fatias até F3.8 estão concluídas. Esta fatia dispara o clique de
  checkout que a chegada (F2.2) deixou possível e reutiliza fila do dia,
  envio durável, recebimento de mensagem e interpretação já existentes.
  Não inventa canal de entrega nem mecanismo de processamento novo.
- A máquina de estados já vigente é a fonte da elegibilidade: para
  encerrado somente a partir de hospedado. O critério do backlog
  (“confirmação só é possível para reserva com entrada já confirmada”) é
  exatamente essa transição.
- O destaque de chegada não confirmada e o de boas-vindas não enviadas já
  existem na fila. Esta fatia acrescenta o de saída vencida, distinguível
  dos outros, e o desliga na confirmação.
- **Independência estrutural (já decidida):** o envio não roda dentro da
  operação que confirma o clique. A confirmação registra a intenção de
  envio de forma durável e um processamento posterior entrega.
- **Porta de mensageria (já decidida):** todo envio passa pela interface
  substituível; testes usam implementação falsa; nenhum teste chama o
  provedor real.
- **Unicidade no armazenamento (já decidida):** “exatamente uma pesquisa
  por reserva” é garantia de unicidade, no mesmo padrão do recado de
  chegada. Conferência prévia em código não satisfaz FR-008.
- A pesquisa é **uma** mensagem com três partes, no padrão da coleta de
  ficha (lista numerada). Formulário nativo do canal fica fora. Não há
  conversa de várias perguntas encadeadas pelo hotel — o hóspede pode
  responder tudo de uma vez ou completar o que faltou dentro da janela,
  sem o sistema cobrar de novo.
- Comentário é opcional. Nota e aceite são as duas partes que fecham a
  pesquisa. Aceite só existe quando o hóspede responde sim ou não à
  pergunta final; nota alta não vira opt-in.
- Avaliação de saída é distinta da de pulso. Pulso pode ter nota vazia;
  saída pede nota de 1 a 5. As duas convivem.
- Consentimento é do titular da reserva, finalidade única nesta fatia
  (comunicações futuras). Nunca se atualiza uma linha: revogação e novo
  aceite são inserções. Origens previstas: pesquisa de saída, painel e
  pedido do titular.
- Revogação posterior, nesta fatia, é registrada no painel pela recepção
  ou pela gestão (o hóspede não opera o painel). Pedido feito depois pelo
  mesmo canal da conversa, se não for mais atribuível à pesquisa, vai
  para leitura humana — a recepção registra a revogação. Não nasce um
  fluxo automático de descadastro após a estadia; o silêncio depois da
  pesquisa é a experiência esperada.
- **Prazo de atribuição:** a janela em que uma mensagem ainda completa a
  pesquisa vive na configuração da propriedade, semeada na instalação com
  24 horas a partir do instante real da saída. Não é constante de regra.
  Ausência da chave impede atribuir resposta automaticamente.
- Chamado aberto e consumo pendente não travam o checkout. Travar
  misturaria a travessia do balcão com a fila de lançamento e com o Alert
  Center, que já são visíveis por outros caminhos.
- A lista de pedidos feitos pelo chat é a fatia F4.2 e **não** entra no
  recado desta fatia, mesmo a jornada citando os dois no mesmo momento do
  checkout. Misturar agora reintroduziria o atrito que a nomenclatura
  existe para evitar.
- Oferta de retorno permanece fora do produto. A pergunta de aceite é a
  substituta deliberada.
- Superfície de uso: operação de confirmação, destaque na fila do dia,
  interpretação da resposta, consulta e revogação de consentimento. Ligar
  o protótipo React continua fora do critério de pronto, no mesmo padrão
  das fatias anteriores.
- Inferência por mensagem (“já fiz checkout”) e confirmação em lote
  ficam fora — esta fatia entrega a detecção de divergência temporal na
  fila, que já é o máximo exigido pelo backlog.
- Isolamento por propriedade vale mesmo com uma única propriedade
  cadastrada.
- Permissão de confirmar fase da reserva já existe para a recepção desde
  a autenticação; esta fatia é a primeira a usá-la na transição para
  encerrado, como a chegada foi a primeira a usá-la para hospedado.
- Gestão consulta consentimento e pode registrar revogação (accountability
  LGPD); não confirma saída no balcão.
- Conteúdo de mensagem nunca vai para log.
