# Feature Specification: Expurgo por Retenção

**Feature Branch**: `023-expurgo-retencao`

**Created**: 2026-08-21

**Status**: Draft

**Input**: User description: "O sistema aplica automaticamente a política de
retenção de dados pessoais. Conteúdo de conversas e comentários de avaliação
é anonimizado doze meses após a saída do hóspede, preservando as estatísticas
de volume. Fichas cadastrais são apagadas cinco anos após a última estadia.
Toda execução registra o que foi tratado, para que o cumprimento possa ser
demonstrado."
(backlog F6.1)

Restrições já decididas no projeto (entrada do specify): prazos declarados
publicamente — ficha cadastral **cinco anos** após o checkout, conversas
**doze meses** com anonimização; expurgo **automático e agendado**, nunca
manual; o relógio começa no instante real da partida confirmada no painel,
nunca na data prevista e nunca por integração com o sistema de gestão do
hotel; anonimizar conteúdo livre **substitui o texto e mantém a linha**,
porque apagar destruiria a estatística de volume de atendimento; cada
execução deixa registro de quantidade e tipo, sem o conteúdo tratado; prazo
operacional não é constante embutida — vive na configuração da propriedade;
dado de um hotel não é tratado no lugar de outro; conteúdo de mensagem
**nunca** vai para log.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conteúdo livre some no prazo, a linha fica (Priority: P1)

Como titular dos dados que já deixou o hotel, quero que o texto que eu
escrevi — mensagens da conversa, comentário de avaliação e demais conteúdos
livres daquela estadia — deixe de ser recuperável **doze meses após a saída
confirmada**, sem que o hotel perca a contagem de que houve atendimento,
para a política declarada ser cumprida de fato e não só no papel.

**Why this priority**: É metade do objetivo da fatia e a obrigação mais
urgente. Conteúdo livre é imprevisível (saúde, terceiros, opinião). Declarar
doze meses e guardar o texto para sempre é pior do que não declarar.

**Independent Test**: Pode ser testado com uma estadia cuja saída já foi
confirmada, avançando o relógio para além de doze meses, disparando a
passagem automática de retenção e verificando: o texto livre daquela estadia
foi substituído; a linha da mensagem, da avaliação e do chamado permanece;
intenção, sentimento, nota e tipo de atendimento continuam legíveis para
contagem; uma estadia cuja saída foi confirmada há menos de doze meses
mantém o texto intacto.

**Acceptance Scenarios**:

1. **Given** uma reserva com saída confirmada há mais de doze meses (prazo
   configurado da propriedade) e mensagens com texto original, **When** a
   passagem automática de retenção corre, **Then** o conteúdo de cada
   mensagem daquela reserva é substituído por marca não identificadora; a
   linha da mensagem permanece; direção, instante e eixos de classificação
   (intenção, sentimento, urgência) permanecem.
2. **Given** a mesma reserva com comentário de avaliação preenchido,
   **When** a passagem corre, **Then** o comentário é substituído; a linha
   da avaliação permanece; a nota, a origem (pulso ou saída) e o instante
   da resposta permanecem.
3. **Given** a mesma reserva com descrição de solicitação em texto livre,
   **When** a passagem corre, **Then** essa descrição é substituída; a
   linha da solicitação permanece, com tipo, status e demais campos
   operacionais intactos.
4. **Given** o corpo bruto da conversa daquela estadia (o registro de
   entrada do canal), **When** a passagem corre, **Then** esse corpo é
   substituído no mesmo prazo das mensagens; o identificador que impede
   reprocessar a mesma entrada permanece, para a conversa não “renascer”.
5. **Given** um comentário de avaliação que **nunca** teve texto (vazio),
   **When** a passagem corre, **Then** o vazio permanece vazio — não
   recebe marca de anonimização como se houvesse havido texto.

---

### User Story 2 - A estatística de volume continua correta (Priority: P1)

Como gestão do hotel, quero continuar vendo **quantas** conversas, pedidos
e avaliações existiram depois que o texto pessoal foi retirado, para o
indicador de volume de atendimento não colapsar no dia em que a retenção
cumpre o prazo.

**Why this priority**: Critério de aceite explícito. Anonimizar apagando a
linha falsificaria o passado operacional. O dado pessoal sai; a métrica
fica.

**Independent Test**: Pode ser testado contando mensagens, solicitações por
tipo e avaliações por nota **antes** da passagem, anonimizando o conteúdo
livre de uma estadia vencida, e conferindo que as mesmas contagens
permanecem, agora sem texto pessoal recuperável.

**Acceptance Scenarios**:

1. **Given** uma propriedade com N mensagens em reservas já vencidas no
   prazo de conteúdo livre, **When** a passagem anonimiza essas mensagens,
   **Then** a contagem de mensagens da propriedade continua N — nenhuma
   linha some.
2. **Given** solicitações de reclamação, serviço e consumo naquela estadia,
   **When** as descrições são anonimizadas, **Then** a contagem por tipo
   continua a mesma; nenhum chamado é encerrado, cancelado ou apagado pela
   retenção.
3. **Given** avaliações com nota e comentário, **When** o comentário é
   anonimizado, **Then** a distribuição de notas permanece; nota não vira
   vazia só porque o texto saiu.
4. **Given** eixos de classificação já gravados (intenção, sentimento,
   urgência), **When** o conteúdo e a saída bruta do classificador são
   retirados, **Then** os eixos estruturados permanecem e continuam
   utilizáveis para volume por tipo.

---

### User Story 3 - A ficha some cinco anos depois da última saída (Priority: P1)

Como titular dos dados, quero que nome, documento, telefone, nascimento e
demais campos da ficha cadastral sejam **apagados** cinco anos após a
última estadia cuja saída foi confirmada, para o hotel não guardar
identidade completa por prazo indefinido.

**Why this priority**: É a outra metade da política declarada (ficha ×
conteúdo livre). A ficha é o depósito de dado pessoal identificável. Sem
esta exclusão, a LGPD anunciada na documentação não se cumpre.

**Independent Test**: Pode ser testado com um hóspede cuja última reserva
vinculada tem saída confirmada há mais de cinco anos, disparando a
passagem, e verificando: a ficha não é mais recuperável; o histórico de
consentimento daquela pessoa sai com ela; a reserva operacional (datas,
status, contagens) permanece sem cópia de nome, documento ou telefone
daquela pessoa; um hóspede com saída mais recente, ou ainda hospedado,
permanece intacto.

**Acceptance Scenarios**:

1. **Given** um hóspede cuja última reserva vinculada tem saída confirmada
   há mais de cinco anos (prazo configurado da propriedade), **When** a
   passagem automática corre, **Then** a ficha cadastral é apagada — nome,
   documento, telefone, nascimento e demais campos da ficha deixam de ser
   recuperáveis.
2. **Given** consentimentos registrados para esse hóspede, **When** a ficha
   é apagada, **Then** o histórico de consentimento daquela pessoa é
   apagado junto — não resta um rastro identificável órfão.
3. **Given** a reserva operacional daquela estadia, **When** a ficha é
   apagada, **Then** a reserva permanece (datas, status, instante de
   entrada e de saída); **não** permanece cópia de nome, documento ou
   telefone da pessoa apagada nessa reserva.
4. **Given** um hóspede com duas reservas vinculadas, a mais recente com
   saída confirmada há menos de cinco anos, **When** a passagem corre,
   **Then** a ficha **não** é apagada — o relógio é a última saída, não a
   primeira.
5. **Given** um hóspede ainda hospedado, ou com reserva encerrada **sem**
   instante de saída confirmado, **When** a passagem corre, **Then** a
   ficha **não** é apagada — o sistema não inventa partida a partir da
   data prevista.

---

### User Story 4 - Dentro do prazo, nada é tocado (Priority: P1)

Como operação do hotel, quero que conversa recente, avaliação recente e
ficha de quem saiu ontem ou há onze meses permaneçam **intactas**, para a
retenção não se antecipar ao prazo declarado e não apagar o que o balcão
ainda precisa.

**Why this priority**: Critério de aceite explícito. Um expurgo ansioso é
perda de dado operacional; um expurgo que “arredonda” o prazo é
descumprimento da política na outra direção.

**Independent Test**: Pode ser testado misturando, na mesma propriedade,
estadias vencidas e estadias dentro do prazo, rodando uma passagem, e
verificando que só o conjunto vencido foi tratado.

**Acceptance Scenarios**:

1. **Given** uma reserva com saída confirmada há menos de doze meses,
   **When** a passagem corre, **Then** conteúdo de mensagem, comentário,
   descrição de solicitação e corpo de entrada da conversa permanecem
   exatamente como estavam.
2. **Given** um hóspede cuja última saída confirmada foi há menos de cinco
   anos, **When** a passagem corre, **Then** a ficha permanece completa.
3. **Given** conteúdo já anonimizado numa passagem anterior, **When** a
   passagem corre de novo, **Then** as linhas já tratadas não são
   recontadas como tratamento novo; o texto não volta; a ficha já apagada
   não reaparece.
4. **Given** duas propriedades, **When** a passagem trata o hotel A,
   **Then** nenhuma ficha, mensagem ou avaliação do hotel B é alterada ou
   apagada.

---

### User Story 5 - O cumprimento pode ser demonstrado (Priority: P1)

Como gestão responsável pelos dados da propriedade, quero que **cada**
passagem de retenção deixe um comprovante: quando rodou, quantas linhas de
cada tipo foram tratadas — sem o texto pessoal — para eu conseguir mostrar
a uma fiscalização ou a uma banca que a política declarada não é só
intenção.

**Why this priority**: A documentação já registrou: sem esse registro não
há como demonstrar cumprimento. Log que some ou que imprime o conteúdo
tratado não serve.

**Independent Test**: Pode ser testado autenticando como gestão,
consultando o comprovante depois de uma passagem que anonimizou N
mensagens e apagou M fichas, e verificando quantidades e tipos; tentando
com recepção; e inspecionando que o comprovante e os registros
operacionais não carregam o texto original.

**Acceptance Scenarios**:

1. **Given** uma passagem que anonimizou mensagens, comentários e
   descrições e apagou fichas, **When** a gestão consulta o comprovante
   daquela execução na própria propriedade, **Then** vê a data e a hora da
   passagem e a quantidade de cada tipo tratado (mensagens anonimizadas,
   comentários, corpos de entrada, descrições, fichas apagadas).
2. **Given** uma passagem em que nada estava vencido, **When** a gestão
   consulta o comprovante, **Then** a execução aparece com quantidades
   zero — o cumprimento também se demonstra pela passagem que não tinha
   o que tratar.
3. **Given** o comprovante e os registros operacionais da passagem,
   **When** são inspecionados, **Then** não contêm conteúdo de mensagem,
   comentário original, documento, telefone nem nome do hóspede tratado.
4. **Given** uma sessão de recepção ou operacional, **When** tenta ler o
   comprovante de retenção, **Then** a operação é recusada.
5. **Given** comprovantes do hotel A, **When** a gestão do hotel B
   consulta os próprios, **Then** nenhum comprovante do hotel A aparece.

---

### Edge Cases

- Reserva ainda hospedada, mesmo com data prevista de saída já vencida há
  anos: **não** entra em anonimização nem em exclusão de ficha. O relógio
  não começa sem o clique de saída. A pendência continua visível na fila
  do dia (já entregue na fatia de confirmar saída); esta fatia não inventa
  a partida.
- Reserva encerrada sem instante de saída gravado: **não** é elegível.
  Ausência do instante não é tratada como “saiu na data prevista”.
- Saída confirmada exatamente no limite do prazo: vence ao completar o
  intervalo configurado, não antes. “Doze meses” e “cinco anos” são os
  valores semeados, lidos da configuração da propriedade.
- Propriedade sem o prazo de conteúdo livre configurado ou com valor
  inválido: a passagem **não** anonimiza naquele hotel e registra que o
  prazo está ausente. **Não** usa doze meses embutidos.
- Propriedade sem o prazo de ficha configurado ou com valor inválido: a
  passagem **não** apaga ficha naquele hotel e registra prazo ausente.
  **Não** usa cinco anos embutidos. O outro prazo, se válido, continua a
  valer na mesma passagem.
- Hóspede vinculado só a reservas que nunca tiveram saída confirmada: ficha
  permanece. Não há “última estadia” no sentido da política.
- Duas reservas do mesmo hóspede: o prazo de **conteúdo livre** corre por
  reserva (doze meses após a saída daquela estadia). O prazo da **ficha**
  corre pela última saída entre as reservas vinculadas.
- Comentário vazio versus comentário já anonimizado: distinguíveis. Vazio
  não recebe marca; já anonimizado não é tratado de novo como original.
- Classificação estruturada permanece; a saída bruta completa do
  classificador — que pode ecoar o texto — sai junto com o conteúdo livre.
- Pedido de esquecimento feito na hora pelo titular (direito avulso, fora
  do prazo automático): **fora desta fatia**. Aqui só o calendário
  automático.
- Dado de funcionário (nome, e-mail, sessão do painel): **fora**. A
  política desta fatia é a do hóspede.
- Inteligência de mercado (concorrente, coleta, preço, nota agregada):
  **fora**. Não é dado do titular da estadia.
- Esta fatia **não** envia mensagem ao hóspede, **não** abre chamado,
  **não** confirma chegada nem saída, **não** consulta o sistema de gestão
  do hotel e **não** oferece botão “expurgar agora” no painel.
- Tela visual nova **não** faz parte do critério de pronto. O comportamento
  observável é a passagem automática, o efeito nos dados vencidos e a
  consulta autenticada do comprovante pela gestão.
- Logs da passagem registram hotel, quantidades por tipo, prazo ausente
  quando couber. **Não** registram o texto tratado.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST aplicar a política de retenção em passagem
  automática periódica, sem depender de clique de funcionário para cada
  linha vencida. MUST NOT oferecer disparo manual de expurgo no painel.
- **FR-002**: O relógio de retenção MUST usar o instante real da saída
  confirmada da reserva. MUST NOT usar a data prevista de saída. MUST NOT
  inferir partida por integração com o sistema de gestão do hotel.
- **FR-003**: Doze meses após a saída confirmada da reserva (prazo de
  conteúdo livre da propriedade), o sistema MUST substituir o conteúdo
  das mensagens daquela reserva por marca não identificadora, mantendo a
  linha.
- **FR-004**: No mesmo prazo da FR-003, o sistema MUST substituir o
  comentário de avaliação daquela reserva, quando houver texto, mantendo
  a linha, a nota, a origem e o instante.
- **FR-005**: No mesmo prazo da FR-003, o sistema MUST substituir a
  descrição em texto livre da solicitação daquela reserva, mantendo a
  linha e os campos operacionais (tipo, status, urgência, valores de
  consumo).
- **FR-006**: No mesmo prazo da FR-003, o sistema MUST substituir o corpo
  bruto de entrada da conversa daquela estadia, preservando o
  identificador que impede reprocessar a mesma entrada.
- **FR-007**: No mesmo prazo da FR-003, o sistema MUST retirar a saída
  bruta completa do classificador das mensagens daquela reserva. Os eixos
  estruturados (intenção, sentimento, urgência) MUST permanecer.
- **FR-008**: Anonimizar MUST NOT apagar a linha de mensagem, avaliação
  ou solicitação. Contagens de volume MUST permanecer corretas após a
  passagem.
- **FR-009**: Comentário ou descrição que já era vazio MUST permanecer
  vazio. MUST NOT receber marca de anonimização.
- **FR-010**: Cinco anos após a saída confirmada da **última** reserva
  vinculada ao hóspede (prazo de ficha da propriedade), o sistema MUST
  apagar a ficha cadastral (nome, documento, telefone, nascimento e
  demais campos da ficha).
- **FR-011**: Ao apagar a ficha, o sistema MUST apagar o histórico de
  consentimento daquela pessoa e MUST NOT deixar nome, documento ou
  telefone da pessoa na reserva vinculada.
- **FR-012**: Reserva operacional (datas, status, instantes de entrada e
  saída, vínculos de atendimento já anonimizados) MUST permanecer após a
  exclusão da ficha.
- **FR-013**: Dados ainda dentro do prazo MUST NOT ser anonimizados nem
  apagados. Reserva sem instante de saída confirmado MUST NOT ser
  elegível.
- **FR-014**: Passagem subsequente MUST ser idempotente: já anonimizado
  não volta e não conta como tratamento novo; ficha já apagada não
  reaparece.
- **FR-015**: Os prazos MUST viver na configuração da propriedade, não
  como intervalo embutido. Valores semeados na instalação: conteúdo livre
  em `meses_retencao_conteudo_livre` = `12`; ficha em
  `anos_retencao_ficha` = `5`. Prazo ausente ou inválido MUST impedir só
  o tratamento daquele tipo naquele hotel, com registro de prazo ausente,
  sem supor o valor semeado.
- **FR-016**: Cada passagem MUST gravar um comprovante durável por hotel:
  instante da execução e quantidade de cada tipo tratado (mensagens
  anonimizadas, comentários, corpos de entrada, descrições, fichas
  apagadas), inclusive quando todas as quantidades forem zero.
- **FR-017**: Consultar o comprovante MUST ser exclusivo do perfil de
  gestão da propriedade da sessão. Recepção e perfil operacional MUST
  receber recusa.
- **FR-018**: Toda passagem e toda consulta MUST considerar o hotel.
  Dado e comprovante de um hotel MUST NOT ser visíveis nem alterados no
  outro.
- **FR-019**: Esta fatia MUST NOT enviar mensagem ao hóspede, MUST NOT
  alterar catálogo, concorrente, coleta de mercado, parâmetro de
  comportamento além de semear as duas chaves de prazo, e MUST NOT
  confirmar fase de reserva.
- **FR-020**: Logs e comprovantes MUST registrar identificadores,
  quantidades, tipos e códigos (incluindo prazo ausente). MUST NOT
  registrar conteúdo de mensagem, comentário original, documento,
  telefone ou nome do hóspede tratado.
- **FR-021**: Pedido avulso de exclusão pelo titular, fora do calendário
  automático, MUST permanecer fora desta fatia.

### Key Entities

- **Política de retenção**: os dois prazos declarados — conteúdo livre
  doze meses após a saída da estadia; ficha cinco anos após a última
  saída do hóspede. Cumprida por passagem automática, não por disciplina
  humana.
- **Saída confirmada**: o instante real da partida registrado quando a
  recepção confirma a saída no painel. É o único eixo do relógio. Data
  prevista não conta.
- **Conteúdo livre**: texto que o titular (ou o canal) pode ter escrito
  sem controle — mensagem, comentário de avaliação, descrição de
  solicitação, corpo bruto de entrada da conversa, saída bruta do
  classificador. No prazo, é substituído; a linha operacional fica.
- **Anonimização**: substituição do conteúdo livre por marca não
  identificadora, distinguível de vazio original. Preserva volume;
  elimina o dado pessoal.
- **Ficha cadastral**: identidade do hóspede (nome, documento, telefone,
  nascimento e correlatos). No prazo, é apagada, não anonimizada.
- **Comprovante de retenção**: registro durável de uma passagem — quando
  e quantas linhas de cada tipo, por propriedade. É o que permite
  demonstrar cumprimento. Não é auditoria genérica de qualquer alteração
  do sistema.
- **Prazo da propriedade**: as duas chaves de retenção na configuração da
  casa. Sem valor válido, aquele tipo não é tratado naquela casa.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das reservas com saída confirmada além do prazo de
  conteúdo livre, o texto original de mensagens, comentários, descrições
  e corpo de entrada deixa de ser recuperável após a passagem. 0 linhas
  dessas entidades são apagadas só para cumprir o prazo.
- **SC-002**: Em verificação antes/depois da anonimização, 100% das
  contagens de mensagens, de solicitações por tipo e de avaliações por
  nota permanecem iguais.
- **SC-003**: Em 100% dos hóspedes cuja última saída confirmada passou do
  prazo de ficha, a ficha deixa de ser recuperável após a passagem, junto
  com o consentimento daquela pessoa. 0 cópias de nome, documento ou
  telefone dessa pessoa permanecem na reserva.
- **SC-004**: Em 100% das estadias ainda dentro do prazo, ou sem saída
  confirmada, 0 conteúdos são substituídos e 0 fichas são apagadas.
- **SC-005**: Em 100% das passagens, existe comprovante com instante e
  quantidades por tipo (inclusive zeros). Em 100% desses comprovantes e
  dos registros operacionais da passagem, 0 conteúdos pessoais tratados
  aparecem.
- **SC-006**: Em verificação com dois hotéis, 0% dos dados e 0% dos
  comprovantes de um são afetados ou visíveis no outro.
- **SC-007**: Em sessão de recepção ou operacional, 100% das tentativas
  de ler o comprovante são recusadas. Em sessão de gestão da própria
  propriedade, 100% das consultas ao comprovante são permitidas.
- **SC-008**: Em propriedade sem prazo válido, 100% das passagens
  registram prazo ausente e 0 tratamentos daquele tipo ocorrem com
  intervalo embutido.
- **SC-009**: Segunda passagem sobre o mesmo conjunto já tratado conta 0
  tratamentos novos e não restaura texto nem ficha. O caminho passagem
  automática → conteúdo vencido irrecuperável → volume intacto → ficha
  vencida apagada → comprovante consultável é verificável sem mensagem ao
  hóspede e sem o sistema de gestão do hotel.
- **SC-010**: Em 100% das execuções desta fatia, 0 mensagens são enviadas
  a hóspede, 0 fases de reserva são confirmadas e 0 disparos manuais de
  expurgo existem no painel.

## Assumptions

- A fatia F0.2 (esquema) e as fatias de estadia até a confirmação de
  saída (F4.1) estão concluídas. O instante real da partida já é gravado
  no clique de saída. Esta fatia **não** cria a confirmação de partida:
  só passa a usá-la como eixo do relógio.
- **Cada cadastro de reserva cria hóspede novo** (decisão da F1.1). Na
  prática do MVP, “última reserva vinculada” costuma ser a única. A regra
  mesmo assim é a da documentação: a ficha só cai quando a **última**
  reserva vinculada àquela ficha venceu o prazo de cinco anos.
- **Conteúdo livre no prazo de doze meses** cobre o que o dicionário já
  classificou como dado pessoal em conteúdo livre na estadia: mensagem,
  comentário de avaliação, descrição de solicitação e corpo de entrada da
  conversa, mais a saída bruta do classificador (pode ecoar o texto). Não
  cobre nota de avaliação, eixos estruturados, tipo de chamado, valor de
  consumo nem catálogo.
- **Ficha no prazo de cinco anos** cobre a identidade e o consentimento
  daquela pessoa. A reserva operacional permanece, porque datas e volume
  de estadia não são o dado cadastral. Identificadores copiados para a
  reserva (telefone de contato, nome) saem com a ficha para a pessoa não
  continuar identificável por outro caminho.
- **Prazos na configuração da propriedade**, semeados na instalação com
  os valores já públicos (12 meses e 5 anos). Não há tela nova para
  editá-los nesta fatia. Ausência não usa default no verificador — o
  mesmo padrão das outras passagens temporais. Quem um dia alterar as
  chaves é a gestão (parâmetro de comportamento), não a recepção.
- **Passagem automática**, encaixada nas demais verificações temporais já
  existentes. Cadência diária conforme a arquitetura documentada. Sem
  agendador externo novo. Sem botão no painel.
- Superfície de consulta do comprovante: consulta autenticada da gestão,
  no mesmo padrão das fatias já entregues (comportamento observável sem
  tela React obrigatória).
- Não existe auditoria genérica de alteração no produto (limitação já
  honesta). O comprovante desta fatia é **específico** da retenção:
  quantidades por tipo e instante, não o histórico de qualquer campo.
- Pedido avulso de exclusão, portabilidade e correção a pedido do titular
  ficam para fatia futura. Esta entrega o calendário que a documentação
  já prometeu.
- Limitação honesta: enquanto a recepção não confirmar a saída, o relógio
  não anda. Estadia esquecida no status hospedado acumula dado. Isso já é
  visível na fila; esta fatia não contorna a premissa de não se integrar
  ao outro sistema do hotel.
