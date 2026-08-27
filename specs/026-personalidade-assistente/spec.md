# Feature Specification: Personalidade da assistente e aviso de IA

**Feature Branch**: `026-personalidade-assistente`

**Created**: 2026-08-27

**Status**: Draft

**Input**: User description: "A propriedade descreve, em texto livre, o tom que
a assistente deve ter ao conversar com o hóspede. Esse tom afeta a forma das
respostas automáticas, nunca o conteúdo: a assistente continua limitada aos
fatos do catálogo, e nenhuma instrução da propriedade é capaz de remover esse
limite. A primeira mensagem de cada estadia informa ao hóspede que o
atendimento inicial é feito por uma assistente virtual e que uma pessoa assume
quando necessário."
(backlog F7.2)

Restrições já decididas no projeto (entrada do specify): o aviso de assistente
virtual na primeira mensagem da estadia **já foi entregue** na fatia anterior
(F7.1) — esta fatia o mantém e não o reabre para edição da casa; o tom é texto
livre na configuração da propriedade, não uma lista fechada de rótulos; a
regra que limita a assistente aos fatos do catálogo é aplicada **depois** da
descrição de tom e fica fora do alcance de quem edita o campo; na dúvida um
humano vê; conteúdo de mensagem de hóspede continua fora do log; o sistema não
se integra ao sistema de gestão do hotel. Linha de convite editável no recado
(F7.3), módulos por propriedade (F7.4) e canal de e-mail (F7.5) permanecem
fora.

## Clarifications

### Session 2026-08-27

- Q: Sem a tela do painel nesta fatia, por onde a gestão lê e grava a descrição de tom da assistente? → A: Operações próprias de ler e gravar só este campo, sem tela nova; a gestão usa a API, como já faz com o catálogo.
- Q: A descrição de tom pode ter quebra de linha e tabulação, ou a gravação recusa esses caracteres como nos três textos de boas-vindas? → A: Aceita quebra de linha e tabulação; recusa acima de 500 caracteres e demais caracteres de controle.
- Q: Se o tom manda inventar um fato e a redação tenta obedecer, mesmo com a dúvida coberta pelo catálogo, o hóspede recebe a resposta fiel ao catálogo ou a conversa vai para a recepção? → A: Recusa a redação inventada e encaminha à recepção, como já acontece quando a resposta não é fiel ao catálogo. Não nasce caminho que limpa a invenção e envia.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A casa descreve o tom da assistente (Priority: P1)

Como gestão da propriedade, quero descrever em texto livre o tom com que a
assistente deve falar com o hóspede (por exemplo, acolhedora e breve, ou
formal e discreta), e quero que o campo vazio não quebre o atendimento — a
assistente continua com a voz padrão do produto — para o hotel de nicho não
ficar preso a três rótulos genéricos e para uma casa que ainda não escreveu
nada continuar operando.

**Why this priority**: Sem o campo, o restante da fatia não existe. É o que
distingue “a assistente soa como a casa” de “a assistente soa igual em todo
hotel”. Vazio quebrar o atendimento seria pior do que não ter personalidade.

**Independent Test**: Pode ser testado pelas operações próprias de ler e
gravar só este campo (sem tela nova, no mesmo molde do catálogo): gestão
grava uma descrição válida e lê de volta; grava vazio (ou só espaços) e a
assistente continua respondendo dúvida coberta com a voz padrão; recepção
lê e não grava; perfil operacional é recusado nos dois.

**Acceptance Scenarios**:

1. **Given** uma sessão autenticada de perfil de gestão e uma descrição de
   tom dentro do tamanho máximo, **When** a gestão grava o texto, **Then** a
   configuração daquela propriedade passa a guardar essa descrição, e a
   leitura seguinte devolve o mesmo texto (após remover espaços nas
   extremidades).
2. **Given** descrição de tom vazia ou composta só de espaços, **When** a
   gestão grava, **Then** a gravação é aceita e a assistente continua
   funcionando: uma dúvida coberta pelo catálogo ativo recebe resposta
   automática na voz padrão do produto, sem exigir que alguém preencha o
   campo.
3. **Given** propriedade recém-instalada, **When** a gestão consulta o tom,
   **Then** o campo já existe e está vazio — a casa opera com voz padrão
   até alguém escrever.
4. **Given** uma sessão de recepção ou de perfil operacional, **When** se
   tenta gravar o tom, **Then** a alteração é recusada e o valor anterior
   permanece. A recepção **pode ler**; o perfil operacional não lê nem
   grava.

---

### User Story 2 - O tom muda a forma, nunca o fato (Priority: P1)

Como hóspede já hospedado, quero que a resposta automática a uma dúvida
coberta pelo catálogo soe com o tom que a casa descreveu, sem o conteúdo
mudar: o que a assistente afirma continua sendo só o que está no catálogo
daquela propriedade.

**Why this priority**: É o valor visível da fatia. Um campo que se grava e
não altera nenhuma resposta é configuração morta. Um campo que altera o
**fato** afirmado seria o hotel reescrevendo o catálogo por um atalho
inseguro.

**Independent Test**: Pode ser testado com a mesma dúvida coberta pelo mesmo
catálogo ativo, uma vez com tom vazio e outra com tom preenchido (por
exemplo, “seja breve e caloroso”), usando inteligência controlada que
devolve redações fiéis ao catálogo: as duas respostas afirmam o mesmo fato;
a redação com tom preenchido é observavelmente distinta da voz padrão; nenhum
chamado nasce só porque o tom existe.

**Acceptance Scenarios**:

1. **Given** uma dúvida coberta pelo catálogo ativo e tom vazio, **When** o
   processamento conclui, **Then** o hóspede recebe resposta automática fiel
   a esse catálogo, na voz padrão.
2. **Given** a mesma dúvida, o mesmo catálogo e um tom preenchido válido,
   **When** o processamento conclui, **Then** o hóspede recebe resposta
   automática que continua fiel ao mesmo fato do catálogo, com redação
   distinta da voz padrão.
3. **Given** tom preenchido, **When** a assistente responde, **Then** ela
   **não** afirma horário, preço, serviço ou regra que não estejam no
   catálogo ativo daquela propriedade — o tom não amplia o que pode ser
   dito.
4. **Given** recados que o produto já redige em texto fixo (boas-vindas,
   confirmação de pedido, confirmação de reclamação, pulso, lista de
   pedidos feitos pelo chat, aviso de que a recepção vai atender),
   **When** o tom da casa está preenchido, **Then** esses recados **não**
   mudam de conteúdo nem de redação: o tom vale só para a resposta
   automática composta a partir do catálogo.

---

### User Story 3 - Instrução para ignorar o catálogo não surte efeito (Priority: P1)

Como titular da conversa e como hotel, quero que um texto de tom que mande a
assistente ignorar o catálogo, inventar fato, revelar dado de outro hóspede
ou deixar de encaminhar a uma pessoa **não tenha efeito**: a resposta
continua fiel ao catálogo da casa, e o pedido de falar com uma pessoa
continua indo para a recepção.

**Why this priority**: É critério de segurança, não de qualidade. Campo de
texto livre que influencia a redação é superfície de ataque. Sem este
cenário, a fatia entregaria um atalho para desligar a regra que o produto
não negocia.

**Independent Test**: Pode ser testado gravando um tom que instrua a
assistente a ignorar o catálogo e a inventar um horário, fazendo uma dúvida
cujo fato **está** no catálogo (e outra cujo fato **não** está), com
inteligência controlada configurada para devolver o que o tom pediria se
fosse obedecido: o hóspede não recebe a redação inventada; a recepção vê
pendência; dúvida descoberta continua o aviso de que a recepção vai
atender; nenhum dado de outro hotel ou de outro hóspede aparece.

**Acceptance Scenarios**:

1. **Given** tom que instrua a ignorar o catálogo e a afirmar um horário
   que **não** está cadastrado, e uma dúvida coberta cujo fato cadastrado é
   outro, **When** a redação tentada inclui esse horário inventado,
   **Then** o hóspede **não** recebe essa redação: o desfecho é o já
   especificado quando a resposta não é fiel ao catálogo (aviso de que a
   recepção vai atender e pendência visível). MUST NOT haver um segundo
   caminho que “limpe” a invenção e envie só o fato cadastrado.
2. **Given** o mesmo tom subversivo e uma dúvida **não** coberta pelo
   catálogo, **When** o sistema trata a pergunta, **Then** o desfecho é o já
   especificado da fatia de dúvida: aviso ao hóspede de que a recepção vai
   atender e chamado visível — **não** uma resposta inventada “no tom da
   casa”.
3. **Given** tom que instrua a nunca chamar uma pessoa e a continuar
   conversando sozinha, **When** o hóspede pede para falar com uma pessoa,
   **Then** a mensagem é encaminhada à recepção e a assistente **não**
   insiste com nova resposta automática.
4. **Given** qualquer tom da propriedade A, **When** um hóspede da
   propriedade B pergunta, **Then** a redação e o catálogo usados são os de
   B — o tom de A não vaza.

---

### User Story 4 - O hóspede sabe com quem fala e consegue uma pessoa (Priority: P1)

Como hóspede, quero que a primeira mensagem da estadia continue dizendo que o
atendimento inicial é por assistente virtual e que uma pessoa assume quando
necessário; e quero que, quando eu pedir para falar com uma pessoa, isso
aconteça sem a assistente insistir em me atender sozinha.

**Why this priority**: O aviso já é postura do produto (entregue na F7.1).
Esta fatia fecha o outro lado da mesma promessa: o pedido de humano não
pode ser engolido pelo tom da casa nem por uma assistente “prestativa
demais”. Sem isso, o aviso na primeira mensagem seria só texto.

**Independent Test**: Pode ser testado confirmando a chegada e lendo a
primeira mensagem (aviso presente, texto fixo, uma vez); e enviando, já na
estadia, um pedido explícito para falar com uma pessoa, com classificação
válida de fora de escopo: encaminhamento visível à recepção, zero resposta
automática adicional tentando continuar a conversa.

**Acceptance Scenarios**:

1. **Given** uma confirmação de chegada bem-sucedida com o recado apto a
   sair, **When** o envio é processado, **Then** a primeira mensagem da
   estadia informa que o atendimento inicial é feito por uma assistente
   virtual e que uma pessoa da recepção assume quando necessário. O texto
   do aviso continua fixo do produto: a propriedade não o edita, não o
   omite e não o substitui pelo campo de tom.
2. **Given** o hóspede já hospedado que pede para falar com uma pessoa,
   **When** a mensagem é classificada como fora de escopo, **Then** a
   recepção da propriedade vê pendência humana, o hóspede **não** recebe
   resposta automática da assistente tentando resolver no lugar da pessoa,
   e o tom da casa **não** altera esse desfecho.
3. **Given** o mesmo pedido de humano, **When** se observam as mensagens
   seguintes automáticas daquela conversa, **Then** a assistente **não**
   reenvia convite a continuar pelo chat, **não** pergunta se o hóspede
   “não quer tentar com ela primeiro”, e **não** dispara segunda
   classificação do mesmo texto para insistir.
4. **Given** coleta ou lembrete da pré-chegada, **When** essas mensagens
   saem, **Then** o aviso de assistente virtual **não** aparece nelas — a
   estadia ainda não começou. (Comportamento já entregue; esta fatia não o
   relaxa.)

---

### User Story 5 - Limite, permissão e conversa fora do log (Priority: P2)

Como gestão e como titular dos dados, quero que a descrição de tom tenha um
tamanho máximo recusado acima dele, que só quem deve altere esse campo, e
que o texto do hóspede continue fora do log mesmo quando o tom entra na
redação, para um campo livre não virar mural sem teto nem cópia da conversa.

**Why this priority**: Sem teto, o campo vira superfície de abuso. Sem
permissão estreita, a recepção herdaria o poder de mudar como o sistema se
comporta com o hóspede. Sem o log limpo, depurar o tom vaza a conversa.

**Independent Test**: Pode ser testado gravando texto no limite (aceito) e
um caractere acima (recusado, valor anterior intacto); tentando gravar com
recepção e com perfil operacional; e inspecionando logs de uma redação com
tom preenchido: identificadores e códigos, sem texto de hóspede e sem
copiar a descrição de tom para o log.

**Acceptance Scenarios**:

1. **Given** uma descrição com exatamente o tamanho máximo permitido,
   **When** a gestão grava, **Then** a gravação é aceita.
2. **Given** uma descrição com um caractere acima do máximo, **When** a
   gestão tenta gravar, **Then** a alteração é recusada, a gestão vê que o
   texto é longo demais, e o valor anterior permanece. Nenhum recorte
   silencioso.
3. **Given** uma descrição com quebra de linha ou tabulação, dentro do
   tamanho máximo, **When** a gestão grava, **Then** a gravação é aceita e
   a leitura devolve o mesmo texto.
4. **Given** uma descrição com caractere de controle que não é quebra de
   linha nem tabulação, **When** a gestão tenta gravar, **Then** a
   alteração é recusada e o valor anterior permanece.
5. **Given** redação automática com tom preenchido, **When** o sistema
   registra log operacional, **Then** aparecem identificadores e a
   propriedade — e não o conteúdo da mensagem do hóspede, não a descrição
   de tom e não a redação enviada.
6. **Given** hotel A e hotel B, **When** a gestão de A altera o tom, **Then**
   o tom de B permanece intacto e as respostas de B não mudam.

---

### Edge Cases

- Descrição só com espaços é tratada como vazia: voz padrão, não um tom
  “em branco” que altere a redação.
- Quebra de linha e tabulação na descrição são aceitas. Outro caractere
  de controle (por exemplo nulo) é recusado por inteiro, sem recorte.
  A defesa contra injeção não depende dessa recusa: a regra do catálogo
  continua depois do tom.
- Tom recém-gravado vale na **próxima** resposta automática composta a
  partir do catálogo. Não exige reinício do processamento. Trabalho já em
  curso pode concluir com o tom que leu ao começar — não se reprocessa
  mensagem já respondida só porque o tom mudou.
- Tom que instrua a assistente a oferecer produto, inventar promoção ou
  afirmar fato de outro hotel: o conteúdo continua recusado pelo catálogo
  da propriedade da reserva. Nenhuma instrução da casa amplia o que pode
  ser afirmado.
- Tom que instrua a ignorar o aviso de assistente virtual: o aviso na
  primeira mensagem **não muda**. Ele não passa pelo campo de tom.
- Pedido de humano misturado com dúvida coberta (“que horas é o café? e
  chama a recepção”) segue a classificação já existente; esta fatia **não**
  inventa sétima intenção nem desempate novo. O que entra é: uma vez
  encaminhado a humano, a assistente não insiste.
- Dúvida coberta com tom preenchido e inteligência indisponível: o
  desfecho continua o encaminhamento humano já especificado. O tom não
  cria um segundo caminho de falha.
- Classificar intenção, extrair ficha, reconhecer item vendável e ler
  pesquisa de saída **não** recebem o tom da casa. O tom não pode
  enviesar a taxonomia nem a extração.
- Recados de texto fixo do produto (confirmações, pulso, lista de pedidos
  feitos pelo chat, coleta, lembrete) não são reescritos no tom da casa.
- Dois hotéis: cada um tem o próprio tom; vazio em um não herda o do outro.
- Hotel A não usa catálogo, tom nem conversa do hotel B.
- Verificação automatizada usa inteligência controlada e não chama rede.
  O teste de injeção configura o controlado para devolver o que o tom
  pediria se fosse obedecido: essa redação é recusada e a recepção vê
  pendência — o mesmo desfecho de resposta não fiel ao catálogo. MUST NOT
  nascer um caminho que limpe a invenção e envie.
- Esta fatia **não** torna o aviso editável, **não** acrescenta linha de
  convite no recado, **não** muda a taxonomia de intenção, **não** liga
  tela nova do painel operacional (ler e gravar o tom é por operações
  próprias, como o catálogo) e **não** se integra ao sistema de gestão do
  hotel.
- Limitação honesta: o tom influencia a **forma** da redação automática
  quando o cérebro a compõe. Não há garantia de que duas casas com tons
  diferentes produzam contrastes literários perceptíveis em toda pergunta;
  a garantia testável é que o tom preenchido é considerado na composição,
  que o fato afirmado permanece o do catálogo, e que a injeção não vence.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A propriedade MUST poder guardar uma descrição em texto livre
  do tom da assistente. MUST haver no máximo uma descrição vigente por
  propriedade.
- **FR-002**: Descrição vazia ou só de espaços MUST ser aceita e MUST
  equivaler à voz padrão do produto. MUST NOT impedir resposta automática
  a dúvida coberta pelo catálogo.
- **FR-003**: Propriedade recém-instalada MUST nascer com o campo presente
  e vazio (voz padrão), sem exigir preenchimento para operar.
- **FR-004**: Devem existir operações próprias de ler e de gravar só a
  descrição de tom, sem tela nova nesta fatia (o mesmo molde do catálogo).
  Somente a gestão MUST gravar. A recepção MUST poder ler e MUST NOT
  gravar. O perfil operacional MUST ser recusado na leitura e na
  gravação. As operações MUST cobrir só este campo — MUST NOT abrir
  alteração genérica da configuração da propriedade.
- **FR-005**: A descrição MUST ter tamanho máximo de 500 caracteres depois
  de remover espaços das extremidades. Texto acima desse limite MUST ser
  recusado por inteiro, com sinalização de que é longo demais. MUST NOT
  haver recorte silencioso. Texto no limite MUST ser aceito. Quebra de
  linha e tabulação MUST ser aceitas (é parágrafo de voz, não slot de
  recado). Demais caracteres de controle MUST ser recusados por inteiro,
  com o valor anterior intacto.
- **FR-006**: Tom preenchido MUST ser considerado na composição da
  resposta automática a dúvida coberta pelo catálogo ativo, de modo que a
  redação possa diferir da voz padrão. O fato afirmado MUST permanecer
  restrito a esse catálogo.
- **FR-007**: Tom preenchido MUST NOT alterar recados de texto fixo do
  produto (boas-vindas, aviso de assistente virtual, confirmações, pulso,
  lista de pedidos feitos pelo chat, coleta, lembrete, aviso de que a
  recepção vai atender).
- **FR-008**: Tom preenchido MUST NOT ser aplicado a classificar intenção,
  extrair ficha, reconhecer item vendável nem ler pesquisa de saída.
- **FR-009**: Nenhuma instrução presente na descrição de tom MUST ser
  capaz de remover o limite do catálogo. Fato que não está no catálogo
  ativo da propriedade da reserva MUST NOT ser afirmado ao hóspede, mesmo
  que o tom peça para inventar, ignorar o catálogo ou “responder mesmo
  assim”.
- **FR-010**: A regra que limita a assistente aos fatos do catálogo MUST
  ser aplicada depois da descrição de tom e MUST permanecer fora do
  alcance de quem edita o campo. Quando a redação tentada não for fiel ao
  catálogo (inclusive porque o tom pediu para inventar), o sistema MUST
  recusar essa redação e MUST encaminhar à recepção pelo desfecho já
  especificado de resposta não fiel — MUST NOT construir um caminho novo
  que descarte a invenção e envie uma resposta automática “limpa”. Teste
  desta fatia MUST incluir o caso em que o tom pede para ignorar o
  catálogo e a redação tentada inventaria fato: o hóspede não recebe
  essa redação e a recepção vê a pendência.
- **FR-011**: A primeira mensagem de cada estadia MUST continuar informando
  que o atendimento inicial é por assistente virtual e que uma pessoa da
  recepção assume quando necessário. O texto desse aviso MUST permanecer
  fixo do produto. MUST NOT nascer slot na configuração da casa para
  editá-lo, omiti-lo ou substituí-lo pelo tom.
- **FR-012**: Hóspede que pede para falar com uma pessoa MUST ser
  encaminhado à recepção da propriedade, pelo caminho já especificado de
  fora de escopo. MUST NOT haver resposta automática insistindo em
  continuar o atendimento. O tom da casa MUST NOT suprimir nem atrasar
  esse encaminhamento.
- **FR-013**: Reprocessar a mesma mensagem já respondida MUST NOT gerar
  segunda resposta só porque o tom foi alterado depois.
- **FR-014**: Tom gravado MUST valer na próxima composição de resposta
  automática daquela propriedade, sem reinício do processamento.
- **FR-015**: Resolução MUST considerar a propriedade da reserva; tom,
  catálogo e conversa de um hotel MUST NOT vazar para outro.
- **FR-016**: Conteúdo de mensagem de hóspede, descrição de tom e redação
  enviada NUNCA MUST aparecer em log operacional; logs registram
  identificadores, a propriedade e códigos de resultado.
- **FR-017**: A verificação desta fatia MUST ser possível sem o serviço
  real de linguagem: inteligência controlada devolve redações previsíveis
  (voz padrão, tom aplicado, injeção tentando inventar fato). Nenhum
  teste MUST chamar o serviço real nem depender de rede.
- **FR-018**: Esta fatia MUST NOT acrescentar linha de convite editável no
  recado de chegada, MUST NOT alterar a taxonomia de intenção, MUST NOT
  confirmar chegada ou saída por conta própria e MUST NOT integrar-se ao
  sistema de gestão do hotel.
- **FR-019**: Persistência da mensagem MUST continuar ocorrendo antes da
  tentativa de envio. Falha ao compor no tom da casa MUST degradar para o
  encaminhamento humano já especificado — MUST NOT enviar fato inventado
  e MUST NOT apagar histórico.

### Key Entities

- **Descrição de tom**: texto livre, por propriedade, que orienta a
  **forma** das respostas automáticas compostas a partir do catálogo.
  Vazio equivale à voz padrão. Tamanho máximo 500 caracteres. Aceita
  quebra de linha e tabulação; recusa demais caracteres de controle.
  Não é o catálogo e não é o aviso de assistente virtual.
- **Voz padrão**: redação automática usada quando a descrição de tom está
  vazia. É a voz que o produto já emprega hoje, sem parágrafo promocional
  inventado para preencher o vazio.
- **Regra do catálogo**: limite inegociável — a assistente só afirma fato
  cadastrado no catálogo ativo da propriedade da reserva. Aplicada depois
  da descrição de tom, fora do alcance de quem edita o campo.
- **Aviso de assistente virtual**: frase fixa do produto na primeira
  mensagem de cada estadia (já entregue). Não é parâmetro da propriedade e
  não é influenciada pelo tom.
- **Encaminhamento humano por pedido do hóspede**: pendência visível à
  recepção quando a intenção é fora de escopo (incluindo pedido explícito
  de falar com uma pessoa). Sem resposta automática de insistência.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das propriedades recém-instaladas, o campo de tom
  existe, está vazio e a assistente responde dúvida coberta sem exigir
  preenchimento.
- **SC-002**: Em roteiro equivalente (mesma dúvida, mesmo catálogo ativo),
  100% das respostas com tom vazio e com tom preenchido afirmam o mesmo
  conjunto de fatos do catálogo. A única diferença permitida é a forma da
  redação.
- **SC-003**: Em 100% dos casos em que o tom pede para ignorar o catálogo
  ou inventar fato e a redação tentada obedece, 0 dessas redações chegam
  ao hóspede e 100% viram encaminhamento à recepção pelo desfecho já
  existente de resposta não fiel. 0 caminhos novos de “limpar e enviar”.
- **SC-004**: Em 100% dos recados de boas-vindas enviados, o hóspede é
  informado de que o atendimento inicial é por assistente virtual e de
  que uma pessoa da recepção assume quando necessário. Em 100% das
  propriedades, 0% conseguem editar, omitir ou substituir esse aviso pelo
  campo de tom.
- **SC-005**: Em 100% dos pedidos explícitos para falar com uma pessoa
  classificados como fora de escopo, a recepção vê pendência humana e o
  hóspede recebe 0 respostas automáticas de insistência. Tom preenchido
  não reduz essa taxa.
- **SC-006**: Em 100% das tentativas de gravar texto acima de 500
  caracteres, a alteração é recusada e o valor anterior permanece. Em
  100% das gravações com exatamente 500, a alteração é aceita.
- **SC-007**: Em 100% das tentativas de alteração por recepção ou perfil
  operacional, 0 valores de tom mudam. Em verificação com dois hotéis, 0%
  dos tons, catálogos ou conversas de um são afetados ou visíveis no
  outro.
- **SC-008**: Em 100% dos registros operacionais desta fatia, 0 conteúdos
  de mensagem de hóspede, 0 descrições de tom e 0 redações enviadas
  aparecem em log.
- **SC-009**: 100% dos testes automatizados desta fatia concluem sem
  chamar o serviço real de linguagem e sem depender de rede.
- **SC-010**: Recados de texto fixo do produto permanecem inalterados em
  100% das propriedades com tom preenchido.
- **SC-011**: O caminho gestão grava tom → próxima dúvida coberta soa com
  esse tom, fiel ao catálogo → tom subversivo não inventa fato → hóspede
  pede pessoa e a recepção vê, sem insistência, é verificável sem o
  serviço real de linguagem e sem o sistema de gestão do hotel.

## Assumptions

- As fatias F7.1 (inteligência real e aviso de assistente virtual), F3.2
  (classificar) e F3.3 (responder pelo catálogo) estão concluídas. O aviso
  na primeira mensagem, a taxonomia (incluindo fora de escopo → humano) e
  a recusa de fato fora do catálogo já existem. Esta fatia **não** os
  redesenha: acrescenta o tom da casa e fecha que esse tom não vence o
  catálogo nem o pedido de humano.
- **Quem altera o tom é a gestão.** O campo muda como o sistema se
  comporta com o hóspede e é superfície de injeção; não é texto
  operacional de balcão (esses três slots de entrada continuam da
  recepção). Permissão estreita, só deste campo — o mesmo recorte já
  usado para não criar alteração genérica da configuração da propriedade.
- **Tamanho máximo: 500 caracteres** depois de remover espaços das
  extremidades. Cabe um parágrafo de voz (hotel de nicho) e limita o
  volume de texto que tenta subverter a regra do catálogo. Não herda o
  formato dos slots de boas-vindas: aqueles recusam quebra de linha
  porque são variável de recado curto; este campo não viaja nesse recado
  e aceita quebra de linha e tabulação. Demais caracteres de controle
  são recusados. A injeção continua vencida pela regra do catálogo
  depois do tom, não pela proibição de quebra de linha.
- **Vazio é válido.** Diferente dos slots de entrada, tom em branco não
  bloqueia boas-vindas nem resposta. Propriedade nova já nasce com o
  campo vazio.
- **O tom vale só na resposta automática composta a partir do catálogo**
  (dúvida coberta). Classificação, extração de ficha, item vendável,
  pesquisa de saída e recados de texto fixo ficam de fora: o hotel muda a
  forma de falar sobre o que já publicou, não o roteamento nem as frases
  que o produto prometeu.
- **A regra do catálogo vem depois do tom.** Decisão já registrada no
  backlog da fase: o hotel muda o tom, nunca o limite do que a assistente
  pode afirmar. Se a redação tentada não for fiel — mesmo com a dúvida
  coberta — o desfecho é o já existente: recusa e encaminhamento à
  recepção. Não se inventa um “reescrever sem a invenção e enviar”.
- **Pedido de humano reutiliza fora de escopo.** Não nasce sétima
  intenção. “Sem insistência” significa: zero resposta automática tentando
  continuar depois do encaminhamento — o tom não adiciona uma pergunta de
  “tem certeza?”.
- **Efeito na próxima composição, sem reinício.** Trabalho já em curso
  pode terminar com o tom que leu; mensagem já respondida não é refeita.
- **Verificação sem rede.** Inteligência controlada simula voz padrão,
  tom aplicado e redação que obedeceria à injeção. Nenhum teste consome
  chamada do serviço real.
- **Voz padrão** é a redação atual, sem parágrafo institucional inventado
  para o vazio. Preencher o campo é opcional.
- Superfície de uso: operações próprias de ler e gravar só a descrição de
  tom (gestão grava; recepção lê), histórico da conversa e encaminhamento
  visível à recepção. Sem tela nova nesta fatia — o mesmo molde do
  catálogo. A tela dedicada nasce na fase do painel.
- Esta fatia estava listada como corte possível no plano de uma semana
  (entrava só o aviso). Está sendo especificada agora como o restante da
  F7.2, depois do aviso já entregue.
- Limitação honesta (Artigo XV): o contraste de tom entre duas casas
  depende do cérebro que redige; o produto garante fidelidade ao catálogo
  e recusa de injeção, não um “teste cego” de estilo em toda pergunta. O
  clique humano de chegada continua necessário para o aviso sair.
