# Feature Specification: Resolver Chamado e Confirmar

**Feature Branch**: `015-resolver-chamado`

**Created**: 2026-08-18

**Status**: Draft

**Input**: User description: "A equipe operacional marca o chamado como resolvido pelo
celular, e o hóspede recebe confirmação da resolução. Chamados não resolvidos
permanecem visíveis na passagem de turno."
(backlog F3.6)

Restrições já decididas no projeto (entrada do specify): o sistema não se integra ao
sistema de gestão do hotel; a fila do painel (Alert Center) é a fonte da verdade e a
notificação é conveniência; gravar antes de enviar; conteúdo de mensagem nunca vai
para log; prazo de destaque de chamado aberto continua sendo o da propriedade, não
número mágico; gestão consulta e não fecha chamado; equipe operacional fecha chamado
sem ver ficha cadastral. Consumo faturável, pulso do segundo dia, atribuir
responsável em passo separado e cancelar solicitação pertencem a fatias seguintes
ou ficam fora deste recorte.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A equipe marca como resolvido e fica registrado quem e quando (Priority: P1)

Como profissional da equipe operacional (manutenção, governança) que já atendeu o
problema no quarto, quero marcar o chamado como resolvido pelo celular em um único
gesto, e quero que fique registrado quem resolveu e quando, para o hotel ter prova
de que o ciclo fechou e para o próximo turno não retrabalhar o que já foi feito.

**Why this priority**: Sem o clique, o trabalho físico não existe para o produto —
o hóspede nunca é avisado e o chamado envelhece aberto. Registrar quem e quando é
o critério de aceite desta fatia e o que torna a omissão perceptível depois.

**Independent Test**: Pode ser testado com um chamado aberto da propriedade,
autenticando um profissional operacional daquela propriedade, marcando como
resolvido e verificando: o chamado deixa de ser pendência aberta, constam o autor
da resolução e o instante, e a mesma ação com o mesmo chamado não produz segunda
resolução.

**Acceptance Scenarios**:

1. **Given** um chamado aberto da propriedade (reclamação técnica ou pedido de
   serviço), **When** um profissional operacional daquela propriedade marca como
   resolvido, **Then** o chamado passa a resolvido, com a identificação de quem
   resolveu e o instante da resolução.
2. **Given** o desfecho do cenário 1, **When** a equipe consulta o Alert Center,
   **Then** aquele chamado **não** aparece mais entre as pendências abertas.
3. **Given** um chamado aberto, **When** a recepção da mesma propriedade marca
   como resolvido, **Then** o resultado é o mesmo: quem resolveu e quando ficam
   registrados, e a pendência sai da fila aberta.

---

### User Story 2 - O hóspede é avisado depois que o chamado foi resolvido (Priority: P1)

Como hóspede que reclamou ou pediu um serviço, quero receber confirmação de que o
atendimento foi concluído **depois** de a equipe marcar a resolução, para eu não
ficar imaginando se alguém veio ao quarto e para eu não ligar de novo à recepção.

**Why this priority**: A confirmação de resolução é o passo que fecha a jornada
de atrito. Sem ela, o clique interno só organiza o painel — o hóspede continua no
escuro. A ordem é a inversa da abertura: aqui o fato já aconteceu no quarto; o
recado informa um fato gravado, não promete um fato futuro.

**Independent Test**: Pode ser testado observando a ordem no caminho feliz: no
instante em que a confirmação de resolução entra no histórico da conversa, o
chamado já consta como resolvido, com autor e instante.

**Acceptance Scenarios**:

1. **Given** um chamado marcado como resolvido, **When** o hóspede consulta a
   conversa, **Then** há uma confirmação de que o atendimento foi concluído,
   gravada no histórico da mesma reserva — e essa confirmação não promete visita
   futura, não cita prazo de garantia e não afirma fato da casa que não foi
   cadastrado.
2. **Given** a resolução do cenário 1, **When** se observa a ordem, **Then** a
   resolução já está registrada **antes** de a confirmação existir como recado
   enviado — zero hóspedes são avisados de uma resolução que ainda não foi
   gravada.
3. **Given** um chamado de reclamação resolvido, **When** se lê o recado, **Then**
   ele fala de problema atendido / manutenção concluída, sem reabrir pergunta de
   horário e sem inventar o que foi feito no quarto.
4. **Given** um pedido de serviço resolvido, **When** se lê o recado, **Then** ele
   fala de pedido atendido, sem preço, sem “conta” e sem a palavra “extrato”.

---

### User Story 3 - Chamado não se resolve duas vezes (Priority: P1)

Como hotel, quero que um chamado já resolvido recuse nova resolução, para um
toque duplo no celular ou um retrabalho não mandar segunda confirmação ao hóspede
nem apagar quem resolveu da primeira vez.

**Why this priority**: Idempotência visível ao hóspede e à operação. Sem ela, o
caminho feliz é frágil no segundo toque.

**Independent Test**: Pode ser testado resolvendo uma vez e tentando resolver de
novo o mesmo chamado, verificando recusa, autor e instante inalterados, e zero
segunda confirmação.

**Acceptance Scenarios**:

1. **Given** um chamado já resolvido, **When** o mesmo profissional ou outro
   autorizado tenta resolver de novo, **Then** a tentativa é recusada, quem
   resolveu e quando permanecem os da primeira resolução, e o hóspede não recebe
   segunda confirmação.
2. **Given** duas tentativas simultâneas de resolver o mesmo chamado ainda
   aberto, **When** ambas concluem, **Then** existe exatamente uma resolução e
   exatamente uma confirmação ao hóspede.

---

### User Story 4 - Na passagem de turno, o que não foi resolvido continua visível (Priority: P1)

Como recepcionista na passagem de turno, quero ver os chamados e pedidos ainda
abertos da propriedade — inclusive os que a manutenção já atendeu no quarto mas
ninguém marcou — para a pendência não se perder na conversa oral e para o próximo
turno não partir do zero.

**Why this priority**: Se o staff resolve fisicamente e não clica, o hóspede
nunca é avisado e o chamado envelhece. A mitigação do produto não é adivinhar o
conserto: é deixar a omissão visível na mesma fila que a equipe já usa. A
passagem de turno desta fatia é essa leitura; não é uma tela nova que misture
ficha parcial e reserva do dia seguinte (isso já vive na fila do dia).

**Independent Test**: Pode ser testado com um chamado ainda aberto e outro já
resolvido, autenticando recepção na consulta da fila operacional, verificando
que o aberto permanece e o resolvido não aparece entre as pendências.

**Acceptance Scenarios**:

1. **Given** chamados e pedidos abertos na propriedade, **When** a recepção
   consulta o Alert Center na passagem de turno, **Then** todas as pendências
   ainda não resolvidas aparecem, inclusive sem responsável atribuído e inclusive
   as abertas além do prazo de destaque da propriedade.
2. **Given** um chamado já resolvido, **When** a mesma consulta acontece,
   **Then** esse chamado **não** figura entre as pendências abertas — a passagem
   de turno mostra o que falta, não o histórico do que já fechou.
3. **Given** a equipe operacional e a gestão da mesma propriedade, **When**
   consultam o Alert Center, **Then** as pendências abertas também são
   recuperáveis — a fila não depende de uma notificação ter chegado a alguém.

---

### User Story 5 - Quem não deve fechar chamado não fecha (Priority: P1)

Como hotel, quero que só recepção e equipe operacional da **própria** propriedade
marquem resolução, e que a gestão continue só consultando, para um indicador não
virar botão de fechar chamado e para o hotel vizinho não encerrar o trabalho
deste.

**Why this priority**: A matriz de perfis já separou autoridade de consulta e
autoridade de fechar. Esta fatia é a primeira a exercitar o fechar. Staff fecha
sem ver ficha; gestão vê a fila e não fecha.

**Independent Test**: Pode ser testado tentando resolver com gestão da mesma
propriedade (recusa), com profissional de outra propriedade (sem revelar que o
chamado existe), e com staff da propriedade certa (sucesso, sem dado cadastral
na resposta).

**Acceptance Scenarios**:

1. **Given** um chamado aberto, **When** a gestão da mesma propriedade tenta
   marcar como resolvido, **Then** a tentativa é recusada, o chamado permanece
   aberto e o hóspede não recebe confirmação.
2. **Given** um chamado da propriedade A, **When** recepção ou staff da
   propriedade B tenta resolver, **Then** a tentativa não revela que o chamado
   existe e o chamado de A permanece aberto.
3. **Given** a resolução bem-sucedida por staff, **When** se observa o que o
   profissional alcança na ação e na fila, **Then** não há nome, telefone,
   documento, endereço nem demais dados da ficha do hóspede.

---

### User Story 6 - Falha ao gravar ou ao enviar não desfaz o trabalho nem inventa resolução (Priority: P1)

Como hóspede e como hotel, quero que uma falha no envio da confirmação **não**
reabra o chamado já resolvido, e que uma falha ao gravar a resolução **não**
mande recado de “já foi atendido”, para “gravar antes de enviar” valer também
neste fechamento.

**Why this priority**: Sem este caminho, a fatia só funciona no dia em que a
mensageria está no ar. Recado de resolução sobre chamado ainda aberto é pior do
que confirmação atrasada.

**Independent Test**: Pode ser testado (a) gravando a resolução com sucesso e
falhando o envio, e (b) falhando a gravação da resolução, verificando chamado
resolvido e envio recuperável no primeiro caso, chamado ainda aberto e zero
recado no segundo.

**Acceptance Scenarios**:

1. **Given** a resolução já gravada e o envio ao hóspede falhando, **When** o
   sistema trata a falha, **Then** o chamado permanece resolvido, a confirmação
   permanece no histórico quando já tiver sido gravada, o envio fica
   recuperável, e o chamado **não** volta à fila aberta por causa da falha de
   envio.
2. **Given** a gravação da resolução falhando, **When** se observa o canal do
   hóspede e o Alert Center, **Then** nenhum recado de atendimento concluído é
   enviado, o chamado permanece aberto na passagem de turno, e a ação continua
   pendente de nova tentativa.

---

### User Story 7 - Reprocessar o aviso de resolução não duplica a mensagem (Priority: P1)

Como hóspede, quero no máximo uma confirmação de que aquele chamado foi
concluído, mesmo se o envio for retomado depois de uma falha.

**Why this priority**: O segundo toque no chamado já é recusado (User Story 3).
Esta história cobre o retrabalho **do aviso**, não da marcação.

**Independent Test**: Pode ser testado concluindo a resolução uma vez, com o
aviso já gravado, e retomando o envio, verificando zero segunda confirmação no
histórico.

**Acceptance Scenarios**:

1. **Given** um chamado já resolvido cuja confirmação já está no histórico,
   **When** o envio é retomado, **Then** o hóspede não recebe segunda
   confirmação daquela resolução.
2. **Given** resolução gravada e confirmação ainda não gravada, **When** o
   trabalho de aviso é processado, **Then** nasce exatamente uma confirmação
   daquela resolução.

---

### User Story 8 - Conteúdo da mensagem não vaza em log (Priority: P2)

Como titular dos dados e responsável pelo hotel, quero que o texto da
confirmação de resolução e a descrição do chamado nunca apareçam em log
operacional.

**Why this priority**: Minimização de dados pessoais continua valendo no
fechamento. O log pode registrar identificadores, a propriedade e o resultado;
o texto não.

**Independent Test**: Pode ser testado nos desfechos feliz, recusa de segunda
resolução, recusa de perfil e falha de envio, inspecionando os logs: há
identificadores e resultado; não há o texto ao hóspede nem a descrição do
chamado.

**Acceptance Scenarios**:

1. **Given** uma resolução confirmada com sucesso, **When** o sistema registra
   log operacional, **Then** aparecem identificadores, a propriedade e a
   indicação de chamado resolvido — e não o conteúdo da confirmação nem a
   descrição do problema.
2. **Given** recusa de segunda resolução, recusa de perfil ou falha de envio,
   **When** o sistema registra log operacional, **Then** há código de resultado
   e identificadores, sem o texto.

---

### Edge Cases

- Esta fatia fecha solicitação **aberta** de tipo reclamação **ou** serviço.
  Não existe fatia posterior para fechar pedido de toalha: se só a reclamação
  fechasse, o serviço operacional ficaria pendente para sempre.
- Consumo faturável **não** entra: ainda não existe nesta linha do produto e
  pertence à fatia de lançamento. Esta fatia MUST NOT inventar valor a cobrar
  nem fila de lançamento ao resolver.
- Atribuir responsável em passo separado, passar para “em andamento” e
  cancelar solicitação estão **fora** desta fatia. O clique único resolve a
  pendência aberta; quem clicou é quem resolveu.
- Gestão consulta o Alert Center e **não** resolve. Equipe operacional resolve
  e **não** vê ficha cadastral.
- Hotel A não resolve chamado do hotel B e a tentativa não revela que o
  chamado de B existe.
- Chamado já resolvido recusa nova resolução (User Story 3). Transição inválida
  é recusada de forma durável — não só no caminho feliz da aplicação.
- Reabrir chamado resolvido está fora desta fatia.
- Confirmação de resolução é recado padrão, distinto da confirmação de
  *recebimento* da abertura. Não pergunta horário, não promete visita, não
  afirma fato da casa, não usa “extrato” nem “conta”.
- A ordem desta fatia é a inversa da abertura: primeiro grava a resolução,
  depois o recado. Avisar o hóspede de um fechamento que ainda não existe é o
  defeito a evitar.
- Falha de envio **não** reabre o chamado. A pendência que resta é o envio,
  recuperável; a passagem de turno já não lista aquele item como aberto.
- Se o staff atendeu no quarto e não clicou, o chamado permanece aberto e
  visível — inclusive com destaque de tempo excessivo, quando a propriedade
  tiver o prazo configurado. O produto não infere resolução.
- Status da reserva (ainda hospedado, já encerrado) **não** impede resolver.
  O trabalho no quarto pode fechar depois da saída; o recado ainda é devido.
- Esta fatia **não** classifica intenção, **não** abre chamado novo, **não**
  responde dúvida pelo catálogo, **não** registra consumo, **não** altera o
  status da reserva, **não** dispara pulso, coleta nem lembrete.
- Superfície de passagem de turno **desta** fatia é o Alert Center (pendências
  abertas). Ficha parcial e reserva do dia seguinte sem cadastro continuam na
  fila do dia; não se mistura as duas listas aqui.
- Ligar telas visuais do protótipo continua fora do critério de pronto.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Recepção e equipe operacional da propriedade MUST poder marcar
  como resolvida uma solicitação aberta do tipo reclamação ou do tipo serviço
  daquela propriedade.
- **FR-002**: Marcar como resolvida MUST registrar quem resolveu (a pessoa
  autenticada que concluiu a ação) e o instante da resolução. MUST NOT deixar
  resolução sem autor nem sem instante.
- **FR-003**: Solicitação resolvida MUST sair da lista de pendências abertas do
  Alert Center. MUST permanecer recuperável como fato histórico daquela
  reserva, sem voltar à fila de passagem de turno.
- **FR-004**: Solicitação ainda não resolvida MUST permanecer visível no Alert
  Center da propriedade para recepção, equipe operacional e gestão — inclusive
  sem responsável atribuído e inclusive além do prazo de destaque. MUST NOT
  depender de uma notificação ter chegado.
- **FR-005**: O hóspede MUST receber confirmação de que o atendimento foi
  concluído. A confirmação MUST ser recado padrão adequado ao tipo (problema
  atendido na reclamação; pedido atendido no serviço). MUST NOT prometer visita
  futura, MUST NOT afirmar fato da casa e MUST NOT usar as palavras “extrato”
  nem “conta”.
- **FR-006**: A resolução MUST estar gravada antes de a confirmação existir
  como recado enviado. MUST NOT avisar o hóspede de uma resolução que ainda
  não foi registrada.
- **FR-007**: A confirmação MUST ficar gravada no histórico da conversa da
  reserva antes de ser enviada ao hóspede.
- **FR-008**: Tentativa de resolver solicitação já resolvida MUST ser recusada.
  MUST NOT alterar quem resolveu nem o instante da primeira resolução, e MUST
  NOT enviar segunda confirmação.
- **FR-009**: Gestão MUST NOT resolver solicitação. Tentativa MUST ser recusada
  e o item MUST permanecer aberto.
- **FR-010**: Tentativa de resolver solicitação de outra propriedade MUST NOT
  revelar que o item existe e MUST NOT alterá-lo.
- **FR-011**: Equipe operacional MUST NOT alcançar nome, telefone, documento,
  endereço nem demais dados da ficha cadastral ao resolver nem ao consultar a
  fila.
- **FR-012**: Se gravar a resolução falhar, o item MUST permanecer aberto, o
  trabalho MUST continuar tentável, e MUST NOT enviar recado de atendimento
  concluído.
- **FR-013**: Se o envio da confirmação falhar depois de gravar a resolução, o
  item MUST permanecer resolvido (MUST NOT reabrir) e o envio MUST continuar
  recuperável. Retomar o envio MUST NOT produzir segunda confirmação daquela
  resolução.
- **FR-014**: Conteúdo da confirmação, descrição do chamado e demais dados
  pessoais NUNCA MUST aparecer em log operacional; logs registram
  identificadores, a propriedade e o resultado — nunca o texto.
- **FR-015**: Resolução MUST considerar a propriedade da reserva; chamado,
  confirmação e Alert Center de um hotel MUST NOT vazar para o histórico ou a
  fila de outro.
- **FR-016**: Esta fatia MUST NOT atribuir responsável em passo separado, MUST
  NOT cancelar solicitação, MUST NOT registrar consumo, MUST NOT alterar o
  status da reserva, MUST NOT abrir chamado novo, MUST NOT responder dúvida
  pelo catálogo e MUST NOT disparar coleta, lembrete, pulso ou pesquisa.
- **FR-017**: Esta fatia MUST NOT resolver tipo consumo. MUST NOT inventar
  valor a cobrar nem status de lançamento ao fechar reclamação ou serviço.
- **FR-018**: A verificação desta fatia MUST ser possível sem o serviço real
  de mensageria: um envio controlado devolve sucesso ou falha previsíveis, sem
  rede.

### Key Entities

- **Solicitação aberta**: reclamação ou pedido de serviço ainda pendente no
  Alert Center da propriedade. É o único insumo que esta fatia fecha.
- **Resolução**: fato de o ciclo ter fechado, com quem resolveu e quando. Tira
  o item da passagem de turno. Não é cancelamento e não é lançamento de
  consumo.
- **Confirmação de resolução**: recado padrão ao hóspede de que o atendimento
  foi concluído, gravado no histórico da conversa e então enviado, **depois**
  da resolução registrada. Distinta da confirmação de recebimento da abertura.
- **Alert Center (passagem de turno desta fatia)**: lista recuperável das
  pendências ainda abertas da propriedade. Fonte da verdade; a notificação, se
  existir no futuro, é conveniência. O que já foi resolvido não permanece nessa
  lista.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das resoluções bem-sucedidas, ficam registrados quem
  resolveu e o instante; 0 resoluções existem sem autor ou sem instante.
- **SC-002**: Em 100% dessas resoluções, o hóspede recebe exatamente 1
  confirmação de atendimento concluído, e essa confirmação só existe depois de
  a resolução estar gravada.
- **SC-003**: Tentativa de resolver o mesmo item pela segunda vez é recusada em
  100% dos casos e produz 0 segundas confirmações e 0 alterações de autor ou
  instante.
- **SC-004**: Em 100% das consultas ao Alert Center na passagem de turno, 100%
  das pendências ainda abertas da propriedade aparecem e 0 itens já resolvidos
  figuram nessa lista.
- **SC-005**: Gestão conclui resolução com sucesso em 0% das tentativas.
  Profissional de outro hotel altera chamado alheio em 0% das tentativas.
- **SC-006**: Em 100% das ações da equipe operacional, 0 dados da ficha
  cadastral do hóspede são expostos.
- **SC-007**: Em verificação com dois hotéis, 0% das resoluções ou
  confirmações de um hotel aparecem no Alert Center ou no histórico do outro.
- **SC-008**: Em 100% das falhas de envio após gravação da resolução, o item
  permanece resolvido e o envio é recuperável; em 100% das falhas de gravação
  da resolução, 0 recados de conclusão são enviados e o item permanece aberto.
- **SC-009**: Retomar o aviso de uma resolução já confirmada no histórico
  produz 0 segundas confirmações.
- **SC-010**: Em 100% dos desfechos, logs operacionais não contêm o conteúdo
  da confirmação nem a descrição do chamado.
- **SC-011**: Pedido de serviço aberto também fecha por esta fatia: 0 pedidos
  de serviço permanecem infecháveis por falta de recorte. Consumo faturável
  resolvido por esta fatia: 0.
- **SC-012**: O caminho pendência aberta → clique de resolver → confirmação ao
  hóspede é verificável de ponta a ponta sem o serviço real de envio de
  mensagem.

## Assumptions

- As fatias F3.4 (pedido de serviço) e F3.5 (chamado de reclamação) estão
  concluídas. O Alert Center desta entrega é a mesma fila de solicitações
  abertas; esta fatia acrescenta o fechar e o aviso de conclusão.
- “Chamado” no enunciado do backlog cobre reclamação **e** serviço
  operacional. Não há fatia posterior para fechar toalha extra; consumo
  faturável é F3.7.
- A passagem de turno do Artefato 2 (R7) mistura chamados abertos, fichas
  parciais e reservas do dia seguinte. **Nesta fatia** só o primeiro item é
  entregue, na lista que a equipe já consulta. Ficha parcial e dia seguinte
  continuam na fila do dia. Não se cria uma tela agregada nova (Artigo XI).
- Ligar o painel visual de protótipo continua fora do critério de pronto. O
  comportamento é observável na fila operacional, no histórico da conversa e
  na confirmação recebida pelo hóspede.
- Quem resolve é quem conclui a ação autenticado. Não há passo separado de
  “assumir” ou “em andamento” neste recorte: acrescentá-lo sem critério de
  aceite no backlog inflaria a fatia. Cancelar também fica fora.
- A ordem confirmação-antes-de-tramitar vale na **abertura**. Na resolução, o
  fato no quarto já ocorreu; gravar a resolução antes do recado evita avisar
  um fechamento inexistente (Artigos III e XV).
- Se o staff não clicar, o produto não infere que o quarto foi atendido. A
  omissão permanece visível na passagem de turno, com o destaque de tempo já
  entregue na F3.5 quando o prazo da propriedade existir.
- A operação de resolver já prevista na matriz de perfis (recepção e equipe
  operacional; gestão recusada) é a permissão desta fatia. Nenhuma operação
  nova de autorização é necessária.
- A verificação usa envio controlado (sucesso ou falha) e nunca chama o
  serviço real de mensageria.
- O recado de resolução pode ocorrer horas depois da última mensagem do
  hóspede. Continua sendo recado transacional ligado a um atendimento já
  existente, não oferta comercial. Justifica-se pelo processo (fechar o ciclo
  visível ao hóspede); não é mensagem proativa de reengajamento (Artigo VII).
- A palavra "extrato" e a palavra "conta" não aparecem em nenhum texto desta
  funcionalidade.
- Existir chamado **aberto** continua sendo o insumo da supressão do pulso
  (F3.8). Esta fatia, ao resolver, tira esse insumo; não dispara nem suprime
  pulso por conta própria.
