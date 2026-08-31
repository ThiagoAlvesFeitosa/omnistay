# Feature Specification: Ficha do hóspede e transcrição para o PMS

**Feature Branch**: `030-ficha-hospede-pms`

**Created**: 2026-08-31

**Status**: Draft

**Input**: User description: "A recepção abre a ficha de um hóspede,
completa no balcão o que faltou, e copia os dados para o sistema de
gestão do hotel. Fichas parciais são identificadas com os campos
ausentes. O consentimento para contato futuro é visível e revogável."
(backlog F8.3)

Restrições já decididas no projeto (entrada do specify): ler a ficha
do titular e consultar ou registrar consentimento **já existem**
(F1.3, F4.1) — esta fatia não inventa campo cadastral, finalidade de
consentimento nem a regra de nunca reescrever linha antiga;
completar no balcão **não** dispara nova rodada de mensagens (F1.3);
foto de documento nunca é aceita e idade nunca é gravada (Artigo
VIII); o sistema **não** se integra ao sistema de gestão do hotel
(Artigo I) — copiar é auxílio à ponte humana, não envio automático;
e-mail do hóspede permanece fora (F7.5, corte declarado); a casca já
nomeia o destino “ficha do hóspede” só para recepção (F8.1); a fila
do dia já sinaliza ficha parcial (F8.2) e deixa abrir a ficha a
partir da linha para esta fatia; gestão e perfil operacional não
vêem dado cadastral; conteúdo de mensagem, nome, telefone e
documento continuam fora do log.
Confirmar saída, consumos, chamados, catálogo e recado de
boas-vindas permanecem nas fatias seguintes. Acompanhantes além do
titular não entram nesta tela.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Abrir a ficha e ver o que falta (Priority: P1)

Como recepcionista no balcão, quero abrir a ficha do titular a partir
da fila do dia e ver, de imediato, se ela está completa ou parcial,
com cada campo ausente nomeado, para eu não descobrir o buraco só na
hora de digitar no sistema de gestão nem tratar ficha vazia como
pronta.

**Why this priority**: É o primeiro critério de aceite da fatia e o
que torna a pendência da ficha acionável. A fila já avisa “parcial”;
sem abrir e nomear o que falta, o aviso não serve ao turno.

**Independent Test**: Pode ser testado autenticando como recepção,
abrindo a ficha de uma reserva com todos os campos, de uma com parte
faltando e de uma ainda só com nome e telefone, e conferindo o
distintivo (completa × parcial) e a lista dos campos ausentes pelo
nome.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção e uma reserva do próprio hotel
   cuja ficha do titular tem todos os campos cadastrais preenchidos,
   **When** a pessoa abre essa ficha, **Then** vê os nove campos
   (nome completo, profissão, data de nascimento, tipo e número de
   documento, endereço, CEP, cidade e telefone), o distintivo de
   ficha completa, e nenhum campo listado como ausente.
2. **Given** uma ficha parcial (pelo menos um dos nove campos sem
   valor utilizável), **When** a recepção abre a ficha, **Then** o
   distintivo é de ficha parcial, distinto do de completa, e cada
   campo ausente aparece nomeado — não um total genérico do tipo
   “faltam 3”.
3. **Given** uma reserva ainda aguardando cadastro (só o nome e o
   telefone do cadastro mínimo), **When** a recepção abre a ficha,
   **Then** os campos que a coleta pediria e ainda não vieram estão
   nomeados como ausentes; a tela não afirma que a ficha está
   completa.
4. **Given** uma ficha cuja resposta pelo canal foi irreconhecível,
   **When** a recepção abre a ficha, **Then** a tela declara que
   precisa de leitura humana, os campos estruturados permanecem
   editáveis e vazios onde nada foi aproveitado, e o corpo da
   mensagem do hóspede **não** é reproduzido nesta tela.
5. **Given** data de nascimento preenchida, **When** a ficha é
   exibida, **Then** a idade aparece só como informação derivada na
   hora, e não como campo que se edita ou se grava.
6. **Given** a fila do dia aberta, **When** a recepção aciona o
   controle rotulado para ver a ficha na linha daquela reserva,
   **Then** chega à ficha daquela reserva — não à de outra, não a
   uma tela só com título.
7. **Given** o destino “ficha do hóspede” aberto pelo menu, sem
   reserva escolhida, **When** a tela aparece, **Then** não mostra
   dado cadastral de ninguém; indica que a ficha se abre a partir da
   fila do dia.

---

### User Story 2 - Completar no balcão o que o canal não trouxe (Priority: P1)

Como recepcionista com o hóspede (ou o documento) à frente, quero
preencher ou corrigir os campos da ficha e gravar na hora, sem que o
sistema mande outra mensagem cobrando cadastro, para o que faltou
deixar de ser pendência sem transformar o WhatsApp em formulário.

**Why this priority**: É a decisão da jornada — resposta parcial não
ganha segunda cobrança; completa-se no balcão. Sem gravar pela tela,
a recepção continua no caderno.

**Independent Test**: Pode ser testado abrindo uma ficha parcial,
preenchendo os campos ausentes com valores válidos, gravando, e
conferindo que a ficha passa a completa, que nenhuma mensagem nova
sai ao hóspede, e que valores inválidos são recusados sem gravar.

**Acceptance Scenarios**:

1. **Given** uma ficha parcial visível, **When** a recepção preenche
   todos os campos ausentes com valores utilizáveis e confirma a
   gravação, **Then** a ficha passa a completa na própria tela, os
   nomes dos ausentes desaparecem, e **nenhuma** mensagem de coleta
   ou de correção é enviada ao hóspede.
2. **Given** uma ficha já completa, **When** a recepção corrige um
   campo (por exemplo o endereço conferido no documento físico) e
   grava, **Then** o valor novo permanece, a ficha continua completa,
   e nenhuma mensagem é disparada.
3. **Given** a recepção ainda editando, **When** ela grava com campo
   obrigatório da ficha ainda vazio, **Then** a ficha permanece
   parcial, os ausentes continuam nomeados, e o que já era válido
   não é apagado.
4. **Given** data de nascimento futura, tipo de documento fora de
   RG / CPF / passaporte, CEP ilegível ou telefone ilegível para
   mensageria brasileira, **When** a pessoa tenta gravar, **Then**
   nada daquele campo inválido é persistido, a recusa nomeia o que
   está errado, e não se inventa valor.
5. **Given** tentativa de informar idade como dado a gravar, ou de
   anexar foto de documento, **When** a tela é usada, **Then** não
   há campo de idade gravável nem caminho para enviar imagem; a
   idade, se visível, continua só derivada da data de nascimento.
6. **Given** gravação aceita que completa o último campo ausente,
   **When** a pessoa volta à fila do dia, **Then** aquela reserva
   deixa de aparecer como ficha parcial — a pendência some onde já
   era visível.
7. **Given** a pessoa editando sem querer gravar, **When** ela
   cancela, **Then** volta ao que estava gravado; nenhum campo novo
   persiste.
8. **Given** uma reserva já hospedada ou ainda só com ficha parcial
   antes da chegada, **When** a recepção completa a ficha, **Then** a
   situação da reserva (chegada, hospedado, encerrado) **não** muda
   por essa gravação — completar dado não confirma chegada nem
   saída.

---

### User Story 3 - Copiar a ficha para colar no sistema de gestão (Priority: P1)

Como recepcionista na ponte entre os dois sistemas, quero copiar a
ficha de uma vez, em texto limpo com o nome de cada campo, para colar
no sistema de gestão do hotel sem redigitar e sem fingir que os dois
sistemas conversam sozinhos.

**Why this priority**: A tela existe para ser transcrita. Sem um
gesto único de copiar, o ganho da ficha digital cai para “olhar e
digitar”, que é o retrabalho que o produto se propõe a encurtar. O
sistema de gestão **não** recebe os dados sozinho.

**Independent Test**: Pode ser testado abrindo uma ficha com campos
preenchidos, acionando copiar tudo, e conferindo que o texto copiado
traz cada campo com o rótulo e o valor visível, sem idade gravada e
sem campo de e-mail.

**Acceptance Scenarios**:

1. **Given** a ficha aberta, **When** a recepção aciona copiar tudo,
   **Then** o texto fica disponível para colagem externa numa única
   ação — copiar é o gesto principal da tela, não um atalho escondido.
2. **Given** o texto copiado, **When** ele é inspecionado, **Then**
   cada um dos nove campos aparece com o mesmo rótulo da tela e com
   o valor atualmente visível; campo vazio entra com o rótulo e sem
   valor inventado.
3. **Given** o texto copiado, **When** ele é inspecionado, **Then**
   não contém idade como campo próprio, não contém e-mail e não
   contém o corpo de mensagem do hóspede.
4. **Given** o ambiente em que a cópia automática não puder ser
   feita, **When** a pessoa aciona copiar tudo, **Then** o mesmo
   texto permanece visível e selecionável na tela para copiar à
   mão — a transcrição não depende de um único atalho.
5. **Given** a ficha copiada, **When** a recepção cola no sistema de
   gestão do hotel, **Then** o OmniStay **não** afirma que o cadastro
   lá foi atualizado: o clique humano continua sendo a ponte.

---

### User Story 4 - Ver o consentimento com data e poder revogar (Priority: P1)

Como recepcionista, quero ver na ficha se o titular aceitou contato
futuro, com a data desse estado, e revogar quando a pessoa pedir no
balcão, para o hotel não comunicar quem recusou e para a revogação
não apagar o histórico do que valia antes.

**Why this priority**: Critério de aceite explícito. Consentimento
sem data não demonstra o estado; apagar a linha antiga impede
responder “o que valia naquele dia”.

**Independent Test**: Pode ser testado abrindo fichas com aceite
datado, com recusa datada e sem nenhum registro, revogando um aceite
no painel, e conferindo o estado vigente, a data e a preservação do
registro anterior.

**Acceptance Scenarios**:

1. **Given** um titular com aceite vigente para comunicações futuras,
   **When** a recepção abre a ficha, **Then** vê que está concedido,
   com a data (e o instante) desse estado.
2. **Given** um titular com recusa vigente, **When** a ficha é
   aberta, **Then** vê que não está concedido, com a data da recusa —
   distinto de “ainda não registrado”.
3. **Given** um titular sem nenhum registro de consentimento,
   **When** a ficha é aberta, **Then** a tela declara que não há
   aceite vigente (nunca registrado), sem inventar concessão.
4. **Given** um aceite vigente visível, **When** a recepção revoga no
   painel, **Then** o estado vigente passa a recusado com a data de
   agora, o registro anterior permanece no histórico (não é apagado
   nem reescrito) e nenhuma mensagem de marketing ou de pesquisa é
   disparada por essa revogação.
5. **Given** um titular sem aceite vigente que pede no balcão para
   passar a receber contato futuro, **When** a recepção registra o
   aceite no painel, **Then** o estado vigente passa a concedido com
   a data de agora, como nova linha, sem alterar linhas anteriores.
6. **Given** a ficha aberta, **When** a recepção consulta só o
   estado atual, **Then** não precisa percorrer o histórico para
   saber se pode ou não contatar; o vigente está visível.

---

### User Story 5 - Só a recepção vê e edita esta ficha (Priority: P1)

Como responsável pelos dados dos hóspedes, quero que o perfil
operacional e a gestão não abram esta tela — nem pelo menu, nem
colando o endereço, nem a partir de qualquer lista — para nome,
documento, telefone e endereço não vazarem a quem a autorização já
recusa.

**Why this priority**: Minimização de dado pessoal. Critério de aceite
da fatia para o perfil operacional; a gestão já não lê ficha. A tela
não pode ser o caminho que fura a recusa.

**Independent Test**: Pode ser testado autenticando gestão e perfil
operacional, tentando o destino da ficha pelo menu e pelo endereço
(com e sem reserva), e verificando recusa sem nome, documento,
telefone ou endereço.

**Acceptance Scenarios**:

1. **Given** uma sessão de perfil operacional, **When** a pessoa
   tenta abrir a ficha pelo endereço ou por qualquer atalho, **Then**
   o acesso é recusado, nenhum dado cadastral aparece, e não há tela
   em branco.
2. **Given** uma sessão de gestão, **When** a pessoa tenta o mesmo,
   **Then** o efeito visível é o mesmo: recusa sem ficha nominada.
   Consentimento pela consulta já existente da gestão **não** abre
   esta tela nem revela o restante da ficha.
3. **Given** uma sessão de recepção de um hotel, **When** ela tenta
   a ficha de reserva de outro hotel, **Then** não vê a ficha e não
   recebe confirmação de que aquela reserva existe.
4. **Given** uma sessão de recepção, **When** olha o menu, **Then** o
   destino “ficha do hóspede” aparece; para gestão e perfil
   operacional, não aparece.

---

### Edge Cases

- Ficha aberta de reserva cancelada ou encerrada: a recepção ainda
  lê e copia (o dado pode ser preciso depois da saída); editar
  permanece possível enquanto a ficha cadastral existir; confirmar
  chegada ou saída **não** é ação desta tela.
- Reserva de outro atendente no mesmo hotel: a recepção da casa lê
  e edita — o isolamento é por hotel, não por quem cadastrou.
- Dois hóspedes com o mesmo telefone: cada ficha continua sendo de
  uma pessoa; abrir a reserva A não mostra a ficha da reserva B.
- Documento (tipo + número) que já pertence a outro hóspede: a
  gravação é recusada com motivo claro; não se fundem fichas.
- Telefone da ficha diferente do telefone de contato da reserva: ao
  editar o telefone cadastral, o canal da reserva **não** muda —
  mensagens continuam no número da reserva.
- CEP com hífen ou só dígitos: a aceitação olha os oito dígitos.
- Data de nascimento no calendário de hoje: recusada (precisa ser
  data passada), como já é regra do cadastro.
- Gravação enquanto outro atendente acabou de completar os mesmos
  campos: prevalece o último gravado visível ao recarregar; não se
  inventa mesclagem campo a campo nesta fatia.
- Copiar com todos os campos vazios (só nome do cadastro mínimo):
  o texto traz os rótulos; não inventa profissão, documento nem
  endereço.
- Falha ao ler a ficha: o painel permanece; a tela declara que a
  ficha não carregou e oferece voltar à fila ou tentar de novo. Não
  é fila vazia, não é tela de entrada, não é ficha de outra pessoa.
- Falha ao gravar: o que estava na tela de edição permanece para
  correção; não se afirma sucesso.
- Sessão expirada no meio da edição ou da revogação: volta à tela
  de entrada, sem dado residual na página, como na casca.
- Visitante sem sessão no endereço da ficha: tela de entrada, nunca
  a ficha.
- Revogar duas vezes seguidas: cada revogação é uma linha nova; o
  vigente continua recusado; não se apaga a primeira recusa.
- Consentimento originado na pesquisa de saída: aparece como
  vigente (se for o mais recente) com a data da pesquisa; revogar
  no painel acrescenta linha nova, não reescreve a da pesquisa.

## Requirements *(mandatory)*

### Functional Requirements

**Abrir e distinguir**

- **FR-001**: A recepção DEVE abrir a ficha do titular de uma reserva
  do próprio hotel a partir da fila do dia, por controle rotulado na
  linha, e chegar aos dados daquela reserva.
- **FR-002**: O destino “ficha do hóspede” já visível no menu da
  recepção DEVE deixar de ser só título: sem reserva escolhida, NÃO
  DEVE exibir dado cadastral; DEVE indicar que a ficha se abre pela
  fila do dia.
- **FR-003**: A ficha DEVE exibir os nove campos do titular: nome
  completo, profissão, data de nascimento, tipo de documento, número
  do documento, endereço, CEP, cidade e telefone. NÃO DEVE exibir
  e-mail. NÃO DEVE exibir idade como campo gravável.
- **FR-004**: Ficha com os nove campos utilizáveis DEVE ser
  distinguível de ficha parcial. Parcial DEVE nomear cada campo
  ausente; NÃO DEVE resumir só a um número (“faltam N”).
- **FR-005**: Idade, quando mostrada, DEVE ser derivada na exibição a
  partir da data de nascimento e NÃO DEVE ser persistida.
- **FR-006**: Foto ou imagem de documento NÃO DEVE ser aceita como
  preenchimento, em nenhuma hipótese.
- **FR-007**: Sinalização de leitura humana (resposta irreconhecível)
  DEVE aparecer nesta tela sem reproduzir o conteúdo da mensagem.

**Editar no balcão**

- **FR-008**: A recepção DEVE poder editar os nove campos e gravar.
  Gravação aceita NÃO DEVE enviar mensagem ao hóspede (nem coleta,
  nem correção, nem confirmação de cadastro).
- **FR-009**: Ao completar o último campo ausente com valor
  utilizável, a ficha DEVE passar a completa nesta tela e deixar de
  constar como parcial na fila do dia.
- **FR-010**: Gravação com campo ainda vazio DEVE manter a ficha
  parcial, preservar o que já era válido e continuar nomeando os
  ausentes.
- **FR-011**: Data de nascimento que não seja passada, tipo de
  documento fora de RG, CPF ou passaporte, CEP que não tenha oito
  dígitos utilizáveis, ou telefone ilegível para mensageria
  brasileira, NÃO DEVEM ser gravados. A recusa DEVE nomear o campo.
- **FR-012**: Completar ou corrigir a ficha NÃO DEVE confirmar
  chegada, confirmar saída, cancelar reserva nem alterar o telefone
  de contato usado pelo canal da reserva.
- **FR-013**: Cancelar a edição DEVE descartar o que não foi gravado
  e manter o último estado persistido.
- **FR-014**: Documento (tipo e número) que conflite com o de outro
  hóspede NÃO DEVE gravar nem fundir as duas fichas.

**Copiar para colagem externa**

- **FR-015**: A recepção DEVE poder copiar a ficha inteira numa
  única ação visível (copiar tudo). O texto DEVE trazer, para cada
  um dos nove campos, o rótulo e o valor visível; campo vazio entra
  com rótulo e sem valor inventado.
- **FR-016**: O texto copiado NÃO DEVE incluir idade como campo,
  e-mail, senha, nem conteúdo de mensagem.
- **FR-017**: Se a cópia automática não estiver disponível, o mesmo
  texto DEVE permanecer visível e selecionável na tela.
- **FR-018**: Esta fatia NÃO DEVE enviar dado ao sistema de gestão
  do hotel, NÃO DEVE afirmar que o cadastro lá foi atualizado, e NÃO
  DEVE oferecer ordem de campos configurável nem cópia campo a
  campo — uma variação (bloco único rotulado) é o que se entrega.

**Consentimento**

- **FR-019**: A ficha DEVE mostrar o estado vigente do consentimento
  para comunicações futuras: concedido com data, recusado com data,
  ou nunca registrado (tratado como sem aceite).
- **FR-020**: A recepção DEVE poder revogar um aceite vigente e
  registrar um aceite no balcão. Cada ação DEVE inserir uma nova
  linha com instante e origem no painel, SEM atualizar ou apagar
  linha anterior.
- **FR-021**: Revogar ou registrar aceite nesta tela NÃO DEVE
  disparar pesquisa de saída, oferta de retorno nem mensagem de
  marketing.

**Autorização, isolamento e honestidade**

- **FR-022**: Perfil operacional e gestão NÃO DEVEM ver nem editar
  esta ficha. Tentativa pelo endereço DEVE ser recusada sem nome,
  documento, telefone, endereço ou lista.
- **FR-023**: Sessão de um hotel NÃO DEVE abrir ficha de reserva de
  outro hotel, nem confirmar que ela existe.
- **FR-024**: Esta fatia NÃO DEVE confirmar chegada ou saída, lançar
  consumo, resolver chamado, editar catálogo, editar recado de
  boas-vindas, cadastrar acompanhante nem cadastrar e-mail de
  hóspede.
- **FR-025**: Esta fatia NÃO DEVE alterar a finalidade de
  consentimento, a regra de nunca reescrever linha antiga, a lista
  dos nove campos, a regra de foto, a regra de idade, o formato de
  telefone nem quem pode ler ficha. NÃO DEVE integrar-se ao sistema
  de gestão do hotel.
- **FR-026**: Log desta fatia NÃO DEVE registrar nome, telefone,
  documento, endereço, conteúdo de mensagem nem senha. PODE
  registrar identificador de reserva, de hóspede, de usuário, perfil
  e código de recusa.
- **FR-027**: Falha ao ler ou ao gravar DEVE manter o painel, declarar
  o ocorrido e NÃO DEVE mostrar ficha de outra pessoa nem o estado
  de sucesso.

### Key Entities

- **Ficha do titular**: os nove campos cadastrais da pessoa titular
  da reserva. Pode estar completa ou parcial. É o que se lê, edita
  no balcão e se copia. Não inclui acompanhante, não inclui e-mail,
  não inclui idade persistida.
- **Campo ausente**: um dos nove campos sem valor utilizável,
  nomeado na tela quando a ficha é parcial.
- **Cópia para colagem externa**: bloco único de texto rotulado,
  destinado a ser colado à mão no sistema de gestão do hotel. Não é
  integração; não é comprovante de que o outro sistema gravou.
- **Consentimento vigente**: o registro mais recente, para
  comunicações futuras, daquele titular. Ausência de registro =
  sem aceite. Revogação e novo aceite são linhas novas, nunca
  correção da linha antiga.
- **Reserva** *(existente)*: o contexto da ficha (qual estadia, de
  qual hotel). Completar a ficha não atravessa a fronteira de
  chegada nem de saída.
- **Telefone de contato da reserva** *(existente)*: número do canal.
  Distinto do telefone cadastral da ficha; editar a ficha não o
  substitui.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma recepcionista autenticada abre a ficha de uma
  reserva da fila do dia e identifica, em menos de 20 segundos, se
  está completa ou parcial e, se parcial, quais campos faltam, pelo
  nome — sem abrir outro sistema.
- **SC-002**: 100% das fichas parciais nomeiam cada campo ausente;
  0% usam só um total numérico; 100% das fichas com os nove campos
  utilizáveis aparecem como completas.
- **SC-003**: Em 100% das gravações feitas no balcão, 0 mensagens de
  coleta ou de correção são enviadas ao hóspede.
- **SC-004**: Depois de gravar o último campo ausente, 100% das
  filas do dia daquela recepção deixam de sinalizar aquela reserva
  como ficha parcial, sem a pessoa pedir a tela da fila de novo ao
  voltar a ela.
- **SC-005**: 100% das tentativas com data de nascimento inválida,
  documento de tipo não admitido, CEP ilegível ou telefone ilegível
  são recusadas na hora; 0 desses valores inválidos são persistidos.
- **SC-006**: Em 100% das ações de copiar tudo, o texto disponível
  para colagem contém os nove rótulos e os valores visíveis, e 0
  idades como campo, 0 e-mails e 0 corpos de mensagem.
- **SC-007**: Em 100% dos aceites vigentes, a ficha mostra a data
  desse estado; em 100% das revogações no painel, o vigente passa a
  recusado com nova data e 0 linhas anteriores são apagadas.
- **SC-008**: 100% das tentativas de gestão e de perfil operacional
  de abrir esta ficha são recusadas, com 0 nome, 0 documento, 0
  telefone e 0 endereço visíveis.
- **SC-009**: 0 fotos de documento são aceitas; 0 idades são
  persistidas; 0 campos de e-mail aparecem na ficha ou no texto
  copiado.
- **SC-010**: 0 gravações de ficha confirmam chegada ou saída; 0
  envios automáticos são feitos ao sistema de gestão do hotel.
- **SC-011**: 0 senhas, 0 nomes, 0 telefones, 0 documentos e 0
  conteúdos de mensagem aparecem em log desta fatia.
- **SC-012**: Cada critério de aceite da fatia F8.3 do backlog tem
  ao menos um cenário de aceitação correspondente nesta spec.

## Assumptions

- **O comportamento de leitura já existe; falta a superfície.** A
  ficha do titular, os nove campos, a distinção completa/parcial, a
  recusa de idade persistida e de foto, e a leitura só pela recepção
  foram entregues na coleta e na interpretação. Consultar e
  registrar consentimento (histórico, vigente, origem no painel)
  foram entregues na saída. Esta fatia liga isso à tela e entrega o
  completar no balcão e o copiar.
- **Uma variação de cópia, de propósito.** A jornada registrou
  copiar em bloco, ordem configurável e cópia campo a campo como
  evolução após testar colagem no sistema de gestão real. A F8.3
  puxa **uma** variação para a entrega: copiar tudo em texto
  rotulado. Ordem por propriedade e copiar um campo por vez
  continuam fora. Testar se o sistema de gestão da casa aceita
  colar no cadastro permanece achado de campo — esta fatia não
  promete que a colagem preenche o outro sistema.
- **Sem e-mail na ficha.** O desenho de telas chegou a mostrar
  e-mail opcional; o segundo canal foi cortado como escopo
  declarado. Mostrar o campo aqui prometia o que o sistema não faz.
- **Nove campos, só o titular.** Acompanhantes estão no modelo como
  possibilidade e ficam fora desta tela. Completar no balcão é a
  ficha que a coleta já pede.
- **Abrir a partir da fila.** O caminho operacional é a linha do
  turno. O item de menu sem reserva escolhida não inventa uma
  segunda lista nominada — aponta de volta à fila.
- **Completar não atravessa fronteira de fase.** A máquina de
  estados da reserva não ganha “transcrição concluída” nem check-in
  automático. A pendência que some é a da ficha incompleta.
- **Telefone da ficha ≠ telefone do canal.** Corrigir o cadastral no
  balcão não redireciona a conversa. Trocar o número do canal é
  outro problema, fora desta fatia.
- **Gestão continua podendo consultar consentimento pela operação
  já existente**, sem passar por esta tela e sem ver o restante da
  ficha. Perfil operacional continua recusado nos dois.
- **Mapa de telas já acordado.** Copiar tudo é o gesto principal;
  editar é o segundo. Computador no balcão; esta fatia não promete
  layout de mão.
- **F7.4 (módulos por propriedade) continua fora.** Ficha é núcleo:
  não desliga.
- **Uma propriedade por instalação no uso previsto da demonstração**,
  mas o isolamento por hotel permanece obrigatório.
- **Limitação honesta (Artigo XV):** o OmniStay elimina a ficha de
  papel, não a digitação no sistema de gestão do hotel. Sustentar
  que esta fatia acaba com o retrabalho seria falso. O ganho
  defensável é dado já validado, legível e copiável, fora do momento
  em que o hóspede está em pé na fila. Se a recepção não copiar e
  não colar, o outro sistema não fica sabendo — e esta tela não
  finge o contrário.
