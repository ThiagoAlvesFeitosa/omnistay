# Feature Specification: Fila do dia e cadastro de reserva

**Feature Branch**: `029-fila-dia-reserva`

**Created**: 2026-08-31

**Status**: Draft

**Input**: User description: "A recepção vê, na tela inicial, quem chega
hoje, quem já está hospedado e quem deveria ter chegado e não foi
confirmado. Da mesma tela ela cadastra uma reserva nova com nome,
telefone e datas, e confirma a chegada de quem apareceu no balcão.
Reservas com pendência — ficha incompleta, recado de boas-vindas não
enviado, chegada vencida — são destacadas."
(backlog F8.2)

Restrições já decididas no projeto (entrada do specify): cadastrar
reserva, listar a fila nominada do hotel e confirmar chegada **já
existem** (F1.1, F2.2) — esta fatia não inventa campo, estado, prazo
nem recado de boas-vindas; a casca e o login já entregam o destino
“fila do dia” e o destino “nova reserva” só para recepção (F8.1); o
que a autorização recusa, a tela não oferece; gestão e perfil
operacional não vêem lista com nome nem telefone; o sistema não se
integra ao sistema de gestão do hotel — a confirmação de chegada
continua sendo clique da recepção; conteúdo de mensagem, nome e
telefone continuam fora do log. Completar ficha no balcão e copiar
para o PMS (F8.3), confirmar saída e tratar consumo (F8.5), editar
textos de boas-vindas (F8.6) e e-mail do hóspede (F7.5, corte
declarado) permanecem fora.

## Clarifications

### Session 2026-08-31

- Q: No resumo no topo da fila, uma reserva com entrada prevista já passada e chegada ainda não confirmada entra em qual conta? → A: Três contas distintas, sem repetir linha: hoje ainda não confirmadas · já hospedados · entrada vencida sem confirmação. Cada linha entra em uma só.
- Q: Se a fila do dia não carrega quando a recepção abre a tela, o que ela deve ver? → A: Mantém o painel, avisa que a lista não carregou, oferece tentar de novo. Não mostra fila vazia.
- Q: Ao confirmar a chegada na linha da reserva, o clique sozinho registra, ou a recepção precisa confirmar de novo? → A: Um clique registra e atualiza a lista, sem “tem certeza?”. O alvo é um botão com rótulo dentro da linha, não a linha inteira — clicar nome ou telefone não confirma.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver o turno inteiro na fila do dia (Priority: P1)

Como recepcionista no início e no meio do turno, quero abrir a tela
inicial e ver, numa lista só, quem chega hoje, quem já está hospedado
e quem deveria ter chegado e ainda não foi confirmado — nunca quem só
chega em data futura — para operar o balcão sem procurar em outra
agenda e sem descobrir atraso por acaso.

**Why this priority**: É a tela que decide a adoção. Se o recepcionista
precisar navegar para saber quem está no turno, ele volta para o
caderno. Sem a lista real, a casca da F8.1 deixa a recepção numa tela
só com título.

**Independent Test**: Pode ser testado autenticando como recepção num
hotel com reservas de hoje, hospedadas, com entrada prevista já
passada sem confirmação, futuras e já encerradas, e conferindo que a
fila mostra só as três primeiras famílias, com nome, telefone e datas,
e omite futura e encerrada.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção e reservas do próprio hotel com
   entrada prevista para hoje ainda não confirmadas, **When** a pessoa
   abre a fila do dia, **Then** cada uma aparece com o nome, o telefone
   de contato, as datas previstas e a situação atual.
2. **Given** reservas já hospedadas do próprio hotel (ainda não
   encerradas), **When** a recepção abre a fila do dia, **Then** elas
   aparecem na mesma lista, distinguíveis das que ainda aguardam
   confirmação de chegada.
3. **Given** uma reserva cuja data prevista de entrada já passou e a
   chegada ainda não foi confirmada, **When** a recepção abre a fila,
   **Then** essa reserva aparece destacada como chegada vencida — o
   sistema não afirma que a pessoa chegou; afirma que deveria ter
   chegado.
4. **Given** uma reserva com entrada prevista em data futura e uma já
   encerrada ou cancelada, **When** a recepção abre a fila do dia,
   **Then** nenhuma das duas aparece.
5. **Given** a fila do dia aberta, **When** a recepção olha o resumo do
   turno, **Then** vê três contas que não se repetem: quantas ainda
   chegam hoje e não foram confirmadas, quantos já estão hospedados e
   quantas estão com a entrada vencida sem confirmação. A soma das
   três é o número de linhas.
6. **Given** uma sessão de recepção em que a fila do dia não pôde ser
   lida, **When** a pessoa abre a tela inicial, **Then** o painel
   permanece (título, menu, caminho para cadastrar reserva), a lista
   declara que não carregou, dá para tentar de novo, e o estado de
   fila vazia **não** aparece.

---

### User Story 2 - Cadastrar reserva sem sair do turno (Priority: P1)

Como recepcionista, quero registrar uma reserva nova a partir da fila
do dia informando só nome, telefone e datas de entrada e saída, com o
telefone recusado na hora se estiver ilegível para mensageria, para o
hóspede entrar no acompanhamento do hotel sem eu preencher de novo a
ficha que já faço no sistema de gestão.

**Why this priority**: Sem o cadastro na superfície do turno, a fila
fica só leitura de um trabalho que continua em outro lugar. Três
campos é decisão fechada: pedir mais aqui é “mais uma tela para
preencher”.

**Independent Test**: Pode ser testado autenticando como recepção,
abrindo o cadastro a partir da fila, gravando os três campos válidos
com entrada hoje, e conferindo que a reserva aparece na fila; e
tentando telefone inválido e datas invertidas, conferindo recusa sem
gravação.

**Acceptance Scenarios**:

1. **Given** a fila do dia na sessão de recepção, **When** a pessoa
   escolhe cadastrar nova reserva, **Then** vê um formulário só com
   nome, telefone de contato e datas previstas de entrada e saída —
   nenhum outro campo de ficha, e nenhum campo de e-mail.
2. **Given** nome, telefone brasileiro válido e saída posterior à
   entrada, com entrada prevista para hoje, **When** a recepção
   confirma o cadastro, **Then** a reserva é gravada, nasce aguardando
   o cadastro do hóspede e passa a constar na fila do dia, visível
   sem a pessoa precisar pedir a tela de novo.
3. **Given** a pessoa ainda no formulário, **When** o telefone digitado
   não é utilizável (faltam dígitos, DDD inválido ou não é número
   brasileiro), **Then** a recusa aparece na digitação, antes de
   gravar, com mensagem que permite corrigir sem adivinhar a regra.
4. **Given** data de saída anterior ou igual à de entrada, ou nome,
   telefone ou data em branco, **When** a pessoa tenta confirmar,
   **Then** nada é gravado e o que falta ou o que está inconsistente
   fica declarado.
5. **Given** cadastro aceito com entrada prevista em data futura,
   **When** a pessoa volta à fila do dia, **Then** a reserva não
   aparece na lista de hoje e a recepção é informada de que o
   registro foi feito e só entra na fila no dia da entrada.
6. **Given** a pessoa no formulário sem querer gravar, **When** ela
   cancela, **Then** volta à fila do dia e nenhuma reserva nova existe.

---

### User Story 3 - Confirmar a chegada na própria lista (Priority: P1)

Como recepcionista com o hóspede no balcão, quero confirmar a chegada
num botão rotulado na linha daquela reserva e ver a situação virar
hospedado na hora, na mesma lista, para o clique humano continuar
sendo a ponte com o que aconteceu no balcão — sem segundo “tem
certeza?”, sem recarregar a tela e sem ir a outro destino. Ler o
telefone ou o nome na linha não pode disparar a confirmação.

**Why this priority**: É o segundo critério de aceite da fatia e a
travessia de fronteira da chegada. Sem atualizar a lista no lugar, o
recepcionista não confia que o clique pegou.

**Independent Test**: Pode ser testado autenticando como recepção,
acionando o botão rotulado de confirmar chegada numa reserva elegível,
conferindo que a linha passa a hospedado sem passo extra, e conferindo
que clicar nome ou telefone na mesma linha **não** confirma.

**Acceptance Scenarios**:

1. **Given** uma reserva visível na fila em estado que admite chegada
   (ficha completa, ficha parcial ou marcada como chegará sem cadastro
   prévio), **When** a recepção aciona o botão rotulado de confirmar
   chegada nessa linha, **Then** a reserva passa a hospedada no mesmo
   clique — sem passo extra de “tem certeza?” —, o momento real da
   entrada fica registrado, e a própria lista reflete a nova situação
   sem a pessoa pedir a tela de novo.
2. **Given** uma reserva destacada como chegada vencida e elegível à
   confirmação, **When** a recepção aciona o botão rotulado de
   confirmar chegada, **Then** o destaque de vencida desaparece nessa
   linha e o resumo do turno deixa de contá-la como atrasada.
3. **Given** uma reserva ainda só aguardando cadastro (nem ficha
   consolidada, nem marcada como chegará sem cadastro prévio),
   **When** a recepção olha a linha, **Then** o botão de confirmar
   chegada não é oferecido — o salto não é admitido, e a tela não
   convida o clique que seria recusado.
4. **Given** uma reserva já hospedada, encerrada ou cancelada,
   **When** a recepção está na fila, **Then** o botão de confirmar
   chegada não é oferecido nessa linha.
5. **Given** uma tentativa de confirmar que o sistema recusa (estado
   mudou entre a leitura e o clique), **When** a recusa chega,
   **Then** a lista não mente que a pessoa está hospedada, e a
   recepção vê o motivo sem tela vazia.
6. **Given** uma reserva elegível com botão de confirmar chegada
   visível, **When** a recepção clica no nome, no telefone ou em outra
   parte da linha que não seja esse botão, **Then** a chegada **não**
   é registrada e a situação permanece a mesma.

---

### User Story 4 - Pendências distintas, sem misturar o que falta (Priority: P1)

Como recepcionista, quero distinguir na fila ficha incompleta, recado
de boas-vindas não enviado e chegada vencida, cada um com sinal
próprio, para eu saber se o próximo passo é completar dado no balcão,
preencher o recado da casa ou clicar a chegada — e não tratar três
omissões como o mesmo alerta.

**Why this priority**: A ausência de ação humana precisa ser visível, e
visível **sem colapsar**. Chegada vencida e recado não enviado já são
sinais mutuamente exclusivos no trabalho já entregue; a tela não pode
fundí-los. É critério de aceite explícito da fatia.

**Independent Test**: Pode ser testado montando uma reserva de cada
pendência (ficha parcial; hospedado sem recado enviado; entrada
prevista passada sem confirmação) e conferindo três sinais
visualmente distintos, sem um emprestar o rótulo do outro.

**Acceptance Scenarios**:

1. **Given** uma reserva cuja ficha veio incompleta, **When** ela
   aparece na fila, **Then** a ficha é sinalizada como parcial, distinta
   de ficha completa, de ainda aguardando cadastro e de chegará sem
   cadastro prévio.
2. **Given** uma reserva já hospedada cujo recado de boas-vindas não
   saiu, **When** ela aparece na fila, **Then** o sinal “recado não
   enviado” está visível e **não** usa o mesmo destaque da chegada
   vencida.
3. **Given** uma reserva com entrada prevista já passada e chegada
   ainda não confirmada, **When** ela aparece na fila, **Then** o sinal
   de chegada vencida está visível e **não** usa o mesmo destaque do
   recado não enviado.
4. **Given** uma reserva hospedada com recado já enviado e ficha
   completa, **When** ela aparece na fila, **Then** não recebe nenhum
   dos três destaques de pendência.

---

### User Story 5 - Só a recepção opera esta tela (Priority: P1)

Como responsável pelos dados dos hóspedes, quero que gestão e equipe
operacional não vejam a fila nominada nem o cadastro de reserva —
nem pelo menu, nem colando o endereço — para nome e telefone não
vazarem a quem a autorização já recusa.

**Why this priority**: Minimização de dado pessoal. A casca já omite o
destino; esta fatia preenche a tela e não pode enfraquecer o recado:
o que a autorização recusa, a tela não oferece e não exibe.

**Independent Test**: Pode ser testado autenticando gestão e perfil
operacional, conferindo que o menu não oferece fila nem nova reserva,
tentando abrir pelo endereço, e verificando recusa sem nome, telefone
ou lista.

**Acceptance Scenarios**:

1. **Given** uma sessão de gestão, **When** a pessoa tenta abrir a fila
   do dia ou o cadastro de reserva pelo endereço, **Then** o acesso é
   recusado, nenhum nome nem telefone aparece, e não há tela em
   branco.
2. **Given** uma sessão de perfil operacional, **When** a pessoa tenta
   o mesmo, **Then** o efeito visível é o mesmo da gestão: recusa sem
   dado cadastral.
3. **Given** uma sessão de recepção de um hotel, **When** existem
   reservas de outro hotel, **Then** a fila não as mostra e confirmar
   chegada ou cadastrar não as alcança.

---

### Edge Cases

- Fila vazia no turno (ninguém chega hoje, ninguém hospedado, ninguém
  atrasado): a tela continua sendo a fila do dia, com as três contas
  em zero e caminho visível para cadastrar reserva — não uma página
  em branco. Zero no resumo só vale quando a lista realmente não tem
  linhas; não se usa para disfarçar falha de leitura.
- Falha ao ler a fila: o painel permanece; a lista avisa que não
  carregou e oferece tentar de novo. Não é tela de entrada, não é
  página vazia, não é o estado de fila vazia.
- Hospedado com recado não enviado conta como hospedado no resumo, não
  como entrada vencida. Entrada vencida é só quem ainda não foi
  confirmado e cuja data prevista já passou.
- Reserva cadastrada com entrada hoje depois de a fila já estar
  aberta: a nova linha entra na lista sem a pessoa pedir a tela de
  novo.
- Dois cadastros com o mesmo telefone: continuam sendo duas pessoas
  (casal, telefone de empresa); a tela não “reaproveita” ficha.
- Telefone digitado com parênteses, espaços ou hífen: a validação
  olha os dígitos; a recusa ou a aceitação não dependem da máscara.
- Número estrangeiro: recusado, como já é regra do cadastro.
- Saída no dia seguinte à entrada (uma diária): aceita; saída no
  mesmo dia: recusada.
- Reserva ainda aguardando cadastro na fila: aparece (é do turno),
  mas confirmar chegada não é oferecido até a ficha consolidar ou o
  silêncio marcar que chegará sem cadastro prévio.
- Ficha irreconhecível sinalizada para leitura humana: a linha
  permanece na fila; completar no balcão é fatia seguinte.
- Recado não enviado: a fila mostra o sinal; preencher os textos da
  casa é fatia seguinte. Completar os textos não é ação desta tela.
- Hospedado com saída prevista para hoje: permanece na lista como
  hospedado; confirmar a saída **não** entra nesta fatia.
- Abrir a ficha a partir da linha: destino já nomeado no menu, sem o
  trabalho de copiar ou editar — isso é a fatia da ficha.
- Sessão expirada ou revogada no meio do cadastro ou da confirmação:
  volta à tela de entrada, sem dado residual, como na casca.
- Clicar no nome, no telefone ou em qualquer parte da linha que não
  seja o botão rotulado de confirmar chegada: a reserva permanece no
  estado anterior; nenhuma chegada é gravada.
- Confirmação recusada porque outro atendente acabou de confirmar a
  mesma reserva: a lista passa a mostrar hospedado (ou a recusa
  clara); não grava segunda chegada.
- Visitante sem sessão no endereço da fila: tela de entrada, nunca a
  lista.

## Requirements *(mandatory)*

### Functional Requirements

**Fila do dia**

- **FR-001**: A tela inicial da recepção DEVE exibir a fila nominada
  do hotel da sessão: chegadas previstas para hoje ainda não
  confirmadas, reservas já hospedadas e chegadas cuja data prevista
  já passou sem confirmação.
- **FR-002**: A fila NÃO DEVE listar reserva com entrada prevista em
  data futura, reserva encerrada nem reserva cancelada.
- **FR-003**: Cada linha DEVE mostrar nome de contato, telefone de
  contato, data prevista de entrada, data prevista de saída, situação
  da reserva e estado da ficha.
- **FR-004**: A fila DEVE destacar de forma distinta (a) chegada
  vencida não confirmada, (b) recado de boas-vindas não enviado em
  reserva já hospedada, e (c) ficha parcial. Os três sinais NÃO
  DEVEM compartilhar o mesmo rótulo nem o mesmo destaque.
- **FR-005**: Um resumo visível DEVE informar três contas distintas,
  sem repetir linha: (1) entradas previstas para hoje ainda não
  confirmadas, (2) já hospedados, (3) entrada prevista já passada e
  chegada ainda não confirmada. Cada linha da lista DEVE entrar em
  exatamente uma conta. A soma das três DEVE ser o número de linhas.
- **FR-006**: A fila DEVE ordenar as reservas pela urgência da chegada
  prevista (mais próxima primeiro), como a visão operacional já faz.
- **FR-007**: Fila sem linhas DEVE permanecer reconhecível como fila do
  dia, com o cadastro de nova reserva alcançável, sem página vazia.
  Contas em zero NÃO DEVEM ser usadas quando a leitura da lista
  falhou.
- **FR-007a**: Se a fila do dia não puder ser lida, a tela DEVE
  manter o painel (título, menu e caminho para cadastrar reserva),
  declarar que a lista não carregou e oferecer tentar de novo. NÃO
  DEVE mostrar o estado de fila vazia nem devolver à tela de entrada
  só por essa falha.

**Cadastro de reserva**

- **FR-008**: A recepção DEVE poder abrir o cadastro de nova reserva a
  partir da fila do dia, sem passar por outro papel nem por um
  destino que o perfil não usa.
- **FR-009**: O cadastro DEVE pedir exclusivamente nome, telefone de
  contato e datas previstas de entrada e saída. NÃO DEVE pedir
  e-mail, documento, endereço nem qualquer outro campo da ficha.
- **FR-010**: Telefone ilegível para mensageria brasileira DEVE ser
  recusado na digitação, com mensagem que permite corrigir, e NÃO
  DEVE gravar reserva.
- **FR-011**: Nome, telefone ou data em branco, e saída anterior ou
  igual à entrada, NÃO DEVEM gravar reserva. A recusa DEVE nomear o
  que está errado.
- **FR-012**: Cadastro aceito DEVE nascer aguardando o cadastro do
  hóspede. Se a entrada prevista for hoje (ou já passada), a reserva
  DEVE aparecer na fila sem a pessoa pedir a tela de novo.
- **FR-013**: Cadastro aceito com entrada futura DEVE informar que foi
  gravado e que não entra na fila de hoje. NÃO DEVE fingir falha.
- **FR-014**: Cancelar o cadastro DEVE devolver à fila sem gravar.
- **FR-015**: Dois cadastros com o mesmo telefone DEVEM continuar
  criando duas pessoas. A tela NÃO DEVE sugerir reaproveitar ficha
  pelo número.

**Confirmar chegada**

- **FR-016**: A recepção DEVE poder confirmar a chegada de uma reserva
  elegível (ficha completa, ficha parcial ou marcada como chegará sem
  cadastro prévio) acionando um botão com rótulo visível **dentro** da
  linha, sem ir a outro destino e sem passo extra de confirmação.
  Clicar no restante da linha (nome, telefone, datas, situação) NÃO
  DEVE registrar a chegada.
- **FR-017**: Confirmação aceita DEVE atualizar a situação na própria
  lista para hospedado, sem a pessoa pedir a tela de novo, e DEVE
  remover o destaque de chegada vencida dessa linha quando existia.
- **FR-018**: O botão de confirmar chegada NÃO DEVE ser oferecido em
  reserva ainda só aguardando cadastro, já hospedada, encerrada ou
  cancelada.
- **FR-019**: Recusa de confirmação DEVE deixar a lista coerente com o
  estado real e mostrar o motivo, sem página vazia e sem afirmar
  hospedado à toa.
- **FR-020**: Esta tela NÃO DEVE confirmar saída. Hospedado com saída
  prevista para hoje permanece visível; o clique de checkout é fatia
  seguinte.

**Autorização, isolamento e honestidade**

- **FR-021**: Gestão e perfil operacional NÃO DEVEM ver a fila
  nominada nem o cadastro de reserva. Tentativa pelo endereço DEVE
  ser recusada sem nome, telefone ou lista.
- **FR-022**: Sessão de um hotel NÃO DEVE mostrar reserva de outro.
  Confirmar chegada e cadastrar NÃO DEVEM alcançar reserva alheia.
- **FR-023**: Esta fatia NÃO DEVE abrir ou editar ficha, copiar dado
  para colagem externa, editar textos de boas-vindas, lançar consumo,
  resolver chamado nem cadastrar e-mail de hóspede.
- **FR-024**: Esta fatia NÃO DEVE alterar regra de estado da reserva,
  formato de telefone, disparo da coleta, conteúdo do recado de
  boas-vindas, prazo de sessão nem matriz de permissões. NÃO DEVE
  integrar-se ao sistema de gestão do hotel.
- **FR-025**: Log desta fatia NÃO DEVE registrar nome, telefone,
  conteúdo de mensagem nem senha. PODE registrar identificador de
  reserva, identificador de usuário, perfil e código de recusa.
- **FR-026**: Destino “nova reserva” já visível no menu da recepção
  DEVE passar a executar o mesmo cadastro desta fatia, não permanecer
  só como título.

### Key Entities

- **Fila do dia**: visão do turno da recepção — quem chega hoje, quem
  já está no hotel e quem deveria ter chegado e não foi confirmado.
  Não inclui reserva futura, encerrada nem cancelada.
- **Linha da reserva**: nome, telefone, datas, situação, estado da
  ficha e ações cabíveis naquele estado. É a unidade de trabalho do
  balcão nesta fatia.
- **Resumo do turno**: três contas no topo da fila — hoje ainda não
  confirmadas, já hospedados, entrada vencida sem confirmação. Partição
  da lista: cada linha entra em uma só; a soma é o tamanho da fila.
- **Pendência visível**: um de três sinais distintos — chegada
  vencida, recado de boas-vindas não enviado, ficha parcial. Tornar a
  omissão perceptível não a elimina. A conta “entrada vencida” do
  resumo é a mesma família da pendência (a); recado não enviado e
  ficha parcial não ganham conta própria no topo.
- **Cadastro mínimo de reserva**: nome, telefone e datas. Nasce
  aguardando o cadastro do hóspede. O restante da ficha vem pela
  conversa ou no balcão, depois.
- **Confirmação de chegada** *(existente)*: clique da recepção no
  botão rotulado da linha, que registra o instante real da entrada e
  passa a reserva a hospedado. Sem segundo passo. O restante da linha
  não dispara essa ação. Esta fatia é a superfície desse clique.
- **Reserva** *(existente)*: registro da estadia prevista, de um único
  hotel, com ciclo de vida já garantido.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma recepcionista autenticada identifica, em menos de 30
  segundos após abrir a fila, quem ainda chega hoje sem confirmação,
  quem já está hospedado e quem está com a entrada vencida, sem abrir
  outro destino. As três contas do resumo somam o número de linhas e
  0 linha entra em duas contas.
- **SC-002**: 100% das reservas com entrada prevista hoje, hospedadas
  ou com chegada vencida do hotel da sessão aparecem na fila; 0% das
  futuras, encerradas ou canceladas aparecem; 0% das reservas de outro
  hotel aparecem.
- **SC-002a**: Em 100% das falhas ao ler a fila, o painel permanece, a
  lista declara que não carregou, e 0% mostram o estado de fila vazia
  ou tela em branco.
- **SC-003**: A recepção conclui um cadastro válido (três campos, entrada
  hoje) e vê a reserva na fila em menos de 1 minuto, sem pedir a tela
  de novo.
- **SC-004**: 100% das tentativas com telefone ilegível ou com saída
  anterior ou igual à entrada são recusadas na hora e 0 reservas são
  criadas nesses casos.
- **SC-005**: Depois de acionar o botão rotulado de confirmar chegada
  numa reserva elegível, 100% das listas visíveis mostram a reserva
  como hospedada sem passo extra e sem a pessoa pedir a tela de novo,
  e 0% mantêm o destaque de chegada vencida nessa linha.
- **SC-005a**: Em 100% dos cliques no nome, no telefone ou no restante
  da linha (fora do botão rotulado), 0 chegadas são registradas.
- **SC-006**: Em verificação lado a lado, o sinal de chegada vencida e
  o sinal de recado não enviado são distinguíveis em 100% dos casos;
  0% das linhas usam o mesmo rótulo para os dois.
- **SC-007**: 100% das tentativas de gestão e de perfil operacional de
  abrir a fila nominada ou o cadastro são recusadas, com 0 nome e 0
  telefone visíveis.
- **SC-008**: 0 botões de confirmar chegada são oferecidos em linha
  ainda só aguardando cadastro, já hospedada, encerrada ou cancelada.
- **SC-009**: 0 senhas, 0 nomes, 0 telefones e 0 conteúdos de mensagem
  aparecem em log desta fatia.
- **SC-010**: Cada critério de aceite da fatia F8.2 do backlog tem ao
  menos um cenário de aceitação correspondente nesta spec.

## Assumptions

- **O comportamento já existe; falta a superfície.** Cadastrar com
  três campos, recusar telefone e datas, nascer aguardando cadastro,
  isolar por hotel, omitir futura/encerrada/cancelada, destacar
  chegada não confirmada, recusar chegada em estado inadmissível e
  sinalizar recado não enviado foram entregues nas fatias de reserva
  e de chegada. Esta fatia liga isso à tela inicial da recepção.
- **A casca já entrega o destino.** Login, sessão, menu só com o que
  o papel pode usar, e recusa de endereço alheio são F8.1. A fila
  deixa de ser só um título; “nova reserva” deixa de ser só um
  título.
- **Mapa de telas já acordado.** A fila mostra hóspede, datas,
  situação, ficha e ação; o cadastro é o formulário curto alcançável
  da fila (e pelo destino já no menu). Computador no balcão; esta
  fatia não promete layout de mão.
- **Sem e-mail no cadastro.** O desenho de telas chegou a mostrar
  e-mail opcional; o canal de e-mail foi cortado como escopo
  declarado. Pedir o campo aqui prometia o que o sistema não faz.
- **Sem clique de saída nesta fatia.** O desenho de telas mostra
  “confirmar saída” em hospedado. Isso é a fatia de consumos e
  checkout. Aqui o hospedado permanece visível; a saída não se
  confirma.
- **Sem editar ficha nem textos de boas-vindas.** A fila torna a
  pendência visível (Artigo V). Completar campo no balcão, copiar
  para o sistema de gestão, e preencher o recado da casa são fatias
  seguintes.
- **O que o ciclo de vida recusa, a tela não oferece.** Reserva ainda
  só aguardando cadastro aparece na lista (é do turno) mas sem o
  clique de chegada. Ficha parcial e “chegará sem cadastro prévio”
  continuam admitindo o clique, como já é regra.
- **Coleta ao hóspede continua como hoje.** Gravar a reserva segue
  disparando o pedido de cadastro pelo canal já existente. Falha de
  envio não desfaz a reserva; o estado de envio que a fila já
  carrega pode aparecer na situação, sem regra nova.
- **Atualizar a lista sem pedir a tela de novo** vale para cadastro
  com entrada hoje e para confirmação de chegada. Confirmar é um
  clique no botão rotulado, sem diálogo extra e sem desfazer nesta
  fatia. Não exige aviso instantâneo vindo de outro computador: dois
  atendentes no mesmo balcão podem se dessincronizar até a próxima
  ação na tela — limitação honesta, não falha silenciosa da pendência
  na linha de quem clicou.
- **F7.4 (módulos por propriedade) continua fora.** Reserva e fila
  são núcleo: não desligam.
- **Uma propriedade por instalação no uso previsto da demonstração**,
  mas o isolamento por hotel permanece obrigatório.
- **Limitação honesta (Artigo XV):** esta fatia não opera o hotel
  sozinha. Sem ficha, checkout, chamados e catálogo na tela, parte do
  turno continua fora do painel. O clique de chegada continua sem
  falar com o sistema de gestão do hotel: se a recepção não clicar,
  a omissão fica visível (chegada vencida), não desaparece.
