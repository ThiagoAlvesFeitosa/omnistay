# Feature Specification: Consumos a lançar e saída do hóspede

**Feature Branch**: `032-consumos-saida-hospede`

**Created**: 2026-08-31

**Status**: Draft

**Input**: User description: "Os consumos faturáveis pendentes de
lançamento aparecem em fila destacada, com o valor praticado e há
quanto tempo esperam. A recepção marca cada um como lançado ou
dispensado. Na saída, ela confirma o checkout e vê a lista de
pedidos feitos pelo chat daquela estadia, avisada se ainda houver
consumo pendente."
(backlog F8.5)

Restrições já decididas no projeto (entrada do specify): a fila
destacada de pendências de lançamento, marcar como lançado ou
dispensado com autor e instante, confirmar a saída, disparar a
pesquisa curta e apresentar os pedidos feitos pelo chat **já
existem** (F3.7, F4.1, F4.2) — esta fatia não inventa tipo de
consumo, valor praticado, status de lançamento, recorte cobrável,
texto de pesquisa nem recado da lista ao hóspede; a casca já nomeia
“Consumos a lançar” e “Saída do hóspede” só para recepção (F8.1); a
fila do dia já lista hospedados e deixa a saída para esta fatia
(F8.2); o que a autorização recusa, a tela não oferece; perfil
operacional não vê ficha cadastral nem lança consumo; gestão não
opera estas telas (consulta agregada é F8.7); o sistema **não** se
integra ao sistema de gestão do hotel — marcar lançado é o clique
humano da ponte, nunca débito automático; consumo pendente **não**
bloqueia o checkout; conteúdo de mensagem, nome, telefone e
documento continuam fora do log; as palavras “extrato” e “conta”
não existem neste produto. Catálogo, itens vendáveis e recado de
boas-vindas permanecem em F8.6.

## Clarifications

### Session 2026-08-31

- Q: Na lista Consumos a lançar, o nome do hóspede deve aparecer em cada linha? → A: Sem nome na lista (quarto, item, valor, tempo). Cada linha leva à reserva correspondente. A consulta de pendências é a mesma que equipe e gestão podem ler — nome na linha vazaria dado cadastral para quem não pode ver ficha.
- Q: Na fila do dia, o controle da linha de quem já está hospedado deve encerrar a estadia na hora, ou só abrir a tela Saída do hóspede? → A: Só abre Saída do hóspede daquela reserva. Encerrar a estadia é o botão rotulado nessa tela, depois da lista e do aviso.
- Q: Na lista Pedidos feitos pelo chat da tela de saída, cada item deve mostrar se ainda está pendente de lançamento ou já foi lançado? → A: Sem status por item. A consulta de pedidos feitos pelo chat devolve só descrição e valor praticado — não traz status de lançamento — e esta fase não altera essa consulta. O aviso no nível da estadia resolve com o que já existe. Observação para depois da semana: status por item seria útil na tela da recepção (com vários itens e um aviso “1 pendente”, ela não sabe qual); é extensão pequena da consulta, fora desta fatia.
- Q: Quando a recepção segue o aviso de pendência na tela de saída, Consumos a lançar deve mostrar a fila da casa inteira ou só os pendentes daquela estadia? → A: Abre Consumos a lançar da casa, a mesma fila do menu. A recepção localiza o item por quarto, descrição e valor. Sem recorte da estadia nesta fatia.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A recepção vê o que falta lançar, com valor, tempo e total (Priority: P1)

Como recepcionista no balcão e na passagem de turno, quero abrir
**Consumos a lançar** e ver só os consumos faturáveis ainda
pendentes da casa — cada um com o valor praticado na hora do pedido
e há quanto tempo espera — e quero o total pendente visível de
imediato, para o serviço entregue e não cobrado não passar em
silêncio.

**Why this priority**: É o primeiro critério de aceite da fatia e a
quarta travessia humana (Artigo V). Sem a fila real, a casca deixa
a recepção numa tela só com título, e o prejuízo silencioso
continua invisível.

**Independent Test**: Pode ser testado autenticando como recepção
num hotel com consumos pendentes de valores e idades diferentes, um
já lançado, um dispensado, um pedido de serviço sem cobrança e um
pendente de outro hotel, e conferindo que só os pendentes da casa
aparecem, cada um com valor e tempo de espera, com o total igual à
soma, e que lançado, dispensado, serviço sem cobrança e o de outro
hotel não aparecem.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção e consumos faturáveis pendentes
   de lançamento do próprio hotel, **When** a pessoa abre Consumos
   a lançar, **Then** cada pendente aparece com a descrição do
   item, o quarto quando conhecido, o valor praticado naquele
   pedido e há quanto tempo espera.
2. **Given** a mesma lista, **When** a recepção olha o resumo no
   topo, **Then** vê quantos estão pendentes, a soma dos valores
   praticados (total pendente) e há quanto tempo espera o mais
   antigo — sem abrir outro destino.
3. **Given** um consumo já lançado, um dispensado e um pedido de
   serviço sem cobrança (toalha, travesseiro), **When** a recepção
   abre Consumos a lançar, **Then** nenhum dos três aparece — a
   fila é só o que ainda falta lançar no sistema de gestão.
4. **Given** um consumo pendente já resolvido no quarto (atendimento
   concluído) e outro ainda aberto operacionalmente, **When** os
   dois continuam pendentes de lançamento, **Then** os dois
   aparecem nesta fila — resolver o quarto não tira a pendência
   financeira.
5. **Given** consumo pendente de outro hotel, **When** a recepção
   desta casa abre a lista, **Then** esse consumo não aparece.
6. **Given** várias pendências, **When** a recepção olha a lista,
   **Then** a mais antiga está no topo e a mais recente no fim.
7. **Given** a lista aberta, **When** a recepção segue uma linha
   até a reserva correspondente (gesto distinto de lançar e de
   dispensar), **Then** chega à ficha já existente dessa reserva —
   inclusive se o consumo não tiver quarto informado.
8. **Given** a mesma lista, **When** se observa o que cada linha
   mostra, **Then** não há nome, telefone nem documento do hóspede
   na própria lista; a identificação de quem pediu é o caminho até
   a reserva, o quarto quando conhecido e a descrição do item.
   Sem esse caminho, consumo sem quarto fica sem forma de
   identificar quem pediu.

---

### User Story 2 - Marcar como lançado registra quem e quando (Priority: P1)

Como recepcionista que acabou de lançar o item no sistema de gestão
do hotel, quero marcar o consumo como lançado em um único gesto
rotulado, e quero que fique gravado quem lançou e quando, para a
pendência sair da fila e o próximo turno não relançar nem esquecer
o que já foi feito.

**Why this priority**: É o segundo critério de aceite da fatia. O
clique é a prova da ponte humana. Sem autor e instante, a omissão
continua invisível.

**Independent Test**: Pode ser testado autenticando a recepção com
um consumo pendente da casa, marcando como lançado pelo botão
rotulado, e conferindo: some da fila sem pedir a tela de novo;
constam autor e instante; o valor praticado não muda; segunda
tentativa é recusada.

**Acceptance Scenarios**:

1. **Given** um consumo pendente da propriedade na lista, **When**
   a recepção aciona o botão rotulado de marcar como lançado,
   **Then** o item deixa de aparecer entre as pendências, o total
   pendente e a conta diminuem na hora, e ficam registrados quem
   lançou e o instante.
2. **Given** o desfecho do cenário 1, **When** se observa o valor
   praticado daquele consumo, **Then** permanece o da hora do
   pedido — marcar como lançado não reajusta preço.
3. **Given** um consumo já lançado (toque duplo, lista desatualizada
   ou outro autorizado tentando de novo), **When** alguém tenta
   marcar como lançado outra vez, **Then** a tentativa é recusada
   de forma visível, quem lançou e quando permanecem os da primeira
   vez, e o item não volta à fila.
4. **Given** a linha de um pendente, **When** a recepção clica na
   descrição, no quarto, no valor ou no caminho até a reserva,
   **Then** isso **não** marca como lançado — o alvo é o botão
   rotulado, não a linha inteira.
5. **Given** o lançamento bem-sucedido, **When** se observa o canal
   do hóspede, **Then** não nasce recado novo por causa deste
   clique — o hóspede já recebeu o valor na confirmação do pedido.
6. **Given** uma sessão de gestão ou de perfil operacional,
   **When** a pessoa tenta marcar como lançado por esta tela,
   **Then** não há botão de lançar: estes perfis não operam
   Consumos a lançar.

---

### User Story 3 - Dispensar tira da fila sem fingir lançamento (Priority: P1)

Como recepcionista que concedeu cortesia ou desfez o pedido antes
de cobrar, quero dispensar o consumo pendente em um gesto rotulado
distinto do lançar, com quem dispensou e quando gravados, para a
fila esvaziar com verdade e o item não aparecer como lançado no
sistema de gestão nem na lista de pedidos feitos pelo chat.

**Why this priority**: O único caminho para sair da fila não pode
ser “lançado”. Marcar cortesia como lançada mente sobre o que será
cobrado.

**Independent Test**: Pode ser testado autenticando a recepção com
um consumo pendente, dispensando-o pelo botão rotulado, e
conferindo: some da fila; constam quem e quando; não consta como
lançado; o item deixa de entrar na lista cobrável da saída.

**Acceptance Scenarios**:

1. **Given** um consumo pendente na lista, **When** a recepção
   aciona o botão rotulado de dispensar, **Then** o item some da
   fila, o total pendente diminui, ficam registrados quem dispensou
   e o instante, e o consumo **não** aparece como lançado.
2. **Given** o desfecho do cenário 1, **When** a recepção abre a
   saída daquela estadia, **Then** o item dispensado **não**
   aparece em pedidos feitos pelo chat.
3. **Given** um consumo já lançado ou já dispensado, **When** se
   tenta lançar ou dispensar de novo, **Then** a ação é recusada e
   o estado original permanece.
4. **Given** a linha de um pendente, **When** a recepção olha as
   ações, **Then** lançar e dispensar são dois controles rotulados
   distintos; um clique não dispara o outro; não há diálogo de
   “tem certeza?”.
5. **Given** a dispensa bem-sucedida, **When** se observa o canal
   do hóspede, **Then** não nasce recado automático de “não será
   cobrado” por causa deste clique.

---

### User Story 4 - Na saída, a recepção vê os pedidos do chat e o aviso de pendência (Priority: P1)

Como recepcionista no checkout do balcão, quero abrir **Saída do
hóspede** daquela estadia, ver a lista de **pedidos feitos pelo
chat** com os valores praticados e ser avisada — antes de
confirmar — se ainda houver consumo pendente de lançamento, para eu
conferir com a pessoa enquanto ela está no hotel e não descobrir o
buraco depois que ela saiu.

**Why this priority**: É o terceiro e o quinto critérios de aceite
(aviso antes da confirmação; serviço sem cobrança fora da lista).
Confirmar no escuro reproduz o prejuízo silencioso. Misturar toalha
com cerveja reabre a dúvida que o rótulo existe para remover.

**Independent Test**: Pode ser testado autenticando a recepção,
abrindo a saída de uma reserva hospedada com consumo pendente, um
já lançado, um dispensado e um serviço sem cobrança, e conferindo:
a lista mostra só pendente e lançado, com valores e o rótulo
“pedidos feitos pelo chat”; o aviso de pendência aparece antes de
confirmar; dispensado e serviço sem cobrança não aparecem; as
palavras “extrato” e “conta” não aparecem.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção e uma reserva hospedada da
   casa, **When** a pessoa abre Saída do hóspede dessa reserva,
   **Then** identifica a estadia (nome do titular, quarto quando
   conhecido, datas) e vê a lista rotulada **pedidos feitos pelo
   chat**, nunca “extrato” nem “conta”.
2. **Given** essa estadia com um consumo pendente, um já lançado,
   um dispensado e um pedido de serviço sem cobrança, **When** a
   lista é exibida, **Then** pendente e lançado aparecem cada um
   com a descrição do item e o valor praticado naquele pedido; o
   total visível é a soma desses itens cobráveis; dispensado e
   serviço sem cobrança **não** aparecem.
3. **Given** a mesma estadia com ao menos um consumo ainda
   pendente de lançamento, **When** a recepção está na tela de
   saída **antes** de confirmar, **Then** um aviso explícito diz
   que há consumo pendente daquela estadia — distinto da lista
   vazia e distinto da falha ao carregar — e o controle de
   confirmar saída permanece visível.
4. **Given** o aviso do cenário 3, **When** a recepção o segue,
   **Then** chega a Consumos a lançar da casa — a mesma fila do
   menu, sem recorte só daquela estadia — e localiza o pendente
   por quarto, descrição e valor; a tela de saída **não** oferece
   lançar nem dispensar.
5. **Given** uma estadia sem nenhum consumo cobrável, **When** a
   recepção abre a saída, **Then** a lista de pedidos feitos pelo
   chat aparece vazia de forma honesta, sem aviso de pendência de
   lançamento, e confirmar saída continua disponível.
6. **Given** a lista na saída, **When** se inspecionam rótulos,
   títulos e avisos, **Then** zero ocorrências de “extrato” e de
   “conta”; cada linha mostra descrição e valor, **sem** status
   de lançamento por item — a consulta de pedidos feitos pelo
   chat não traz esse status, e esta fatia não a estende. O que
   ainda falta lançar é o aviso da estadia.
7. **Given** o destino Saída do hóspede aberto pelo menu, sem
   reserva escolhida, **When** a recepção olha a tela, **Then**
   vê estado honesto de que a saída se abre pela fila do dia (ou
   por uma reserva já escolhida), sem lista inventada e sem botão
   de confirmar órfão.

---

### User Story 5 - Confirmar a saída no balcão, sem travar por pendência (Priority: P1)

Como recepcionista com a pessoa no balcão, quero confirmar a saída
em um gesto rotulado nesta tela — depois de ver a lista e o aviso,
se houver — para encerrar a estadia no instante real da partida, e
quero que o hóspede receba a pesquisa curta e, quando couber, a
lista de pedidos feitos pelo chat, mesmo que ainda exista consumo
pendente.

**Why this priority**: A partida é travessia humana. Travar o
checkout por lançamento pendente prende o hóspede no balcão; omitir
o aviso esconde o prejuízo. Os dois já foram decididos: avisa e
não bloqueia.

**Independent Test**: Pode ser testado autenticando a recepção numa
reserva hospedada com consumo pendente, confirmando a saída pelo
botão rotulado, e conferindo: a reserva passa a encerrada; o
instante da partida é o do clique; o destaque de saída vencida some
quando existia; a pesquisa é disparada; a lista ao hóspede segue a
regra já existente (uma mensagem se houver cobrável; nenhuma se não
houver); segunda confirmação é recusada.

**Acceptance Scenarios**:

1. **Given** uma reserva hospedada da casa na tela de saída,
   **When** a recepção aciona o botão rotulado de confirmar saída,
   **Then** a reserva passa a encerrada, o instante real da
   partida fica gravado (não a data prevista) e o controle de
   confirmar deixa de ser oferecido nessa estadia.
2. **Given** a mesma reserva com consumo ainda pendente e o aviso
   visível, **When** a recepção confirma a saída, **Then** a
   confirmação é aceita — o aviso não é trava; o consumo permanece
   pendente em Consumos a lançar para depois do checkout.
3. **Given** uma confirmação bem-sucedida, **When** se observam as
   mensagens ao hóspede, **Then** a pesquisa curta de avaliação é
   disparada como já definido; se houver pedido cobrável, a lista
   de pedidos feitos pelo chat sai em mensagem distinta, com o
   mesmo recorte e os mesmos valores da tela; se não houver
   cobrável, nenhuma mensagem extra de lista.
4. **Given** a confirmação do cenário 1, **When** a recepção volta
   à fila do dia, **Then** aquela reserva não aparece mais como
   hospedada à espera de checkout; se estava destacada como saída
   vencida, o destaque desapareceu.
5. **Given** uma reserva já encerrada, ainda não hospedada ou
   cancelada, **When** a recepção tenta confirmar a saída nesta
   tela, **Then** a operação é recusada de forma visível, o status
   não muda e nenhuma pesquisa nem lista novas nascem.
6. **Given** toque duplo ou segunda tentativa na mesma reserva já
   encerrada, **When** alguém confirma de novo, **Then** a
   tentativa é recusada, o instante da partida original permanece
   e o hóspede não recebe segunda pesquisa nem segunda lista.
7. **Given** a tela de saída, **When** a recepção clica no nome,
   na lista ou no aviso, **Then** isso **não** confirma a saída —
   o alvo é o botão rotulado. Não há segundo passo de “tem
   certeza?”: a lista e o aviso **são** o que ela vê antes.

---

### User Story 6 - A fila do dia leva à saída e destaca quem deveria ter saído (Priority: P1)

Como recepcionista na fila do dia, quero um controle rotulado na
linha de quem já está hospedado que me leve à Saída do hóspede
daquela reserva — e quero ver destacada a hospedagem cuja data
prevista de saída já passou e ainda não foi confirmada — para o
checkout não depender de eu lembrar o endereço da tela e a omissão
do clique não passar em silêncio.

**Why this priority**: A fila é a casa da recepção. Sem o caminho
na linha, a tela de saída fica órfã. Sem o destaque de saída
vencida (já definido na jornada de encerramento), a ausência do
clique continua invisível no turno.

**Independent Test**: Pode ser testado autenticando a recepção com
hospedado com saída prevista hoje, hospedado com saída prevista já
passada, e reserva ainda não hospedada, e conferindo: só o
hospedado oferece o caminho para a saída; o vencido aparece
destacado de forma distinta da chegada vencida; o caminho abre a
tela de saída daquela reserva e **não** encerra no mesmo gesto.

**Acceptance Scenarios**:

1. **Given** uma reserva hospedada na fila do dia, **When** a
   recepção olha a linha, **Then** há um controle rotulado que
   leva à Saída do hóspede dessa reserva, distinto de confirmar
   chegada e de ver a ficha — e **não** rotulado de modo a
   sugerir que a estadia já se encerra nesse gesto.
2. **Given** esse controle, **When** a recepção o aciona, **Then**
   chega à tela de saída daquela estadia com a lista e o aviso
   cabíveis; a reserva **permanece** hospedada até o botão de
   confirmar saída naquela tela.
3. **Given** uma reserva ainda não hospedada (aguardando cadastro,
   ficha recebida, ficha parcial ou chegará sem cadastro prévio),
   **When** a recepção olha a linha, **Then** o caminho de saída
   **não** é oferecido — não se faz checkout de quem não fez
   check-in.
4. **Given** uma reserva hospedada cuja data prevista de saída já
   passou e a saída ainda não foi confirmada, **When** a recepção
   olha a fila, **Then** a linha está destacada como saída não
   confirmada, de forma distinguível do destaque de chegada
   vencida, do recado de boas-vindas não enviado e da ficha
   parcial.
5. **Given** uma reserva hospedada cuja saída prevista é o dia
   corrente, **When** a recepção olha a fila, **Then** o caminho
   de saída é oferecido e o destaque de saída vencida **não** se
   aplica — o atraso começa no dia seguinte.
6. **Given** a fila do dia, **When** a recepção confirma a saída
   pela tela desta fatia e volta, **Then** o destaque de saída
   vencida daquela linha não permanece.

---

### User Story 7 - Lista vazia, falha e isolamento não se confundem (Priority: P2)

Como recepcionista, quero distinguir “não há nada a lançar”, “a
lista não carregou” e “esta tela não é sua”, e quero o mesmo na
saída, para eu não achar que o turno financeiro está limpo quando a
leitura falhou, nem ver consumo ou estadia de outro papel ou de
outro hotel.

**Why this priority**: Sem isso, a omissão deixa de ser perceptível
(Artigo V). Fica em P2 porque o turno já entrega valor com a fila
cheia, o lançar, o dispensar e o checkout.

**Independent Test**: Pode ser testado com hotel sem pendência de
lançamento, com falha ao ler, com gestão e equipe tentando as
telas, e com reserva de outro hotel, conferindo três estados
visíveis distintos e zero vazamento.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção e nenhum consumo pendente na
   casa, **When** a pessoa abre Consumos a lançar, **Then** vê o
   destino nomeado com estado de lista vazia explícito, total
   pendente zero — não uma página em branco, não o aviso de falha.
2. **Given** que Consumos a lançar ou a lista da saída não
   carregou, **When** a pessoa está na tela, **Then** o painel
   permanece, a tela declara que não carregou, oferece tentar de
   novo, e **não** mostra o estado de lista vazia nem afirma
   checkout concluído.
3. **Given** falha ao lançar, dispensar ou confirmar saída,
   **When** a ação não conclui, **Then** o item ou a reserva
   permanece no estado anterior, o hóspede não recebe recado novo
   por essa tentativa, e a pessoa pode tentar de novo — sem tela
   de erro de sistema no lugar da lista.
4. **Given** uma sessão de gestão ou de perfil operacional,
   **When** a pessoa tenta abrir Consumos a lançar ou Saída do
   hóspede pelo endereço, **Then** o acesso é recusado, nenhum
   consumo nem nome aparece, e não há tela em branco. A casa de
   cada papel permanece a já definida.
5. **Given** uma reserva do hotel A, **When** a recepção do hotel
   B tenta abrir a saída ou lançar consumo de A, **Then** a
   operação é recusada sem revelar que a reserva ou o consumo
   existe.

---

### Edge Cases

- Lista vazia de verdade (zero pendentes na casa): destino nomeado,
  contas em zero, sem botão de lançar ou dispensar órfão. Zero só
  vale quando a leitura concluiu.
- Falha ao ler Consumos a lançar ou a lista da saída: o painel
  permanece; aviso de que não carregou; tentar de novo. Não é tela
  de entrada, não é página vazia, não é lista vazia, não é “nada
  pendente”.
- Falha ao lançar, dispensar ou confirmar saída: estado anterior
  permanece; sem recado novo ao hóspede; a pessoa tenta de novo.
- Toque duplo no mesmo lançar, dispensar ou confirmar: uma
  transição, uma vez.
- Item lançado ou dispensado por outra pessoa enquanto a lista
  ainda o mostra: o segundo gesto é recusado de forma visível; a
  lista deixa de exibir o item.
- Consumo sem quarto: aparece mesmo assim; o sistema não inventa
  número de quarto. A identificação de quem pediu é o caminho da
  linha até a reserva.
- Consumo resolvido no quarto e ainda pendente de lançamento:
  permanece nesta fila. Esta tela **não** oferece resolver o
  quarto.
- Pedido de serviço sem cobrança: nunca entra em Consumos a lançar
  nem em pedidos feitos pelo chat.
- Consumo dispensado: sai da fila financeira e da lista cobrável
  da saída; não é lançado.
- Confirmar saída com consumo pendente: aceita; o aviso antecedeu
  o clique; a pendência continua em Consumos a lançar depois do
  checkout. Lançar depois da saída é caminho válido.
- Confirmar saída com chamado aberto: aceita, como já definido —
  esta fatia não fecha chamado.
- Reserva hospedada com saída prevista para hoje: caminho de saída
  oferecido; sem destaque de vencida.
- Reserva hospedada com saída prevista já passada: caminho de
  saída e destaque de saída não confirmada, distinto da chegada
  vencida.
- Reserva ainda não hospedada, já encerrada ou cancelada: sem
  caminho de saída na fila; confirmar nesta tela é recusado.
- Menu Saída do hóspede sem reserva: estado honesto, aponta para a
  fila; sem confirmar órfão.
- Reajuste de preço depois do pedido: a fila e a lista da saída
  mostram o valor praticado original.
- Isolamento por hotel: sessão de A nunca lista nem encerra item
  de B.
- Gestão e equipe: não operam estas telas; recusa sem cadastral e
  sem tela em branco.
- Sair, sessão vencida ou revogada: voltam à entrada, como já é
  regra da casca; esta fatia não redesenha sessão.
- A palavra “extrato” e a palavra “conta” não aparecem na
  interface, em nenhum rótulo, aviso, lista ou botão.
- Marcar lançado não afirma que o outro sistema recebeu o valor —
  afirma que a recepção fez a ponte. O produto não consulta o
  sistema de gestão.
- Não há notificação empurrada de consumo envelhecido: a fila
  destacada é a fonte da verdade.

## Requirements *(mandatory)*

### Functional Requirements

**Consumos a lançar**

- **FR-001**: A recepção DEVE ver, em Consumos a lançar, todos os
  consumos faturáveis ainda pendentes de lançamento da própria
  propriedade. Item já lançado, já dispensado, pedido de serviço
  sem cobrança e item de outro hotel NÃO DEVEM aparecer.
- **FR-002**: Cada item DEVE exibir descrição do item, quarto
  quando conhecido, valor praticado naquele pedido, instante de
  abertura e tempo de espera visível desde então. A lista DEVE
  aparecer com os mais antigos primeiro.
- **FR-003**: O topo da tela DEVE exibir a quantidade de
  pendentes, o total pendente (soma dos valores praticados da
  lista) e o tempo de espera do mais antigo.
- **FR-004**: Consumo resolvido no quarto e ainda pendente de
  lançamento DEVE permanecer nesta fila. Esta tela NÃO DEVE
  oferecer resolver o atendimento.
- **FR-005**: A lista NÃO DEVE exibir nome, telefone, documento
  nem endereço do hóspede. A consulta de pendências é a mesma que
  equipe e gestão podem ler; nome na linha vazaria dado cadastral
  para quem não pode ver ficha. Cada linha DEVE levar à reserva
  correspondente, no destino de ficha já entregue — inclusive
  quando o quarto não foi informado. Esse caminho DEVE ser
  distinto de lançar e de dispensar. Só a recepção opera lançar e
  dispensar nesta tela; o caminho até a ficha é só da recepção.
- **FR-006**: Recepção da própria propriedade DEVE poder marcar
  consumo pendente como lançado, com botão rotulado, sem diálogo
  extra. Marcar como lançado DEVE registrar quem lançou e quando,
  retirar o item da fila sem a pessoa pedir a tela de novo, e
  atualizar quantidade, total e tempo do mais antigo.
- **FR-007**: Recepção da própria propriedade DEVE poder dispensar
  consumo pendente, com botão rotulado distinto do lançar, sem
  diálogo extra. Dispensar DEVE registrar quem dispensou e quando,
  retirar o item da fila, NÃO DEVE constar como lançado, e DEVE
  tirá-lo do recorte cobrável da saída.
- **FR-008**: Clicar no restante do item NÃO DEVE lançar nem
  dispensar. Lançar NÃO DEVE dispensar. Dispensar NÃO DEVE lançar.
- **FR-009**: Segunda tentativa de lançar ou dispensar o mesmo
  item DEVE ser recusada de forma visível, sem alterar autor e
  instante da primeira transição.
- **FR-010**: Lançar ou dispensar NÃO DEVE disparar recado novo ao
  hóspede. NÃO DEVE alterar o valor praticado.

**Saída do hóspede**

- **FR-011**: A recepção DEVE abrir Saída do hóspede de uma reserva
  da casa a partir da fila do dia (controle rotulado na linha
  hospedada) e, quando a reserva já estiver escolhida, pelo
  destino nomeado. Abrir a saída NÃO DEVE encerrar a estadia.
- **FR-012**: A tela de saída DEVE identificar a estadia (nome do
  titular, quarto quando conhecido, datas) e DEVE exibir a lista
  rotulada **pedidos feitos pelo chat** daquela reserva, com a
  descrição e o valor praticado de cada item cobrável e o total
  desses itens.
- **FR-013**: A lista da saída DEVE incluir consumo pendente de
  lançamento e consumo já lançado. NÃO DEVE incluir pedido de
  serviço sem cobrança nem consumo dispensado.
- **FR-014**: Se a estadia tiver ao menos um consumo ainda
  pendente de lançamento, a tela DEVE avisar isso de forma
  explícita **antes** de a recepção confirmar a saída. O aviso
  DEVE apontar para Consumos a lançar da casa — a mesma fila do
  menu, sem recorte aos pendentes daquela estadia. A tela de
  saída NÃO DEVE oferecer lançar nem dispensar.
- **FR-015**: Ausência de consumo cobrável DEVE mostrar lista vazia
  honesta, sem aviso de pendência de lançamento, e NÃO DEVE
  impedir confirmar a saída.
- **FR-016**: A lista da saída NÃO DEVE apresentar status de
  lançamento por item: a consulta de pedidos feitos pelo chat
  devolve descrição e valor praticado, e esta fatia NÃO DEVE
  estendê-la. O que ainda falta lançar DEVE aparecer só no aviso
  da estadia. A lista NÃO DEVE ser chamada de “extrato” nem de
  “conta” em nenhum ponto da interface — nomenclatura da lista,
  não o motivo de omitir o status por item.
- **FR-017**: Destino Saída do hóspede sem reserva escolhida DEVE
  declarar que a saída se abre pela fila, sem botão de confirmar
  órfão e sem lista inventada.

**Confirmar saída**

- **FR-018**: Recepção da própria propriedade DEVE poder confirmar
  a saída de reserva hospedada a partir desta tela, com botão
  rotulado, sem diálogo extra. Clicar no restante da tela NÃO DEVE
  confirmar.
- **FR-019**: Confirmar a saída DEVE encerrar a estadia, gravar o
  instante real da partida, disparar a pesquisa curta já definida
  e, quando houver item cobrável, a lista de pedidos feitos pelo
  chat em mensagem distinta, no recorte e nos valores já
  definidos. Sem cobrável, NÃO DEVE nascer mensagem extra de
  lista.
- **FR-020**: Consumo pendente, chamado aberto e demais
  pendências operacionais NÃO DEVEM bloquear a confirmação. O
  consumo pendente DEVE permanecer em Consumos a lançar depois do
  checkout.
- **FR-021**: Confirmar saída de reserva que não está hospedada,
  já encerrada ou cancelada DEVE ser recusado de forma visível,
  sem alterar status e sem disparar pesquisa nem lista.
- **FR-022**: Segunda confirmação na mesma reserva DEVE ser
  recusada, sem alterar o instante da partida e sem segunda
  pesquisa ou segunda lista ao hóspede.

**Fila do dia (acréscimo desta fatia)**

- **FR-023**: Linha de reserva hospedada DEVE oferecer controle
  rotulado que leva à Saída do hóspede dessa reserva. O controle
  NÃO DEVE confirmar a saída no mesmo gesto — não é o equivalente
  da confirmação de chegada. Reserva ainda não hospedada NÃO DEVE
  oferecer esse caminho.
- **FR-024**: Reserva hospedada cuja data prevista de saída já
  passou e cuja saída ainda não foi confirmada DEVE aparecer na
  fila destacada como saída não confirmada, distinguível de
  chegada vencida, recado não enviado e ficha parcial. Saída
  prevista no dia corrente NÃO DEVE usar esse destaque.
- **FR-025**: Confirmação de saída aceita DEVE fazer a reserva
  deixar de aparecer como hospedada à espera de checkout e DEVE
  remover o destaque de saída não confirmada dessa linha.

**Autorização e honestidade**

- **FR-026**: Gestão e perfil operacional NÃO DEVEM ver Consumos a
  lançar nem Saída do hóspede. Tentativa pelo endereço DEVE ser
  recusada sem consumo, sem nome e sem tela em branco. O que o
  perfil não pode usar NÃO DEVE aparecer no menu.
- **FR-027**: Lista vazia e falha ao ler DEVEM ser estados
  distintos. Falha NÃO DEVE ser apresentada como “nada pendente”
  nem como checkout concluído. Falha ao lançar, dispensar ou
  confirmar NÃO DEVE alterar o estado anterior nem avisar o
  hóspede.
- **FR-028**: Esta fatia NÃO DEVE cadastrar item vendável, editar
  catálogo, editar recado de boas-vindas, resolver chamado,
  confirmar chegada, completar ficha, atribuir responsável nem
  lançar valor automaticamente no sistema de gestão do hotel.
- **FR-029**: Esta fatia NÃO DEVE alterar regra de estado da
  reserva, recorte cobrável, textos de pesquisa ou da lista ao
  hóspede, prazo de sessão nem matriz de permissões.
- **FR-030**: Log desta fatia NÃO DEVE registrar senha, conteúdo
  de mensagem, descrição do item, nome, telefone, documento nem
  valor como texto livre. PODE registrar identificador de usuário,
  de consumo, de reserva, perfil e código de recusa.
- **FR-031**: Toda leitura, lançamento, dispensa e confirmação de
  saída DEVEM considerar a propriedade do funcionário. Sessão de
  um hotel NÃO DEVE mostrar nem alterar item de outro.

### Key Entities

- **Consumos a lançar**: tela da recepção com a fila destacada de
  pendências financeiras da casa. É a passagem de turno do que
  ainda falta lançar no sistema de gestão. Não é Chamados e
  pedidos (atendimento no quarto) nem a lista da saída.
- **Consumo pendente**: consumo faturável ainda não lançado e ainda
  não dispensado. Entra nesta fila mesmo depois de resolvido no
  quarto e mesmo depois do checkout.
- **Valor praticado**: preço gravado no instante do pedido. Não
  acompanha reajuste posterior. É o número da fila, do total
  pendente e da lista da saída.
- **Tempo de espera**: quanto tempo o consumo está pendente de
  lançamento, visível em cada item e, no resumo, no mais antigo.
  Também define a ordem: mais antigos primeiro.
- **Total pendente**: soma dos valores praticados ainda na fila.
  Não é o total da estadia nem o total do sistema de gestão.
- **Lançado**: a recepção afirma ter lançado o item no sistema de
  gestão. Registra autor e instante. Sai da fila. Permanece no
  recorte cobrável da saída.
- **Dispensado**: não será lançado (cortesia ou pedido desfeito).
  Registra autor e instante. Sai da fila e da lista cobrável.
  Não é lançado.
- **Saída do hóspede**: tela da recepção para uma reserva já
  escolhida. Mostra pedidos feitos pelo chat, avisa pendência de
  lançamento e confirma o checkout. Não lança consumo.
- **Pedidos feitos pelo chat**: lista cobrável daquela estadia
  (pendente + lançado), com valores praticados. Rótulo fixo. Nunca
  “extrato” nem “conta”. Serviço sem cobrança e dispensado ficam
  de fora.
- **Aviso de pendência na saída**: alerta, antes do clique de
  confirmar, de que aquela estadia ainda tem consumo por lançar.
  Não trava o checkout. Aponta para Consumos a lançar da casa
  (a mesma fila do menu), não para uma fila só daquela estadia.
- **Confirmação de saída**: gesto único que encerra a estadia,
  grava o instante real da partida e dispara a pesquisa e, quando
  couber, a lista ao hóspede. Não é o caminho na fila do dia.
- **Destaque de saída não confirmada**: hospedado cuja data
  prevista de saída já passou e cujo clique ainda não aconteceu.
  Distinto da chegada vencida.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma recepcionista autenticada identifica, em menos
  de 30 segundos após abrir Consumos a lançar, quantos consumos
  estão pendentes, o total a lançar e há quanto tempo o mais
  antigo espera, sem abrir outro destino. Em 100% das listas com
  mais de um item, o primeiro é o mais antigo e o último o mais
  recente.
- **SC-002**: 100% dos consumos pendentes da casa aparecem nesta
  fila; 0% dos já lançados, já dispensados, dos pedidos sem
  cobrança e dos de outro hotel aparecem.
- **SC-003**: Em 100% dos itens da fila, o valor exibido é o
  praticado na hora do pedido e o tempo de espera é visível. O
  total pendente do topo coincide com a soma dos valores da lista
  em 100% das leituras bem-sucedidas.
- **SC-004**: A recepção marca um pendente como lançado em um
  único gesto, em menos de 15 segundos após ver o item, sem
  redigir texto. Em 100% dos lançamentos bem-sucedidos, o item
  some da lista visível sem pedir a tela de novo, e constam autor
  e instante. 0 recados novos ao hóspede nascem deste clique.
- **SC-005**: 100% das dispensas bem-sucedidas retiram o item da
  fila e da lista cobrável da saída; 0% constam como lançadas. 100%
  das segundas tentativas de lançar ou dispensar o mesmo item são
  recusadas.
- **SC-006**: Em 100% das saídas abertas de estadia com consumo
  pendente, o aviso aparece antes do clique de confirmar. Em 100%
  dessas confirmações, o checkout é aceito e o consumo permanece
  pendente na fila financeira. 0 checkouts são recusados só por
  haver pendência de lançamento.
- **SC-007**: 100% das listas da saída usam o rótulo “pedidos
  feitos pelo chat”; 0 ocorrências de “extrato” e de “conta” na
  interface desta fatia. 100% dos pedidos de serviço sem cobrança
  e 100% dos dispensados ficam de fora da lista da saída. 100%
  dos cobráveis (pendente + lançado) daquela estadia aparecem com
  o valor praticado.
- **SC-008**: 100% das confirmações de saída bem-sucedidas
  encerram a estadia no instante do clique, disparam a pesquisa
  curta, e disparam a lista ao hóspede somente quando há cobrável.
  100% das segundas confirmações são recusadas; 0 segundas
  pesquisas e 0 segundas listas.
- **SC-009**: 100% das linhas hospedadas da fila oferecem caminho
  à saída daquela reserva; 0% desses caminhos encerram a estadia
  no mesmo gesto. 100% das reservas ainda não hospedadas omitem
  esse caminho. 100% das hospedagens com saída prevista já passada
  e não confirmada aparecem com destaque distinguível da chegada
  vencida; 0% das com saída prevista no dia corrente recebem esse
  destaque.
- **SC-010**: Em 100% das falhas ao ler Consumos a lançar ou a
  lista da saída, o painel permanece, a tela declara que não
  carregou, e 0% mostram lista vazia, tela em branco ou checkout
  concluído.
- **SC-011**: 100% das tentativas de gestão e de perfil
  operacional de abrir estas telas, lançar, dispensar ou confirmar
  saída são recusadas sem consumo, sem nome e sem tela em branco.
  0 senhas, 0 nomes, 0 telefones, 0 documentos e 0 conteúdos de
  mensagem aparecem em log desta fatia.
- **SC-012**: Cada critério de aceite da fatia F8.5 do backlog tem
  ao menos um cenário de aceitação correspondente nesta spec.

## Assumptions

- **O comportamento já existe; falta a superfície.** Listar
  pendentes de lançamento, marcar lançado ou dispensado com autor
  e instante, confirmar saída, disparar pesquisa e montar a lista
  de pedidos feitos pelo chat foram entregues nas fatias de
  estadia. Esta fatia liga isso às duas telas já nomeadas na casca
  e ao caminho na fila do dia.
- **O desenho de telas é rascunho, não contrato.** O mapa mostra
  nome do hóspede na fila financeira, coluna de “lançamento no
  sistema de gestão” na lista da saída, e “confirmar saída”
  encerrando na própria fila. Nada disso foi entregue nas
  operações: a fila de pendentes não traz cadastral; a lista
  cobrável não traz status de lançamento por item; o checkout
  precisa da lista e do aviso **antes** do clique. Esta fatia
  segue o que já existe e o que esta sessão fechou: lista
  financeira sem nome, com caminho até a reserva; lista da saída
  sem status por item, porque a consulta cobrável não o traz e
  esta fase não a altera — o aviso da estadia cobre o que falta
  lançar; caminho na fila que **só** abre a tela de saída —
  encerrar é o botão rotulado dessa tela, depois da lista e do
  aviso.
- **Sem nome na fila financeira.** A consulta de pendências é a
  mesma que equipe e gestão podem ler. Nome na linha vazaria
  dado cadastral para quem não pode ver ficha — a mesma razão da
  lista de chamados. Cada linha leva à reserva correspondente; é
  por ali que a recepção chega ao nome. Sem esse caminho, consumo
  sem quarto fica sem forma de identificar quem pediu. Inventar
  nome nesta lista misturaria ficha na passagem de turno
  financeira e quebraria a minimização do recorte compartilhado.
- **Um clique no botão rotulado, sem “tem certeza?”.** O aviso
  visível na saída **é** o que a recepção vê antes. Segundo
  diálogo depois do aviso duplica o gesto e diverge da confirmação
  de chegada. O alvo é o botão, não o cartão inteiro.
- **Aviso não é trava.** Consumo pendente na saída avisa e deixa
  confirmar. Travar o checkout contradiz a jornada de encerramento
  já entregue. Lançar depois da saída permanece válido.
- **Lançar e resolver o quarto são ciclos distintos.** Esta tela
  não fecha atendimento. Chamados e pedidos não lançam. Dispensar
  não é cortesia anunciada ao hóspede nesta fatia.
- **A lista da saída reusa a consulta cobrável já existente.**
  Recorte pendente + lançado, descrição e valor praticado, rótulo
  “pedidos feitos pelo chat”. Essa consulta não traz status de
  lançamento por item; esta fase não a altera. O aviso no nível
  da estadia é o que a recepção vê antes de confirmar. A
  proibição das palavras “extrato” e “conta” continua na
  interface e na mensagem ao hóspede (nomenclatura da lista);
  não é o motivo de omitir o status por item — essa tela é da
  recepção, e o status por linha seria útil de verdade.
- **O aviso abre a fila da casa, não um recorte da estadia.**
  Consumos a lançar continua sendo a passagem de turno
  financeira da propriedade. A recepção acha o item por quarto,
  descrição e valor. Qual linha da lista da saída ainda está
  pendente fica para o status por item, depois da semana.
- **Gestão não opera estas telas.** Ver indicadores de pendência
  financeira é F8.7. A gestão continua podendo consultar a fila
  pelo caminho já existente, sem tela nesta fatia.
- **Catálogo, itens vendáveis e recado de boas-vindas são F8.6.**
  Esta fatia não cadastra preço nem edita texto de entrada.
- **A casca já entrega os destinos.** Login, menu só com o que o
  papel pode usar, recusa de endereço alheio. Consumos a lançar e
  Saída do hóspede deixam de ser só título. Saída sem reserva
  escolhida segue o padrão da ficha: aponta para a fila.
- **Destaque de saída vencida já estava definido e ficou de fora
  da fila do dia desta fase.** Entra agora, porque esta é a fatia
  do checkout. Não ganha conta própria no resumo do turno (as três
  contas da F8.2 permanecem).
- **F7.4 (módulos por propriedade) continua fora.** Consumo
  faturável como módulo desligável não entra aqui.
- **Uma propriedade por instalação no uso previsto da
  demonstração**, mas o isolamento por hotel permanece
  obrigatório.
- **Limitação honesta (Artigo XV):** se a recepção não abrir
  Consumos a lançar, o prejuízo continua possível — esta tela
  torna a omissão perceptível, não lança no outro sistema. Se
  confirmar a saída com pendência, o hóspede vai embora e o item
  envelhece na fila financeira. O produto não consulta o sistema
  de gestão para saber se o valor foi cobrado de verdade. Não há
  notificação empurrada: a fila é a fonte da verdade.
