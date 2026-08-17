# Feature Specification: Responder Dúvida a partir do Catálogo

**Feature Branch**: `012-responder-duvida-catalogo`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "Perguntas classificadas como dúvida geral são respondidas
automaticamente, usando exclusivamente os fatos cadastrados no catálogo da propriedade.
Quando a resposta não está no catálogo, o sistema não responde por conhecimento próprio:
informa o hóspede que a recepção vai atender e abre um chamado."
(backlog F3.3)

Restrições já decididas no projeto (entrada do specify): a resposta automática só é
permitida quando o fato está no catálogo da propriedade — conhecimento geral não é fonte
válida para falar em nome do hotel; na dúvida, um humano vê; gravar a mensagem de saída
antes de enviá-la; o aviso ao hóspede vem antes de abrir o chamado; conteúdo de mensagem
nunca vai para log; o catálogo de um hotel nunca é usado para outro; o sistema não se
integra ao sistema de gestão do hotel. Pedido de serviço, reclamação técnica com
confirmação e janela de preferência, e consumo faturável pertencem às fatias seguintes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dúvida coberta pelo catálogo recebe resposta automática (Priority: P1)

Como hóspede já hospedado que pergunta algo que o hotel publicou no catálogo (horário,
cardápio, serviço, programação ou regra), quero uma resposta imediata baseada só no que
a casa cadastrou, sem esperar uma pessoa, para o convite a perguntar das boas-vindas
ter efeito e a recepção não ser interrompida por o que já está escrito.

**Why this priority**: É o único ramo automático da estadia. Sem ele, classificar dúvida
geral não entrega valor ao hóspede. É também o depósito de controle de alucinação em
ação: o que não estiver no catálogo desta propriedade não pode ser afirmado.

**Independent Test**: Pode ser testado partindo de uma mensagem já classificada como
dúvida geral, com o catálogo ativo daquela propriedade contendo o fato perguntado, e
verificando que o hóspede recebe uma resposta automática, que essa resposta só afirma o
que está nesse catálogo, e que nenhum chamado foi aberto.

**Acceptance Scenarios**:

1. **Given** uma mensagem de estadia já classificada como dúvida geral e o catálogo
   ativo da propriedade da reserva contendo o fato perguntado, **When** o sistema
   responde, **Then** o hóspede recebe uma resposta automática e essa resposta afirma
   o fato a partir do catálogo daquela propriedade.
2. **Given** o desfecho do cenário anterior, **When** a recepção consulta o histórico
   da reserva, **Then** a resposta automática aparece no histórico, vinculada à mesma
   conversa, e nenhum chamado de acompanhamento foi aberto.
3. **Given** o catálogo ativo com o fato em uma redação diferente da pergunta do
   hóspede (por exemplo, o hóspede pergunta por um sinônimo do título cadastrado),
   **When** o sistema responde, **Then** a pergunta ainda é considerada coberta e a
   resposta automática usa o fato cadastrado — não escala a humano só por diferença
   de palavras.

---

### User Story 2 - Dúvida fora do catálogo avisa o hóspede e abre chamado (Priority: P1)

Como hóspede e como hotel, quero que uma pergunta que o catálogo não cobre não seja
respondida com conhecimento inventado: quero um aviso claro de que a recepção vai
atender, e quero que a pergunta vire chamado recuperável no painel, para o recado não
se perder se ninguém estiver olhando o chat naquele instante.

**Why this priority**: É o caso obrigatório da fatia e o que distingue “responder” de
“inventar”. Abrir o chamado sem avisar deixa o hóspede no silêncio; avisar sem chamado
deixa a omissão invisível. Os dois juntos são a regra.

**Independent Test**: Pode ser testado com dúvida geral classificada cujo fato não
existe no catálogo ativo da propriedade, e verificando: aviso ao hóspede de que a
recepção vai atender, chamado visível à recepção daquela propriedade, nenhuma
afirmação sobre a casa que não esteja no catálogo.

**Acceptance Scenarios**:

1. **Given** uma mensagem já classificada como dúvida geral e o catálogo ativo da
   propriedade sem o fato perguntado, **When** o sistema trata a pergunta, **Then** o
   hóspede recebe um aviso de que a recepção vai atender, e um chamado fica visível
   para a recepção da propriedade, recuperável no painel mesmo se uma notificação
   não tiver chegado a ninguém.
2. **Given** o mesmo caso, **When** se observa o que o hóspede recebeu, **Then** não
   há resposta que afirme horário, cardápio, serviço, programação ou regra ausentes
   do catálogo — o aviso não completa a lacuna com conhecimento próprio.
3. **Given** o aviso e o chamado do cenário 1, **When** se observa a ordem, **Then** o
   hóspede já foi informado antes de o chamado existir como pendência tramitada —
   confirmação primeiro, encaminhamento depois.

---

### User Story 3 - Resposta automática nunca cita fato ausente do catálogo (Priority: P1)

Como responsável pelo hotel, quero que o texto enviado ao hóspede no ramo automático
não contenha informação que o catálogo daquela propriedade não tenha publicado, mesmo
que o serviço de redação tente completar com conhecimento geral, para o hotel não
afirmar o que não cadastrou.

**Why this priority**: A cobertura (User Story 1) não basta se a redação puder
acrescentar fato. Este é o critério de aceite “a resposta automática não cita
informação ausente do catálogo”, e precisa ser testável à parte.

**Independent Test**: Pode ser testado com catálogo ativo conhecido (um conjunto
fechado de fatos) e uma redação controlada que tente incluir um fato fora desse
conjunto, verificando que esse texto não é enviado ao hóspede e que o caso segue o
desfecho de pergunta não coberta (aviso + chamado).

**Acceptance Scenarios**:

1. **Given** o catálogo ativo da propriedade com um conjunto fechado de fatos e uma
   redação que inclui pelo menos um fato fora desse conjunto, **When** o sistema
   decide o que enviar, **Then** esse texto não é entregue ao hóspede.
2. **Given** o desfecho do cenário anterior, **When** o fluxo continua, **Then** o
   hóspede recebe o aviso de que a recepção vai atender e o chamado fica visível à
   recepção — o mesmo desfecho da pergunta não coberta, não um meio-termo com texto
   parcialmente inventado.

---

### User Story 4 - Catálogo de outra propriedade nunca é usado (Priority: P1)

Como responsável pelos dados da casa, quero que a resposta (ou a decisão de não
responder) use somente o catálogo ativo da propriedade da reserva, nunca o de outro
hotel, para o sistema não falar pelo vizinho nem vazar fato de uma propriedade à
conversa de outra.

**Why this priority**: Multi-tenant já vale no cadastro do catálogo; esta fatia é a
primeira que afirma esses fatos em nome do hotel para o hóspede. Isolamento na
manutenção sem isolamento na resposta seria falha visível ao hóspede.

**Independent Test**: Pode ser testado com o mesmo tipo de pergunta em dois hotéis,
cada um com fato distinto no catálogo ativo, e verificando que cada hóspede recebe
(ou deixa de receber) apenas com base no catálogo da própria reserva.

**Acceptance Scenarios**:

1. **Given** o hotel A com o fato no catálogo ativo e o hotel B sem esse fato,
   **When** um hóspede da reserva do hotel A pergunta aquilo, **Then** a resposta
   automática usa o catálogo de A e não menciona o catálogo de B.
2. **Given** a mesma pergunta feita por um hóspede da reserva do hotel B, **When** o
   sistema trata a dúvida, **Then** não usa o fato cadastrado em A: o desfecho é o
   de pergunta não coberta (aviso + chamado no hotel B).
3. **Given** itens ativos no hotel A e inativos ou inexistentes no hotel B,
   **When** se responde uma dúvida do hotel B, **Then** nenhum item de A aparece na
   resposta nem é usado para decidir cobertura.

---

### User Story 5 - Falha ao redigir ou catálogo vazio escala para a recepção (Priority: P1)

Como hóspede e como hotel, quero que a indisponibilidade do serviço que redige a
resposta, ou um catálogo ativo vazio, não gere texto inventado nem deixe a pergunta
sumir: o hóspede é avisado e a recepção vê o chamado, para “na dúvida, um humano vê”
valer também quando não dá para consultar o catálogo com segurança.

**Why this priority**: Sem este caminho, a fatia só funciona no dia em que o serviço
de redação está no ar e o hotel já publicou fatos. Catálogo vazio é o estado inicial
da propriedade; tratar como “não coberto” é o desfecho honesto.

**Independent Test**: Pode ser testado com dúvida geral classificada e (a) serviço de
redação indisponível, ou (b) catálogo ativo vazio, verificando aviso ao hóspede,
chamado visível à recepção e zero afirmações sobre a propriedade.

**Acceptance Scenarios**:

1. **Given** uma dúvida geral classificada e o serviço que redige a resposta a partir
   do catálogo indisponível, **When** o trabalho é processado, **Then** o hóspede
   recebe o aviso de que a recepção vai atender, o chamado fica visível à recepção, e
   nenhuma resposta automática com fato da casa é enviada.
2. **Given** uma dúvida geral classificada e a propriedade sem nenhum item ativo no
   catálogo, **When** o sistema trata a pergunta, **Then** o desfecho é o de pergunta
   não coberta (aviso + chamado), não uma resposta improvisada.
3. **Given** qualquer um dos dois desfechos, **When** a aplicação é reiniciada em
   seguida, **Then** o aviso e o chamado permanecem recuperáveis — a falha não se
   converte em perda.

---

### User Story 6 - Conteúdo da mensagem não vaza em log (Priority: P2)

Como titular dos dados e responsável pelo hotel, quero que o texto da pergunta e o
texto da resposta automática nunca apareçam em log operacional, para um arquivo
técnico não virar cópia da conversa nem do catálogo recitado ao hóspede.

**Why this priority**: Minimização de dados pessoais continua valendo neste passo. O
log pode registrar identificadores, a propriedade, se a pergunta foi coberta ou não,
e códigos de resultado; o texto não.

**Independent Test**: Pode ser testado nos desfechos coberto, não coberto, redação
inválida e serviço indisponível, inspecionando os logs: há identificadores e
resultado; não há o texto da pergunta nem o da resposta.

**Acceptance Scenarios**:

1. **Given** uma resposta automática enviada com sucesso, **When** o sistema registra
   log operacional, **Then** aparecem identificadores, a propriedade e a indicação de
   pergunta coberta — e não o conteúdo da pergunta nem o da resposta.
2. **Given** pergunta não coberta, redação com fato ausente ou serviço indisponível,
   **When** o sistema registra log operacional, **Then** há código de resultado e
   identificadores, sem o texto do hóspede e sem o texto que teria sido enviado.

---

### Edge Cases

- Somente mensagem já classificada como dúvida geral entra nesta fatia. Pedido de
  serviço, reclamação técnica, interesse comercial, pedido de checkout e fora de
  escopo não são respondidos aqui.
- Item desativado do catálogo não conta como fato afirmável: a pergunta que só
  seria coberta por ele segue o desfecho de não coberta.
- Catálogo ativo vazio é pergunta não coberta, não erro de configuração visível ao
  hóspede.
- Redação que mistura fato cadastrado com fato ausente é recusada por inteiro (User
  Story 3); não se envia a parte “boa”.
- Reprocessar uma dúvida já respondida automaticamente não envia segunda resposta
  nem abre chamado.
- Reprocessar uma dúvida já encaminhada (aviso + chamado) não envia segundo aviso
  nem abre segundo chamado para a mesma mensagem.
- Falha ao gravar a resposta ou o chamado: a mensagem original do hóspede permanece;
  o trabalho continua recuperável; não se envia texto que ainda não foi gravado.
- Falha no envio depois de gravar: o dado permanece; o hóspede pode não receber na
  hora, mas a conversa e o chamado não se perdem.
- O aviso de que a recepção vai atender é recado padrão, não texto composto a partir
  de conhecimento geral.
- O chamado desta fatia é pendência da **recepção** da propriedade da reserva (quem
  o hóspede foi informado que vai atender). Não é o chamado operacional de
  manutenção da fatia de reclamação: não pede janela de preferência, não afirma que
  a manutenção foi acionada e não aparece como tarefa da equipe operacional.
- Perfil operacional continua sem acesso a dado cadastral de hóspede. A pendência é
  visível à recepção no painel da propriedade; não depende de notificação ter
  chegado.
- Hotel A não responde conversa do hotel B e não abre chamado no hotel B.
- Esta fatia **não** classifica intenção, **não** registra pedido de serviço, **não**
  abre chamado de reclamação técnica, **não** registra consumo, **não** altera o
  status da reserva e **não** dispara pulso, coleta nem lembrete.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST responder automaticamente mensagem de estadia já
  classificada como dúvida geral quando o catálogo ativo da propriedade da reserva
  cobrir o fato perguntado.
- **FR-002**: A resposta automática MUST usar exclusivamente os fatos ativos do
  catálogo da propriedade da reserva. MUST NOT afirmar fato com base em
  conhecimento geral, em catálogo de outro hotel ou em item desativado.
- **FR-003**: Diferença de redação entre a pergunta do hóspede e o título ou o texto
  cadastrado MUST NOT, por si só, fazer a pergunta ser tratada como não coberta
  quando o fato correspondente está no catálogo ativo.
- **FR-004**: Quando o catálogo ativo da propriedade não cobrir o fato perguntado, o
  sistema MUST NOT enviar resposta que afirme o fato, MUST informar o hóspede de que
  a recepção vai atender, e MUST abrir um chamado visível à recepção daquela
  propriedade.
- **FR-005**: O aviso ao hóspede de que a recepção vai atender MUST ocorrer antes de
  o chamado ser tramitado como pendência. O aviso MUST ser recado padrão — MUST NOT
  ser composto a partir de conhecimento geral para “preencher” a lacuna.
- **FR-006**: Chamado desta fatia MUST ser perceptível no painel da recepção da
  propriedade da reserva, recuperável pela leitura do painel; MUST NOT depender de
  uma notificação ter chegado a alguém.
- **FR-007**: Chamado desta fatia MUST NOT ser o chamado operacional de reclamação
  (sem janela de preferência, sem acionamento de manutenção, sem fila da equipe
  operacional).
- **FR-008**: Se a redação da resposta automática incluir fato ausente do catálogo
  ativo daquela propriedade, o sistema MUST NOT enviar esse texto e MUST seguir o
  desfecho de pergunta não coberta (aviso + chamado).
- **FR-009**: Catálogo ativo vazio MUST ser tratado como pergunta não coberta.
- **FR-010**: Indisponibilidade do serviço que redige a resposta a partir do
  catálogo MUST preservar a mensagem original, MUST NOT enviar resposta automática
  com fato da casa, MUST avisar o hóspede de que a recepção vai atender e MUST abrir
  o chamado visível à recepção.
- **FR-011**: Resposta automática enviada MUST ficar gravada no histórico da conversa
  da reserva antes de ser enviada ao hóspede.
- **FR-012**: Esta fatia MUST NOT responder nem abrir chamado para intenção diferente
  de dúvida geral.
- **FR-013**: Reprocessar mensagem já respondida automaticamente ou já encaminhada
  com aviso e chamado MUST NOT produzir segundo efeito observável (segunda resposta,
  segundo aviso ou segundo chamado).
- **FR-014**: Conteúdo da pergunta, conteúdo da resposta e demais dados pessoais
  NUNCA MUST aparecer em log operacional; logs registram identificadores, a
  propriedade e o resultado (coberta / não coberta / falha) — nunca o texto.
- **FR-015**: Resolução MUST considerar a propriedade da reserva; catálogo, resposta
  e chamado de um hotel MUST NOT vazar para o histórico ou a fila de outro.
- **FR-016**: Esta fatia MUST NOT alterar o status da reserva, MUST NOT confirmar
  chegada ou saída, MUST NOT registrar pedido de serviço, MUST NOT abrir chamado de
  reclamação técnica, MUST NOT registrar consumo e MUST NOT disparar coleta,
  lembrete, pulso ou pesquisa.
- **FR-017**: A verificação desta fatia MUST ser possível sem o serviço real de
  redação: um redator controlado devolve resultados previsíveis (resposta coberta,
  não coberta, texto com fato ausente, indisponível) sem rede.
- **FR-018**: Se gravar a resposta, o aviso ou o chamado falhar, a mensagem original
  MUST permanecer e o trabalho MUST continuar recuperável. MUST NOT enviar ao
  hóspede texto que ainda não foi gravado.

### Key Entities

- **Dúvida geral classificada**: mensagem de estadia já marcada com a intenção
  “dúvida geral”. É o único insumo desta fatia; as demais intenções não entram.
- **Catálogo ativo da propriedade**: conjunto dos fatos publicados (ativos) da
  propriedade da reserva, nas categorias já cadastradas. Única fonte a partir da
  qual se pode afirmar algo em nome da casa.
- **Resposta automática**: texto ao hóspede composto só a partir do catálogo ativo
  daquela propriedade, gravado no histórico da conversa e então enviado.
- **Aviso de encaminhamento**: recado padrão ao hóspede de que a recepção vai
  atender, usado quando a pergunta não é coberta, quando a redação não é segura ou
  quando o serviço de redação falha.
- **Chamado de dúvida não coberta**: pendência visível à recepção da propriedade,
  nascida depois do aviso ao hóspede, recuperável no painel. Não é o chamado
  operacional de manutenção da fatia de reclamação.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das dúvidas gerais cujo fato está no catálogo ativo da
  propriedade da reserva, o hóspede recebe uma resposta automática e 0 chamados são
  abertos para essa mensagem.
- **SC-002**: Em 100% das dúvidas gerais cujo fato não está no catálogo ativo, o
  hóspede recebe o aviso de que a recepção vai atender, a recepção da propriedade
  vê o chamado no painel, e 0 respostas afirmam fato ausente do catálogo.
- **SC-003**: Em 100% das redações que incluem fato ausente do catálogo ativo da
  propriedade, esse texto não é enviado; o desfecho observado é o de SC-002.
- **SC-004**: Em verificação com dois hotéis e fatos distintos, 0% das respostas ou
  chamados de um hotel usam o catálogo do outro.
- **SC-005**: Em 100% dos casos de serviço de redação indisponível ou de catálogo
  ativo vazio, há aviso ao hóspede, chamado visível à recepção e 0 respostas
  automáticas com fato da casa.
- **SC-006**: Em 100% das dúvidas não cobertas (incluindo catálogo vazio, redação
  com fato ausente e serviço de redação indisponível), o aviso ao hóspede precede
  a tramitação do chamado; 0 tramitam em silêncio.
- **SC-007**: Em 100% dos desfechos, logs operacionais não contêm o conteúdo da
  pergunta nem o da resposta.
- **SC-008**: 0 mensagens de dúvida geral já classificadas são perdidas por falha de
  redação, por catálogo vazio ou por reinicialização após o encaminhamento.
- **SC-009**: O caminho dúvida classificada → resposta automática ou aviso + chamado
  é verificável de ponta a ponta sem o serviço real de redação.
- **SC-010**: Reprocessar a mesma mensagem já concluída produz 0 segundos envios e 0
  segundos chamados.

## Assumptions

- As fatias F2.1 (catálogo da propriedade) e F3.2 (classificar a intenção) estão
  concluídas. Esta fatia parte de mensagem já classificada como dúvida geral e da
  consulta do catálogo ativo da propriedade da reserva.
- A consulta do catálogo ativo completo, já entregue na F2.1, é a fonte exclusiva
  de fatos afirmáveis. Item desativado não entra.
- “Coberta” significa: o fato necessário para responder está entre os itens ativos
  daquela propriedade, mesmo que o hóspede tenha usado outras palavras. “Não
  coberta” significa: esse fato não está lá — inclusive catálogo vazio.
- O aviso de encaminhamento é recado padrão (não redigido a partir de conhecimento
  geral). A resposta automática, quando houver, é o único texto composto a partir
  do catálogo.
- O chamado desta fatia é pendência da recepção, alinhado à frase que o hóspede
  recebe (“a recepção vai atender”). O chamado operacional com quarto, urgência e
  janela de preferência permanece na fatia de reclamação técnica (F3.5). As três
  origens de chamado do mapa de processos convergem na ideia de “humano vê e a
  fila não depende de notificação”; não obrigam esta fatia a reutilizar o fluxo
  completo de manutenção.
- Pedido de serviço (F3.4), reclamação técnica (F3.5) e consumo faturável (F3.7)
  não são executados aqui, mesmo que a classificação já exista.
- Superfície de uso: comportamento observável no histórico da conversa, na
  resposta ou aviso recebidos pelo hóspede, e na pendência visível à recepção.
  Ligar o protótipo React continua fora do critério de pronto.
- A verificação usa um redator controlado (resposta coberta, não coberta, texto
  com fato ausente, indisponível) e nunca chama o serviço real.
- Confirmação antes de tramitar vale para o desfecho não coberto: o hóspede é
  avisado antes de o chamado existir como pendência. No desfecho coberto não há
  chamado — a resposta automática é o atendimento.
- Ordem entre mensagens consecutivas não é garantida. Cada dúvida geral é tratada
  isoladamente.
- O hóspede acabou de escrever, então a resposta desta fatia ocorre dentro da
  janela de conversa já aberta; não se inicia conversa proativa nova.
- Preço estruturado de item vendável continua fora (adiado para F3.7). Responder
  dúvida sobre cardápio ou horário usa o texto do fato cadastrado, sem extrair
  valor a cobrar.
