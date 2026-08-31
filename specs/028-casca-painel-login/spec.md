# Feature Specification: Casca do painel e login

**Feature Branch**: `028-casca-painel-login`

**Created**: 2026-08-28

**Status**: Draft

**Input**: User description: "O funcionário entra com e-mail e senha e é
levado à tela inicial correspondente ao seu papel: a recepção à fila do
dia, a equipe operacional aos seus chamados, a gestão ao painel de
indicadores. A sessão permanece válida entre visitas no mesmo
dispositivo, e sair encerra a sessão no servidor. Enquanto a sessão for
válida, o funcionário não precisa autenticar de novo."
(backlog F8.1)

Restrições já decididas no projeto (entrada do specify): autenticar,
manter sessão e autorizar por perfil **já existem** (F0.3) — esta fatia
não inventa credencial, prazo nem matriz de permissões; a tela nunca
manipula o identificador da sessão (o funcionário permanece reconhecido
no mesmo dispositivo sem copiar código nenhum); recepção e gestão
operam no computador, e só a equipe operacional usa a tela no celular;
o que a autorização recusa, a tela não oferece; dado cadastral de
hóspede não aparece para quem não pode vê-lo; o sistema não se integra
ao sistema de gestão do hotel; conteúdo de mensagem e senha continuam
fora do log. Telas operacionais (fila com hóspedes, cadastro de
reserva, ficha, resolução de chamado, consumos, catálogo, recado,
usuários, mercado, retenção) permanecem nas fatias F8.2 a F8.7. Módulos
por propriedade (F7.4) e canal de e-mail (F7.5) permanecem fora.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Entrar e cair na tela do próprio papel (Priority: P1)

Como funcionário do hotel, quero entrar com o e-mail e a senha que já
uso no sistema e ser levado imediatamente à tela inicial do meu papel —
recepção na fila do dia, equipe operacional em meus chamados, gestão no
painel de indicadores — para começar o turno sem escolher destino e sem
esbarrar no trabalho de outro perfil.

**Why this priority**: Sem a entrada e o destino certo, o painel não
existe como produto. É o critério central da fatia e o que desbloqueia
todas as telas seguintes.

**Independent Test**: Pode ser testado autenticando um funcionário ativo
de cada perfil com credencial válida e conferindo que cada um chega à
tela inicial do seu papel, identificável pelo título, sem passar por um
seletor de destino.

**Acceptance Scenarios**:

1. **Given** um funcionário ativo de recepção com credencial válida e
   sem sessão aberta, **When** ele informa e-mail e senha e confirma
   entrar, **Then** ele deixa a tela de entrada e chega à fila do dia
   como tela inicial, identificável pelo título.
2. **Given** um funcionário ativo de perfil operacional com credencial
   válida e sem sessão aberta, **When** ele entra, **Then** chega a
   meus chamados como tela inicial, identificável pelo título.
3. **Given** um funcionário ativo de gestão com credencial válida e
   sem sessão aberta, **When** ele entra, **Then** chega ao painel de
   indicadores como tela inicial, identificável pelo título.
4. **Given** um funcionário já reconhecido no dispositivo, **When** ele
   abre de novo a tela de entrada, **Then** não precisa autenticar: é
   levado à tela inicial do seu papel.

---

### User Story 2 - Credencial inválida não ensina quem existe (Priority: P1)

Como responsável pelos acessos do hotel, quero que e-mail inexistente,
senha errada e usuário desativado produzam a mesma recusa visível, sem
dizer se aquele e-mail está cadastrado, para que tentativa de adivinhar
não vire lista de funcionários.

**Why this priority**: É critério de aceite da fatia e já é regra de
autenticação. A tela de entrada não pode enfraquecer o que o sistema já
garante.

**Independent Test**: Pode ser testado tentando entrar com e-mail
desconhecido, com e-mail existente e senha errada, e com usuário
desativado e senha correta, e conferindo recusa indistinguível e
permanência na tela de entrada.

**Acceptance Scenarios**:

1. **Given** a tela de entrada sem sessão, **When** alguém tenta entrar
   com e-mail que não existe e quando tenta com e-mail existente e senha
   errada, **Then** as duas recusas são indistinguíveis entre si, ninguém
   entra, e a pessoa permanece na tela de entrada.
2. **Given** um usuário desativado com a senha que era a correta,
   **When** ele tenta entrar, **Then** o acesso é recusado da mesma
   forma visível, sem mensagem especial de desativação.
3. **Given** e-mail ou senha em branco, **When** alguém confirma entrar,
   **Then** o sistema não autentica e pede o que falta, sem tratar o
   caso como “e-mail não encontrado”.

---

### User Story 3 - Continuar reconhecido no mesmo dispositivo (Priority: P1)

Como funcionário no meio do turno (e, no caso da equipe, com as mãos
ocupadas no celular), quero recarregar a página ou voltar mais tarde no
mesmo aparelho e continuar onde o meu papel começa, sem digitar senha de
novo enquanto a sessão for válida.

**Why this priority**: A sessão longa por dispositivo já foi decidida
para a equipe não abandonar o registro do chamado. Sem isso na tela, o
login vira obstáculo a cada visita.

**Independent Test**: Pode ser testado autenticando, recarregando a
página na tela inicial, fechando e reabrindo o painel no mesmo
dispositivo dentro do prazo da sessão, e conferindo que a pessoa
permanece reconhecida e na tela do seu papel.

**Acceptance Scenarios**:

1. **Given** um funcionário autenticado na tela inicial do seu papel,
   **When** ele recarrega a página, **Then** permanece reconhecido na
   mesma tela, sem voltar à entrada e sem tela em branco.
2. **Given** um funcionário autenticado que encerrou o navegador e
   voltou no mesmo dispositivo ainda dentro do prazo da sessão,
   **When** ele abre o painel, **Then** não precisa autenticar de novo
   e chega à tela inicial do seu papel.
3. **Given** uma sessão ainda válida, **When** o funcionário navega
   entre destinos que o seu perfil pode usar, **Then** não é pedido
   e-mail nem senha de novo.

---

### User Story 4 - Sair encerra de verdade (Priority: P1)

Como funcionário que deixa o computador ou o celular, quero um sair
visível que encerre a sessão no servidor — não só esconda a tela — para
que a próxima pessoa naquele aparelho não herde o meu acesso.

**Why this priority**: Sem encerramento no servidor, “sair” é teatro:
recarregar devolveria a pessoa autenticada. É critério de aceite da
fatia.

**Independent Test**: Pode ser testado autenticando, saindo, tentando
abrir de novo o painel no mesmo dispositivo, e conferindo que a tela de
entrada reaparece e que o acesso autenticado anterior deixou de ser
aceito.

**Acceptance Scenarios**:

1. **Given** um funcionário autenticado em qualquer tela do painel,
   **When** ele escolhe sair, **Then** a sessão deixa de ser aceita e
   a tela de entrada reaparece.
2. **Given** que o funcionário acabou de sair, **When** ele recarrega
   a página ou tenta abrir a tela inicial do seu papel, **Then** é
   tratado como visitante: vê a tela de entrada e não vê dado do
   hotel.
3. **Given** duas sessões do mesmo usuário em dispositivos diferentes,
   **When** ele sai em um deles, **Then** só a sessão daquele
   dispositivo se encerra; a outra continua válida.

---

### User Story 5 - O menu só oferece o que o papel pode usar (Priority: P2)

Como responsável pelos dados dos hóspedes, quero que o menu de cada
perfil mostre apenas destinos daquele papel, e que um endereço de tela
alheia seja recusado sem vazar informação, para que a minimização não
dependa de o funcionário “não clicar”.

**Why this priority**: Autenticação sem filtro visível entrega porta
aberta e parede invisível. A regra da fase é: o que a autorização
recusa, a tela não oferece. Fica em P2 porque o login já entrega valor
com as três telas iniciais.

**Independent Test**: Pode ser testado autenticando cada perfil,
listando o que o menu mostra e o que omite, e tentando abrir o destino
inicial de outro perfil pelo endereço, conferindo recusa sem dado.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção, **When** a pessoa olha o menu,
   **Then** vê os destinos de recepção (inclusive a fila do dia e o
   simulador de conversa, que ela já pode usar) e **não** vê meus
   chamados da equipe nem o painel de indicadores da gestão.
2. **Given** uma sessão de perfil operacional, **When** a pessoa olha
   o menu, **Then** vê meus chamados e não vê fila do dia, ficha,
   catálogo, simulador de conversa, painel da gestão nem destinos de
   administração.
3. **Given** uma sessão de gestão, **When** a pessoa olha o menu,
   **Then** vê o painel de indicadores e o simulador de conversa, e
   **não** vê fila do dia, ficha, meus chamados nem o destino de
   revogar dispositivo (urgência da recepção, não da gestão).
4. **Given** uma sessão de um perfil, **When** a pessoa tenta abrir
   pelo endereço a tela inicial de outro perfil, **Then** o acesso é
   recusado, nenhum dado daquela tela é exibido, e não há tela em
   branco.

---

### User Story 6 - Sessão vencida devolve à entrada, sem tela morta (Priority: P2)

Como funcionário cujo prazo de sessão acabou (ou cuja sessão foi
revogada no balcão), quero ser levado de volta à tela de entrada com um
aviso compreensível, nunca a uma página vazia, para retomar o trabalho
sem achar que o sistema quebrou.

**Why this priority**: É o último critério de aceite da fatia. Uma
sessão longa que expira no celular da equipe sem caminho de volta vira
abandono do registro do chamado.

**Independent Test**: Pode ser testado autenticando, fazendo a sessão
deixar de valer (prazo esgotado ou revogação), tentando recarregar ou
navegar, e conferindo retorno à entrada sem tela vazia.

**Acceptance Scenarios**:

1. **Given** um funcionário autenticado cuja sessão acabou de expirar,
   **When** ele recarrega a página ou tenta ir a outro destino do
   painel, **Then** vê a tela de entrada, não uma página em branco, e
   nenhum dado do hotel permanece visível.
2. **Given** um funcionário autenticado cuja sessão foi revogada pela
   recepção, **When** ele tenta continuar no painel, **Then** o efeito
   visível é o mesmo da expiração: volta à entrada, sem dado residual.
3. **Given** que voltou à entrada por sessão inválida, **When** ele
   entra de novo com credencial válida, **Then** chega à tela inicial
   do seu papel como na primeira vez.

---

### Edge Cases

- Identificador de sessão forjado ou adulterado: tratado como
  visitante sem sessão — tela de entrada, sem dado.
- Usuário desativado depois de já autenticado: o acesso cai na visita
  seguinte, como qualquer sessão que deixou de valer.
- Sair sem ter sessão: a tela de entrada permanece; não há erro
  visível de sistema.
- Abrir o painel em duas abas, sair em uma: a outra, ao continuar,
  também é tratada como visitante.
- Perfil operacional no computador (não só no celular): a tela inicial
  continua sendo meus chamados; o destino não muda por tamanho de
  tela.
- Recepção ou gestão no celular: esta fatia não promete layout de
  mão; o login e o destino inicial funcionam, mas o desenho compacto
  é só da equipe.
- Destino cujo trabalho operacional ainda não foi entregue (fila com
  hóspedes, lista de chamados, números do painel): a pessoa chega à
  tela nomeada do seu papel, sem dado inventado e sem ação da fatia
  seguinte.
- Tentativa repetida de adivinhar senha: continua fora, como na
  autenticação já entregue — escolha registrada, não esquecimento.

## Requirements *(mandatory)*

### Functional Requirements

**Entrada**

- **FR-001**: O painel DEVE autenticar o funcionário com o mesmo
  e-mail e a mesma senha já usados no sistema. NÃO DEVE existir
  segundo cadastro nem segundo tipo de credencial só para a tela.
- **FR-002**: Credencial inválida (e-mail inexistente, senha errada ou
  usuário desativado) DEVE recusar a entrada sem revelar se o e-mail
  está cadastrado. As recusas visíveis DEVEM ser indistinguíveis
  entre si.
- **FR-003**: E-mail ou senha em branco NÃO DEVEM autenticar.
- **FR-004**: Entrada bem-sucedida DEVE levar o funcionário à tela
  inicial do seu perfil, sem passo intermediário de escolha:
  recepção → fila do dia; operação → meus chamados; gestão → painel
  de indicadores.
- **FR-005**: Funcionário já reconhecido no dispositivo NÃO DEVE
  precisar autenticar de novo para ver a tela inicial do seu papel
  enquanto a sessão for válida.

**Sessão na tela**

- **FR-006**: Recarregar a página com sessão válida DEVE manter o
  funcionário reconhecido na tela em que estava (ou na inicial do
  papel, se o destino anterior não puder ser restaurado), sem tela
  em branco.
- **FR-007**: A tela NÃO DEVE exibir, copiar nem pedir que o
  funcionário guarde um código de sessão. Permanecer reconhecido no
  mesmo dispositivo é automático enquanto a sessão valer.
- **FR-008**: Sair DEVE encerrar a sessão no servidor e devolver à
  tela de entrada. Recarregar depois de sair NÃO DEVE restaurar o
  acesso.
- **FR-009**: Sair em um dispositivo NÃO DEVE encerrar as outras
  sessões do mesmo usuário em outros dispositivos.
- **FR-010**: Sessão expirada ou revogada DEVE devolver à tela de
  entrada na próxima ação (recarregar ou navegar), sem página vazia
  e sem dado do hotel visível.

**Navegação e perfil**

- **FR-011**: O menu DEVE listar apenas destinos que o perfil autenticado
  pode usar. Item que o perfil não pode usar NÃO DEVE aparecer.
- **FR-012**: Destinos de recepção NÃO DEVEM aparecer para operação
  nem para gestão quando forem exclusivos da recepção (fila do dia,
  ficha, revogar dispositivo). Destinos exclusivos da equipe (meus
  chamados) NÃO DEVEM aparecer para recepção nem gestão. Destinos
  exclusivos da gestão (painel de indicadores como casa da gestão)
  NÃO DEVEM aparecer como casa da recepção ou da equipe.
- **FR-013**: O simulador de conversa, já existente, DEVE permanecer
  visível no menu de recepção e de gestão. NÃO DEVE aparecer no menu
  do perfil operacional.
- **FR-014**: Tentar abrir pelo endereço um destino que o perfil não
  pode usar DEVE ser recusado sem exibir o conteúdo daquela tela.
- **FR-015**: Visitante sem sessão que abrir qualquer destino interno
  DEVE ver a tela de entrada, não uma página vazia e não o conteúdo
  protegido.
- **FR-016**: Dado cadastral de hóspede (nome, telefone, documento)
  NÃO DEVE aparecer para o perfil operacional em nenhum destino desta
  fatia.

**Escopo e honestidade**

- **FR-017**: Esta fatia NÃO DEVE cadastrar reserva, confirmar
  chegada ou saída, editar ficha, resolver chamado, lançar consumo,
  alterar catálogo, editar recado, criar usuário, revogar dispositivo
  pela lista, consultar mercado nem consultar retenção. Essas ações
  pertencem às fatias seguintes.
- **FR-018**: Telas iniciais nesta fatia DEVEM ser reconhecíveis pelo
  título do destino. NÃO DEVEM apresentar hóspede, chamado ou
  indicador inventados para simular o trabalho futuro.
- **FR-019**: Esta fatia NÃO DEVE alterar prazo de sessão, matriz de
  permissões, instalação inicial da propriedade nem a forma de guardar
  senha. NÃO DEVE integrar-se ao sistema de gestão do hotel.
- **FR-020**: Log desta fatia NÃO DEVE registrar senha, identificador
  de sessão apresentado ao cliente, nem conteúdo de mensagem. PODE
  registrar identificador de usuário, perfil, resultado da entrada e
  código de recusa.
- **FR-021**: Toda leitura de destino autenticado DEVE considerar a
  propriedade do funcionário. Sessão de um hotel NÃO DEVE mostrar
  tela ou dado de outro.

### Key Entities

- **Tela de entrada**: superfície em que qualquer perfil informa
  e-mail e senha. É o único destino visível sem sessão válida.
- **Tela inicial do papel**: destino para o qual a entrada bem-sucedida
  leva o funcionário — fila do dia (recepção), meus chamados
  (operação), painel de indicadores (gestão). Nesta fatia, é o ponto
  de chegada identificável; o trabalho operacional de cada uma vem
  depois.
- **Menu do perfil**: lista visível de destinos permitidos àquele
  papel. Omissão é a proteção visível; a recusa ao abrir destino
  alheio é a proteção de fato.
- **Sessão** *(existente)*: reconhecimento do funcionário num
  dispositivo, com prazo por perfil e revogação já entregues. O
  painel a usa; não a redesenha.
- **Funcionário** *(existente)*: usuário ativo com e-mail, senha e um
  dos três perfis — recepção, operação ou gestão.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um funcionário ativo de cada perfil completa a entrada
  com credencial válida e chega à tela inicial correta em menos de
  1 minuto, sem ajuda e sem escolher destino.
- **SC-002**: 100% das tentativas com e-mail inexistente, senha
  errada ou usuário desativado permanecem na tela de entrada e 0%
  revelam se o e-mail está cadastrado.
- **SC-003**: Em 100% das recargas com sessão válida, o funcionário
  permanece reconhecido e 0% vêem tela em branco.
- **SC-004**: Depois de sair, 100% das visitas seguintes no mesmo
  dispositivo exigem nova entrada; 0% restauram o acesso só com
  recarregar.
- **SC-005**: 0 itens de menu visíveis para um perfil correspondem a
  destinos que esse perfil não pode usar. 100% das tentativas de
  abrir destino alheio pelo endereço são recusadas sem exibir o
  conteúdo.
- **SC-006**: Sessão expirada ou revogada devolve à tela de entrada
  em 100% das próximas ações, com 0 páginas em branco e 0 dado do
  hotel visível depois da recusa.
- **SC-007**: Perfil operacional vê 0 nome, telefone ou documento de
  hóspede em qualquer destino desta fatia.
- **SC-008**: 0 senhas e 0 conteúdos de mensagem aparecem em log
  desta fatia.
- **SC-009**: Em verificação com dois hotéis, 0% das telas de um são
  visíveis na sessão do outro.
- **SC-010**: Cada critério de aceite da fatia F8.1 do backlog tem ao
  menos um cenário de aceitação correspondente nesta spec.

## Assumptions

- **A autenticação já existe.** Entrar, recusar credencial
  indistinguível, manter sessão por dispositivo, expirar, revogar e
  autorizar por perfil foram entregues na F0.3. Esta fatia é a
  superfície do funcionário sobre esse comportamento, não um segundo
  sistema de acesso.
- **A tela não guarda sessão por conta própria.** O reconhecimento no
  dispositivo é o que o sistema já emite ao autenticar. Nada de
  “lembrar-me” paralelo, nem código colável pelo funcionário.
- **Telas iniciais nesta fatia são pontos de chegada, não o turno.**
  Ver quem chega hoje, cadastrar reserva e confirmar chegada são
  F8.2. Ver e resolver chamados é F8.4. Números do painel da gestão,
  usuários, mercado e retenção são F8.7. Catálogo, itens vendáveis e
  recado são F8.6. Ficha é F8.3. Consumos e saída são F8.5. A casca
  leva a pessoa ao lugar certo; não antecipa a operação.
- **O menu já mostra o mapa do papel**, para o filtro por perfil ser
  observável desde o primeiro dia. Destinos cujo trabalho ainda não
  foi entregue aparecem como tela nomeada, sem ação operacional e
  sem dado inventado.
- **O simulador de conversa já entregue entra no menu** de recepção e
  gestão. Continua recusado ao perfil operacional. Não é tela nova
  desta fatia.
- **Computador no balcão e na sala; celular só na equipe.** Login da
  recepção e da gestão não precisa de desenho compacto. A tela
  inicial da equipe precisa ser utilizável em tela de telefone
  (chegar, ver o título, sair), mesmo vazia de chamados.
- **Redefinição de senha, “lembrar-me” extra e limite de tentativas
  continuam fora**, como na F0.3. Gestão desativa e cria de novo.
  Contenção de adivinhação entra antes de exposição contínua à
  internet, não nesta fatia.
- **Dispositivos conectados (listar e revogar) não entram nesta
  fatia.** A recepção já tem a operação; a tela da lista é destino
  posterior. Sair encerra só a sessão atual.
- **F7.4 (módulos por propriedade) continua fora do plano da semana.**
  Esta casca não esconde destino por módulo ligado ou desligado —
  só por perfil.
- **Uma propriedade por instalação no uso previsto da demonstração**,
  mas o isolamento por hotel permanece obrigatório (o funcionário só
  vê a casa da própria sessão).
- **O desenho de campos da entrada e dos destinos por perfil** segue
  o mapa de telas já acordado do painel: entrada com e-mail, senha e
  ação Entrar; depois, a casa de cada papel.
- **Limitação honesta (Artigo XV):** esta fatia não torna o hotel
  operável sozinha. Sem as telas seguintes, o turno continua
  dependendo das operações já existentes fora do painel. Não há alta
  disponibilidade, e a sessão longa da equipe continua com a
  contrapartida já aceita: dispositivo perdido mantém acesso até a
  revogação no balcão.
