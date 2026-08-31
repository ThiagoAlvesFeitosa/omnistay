# Feature Specification: Chamados, pedidos e a tela da equipe

**Feature Branch**: `031-chamados-pedidos-equipe`

**Created**: 2026-08-31

**Status**: Draft

**Input**: User description: "A recepção acompanha chamados e pedidos
abertos, com o tempo decorrido visível, e distingue reclamação,
serviço operacional e consumo. A equipe operacional acessa pelo
celular uma lista apenas dos chamados atribuídos a ela, com um único
botão para marcar como resolvido, sem qualquer dado cadastral do
hóspede na tela."
(backlog F8.4)

Restrições já decididas no projeto (entrada do specify): listar
pendências abertas da propriedade e marcar como resolvido **já
existem** (F3.4, F3.5, F3.6, F3.7) — esta fatia não inventa tipo,
urgência, janela de preferência, valor a cobrar, prazo de destaque
nem o recado de confirmação ao hóspede; a casca já nomeia “Chamados
e pedidos” só para recepção e “Meus chamados” como casa da equipe
(F8.1); atribuir responsável em passo separado continua fora (F3.6)
— “atribuídos a ela” é o trabalho da equipe da casa, não uma fila
pessoal; o que a autorização recusa, a tela não oferece; perfil
operacional não vê ficha cadastral; resolver confirma ao hóspede
depois de gravar a resolução, automaticamente, sem segundo recado
digitado; lançar ou dispensar consumo no sistema de gestão do hotel
é F8.5; o sistema não se integra a esse sistema de gestão; conteúdo
de mensagem, nome, telefone e documento continuam fora do log.

## Clarifications

### Session 2026-08-31

- Q: Na lista Chamados e pedidos da recepção, o nome do hóspede deve aparecer em cada linha? → A: Sem nome na lista (quarto, descrição, natureza, tempo, janela e valor quando couber). Cada linha leva à reserva correspondente; é por ali que a recepção chega ao nome e à ficha. Sem esse caminho, chamado sem quarto (campo opcional) fica sem forma de identificar quem abriu.
- Q: Em Meus chamados, o consumo faturável aberto deve aparecer junto com reclamação e serviço? → A: Sim. A equipe vê as três naturezas. Resolver consumo conclui o quarto; lançar continua na tela da recepção.
- Q: Na lista de pendências abertas, em que ordem os itens devem aparecer? → A: Mais antigos primeiro (tempo aberto crescente) nas duas telas. Destaque de prazo da reclamação não reordena a lista.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A recepção vê o que está aberto, com tempo e natureza (Priority: P1)

Como recepcionista no balcão e na passagem de turno, quero abrir
**Chamados e pedidos** e ver todas as pendências ainda abertas da
casa — reclamação, serviço operacional e consumo — cada uma com o
tempo decorrido desde que abriu e com a natureza distinguível à
primeira vista, para eu não misturar toalha com ar-condicionado nem
descobrir atraso só quando o hóspede liga.

**Why this priority**: É o primeiro critério de aceite da fatia e o
que torna a fila operacional visível no painel. Sem a lista real, a
casca deixa a recepção numa tela só com título, e a passagem de
turno volta a ser conversa oral.

**Independent Test**: Pode ser testado autenticando como recepção
num hotel com reclamação, serviço e consumo abertos, um item já
resolvido e um de outro hotel, e conferindo que só os três abertos
da casa aparecem, cada um com natureza distinta e tempo decorrido
visível, e que o resolvido e o de outro hotel não aparecem.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção e pendências abertas do próprio
   hotel — uma reclamação, um serviço operacional e um consumo —,
   **When** a pessoa abre Chamados e pedidos, **Then** as três
   aparecem na mesma lista, cada uma com rótulo de natureza
   distinto (reclamação × serviço × consumo), a descrição do que
   foi pedido ou reclamado, o quarto quando conhecido, e há quanto
   tempo está aberta.
2. **Given** uma reclamação aberta além do prazo de destaque da
   propriedade, **When** ela aparece na lista, **Then** está
   destacada como tempo excessivo, de forma distinta das demais
   naturezas e distinta de um serviço ou consumo da mesma idade.
3. **Given** um serviço ou um consumo aberto há o mesmo tempo que
   essa reclamação, **When** a recepção olha a lista, **Then**
   serviço e consumo **não** recebem o destaque de tempo excessivo
   — o destaque de prazo é da reclamação.
4. **Given** uma pendência já resolvida e uma ainda aberta, **When**
   a recepção abre Chamados e pedidos, **Then** só a aberta aparece
   — a tela mostra o que falta, não o histórico do que já fechou.
5. **Given** pendência de outro hotel, **When** a recepção desta
   casa abre a lista, **Then** essa pendência não aparece.
6. **Given** uma reclamação com horário de preferência informado
   pelo hóspede, **When** ela aparece, **Then** a janela é visível
   na linha, sem nome, telefone ou documento do hóspede.
7. **Given** um consumo aberto, **When** ele aparece, **Then** a
   natureza é consumo, o valor praticado é visível, e a linha **não**
   oferece lançar nem dispensar no sistema de gestão — isso é a
   fila de consumos a lançar.
8. **Given** a lista aberta, **When** a recepção segue uma linha
   até a reserva correspondente (gesto distinto do botão de
   resolver), **Then** chega à ficha já existente dessa reserva,
   com o nome e os campos do titular — inclusive se a pendência
   não tiver quarto informado.
9. **Given** uma pendência sem número de quarto, **When** a
   recepção olha só a lista, **Then** a linha continua sem nome;
   a forma de identificar quem abriu é seguir essa linha até a
   reserva, não um nome escrito na própria lista.
10. **Given** várias pendências abertas de naturezas diferentes,
    **When** a recepção olha a lista, **Then** a mais antiga está
    no topo e a mais recente no fim — o destaque de tempo
    excessivo na reclamação não a sobe na ordem.

---

### User Story 2 - A equipe resolve no celular com um botão, sem ficha (Priority: P1)

Como profissional da equipe operacional (manutenção, governança)
com as mãos ocupadas no quarto, quero abrir **Meus chamados** no
celular e ver só o trabalho aberto da minha casa — o que levar ou
consertar, o quarto quando conhecido, a natureza, o tempo decorrido
e, na reclamação, o destaque de atraso e a janela de preferência —
com um único botão rotulado para marcar como resolvido, sem nome,
telefone nem documento do hóspede.

**Why this priority**: O app da equipe foi cortado; esta tela o
substitui. Sem ela, o conserto no quarto não existe para o produto
e o hóspede não é avisado. Sem o botão único, o celular vira
formulário. Sem a omissão do cadastral, a sessão longa no aparelho
carrega dado que o perfil não pode ver.

**Independent Test**: Pode ser testado autenticando um profissional
operacional da casa com reclamação, serviço e consumo abertos,
conferindo a lista compacta com natureza, tempo, quarto e descrição,
a ausência de dado cadastral, um único controle de resolver por
item, e que o mesmo perfil de outro hotel não vê esses itens.

**Acceptance Scenarios**:

1. **Given** uma sessão de perfil operacional e pendências abertas
   da própria propriedade, **When** a pessoa chega a Meus chamados
   (tela inicial do papel), **Then** cada item aberto aparece com
   natureza distinta, tempo decorrido, descrição, quarto quando
   conhecido, urgência, e — na reclamação — janela de preferência
   quando houver e destaque de tempo excessivo quando couber.
2. **Given** a mesma lista, **When** se observa o que a tela
   mostra, **Then** não há nome completo, telefone, documento,
   endereço, CEP, cidade, data de nascimento nem profissão do
   hóspede — em nenhum item, título, detalhe ou recado.
3. **Given** cada item aberto que o perfil operacional pode
   resolver, **When** a pessoa olha a linha, **Then** há exatamente
   um botão rotulado para marcar como resolvido; não há segundo
   passo de “tem certeza?”, não há campo de texto para recado,
   clicar fora do botão (descrição, quarto, natureza) **não**
   resolve, e **não** há caminho à ficha nem à reserva nominada.
4. **Given** um consumo aberto, **When** ele aparece em Meus
   chamados, **Then** a natureza é consumo, o valor praticado é
   visível para a entrega, e o botão resolve o atendimento no
   quarto — não lança nem dispensa no sistema de gestão.
5. **Given** pendências da propriedade A, **When** um profissional
   da propriedade B abre Meus chamados, **Then** os itens de A não
   aparecem e a consulta não revela que existem.
6. **Given** a lista no celular, **When** a pessoa usa a tela com
   uma mão, **Then** o botão de resolver é o alvo principal de cada
   cartão, a lista é a tela inteira (sem navegação extra para
   “abrir o chamado”), e o desenho compacto da equipe permanece —
   sem depender de computador.
7. **Given** várias pendências abertas, **When** a equipe olha
   Meus chamados, **Then** a ordem é a mesma da recepção: mais
   antigos primeiro; reclamação em destaque de prazo não sobe só
   por isso.

---

### User Story 3 - Resolver confirma ao hóspede e some da lista (Priority: P1)

Como hóspede que reclamou ou pediu, e como hotel que precisa da
prova do ciclo, quero que um toque em **Resolvido** grave quem
fechou e quando, tire o item da lista aberta e avise o hóspede de
que o atendimento concluiu — automaticamente, sem a equipe redigir
mensagem e sem segundo toque mandar segundo recado.

**Why this priority**: É o segundo critério de aceite da fatia. O
clique interno sem o recado deixa o hóspede no escuro; o recado
sem o clique inventa um conserto. Os dois já existem; a tela é o
gesto que os dispara no turno.

**Independent Test**: Pode ser testado autenticando recepção ou
equipe, marcando um item aberto como resolvido pelo botão
rotulado, e conferindo: o item some da lista sem pedir a tela de
novo, constam autor e instante, e o hóspede recebe a confirmação
de conclusão já definida para aquele tipo — uma só.

**Acceptance Scenarios**:

1. **Given** uma reclamação ou um serviço aberto na lista da
   recepção ou da equipe, **When** a pessoa aciona o botão
   rotulado de resolvido, **Then** o item deixa de aparecer entre
   as pendências abertas nas duas telas, sem a pessoa pedir a
   lista de novo, e a confirmação ao hóspede de atendimento
   concluído é disparada automaticamente — recado padrão do tipo,
   sem a equipe escrever texto.
2. **Given** um consumo aberto, **When** recepção ou equipe marca
   como resolvido, **Then** o item some desta lista aberta e o
   hóspede é avisado de pedido atendido; o consumo **permanece**
   pendente de lançamento — resolver o quarto não lança no sistema
   de gestão.
3. **Given** o desfecho do cenário 1, **When** se observa a ordem,
   **Then** a resolução já está registrada antes de o recado
   existir como aviso ao hóspede; zero hóspedes são avisados de
   um fechamento que ainda não foi gravado.
4. **Given** um item já resolvido (toque duplo, lista desatualizada
   ou outro autorizado tentando de novo), **When** alguém aciona
   resolver outra vez, **Then** a tentativa é recusada de forma
   visível, quem resolveu e quando permanecem os da primeira vez,
   e o hóspede não recebe segunda confirmação.
5. **Given** uma sessão de gestão, **When** a pessoa tenta resolver
   pelo painel desta fatia, **Then** não há botão de resolver: a
   gestão não opera Chamados e pedidos nem Meus chamados.

---

### User Story 4 - A equipe não abre ficha por caminho nenhum (Priority: P1)

Como responsável pelos dados dos hóspedes, quero que o perfil
operacional não alcance ficha cadastral — nem por atalho na lista
de chamados, nem colando o endereço da ficha, nem por identificador
de reserva visível como convite a “ver o hóspede” — para a
minimização não depender de o profissional “não clicar”.

**Why this priority**: É o quinto critério de aceite da fatia. A
casca já omite o destino; esta fatia preenche Meus chamados e não
pode abrir uma porta que a autorização já fechou.

**Independent Test**: Pode ser testado autenticando o perfil
operacional, conferindo que Meus chamados não oferece abrir ficha,
tentando o endereço da ficha de uma reserva da casa, e verificando
recusa sem nome, telefone, documento nem endereço.

**Acceptance Scenarios**:

1. **Given** uma sessão de perfil operacional em Meus chamados,
   **When** a pessoa olha cada item, **Then** não há controle,
   ligação nem texto que leve à ficha do hóspede.
2. **Given** a mesma sessão, **When** a pessoa tenta abrir pelo
   endereço a ficha de uma reserva da casa, **Then** o acesso é
   recusado, nenhum dado cadastral aparece, e não há tela em
   branco.
3. **Given** a mesma sessão, **When** a pessoa tenta abrir
   Chamados e pedidos da recepção ou a fila do dia pelo endereço,
   **Then** o acesso é recusado e nenhum nome nem telefone
   aparece.
4. **Given** uma sessão de recepção em Chamados e pedidos, **When**
   a pessoa olha a lista, **Then** a linha **não** mostra nome,
   telefone nem documento; o nome e a ficha aparecem só depois de
   seguir a linha até a reserva correspondente.

---

### User Story 5 - No celular, sem autenticar a cada chamado (Priority: P1)

Como profissional da equipe no meio do corredor, quero recarregar
Meus chamados ou voltar mais tarde no mesmo aparelho e continuar
reconhecido, sem digitar senha de novo, e quero que a lista caiba
na tela de telefone — letra legível, um botão por item, sem tabela
de computador.

**Why this priority**: É o quarto critério de aceite da fatia. A
sessão longa já existe; se esta tela a quebrar ou exigir
computador, o registro do chamado é abandonado.

**Independent Test**: Pode ser testado autenticando a equipe no
celular (ou no desenho compacto equivalente), resolvendo um item,
recarregando, e conferindo que a pessoa permanece em Meus chamados
sem nova entrada, com a lista ainda utilizável em tela estreita.

**Acceptance Scenarios**:

1. **Given** um profissional operacional autenticado em Meus
   chamados, **When** ele recarrega a página no mesmo aparelho com
   a sessão ainda válida, **Then** permanece reconhecido na mesma
   tela, vê a lista (ou o vazio honesto), e não volta à entrada.
2. **Given** a mesma sessão, **When** ele marca um item como
   resolvido e em seguida abre outro item da lista, **Then** não é
   pedido e-mail nem senha entre um chamado e o outro.
3. **Given** Meus chamados aberto em tela de telefone, **When** há
   ao menos um item, **Then** natureza, tempo, quarto, descrição e
   o botão de resolver cabem sem rolagem horizontal e sem depender
   de passar o dedo para achar a ação.
4. **Given** recepção em Chamados e pedidos no computador do
   balcão, **When** a lista é usada, **Then** o desenho compacto de
   mão **não** é exigido — o balcão opera em tela larga; o compacto
   é da equipe.

---

### User Story 6 - Lista vazia, falha e isolamento não se confundem (Priority: P2)

Como recepcionista e como profissional da equipe, quero distinguir
“não há nada aberto”, “a lista não carregou” e “esta tela não é
sua”, para eu não achar que o turno está limpo quando a leitura
falhou, nem ver chamado de outro papel ou de outro hotel.

**Why this priority**: Sem isso, a omissão deixa de ser perceptível
(Artigo V) e a minimização depende de sorte. Fica em P2 porque o
turno já entrega valor com a lista cheia e o resolver.

**Independent Test**: Pode ser testado com hotel sem pendência
aberta, com falha ao ler a lista, com gestão e com recepção
tentando a casa da equipe, conferindo três estados visíveis
distintos e zero vazamento de dado.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção ou de equipe e nenhuma
   pendência aberta na casa, **When** a pessoa abre a tela do seu
   papel, **Then** vê o destino nomeado com estado de lista vazia
   explícito — não uma página em branco, não o aviso de falha.
2. **Given** que a lista não carregou, **When** a pessoa está em
   Chamados e pedidos ou em Meus chamados, **Then** o painel
   permanece, a lista declara que não carregou, oferece tentar de
   novo, e **não** mostra o estado de lista vazia.
3. **Given** uma sessão de gestão, **When** a pessoa tenta abrir
   Chamados e pedidos ou Meus chamados pelo endereço, **Then** o
   acesso é recusado, nenhum chamado é listado, e não há tela em
   branco. Indicadores da gestão continuam na fatia dela.
4. **Given** uma sessão de recepção, **When** a pessoa tenta abrir
   Meus chamados pelo endereço, **Then** é recusada sem ver a lista
   compacta da equipe; o caminho dela é Chamados e pedidos.

---

### Edge Cases

- Lista vazia de verdade (zero abertas na casa): destino nomeado,
  contas em zero, sem botão de resolver órfão. Zero só vale quando
  a leitura concluiu; não se usa para disfarçar falha.
- Falha ao ler: o painel permanece; aviso de que não carregou;
  tentar de novo. Não é tela de entrada, não é página vazia, não é
  lista vazia.
- Falha ao resolver (rede ou recusa): o item permanece na lista; o
  hóspede não recebe confirmação nova; a pessoa pode tentar de
  novo. Não há tela de erro de sistema no lugar da lista.
- Toque duplo no mesmo botão: uma resolução, uma confirmação.
- Item resolvido por outra pessoa enquanto a lista ainda o mostra:
  o segundo toque é recusado de forma visível; a lista deixa de
  exibir o item.
- Pendência sem quarto: aparece mesmo assim, perceptível — não some
  por estar incompleta; o sistema não inventa número de quarto. Na
  recepção, a identificação de quem abriu é o caminho da linha até
  a reserva correspondente, não um nome na lista.
- Reclamação sem janela de preferência: aparece sem horário; não
  bloqueia resolver.
- Status “em andamento” se existir no registro: continua pendência
  aberta nesta tela; não há aba nem passo para mover para
  andamento. Atribuir responsável em passo separado continua fora.
- Reserva já encerrada: não impede resolver. O trabalho no quarto
  pode fechar depois da saída; o recado ainda é devido.
- Consumo resolvido no quarto continua pendente de lançamento. Esta
  tela **não** oferece lançar nem dispensar.
- Pergunta fora do catálogo (fila humana de dúvida) **não** entra
  nesta lista. Chamados e pedidos são reclamação, serviço e
  consumo. Atender dúvida no balcão não é esta fatia.
- Histórico de resolvidos do dia, canal (WhatsApp ou outro) e
  coluna de “atribuído a manutenção/governança” **não** entram:
  não há responsável pessoal e não há lista de encerrados nesta
  superfície.
- Gestão consulta números na fatia dela; não opera estas duas
  telas.
- Perfil operacional no computador: Meus chamados continua sendo a
  casa; o destino não muda por tamanho de tela. O desenho compacto
  permanece o da equipe.
- Recepção ou gestão no celular: esta fatia não promete layout de
  mão para Chamados e pedidos da recepção.
- Dois profissionais da mesma casa: os dois vêem a mesma lista
  aberta da propriedade. Não há fila “só os meus”.
- Isolamento por hotel: sessão de A nunca lista item de B.
- Sair, sessão vencida ou revogada: voltam à entrada, como já é
  regra da casca; esta fatia não redesenha sessão.
- Reclamação com tempo excessivo: permanece destacada na posição
  que a idade determina; não sobe ao topo só pelo destaque.
- A palavra “extrato” e a palavra “conta” não aparecem na
  interface, nem no consumo.

## Requirements *(mandatory)*

### Functional Requirements

**Lista da recepção (Chamados e pedidos)**

- **FR-001**: A recepção DEVE ver, em Chamados e pedidos, todas as
  pendências ainda abertas da própria propriedade: reclamação,
  serviço operacional e consumo.
- **FR-002**: Cada item DEVE exibir natureza distinguível,
  descrição, quarto quando conhecido, urgência, instante de
  abertura e tempo decorrido visível desde então. Nas duas telas,
  a lista DEVE aparecer com os mais antigos primeiro (tempo aberto
  crescente). Destaque de tempo excessivo NÃO DEVE reordenar o
  item.
- **FR-003**: Reclamação DEVE exibir a janela de preferência quando
  o hóspede a tiver informado, e DEVE ser destacada quando o tempo
  aberto ultrapassar o prazo de destaque da propriedade. Serviço e
  consumo NÃO DEVEM usar esse destaque de prazo.
- **FR-004**: Consumo DEVE exibir o valor praticado e a natureza
  consumo. NÃO DEVE oferecer lançar nem dispensar nesta tela.
- **FR-005**: Item já resolvido NÃO DEVE aparecer. Item de outro
  hotel NÃO DEVE aparecer.
- **FR-006**: A lista da recepção NÃO DEVE exibir nome, telefone,
  documento, endereço nem demais dados da ficha do hóspede. Cada
  linha DEVE levar à reserva correspondente, no destino de ficha
  já entregue, para a recepção chegar ao nome e à ficha — inclusive
  quando o quarto não foi informado. Esse caminho DEVE ser distinto
  do botão de resolver: seguir a linha NÃO DEVE marcar como
  resolvido. Meus chamados NÃO DEVE oferecer caminho à ficha nem
  à reserva nominada.

**Lista da equipe (Meus chamados)**

- **FR-007**: O perfil operacional DEVE ver, em Meus chamados (casa
  do papel), as pendências ainda abertas da própria propriedade
  nas três naturezas — reclamação, serviço operacional e consumo
  — sem recorte por pessoa. Consumo aberto NÃO DEVE ser omitido
  desta lista.
- **FR-008**: Meus chamados NÃO DEVE exibir nome, telefone,
  documento, endereço, CEP, cidade, data de nascimento nem
  profissão do hóspede, em nenhum elemento da tela.
- **FR-009**: Cada item resolvível DEVE ter exatamente um botão
  rotulado para marcar como resolvido. Clicar no restante do item
  NÃO DEVE resolver.
- **FR-010**: Meus chamados DEVE ser utilizável em tela de
  telefone: lista como tela inteira, sem passo de “abrir o
  chamado”, sem rolagem horizontal para alcançar a ação.
- **FR-011**: Enquanto a sessão da equipe for válida, resolver um
  item NÃO DEVE pedir nova autenticação para o seguinte, nem ao
  recarregar a lista.

**Resolver**

- **FR-012**: Recepção e equipe operacional da própria propriedade
  DEVEM poder marcar como resolvida uma pendência aberta de
  reclamação, serviço ou consumo a partir destas telas, com o
  botão rotulado, sem diálogo extra e sem redigir recado.
- **FR-013**: Marcar como resolvida DEVE registrar quem resolveu e
  quando, retirar o item das listas abertas sem a pessoa pedir a
  tela de novo, e disparar automaticamente a confirmação ao
  hóspede já definida para aquele tipo.
- **FR-014**: A resolução DEVE estar gravada antes de o hóspede
  ser avisado. NÃO DEVE haver recado de conclusão sobre item ainda
  aberto.
- **FR-015**: Segunda tentativa no mesmo item DEVE ser recusada de
  forma visível, sem alterar autor e instante da primeira
  resolução e sem segunda confirmação ao hóspede.
- **FR-016**: Resolver consumo DEVE concluir o atendimento no
  quarto e NÃO DEVE lançar nem dispensar no sistema de gestão.
- **FR-017**: Gestão NÃO DEVE resolver. Chamados e pedidos e Meus
  chamados NÃO DEVEM ser oferecidos à gestão.

**Autorização e honestidade**

- **FR-018**: Perfil operacional NÃO DEVE alcançar a ficha do
  hóspede por atalho nestas telas nem pelo endereço. A recusa NÃO
  DEVE exibir dado cadastral nem tela em branco.
- **FR-019**: Recepção NÃO DEVE ver Meus chamados. Equipe NÃO DEVE
  ver Chamados e pedidos, fila do dia nem ficha. O que o perfil
  não pode usar NÃO DEVE aparecer no menu e DEVE ser recusado no
  endereço.
- **FR-020**: Lista vazia e falha ao ler DEVEM ser estados
  distintos. Falha NÃO DEVE ser apresentada como “nada aberto”.
  Falha ao resolver NÃO DEVE remover o item nem avisar o hóspede.
- **FR-021**: Esta fatia NÃO DEVE atribuir responsável, cancelar
  pendência, reabrir resolvida, lançar consumo, confirmar saída,
  editar catálogo, abrir chamado novo nem responder dúvida fora do
  catálogo.
- **FR-022**: Esta fatia NÃO DEVE integrar-se ao sistema de gestão
  do hotel nem alterar prazo de sessão, matriz de permissões ou
  textos de confirmação ao hóspede.
- **FR-023**: Log desta fatia NÃO DEVE registrar senha, conteúdo de
  mensagem, descrição do chamado, nome, telefone nem documento.
  PODE registrar identificador de usuário, de pendência, perfil,
  natureza e código de recusa.
- **FR-024**: Toda leitura e toda resolução DEVEM considerar a
  propriedade do funcionário. Sessão de um hotel NÃO DEVE mostrar
  nem fechar item de outro.
- **FR-025**: A interface NÃO DEVE usar as palavras “extrato” nem
  “conta”.

### Key Entities

- **Chamados e pedidos**: tela da recepção com as pendências
  abertas da casa. É o Alert Center no balcão. A lista não mostra
  nome; cada linha leva à reserva correspondente (ficha já
  existente). Não é a fila do dia (hóspedes) nem a fila de
  consumos a lançar.
- **Meus chamados**: tela inicial da equipe operacional, feita
  para o celular. Mesma fila aberta da casa, sem dado cadastral,
  com um botão por item. Não é uma fila pessoal por responsável.
- **Pendência aberta**: reclamação, serviço operacional ou consumo
  ainda não resolvido da propriedade. Some da lista ao ser
  resolvida. Não inclui pergunta fora do catálogo.
- **Natureza**: distintivo visível entre reclamação, serviço e
  consumo. Não é urgência e não é o destaque de prazo.
- **Tempo decorrido**: quanto tempo a pendência está aberta,
  visível em cada item, derivado do instante de abertura. Também
  define a ordem da lista: mais antigos primeiro, nas duas telas.
- **Destaque de tempo excessivo**: só na reclamação aberta além do
  prazo configurado da propriedade. Serviço e consumo não o usam.
- **Resolução**: gesto único que fecha a pendência, registra autor
  e instante, e dispara a confirmação padrão ao hóspede. No
  consumo, fecha o quarto; não lança cobrança.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma recepcionista autenticada identifica, em menos
  de 30 segundos após abrir Chamados e pedidos, quantas pendências
  estão abertas, a natureza de cada uma e há quanto tempo a mais
  antiga espera, sem abrir outro destino. Em 100% das listas com
  mais de um item, o primeiro é o mais antigo e o último o mais
  recente.
- **SC-002**: 100% das pendências abertas da casa (reclamação,
  serviço e consumo) aparecem nas listas desta fatia; 0% das já
  resolvidas aparecem; 0% das de outro hotel aparecem.
- **SC-003**: Em verificação lado a lado, reclamação, serviço e
  consumo são distinguíveis em 100% dos itens; 0% das linhas usam
  o mesmo rótulo para duas naturezas.
- **SC-004**: 100% das reclamações abertas além do prazo de
  destaque da propriedade aparecem destacadas; 0% dos serviços e
  consumos recebem esse destaque só pela idade.
- **SC-005**: Um profissional operacional autentica uma vez e
  marca um chamado como resolvido no celular em um único gesto, em
  menos de 15 segundos após ver o item, sem redigir recado e sem
  autenticar de novo.
- **SC-006**: Em 100% das resoluções bem-sucedidas, o item some da
  lista visível sem a pessoa pedir a tela de novo, e 100% disparam
  a confirmação automática ao hóspede; 0% avisam o hóspede antes
  de a resolução estar gravada.
- **SC-007**: 100% das segundas tentativas no mesmo item são
  recusadas; 0 segundas confirmações são enviadas ao hóspede.
- **SC-008**: A tela da equipe exibe 0 nome, 0 telefone e 0
  documento de hóspede. 100% das tentativas do perfil operacional
  de abrir ficha, fila do dia ou Chamados e pedidos são recusadas
  sem dado cadastral e sem tela em branco. 100% das linhas da
  recepção levam à reserva correspondente; 0% das linhas da equipe
  oferecem esse caminho. 100% das pendências sem quarto na
  recepção continuam identificáveis por esse caminho.
- **SC-009**: Em tela de telefone, 100% dos itens da equipe
  mostram natureza, tempo, descrição e o botão de resolver sem
  rolagem horizontal. 100% das recargas com sessão válida
  mantêm a equipe reconhecida em Meus chamados.
- **SC-010**: Em 100% das falhas ao ler a lista, o painel
  permanece, a lista declara que não carregou, e 0% mostram o
  estado de lista vazia ou tela em branco.
- **SC-011**: 100% das resoluções de consumo deixam o lançamento
  pendente; 0 lançamentos e 0 dispensas nascem destas telas.
- **SC-012**: 0 senhas, 0 nomes, 0 telefones, 0 documentos e 0
  conteúdos de mensagem aparecem em log desta fatia. 0 ocorrências
  das palavras “extrato” e “conta” na interface.
- **SC-013**: Cada critério de aceite da fatia F8.4 do backlog tem
  ao menos um cenário de aceitação correspondente nesta spec.

## Assumptions

- **O comportamento já existe; falta a superfície.** Listar
  pendências abertas da propriedade (sem ficha), distinguir os
  três tipos, expor quarto, urgência, janela, valor do consumo e
  destaque de prazo da reclamação, e resolver com confirmação
  automática ao hóspede foram entregues nas fatias de estadia.
  Esta fatia liga isso às duas telas já nomeadas na casca.
- **“Atribuídos a ela” é o trabalho da casa, não da pessoa.** Não
  existe passo de atribuir responsável. Recepção e equipe da mesma
  propriedade vêem a mesma lista aberta. Inventar fila pessoal
  nesta fatia criaria um recorte que o produto ainda não tem.
- **O desenho de telas é rascunho, não contrato.** O mapa mostra
  nome do hóspede, coluna de atribuído, canal, abas de andamento e
  de resolvidos do dia, pergunta fora do catálogo misturada,
  “abrir” em vez de resolver, e a tela da equipe só com reclamação
  e serviço. Nada disso foi entregue nas operações. Esta fatia
  segue o que já existe: lista única de abertas nas três naturezas
  (também no celular), sem cadastral, sem responsável, sem
  histórico do dia, resolver na própria linha, dúvida fora do
  catálogo fora daqui.
  Corrigir o mapa de telas para não prometer essas colunas é
  trabalho documental posterior, não bloqueio desta spec.
- **A casca já entrega os destinos.** Login, sessão longa da
  equipe, menu só com o que o papel pode usar, recusa de endereço
  alheio e desenho compacto da equipe são F8.1. Chamados e pedidos
  e Meus chamados deixam de ser só título.
- **Confirmação ao hóspede não se redige na tela.** O recado de
  conclusão já é padrão por tipo. A equipe não escolhe texto. A
  ordem continua: gravar a resolução, depois avisar.
- **Um clique no botão rotulado, sem “tem certeza?”.** O alvo é o
  botão, não o cartão inteiro — o mesmo critério da confirmação de
  chegada. Desfazer e reabrir continuam fora.
- **Consumos a lançar é outra tela.** A equipe vê e resolve o
  consumo no quarto, no mesmo gesto das outras naturezas. Resolver
  aqui não substitui a fila financeira da recepção. Valor na lista
  serve à entrega, não ao lançamento.
- **Ficha não se mistura na lista; a linha leva até ela.** A lista
  da recepção permanece sem nome. Cada linha abre a reserva
  correspondente no destino de ficha já entregue — é o único jeito
  de identificar quem abriu quando o quarto não veio. A equipe não
  tem esse caminho. Misturar o nome na própria lista reabriria o
  cadastral no recorte que o perfil operacional não pode ver.
- **Gestão não opera estas telas.** Ver indicadores de chamados
  abertos é F8.7. A gestão continua podendo consultar a fila
  operacional pelo caminho já existente, sem tela nesta fatia.
- **Mapa de telas já acordado para o que esta fatia cobre:**
  recepção em Chamados e pedidos no computador; equipe em Meus
  chamados no celular, um botão, sem cadastral.
- **F7.4 (módulos por propriedade) continua fora.** Chamados são
  núcleo: não desligam.
- **Uma propriedade por instalação no uso previsto da
  demonstração**, mas o isolamento por hotel permanece
  obrigatório.
- **Limitação honesta (Artigo XV):** se a equipe atende no quarto
  e não toca em Resolvido, o hóspede não é avisado e o item
  envelhece aberto. Esta tela torna a omissão perceptível na
  passagem de turno; não infere o conserto. Não há notificação
  empurrada para o celular — a lista é a fonte da verdade.
