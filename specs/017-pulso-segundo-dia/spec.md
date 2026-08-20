# Feature Specification: Pulso do Segundo Dia

**Feature Branch**: `017-pulso-segundo-dia`

**Created**: 2026-08-19

**Status**: Draft

**Input**: User description: "No segundo dia de estadia, o sistema envia uma única
pergunta sobre a experiência do hóspede. O envio é suprimido quando há chamado em
aberto para aquela estadia ou quando restam menos de vinte e quatro horas de
hospedagem, porque nesses casos ele deixa de servir ao propósito de permitir
correção. Resposta negativa gera chamado para a equipe."
(backlog F3.8)

Restrições já decididas no projeto (entrada do specify): não ser intrusivo é
requisito — um único pulso por estadia, sem lembrete se o hóspede ignorar; o
envio é suprimido com chamado em aberto ou sem tempo hábil de correção; o prazo
mínimo de estadia restante vem da configuração da propriedade, nunca de número
mágico; gravar antes de enviar; conteúdo de mensagem nunca vai para log; na
dúvida, um humano vê; confirmação ao hóspede antes de tramitar chamado; a fila
do painel é a fonte da verdade; o sistema não se integra ao sistema de gestão
do hotel e portanto não infere checkout. Pesquisa de avaliação na saída,
consentimento para comunicações futuras e lista de pedidos feitos pelo chat
pertencem a fatias seguintes.

## Clarifications

### Session 2026-08-19

- Q: Quando o hóspede responde ao pulso e a classificação marca o sentimento como neutro, o que o sistema deve fazer? → A: Mesmo caminho do positivo: grava a avaliação, reconhecimento breve, sem chamado. O recado de reconhecimento é **o mesmo** para positivo e neutro e **não** afirma satisfação (nada de "que bom que está gostando"). Irreconhecível continua na leitura humana; só o negativo abre chamado.
- Q: Quando a primeira mensagem depois do pulso é claramente um pedido de serviço ou uma dúvida do catálogo, o sistema deve tratá-la só como resposta ao pulso? → A: Não. Intenção operacional clara (dúvida, pedido, reclamação técnica) segue o fluxo já existente e também encerra o pulso com a polaridade. **No máximo uma resposta ao hóspede por mensagem.** Se o fluxo operacional já respondeu (confirmação de pedido, resposta do catálogo, abertura de chamado), o pulso encerra em **silêncio**: grava o sentimento e não manda o reconhecimento. O recado "obrigado por responder" só sai quando nada mais respondeu. No máximo um chamado de reclamação por mensagem.
- Q: Quando o pulso é quem responde a uma avaliação negativa, a confirmação deve perguntar horário de preferência para ir ao quarto? → A: Não. Só confirma recebimento e acionamento, **sem** perguntar horário. O recado MUST dizer o que vai acontecer (equipe avisada, alguém vai falar com o hóspede), não só que a mensagem chegou. Problema de quarto continua na reclamação técnica, que já pergunta horário; não nasce ramo novo para detectar isso no pulso. Confirmação antes de tramitar permanece.
- Q: O pulso também deve ser suprimido quando a estadia já está sinalizada para a recepção atender (dúvida não coberta, classificação falhou), mesmo sem reclamação aberta? → A: Não. Só reclamação ainda não resolvida suprime. O sinal de leitura humana não tem fechamento claro e travaria o pulso o resto da estadia após uma única dúvida fora do catálogo. Pedido de toalha e consumo pendente também não suprimem.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - No segundo dia, uma única pergunta sobre a experiência (Priority: P1)

Como hóspede já hospedado no segundo dia de estadia, com tempo pela frente e
sem chamado de reclamação em aberto, quero receber **uma única pergunta** sobre
como está sendo a experiência, para eu poder falar de um incômodo enquanto o
hotel ainda tem como corrigir — e não só na saída, quando já não dá.

**Why this priority**: É o item de maior valor comercial da estadia: insatisfação
descoberta no checkout (ou na avaliação pública) não se recupera. O pulso só
existe se chegar no momento certo e uma vez.

**Independent Test**: Pode ser testado com uma reserva hospedada cujo check-in
real já foi no dia civil anterior, com tempo restante acima do mínimo da
propriedade e sem reclamação aberta, rodando a verificação de pulso e
conferindo: exatamente uma pergunta enviada, gravada no histórico daquela
reserva, sem oferta comercial e sem segunda pergunta no mesmo recado.

**Acceptance Scenarios**:

1. **Given** uma reserva hospedada cujo instante real de entrada caiu no dia
   civil anterior, com horas restantes de estadia prevista iguais ou acima do
   mínimo da propriedade e sem reclamação em aberto, **When** o sistema verifica
   o pulso, **Then** o hóspede recebe exatamente uma pergunta sobre a
   experiência, gravada no histórico da mesma reserva.
2. **Given** o texto dessa pergunta, **When** ele é inspecionado, **Then** é uma
   única pergunta, em linguagem de cuidado, que convida a uma resposta curta;
   não contém oferta comercial, não pede nota numérica obrigatória, não pede
   consentimento de marketing, não usa as palavras "extrato" nem "conta", e o
   único dado pessoal permitido no corpo é o primeiro nome.
3. **Given** uma reserva ainda no mesmo dia civil do check-in real, **When** o
   sistema verifica o pulso, **Then** nenhuma pergunta é enviada.

---

### User Story 2 - Chamado de reclamação em aberto suprime o pulso (Priority: P1)

Como hóspede que já abriu uma reclamação e ainda espera o conserto, não quero
receber "como está sendo sua estadia?" — isso soa a deboche. Como hotel, quero
que o sistema **não** pergunte o que a própria operação já sabe.

**Why this priority**: Timing errado destrói o produto. A jornada registra
explicitamente que pulso com chamado aberto demonstra que o sistema ignora o
que a casa já sabe.

**Independent Test**: Pode ser testado com a mesma estadia elegível por dia e
por tempo restante, porém com uma reclamação ainda não resolvida, verificando
zero envios de pulso.

**Acceptance Scenarios**:

1. **Given** uma estadia no segundo dia, com tempo restante suficiente, e uma
   solicitação do tipo reclamação ainda não resolvida, **When** o sistema
   verifica o pulso, **Then** a pergunta **não** é enviada.
2. **Given** somente pedido de serviço sem cobrança, consumo faturável em
   aberto, ou estadia sinalizada para leitura humana — **sem** reclamação
   aberta —, **When** a verificação ocorre nas mesmas demais condições de
   elegibilidade, **Then** o pulso **é** enviado. Toalha, item de bar ou uma
   dúvida antiga fora do catálogo não são o conserto em aberto.
3. **Given** a reclamação da estadia já resolvida, e a estadia ainda elegível
   por dia e por tempo restante, e o pulso ainda não enviado, **When** o
   sistema verifica de novo, **Then** a pergunta é enviada — a supressão
   atrasou o primeiro envio; não o cancelou para sempre.

---

### User Story 3 - Sem tempo hábil, o pulso não sai (Priority: P1)

Como hotel, não quero perguntar "como está sendo?" quando já não dá tempo de
corrigir: aí o pulso vira pesquisa antecipada, função que a saída já cumpre.

**Why this priority**: A decisão de escopo da jornada é esta. Sem a trava, o
instrumento de recuperação vira ruído na véspera do checkout.

**Independent Test**: Pode ser testado com estadia no segundo dia, sem
reclamação aberta, porém com horas restantes abaixo do mínimo da propriedade,
verificando zero envios.

**Acceptance Scenarios**:

1. **Given** uma estadia no segundo dia ou depois, sem reclamação aberta, cuja
   data prevista de saída deixa menos horas restantes do que o mínimo
   configurado na propriedade, **When** o sistema verifica o pulso, **Then** a
   pergunta **não** é enviada.
2. **Given** uma estadia de uma noite (entrada num dia e saída prevista no dia
   seguinte), **When** chega o segundo dia civil, **Then** o pulso é suprimido
   por tempo restante — não há janela de correção.
3. **Given** duas propriedades com mínimos diferentes, **When** a mesma
   combinação de datas é verificada em cada uma, **Then** a que tem mínimo
   menor pode enviar e a que tem mínimo maior suprime, sem número fixo na
   regra.

---

### User Story 4 - Nunca duas vezes na mesma estadia (Priority: P1)

Como hóspede, quero receber o pulso no máximo uma vez, mesmo que a verificação
rode de novo, o envio tenha falhado depois de gravar, ou dois processos
verifiquem ao mesmo tempo.

**Why this priority**: Não ser intrusivo é requisito. Segunda pergunta transforma
cuidado em insistência e gasta mensagem iniciada pelo hotel.

**Independent Test**: Pode ser testado enviando o pulso uma vez e rodando a
verificação de novo, inclusive em paralelo, verificando exatamente um recado
de pulso naquela reserva.

**Acceptance Scenarios**:

1. **Given** uma estadia que já recebeu o pulso, **When** a verificação ocorre
   de novo no dia seguinte ainda com tempo restante, **Then** nenhuma segunda
   pergunta é enviada.
2. **Given** duas verificações simultâneas da mesma estadia ainda sem pulso,
   **When** ambas concluem, **Then** existe exatamente um recado de pulso.
3. **Given** o hóspede que recebeu o pulso e não respondeu, **When** o silêncio
   persiste, **Then** o sistema **não** envia lembrete nem segunda pergunta.

---

### User Story 5 - Resposta negativa vira chamado, com confirmação antes (Priority: P1)

Como hóspede que responde ao pulso dizendo que a estadia não vai bem, quero
confirmação imediata de que fui ouvido e de que a equipe vai atuar, e quero
que isso apareça para a operação — para eu não ligar ao balcão e para o hotel
ainda ter tempo de recuperar.

**Why this priority**: Sem chamado, a resposta negativa some no chat. Sem
confirmação antes da tramitação, o hóspede irritado espera em silêncio.

**Independent Test**: Pode ser testado com um pulso já enviado e uma resposta
classificada como negativa, verificando: confirmação no histórico **antes** de
o chamado existir no Alert Center; exatamente um chamado de reclamação
vinculado àquela mensagem; visível na fila operacional da propriedade.

**Acceptance Scenarios**:

1. **Given** um pulso já enviado e ainda sem resposta registrada, **When** o
   hóspede responde com insatisfação (sentimento negativo), **Then** nasce
   exatamente uma solicitação do tipo reclamação naquela reserva, vinculada à
   mensagem da resposta, visível no Alert Center, sem valor a cobrar.
2. **Given** o desfecho do cenário anterior, **When** se observa a ordem,
   **Then** a confirmação ao hóspede já está no histórico da conversa no
   instante em que o chamado passa a existir como pendência — zero respostas
   negativas tramitam em silêncio.
3. **Given** o texto da confirmação, **When** ele é lido, **Then** reconhece o
   desconforto **e diz o que vai acontecer** (a recepção foi avisada e alguém
   vai falar com o hóspede); **não** pergunta horário para ir ao quarto; não
   promete prazo de conserto; não afirma fato da casa que não foi cadastrado;
   não usa "extrato" nem "conta".
4. **Given** a mesma resposta negativa, **When** a avaliação da estadia é
   consultada, **Then** existe um registro de pulso daquela reserva com a
   origem de segundo dia, o instante da resposta e o comentário preservado.
5. **Given** o texto "não estou gostando" sem descrever defeito de quarto,
   **When** a confirmação de pulso é montada, **Then** não há pergunta de
   visita ao quarto — problema de manutenção continua no fluxo de reclamação
   técnica, que já pergunta horário quando for o caso.

---

### User Story 6 - Resposta positiva, neutra ou silêncio não geram chamado nem insistência (Priority: P1)

Como hóspede que responde que está tudo bem, que responde de forma neutra, ou
que simplesmente ignora a pergunta, não quero chamado aberto à toa, não quero
um recado que finja que estou satisfeito, nem uma segunda mensagem cobrando
avaliação.

**Why this priority**: Chamado falso consome a equipe. Lembrete viola o teto de
não ser intrusivo. Afirmar satisfação no neutro soa falso e quebra a
confiança. O pulso é instrumento de recuperação, não pesquisa obrigatória.

**Independent Test**: Pode ser testado com resposta positiva, com resposta
neutra e com silêncio, verificando: avaliação registrada só quando houve
resposta classificada; o reconhecimento (quando houver) é o mesmo texto nos
dois sentimentos e não afirma que a estadia está boa; zero chamados; zero
mensagens extras de cobrança.

**Acceptance Scenarios**:

1. **Given** um pulso aguardando resposta, **When** o hóspede responde com
   sentimento positivo **ou** neutro, **Then** a avaliação de pulso é
   registrada, o hóspede recebe um reconhecimento breve de que a resposta
   chegou, e **não** nasce chamado.
2. **Given** os desfechos positivo e neutro, **When** se comparam os recados de
   reconhecimento, **Then** o texto é o **mesmo** nos dois casos — agradece a
   resposta e convida a chamar se precisar — e **não** afirma que a estadia
   está boa nem que o hóspede está gostando.
3. **Given** um pulso enviado, **When** o hóspede não responde, **Then** não
   existe avaliação de pulso daquela reserva, não nasce chamado e não sai
   lembrete.
4. **Given** a resposta positiva ou neutra já registrada, **When** o hóspede
   escreve de novo (dúvida, pedido ou reclamação), **Then** essa mensagem segue
   o atendimento normal da estadia — o pulso já foi respondido e não intercepta
   o restante da conversa.

---

### User Story 6b - Pedido ou dúvida na janela do pulso não é engolido (Priority: P1)

Como hóspede que recebeu o pulso e, em vez de avaliar a estadia, pede uma
toalha ou pergunta o horário do café, quero que esse pedido ou dúvida seja
atendido como sempre — e quero **um** recado só, não um "obrigado por
responder" empilhado na confirmação que já veio.

**Why this priority**: Engolir toalha ou dúvida na micro-pesquisa falha o
operacional. Dois recados na mesma mensagem é ruído e gasta a janela de
conversa. O pulso ainda precisa encerrar, senão a interceptação nunca fecha.

**Independent Test**: Pode ser testado com pulso aguardando resposta e uma
mensagem classificada como pedido de serviço ou dúvida coberta pelo catálogo,
verificando: o fluxo operacional ocorre; nasce exatamente um recado ao
hóspede (o operacional); a avaliação de pulso é gravada; zero reconhecimento
de pulso extra.

**Acceptance Scenarios**:

1. **Given** um pulso enviado e ainda sem resposta, **When** o hóspede pede um
   serviço ou faz uma dúvida que o catálogo cobre, **Then** o fluxo já
   existente de pedido ou de dúvida corre normalmente, e a avaliação de pulso
   é registrada com o sentimento daquela mensagem.
2. **Given** o desfecho do cenário 1, **When** se conta o que o hóspede
   recebeu, **Then** existe exatamente um recado — a confirmação do pedido ou
   a resposta do catálogo — e **não** existe o reconhecimento "obrigado por
   responder".
3. **Given** um pulso aguardando e uma reclamação técnica na primeira
   mensagem, **When** o chamado de reclamação é aberto com a confirmação já
   existente, **Then** o pulso grava o sentimento, **não** abre segundo
   chamado e **não** manda segundo recado.
4. **Given** um pulso aguardando e uma mensagem que **não** disparou recado
   operacional (só avaliou a experiência), **When** o sentimento é positivo ou
   neutro, **Then** sai o reconhecimento único de pulso — porque nada mais
   respondeu.

---

### User Story 7 - Resposta irreconhecível vai para humano, sem inventar polaridade (Priority: P1)

Como hotel, quando não for possível dizer se a resposta ao pulso é positiva,
neutra ou negativa — texto ambíguo, serviço de classificação indisponível ou
formato inválido — quero que um humano veja a mensagem, sem chamado automático
inventado e sem o sistema fingir que entendeu. Sentimento **neutro** classificado
com sucesso não entra neste ramo.

**Why this priority**: Na dúvida, um humano vê. Polaridade inventada ou descarte
silencioso são os dois erros que esta regra existe para impedir.

**Independent Test**: Pode ser testado com resposta de pulso que o classificador
não polariza, e com serviço de classificação indisponível, verificando:
mensagem preservada, visível para atendimento humano da recepção, zero chamado
automático de recuperação, zero segunda pergunta ao hóspede.

**Acceptance Scenarios**:

1. **Given** uma resposta ao pulso cuja polaridade não é reconhecida, **When**
   o sistema a interpreta, **Then** a mensagem permanece, a recepção vê que
   precisa de leitura humana, e não nasce chamado automático.
2. **Given** o serviço de classificação indisponível ou resposta em formato
   inválido, **When** chega a resposta ao pulso, **Then** o mesmo desfecho:
   preservar, sinalizar humano, não inventar positivo nem negativo.
3. **Given** esse desfecho, **When** o hóspede consulta a conversa, **Then**
   não recebe pergunta nova de pulso nem recado que afirme ter entendido a
   avaliação.

---

### User Story 8 - O mínimo de horas restantes é da propriedade (Priority: P1)

Como gestão, quero que o tempo mínimo para ainda valer a pena perguntar seja
configuração da propriedade, não regra escondida, para um hotel de passagem
curta e um de estadia longa não viverem o mesmo corte.

**Why this priority**: Parâmetro operacional não é constante. O backlog e a
constituição já nomeiam esse prazo.

**Independent Test**: Pode ser testado alterando o mínimo da propriedade e
rodando a verificação, sem mudar a regra, conferindo mudança no desfecho;
ausência da chave não envia e não inventa 24.

**Acceptance Scenarios**:

1. **Given** o mínimo da propriedade alterado, **When** a verificação seguinte
   avalia a mesma estadia, **Then** o desfecho (enviar ou suprimir) acompanha o
   novo valor, sem mudança de regra.
2. **Given** uma propriedade sem o prazo mínimo configurado, **When** a
   verificação ocorre, **Then** o pulso **não** é enviado para as estadias
   daquela propriedade, o fato fica registrado de forma operacional (sem o
   texto da mensagem), e nenhum número é assumido no lugar.
3. **Given** uma propriedade nova na instalação inicial, **When** ela nasce,
   **Then** o prazo mínimo já está configurado (valor padrão da instalação).

---

### User Story 9 - Falha de envio não duplica nem desfaz a estadia (Priority: P1)

Como hotel, quero que a intenção de enviar o pulso fique gravada **antes** da
tentativa de entrega. Se a entrega falhar ainda dentro da janela útil, quero
retomar **o mesmo** envio — não uma segunda pergunta nova. Se a janela útil já
fechou, paro: perda do pulso é tolerável; disparar fora de hora não é.

**Why this priority**: Gravar antes de enviar vale para toda mensagem. O
catálogo de eventos desta fatia admite perder o pulso; não admite insistir
fora da janela de correção.

**Independent Test**: Pode ser testado gravando o pulso, falhando o envio,
retomando ainda elegível (um recado) e retomando já sem tempo restante (zero
novo recado, estadia intacta).

**Acceptance Scenarios**:

1. **Given** o pulso gravado e o envio falho, a estadia ainda elegível, **When**
   o trabalho é retomado, **Then** tenta-se de novo **o mesmo** recado; o
   hóspede não recebe uma segunda pergunta distinta.
2. **Given** o pulso ainda não entregue e a estadia já sem tempo restante (ou
   já com reclamação aberta, ou já encerrada), **When** a retomada ocorre,
   **Then** não há nova tentativa ao hóspede; a reserva permanece no estado em
   que estava; nada é desfeito.
3. **Given** falha na gravação da intenção de enviar, **When** o ciclo termina,
   **Then** o hóspede não recebe pergunta de pulso que ainda não foi gravada.

---

### User Story 10 - Hotel A não pulsa o hóspede do hotel B (Priority: P1)

Como hotel, quero que só as minhas estadias entrem na verificação, com o meu
prazo e as minhas reclamações.

**Why this priority**: Isolamento entre propriedades vale desde a primeira linha.

**Independent Test**: Pode ser testado com duas propriedades, uma estadia
elegível em cada, verificando que prazo, envio, avaliação e chamado não
atravessam.

**Acceptance Scenarios**:

1. **Given** duas propriedades, **When** o pulso é verificado, **Then** cada
   estadia só é avaliada com o prazo e as reclamações da própria propriedade.
2. **Given** um chamado aberto no hotel A, **When** o hotel B verifica uma
   estadia no mesmo telefone, **Then** o chamado de A **não** suprime o pulso
   de B.

---

### User Story 11 - Conteúdo da mensagem não vaza em log (Priority: P2)

Como titular dos dados, quero que a pergunta, a resposta e a confirmação nunca
apareçam em log operacional.

**Why this priority**: Minimização de dados pessoais. Log registra
identificadores e resultado, nunca o texto.

**Independent Test**: Pode ser testado nos desfechos enviar, suprimir, responder
e falhar, inspecionando logs: identificadores e código; zero texto.

**Acceptance Scenarios**:

1. **Given** pulso enviado, suprimido, respondido ou com falha de envio,
   **When** o sistema registra log operacional, **Then** há identificadores, a
   propriedade e o resultado — e não o texto da pergunta, da resposta nem da
   confirmação.

---

### Edge Cases

- O eixo do "segundo dia" é o **instante real do check-in**, nunca a data
  prevista de entrada. Chegada antecipada ou atrasada não usa o calendário da
  reserva original. Lição já registrada na confirmação de chegada.
- Data prevista de saída é uma **data civil, sem hora**. As horas restantes são
  `24 × (data prevista de saída − hoje)`, em dias inteiros. Saída prevista hoje
  → 0 horas. Saída prevista amanhã → 24 horas. O sistema **não** inventa horário
  de checkout a partir do texto de boas-vindas.
- Reserva que ainda não está hospedada, já encerrada ou cancelada fica fora da
  verificação, mesmo que as datas coincidam com o segundo dia.
- "Chamado em aberto" nesta fatia é solicitação do tipo **reclamação ainda não
  resolvida** daquela reserva. Pedido de toalha, consumo pendente de lançamento
  e sinalização de leitura humana (dúvida não coberta, classificação falha)
  **não** suprimem. Reclamação de outra reserva do mesmo telefone não suprime.
- Reclamação aberta no segundo dia **atrasa** o primeiro envio; se depois for
  resolvida e a estadia ainda tiver tempo restante e ainda não tiver pulso, o
  envio ocorre. Não é uma janela de um único dia civil que, uma vez perdida,
  nunca volta — o propósito é recuperar enquanto dá tempo.
- Falha da verificação periódica (não rodou no dia) é perda tolerável se, quando
  voltar a rodar, a estadia já não for elegível. Não há compensação com recado
  atrasado fora da janela.
- A primeira mensagem do hóspede **depois** de um pulso enviado e ainda sem
  resposta encerra o pulso (grava polaridade) **e**, se a intenção for dúvida,
  pedido ou reclamação técnica, segue o fluxo operacional já existente. Não há
  ramo paralelo que engula toalha ou café. Depois do desfecho, as mensagens
  seguintes voltam ao atendimento normal.
- **No máximo um recado ao hóspede por mensagem de entrada.** Se o fluxo
  operacional já enviou confirmação de pedido, resposta de catálogo, aviso de
  dúvida não coberta ou confirmação de chamado, o pulso encerra em silêncio:
  grava o sentimento e **não** manda o reconhecimento. O "obrigado por
  responder" só sai quando aquele turno não produziu nenhum outro recado.
- Resposta negativa abre chamado de recuperação **somente se** esta mensagem
  ainda não abriu uma reclamação. A mesma mensagem **não** abre segundo
  chamado. Se o recado operacional já ocupou o turno, a confirmação extra de
  "equipe acionada" do pulso **não** sai — o hóspede já recebeu uma resposta.
- Confirmação de pulso negativo **não** pergunta horário de visita ao quarto.
  "Não estou gostando" não é ordem de manutenção. Defeito de quarto segue o
  fluxo de reclamação técnica, que já pergunta horário. Não nasce classificador
  extra no pulso para distinguir os dois. O recado de pulso diz o próximo passo
  (recepção avisada, alguém fala com o hóspede), não só o recebimento.
- Avaliação de pulso é no máximo uma por reserva. Segunda interpretação da
  mesma origem não cria segunda avaliação.
- Polaridade vem do serviço de classificação já usado na estadia: sentimento
  `positivo`, `neutro` ou `negativo`. Positivo e neutro seguem o **mesmo**
  caminho (avaliação + reconhecimento idêntico, sem chamado). Só `negativo`
  abre chamado. Irreconhecível, serviço indisponível ou formato inválido **não**
  são neutro — vão para leitura humana. Esta fatia **não** exige nota de 1 a 5
  na pergunta. Nota na avaliação de pulso pode permanecer vazia.
- O reconhecimento de positivo/neutro agradece a resposta e deixa o canal
  aberto; **não** afirma satisfação. Um recado do tipo "que bom que está
  gostando" é recusado pelo aceite.
- O pulso é mensagem **iniciada pelo hotel**. Não contém oferta comercial (isso
  reclassifica o recado como marketing e destrói a premissa de custo). Variável
  de recado iniciado pelo hotel não carrega texto longo estruturado, quebra de
  linha, tabulação, mais de quatro espaços seguidos nem vazio.
- Horário de relógio em que a verificação roda segue a cadência já usada nas
  varreduras da propriedade (silêncio, recuperação de boas-vindas). Esta fatia
  **não** introduz janela de silêncio noturno. Se a verificação cair de
  madrugada, o envio pode ocorrer de madrugada — limitação honesta; horário
  nobre seria parâmetro novo e fica fora.
- Pesquisa de checkout, consentimento para comunicações futuras, lista de
  pedidos feitos pelo chat, tela de indicadores de satisfação e edição dos
  prazos no painel **não** fazem parte desta fatia.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST verificar periodicamente, por propriedade, as
  reservas hospedadas e aplicar as regras de elegibilidade, envio único,
  supressão e interpretação de resposta descritas nesta spec.
- **FR-002**: O pulso MUST ser enviado somente quando **todas** as condições
  forem verdadeiras: reserva hospedada daquela propriedade; o dia civil atual é
  posterior ao dia civil do instante real de entrada; as horas restantes de
  estadia prevista são iguais ou superiores ao mínimo da propriedade; não há
  reclamação em aberto naquela reserva; aquela reserva ainda não tem pulso
  gravado.
- **FR-003**: O mínimo de horas restantes MUST ser lido da configuração da
  propriedade (`horas_minimas_para_pulso`). MUST NOT ser constante de regra de
  negócio. Propriedade nova MUST nascer com a chave já configurada. Ausência da
  chave MUST impedir o envio para aquela propriedade de forma explícita, sem
  assumir número embutido.
- **FR-004**: Horas restantes MUST ser calculadas como
  `24 × (data prevista de saída − data civil de hoje)`. MUST NOT usar horário
  inventado de checkout.
- **FR-005**: Reclamação em aberto MUST significar solicitação do tipo
  reclamação daquela reserva ainda não resolvida. MUST NOT suprimir por pedido
  de serviço sem cobrança, por consumo pendente de lançamento, nem por estadia
  apenas sinalizada para leitura humana (dúvida não coberta, classificação
  falha ou formato inválido).
- **FR-006**: Cada reserva MUST receber no máximo um pulso. Unicidade MUST
  valer inclusive sob verificação simultânea. MUST NOT haver lembrete nem
  segunda pergunta se o hóspede não responder.
- **FR-007**: O recado de pulso MUST ser uma única pergunta sobre a experiência,
  convidando resposta curta. MUST NOT conter oferta comercial, pedido de
  consentimento, lista de pedidos, as palavras "extrato" ou "conta". O único
  dado pessoal permitido no corpo é o primeiro nome.
- **FR-008**: A intenção de enviar o pulso MUST ser gravada no histórico da
  reserva **antes** da tentativa de entrega. Falha de envio MUST NOT desfazer o
  check-in nem gerar um segundo pulso distinto. Retomada MUST reenviar o mesmo
  recado somente enquanto a estadia continuar elegível; fora da janela, MUST
  parar.
- **FR-009**: A primeira mensagem do hóspede após pulso enviado e ainda sem
  resposta MUST encerrar o pulso (registrar polaridade). Se a intenção for
  dúvida geral, pedido de serviço ou reclamação técnica, os fluxos já
  existentes MUST correr; esta fatia MUST NOT engolir esses ramos.
- **FR-009b**: Cada mensagem de entrada do hóspede MUST gerar no máximo um
  recado de saída. Se o fluxo operacional já produziu recado ao hóspede
  (confirmação de pedido, resposta do catálogo, aviso de dúvida não coberta
  ou confirmação de chamado), o pulso MUST gravar o sentimento e MUST NOT
  enviar reconhecimento nem segunda confirmação. O reconhecimento de pulso
  MUST sair somente quando aquele turno não tiver produzido outro recado.
- **FR-010**: Resposta com sentimento negativo MUST registrar a avaliação de
  pulso da reserva (origem segundo dia, instante, comentário). MUST abrir
  exatamente uma solicitação do tipo reclamação vinculada àquela mensagem,
  visível no Alert Center, sem valor a cobrar — **exceto** se esta mensagem
  já tiver aberto uma reclamação pelo fluxo existente, caso em que MUST NOT
  abrir segunda.
- **FR-011**: Quando o pulso é quem responde ao hóspede (nenhum recado
  operacional no turno) e o sentimento é negativo, o hóspede MUST receber
  confirmação **antes** de o chamado existir como pendência. A confirmação
  MUST dizer o que vai acontecer: a recepção foi avisada e alguém vai falar
  com o hóspede — MUST NOT limitar-se a "recebemos sua mensagem". MUST NOT
  perguntar horário para ir ao quarto. MUST NOT criar ramo que detecte se o
  texto descreve defeito de quarto (isso permanece na reclamação técnica).
  MUST NOT prometer prazo de conserto nem afirmar fato não cadastrado. A
  confirmação MUST ser gravada no histórico antes de ser enviada. Quando
  outro recado já saiu no turno, MUST NOT haver segunda confirmação de pulso.
- **FR-012**: Resposta com sentimento positivo **ou** neutro MUST registrar a
  avaliação de pulso e MUST NOT abrir chamado. Quando nenhum outro recado
  saiu no turno, MUST enviar o reconhecimento breve de recebimento. O texto
  MUST ser o **mesmo** para positivo e neutro. MUST NOT afirmar que a estadia
  está boa, que o hóspede está gostando ou qualquer satisfação inferida.
  Quando outro recado já saiu no turno, MUST NOT enviar esse reconhecimento.
- **FR-013**: Silêncio após o pulso MUST NOT criar avaliação, MUST NOT abrir
  chamado e MUST NOT gerar lembrete.
- **FR-014**: Polaridade irreconhecível, serviço de classificação indisponível
  ou formato inválido MUST preservar a mensagem, MUST sinalizar atendimento
  humano à recepção da propriedade, MUST NOT inventar polaridade, MUST NOT
  abrir chamado automático de recuperação e MUST NOT enviar segunda pergunta
  de pulso.
- **FR-015**: Depois de a resposta ao pulso ter desfecho (avaliação
  registrada ou desvio para humano), mensagens seguintes da mesma reserva MUST
  voltar ao atendimento normal da estadia.
- **FR-016**: Avaliação de pulso MUST ser no máximo uma por reserva. MUST
  distinguir-se da avaliação de checkout, que esta fatia não cria.
- **FR-017**: Resolução MUST considerar o hotel da reserva: prazo, envio,
  supressão, avaliação e chamado de um hotel MUST NOT vazar para outro.
- **FR-018**: Conteúdo da pergunta, da resposta e da confirmação NUNCA MUST
  aparecer em log operacional; logs registram identificadores, a propriedade e
  o resultado — nunca o texto.
- **FR-019**: Esta fatia MUST NOT confirmar chegada ou saída, MUST NOT alterar
  o status da reserva, MUST NOT reimplementar dúvida, pedido ou consumo (usa
  os fluxos já existentes quando a intenção for essa), MUST NOT coletar
  consentimento, MUST NOT apresentar lista de pedidos feitos pelo chat, e
  MUST NOT oferecer tela nova de edição de prazos.
- **FR-020**: A verificação desta fatia MUST ser possível sem o serviço real de
  mensageria e sem o serviço real de classificação: envio e polaridade
  controlados devolvem sucesso, falha, positivo, neutro, negativo ou
  irreconhecível previsíveis, sem rede.

### Key Entities

- **Pulso do segundo dia**: única pergunta proativa sobre a experiência,
  enviada no máximo uma vez por estadia hospedada, quando o dia civil já
  passou do check-in real, há tempo hábil de correção e não há reclamação
  aberta.
- **Prazo mínimo da propriedade**: `horas_minimas_para_pulso` — corte abaixo do
  qual o pulso deixa de ser instrumento de recuperação. Semeado na instalação;
  ausência impede o envio sem inventar número.
- **Horas restantes de estadia prevista**: `24 × (data prevista de saída −
  hoje)`, a partir da data civil de checkout já gravada na reserva. Não usa
  saída real (ainda não ocorreu) nem horário de checkout inventado.
- **Reclamação em aberto**: solicitação do tipo reclamação daquela reserva
  ainda não resolvida. Único tipo que suprime o pulso. Leitura humana na
  recepção, serviço e consumo não entram nesta trava.
- **Avaliação de pulso**: registro da resposta do hóspede à pergunta, com
  origem de segundo dia, instante e comentário; no máximo um por reserva;
  distinto da avaliação de checkout.
- **Chamado de recuperação**: solicitação do tipo reclamação aberta a partir
  de resposta negativa ao pulso, visível no Alert Center, com a mensagem de
  origem vinculada. Não é consumo e não é pedido de toalha.
- **Confirmação da resposta negativa**: recado, **antes** da tramitação, de
  que o hóspede foi ouvido **e** do que acontece em seguida (recepção avisada,
  alguém vai falar com ele). Sem pergunta de horário. Só quando o pulso é quem
  responde no turno.
- **Reconhecimento de pulso respondido**: recado único para sentimento
  positivo e neutro — agradece a resposta e convida a chamar se precisar; não
  afirma satisfação; **só sai se nenhum outro recado ocupou o turno**.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das estadias elegíveis (segundo dia a partir do check-in
  real, tempo restante ≥ mínimo da propriedade, sem reclamação aberta, pulso
  ainda não enviado), o hóspede recebe exatamente 1 pergunta sobre a
  experiência.
- **SC-002**: Em 100% das estadias com reclamação ainda não resolvida, 0 pulsos
  são enviados enquanto ela permanecer aberta.
- **SC-003**: Em 100% das estadias com horas restantes abaixo do mínimo da
  propriedade, 0 pulsos são enviados.
- **SC-004**: Em 100% das estadias que já receberam o pulso, nova verificação
  produz 0 segundas perguntas, inclusive sob concorrência e inclusive se o
  hóspede permanecer em silêncio.
- **SC-005**: Em 100% das respostas negativas, há 1 avaliação de pulso e 1
  chamado de reclamação no Alert Center (0 segundos chamados da mesma
  mensagem). Quando o pulso é quem responde, a confirmação precede a
  tramitação, informa o próximo passo e contém 0 perguntas de horário de
  visita. Quando outro recado já saiu no turno, há 0 confirmações extras
  de pulso.
- **SC-006**: Em 100% das respostas positivas e em 100% das neutras, há 1
  avaliação de pulso e 0 chamados. Quando nenhum outro recado saiu no turno,
  o reconhecimento é o mesmo texto — sem afirmar satisfação. Quando outro
  recado já saiu, há 0 reconhecimentos de pulso. Em 100% dos silêncios, há 0
  avaliações, 0 chamados e 0 lembretes.
- **SC-006b**: Em 100% das primeiras mensagens na janela do pulso que disparam
  dúvida, pedido ou reclamação técnica, o fluxo operacional ocorre e o
  hóspede recebe exatamente 1 recado (o operacional), com 0 empilhamentos de
  "obrigado por responder".
- **SC-007**: Em 100% das polaridades irreconhecíveis ou falhas de
  classificação, a mensagem permanece visível para humano, com 0 polaridades
  inventadas e 0 chamados automáticos de recuperação.
- **SC-008**: Alterar `horas_minimas_para_pulso` muda o desfecho na verificação
  seguinte sem mudança de regra. Ausência da chave produz 0 envios naquela
  propriedade e 0 números inventados.
- **SC-009**: Em verificação com dois hotéis, 0% dos pulsos, prazos, avaliações
  ou chamados de um aparecem no outro.
- **SC-010**: Em 100% das falhas de envio ainda dentro da janela, retoma-se o
  mesmo recado (0 perguntas distintas a mais). Em 100% das retomadas já fora
  da janela, 0 novas tentativas ao hóspede.
- **SC-011**: Em 100% dos desfechos, logs operacionais não contêm o texto da
  pergunta, da resposta nem da confirmação.
- **SC-012**: O caminho estadia elegível → uma pergunta → resposta negativa →
  confirmação antes do chamado no Alert Center (e os caminhos de supressão) é
  verificável de ponta a ponta sem o serviço real de envio e sem o serviço real
  de classificação.

## Assumptions

- As fatias F2.2 (chegada com instante real de check-in) e F3.5/F3.6 (abrir e
  resolver reclamação) estão concluídas. Esta fatia começa na estadia já
  hospedada e usa reclamação aberta/resolvida como trava e como destino da
  resposta negativa.
- O prazo `horas_minimas_para_pulso` já está previsto na configuração da
  propriedade. O bootstrap desta fatia passa a semeá-lo. Valor padrão da
  instalação inicial: **24**. O hotel altera por configuração da propriedade
  (sem tela nova no MVP).
- "Segundo dia" = o dia civil atual é estritamente posterior ao dia civil do
  `checkin_em`. Não se usa `data_checkin_prevista`.
- Cálculo de horas restantes com data de saída sem hora: 24 vezes a diferença
  em dias civis até `data_checkout_prevista`. É a mesma honestidade da fatia de
  silêncio, que também não inventa hora sobre um campo só de data. Um hotel que
  precise de corte em horas cheias contra um horário de checkout cadastrará
  isso em fatia futura; hoje o campo não existe.
- Pedido de serviço, consumo pendente e sinalização de leitura humana **não**
  suprimem o pulso. A justificativa emocional da jornada é o conserto em
  aberto. O aviso de humano não tem estado "resolvido" e, se trava-se, uma
  dúvida fora do catálogo cancelaria o pulso o resto da estadia.
- Reclamação aberta no segundo dia **adiará** o pulso até haver tempo e o
  chamado fechar; não o cancela para o restante de uma estadia longa. Perda
  definitiva só ocorre se, quando a reclamação fechar, já não houver tempo
  hábil — e isso é o desenho, não um defeito.
- A primeira mensagem após o pulso unanswered **encerra** o pulso (grava
  polaridade) e **não** bloqueia dúvida, pedido ou reclamação técnica: esses
  fluxos já existentes correm. **No máximo um recado de saída por mensagem de
  entrada.** Recado operacional já enviado → pulso em silêncio (sentimento
  gravado, sem "obrigado"). Recado de pulso só quando nada mais respondeu.
  Mensagens seguintes voltam ao fluxo normal. No máximo um chamado de
  reclamação por mensagem.
- Sentimento vem do mesmo serviço de classificação já usado na estadia
  (`positivo` / `neutro` / `negativo`). Não se pede nota 1–5 no pulso (a
  pesquisa de checkout é que pede nota; é outra fatia). Comentário da avaliação
  guarda o texto da resposta; nota pode ficar vazia. Neutro **não** é falha de
  classificação: é um eixo válido, no mesmo ramo do positivo, com o mesmo
  recado de reconhecimento.
- Recado iniciado pelo hotel: uma pergunta, sem oferta. Categoria operacional
  de utilidade, no mesmo espírito da coleta e das boas-vindas. Confirmação e
  reconhecimento da resposta ocorrem na conversa já aberta pelo pulso.
- Verificação periódica: a cadência já usada nas varreduras (na ordem de uma
  vez por hora) serve; atraso de um ciclo não justifica segundo pulso. A
  arquitetura nomeou uma passagem diária; o comportamento exigido é "no segundo
  dia, uma vez", não um relógio novo. Sem janela noturna nesta fatia.
- Envio e classificação nos testes são controlados (implementações falsas das
  portas). Nenhum teste chama serviço externo.
- Superfície de uso: histórico da conversa, Alert Center, registro de
  avaliação de pulso e desfecho da verificação. Ligar tela React de
  indicadores de satisfação continua fora do critério de pronto.
- Tela para editar o prazo no painel permanece fora (SQL / configuração da
  propriedade no MVP).
- Pesquisa de checkout, consentimento, lista de pedidos feitos pelo chat e
  inteligência de mercado ficam fora.
