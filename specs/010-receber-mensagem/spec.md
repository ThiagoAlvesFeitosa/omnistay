# Feature Specification: Receber Mensagem com Segurança

**Feature Branch**: `010-receber-mensagem`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "O sistema recebe as mensagens dos hóspedes por notificação do
provedor de mensageria. Antes de qualquer processamento, verifica que a notificação é
autêntica e veio de fato do provedor. Notificações repetidas do mesmo evento são descartadas
sem efeito. A resposta ao provedor é imediata; todo o processamento acontece depois, a
partir de uma fila durável que sobrevive a reinicialização da aplicação."
(backlog F3.1)

Restrições já decididas no projeto (entrada do specify): o canal de entrada é um endereço
público — notificação sem prova de origem ou com prova inválida não entra; gravar vem antes
de qualquer trabalho lento (classificar, responder, enviar); a fila é a fonte da verdade, e
queda da aplicação não pode perder mensagem já aceita; conteúdo de mensagem nunca vai para
log; o sistema não infere check-in nem se integra ao sistema de gestão do hotel; classificação
de intenção, resposta automática e abertura de chamado pertencem a fatias seguintes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mensagem autêntica da estadia é gravada sem o hóspede esperar (Priority: P1)

Como hóspede já hospedado que manda uma mensagem pelo canal (dúvida, pedido ou reclamação),
quero que o hotel receba o que eu enviei na hora, mesmo que o sistema ainda não tenha
entendido nem respondido, para eu não ter a sensação de que a mensagem se perdeu no vazio.

**Why this priority**: Sem esta fatia, a conversa da estadia não existe. A F1.3 só aproveita
resposta de ficha em reserva ainda aguardando cadastro; mensagem de quem já fez check-in
hoje é ignorada como conversa. É o alicerce de toda a Fase 3.

**Independent Test**: Pode ser testado entregando uma notificação autêntica de texto de um
telefone vinculado a uma reserva hospedada e verificando que a mensagem fica no histórico
daquela reserva, que um trabalho pendente de processamento posterior existe, e que o
provedor já foi respondido sem o sistema ter classificado nem enviado nada ao hóspede.

**Acceptance Scenarios**:

1. **Given** uma reserva da propriedade no estado hospedado e uma notificação autêntica de
   texto do telefone de contato dessa reserva, **When** a notificação chega, **Then** a
   mensagem é gravada no histórico da conversa daquela reserva e um trabalho pendente de
   processamento posterior é registrado na fila durável.
2. **Given** a mesma notificação do cenário anterior, **When** o provedor recebe a
   confirmação de recebimento, **Then** essa confirmação já ocorreu — classificação,
   resposta automática e envio ao hóspede ainda não começaram (e não fazem parte desta
   fatia).
3. **Given** uma mensagem gravada nesta fatia, **When** a recepção consulta o histórico da
   reserva, **Then** o texto enviado pelo hóspede está recuperável, vinculado à reserva
   correta da propriedade.

---

### User Story 2 - Notificação falsa ou sem prova de origem não entra (Priority: P1)

Como responsável pelo hotel, quero que só entre no sistema o que o provedor de mensageria
de fato enviou, para ninguém na internet injetar conversa falsa, disparar trabalho interno
ou contaminar o histórico do hóspede.

**Why this priority**: O endereço de recebimento é público. Sem esta recusa, o restante da
Fase 3 (classificar, responder, abrir chamado) operaria sobre mentira. É o item de
segurança desta fatia, e o que a distingue de “apenas gravar o que chegou”.

**Independent Test**: Pode ser testado enviando uma notificação sem prova de origem e outra
com prova inválida, e verificando recusa, ausência de mensagem no histórico, ausência de
trabalho na fila e ausência de efeito na reserva.

**Acceptance Scenarios**:

1. **Given** uma notificação sem prova de autenticidade do provedor, **When** ela é
   apresentada ao sistema, **Then** é recusada: nenhuma mensagem é gravada, nenhum trabalho
   é enfileirado, nenhum histórico de reserva é alterado.
2. **Given** uma notificação com prova de autenticidade inválida (não conferida com o
   segredo configurado da propriedade), **When** ela é apresentada ao sistema, **Then** é
   recusada do mesmo modo — sem processamento e sem rastro de conversa.
3. **Given** uma notificação recusada por autenticidade, **When** se consulta o histórico
   das reservas da propriedade, **Then** aquele conteúdo não aparece como mensagem de
   hóspede.

---

### User Story 3 - Reenvio do mesmo evento não duplica efeito (Priority: P1)

Como hóspede, quero que um reenvio do provedor (porque ele não teve certeza de que o hotel
recebeu) não gere duas mensagens iguais nem dois processamentos, para eu não ser tratado
duas vezes pelo mesmo recado.

**Why this priority**: O provedor reenvia quando não confirma o recebimento. Sem
idempotência, a Fase 3 inteira duplicaria resposta, chamado e cobrança. A garantia precisa
existir já na entrada, antes de classificar.

**Independent Test**: Pode ser testado entregando a mesma notificação autêntica duas vezes
e verificando um único efeito observável: uma mensagem, um trabalho pendente, nenhum segundo
histórico.

**Acceptance Scenarios**:

1. **Given** uma notificação autêntica já aceita (mensagem e trabalho pendente gravados),
   **When** o provedor reenvia o mesmo evento, **Then** o sistema confirma o recebimento de
   novo e não cria segunda mensagem nem segundo trabalho.
2. **Given** o reenvio do cenário anterior, **When** se consulta o histórico da reserva,
   **Then** o hóspede aparece com exatamente uma ocorrência daquele recado.

---

### User Story 4 - Queda da aplicação não perde mensagem já aceita (Priority: P1)

Como recepção e como hóspede, quero que uma mensagem já aceita continue existindo se a
aplicação for reiniciada antes de ser processada, para o hotel não depender de a máquina
ter ficado no ar entre o “recebi” e o “vou tratar”.

**Why this priority**: “Gravar antes de processar” só vale se o que foi gravado sobrevive
à queda. Fila só em memória perderia a mensagem do hóspede sem deixar rastro — exatamente
o defeito que esta fatia existe para impedir.

**Independent Test**: Pode ser testado aceitando uma notificação autêntica de estadia,
interrompendo a aplicação antes do processamento posterior, religando, e verificando que a
mensagem e o trabalho pendente continuam recuperáveis para processamento.

**Acceptance Scenarios**:

1. **Given** uma mensagem de estadia já gravada com trabalho pendente ainda não processado,
   **When** a aplicação é reiniciada, **Then** a mensagem permanece no histórico e o
   trabalho permanece pendente na fila durável.
2. **Given** o estado após a reinicialização, **When** o processamento posterior é retomado,
   **Then** aquele trabalho pode ser consumido — a mensagem não precisa ser reenviada pelo
   hóspede.

---

### User Story 5 - Conteúdo da mensagem não vaza em log (Priority: P2)

Como titular dos dados e responsável pelo hotel, quero que o texto do que o hóspede mandou
nunca apareça em log operacional, para um arquivo técnico não virar cópia da conversa.

**Why this priority**: Minimização de dados pessoais é princípio do produto. Identificadores
e códigos de resultado bastam para diagnosticar; o texto não.

**Independent Test**: Pode ser testado aceitando e recusando notificações (sucesso,
duplicata, sem prova de origem) e inspecionando os logs: há identificadores e códigos; não
há o texto da mensagem nem demais dados pessoais.

**Acceptance Scenarios**:

1. **Given** qualquer desfecho desta fatia (aceita, recusada, duplicada, sem reserva
   elegível), **When** o sistema registra log operacional, **Then** o conteúdo da mensagem
   e demais dados pessoais não aparecem — só identificadores, códigos de resultado e o
   hotel envolvido.
2. **Given** uma notificação autêntica cujo envelope traga o texto do hóspede, **When** o
   log é gerado, **Then** esse texto não é copiado para o log nem mesmo como “payload de
   diagnóstico”.

---

### Edge Cases

- Notificação autêntica de telefone sem reserva hospedada na propriedade: o evento é
  registrado como recebido (para o reenvio do provedor não gerar efeito novo), mas não se
  inventa conversa, não se cria reserva e não se confirma check-in. A coleta de ficha da
  F1.3 continua valendo só para reserva em aguardo de cadastro.
- Mensagem de reserva conhecida que ainda não está hospedada (ficha pronta, parcial ou
  chegará sem cadastro, entrada ainda não confirmada): o sistema não infere chegada. O
  destaque “possível chegada não registrada” no painel fica fora desta fatia.
- Reserva encerrada ou cancelada: a notificação autêntica é aceita como evento; esta fatia
  não reabre estadia nem grava conversa de atendimento.
- Mídia sem texto utilizável (áudio, imagem, documento): o evento autêntico é registrado;
  não se inventa texto; foto de documento nunca vira cadastro. Trabalho de conversa da
  estadia não é criado a partir de mídia sem texto.
- Notificação de status de entrega (mensagem enviada pelo hotel foi entregue ou lida):
  fora desta fatia; se chegar, não pode ser tratada como mensagem de hóspede.
- Duas mensagens seguidas do mesmo hóspede entregues fora de ordem: o MVP não garante
  ordem de processamento; cada notificação autêntica é aceita de forma independente, com
  o instante de origem preservado para exibição futura.
- Falha ao gravar (armazenamento indisponível): o sistema não confirma sucesso ao provedor
  — o reenvio posterior é o comportamento desejado, para a mensagem não se perder.
- Segredo de autenticidade ausente ou canal ainda não configurado: o sistema recusa
  notificação de entrada (falha fechada). Não há modo “aceitar tudo até configurar”.
- Prova de posse do endereço de recebimento (desafio de cadastro do canal): pedido com
  token correto é confirmado; token errado é recusado. Não grava mensagem.
- Hotel A não recebe conversa do hotel B: telefone e reserva são resolvidos no contexto da
  propriedade do canal.
- Esta fatia **não** classifica intenção, **não** responde ao hóspede, **não** abre
  chamado, **não** confirma pedido e **não** consulta o catálogo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST receber notificações de mensagem do provedor de mensageria
  pelo canal de entrada já existente, distinguindo notificação autêntica de notificação
  forjada.
- **FR-002**: Antes de gravar mensagem, enfileirar trabalho ou alterar histórico, o sistema
  MUST verificar a prova de autenticidade da notificação (assinatura do provedor).
- **FR-003**: Notificação sem prova de autenticidade MUST ser recusada, sem processamento
  e sem efeito em conversa, fila ou reserva.
- **FR-004**: Notificação com prova de autenticidade inválida MUST ser recusada do mesmo
  modo que a ausência de prova.
- **FR-005**: Quando a autenticidade não puder ser verificada (segredo do canal ausente),
  o sistema MUST recusar a notificação de entrada — falha fechada.
- **FR-006**: Notificação autêntica de texto cujo telefone corresponda a uma reserva
  hospedada da propriedade do canal MUST gravar a mensagem no histórico dessa reserva e
  registrar um trabalho pendente na fila durável, na mesma aceitação.
- **FR-007**: A confirmação de recebimento ao provedor MUST ocorrer sem esperar
  classificação, interpretação, consulta a catálogo ou envio de mensagem ao hóspede.
- **FR-008**: Reapresentação da mesma notificação (mesmo identificador de evento do
  provedor) MUST ser confirmada ao provedor e MUST NOT criar segunda mensagem, segundo
  trabalho nem segundo efeito observável.
- **FR-009**: Mensagem e trabalho já aceitos MUST permanecer recuperáveis após
  reinicialização da aplicação, até o processamento posterior consumi-los.
- **FR-010**: Conteúdo de mensagem e demais dados pessoais NUNCA MUST aparecer em log
  operacional; logs registram identificadores, códigos de resultado e a propriedade
  envolvida.
- **FR-011**: Resolução de reserva MUST considerar a propriedade do canal; mensagem de um
  hotel MUST NOT ser gravada no histórico de outro.
- **FR-012**: Notificação autêntica de telefone sem reserva hospedada MUST registrar o
  evento o bastante para o reenvio ser inócuo, MUST NOT inventar reserva nem conversa, e
  MUST NOT confirmar chegada.
- **FR-013**: O caminho da F1.3 (resposta de ficha em reserva aguardando cadastro) MUST
  permanecer: esta fatia não substitui a interpretação da ficha nem dispara nova coleta.
- **FR-014**: Mídia sem texto utilizável MUST NOT gerar trabalho de conversa da estadia
  nem texto inventado; foto de documento MUST NOT ser aceita como cadastro.
- **FR-015**: Pedido de prova de posse do endereço de recebimento (desafio de cadastro do
  canal) MUST ser confirmado só com o token configurado da propriedade; token inválido
  MUST ser recusado, sem gravar mensagem.
- **FR-016**: Esta fatia MUST NOT classificar intenção, sentimento ou urgência; MUST NOT
  responder automaticamente; MUST NOT abrir chamado, registrar pedido de serviço nem
  consumo; MUST NOT alterar o status da reserva.
- **FR-017**: Se a gravação da notificação autêntica falhar, o sistema MUST NOT confirmar
  sucesso ao provedor.
- **FR-018**: O trabalho enfileirado nesta fatia é “mensagem de estadia pendente de
  processamento posterior”. O que esse processamento fará (classificar, responder,
  encaminhar a humano) pertence às fatias seguintes; nesta fatia basta o trabalho existir
  e sobreviver à queda.

### Key Entities

- **Notificação de entrada**: aviso do provedor de que algo aconteceu no canal (em geral,
  o hóspede enviou texto). Traz identificador único do evento, prova de autenticidade e,
  quando houver, telefone de origem e texto.
- **Mensagem recebida da estadia**: texto do hóspede gravado no histórico da reserva
  hospedada, recuperável pela recepção, ainda sem classificação nesta fatia.
- **Trabalho pendente**: item na fila durável que representa “esta mensagem ainda precisa
  ser processada”. Sobrevive à reinicialização; não é executado nesta fatia além de ser
  criado.
- **Prova de autenticidade**: evidência de que a notificação veio do provedor, conferida
  com o segredo configurado da propriedade antes de qualquer efeito.
- **Reserva hospedada**: reserva cuja chegada já foi confirmada pela recepção; é o
  contexto em que a conversa da estadia passa a ser aceita como mensagem.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das notificações autênticas de texto de reserva hospedada, a mensagem
  aparece no histórico da reserva correta e existe exatamente um trabalho pendente
  associado, sem o hóspede ter recebido resposta nesta fatia.
- **SC-002**: Em 100% das notificações sem prova de autenticidade ou com prova inválida,
  o efeito observável é zero: 0 mensagens novas, 0 trabalhos novos, 0 alterações de
  reserva.
- **SC-003**: Em 100% dos reenvios do mesmo evento já aceito, o histórico permanece com
  uma única ocorrência daquele recado e a fila não ganha segundo trabalho.
- **SC-004**: Após reinicialização com trabalho ainda pendente, 100% das mensagens já
  aceitas continuam recuperáveis e o trabalho permanece pendente — 0 mensagens somem por
  queda da aplicação.
- **SC-005**: A confirmação ao provedor não espera classificação nem envio: em 100% das
  aceitações desta fatia, o provedor já foi respondido enquanto o trabalho ainda está
  pendente.
- **SC-006**: Em 100% dos desfechos (aceita, recusada, duplicada, sem reserva elegível),
  logs operacionais não contêm o conteúdo da mensagem nem demais dados pessoais.
- **SC-007**: 0 check-ins são confirmados, 0 reservas são criadas e 0 chamados são abertos
  como efeito desta fatia.
- **SC-008**: O caminho notificação → verificação de autenticidade → gravação →
  confirmação ao provedor → fila durável é verificável de ponta a ponta sem depender do
  canal real de mensagens nos testes automatizados.

## Assumptions

- A fatia F2.2 (confirmar chegada) está concluída: existe reserva no estado hospedado, e
  o recado de boas-vindas já convidou o hóspede a perguntar pelo mesmo canal.
- A fatia F1.3 já recebe resposta de ficha pelo mesmo canal de entrada, com recusa de
  prova inválida e idempotência do identificador de evento. Esta fatia **reusa esse canal**
  e passa a aceitar conversa de reserva hospedada; não cria um segundo endereço de
  recebimento.
- O identificador único do evento vem do provedor e já é a chave de idempotência do
  produto (garantia no armazenamento, não só conferência em memória).
- A fila durável é a mesma fila de trabalho já usada para envio de coleta, interpretação
  de ficha, lembrete e boas-vindas. Não se introduz mecanismo paralelo de fila.
- O tipo de trabalho novo desta fatia é só o gancho para a F3.2 (classificar). Até a F3.2
  existir, o item pode permanecer pendente sem efeito visível ao hóspede — isso é
  correto: esta fatia não responde.
- Reserva hospedada é resolvida pelo telefone de contato no contexto da propriedade do
  canal (MVP: um número de negócio, uma propriedade).
- Ordem entre mensagens consecutivas não é garantida (Artigo XV). O instante de origem,
  quando o provedor o envia, é preservado para a conversa ser reconstruída na exibição.
- Notificação de status de entrega, simulador visual (F6.2), limite de taxa por origem,
  destaque de “possível chegada não registrada” e qualquer resposta ao hóspede ficam fora.
- Superfície de uso: comportamento observável pela entrada do canal, pelo histórico da
  reserva e pela fila de trabalho. Ligar o protótipo React continua fora do critério de
  pronto.
- Testes automatizados usam implementação falsa do canal / envelopes assinados de teste;
  nenhum teste desta fatia chama o provedor real.
