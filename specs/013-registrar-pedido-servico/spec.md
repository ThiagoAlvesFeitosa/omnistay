# Feature Specification: Registrar Pedido de Serviço

**Feature Branch**: `013-registrar-pedido-servico`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "Pedidos de serviço sem cobrança — toalha, travesseiro,
cobertor — são registrados como tarefa operacional e confirmados ao hóspede
imediatamente. A confirmação acontece antes de qualquer outro processamento."
(backlog F3.4)

Restrições já decididas no projeto (entrada do specify): o hóspede nunca fica esperando
em silêncio — toda solicitação recebe confirmação de recebimento **antes** de qualquer
tramitação; gravar a mensagem de saída antes de enviá-la; a fila do painel é a fonte da
verdade e a notificação é conveniência; conteúdo de mensagem nunca vai para log; o
sistema não se integra ao sistema de gestão do hotel e portanto não inventaria quarto
nem lança cobrança; pedido de serviço operacional não gera valor a cobrar. Reclamação
técnica com janela de preferência, marcar como resolvido e consumo faturável pertencem
às fatias seguintes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pedido sem cobrança vira tarefa e o hóspede é confirmado (Priority: P1)

Como hóspede já hospedado que pede um serviço operacional sem cobrança (toalha extra,
travesseiro, cobertor), quero confirmação imediata de que o pedido foi recebido e quero
que a equipe saiba o que levar e aonde, para eu não ligar para a recepção nem descer ao
balcão, e para o hotel ter prova de que o pedido existiu.

**Why this priority**: É o valor mais frequente da estadia depois da dúvida coberta pelo
catálogo. Sem registro, o pedido some no chat. Sem confirmação, o hóspede conclui que
ninguém viu. Os dois juntos são a fatia.

**Independent Test**: Pode ser testado partindo de uma mensagem já classificada como
pedido de serviço, verificando: confirmação ao hóspede, uma solicitação do tipo serviço
com descrição e quarto quando o hóspede o informou, nenhum valor a cobrar, e a
solicitação visível na fila da equipe operacional daquela propriedade.

**Acceptance Scenarios**:

1. **Given** uma mensagem de estadia já classificada como pedido de serviço (por
   exemplo, toalha extra), **When** o sistema registra o pedido, **Then** nasce uma
   solicitação do tipo serviço, com a descrição do que foi pedido e com o quarto
   informado na mensagem, se houver.
2. **Given** o desfecho do cenário anterior, **When** o hóspede consulta a conversa,
   **Then** há uma confirmação de que o pedido foi recebido, gravada no histórico da
   mesma reserva, e essa confirmação não promete horário, preço nem resolução.
3. **Given** o mesmo pedido, **When** se observa cobrança, **Then** a solicitação não
   tem valor a cobrar e não entra em fila de lançamento no sistema de gestão do hotel.

---

### User Story 2 - A confirmação chega antes de a equipe ver a tarefa (Priority: P1)

Como hóspede, quero saber que o pedido foi recebido **antes** de ele tramitar como
tarefa da equipe, para eu não ficar no silêncio enquanto alguém decide o que fazer.

**Why this priority**: Confirmação antes de tramitação é regra do produto, não cortesia.
Confirmar depois (ou só internamente) reproduz o telefone que ninguém atende.

**Independent Test**: Pode ser testado observando a ordem no caminho feliz: a
confirmação já está no histórico da conversa no instante em que a solicitação passa a
existir como pendência visível à equipe operacional.

**Acceptance Scenarios**:

1. **Given** um pedido de serviço classificado, **When** o registro conclui, **Then** a
   confirmação ao hóspede precede a tramitação da solicitação como pendência da equipe
   — zero pedidos tramitam em silêncio.
2. **Given** a confirmação do cenário 1, **When** se lê o texto enviado, **Then** é
   recado padrão de recebimento, não um compromisso de prazo nem uma resposta inventada
   sobre a casa.

---

### User Story 3 - A equipe operacional vê o pedido na fila, sem ficha cadastral (Priority: P1)

Como profissional da equipe operacional (governança, manutenção), quero ver os pedidos
de serviço abertos da minha propriedade — o que levar, o quarto quando conhecido, a
urgência e desde quando está aberto — sem acessar nome, telefone ou documento do
hóspede, para eu executar a tarefa pelo celular sem carregar dado cadastral num
dispositivo de sessão longa.

**Why this priority**: Pedido que só a recepção vê continua sendo o telefone do balcão.
Pedido visível só por notificação some se o aviso não chegar. A fila do painel é o que
torna a omissão perceptível.

**Independent Test**: Pode ser testado com um pedido já registrado, autenticando um
profissional operacional daquela propriedade e verificando a solicitação aberta na
fila; autenticando o mesmo perfil e verificando a ausência de dado cadastral; e
autenticando um profissional de outra propriedade e verificando que o pedido não
aparece.

**Acceptance Scenarios**:

1. **Given** uma solicitação de serviço aberta na propriedade, **When** um profissional
   operacional daquela propriedade consulta a fila da equipe, **Then** o pedido
   aparece com tipo serviço, descrição, urgência, instante de abertura e quarto quando
   conhecido — inclusive se ainda ninguém o tiver assumido.
2. **Given** a mesma consulta, **When** se observa o que o profissional operacional
   alcança, **Then** não há nome completo, telefone, documento, endereço nem demais
   dados da ficha do hóspede.
3. **Given** o mesmo pedido, **When** a recepção da propriedade consulta, **Then** a
   solicitação também é recuperável no painel — a fila não depende de uma notificação
   ter chegado a alguém.
4. **Given** um pedido da propriedade A, **When** um profissional da propriedade B
   consulta a fila, **Then** esse pedido não aparece e a consulta não revela que ele
   existe.

---

### User Story 4 - Pedido sem quarto informado ainda é confirmado e não inventa quarto (Priority: P1)

Como hotel, quero que a ausência do número do quarto na mensagem não faça o sistema
adivinhar um quarto que só existe no sistema de gestão da casa, nem descarte o pedido:
o hóspede é confirmado, a tarefa nasce, e a falta do quarto fica visível na fila, para
a equipe localizar o hóspede pelos meios que o hotel já usa.

**Why this priority**: O sistema não consulta inventário de quartos. Inventar o 402
porque “parece o caso” é o mesmo defeito de afirmar horário de café que não está no
catálogo. Esconder o pedido até alguém digitar o quarto deixa o hóspede no silêncio.

**Independent Test**: Pode ser testado com pedido de serviço classificado cuja
mensagem não cita quarto, verificando confirmação, solicitação do tipo serviço sem
quarto inventado, e visibilidade da pendência na fila.

**Acceptance Scenarios**:

1. **Given** um pedido de serviço classificado em que o hóspede não informou o quarto,
   **When** o sistema registra, **Then** a solicitação nasce mesmo assim, a confirmação
   é enviada, e nenhum número de quarto é atribuído por conta própria.
2. **Given** o desfecho anterior, **When** a equipe consulta a fila, **Then** o pedido
   aparece como pendência sem quarto, perceptível — não some da fila por estar
   incompleto.

---

### User Story 5 - Reprocessar o mesmo pedido não duplica confirmação nem tarefa (Priority: P1)

Como hotel e como hóspede, quero que a mesma mensagem classificada como pedido de
serviço gere no máximo uma confirmação e uma solicitação, para um retrabalho ou uma
reinicialização não mandar duas toalhas nem duas mensagens.

**Why this priority**: Idempotência visível ao hóspede e à equipe. Sem ela, o caminho
feliz é frágil no segundo processamento.

**Independent Test**: Pode ser testado concluindo o registro uma vez e disparando o
mesmo trabalho de novo, verificando zero segunda confirmação e zero segunda
solicitação para aquela mensagem.

**Acceptance Scenarios**:

1. **Given** uma mensagem cujo pedido de serviço já foi registrado e confirmado,
   **When** o mesmo trabalho é processado outra vez, **Then** o hóspede não recebe
   segunda confirmação e a equipe não vê segunda solicitação daquela origem.
2. **Given** uma falha depois de gravar e antes de concluir o envio, **When** o
   trabalho é retomado, **Then** a solicitação permanece única e o envio pendente é
   retomado — não se cria outro pedido.

---

### User Story 6 - Falha ao gravar ou ao enviar não perde o pedido (Priority: P1)

Como hóspede e como hotel, quero que uma falha no envio da confirmação não apague o
pedido, e que uma falha ao gravar não envie recado sobre um pedido que não existe, para
“gravar antes de enviar” valer também neste ramo.

**Why this priority**: Sem este caminho, a fatia só funciona no dia em que a
mensageria está no ar. Pedido perdido é pior do que confirmação atrasada.

**Independent Test**: Pode ser testado (a) gravando com sucesso e falhando o envio, e
(b) falhando a gravação, verificando preservação do pedido no primeiro caso, ausência
de envio no segundo, e trabalho recuperável nos dois.

**Acceptance Scenarios**:

1. **Given** confirmação e solicitação já gravadas e o envio ao hóspede falhando,
   **When** o sistema trata a falha, **Then** o pedido permanece na fila da equipe, a
   confirmação permanece no histórico, e o envio fica recuperável — nenhum dos dois
   some.
2. **Given** a gravação da confirmação ou da solicitação falhando, **When** se observa
   o canal do hóspede, **Then** nenhum recado de pedido recebido é enviado, a mensagem
   original permanece, e o trabalho continua pendente de novo processamento.

---

### User Story 7 - Conteúdo da mensagem não vaza em log (Priority: P2)

Como titular dos dados e responsável pelo hotel, quero que o texto do pedido e o texto
da confirmação nunca apareçam em log operacional, para um arquivo técnico não virar
cópia da conversa.

**Why this priority**: Minimização de dados pessoais continua valendo neste passo. O
log pode registrar identificadores, a propriedade, o tipo serviço e o resultado; o
texto não.

**Independent Test**: Pode ser testado nos desfechos feliz, reprocessamento e falha de
envio, inspecionando os logs: há identificadores e resultado; não há o texto do hóspede
nem o da confirmação.

**Acceptance Scenarios**:

1. **Given** um pedido registrado e confirmado com sucesso, **When** o sistema
   registra log operacional, **Then** aparecem identificadores, a propriedade e a
   indicação de pedido de serviço registrado — e não o conteúdo do pedido nem o da
   confirmação.
2. **Given** falha de envio ou reprocessamento, **When** o sistema registra log
   operacional, **Then** há código de resultado e identificadores, sem o texto.

---

### Edge Cases

- Somente mensagem já classificada como pedido de serviço entra nesta fatia. Dúvida
  geral, reclamação técnica, interesse comercial, pedido de checkout e fora de escopo
  não geram solicitação de serviço aqui.
- Esta fatia trata todo pedido de serviço classificado como **serviço operacional sem
  cobrança**. Distinguir bar, impressão e lavanderia (consumo com valor) é a fatia de
  consumo faturável; até lá, o sistema não inventa preço nem fila de lançamento.
- O quarto da solicitação é o número que o hóspede informou na mensagem, em texto
  livre. O sistema não consulta o sistema de gestão do hotel e não completa o quarto a
  partir de um inventário que não possui. Mensagem sem quarto: User Story 4.
- A urgência da solicitação é a já gravada na classificação da mensagem. Esta fatia
  não reclassifica.
- A descrição da solicitação reflete o pedido do hóspede; não é reescrita com
  conhecimento geral sobre o hotel.
- A confirmação é recado padrão de recebimento. Não promete prazo de entrega, não cita
  cardápio, horário nem regra da casa, e não pergunta janela de preferência (isso é a
  fatia de reclamação técnica).
- Solicitação desta fatia nasce aberta, do tipo serviço, sem responsável atribuído, sem
  valor e sem status de lançamento.
- Marcar como resolvido, atribuir responsável e avisar o hóspede da conclusão estão
  fora desta fatia.
- Perfil operacional vê a fila de solicitações abertas da propriedade; não vê ficha
  cadastral. Gestão também não vê ficha cadastral. Recepção vê a solicitação e continua
  sendo quem vê dado cadastral quando precisar localizar o hóspede sem quarto.
- Hotel A não registra pedido na conversa do hotel B e não exibe a fila do hotel B.
- Reprocessar depois de falha de envio não cria segunda solicitação (User Story 5).
- Esta fatia **não** classifica intenção, **não** responde dúvida pelo catálogo, **não**
  abre chamado de reclamação técnica, **não** registra consumo, **não** altera o status
  da reserva e **não** dispara pulso, coleta nem lembrete.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST registrar mensagem de estadia já classificada como pedido
  de serviço como uma solicitação do tipo serviço, vinculada à reserva e à mensagem
  de origem, com descrição do que foi pedido.
- **FR-002**: A solicitação MUST registrar o quarto informado na mensagem do hóspede,
  quando houver. MUST NOT atribuir número de quarto a partir de inventário, de outra
  reserva, de outro hotel ou de suposição. Ausência de quarto MUST NOT impedir o
  registro nem a confirmação.
- **FR-003**: A solicitação de serviço MUST NOT ter valor a cobrar e MUST NOT nascer
  pendente de lançamento no sistema de gestão do hotel.
- **FR-004**: O hóspede MUST receber confirmação de que o pedido foi recebido. A
  confirmação MUST ser recado padrão — MUST NOT prometer prazo, MUST NOT afirmar fato
  da casa e MUST NOT perguntar horário de preferência.
- **FR-005**: A confirmação ao hóspede MUST ocorrer antes de a solicitação existir
  como pendência tramitada da equipe operacional.
- **FR-006**: A confirmação MUST ficar gravada no histórico da conversa da reserva
  antes de ser enviada ao hóspede.
- **FR-007**: A solicitação MUST aparecer na fila da equipe operacional da propriedade
  da reserva, recuperável pela leitura do painel, inclusive sem responsável atribuído.
  MUST NOT depender de uma notificação ter chegado a alguém.
- **FR-008**: Profissional operacional e gestão MUST conseguir consultar a fila de
  solicitações da própria propriedade. MUST NOT alcançar nome, telefone, documento,
  endereço nem demais dados da ficha cadastral do hóspede.
- **FR-009**: Recepção da propriedade MUST também recuperar a solicitação no painel.
- **FR-010**: Esta fatia MUST NOT registrar solicitação de serviço para intenção
  diferente de pedido de serviço.
- **FR-011**: Reprocessar mensagem cujo pedido já foi registrado MUST NOT produzir
  segunda confirmação nem segunda solicitação daquela origem.
- **FR-012**: Se gravar a confirmação ou a solicitação falhar, a mensagem original
  MUST permanecer, o trabalho MUST continuar recuperável, e MUST NOT enviar ao hóspede
  recado de pedido que ainda não foi gravado.
- **FR-013**: Se o envio da confirmação falhar depois de gravar, o pedido e a
  confirmação gravada MUST permanecer; o envio MUST continuar recuperável.
- **FR-014**: Conteúdo do pedido, conteúdo da confirmação e demais dados pessoais
  NUNCA MUST aparecer em log operacional; logs registram identificadores, a
  propriedade e o resultado — nunca o texto.
- **FR-015**: Resolução MUST considerar a propriedade da reserva; solicitação,
  confirmação e fila de um hotel MUST NOT vazar para o histórico ou a fila de outro.
- **FR-016**: Esta fatia MUST NOT alterar o status da reserva, MUST NOT confirmar
  chegada ou saída, MUST NOT responder dúvida pelo catálogo, MUST NOT abrir chamado de
  reclamação técnica, MUST NOT registrar consumo, MUST NOT marcar solicitação como
  resolvida e MUST NOT disparar coleta, lembrete, pulso ou pesquisa.
- **FR-017**: A urgência da solicitação MUST ser a já registrada na classificação da
  mensagem; esta fatia MUST NOT reclassificar intenção, sentimento ou urgência.
- **FR-018**: A verificação desta fatia MUST ser possível sem o serviço real de
  mensageria: um envio controlado devolve sucesso ou falha previsíveis, sem rede.

### Key Entities

- **Pedido de serviço classificado**: mensagem de estadia já marcada com a intenção
  “pedido de serviço”. É o único insumo desta fatia; as demais intenções não entram.
- **Solicitação do tipo serviço**: tarefa operacional sem cobrança, com descrição,
  quarto quando informado, urgência herdada da classificação, status aberto e vínculo
  com a reserva e a mensagem de origem. Não é reclamação técnica e não é consumo.
- **Confirmação de recebimento**: recado padrão ao hóspede de que o pedido foi
  recebido, gravado no histórico da conversa e então enviado, antes da tramitação.
- **Fila da equipe operacional**: lista recuperável no painel das solicitações abertas
  da propriedade, visível à equipe operacional, à recepção e à gestão daquele hotel,
  sem dado cadastral para quem não tem permissão de ficha. Fonte da verdade; a
  notificação, se existir no futuro, é conveniência.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das mensagens classificadas como pedido de serviço, o hóspede
  recebe uma confirmação de recebimento e nasce exatamente 1 solicitação do tipo
  serviço vinculada àquela mensagem.
- **SC-002**: Em 100% desses registros, a confirmação ao hóspede precede a tramitação
  da solicitação como pendência da equipe; 0 tramitam em silêncio.
- **SC-003**: Em 100% das solicitações desta fatia, há 0 valores a cobrar e 0 itens em
  fila de lançamento no sistema de gestão do hotel.
- **SC-004**: Em 100% dos pedidos em que o hóspede informou o quarto, a solicitação
  exibe esse quarto; em 100% dos pedidos em que não informou, 0 quartos são inventados
  e a pendência permanece visível na fila.
- **SC-005**: Em verificação com dois hotéis, 0% das solicitações ou confirmações de
  um hotel aparecem na fila ou no histórico do outro.
- **SC-006**: Em 100% das consultas da equipe operacional à fila, o pedido aberto da
  própria propriedade é recuperável e 0 dados da ficha cadastral do hóspede são
  expostos a esse perfil.
- **SC-007**: Reprocessar a mesma mensagem já concluída produz 0 segundas confirmações
  e 0 segundas solicitações.
- **SC-008**: Em 100% das falhas de envio após gravação, o pedido permanece na fila e
  a confirmação permanece no histórico; em 100% das falhas de gravação, 0 recados são
  enviados ao hóspede.
- **SC-009**: Em 100% dos desfechos, logs operacionais não contêm o conteúdo do pedido
  nem o da confirmação.
- **SC-010**: O caminho pedido classificado → confirmação + solicitação na fila da
  equipe é verificável de ponta a ponta sem o serviço real de envio de mensagem.

## Assumptions

- A fatia F3.2 (classificar a intenção) está concluída. Esta fatia parte de mensagem
  já classificada como pedido de serviço, com sentimento e urgência já gravados.
- Todo `pedido de serviço` classificado é, nesta fatia, serviço operacional sem
  cobrança. A intenção única da classificação não distingue toalha de consumo do bar;
  preço estruturado e fila de lançamento permanecem na fatia de consumo faturável
  (F3.7). Até lá, o produto não promete cobrança nem deixa de registrar o pedido.
- A estadia não guarda inventário de quartos: o número vive no sistema de gestão do
  hotel, fora do alcance deste produto. O quarto na solicitação é texto informado pelo
  hóspede, quando houver.
- A confirmação é recado padrão (não redigida a partir de conhecimento geral). Não há
  pergunta de janela de preferência neste ramo — essa pergunta é da reclamação
  técnica (F3.5).
- Marcar a solicitação como resolvida e avisar o hóspede da conclusão são a fatia de
  resolver chamado (F3.6), que depende da abertura de chamado de reclamação. Esta
  fatia só registra e confirma o recebimento.
- Superfície de uso: comportamento observável no histórico da conversa, na
  confirmação recebida pelo hóspede, e na fila de solicitações abertas visível à
  equipe operacional, à recepção e à gestão da propriedade. Ligar telas do painel
  visual de protótipo continua fora do critério de pronto.
- A verificação usa envio controlado (sucesso ou falha) e nunca chama o serviço real
  de mensageria.
- Ordem entre mensagens consecutivas não é garantida. Cada pedido de serviço é
  tratado isoladamente.
- O hóspede acabou de escrever, então a confirmação ocorre dentro da janela de
  conversa já aberta; não se inicia conversa proativa nova.
- A operação de ler solicitação já prevista na matriz de perfis (recepção, equipe
  operacional e gestão da propriedade) é a permissão desta fila. Equipe operacional e
  gestão seguem sem leitura de ficha cadastral.
- A palavra "extrato" e a palavra "conta" não aparecem em nenhum texto desta
  funcionalidade. Pedido de serviço sem cobrança também não entra em “pedidos feitos
  pelo chat” no checkout — essa lista é só de consumo e pertence a fatia posterior.
