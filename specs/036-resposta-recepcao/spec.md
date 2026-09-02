# Feature Specification: A recepção responde ao hóspede

**Feature Branch**: `036-resposta-recepcao`

**Created**: 2026-09-02

**Status**: Draft

**Input**: User description: "A recepção responde ao hóspede pelo
painel, com texto livre, quando o atendimento automático encaminha
uma pergunta ou quando ela precisa dizer algo sobre um chamado. A
resposta chega ao hóspede pelo mesmo canal em que ele escreveu e
fica registrada no histórico da conversa, junto das mensagens
automáticas."
(backlog F7.6)

Restrições já decididas no projeto (entrada do specify): hoje o
sistema avisa o hóspede que a recepção vai atender, abre o chamado
e permite marcá-lo como resolvido — **não existe forma de a
recepção escrever a resposta**; o hóspede chega a receber “seu
chamado foi resolvido” sem nunca ter recebido a resposta; a
resposta é texto livre (o hóspede escreveu há pouco, a janela de
conversa está aberta, não é preciso modelo aprovado); sai pelo
mesmo canal de origem da mensagem do hóspede; só o perfil de
recepção responde — a equipe operacional resolve chamado e não
escreve ao hóspede, a gestão não escreve; a tela **não** envia
direto — o envio segue o mesmo caminho das demais mensagens de
saída; falha no envio não perde o texto escrito: fica marcada para
nova tentativa e visível no painel; responder **não** resolve o
chamado automaticamente — são ações distintas; conteúdo de
mensagem continua fora do log; o sistema não se integra ao sistema
de gestão do hotel. Canal de e-mail, modelo aprovado para
mensagem fria e atribuição de responsável em passo separado
permanecem fora.

## Clarifications

### Session 2026-09-02

- Q: A recepção pode enviar texto livre a qualquer hóspede que já tenha escrito nesta estadia, ou só quando o automático encaminhou a pergunta ou há um chamado aberto? → A: Enquanto a janela de 24 horas do canal estiver aberta — o hóspede escreveu recentemente. Fora da janela, texto livre não é entregue (exigiria modelo aprovado, fora desta fatia). A tela mostra o campo com o motivo da janela fechada, em vez de escondê-lo. Não é permissão de negócio a inventar; é o comportamento do canal. “Não ser intrusivo” vale para disparo automático do sistema, não para um humano responder quem acabou de escrever. Chamado resolvido não impede complementar a informação.
- Q: Onde a recepção lê o histórico e escreve a resposta no painel? → A: No destino que hoje se chama Ficha do hóspede, que passa a se chamar **Estadia**. A conversa vem antes dos campos cadastrais (quem chega de um chamado veio responder, não ler documento). Os dados cadastrais ficam abaixo, recolhidos, abertos pelo controle “ver dados cadastrais”. O botão de copiar para o sistema de gestão do hotel permanece junto desses campos. Sem destino novo no menu.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A recepção lê a conversa e o hóspede recebe a resposta (Priority: P1)

Como recepcionista no balcão, quero abrir a conversa da estadia,
ler o que o hóspede e o sistema já disseram, e enviar um texto
livre enquanto a janela de 24 horas do canal estiver aberta, para
o hóspede receber de fato a resposta no mesmo canal em que
escreveu — e não só o recado de que “a recepção vai atender”
seguido, mais tarde, de “foi resolvido”.

**Why this priority**: É o buraco que esta fatia tapa. Sem o
envio, o ciclo de atendimento não fecha. É o primeiro critério de
aceite do backlog e o que torna o encaminhamento humano uma
conversa, não um beco.

**Independent Test**: Pode ser testado com uma estadia hospedada
em que o hóspede perguntou algo que o catálogo não cobre (já avisado
de que a recepção vai atender), autenticando recepção daquela
casa, abrindo a conversa, enviando um texto livre não vazio e
conferindo que o hóspede recebe exatamente esse texto no canal em
que escreveu, e que o mesmo texto aparece no histórico da conversa.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção e uma reserva hospedada da
   própria casa cujo hóspede perguntou algo que o atendimento
   automático não cobriu (já recebeu o aviso de que a recepção vai
   atender), **When** a pessoa abre a **Estadia** dessa reserva,
   **Then** a conversa (mensagens do hóspede e as automáticas, em
   ordem, e o campo para escrever) aparece **antes** dos dados
   cadastrais; os nove campos da ficha não ocupam o topo da tela.
2. **Given** o desfecho do cenário 1, **When** a recepção envia um
   texto livre não vazio, **Then** o hóspede recebe esse mesmo
   texto no canal em que escreveu, e o texto fica no histórico da
   conversa daquela reserva, distinguível das mensagens automáticas
   e das do hóspede.
3. **Given** um chamado operacional aberto (reclamação, serviço ou
   consumo) na mesma casa e a janela do canal aberta, **When** a
   recepção abre a Estadia da reserva correspondente a partir de
   Chamados e pedidos e envia um texto livre, **Then** o hóspede
   recebe esse texto no canal de origem, o chamado permanece
   aberto, e o recado padrão de “atendimento concluído” **não** é
   disparado por esse envio.
4. **Given** um chamado já resolvido, a janela do canal ainda
   aberta e a recepção da casa, **When** ela envia um texto
   complementar, **Then** o hóspede recebe esse texto, o chamado
   permanece resolvido e não há segundo recado de conclusão.
5. **Given** a fila do dia, **When** há estadia hospedada que
   precisa de resposta humana (pergunta não coberta ou
   classificação que encaminhou a uma pessoa), **Then** essa
   pendência é visível na linha da reserva, distinta das demais
   pendências já existentes (ficha incompleta, boas-vindas, chegada
   vencida), e a linha leva à Estadia, com a conversa no topo.
6. **Given** a Estadia aberta, **When** a recepção precisa dos
   dados cadastrais ou de copiar para o sistema de gestão do
   hotel, **Then** aciona **ver dados cadastrais**, os campos da
   ficha aparecem **abaixo** da conversa, e o controle de copiar
   permanece junto desses campos — não junto da conversa.

---

### User Story 2 - A resposta fica no histórico, junto das automáticas (Priority: P1)

Como recepcionista (e como hotel na passagem de turno), quero ver
na mesma conversa o que o hóspede escreveu, o que o sistema
respondeu sozinho, o aviso de encaminhamento e o que a recepção
escreveu, para o próximo turno não repetir a resposta nem
improvisar no escuro.

**Why this priority**: Sem histórico único, a resposta humana
vira recado oral. O critério de aceite pede registro junto das
automáticas.

**Independent Test**: Pode ser testado numa conversa que já tenha
mensagem do hóspede, resposta automática ou aviso de
encaminhamento, e uma resposta da recepção, conferindo que as três
naturezas aparecem no mesmo histórico da reserva, em ordem, sem
apagar nem reescrever o que já estava lá.

**Acceptance Scenarios**:

1. **Given** uma conversa com mensagem do hóspede, recado
   automático (aviso de encaminhamento ou resposta do catálogo) e
   resposta da recepção, **When** a recepção abre o histórico
   dessa estadia, **Then** as três aparecem juntas, cada uma com
   origem distinguível (hóspede × automático × recepção), na ordem
   em que ocorreram.
2. **Given** uma resposta da recepção ainda não entregue (falha de
   envio ou aguardando nova tentativa), **When** a recepção olha o
   histórico, **Then** o texto escrito está lá, marcado de forma
   distinta de uma mensagem já entregue — não some e não é
   apresentado como se o hóspede já tivesse recebido.
3. **Given** o mesmo histórico, **When** a gestão ou a equipe
   operacional tenta abri-lo, **Then** não alcançam a conversa nem
   o texto: esta leitura é da recepção da própria casa.

---

### User Story 3 - Falha no envio não perde o que foi escrito (Priority: P1)

Como recepcionista, quero que um envio que falhou preserve o texto
que eu já redigi, fique visível no painel como pendente de nova
tentativa, e não obrigue a digitar de novo, para “gravar antes de
enviar” valer também na resposta humana.

**Why this priority**: É restrição explícita da fatia e do Artigo
III. Perder o texto no clique seria pior do que o buraco atual.

**Independent Test**: Pode ser testado gravando uma resposta
válida e fazendo o envio ao canal falhar, conferindo que o texto
permanece no histórico da reserva, marcado para nova tentativa,
visível à recepção, e que o hóspede ainda não o recebeu; depois,
com o envio restabelecido, que uma única entrega ocorre sem a
recepção redigir de novo.

**Acceptance Scenarios**:

1. **Given** um texto livre já confirmado pela recepção, **When** o
   envio ao canal falha, **Then** o texto permanece gravado na
   conversa da reserva, visível no painel como não entregue /
   pendente de nova tentativa, e o hóspede não o recebe nessa
   passagem.
2. **Given** o desfecho do cenário 1, **When** o envio é
   restabelecido, **Then** o hóspede recebe exatamente aquele
   texto uma vez, sem a recepção ter de colar ou redigir de novo,
   e o histórico passa a marcá-lo como entregue.
3. **Given** um envio ainda pendente, **When** a recepção tenta
   enviar o mesmo texto outra vez no mesmo gesto, **Then** não
   nasce segunda cópia na conversa nem segunda entrega ao
   hóspede.

---

### User Story 4 - Só a recepção escreve; responder não fecha o chamado (Priority: P1)

Como hotel, quero que só a recepção da própria casa escreva ao
hóspede, que a equipe continue só resolvendo o trabalho no quarto,
e que enviar uma resposta **não** marque o chamado como resolvido,
para o conserto físico e o recado escrito não se misturarem.

**Why this priority**: Critérios de aceite do backlog. Sem a
separação, a equipe no celular passaria a redigir, ou o clique de
“enviar” fecharia a pendência antes do quarto ser atendido.

**Independent Test**: Pode ser testado autenticando recepção,
equipe e gestão; conferindo que só a recepção vê o campo de
escrever e consegue enviar; resolvendo um chamado sem ter
escrito; e enviando uma resposta com chamado aberto sem que ele
saia da lista de pendências.

**Acceptance Scenarios**:

1. **Given** uma sessão de equipe operacional, **When** a pessoa
   está em Meus chamados, **Then** não há campo para escrever ao
   hóspede, o botão de resolvido continua o único gesto por item,
   e tentar o endereço da conversa não revela o texto nem oferece
   envio.
2. **Given** uma sessão de gestão, **When** a pessoa navega o
   painel, **Then** não há conversa de hóspede nem envio de
   resposta.
3. **Given** um chamado aberto e uma resposta da recepção já
   enviada, **When** se consulta Chamados e pedidos, **Then** o
   chamado continua aberto; quem resolve e quando permanecem
   vazios até o gesto distinto de resolver.
4. **Given** um chamado aberto sem resposta da recepção, **When** a
   equipe ou a recepção marca como resolvido, **Then** o recado
   padrão de atendimento concluído segue como hoje — esta fatia
   não o substitui nem o impede. O buraco que ela tapa é a
   **possibilidade** de ter escrito antes, não a obrigação de
   escrever para poder resolver.

---

### User Story 5 - Quem não deve falar por esta casa não fala (Priority: P1)

Como hotel, quero que a recepção de um estabelecimento não leia
nem escreva na conversa de outro, e que texto vazio ou só espaços
não saia como mensagem, para não haver envio cruzado nem recado em
branco no canal do hóspede.

**Why this priority**: Multi-tenant e honestidade do envio. Sem
isso, o caminho feliz vaza ou polui o canal.

**Independent Test**: Pode ser testado com duas casas, tentando
abrir e enviar na conversa alheia, e tentando enviar texto vazio
na própria, conferindo recusa visível e zero mensagem nova ao
hóspede.

**Acceptance Scenarios**:

1. **Given** recepção do hotel A, **When** tenta abrir ou enviar
   na conversa de uma reserva do hotel B, **Then** a tentativa é
   recusada, o histórico de B não muda e o hóspede de B não
   recebe nada.
2. **Given** o campo de resposta aberto numa estadia da própria
   casa, **When** a recepção confirma envio com texto vazio ou só
   espaços, **Then** nada é gravado como mensagem de saída, nada
   é enviado, e a recusa é visível na tela.
3. **Given** a janela de 24 horas do canal fechada (o hóspede não
   escreveu recentemente, ou nunca escreveu nesta estadia),
   **When** a recepção abre a conversa, **Then** o campo de
   escrever permanece visível, o envio não é aceito, e o motivo
   (janela fechada / sem mensagem recente do hóspede) está
   declarado na tela — o campo não some sem explicação.

---

### Edge Cases

- Segunda confirmação de envio enquanto a primeira ainda está
  pendente: não duplica texto nem entrega.
- Hóspede já com saída confirmada: a conversa permanece
  recuperável para leitura; novo envio só se a janela de 24 horas
  do canal ainda estiver aberta.
- Nova pergunta do hóspede depois de uma resposta humana: entra
  no mesmo histórico; se o automático não cobrir de novo, o sinal
  de que a recepção precisa atender volta a aparecer; a janela
  reabre a partir dessa mensagem.
- Chamado já resolvido: a conversa continua legível e, com a
  janela aberta, a recepção pode complementar; isso não reabre o
  chamado nem dispara segundo recado de conclusão.
- Janela fecha enquanto a recepção ainda está com o texto no
  campo: o envio é recusado, o motivo aparece na tela, o texto
  digitado não some.
- Falha ao gravar (antes de qualquer envio): o hóspede não
  recebe; a tela declara que não gravou; o campo preserva o que a
  pessoa digitou para tentar de novo.
- Dois recepcionistas da mesma casa enviando ao mesmo tempo na
  mesma conversa: as duas respostas podem existir como mensagens
  distintas (são textos diferentes); o que não pode é o mesmo
  gesto gerar duas cópias idênticas.
- Conteúdo da resposta, da pergunta e do histórico: nunca em log
  operacional.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A recepção da própria propriedade DEVE poder ler o
  histórico da conversa de uma reserva da casa — mensagens do
  hóspede, recados automáticos e respostas da recepção — em ordem,
  com origem distinguível, inclusive depois da saída.
- **FR-002**: A recepção da própria propriedade DEVE poder enviar
  texto livre ao hóspede dessa reserva **somente** enquanto a
  janela de 24 horas do canal estiver aberta (o hóspede escreveu
  recentemente nesta estadia). Essa janela é a do canal, não um
  parâmetro da propriedade e não uma permissão de “encaminhamento
  ou chamado aberto”. Chamado resolvido NÃO DEVE, por si só,
  impedir o envio.
- **FR-003**: O texto enviado DEVE chegar ao hóspede pelo mesmo
  canal de origem da mensagem do hóspede. NÃO DEVE exigir modelo
  aprovado nem recado padrão.
- **FR-004**: A resposta da recepção DEVE ser gravada no histórico
  da conversa da reserva **antes** de ser enviada. A tela NÃO DEVE
  enviar direto ao canal.
- **FR-005**: Se o envio falhar, o texto já gravado DEVE
  permanecer, DEVE ficar visível no painel como pendente de nova
  tentativa (distinto de entregue), e DEVE ser reenviável sem a
  recepção redigir de novo. NÃO DEVE haver perda silenciosa.
- **FR-006**: Só o perfil de recepção da própria propriedade DEVE
  ler essa conversa e enviar. Equipe operacional e gestão NÃO
  DEVEM ver o histórico nem o campo de escrever; o que o perfil
  não pode usar NÃO DEVE aparecer e DEVE ser recusado no endereço.
- **FR-007**: Enviar resposta NÃO DEVE marcar chamado como
  resolvido, NÃO DEVE registrar autor/instante de resolução e NÃO
  DEVE disparar o recado padrão de atendimento concluído.
- **FR-008**: Resolver chamado DEVE continuar o gesto já
  existente, independente de ter havido resposta da recepção.
  Esta fatia NÃO DEVE tornar a resposta humana obrigatória para
  resolver.
- **FR-009**: Na fila do dia, estadia hospedada que precisa de
  atendimento humano (pergunta não coberta pelo catálogo ou
  classificação encaminhada a uma pessoa) DEVE ter essa pendência
  visível na linha, distinta das pendências já mostradas, e a
  linha DEVE levar à conversa para a recepção escrever.
- **FR-010**: Depois de uma resposta da recepção gravada para essa
  estadia, o sinal de que a recepção ainda precisa atender **por
  aquelas mensagens já encaminhadas** NÃO DEVE permanecer aceso só
  por elas. Uma nova mensagem do hóspede que o automático
  encaminhar DEVE acender o sinal de novo.
- **FR-011**: Texto vazio ou só espaços NÃO DEVE ser gravado nem
  enviado. A recusa DEVE ser visível na tela.
- **FR-012**: Tentativa da recepção de um hotel sobre conversa de
  outro DEVE ser recusada, sem alterar histórico alheio e sem
  envio ao hóspede alheio.
- **FR-013**: Chamados e pedidos DEVE continuar levando à reserva
  correspondente; desse caminho a recepção DEVE alcançar a mesma
  Estadia (conversa no topo, mesmo envio). Meus chamados NÃO DEVE
  oferecer escrever ao hóspede. O atalho que hoje se chama “Ver
  ficha” DEVE passar a nomear essa Estadia.
- **FR-014**: Esta fatia NÃO DEVE inventar destino de menu. O
  destino que hoje se chama “Ficha do hóspede” DEVE passar a
  chamar-se **Estadia** (menu, título da tela e atalhos a partir
  da fila do dia e de Chamados e pedidos). A conversa vive nessa
  tela.
- **FR-015**: Log operacional NÃO DEVE registrar conteúdo de
  mensagem (entrada, automática ou da recepção), nome, telefone
  nem documento. PODE registrar identificadores, perfil, canal,
  resultado do envio e código de recusa.
- **FR-016**: Esta fatia NÃO DEVE integrar-se ao sistema de gestão
  do hotel, NÃO DEVE abrir canal de e-mail, NÃO DEVE enviar
  mensagem fria com modelo aprovado, NÃO DEVE atribuir responsável
  em passo separado, NÃO DEVE alterar os recados padrão já
  existentes (aviso de encaminhamento, confirmação de pedido,
  confirmação de resolução) e NÃO DEVE usar a palavra “extrato”.
- **FR-017**: Novo envio nesta fatia NÃO DEVE ser aceito com a
  janela do canal fechada, mesmo que a reserva ainda esteja
  hospedada. O histórico DEVE permanecer legível à recepção da
  casa depois da saída; se a janela ainda estiver aberta, o envio
  continua permitido.
- **FR-018**: Com a janela fechada (hóspede não escreveu
  recentemente, ou nunca escreveu nesta estadia), o campo de
  escrever DEVE permanecer visível, o envio NÃO DEVE ser aceito, e
  o motivo DEVE estar declarado na tela. NÃO DEVE esconder o campo
  sem explicação. NÃO DEVE exigir modelo aprovado nesta fatia.
- **FR-019**: Na Estadia, a conversa (histórico e campo de
  escrever) DEVE aparecer **antes** dos campos cadastrais. Os
  dados cadastrais DEVEM ficar abaixo, inicialmente recolhidos, e
  DEVEM abrir pelo controle rotulado **ver dados cadastrais**. O
  controle de copiar para o sistema de gestão do hotel DEVE
  permanecer junto dos campos cadastrais, não junto da conversa.

### Key Entities

- **Estadia**: tela da reserva que a recepção já abre pela fila
  do dia e por Chamados e pedidos. Antes se chamava Ficha do
  hóspede. Agora reúne a conversa (no topo) e os dados cadastrais
  (abaixo, recolhidos). Não é um destino novo de menu.
- **Conversa da estadia**: histórico único da reserva, com
  mensagens do hóspede, recados automáticos e respostas da
  recepção. Não é a ficha cadastral e não é a lista de chamados.
- **Resposta da recepção**: texto livre redigido no painel,
  gravado na conversa e então enviado no canal de origem. Não é
  recado padrão e não é resposta automática do catálogo.
- **Pendência de atendimento humano**: sinal na fila do dia de que
  aquela estadia hospedada precisa de uma pessoa para responder
  (pergunta não coberta ou classificação encaminhada). Não é o
  chamado operacional da equipe (reclamação, serviço, consumo).
- **Estado de entrega da resposta**: visível no histórico
  (pendente / entregue / a tentar de novo). Permite recuperar
  falha pela leitura do painel.
- **Canal de origem**: o canal em que o hóspede escreveu a
  mensagem desta estadia. Nesta fatia é o único canal em que a
  resposta sai.
- **Janela de 24 horas do canal**: intervalo em que o canal
  entrega texto livre, aberto pela mensagem recente do hóspede.
  Não é parâmetro da propriedade. Fora dela, esta fatia não envia
  (modelo aprovado está fora).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos envios confirmados pela recepção com
  texto não vazio, o hóspede recebe esse texto no canal em que
  escreveu **ou** o painel ainda mostra o mesmo texto pendente de
  nova tentativa — zero perda silenciosa.
- **SC-002**: Uma recepcionista que já está na conversa da estadia
  conclui a leitura da última mensagem do hóspede e o envio de uma
  resposta curta em menos de dois minutos.
- **SC-003**: Depois da primeira resposta da recepção a uma
  pergunta encaminhada, a fila do dia deixa de marcar aquela
  estadia como aguardando a recepção **somente por essa
  pergunta**; 100% das novas perguntas encaminhadas voltam a
  marcar.
- **SC-004**: 0% das sessões de equipe operacional ou de gestão
  conseguem enviar texto ao hóspede por este caminho.
- **SC-005**: Um observador dos registros operacionais da fatia
  encontra zero corpos de mensagem, zero nomes e zero telefones.
- **SC-006**: Em 100% dos casos, enviar a resposta deixa o chamado
  operacional no mesmo estado em que estava (aberto continua
  aberto; resolvido continua resolvido).
- **SC-008**: Quem abre a Estadia a partir de um chamado vê a
  conversa no topo, sem precisar passar pelos campos cadastrais
  para escrever; os dados da ficha só aparecem depois de **ver
  dados cadastrais**.

## Assumptions

- O destino já existente da reserva (hoje “Ficha do hóspede”)
  passa a chamar-se **Estadia**: conversa no topo; dados
  cadastrais abaixo, recolhidos atrás de “ver dados cadastrais”;
  copiar para o sistema de gestão do hotel permanece junto da
  ficha. Sem item novo no menu. O nome “Hóspede” foi considerado e
  recusado em favor de Estadia, que nomeia a reserva e a conversa.
- O sinal de atendimento humano já existe na fila do dia como
  dado; a tela da fila ainda não o destaca. Esta fatia o torna
  visível e o usa como caminho até a conversa — não como condição
  para poder escrever.
- Pergunta fora do catálogo **não** entra em Chamados e pedidos
  (já decidido). O caminho dela é a fila do dia; o caminho do
  chamado operacional continua sendo Chamados e pedidos, que já
  leva à reserva.
- A janela de 24 horas é regra do canal (aberta pela última
  mensagem do hóspede nesta estadia), não chave em
  `parametro_hotel` e não recorte de “só encaminhamento ou chamado
  aberto”. “Não ser intrusivo” continua valendo para disparos
  automáticos do sistema, não para a recepção responder quem
  escreveu.
- A identidade no canal do hóspede continua sendo a da casa, não
  o nome da recepcionista.
- Duas respostas humanas distintas na mesma conversa são
  permitidas (a recepção pode escrever mais de uma vez, inclusive
  depois do chamado resolvido, enquanto a janela estiver aberta).
- E-mail como segundo canal, modelo aprovado para mensagem fria e
  módulos por propriedade permanecem nas fatias já mapeadas, fora
  deste recorte.
