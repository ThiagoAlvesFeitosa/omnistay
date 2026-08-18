# Feature Specification: Abrir Chamado de Reclamação

**Feature Branch**: `014-abrir-chamado-reclamacao`

**Created**: 2026-08-18

**Status**: Draft

**Input**: User description: "Reclamações técnicas com sentimento negativo geram chamado
para a equipe operacional. Antes de qualquer tramitação, o hóspede recebe confirmação
de que a mensagem foi recebida e de que a manutenção está sendo acionada, e é
perguntado sobre o horário de sua preferência para o atendimento. O chamado registra
quarto, tipo, urgência e a janela informada."
(backlog F3.5)

Restrições já decididas no projeto (entrada do specify): o hóspede nunca fica esperando
em silêncio — toda reclamação recebe confirmação de recebimento **antes** de qualquer
tramitação; gravar a mensagem de saída antes de enviá-la; a fila do painel (Alert
Center) é a fonte da verdade e a notificação é conveniência; conteúdo de mensagem nunca
vai para log; o sistema não se integra ao sistema de gestão do hotel e portanto não
inventaria quarto; prazo de “tempo excessivo” não é número mágico — vem da configuração
da propriedade. Marcar o chamado como resolvido e avisar o hóspede da conclusão
pertencem à fatia seguinte. Consumo faturável e pulso do segundo dia também.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reclamação técnica vira chamado e o hóspede é confirmado (Priority: P1)

Como hóspede já hospedado que relata um problema técnico (ar-condicionado que não gela,
vazamento, lâmpada queimada), quero confirmação imediata de que a mensagem foi recebida
e de que a manutenção está sendo acionada, e quero que a equipe operacional veja o
chamado com o que aconteceu, o quarto quando eu o informei, a urgência e o horário que
eu preferir para o atendimento — para eu não ligar para a recepção nem concluir que o
recado se perdeu.

**Why this priority**: É o momento em que o produto se prova ou se desmoraliza. Sem
confirmação, o hóspede irritado espera em silêncio e liga para o balcão. Sem chamado
estruturado, a manutenção não tem quarto, urgência nem preferência de horário.

**Independent Test**: Pode ser testado partindo de uma mensagem já classificada como
reclamação técnica, verificando: confirmação ao hóspede de recebimento e de acionamento
da manutenção, pergunta pelo horário de preferência quando ele ainda não foi informado,
exatamente um chamado do tipo reclamação vinculado àquela mensagem, com descrição,
urgência, quarto quando informado e janela quando informada, visível no Alert Center da
propriedade — e nenhum valor a cobrar.

**Acceptance Scenarios**:

1. **Given** uma mensagem de estadia já classificada como reclamação técnica (por
   exemplo, ar-condicionado que não gela), **When** o sistema abre o chamado, **Then**
   nasce uma solicitação do tipo reclamação, vinculada à reserva e à mensagem de
   origem, com a descrição do problema e com a urgência já registrada na classificação.
2. **Given** o desfecho do cenário anterior, **When** o hóspede consulta a conversa,
   **Then** há uma confirmação de que a mensagem foi recebida e de que a manutenção
   está sendo acionada, gravada no histórico da mesma reserva — e essa confirmação não
   promete prazo de conserto nem afirma fato da casa que não foi cadastrado.
3. **Given** o mesmo chamado, **When** se observa cobrança, **Then** a solicitação não
   tem valor a cobrar e não entra em fila de lançamento no sistema de gestão do hotel.

---

### User Story 2 - A confirmação chega antes de a equipe ver o chamado (Priority: P1)

Como hóspede, quero saber que o recado foi recebido e que a manutenção está sendo
acionada **antes** de o chamado tramitar como pendência da equipe, para eu não ficar no
silêncio enquanto alguém decide o que fazer.

**Why this priority**: Confirmação antes de tramitação é regra do produto, não cortesia.
Confirmar depois (ou só internamente) reproduz o telefone que ninguém atende — exatamente
o que a jornada de atrito quer evitar.

**Independent Test**: Pode ser testado observando a ordem no caminho feliz: a
confirmação já está no histórico da conversa no instante em que o chamado passa a
existir como pendência visível no Alert Center.

**Acceptance Scenarios**:

1. **Given** uma reclamação técnica classificada, **When** a abertura conclui, **Then**
   a confirmação ao hóspede precede a tramitação do chamado como pendência da equipe —
   zero reclamações tramitam em silêncio.
2. **Given** a confirmação do cenário 1, **When** se lê o texto enviado, **Then** é
   recado de recebimento e de acionamento da manutenção, não um compromisso de horário
   de chegada da equipe nem uma resposta inventada sobre a casa.

---

### User Story 3 - A equipe vê o chamado no Alert Center, sem ficha cadastral (Priority: P1)

Como profissional da equipe operacional (manutenção, governança), quero ver os chamados
de reclamação abertos da minha propriedade — o problema, o quarto quando conhecido, a
urgência, a janela de preferência quando informada e desde quando está aberto — sem
acessar nome, telefone ou documento do hóspede, para eu atender pelo celular sem
carregar dado cadastral num dispositivo de sessão longa.

**Why this priority**: Chamado que só a recepção vê continua sendo o telefone do balcão.
Chamado visível só por notificação some se o aviso não chegar. O Alert Center é o que
torna a omissão perceptível.

**Independent Test**: Pode ser testado com um chamado já aberto, autenticando um
profissional operacional daquela propriedade e verificando o chamado na fila;
autenticando o mesmo perfil e verificando a ausência de dado cadastral; e autenticando
um profissional de outra propriedade e verificando que o chamado não aparece.

**Acceptance Scenarios**:

1. **Given** um chamado de reclamação aberto na propriedade, **When** um profissional
   operacional daquela propriedade consulta o Alert Center, **Then** o chamado aparece
   com tipo reclamação, descrição, urgência, instante de abertura, quarto quando
   conhecido e janela de preferência quando informada — inclusive se ainda ninguém o
   tiver assumido.
2. **Given** a mesma consulta, **When** se observa o que o profissional operacional
   alcança, **Then** não há nome completo, telefone, documento, endereço nem demais
   dados da ficha do hóspede.
3. **Given** o mesmo chamado, **When** a recepção da propriedade consulta, **Then** a
   solicitação também é recuperável no painel — a fila não depende de uma notificação
   ter chegado a alguém.
4. **Given** um chamado da propriedade A, **When** um profissional da propriedade B
   consulta o Alert Center, **Then** esse chamado não aparece e a consulta não revela
   que ele existe.

---

### User Story 4 - Horário de preferência é pedido e registrado, sem atrasar o chamado (Priority: P1)

Como hóspede, quero ser perguntado qual horário prefiro para o atendimento quando ainda
não disse, e quero que esse horário apareça no chamado da equipe. Como hotel, quero que
a ausência dessa resposta **não** esconda o chamado nem deixe o hóspede sem confirmação:
a manutenção precisa ver o problema agora; o horário, quando vier, completa o mesmo
chamado.

**Why this priority**: Perguntar o horário transforma incômodo em sensação de controle.
Esperar a resposta para abrir o chamado reproduz o silêncio e perde o recado se o
hóspede não responder. Inventar um horário é o mesmo defeito de inventar o quarto.

**Independent Test**: Pode ser testado (a) com reclamação que já cita horário, (b) com
reclamação que não cita, e (c) com a janela informada depois da abertura, verificando
confirmação, pergunta só quando a janela ainda é desconhecida, um único chamado e a
janela visível no Alert Center quando informada.

**Acceptance Scenarios**:

1. **Given** uma reclamação técnica classificada em que o hóspede **não** informou
   horário de preferência, **When** o sistema confirma, **Then** o recado pergunta o
   horário de preferência para o atendimento, o chamado nasce mesmo assim, e nenhuma
   janela é inventada.
2. **Given** uma reclamação técnica classificada em que o hóspede **já** informou o
   horário na própria mensagem, **When** o sistema confirma, **Then** o chamado registra
   essa janela, o recado **não** pergunta de novo o horário, e a equipe vê a janela no
   Alert Center.
3. **Given** um chamado já aberto sem janela, **When** o hóspede informa o horário em
   seguida, **Then** a janela passa a constar **naquele** chamado, nenhum segundo
   chamado nasce dessa resposta de horário, e o hóspede não recebe uma segunda
   confirmação de que a manutenção está sendo acionada.
4. **Given** um chamado aberto sem janela e o hóspede em silêncio sobre o horário,
   **When** a equipe consulta o Alert Center, **Then** o chamado permanece visível como
   pendência sem janela — não some por estar incompleto.

---

### User Story 5 - Reclamação sem quarto informado ainda é confirmada e não inventa quarto (Priority: P1)

Como hotel, quero que a ausência do número do quarto na mensagem não faça o sistema
adivinhar um quarto que só existe no sistema de gestão da casa, nem descarte o chamado:
o hóspede é confirmado, o chamado nasce, e a falta do quarto fica visível no Alert
Center, para a equipe localizar o hóspede pelos meios que o hotel já usa.

**Why this priority**: O sistema não consulta inventário de quartos. Inventar o 402
porque “parece o caso” é o mesmo defeito de afirmar horário de café que não está no
catálogo. Esconder o chamado até alguém digitar o quarto deixa o hóspede no silêncio.

**Independent Test**: Pode ser testado com reclamação técnica classificada cuja
mensagem não cita quarto, verificando confirmação, chamado do tipo reclamação sem
quarto inventado, e visibilidade da pendência no Alert Center.

**Acceptance Scenarios**:

1. **Given** uma reclamação técnica classificada em que o hóspede não informou o quarto,
   **When** o sistema abre o chamado, **Then** a solicitação nasce mesmo assim, a
   confirmação é enviada, e nenhum número de quarto é atribuído por conta própria.
2. **Given** o desfecho anterior, **When** a equipe consulta o Alert Center, **Then** o
   chamado aparece como pendência sem quarto, perceptível — não some da fila por estar
   incompleto.

---

### User Story 6 - Chamado aberto há tempo excessivo é destacado (Priority: P1)

Como profissional da equipe operacional e como recepção na passagem de turno, quero
que um chamado de reclamação ainda aberto além do prazo da propriedade apareça
destacado no Alert Center, para a omissão não se misturar aos recados recém-chegados.

**Why this priority**: Chamado antigo sem destaque falha em silêncio no mesmo sentido
em que reserva sem check-in some na fila do dia. O prazo é da propriedade, não um
número fixo do produto.

**Independent Test**: Pode ser testado com um chamado aberto há menos tempo que o
prazo da propriedade (sem destaque) e outro aberto além desse prazo (com destaque);
e com propriedade sem o prazo configurado, verificando que nenhum prazo é suposto e
que a ausência fica perceptível na operação — não se inventa um limite.

**Acceptance Scenarios**:

1. **Given** um chamado de reclamação aberto além do prazo configurado da propriedade,
   **When** a equipe consulta o Alert Center, **Then** esse chamado aparece destacado
   em relação aos que ainda estão dentro do prazo.
2. **Given** um chamado aberto há menos tempo que o prazo da propriedade, **When** a
   equipe consulta, **Then** esse chamado aparece na fila **sem** o destaque de tempo
   excessivo.
3. **Given** a propriedade sem o prazo de destaque configurado, **When** a equipe
   consulta, **Then** nenhum chamado é destacado por tempo excessivo com um limite
   inventado, e a ausência do prazo fica registrada de forma operacional (sem texto
   da conversa).

---

### User Story 7 - Reprocessar a mesma reclamação não duplica confirmação nem chamado (Priority: P1)

Como hotel e como hóspede, quero que a mesma mensagem classificada como reclamação
técnica gere no máximo uma confirmação e um chamado, para um retrabalho ou uma
reinicialização não acionar a manutenção duas vezes nem mandar duas mensagens.

**Why this priority**: Idempotência visível ao hóspede e à equipe. Sem ela, o caminho
feliz é frágil no segundo processamento.

**Independent Test**: Pode ser testado concluindo a abertura uma vez e disparando o
mesmo trabalho de novo, verificando zero segunda confirmação e zero segundo chamado
para aquela mensagem.

**Acceptance Scenarios**:

1. **Given** uma mensagem cuja reclamação já foi confirmada e virou chamado, **When**
   o mesmo trabalho é processado outra vez, **Then** o hóspede não recebe segunda
   confirmação e a equipe não vê segundo chamado daquela origem.
2. **Given** uma falha depois de gravar e antes de concluir o envio, **When** o
   trabalho é retomado, **Then** o chamado permanece único e o envio pendente é
   retomado — não se cria outra reclamação.

---

### User Story 8 - Falha ao gravar ou ao enviar não perde o chamado (Priority: P1)

Como hóspede e como hotel, quero que uma falha no envio da confirmação não apague o
chamado, e que uma falha ao gravar não envie recado sobre uma reclamação que não
existe, para “gravar antes de enviar” valer também neste ramo.

**Why this priority**: Sem este caminho, a fatia só funciona no dia em que a
mensageria está no ar. Chamado perdido é pior do que confirmação atrasada.

**Independent Test**: Pode ser testado (a) gravando com sucesso e falhando o envio, e
(b) falhando a gravação, verificando preservação do chamado no primeiro caso,
ausência de envio no segundo, e trabalho recuperável nos dois.

**Acceptance Scenarios**:

1. **Given** confirmação e chamado já gravados e o envio ao hóspede falhando, **When**
   o sistema trata a falha, **Then** o chamado permanece no Alert Center, a
   confirmação permanece no histórico, e o envio fica recuperável — nenhum dos dois
   some.
2. **Given** a gravação da confirmação ou do chamado falhando, **When** se observa o
   canal do hóspede, **Then** nenhum recado de manutenção acionada é enviado, a
   mensagem original permanece, e o trabalho continua pendente de novo processamento.

---

### User Story 9 - Conteúdo da mensagem não vaza em log (Priority: P2)

Como titular dos dados e responsável pelo hotel, quero que o texto da reclamação, o
texto da confirmação e o horário informado nunca apareçam em log operacional, para um
arquivo técnico não virar cópia da conversa.

**Why this priority**: Minimização de dados pessoais continua valendo neste passo. O
log pode registrar identificadores, a propriedade, o tipo reclamação e o resultado; o
texto não.

**Independent Test**: Pode ser testado nos desfechos feliz, reprocessamento, destaque
por tempo e falha de envio, inspecionando os logs: há identificadores e resultado;
não há o texto do hóspede nem o da confirmação.

**Acceptance Scenarios**:

1. **Given** um chamado aberto e confirmado com sucesso, **When** o sistema registra
   log operacional, **Then** aparecem identificadores, a propriedade e a indicação de
   reclamação registrada — e não o conteúdo da reclamação, o da confirmação nem a
   janela em texto livre.
2. **Given** falha de envio, reprocessamento ou ausência de prazo de destaque, **When**
   o sistema registra log operacional, **Then** há código de resultado e
   identificadores, sem o texto.

---

### Edge Cases

- Somente mensagem já classificada como reclamação técnica entra nesta fatia. Dúvida
  geral, pedido de serviço, interesse comercial, pedido de checkout e fora de escopo
  não geram chamado de reclamação aqui.
- Reclamação técnica gera chamado **mesmo quando o sentimento não é negativo** (neutro
  ou positivo). O caso típico da jornada é o sentimento negativo; filtrar só ele
  deixaria um vazamento relatado com educação sem manutenção. Sentimento e urgência
  já gravados na classificação não são reclassificados aqui.
- O quarto do chamado é o número que o hóspede informou na mensagem, em texto livre.
  O sistema não consulta o sistema de gestão do hotel e não completa o quarto a
  partir de um inventário que não possui. Mensagem sem quarto: User Story 5.
- A urgência do chamado é a já gravada na classificação da mensagem. Esta fatia não
  reclassifica.
- A descrição do chamado reflete o relato do hóspede; não é reescrita com
  conhecimento geral sobre o hotel nem convertida numa taxonomia de manutenção
  (elétrica, hidráulica etc.) que o produto não cadastrou.
- A confirmação é recado padrão: recebimento + manutenção acionada. Não promete
  prazo de conserto, não cita cardápio, horário de funcionamento nem regra da casa.
  Pergunta o horário de preferência **somente** quando a janela ainda é desconhecida.
- O chamado desta fatia nasce aberto, do tipo reclamação, sem responsável atribuído,
  sem valor e sem status de lançamento. Não é pedido de serviço e não é consumo.
- Este chamado **não** reutiliza o sinal de “precisa de atendimento humano” da fila
  do dia (usado quando a classificação falha ou a dúvida não está no catálogo).
  Reclamação técnica é trabalho da equipe operacional no Alert Center, não recado da
  recepção para “uma pessoa ver o chat”.
- Marcar como resolvido, atribuir responsável e avisar o hóspede da conclusão estão
  fora desta fatia.
- Perfil operacional vê o Alert Center da propriedade; não vê ficha cadastral. Gestão
  também não vê ficha cadastral. Recepção vê o chamado e continua sendo quem vê dado
  cadastral quando precisar localizar o hóspede sem quarto.
- Hotel A não registra chamado na conversa do hotel B e não exibe o Alert Center do
  hotel B.
- Reprocessar depois de falha de envio não cria segundo chamado (User Story 7).
- Informar o horário depois da abertura atualiza o mesmo chamado; não abre outro e
  não dispara nova confirmação de acionamento.
- Uma mensagem posterior que relata **outro** problema técnico (já classificada como
  nova reclamação) gera um chamado próprio, vinculado àquela nova origem — não se
  mistura com a janela do chamado anterior.
- O prazo de destaque por tempo excessivo vem da configuração da propriedade. Sem o
  prazo, nenhum limite é inventado.
- Esta fatia **não** classifica intenção, **não** responde dúvida pelo catálogo,
  **não** registra pedido de serviço, **não** registra consumo, **não** altera o
  status da reserva e **não** dispara pulso, coleta nem lembrete. Existir chamado
  aberto nesta fatia é o insumo da supressão do pulso na fatia correspondente; esta
  entrega só garante que o chamado exista.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST registrar mensagem de estadia já classificada como
  reclamação técnica como uma solicitação do tipo reclamação, vinculada à reserva e
  à mensagem de origem, com descrição do problema relatado.
- **FR-002**: A solicitação MUST registrar o quarto informado na mensagem do hóspede,
  quando houver. MUST NOT atribuir número de quarto a partir de inventário, de outra
  reserva, de outro hotel ou de suposição. Ausência de quarto MUST NOT impedir o
  registro nem a confirmação.
- **FR-003**: A solicitação de reclamação MUST NOT ter valor a cobrar e MUST NOT
  nascer pendente de lançamento no sistema de gestão do hotel.
- **FR-004**: O hóspede MUST receber confirmação de que a mensagem foi recebida e de
  que a manutenção está sendo acionada. A confirmação MUST ser recado padrão —
  MUST NOT prometer prazo de conserto e MUST NOT afirmar fato da casa.
- **FR-005**: A confirmação ao hóspede MUST ocorrer antes de o chamado existir como
  pendência tramitada da equipe operacional.
- **FR-006**: A confirmação MUST ficar gravada no histórico da conversa da reserva
  antes de ser enviada ao hóspede.
- **FR-007**: Quando o hóspede ainda não informou horário de preferência, o recado de
  confirmação MUST perguntar esse horário. Quando o horário já constar da mensagem
  de origem, o recado MUST NOT perguntar de novo, e o chamado MUST registrar a
  janela informada.
- **FR-008**: Ausência de janela de preferência MUST NOT impedir a confirmação nem a
  abertura do chamado. MUST NOT inventar horário. O chamado MUST permanecer visível
  no Alert Center sem janela.
- **FR-009**: Quando o hóspede informar o horário depois da abertura, o sistema MUST
  registrar essa janela no chamado já existente daquela reclamação. MUST NOT abrir
  segundo chamado por causa dessa resposta de horário e MUST NOT reenviar a
  confirmação de que a manutenção está sendo acionada.
- **FR-010**: O chamado MUST aparecer no Alert Center da propriedade da reserva,
  recuperável pela leitura do painel, inclusive sem responsável atribuído. MUST NOT
  depender de uma notificação ter chegado a alguém.
- **FR-011**: Profissional operacional e gestão MUST conseguir consultar o Alert
  Center da própria propriedade. MUST NOT alcançar nome, telefone, documento,
  endereço nem demais dados da ficha cadastral do hóspede.
- **FR-012**: Recepção da propriedade MUST também recuperar o chamado no painel.
- **FR-013**: Chamado de reclamação aberto além do prazo configurado da propriedade
  MUST aparecer destacado no Alert Center. Chamado ainda dentro do prazo MUST NOT
  receber esse destaque. Se o prazo não estiver configurado, o sistema MUST NOT
  inventar um limite e MUST registrar a ausência de forma operacional, sem conteúdo
  da conversa.
- **FR-014**: Esta fatia MUST NOT registrar chamado de reclamação para intenção
  diferente de reclamação técnica. MUST registrar o chamado para reclamação técnica
  independentemente de o sentimento ser negativo, neutro ou positivo.
- **FR-015**: Reprocessar mensagem cuja reclamação já foi registrada MUST NOT
  produzir segunda confirmação nem segundo chamado daquela origem.
- **FR-016**: Se gravar a confirmação ou o chamado falhar, a mensagem original MUST
  permanecer, o trabalho MUST continuar recuperável, e MUST NOT enviar ao hóspede
  recado de manutenção acionada que ainda não foi gravado.
- **FR-017**: Se o envio da confirmação falhar depois de gravar, o chamado e a
  confirmação gravada MUST permanecer; o envio MUST continuar recuperável.
- **FR-018**: Conteúdo da reclamação, conteúdo da confirmação, janela em texto livre
  e demais dados pessoais NUNCA MUST aparecer em log operacional; logs registram
  identificadores, a propriedade e o resultado — nunca o texto.
- **FR-019**: Resolução MUST considerar a propriedade da reserva; chamado,
  confirmação e Alert Center de um hotel MUST NOT vazar para o histórico ou a fila
  de outro.
- **FR-020**: Esta fatia MUST NOT alterar o status da reserva, MUST NOT confirmar
  chegada ou saída, MUST NOT responder dúvida pelo catálogo, MUST NOT registrar
  pedido de serviço, MUST NOT registrar consumo, MUST NOT marcar solicitação como
  resolvida e MUST NOT disparar coleta, lembrete, pulso ou pesquisa.
- **FR-021**: A urgência da solicitação MUST ser a já registrada na classificação da
  mensagem; esta fatia MUST NOT reclassificar intenção, sentimento ou urgência.
- **FR-022**: Chamado desta fatia MUST NOT ser confundido com o sinal de atendimento
  humano da fila do dia. A pendência visível à equipe operacional é o próprio
  chamado no Alert Center.
- **FR-023**: A verificação desta fatia MUST ser possível sem o serviço real de
  mensageria: um envio controlado devolve sucesso ou falha previsíveis, sem rede.

### Key Entities

- **Reclamação técnica classificada**: mensagem de estadia já marcada com a intenção
  “reclamação técnica”, com sentimento e urgência já gravados. É o único insumo que
  abre chamado nesta fatia.
- **Chamado (solicitação do tipo reclamação)**: ocorrência operacional para a
  manutenção, com descrição, quarto quando informado, urgência herdada da
  classificação, janela de preferência quando informada, status aberto e vínculo com
  a reserva e a mensagem de origem. Não é pedido de serviço e não é consumo.
- **Confirmação de recebimento**: recado padrão ao hóspede de que a mensagem foi
  recebida e de que a manutenção está sendo acionada, gravado no histórico da
  conversa e então enviado, antes da tramitação. Inclui a pergunta pelo horário de
  preferência somente quando a janela ainda é desconhecida.
- **Janela de preferência**: horário informado pelo hóspede para o atendimento, em
  texto curto. Completa o chamado; não é pré-requisito para abri-lo.
- **Alert Center**: lista recuperável no painel dos chamados abertos da propriedade,
  visível à equipe operacional, à recepção e à gestão daquele hotel, sem dado
  cadastral para quem não tem permissão de ficha. Fonte da verdade; a notificação, se
  existir no futuro, é conveniência. Destaca chamado aberto além do prazo da
  propriedade.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das mensagens classificadas como reclamação técnica, o hóspede
  recebe uma confirmação de recebimento com acionamento da manutenção e nasce
  exatamente 1 chamado do tipo reclamação vinculado àquela mensagem.
- **SC-002**: Em 100% desses registros, a confirmação ao hóspede precede a tramitação
  do chamado como pendência da equipe; 0 tramitam em silêncio.
- **SC-003**: Em 100% das reclamações em que o hóspede ainda não informou horário, o
  recado pergunta a preferência e o chamado nasce mesmo assim, com 0 janelas
  inventadas. Em 100% das que já informaram o horário na origem, a janela aparece no
  chamado e 0 perguntas repetidas são enviadas.
- **SC-004**: Informar o horário depois da abertura atualiza aquele chamado em 100%
  dos casos e produz 0 segundos chamados e 0 segundas confirmações de acionamento.
- **SC-005**: Em 100% dos chamados em que o hóspede informou o quarto, a solicitação
  exibe esse quarto; em 100% dos que não informou, 0 quartos são inventados e a
  pendência permanece visível no Alert Center.
- **SC-006**: Em 100% das solicitações desta fatia, há 0 valores a cobrar e 0 itens em
  fila de lançamento no sistema de gestão do hotel.
- **SC-007**: Em verificação com dois hotéis, 0% dos chamados ou confirmações de um
  hotel aparecem no Alert Center ou no histórico do outro.
- **SC-008**: Em 100% das consultas da equipe operacional ao Alert Center, o chamado
  aberto da própria propriedade é recuperável e 0 dados da ficha cadastral do hóspede
  são expostos a esse perfil.
- **SC-009**: Chamado aberto além do prazo da propriedade é destacado em 100% das
  consultas ao Alert Center; chamado dentro do prazo recebe esse destaque em 0% das
  consultas. Propriedade sem o prazo configurado destaca 0 chamados com limite
  inventado.
- **SC-010**: Reprocessar a mesma mensagem já concluída produz 0 segundas
  confirmações e 0 segundos chamados.
- **SC-011**: Em 100% das falhas de envio após gravação, o chamado permanece no Alert
  Center e a confirmação permanece no histórico; em 100% das falhas de gravação, 0
  recados são enviados ao hóspede.
- **SC-012**: Em 100% dos desfechos, logs operacionais não contêm o conteúdo da
  reclamação, o da confirmação nem a janela em texto livre.
- **SC-013**: O caminho reclamação classificada → confirmação + chamado no Alert
  Center é verificável de ponta a ponta sem o serviço real de envio de mensagem.

## Assumptions

- A fatia F3.2 (classificar a intenção) está concluída. Esta fatia parte de mensagem
  já classificada como reclamação técnica, com sentimento e urgência já gravados.
- A fatia F3.4 (registrar pedido de serviço) está concluída. O Alert Center desta
  entrega é a mesma fila de solicitações abertas da propriedade, agora também com o
  tipo reclamação — não uma fila paralela. Pedido de serviço continua sem ser
  chamado de manutenção.
- Toda `reclamação técnica` classificada gera chamado, inclusive com sentimento
  neutro ou positivo. O enunciado do backlog usa “sentimento negativo” como o caso
  típico da jornada de atrito, não como filtro que descarta relato educado.
- A estadia não guarda inventário de quartos: o número vive no sistema de gestão do
  hotel, fora do alcance deste produto. O quarto no chamado é texto informado pelo
  hóspede, quando houver.
- A janela de preferência é texto curto informado pelo hóspede, não um horário
  estruturado contra a agenda da manutenção. O sistema não consulta disponibilidade
  da equipe.
- Confirmação e pergunta de horário cabem no mesmo recado quando a janela ainda é
  desconhecida, para não ser intrusivo com duas mensagens seguidas. Quando a janela
  já veio na origem, o recado só confirma.
- Esperar a resposta do horário para abrir o chamado está fora desta fatia: perderia
  o recado se o hóspede não respondesse e deixaria o hóspede no silêncio. O chamado
  abre na confirmação; a janela completa depois, no mesmo registro.
- Resposta que só informa o horário preenche o chamado já aberto. Mensagem posterior
  classificada como **nova** reclamação técnica (outro problema) abre chamado próprio,
  vinculado à nova origem.
- O prazo a partir do qual o chamado aberto é destacado é configuração da
  propriedade (no mesmo mecanismo já usado para os demais prazos operacionais),
  semeado na instalação. Sem o valor, nenhum limite é suposto. A recepção **não**
  altera esse prazo — é parâmetro de comportamento, não texto de balcão.
- Marcar o chamado como resolvido e avisar o hóspede da conclusão são a fatia de
  resolver chamado (F3.6). Esta fatia só confirma, pergunta o horário e abre.
- A dúvida não coberta pelo catálogo (F3.3) continua sendo sinal na fila do dia da
  recepção, **não** um chamado de reclamação desta fatia. Não se unifica os dois.
- Superfície de uso: comportamento observável no histórico da conversa, na
  confirmação recebida pelo hóspede, e no Alert Center visível à equipe operacional,
  à recepção e à gestão da propriedade. Ligar telas do painel visual de protótipo
  continua fora do critério de pronto.
- A verificação usa envio controlado (sucesso ou falha) e nunca chama o serviço real
  de mensageria.
- Ordem entre mensagens consecutivas não é garantida. Cada reclamação de origem é
  tratada isoladamente.
- O hóspede acabou de escrever, então a confirmação ocorre dentro da janela de
  conversa já aberta; não se inicia conversa proativa nova.
- A operação de ler solicitação já prevista na matriz de perfis (recepção, equipe
  operacional e gestão da propriedade) é a permissão deste Alert Center. Equipe
  operacional e gestão seguem sem leitura de ficha cadastral.
- A palavra "extrato" e a palavra "conta" não aparecem em nenhum texto desta
  funcionalidade.
- Existir chamado aberto nesta fatia é o que a fatia do pulso (F3.8) usará para
  suprimir a pesquisa do segundo dia; esta entrega não dispara nem suprime pulso.
