# Feature Specification: Classificar a Intenção

**Feature Branch**: `011-classificar-intencao`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "Cada mensagem recebida é classificada quanto à intenção, ao
sentimento e à urgência, para que o sistema decida entre responder automaticamente e
envolver uma pessoa. Quando a classificação não é possível — por indisponibilidade do
serviço de classificação ou por resposta inválida — a mensagem é preservada e encaminhada
para atendimento humano."
(backlog F3.2)

Restrições já decididas no projeto (entrada do specify): na dúvida, um humano vê — falha
de classificação nunca vira resposta automática nem descarte; a mensagem da estadia já foi
gravada na fatia anterior, e este trabalho acontece depois, a partir da fila durável;
conteúdo de mensagem nunca vai para log (identificadores, intenção resultante e códigos de
erro bastam); cada mensagem é classificada isoladamente, sem garantia de ordem; o sistema
não se integra ao sistema de gestão do hotel. Responder a dúvida pelo catálogo, registrar
pedido de serviço e abrir chamado de reclamação (com confirmação ao hóspede) pertencem às
fatias seguintes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mensagem classificada ganha intenção, sentimento e urgência (Priority: P1)

Como recepção (e, nas fatias seguintes, o próprio atendimento), quero que cada mensagem
já recebida de um hóspede hospedado fique marcada com intenção, sentimento e urgência, e
que a resposta completa do classificador fique guardada, para o hotel decidir com base
num registro auditável — e não no palpite de quem leu o chat depois.

**Why this priority**: Sem os três eixos gravados, não há como decidir entre responder
sozinho e chamar uma pessoa. É o único resultado positivo desta fatia, e o insumo de toda
a Fase 3 que vem depois.

**Independent Test**: Pode ser testado partindo de uma mensagem de estadia já gravada,
com trabalho pendente de classificação, fazendo o classificador devolver um resultado
válido, e verificando os três campos na mensagem, a resposta completa preservada, e o
trabalho deixando de estar pendente — sem nenhuma mensagem nova ao hóspede.

**Acceptance Scenarios**:

1. **Given** uma mensagem de texto de reserva hospedada já gravada, com trabalho pendente
   de classificação, **When** o classificador devolve um resultado válido com os três
   eixos, **Then** a mensagem passa a registrar intenção, sentimento e urgência, e a
   resposta completa do classificador fica preservada para auditoria.
2. **Given** a classificação bem-sucedida do cenário anterior, **When** a recepção consulta
   o histórico da reserva, **Then** o texto original do hóspede continua lá, agora com a
   classificação anexada — nada foi apagado nem reescrito no conteúdo.
3. **Given** a mesma classificação bem-sucedida, **When** o fluxo desta fatia termina,
   **Then** o trabalho pendente de classificação daquela mensagem não permanece pendente
   (foi concluído), e o hóspede ainda não recebeu resposta automática nem chamado aberto.

---

### User Story 2 - Serviço de classificação indisponível encaminha a uma pessoa (Priority: P1)

Como hóspede e como hotel, quero que uma falha do serviço de classificação não faça minha
mensagem desaparecer nem gere uma resposta inventada, e que uma pessoa do hotel veja que
aquilo precisa de atendimento, para a regra “na dúvida, um humano vê” valer na prática.

**Why this priority**: É o caso obrigatório da fatia e o que distingue classificar de
“tentar classificar e, se não der, ignorar”. Perder a mensagem ou responder no escuro
seria pior do que não ter classificador.

**Independent Test**: Pode ser testado com mensagem já gravada e classificador
indisponível, e verificando: texto ainda no histórico, sem intenção/sentimento/urgência
preenchidos, pendência visível para a recepção da propriedade, nenhuma resposta automática
ao hóspede, trabalho de classificação não deixado em espera infinita.

**Acceptance Scenarios**:

1. **Given** uma mensagem de estadia já gravada e o serviço de classificação indisponível,
   **When** o trabalho pendente é processado, **Then** a mensagem permanece no histórico
   da reserva correta, os três eixos estruturados ficam vazios, e a reserva aparece para
   a recepção da propriedade com indicação de que aquela mensagem precisa de atendimento
   humano.
2. **Given** o desfecho do cenário anterior, **When** se observa o que o hóspede recebeu
   nesta fatia, **Then** nenhuma resposta automática foi enviada — nem desculpa gerada,
   nem afirmação sobre a propriedade.
3. **Given** a mesma falha, **When** a aplicação é reiniciada em seguida, **Then** a
   mensagem continua recuperável e a pendência humana continua visível — a falha do
   classificador não se converte em perda por queda.

---

### User Story 3 - Resposta inválida do classificador também vai para humano (Priority: P1)

Como responsável pelo hotel, quero que uma resposta do classificador fora do formato
esperado (campos faltando, valores que não existem na taxonomia, texto que não é o
resultado estruturado) seja tratada como falha de classificação — preservando o que veio,
sem usar esse resultado para decidir — para o sistema não roteá-lo com base em lixo.

**Why this priority**: Indisponibilidade é só um modo de falha. Aceitar um resultado
malformado como se fosse classificação é o outro, e costuma ser o que gera chamado
errado ou resposta automática indevida.

**Independent Test**: Pode ser testado fazendo o classificador devolver um resultado que
não fecha com a taxonomia (ou que omite um dos três eixos) e verificando encaminhamento
humano, eixos estruturados vazios, resposta completa preservada para auditoria e nenhuma
resposta ao hóspede.

**Acceptance Scenarios**:

1. **Given** uma mensagem de estadia já gravada, **When** o classificador devolve um
   resultado que não atende ao formato esperado (falta eixo, valor fora da taxonomia, ou
   conteúdo que não é o resultado estruturado), **Then** os três eixos estruturados
   permanecem vazios, a mensagem é encaminhada para atendimento humano visível à
   recepção, e a resposta completa recebida fica preservada para auditoria posterior.
2. **Given** o desfecho do cenário anterior, **When** o sistema decide o próximo passo
   desta fatia, **Then** não trata aquele resultado como classificação válida: não
   encaminha para o ramo automático e não dispara resposta ao hóspede.
3. **Given** uma resposta inválida já preservada, **When** alguém for investigar depois
   por que a mensagem foi para humano, **Then** o bruto do classificador ainda está
   disponível — não só o fato de ter falhado.

---

### User Story 4 - Classificar não é ainda responder nem abrir chamado (Priority: P1)

Como hóspede, quero que o fato de o sistema ter entendido minha mensagem (dúvida, pedido
ou reclamação) não dispare sozinho, nesta fatia, uma resposta nem um chamado, para cada
tipo de recado seguir o fluxo certo depois — confirmação antes de tramitar, catálogo
como única fonte de afirmação.

**Why this priority**: O propósito desta fatia é **decidir**, não executar os ramos.
Abrir chamado ou responder aqui furaria a ordem “confirmação antes de tramitação” e
misturaria F3.3–F3.5 nesta entrega.

**Independent Test**: Pode ser testado classificando com sucesso uma dúvida geral, um
pedido de serviço e uma reclamação técnica com sentimento negativo, e verificando os
três eixos gravados em cada uma, zero mensagens enviadas ao hóspede e zero chamados ou
pedidos criados.

**Acceptance Scenarios**:

1. **Given** mensagens classificadas com sucesso como dúvida geral, pedido de serviço e
   reclamação técnica (esta última com sentimento negativo), **When** esta fatia termina,
   **Then** cada uma tem intenção, sentimento e urgência registrados, e nenhuma gerou
   resposta automática, consulta a fatos da propriedade para redigir texto, chamado ou
   pedido.
2. **Given** uma mensagem classificada como fora de escopo, interesse comercial ou
   pedido de checkout, **When** esta fatia termina, **Then** a classificação está
   registrada e a mensagem é encaminhada para atendimento humano visível à recepção —
   o sistema não inventa resposta para esses casos.
3. **Given** qualquer desfecho desta fatia, **When** se consulta o estado da reserva,
   **Then** o status da hospedagem não mudou (não há check-in, checkout nem cancelamento
   inferidos pela classificação).

---

### User Story 5 - Conteúdo da mensagem não vaza em log (Priority: P2)

Como titular dos dados e responsável pelo hotel, quero que o texto do que o hóspede
mandou nunca apareça em log operacional, inclusive no caminho de classificar e de
falhar a classificação, para um arquivo técnico não virar cópia da conversa.

**Why this priority**: Minimização de dados pessoais continua valendo neste passo. O
log pode registrar identificadores, a intenção resultante e o código de falha; o texto
não.

**Independent Test**: Pode ser testado nos desfechos de sucesso, serviço indisponível e
resposta inválida, inspecionando os logs: há identificadores, hotel, intenção (quando
houver) e códigos; não há o texto da mensagem nem a resposta completa do classificador
quando ela puder reproduzir o conteúdo.

**Acceptance Scenarios**:

1. **Given** classificação bem-sucedida, **When** o sistema registra log operacional,
   **Then** aparecem identificadores, a propriedade e a intenção resultante — e não o
   conteúdo da mensagem.
2. **Given** serviço indisponível ou resposta inválida, **When** o sistema registra log
   operacional, **Then** há código de resultado e identificadores, sem o texto do
   hóspede e sem copiar a resposta bruta do classificador para o log.

---

### Edge Cases

- Cada mensagem é classificada isoladamente. Duas mensagens seguidas do mesmo hóspede
  entregues fora de ordem não se bloqueiam; o MVP não garante ordem.
- Reprocessar um trabalho cuja mensagem já foi classificada com sucesso não gera segunda
  classificação, segundo encaminhamento humano nem segunda alteração observável.
- Esta fatia só consome o trabalho de classificação da conversa da estadia (mensagem de
  reserva hospedada). Não interpreta ficha da pré-chegada e não dispara coleta nem
  lembrete.
- Mensagem de mídia sem texto utilizável não chega a esta fatia (não gera trabalho de
  conversa na fatia anterior); se um trabalho órfão existir, não se inventa texto para
  classificar — encaminha a humano.
- Classificador devolve só parte dos três eixos, eixo com valor fora da taxonomia, ou
  conteúdo que não é o resultado estruturado: é resposta inválida (User Story 3), não
  “classificação parcial”.
- Serviço de classificação demora além do aceitável ou recusa a chamada: trata-se como
  indisponível (User Story 2), sem deixar o hóspede num limbo de retentativas de
  classificação.
- Encaminhamento humano desta fatia é visível ao perfil de recepção da propriedade.
  Não abre o chamado operacional completo (quarto, janela de preferência, Alert Center)
  — isso é a fatia de reclamação. Perfil operacional continua sem acesso a dado
  cadastral de hóspede.
- Hotel A não classifica nem encaminha conversa do hotel B: a mensagem e a pendência
  humana ficam no contexto da propriedade da reserva.
- Falha ao gravar o resultado da classificação: o trabalho permanece recuperável para
  nova tentativa; a mensagem original não é apagada.
- Esta fatia **não** responde ao hóspede, **não** consulta o catálogo para afirmar fato,
  **não** confirma pedido, **não** abre chamado de reclamação e **não** registra consumo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST classificar cada mensagem de estadia com trabalho pendente
  de classificação, de forma isolada, quanto à intenção, ao sentimento e à urgência.
- **FR-002**: A taxonomia de intenção MUST ser exatamente: dúvida geral, pedido de
  serviço, reclamação técnica, interesse comercial, pedido de checkout e fora de
  escopo. Valor fora dessa lista MUST ser tratado como resposta inválida.
- **FR-003**: O sentimento MUST ser um de: positivo, neutro, negativo. A urgência MUST
  ser uma de: baixa, média, alta. Valor fora desses conjuntos MUST ser tratado como
  resposta inválida.
- **FR-004**: Classificação válida MUST gravar os três eixos na mensagem e MUST
  preservar a resposta completa do classificador para auditoria posterior.
- **FR-005**: Classificação válida MUST NOT apagar nem alterar o conteúdo original da
  mensagem do hóspede.
- **FR-006**: Quando o serviço de classificação estiver indisponível, o sistema MUST
  preservar a mensagem, MUST NOT preencher os três eixos como se houvesse
  classificação, MUST encaminhar para atendimento humano visível à recepção da
  propriedade, e MUST NOT enviar resposta automática ao hóspede.
- **FR-007**: Quando a resposta do classificador for inválida (formato, eixos
  incompletos ou valores fora da taxonomia), o sistema MUST comportar-se como falha de
  classificação (encaminhamento humano, sem ramo automático) e MUST preservar a
  resposta completa recebida para auditoria.
- **FR-008**: Encaminhamento humano MUST ser perceptível no painel da recepção da
  propriedade da reserva; MUST NOT depender de uma notificação ter chegado a alguém.
- **FR-009**: Mensagem classificada com sucesso como dúvida geral, pedido de serviço ou
  reclamação técnica MUST ficar apenas registrada nesta fatia — MUST NOT gerar
  resposta automática, MUST NOT abrir chamado ou pedido, MUST NOT consultar o catálogo
  para redigir texto ao hóspede.
- **FR-010**: Mensagem classificada com sucesso como interesse comercial, pedido de
  checkout ou fora de escopo MUST ser encaminhada para atendimento humano visível à
  recepção, sem resposta inventada.
- **FR-011**: Conteúdo de mensagem e demais dados pessoais NUNCA MUST aparecer em log
  operacional; logs registram identificadores, códigos de resultado, a propriedade e,
  quando houver, a intenção resultante — nunca o texto e nunca a resposta bruta do
  classificador.
- **FR-012**: O trabalho pendente de classificação, após sucesso ou após encaminhamento
  humano por falha, MUST deixar de estar pendente de classificação. MUST NOT permanecer
  em retentativa indefinida contra o classificador.
- **FR-013**: Reprocessar mensagem já classificada com sucesso MUST NOT produzir segundo
  efeito observável.
- **FR-014**: Resolução e encaminhamento MUST considerar a propriedade da reserva;
  classificação de um hotel MUST NOT vazar para o histórico ou a fila de outro.
- **FR-015**: Esta fatia MUST NOT alterar o status da reserva, MUST NOT confirmar
  chegada ou saída, MUST NOT interpretar ficha da pré-chegada e MUST NOT disparar
  coleta, lembrete, pulso ou pesquisa.
- **FR-016**: A verificação desta fatia MUST ser possível sem o serviço real de
  classificação: um classificador controlado devolve resultados previsíveis (sucesso,
  indisponível, inválido) sem rede.
- **FR-017**: Se gravar o resultado (classificação ou encaminhamento humano) falhar, a
  mensagem original MUST permanecer e o trabalho MUST continuar recuperável.

### Key Entities

- **Mensagem recebida da estadia**: texto do hóspede já gravado no histórico da reserva
  hospedada. Nesta fatia ganha (ou não) classificação; o conteúdo original não muda.
- **Classificação**: decisão estruturada sobre uma mensagem, com três eixos —
  intenção, sentimento e urgência — mais a resposta completa do classificador,
  guardada para quando a decisão estiver errada.
- **Taxonomia de intenção**: as seis intenções do produto (dúvida geral, pedido de
  serviço, reclamação técnica, interesse comercial, pedido de checkout, fora de
  escopo). Só elas autorizam o ramo que as fatias seguintes vão executar; qualquer
  outra coisa é falha.
- **Encaminhamento humano**: pendência visível à recepção de que aquela mensagem
  precisa de pessoa. Nasce quando a classificação é impossível ou quando a intenção
  classificada não tem ramo automático nesta fase. Não é o chamado operacional
  completo da fatia de reclamação.
- **Trabalho pendente de classificação**: item da fila durável criado ao receber a
  mensagem da estadia. Esta fatia o conclui, por sucesso ou por encaminhamento humano.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das classificações válidas, a mensagem correspondente registra
  os três eixos (intenção, sentimento e urgência) e a resposta completa do
  classificador permanece recuperável para auditoria.
- **SC-002**: Em 100% dos casos de serviço indisponível, a mensagem original permanece
  no histórico, os três eixos estruturados não são preenchidos como classificação, a
  recepção da propriedade vê pendência humana, e o hóspede recebe 0 respostas
  automáticas nesta fatia.
- **SC-003**: Em 100% das respostas inválidas do classificador, o comportamento de
  SC-002 se repete e, adicionalmente, a resposta completa recebida fica preservada
  para auditoria.
- **SC-004**: Em 100% das classificações válidas de dúvida geral, pedido de serviço e
  reclamação técnica, esta fatia produz 0 respostas ao hóspede, 0 chamados e 0 pedidos.
- **SC-005**: Em 100% das classificações válidas de interesse comercial, pedido de
  checkout e fora de escopo, há encaminhamento humano visível à recepção e 0 respostas
  inventadas.
- **SC-006**: Em 100% dos desfechos (sucesso, indisponível, inválido), logs operacionais
  não contêm o conteúdo da mensagem nem a resposta bruta do classificador.
- **SC-007**: 0 mensagens de estadia já aceitas são perdidas por falha de classificação
  ou por reinicialização após o encaminhamento humano.
- **SC-008**: O caminho mensagem gravada → classificar → registrar eixos ou encaminhar
  a humano é verificável de ponta a ponta sem o serviço real de classificação.

## Assumptions

- A fatia F3.1 está concluída: mensagem de reserva hospedada já foi gravada e existe
  trabalho pendente de classificação na fila durável. Esta fatia consome esse trabalho;
  não recebe de novo a notificação do provedor.
- A fila durável é a mesma já usada nas fatias anteriores. Não se introduz mecanismo
  paralelo de fila.
- A taxonomia de intenção, sentimento e urgência é a já decidida no mapa de processos
  e na modelagem (seis intenções; sentimento positivo/neutro/negativo; urgência
  baixa/média/alta). Esta fatia não inventa sétima intenção.
- Classificação válida de dúvida geral, pedido de serviço e reclamação técnica fica
  apenas registrada: responder pelo catálogo é F3.3; registrar serviço com confirmação
  é F3.4; abrir chamado de reclamação com confirmação e janela de preferência é F3.5.
- Intenções sem fatia posterior de ramo próprio (interesse comercial, pedido de
  checkout, fora de escopo) são encaminhadas a humano já aqui, para a mensagem não
  ficar classificada e invisível.
- Encaminhamento humano desta fatia usa a superfície já existente da recepção (fila do
  dia / histórico da reserva), não cria o Alert Center da equipe operacional.
- Na primeira falha do classificador (indisponível ou inválido), escala-se a humano —
  não se espera o serviço voltar enquanto o hóspede não tem ninguém olhando.
- O classificador é substituível. Testes usam um classificador controlado (sucesso,
  indisponível, inválido) e nunca chamam o serviço real.
- Superfície de uso: comportamento observável no histórico da reserva, na classificação
  anexada, na fila de trabalho e no sinal visível à recepção. Ligar o protótipo React
  continua fora do critério de pronto.
- Ordem entre mensagens consecutivas não é garantida (Artigo XV). Cada classificação é
  independente.
- Confirmação ao hóspede antes de tramitar solicitação ou reclamação permanece nas
  fatias que criam essas entidades; falha de classificação nesta fatia não envia
  mensagem ao hóspede.
