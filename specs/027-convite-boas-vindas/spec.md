# Feature Specification: Linha de convite no recado de boas-vindas

**Feature Branch**: `027-convite-boas-vindas`

**Created**: 2026-08-27

**Status**: Draft

**Input**: User description: "Além das três informações de entrada, o recado de
boas-vindas passa a ter uma linha de convite mantida pela propriedade, que diz
ao hóspede o que ele pode perguntar por ali — serviços, cardápio, horários. A
linha segue as mesmas restrições de formato dos outros campos e nunca fica
vazia."
(backlog F7.3)

Restrições já decididas no projeto (entrada do specify): o recado de chegada
já existe — confirma a chegada, leva café, wi-fi e checkout, e termina
convidando a perguntar; esta fatia **substitui** o convite fixo do produto
pela linha que a casa escreve, sem reabrir o recado curto, a unicidade de um
pacote por reserva, a recuperação na janela de validade nem a proibição de
oferta comercial. O aviso de assistente virtual na primeira mensagem da
estadia **já foi entregue** (F7.1): permanece texto fixo do produto, antes
do convite, e esta fatia não o torna editável. A estrutura aprovada do recado
não muda de forma — é um campo a mais, no mesmo molde dos três de entrada,
com rótulo de produto imediatamente antes do texto da casa. Recepção edita;
gestão lê; perfil operacional é recusado. Sem tela nova do painel (isso é
fatia posterior). Módulos por propriedade (F7.4) e canal de e-mail (F7.5)
permanecem fora. O sistema não se integra ao sistema de gestão do hotel.
Conteúdo de mensagem de hóspede continua fora do log.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A casa escreve o convite com as próprias palavras (Priority: P1)

Como recepção, quero manter uma linha de convite da propriedade — o que o
hóspede pode perguntar por aquele canal, nas palavras da casa (serviços,
cardápio, horários, ou o que aquela operação quiser destacar) — no mesmo
lugar em que já cuido do café, do wi-fi e do checkout, para o recado de
chegada soar como a casa e não como um texto genérico de produto.

**Why this priority**: Sem o campo gravável, o restante da fatia não existe.
É o que distingue “o hotel convida com as próprias palavras” de “o produto
repete a mesma frase em toda propriedade”.

**Independent Test**: Pode ser testado pelas operações já usadas para ler e
gravar os textos de boas-vindas, sem tela nova: a recepção grava um convite
válido e lê de volta junto com café, wi-fi e checkout; tenta gravar vazio,
só espaços, com quebra de linha, tabulação ou mais de quatro espaços
seguidos e a gravação é recusada; gestão lê e não grava; perfil operacional
é recusado nos dois.

**Acceptance Scenarios**:

1. **Given** uma sessão autenticada de recepção e um convite de uma linha,
   dentro do mesmo limite de tamanho dos outros três textos de entrada,
   **When** a recepção grava, **Then** a configuração daquela propriedade
   passa a guardar essa linha, e a leitura seguinte devolve o mesmo texto
   (após remover espaços nas extremidades), junto com café, wi-fi e
   checkout.
2. **Given** convite vazio, só espaços, com quebra de linha, tabulação ou
   mais de quatro espaços seguidos, **When** a recepção tenta gravar,
   **Then** a gravação é recusada na hora, o valor anterior permanece, e a
   recusa deixa claro o que foi recusado — não espera o envio ao hóspede
   para falhar.
3. **Given** convite acima do limite de tamanho dos outros três textos,
   **When** a recepção tenta gravar, **Then** a gravação é recusada e o
   valor anterior permanece.
4. **Given** uma sessão de gestão, **When** consulta os textos de
   boas-vindas, **Then** lê o convite; **When** tenta gravá-lo, **Then** a
   alteração é recusada e o valor anterior permanece.
5. **Given** uma sessão de perfil operacional, **When** tenta ler ou gravar
   o convite, **Then** a operação é recusada nos dois sentidos.

---

### User Story 2 - O hóspede lê o convite da casa no recado de chegada (Priority: P1)

Como hóspede que acabou de chegar, quero que o recado curto de boas-vindas
termine com o convite que aquela propriedade escreveu — o que posso
perguntar por ali — para eu saber o que aquele canal cobre, nas palavras da
casa, e não uma frase igual em todo hotel.

**Why this priority**: Critério de aceite explícito da fatia. Campo gravado
que o hóspede não lê é configuração morta. O recado que o hóspede recebe
tem de carregar a linha da casa, em qualquer canal pelo qual esse recado
é entregue.

**Independent Test**: Pode ser testado confirmando a chegada de uma reserva
elegível com os quatro textos válidos e inspecionando o recado que chega ao
hóspede (e o que fica no histórico da conversa): café, wi-fi e checkout da
propriedade, aviso de assistente virtual intacto, e a última linha igual ao
convite gravado — não à frase antiga do produto. O mesmo roteiro no canal
de demonstração e no canal real de mensagens.

**Acceptance Scenarios**:

1. **Given** os quatro textos de boas-vindas preenchidos e válidos e uma
   reserva cuja chegada acaba de ser confirmada, **When** o recado é
   entregue, **Then** o hóspede recebe exatamente um recado curto que
   confirma a chegada, leva café, wi-fi e checkout, inclui o aviso de
   assistente virtual já entregue, e **termina** com a linha de convite
   gravada por aquela propriedade.
2. **Given** duas propriedades com convites diferentes, **When** cada uma
   confirma uma chegada, **Then** cada hóspede lê o convite da própria casa;
   o texto da outra propriedade não aparece.
3. **Given** o recado entregue, **When** o texto é inspecionado, **Then** o
   convite ocupa a última linha; o aviso de assistente virtual permanece
   imediatamente antes, intacto e não editável; há exatamente um convite —
   o da casa — e a frase fixa antiga do produto **não** aparece junto.
4. **Given** um canal pelo qual o recado de chegada é de fato entregue ao
   hóspede, **When** a casa grava um convite novo e uma chegada posterior é
   confirmada, **Then** o hóspede daquela chegada lê o convite novo na
   mensagem que recebe — não uma cópia congelada da frase antiga do
   produto. Canal que entrega o recado sem a linha da casa **não**
   satisfaz esta história.

---

### User Story 3 - Convite vazio não envia e sinaliza na fila (Priority: P1)

Como recepção, quero que um convite vazio ou ausente se comporte como café,
wi-fi ou checkout vazio: o check-in no balcão acontece, o recado **não**
sai com linha em branco, e a reserva aparece na fila do dia com a mesma
indicação distinguível de boas-vindas não enviadas, para a omissão não
passar em silêncio e o hóspede não ganhar um recado pela metade.

**Why this priority**: “Nunca fica vazia” só vale se o envio recusar o vazio
com a mesma visibilidade dos outros três campos. Sem isso, a casa apaga o
convite e o hóspede recebe um recado que termina no aviso, ou com variável
em branco.

**Independent Test**: Pode ser testado com propriedade cujo convite está
ausente ou vazio (os três de entrada válidos) confirmando a chegada: a
reserva fica hospedada, nenhum recado sai, a fila do dia sinaliza
boas-vindas não enviadas. Completar o convite dentro da janela de validade
envia exatamente um recado já com a linha da casa; completar fora da
janela não dispara envio automático.

**Acceptance Scenarios**:

1. **Given** café, wi-fi e checkout válidos e convite vazio ou ausente,
   **When** a recepção confirma a chegada, **Then** a reserva fica
   hospedada, o recado **não** é enviado, e a fila do dia apresenta a
   indicação distinguível de boas-vindas não enviadas — a mesma já usada
   quando falta um dos três de entrada, não um destaque novo.
2. **Given** uma reserva hospedada nessa situação cujo instante de chegada
   ainda está dentro da janela de validade, **When** o convite passa a
   estar preenchido e válido e o processamento seguinte ocorre, **Then**
   aquela reserva recebe exatamente um recado, já com a linha da casa, e
   deixa de constar como boas-vindas não enviadas.
3. **Given** uma reserva hospedada nessa situação cujo instante de chegada
   é anterior à janela de validade, **When** o convite é preenchido,
   **Then** nenhum recado sai automaticamente e a sinalização na fila
   permanece.
4. **Given** um recado já enviado, **When** a recepção altera o convite,
   **Then** nenhum segundo recado de chegada nasce para aquela reserva; o
   texto novo vale para chegadas seguintes.

---

### User Story 4 - Propriedade nova já nasce com convite padrão (Priority: P2)

Como gestão que instala o sistema, quero que a propriedade recém-criada já
venha com um convite padrão válido — uma linha que convida a perguntar
sobre serviços, cardápio e horários — para a primeira confirmação de
chegada não depender de alguém lembrar de escrever o campo. A recepção
substitui pelo texto da casa quando quiser.

**Why this priority**: Sem semente, o campo “nunca vazio” trava o primeiro
recado. Com semente, a casa opera no primeiro dia e personaliza depois.

**Independent Test**: Pode ser testado instalando uma propriedade nova e
lendo os textos de boas-vindas: os quatro campos estão presentes e não
vazios; o convite é uma linha válida no formato dos outros. Propriedade já
em operação, que nasceu antes deste campo, também passa a ter o mesmo
padrão preenchido, sem exigir cadastro manual para o recado voltar a sair.

**Acceptance Scenarios**:

1. **Given** uma propriedade recém-instalada, **When** a recepção consulta
   os textos de boas-vindas, **Then** o convite já existe, não está vazio,
   respeita o formato de uma linha, e convida o hóspede a perguntar sobre
   serviços, cardápio e horários por aquele canal.
2. **Given** uma propriedade que já operava com os três textos de entrada e
   ainda não tinha convite editável, **When** esta fatia passa a valer,
   **Then** essa propriedade também fica com o convite padrão preenchido —
   o recado de chegadas seguintes não para de sair só porque o campo é
   novo.
3. **Given** o convite padrão, **When** a recepção grava o texto da casa no
   lugar, **Then** as chegadas seguintes usam o texto novo.

---

### Edge Cases

- Um dos três textos de entrada vazio e convite válido: o recado não sai;
  a sinalização é a já existente de boas-vindas não enviadas. Os quatro
  precisam estar válidos para o recado ir.
- Convite apagado por escrito direto no armazenamento, fora da gravação
  validada: o recado não sai; a fila sinaliza; não se monta mensagem com
  linha em branco.
- Convite com uma interrogação, com várias, ou sem nenhuma: a gravação
  aceita, desde que a linha cumpra o formato dos outros três. A regra
  antiga de “exatamente uma interrogação na última linha” pertencia à
  frase fixa do produto e **não** constrange o texto da casa.
- Aviso de assistente virtual: continua imediatamente antes do convite,
  texto fixo do produto. Tentativa de editá-lo por esta fatia não existe.
- Alterar só o convite, sem mexer em café, wi-fi e checkout: os três
  permanecem; só a linha de convite muda.
- Recado já enviado: mudar o convite não reabre unicidade nem dispara
  segundo pacote. Recuperação continua só para quem ainda não recebeu e
  está na janela.
- Hotel A não lê nem grava convite do hotel B. Consulta e gravação
  consideram a propriedade da sessão.
- Conteúdo do convite e do recado nunca aparecem em log; logs registram
  identificadores, propriedade, resultado da gravação ou do envio e
  código de recusa.
- Tela do painel para editar o recado, módulos por propriedade e segundo
  canal por e-mail **não** fazem parte desta fatia.
- Oferta comercial, desconto ou convite de compra **não** entram nesta
  fatia: o campo existe para dizer o que o hóspede pode perguntar, não
  para virar recado promocional. Não há filtro automático de marketing no
  texto; a recepção é responsável pelo teor, como já é nos três de
  entrada.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A configuração de boas-vindas da propriedade MUST passar a
  ter exatamente **quatro** textos de uma linha: café, wi-fi, checkout e
  **convite**. MUST NOT haver quinto texto de entrada nem substituição do
  convite por item de catálogo escolhido na hora.
- **FR-002**: O convite MUST dizer, nas palavras da propriedade, o que o
  hóspede pode perguntar por aquele canal. MUST ser gravável pela
  recepção da própria propriedade.
- **FR-003**: A gravação do convite MUST ser recusada na hora se o valor
  for vazio, só espaços, contiver quebra de linha, tabulação, mais de
  quatro espaços seguidos, ou ultrapassar o mesmo limite de tamanho dos
  outros três textos de entrada. A recusa MUST ocorrer na configuração,
  não no envio ao hóspede. O valor anterior MUST permanecer.
- **FR-004**: O valor gravado MUST ser o texto após remover espaços nas
  extremidades.
- **FR-005**: A recepção MUST poder ler e gravar os quatro textos da
  própria propriedade pela mesma operação já usada para os três de
  entrada — sem tela nova nesta fatia. Gestão MUST poder ler e MUST NOT
  gravar. Perfil operacional MUST receber recusa de leitura e de
  gravação.
- **FR-006**: A autorização de gravação MUST continuar específica dos
  textos de boas-vindas, agora incluindo o convite. Parâmetro de
  comportamento do sistema (prazo de reenvio, janela de corte, duração de
  sessão, periodicidade de coleta, validade das boas-vindas) MUST
  permanecer fora do que esta permissão alcança.
- **FR-007**: A instalação inicial MUST semear o convite com texto não
  vazio e válido no formato de uma linha, que convide o hóspede a
  perguntar sobre serviços, cardápio e horários por aquele canal.
  Propriedade que já existia sem este campo MUST receber o mesmo padrão,
  sem exigir cadastro manual para o recado continuar saindo.
- **FR-008**: O recado de boas-vindas entregue ao hóspede MUST terminar
  com o convite gravado por aquela propriedade. MUST haver exatamente um
  convite, na última linha. A frase fixa antiga do produto MUST NOT
  aparecer no recado depois desta fatia.
- **FR-009**: O aviso de assistente virtual MUST permanecer imediatamente
  antes da linha de convite, texto fixo do produto, não editável. Esta
  fatia MUST NOT torná-lo configurável nem omiti-lo.
- **FR-010**: Os três fatos de entrada (café, wi-fi, checkout), a
  confirmação da chegada, a unicidade de um recado por reserva, a
  recuperação na janela de validade, a proibição de oferta comercial no
  recado e a ausência do catálogo completo MUST permanecer como já
  especificados. O convite acresce; não substitui os fatos.
- **FR-011**: Se, no momento de enviar, o convite estiver vazio ou
  ausente, o sistema MUST NOT enviar o recado e MUST sinalizar a reserva
  na fila do dia com a indicação já existente de boas-vindas não
  enviadas. O status hospedado e o momento de entrada MUST permanecer.
  MUST NOT se montar recado com linha de convite em branco.
- **FR-012**: A condição para o recado sair MUST ser os **quatro** textos
  válidos. Faltar café, wi-fi, checkout **ou** convite MUST produzir o
  mesmo desfecho de omissão sinalizada.
- **FR-013**: Quando os quatro textos passarem a estar preenchidos e
  válidos, o processamento seguinte MUST enviar exatamente um recado para
  cada reserva que esteja hospedada, cujo instante real de chegada esteja
  dentro da janela de validade, e que ainda não tenha recebido
  boas-vindas — o mesmo recorte já especificado, agora exigindo também o
  convite.
- **FR-014**: Alterar o convite depois de um recado já enviado MUST NOT
  gerar segundo recado de chegada para aquela reserva. O texto novo MUST
  valer só para chegadas seguintes (e para recuperação de quem ainda não
  recebeu).
- **FR-015**: O convite que a propriedade gravou MUST ser o que o hóspede
  lê no recado que recebe, em **qualquer** canal pelo qual esse recado é
  entregue. Um canal que entregue o recado de chegada com a frase antiga
  do produto, ou sem a linha da casa, MUST NOT ser considerado pronto
  nesta fatia.
- **FR-016**: Toda leitura e toda gravação MUST considerar o hotel da
  sessão. Convite de um hotel MUST NOT ser visível nem alterável por
  outro.
- **FR-017**: Conteúdo do convite, do recado e demais dados pessoais
  NUNCA MUST aparecer em log; logs registram identificadores, hotel,
  resultado e código de recusa.
- **FR-018**: Esta fatia MUST NOT criar tela do painel, MUST NOT ligar ou
  desligar módulos da propriedade, MUST NOT acrescentar canal de e-mail,
  MUST NOT reabrir o aviso de assistente virtual para edição, MUST NOT
  alterar a personalidade da assistente, e MUST NOT integrar-se ao
  sistema de gestão do hotel.
- **FR-019**: A verificação automatizada desta fatia MUST ser possível
  sem chamar a rede do serviço de mensagens de produção. O critério de
  FR-015 (o hóspede lê a linha da casa no canal que de fato entrega o
  recado) permanece obrigatório no caminho de produção; a verificação
  automatizada prova o recado montado e gravado.

### Key Entities

- **Linha de convite**: quarto texto de uma linha da configuração de
  boas-vindas da propriedade. Diz ao hóspede o que ele pode perguntar por
  aquele canal, nas palavras da casa. Obrigatório, nunca vazio, mesmo
  formato dos três de entrada.
- **Textos de entrada**: café, wi-fi e checkout — inalterados em papel;
  passam a ser quatro junto com o convite para o recado poder sair.
- **Pacote de boas-vindas**: recado operacional curto e único por
  reserva. Continua confirmando a chegada e levando os três fatos; passa
  a terminar com o convite da casa, depois do aviso de assistente
  virtual.
- **Aviso de assistente virtual**: frase fixa do produto na primeira
  mensagem da estadia, já entregue. Fora do alcance de quem edita o
  convite.
- **Sinalização de boas-vindas não enviadas**: indicação já existente na
  fila do dia. Esta fatia não cria destaque novo; o convite vazio ou
  ausente acende a mesma indicação.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das gravações aceitas, a leitura seguinte devolve o
  convite gravado (após remover espaços nas extremidades), daquela
  propriedade, junto com os três textos de entrada.
- **SC-002**: Em 100% das tentativas de gravar convite vazio, só espaços,
  com quebra de linha, tabulação, mais de quatro espaços seguidos ou
  acima do limite de tamanho, a gravação é recusada e o valor anterior
  permanece.
- **SC-003**: Em 100% dos recados de chegada entregues com os quatro
  textos válidos, a última linha é o convite daquela propriedade, 0
  recados trazem a frase fixa antiga do produto, e 100% trazem o aviso de
  assistente virtual imediatamente antes do convite.
- **SC-004**: Em verificação com duas propriedades, 0% dos recados do
  hotel A trazem o convite do hotel B.
- **SC-005**: Em 100% das confirmações de chegada com convite vazio ou
  ausente, nascem 0 envios ao hóspede, a reserva fica hospedada, e 100%
  dessas reservas aparecem na fila do dia com a indicação de boas-vindas
  não enviadas.
- **SC-006**: Ao completar o convite (com os outros três já válidos),
  100% das reservas hospedadas cujo instante de chegada está dentro da
  janela de validade e que não receberam boas-vindas recebem exatamente
  um recado na passagem seguinte; 0% das reservas cujo instante é
  anterior à janela recebem envio automático.
- **SC-007**: Em 100% das alterações de convite após recado já enviado,
  nascem 0 segundos recados de chegada para aquela reserva.
- **SC-008**: Após a instalação inicial, 100% das propriedades novas têm
  o convite presente e não vazio. Em 100% das propriedades que já
  operavam sem este campo, o convite padrão também passa a estar
  presente e não vazio.
- **SC-009**: Em verificação com sessão de gestão, 100% das leituras do
  convite são permitidas e 100% das gravações são recusadas. Em
  verificação com perfil operacional, 100% das leituras e das gravações
  são recusadas.
- **SC-010**: Em verificação com sessão de recepção, 100% das tentativas
  de alterar parâmetro de comportamento da propriedade continuam sem
  caminho autorizado; a permissão alcança os quatro textos de
  boas-vindas e somente eles.
- **SC-011**: 100% dos recados montados para entrega ao hóspede — no
  canal de demonstração e no canal que a propriedade usa com hóspede
  real — carregam a linha de convite gravada. 0% dos caminhos de entrega
  do recado de chegada omitem essa linha ou a substituem pela frase
  antiga do produto.
- **SC-012**: O caminho gravar convite → confirmar chegada → hóspede lê a
  linha da casa (sucesso, recusa de formato, omissão sinalizada) é
  verificável ponta a ponta sem chamada à rede do provedor real na suíte
  e sem tela visual nova.

## Assumptions

- A fatia F2.2 (confirmar chegada e recado curto) está concluída. Esta
  fatia acrescenta o quarto texto; não redesenha o recado, a fila, a
  unicidade nem a janela de validade.
- A fatia F7.1 já entregou o aviso de assistente virtual na primeira
  mensagem da estadia. Esta fatia o mantém e não o reabre.
- **Mesmo molde dos três de entrada (já decidido no backlog):** o convite
  vive na mesma configuração por propriedade, com as mesmas recusas de
  formato (vazio, quebra de linha, tabulação, mais de quatro espaços
  seguidos, teto de tamanho). Não há cadastro separado. O rótulo
  imediatamente antes do texto da casa é fixo do produto, como “Café da
  manhã:” antes do café. A última linha que o hóspede lê é o convite
  gravado — não uma segunda frase de convite do produto.
- **A frase fixa antiga sai de cena.** O recado deixa de terminar com
  “Quer saber mais alguma coisa da sua estadia? Pode perguntar por
  aqui.” Essa frase era do produto; a casa a substitui. A regra de
  exatamente uma interrogação na última linha era contrato da frase
  fixa e não se aplica ao texto da casa.
- **Semente (já decidida no backlog):** propriedade nova e propriedade já
  instalada recebem um convite padrão válido. O valor literal da semente
  é detalhe de planejamento; o sentido é convidar a perguntar sobre
  serviços, cardápio e horários por aquele canal, para a recepção
  substituir pelas palavras da casa.
- **Quem edita (já decidido no backlog):** recepção grava; gestão lê;
  perfil operacional recusado — o mesmo recorte dos três textos. A
  operação de autorização já existente para textos de boas-vindas passa
  a cobrir o convite; não se cria permissão genérica sobre toda a
  configuração da propriedade.
- **Sem tela nesta fatia.** A recepção usa a mesma operação de
  configuração já usada para os três textos. A tela do painel que edita
  o recado é fatia posterior (F8.6).
- **O hóspede lê o que a casa gravou (Artigo XV).** Se um canal de
  entrega do recado de chegada tiver texto de convite congelado no
  provedor, diferente do gravado pela propriedade, essa fatia não está
  pronta naquele canal — não se declara sucesso só no histórico ou só no
  canal de demonstração. A verificação automatizada continua sem a rede
  do serviço de produção; o caminho que de fato entrega o recado ao
  hóspede precisa carregar a linha da casa.
- Slot vazio não bloqueia o check-in e **não** degrada o recado com
  variável em branco: a mensagem não sai, e a omissão fica visível na
  fila — agora também quando o que falta é o convite.
- Não há filtro automático de linguagem comercial no texto do convite. A
  fatia não cria recado promocional; a recepção responde pelo teor, como
  já responde pelo texto do wi-fi.
- Conteúdo de mensagem continua fora do log (Artigo VIII). `id_hotel` em
  toda operação (Artigo XIV). Na dúvida, esta fatia não inventa resposta
  ao hóspede — só o recado de chegada já existente.
- F7.4 (módulos) e F7.5 (e-mail) permanecem fora. Personalidade da
  assistente (F7.2) não é alterada aqui.
