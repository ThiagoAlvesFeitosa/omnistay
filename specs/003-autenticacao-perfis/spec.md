# Feature Specification: Autenticação e Perfis

**Feature Branch**: `003-autenticacao-perfis`

**Created**: 2026-08-11

**Status**: Draft

**Input**: User description: "Funcionários do hotel acessam o painel com credenciais próprias
e enxergam apenas o que o seu papel permite. A recepção vê reservas, fichas e confirmações de
fase. A equipe operacional vê somente os chamados atribuídos, sem acesso a dados cadastrais de
hóspedes. A gestão vê painéis de consulta, sem poder alterar dados. A equipe operacional acessa
pelo celular e não deve precisar autenticar a cada chamado." (backlog F0.3, acrescido do comando
de bootstrap registrado como lacuna no `00-ESTADO-DO-PROJETO.md`)

## Clarifications

### Session 2026-08-11

- Q: Esta fatia inclui tela de login no painel React? → A: Não. Apenas o comportamento de
  backend — autenticar, manter sessão, autorizar por perfil e revogar. Uma tela de login agora
  levaria a uma tela vazia depois do login, porque não há nada a exibir antes da F1.1: seria
  construir o casco do frontend sem conteúdo e refazê-lo depois.
- Q: Como o token de sessão viaja e onde o cliente o guarda? → A: Em cookie inacessível a script,
  restrito a canal seguro e não enviado em requisição originada de outro site. O frontend nunca
  toca no token, e nada fica em armazenamento acessível a script. Fechado aqui porque é contrato
  entre backend e painel: se ficasse em aberto, a F1.1 herdaria uma escolha feita por acidente.
- Q: Como sustentar sessão longa por dispositivo e revogável, se o esquema da F0.2 tem apenas a
  tabela de usuário? → A: Com registro persistido de sessão por dispositivo, o que permite à
  recepção revogar um dispositivo específico em vez de derrubar todas as sessões do usuário.
  **Isso exige alteração de esquema** — revisão nova de migração e atualização do `04-schema.sql`
  na mesma entrega.
- Q: Quem administra usuários, se o backlog exige que a gestão receba recusa ao alterar dados? →
  A: A gestão cria e desativa usuários — administrar usuário não é dado de domínio. O critério de
  aceite do backlog foi reescrito com precisão: a recusa vale para dado de domínio, isto é,
  reserva, hóspede, solicitação, consumo e avaliação.
- Q: Quem revoga a sessão de um dispositivo perdido? → A: A recepção. Autoridade e urgência são
  coisas diferentes: criar e desativar usuário é autoridade e cabe à gestão; revogar sessão é
  urgência e não pode depender do gerente às três da manhã.
- Q: O primeiro acesso de uma instalação nova vem de onde? → A: De um comando de bootstrap, não
  de tela. Ele cria a propriedade, o usuário inicial de gestão e os parâmetros operacionais com
  valores padrão. Sem ele a fatia é impossível de usar: o painel exige login, usuário exige
  hotel, e nada cria o primeiro hotel.
- Q: Registrar quem criou cada usuário e quando? → A: Não no MVP. Coluna de auditoria de criação
  de usuário é peça a mais sem problema presente que a justifique (Artigo XI).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dar o primeiro acesso a uma instalação nova (Priority: P1)

Como responsável pela instalação, quero levar um sistema recém-migrado ao estado em que existe
uma propriedade cadastrada, um usuário capaz de entrar e os parâmetros operacionais com valores
padrão, para que o painel possa ser usado sem que ninguém precise escrever SQL à mão.

**Why this priority**: É o desbloqueio do impasse registrado no estado do projeto — o painel
exige login, o usuário exige hotel, e nenhuma tela cria o primeiro hotel. Sem esta história,
todas as outras são inalcançáveis fora dos testes.

**Independent Test**: Pode ser testado isoladamente sobre um banco apenas migrado, executando o
comando e verificando que a propriedade, o usuário de gestão e os parâmetros passaram a existir e
que o login com aquela credencial é aceito.

**Acceptance Scenarios**:

1. **Given** um banco migrado e vazio de dados, **When** o comando de bootstrap é executado com
   a senha inicial fornecida pelo ambiente, **Then** passam a existir a propriedade, um usuário
   de perfil de gestão e os parâmetros operacionais com valores padrão.
2. **Given** um sistema que já tem propriedade cadastrada, **When** o comando é executado de
   novo, **Then** nada é criado nem alterado e o motivo é declarado explicitamente.
3. **Given** um ambiente que não fornece a senha inicial, **When** o comando é executado,
   **Then** ele falha com mensagem explícita e não cria usuário nenhum — em nenhuma hipótese
   assume uma senha padrão.

---

### User Story 2 - Entrar no painel e ser barrado sem sessão válida (Priority: P1)

Como funcionário do hotel, quero entrar com credencial própria e permanecer reconhecido nas
requisições seguintes; e, como responsável pelo sistema, quero que todo recurso protegido recuse
quem não tem sessão válida.

**Why this priority**: É o que transforma a API em sistema com acesso controlado. Nenhuma fatia
posterior pode expor dado de hóspede antes disso existir.

**Independent Test**: Pode ser testado isoladamente autenticando com credencial válida, usando a
sessão obtida para alcançar um recurso protegido, e verificando que a mesma requisição sem sessão
é recusada.

**Acceptance Scenarios**:

1. **Given** um usuário ativo com credencial válida, **When** ele se autentica, **Then** a
   sessão é estabelecida em cookie inacessível a script e a requisição seguinte a um recurso
   protegido é aceita.
2. **Given** uma requisição sem sessão, **When** ela alcança um recurso protegido, **Then** é
   recusada sem que nenhum dado seja devolvido.
3. **Given** um e-mail que não existe e um e-mail existente com senha errada, **When** ambos
   tentam autenticar, **Then** as duas recusas são indistinguíveis entre si.
4. **Given** um usuário desativado, **When** ele tenta autenticar com a senha correta, **Then** o
   acesso é recusado.
5. **Given** uma sessão estabelecida, **When** o usuário encerra a sessão, **Then** a sessão
   deixa de ser aceita nas requisições seguintes.

---

### User Story 3 - Cada perfil alcança apenas o que lhe cabe (Priority: P1)

Como responsável pelos dados pessoais dos hóspedes, quero que o perfil de operação não alcance
ficha cadastral e que o perfil de gestão não altere dado de domínio, para que a minimização de
dados deixe de depender de disciplina de uso e passe a ser imposta pelo sistema.

**Why this priority**: É a razão de existirem três perfis. Autenticação sem autorização entrega
porta com chave e nenhuma parede.

**Independent Test**: Pode ser testado isoladamente autenticando com cada perfil e verificando,
para cada um, um caminho permitido e um caminho recusado.

**Acceptance Scenarios**:

1. **Given** uma sessão de perfil de operação, **When** ela tenta ler dado cadastral de hóspede,
   **Then** a leitura é recusada.
2. **Given** uma sessão de perfil de gestão, **When** ela tenta alterar reserva, hóspede,
   solicitação, consumo ou avaliação, **Then** a alteração é recusada.
3. **Given** uma sessão de perfil de gestão, **When** ela cria ou desativa um usuário, **Then** a
   operação é aceita, porque administrar usuário não é dado de domínio.
4. **Given** uma sessão vinculada a uma propriedade, **When** ela tenta alcançar dado de outra
   propriedade, **Then** o acesso é recusado.

---

### User Story 4 - A equipe operacional não reautentica a cada chamado (Priority: P2)

Como profissional de manutenção com as mãos ocupadas, quero continuar reconhecido no meu celular
por um período longo, para não digitar e-mail e senha em navegador de celular cada vez que preciso
marcar um chamado como resolvido.

**Why this priority**: Está registrada como decisão no Artefato 5 §11.2 e é o que evita o pior
desfecho operacional — o profissional resolve o problema, não marca como resolvido, e o hóspede
nunca recebe a confirmação. Depende da história 2 para existir.

**Independent Test**: Pode ser testado isoladamente configurando durações distintas por perfil e
verificando que a sessão de operação continua válida além do prazo das demais.

**Acceptance Scenarios**:

1. **Given** um usuário de perfil de operação autenticado no mesmo dispositivo, **When** o tempo
   avança dentro do período configurado para aquele perfil, **Then** ele continua reconhecido sem
   autenticar de novo.
2. **Given** uma sessão cujo prazo já passou, **When** o cookie ainda é apresentado, **Then** a
   requisição é recusada.
3. **Given** durações diferentes configuradas para os perfis da propriedade, **When** as sessões
   são criadas, **Then** cada uma expira segundo a configuração do seu perfil, e nenhum prazo vem
   de constante no código.

---

### User Story 5 - Cortar o acesso de um dispositivo perdido (Priority: P2)

Como recepcionista de plantão, quero revogar a sessão de um dispositivo específico no momento em
que soube do extravio, para que o acesso cesse imediatamente sem depender de ninguém e sem
derrubar os outros dispositivos da equipe.

**Why this priority**: É a mitigação declarada da contrapartida aceita na decisão de sessão longa.
Sem ela, um celular perdido mantém acesso por semanas.

**Independent Test**: Pode ser testado isoladamente estabelecendo duas sessões do mesmo usuário,
revogando uma e verificando que ela é recusada enquanto a outra continua válida.

**Acceptance Scenarios**:

1. **Given** duas sessões ativas do mesmo usuário em dispositivos diferentes, **When** a recepção
   revoga uma delas, **Then** a revogada é recusada na requisição seguinte e a outra continua
   sendo aceita.
2. **Given** uma sessão já revogada ou já expirada, **When** a recepção tenta revogá-la de novo,
   **Then** nada acontece e nenhum erro é reportado.
3. **Given** uma sessão de outra propriedade, **When** a recepção tenta revogá-la, **Then** a
   operação é recusada.
4. **Given** uma sessão de perfil de operação ou de gestão, **When** ela tenta revogar qualquer
   sessão, **Then** a operação é recusada.

---

### User Story 6 - Cadastrar e desligar funcionários (Priority: P2)

Como gestão do hotel, quero cadastrar os funcionários com o perfil de cada um e desativar quem
deixou a equipe, para que o acesso ao sistema acompanhe a realidade do quadro de pessoal.

**Why this priority**: É o que dá ao bootstrap um caminho de saída — sem esta história, existe um
único usuário e nenhum outro perfil pode ser exercido fora dos testes. Fica em P2 porque a fatia
já entrega valor com o usuário inicial.

**Independent Test**: Pode ser testado isoladamente criando um usuário de cada perfil com uma
sessão de gestão e verificando que cada um autentica; e desativando um usuário com sessão ativa.

**Acceptance Scenarios**:

1. **Given** uma sessão de gestão, **When** um usuário é criado com e-mail, nome, perfil e senha
   inicial, **Then** ele passa a autenticar com aquela credencial.
2. **Given** um e-mail já cadastrado, **When** se tenta criar outro usuário com o mesmo e-mail,
   **Then** a criação é recusada com motivo claro.
3. **Given** um perfil fora dos três previstos, **When** se tenta criar o usuário, **Then** a
   criação é recusada.
4. **Given** um usuário com sessões ativas, **When** ele é desativado, **Then** suas sessões
   deixam de ser aceitas.

---

### Edge Cases

- O que acontece quando o cookie apresentado é forjado ou adulterado? A requisição é recusada
  como qualquer outra sem sessão válida.
- O que acontece quando a sessão existe mas o usuário foi desativado no intervalo? O acesso é
  cortado — a validade da sessão depende do usuário continuar ativo, não apenas do prazo.
- O que acontece quando alguém tenta encerrar sessão sem ter sessão? A operação não produz erro e
  não tem efeito.
- O que acontece se o comando de bootstrap for interrompido no meio? Não resta propriedade sem
  usuário nem usuário sem parâmetros: ou tudo passa a existir, ou nada.
- O que acontece com uma sessão criada antes de uma mudança na duração configurada? A duração é
  fixada no momento da criação da sessão; alterar a configuração afeta as sessões seguintes, não
  as existentes.
- O que acontece se o mesmo usuário autenticar no mesmo dispositivo duas vezes? A segunda
  autenticação cria uma sessão nova, sem invalidar a anterior — que continua revogável
  individualmente.
- Tentativa repetida de adivinhar senha não é contida nesta fatia. É escolha registrada, não
  esquecimento: ver Assumptions.

## Requirements *(mandatory)*

### Functional Requirements

**Autenticação**

- **FR-001**: O sistema DEVE autenticar funcionário por credencial própria, formada por e-mail e
  senha.
- **FR-002**: A senha DEVE ser armazenada exclusivamente como resultado de algoritmo de
  derivação lenta. Em nenhum momento pode existir senha em texto legível no banco, em log, em
  resposta da API ou em arquivo versionado.
- **FR-003**: A recusa por senha errada e a recusa por e-mail inexistente DEVEM ser
  indistinguíveis entre si, para que o sistema não revele quais e-mails estão cadastrados.
- **FR-004**: Usuário desativado NÃO DEVE conseguir autenticar.
- **FR-005**: A autenticação bem-sucedida DEVE criar um registro de sessão vinculado ao usuário e
  ao dispositivo, com instante de criação e instante de expiração.
- **FR-006**: A sessão DEVE viajar em cookie inacessível a script, restrito a canal seguro e não
  enviado em requisição originada de outro site. O cliente NÃO DEVE guardar o identificador de
  sessão em nenhum armazenamento acessível a script.
- **FR-007**: O valor guardado no registro de sessão NÃO DEVE permitir reconstruir o token
  apresentado pelo cliente: vazamento da tabela de sessões não pode equivaler a vazamento de
  acesso.
- **FR-008**: Todo recurso protegido DEVE recusar requisição sem sessão válida, sem devolver
  nenhum dado do domínio.
- **FR-009**: O usuário DEVE poder encerrar a própria sessão, o que a invalida e remove o cookie
  do cliente.

**Duração da sessão**

- **FR-010**: A duração da sessão DEVE vir da configuração da propriedade, por perfil, e NÃO DEVE
  existir prazo fixado em código.
- **FR-011**: O perfil de operação DEVE permanecer reconhecido no mesmo dispositivo por período
  longo, sem reautenticação durante o prazo configurado.
- **FR-012**: Sessão cujo prazo já passou DEVE ser recusada, ainda que o cookie seja apresentado.

**Revogação**

- **FR-013**: O perfil de recepção DEVE poder listar as sessões ativas da própria propriedade,
  identificando usuário, dispositivo e prazo.
- **FR-014**: O perfil de recepção DEVE poder revogar uma sessão específica, e a revogação DEVE
  valer já na requisição seguinte daquela sessão, sem janela de tolerância.
- **FR-015**: Revogar sessão já revogada ou já expirada NÃO DEVE produzir erro nem efeito
  adicional.
- **FR-016**: Revogar uma sessão NÃO DEVE afetar as outras sessões do mesmo usuário.
- **FR-017**: Desativar um usuário DEVE invalidar todas as sessões dele.

**Autorização por perfil**

- **FR-018**: O perfil de operação DEVE receber recusa ao tentar ler dado cadastral de hóspede.
- **FR-019**: O perfil de gestão DEVE receber recusa ao tentar alterar dado de domínio, entendido
  como reserva, hóspede, solicitação, consumo e avaliação.
- **FR-020**: O perfil de gestão DEVE poder criar e desativar usuário, porque administração de
  usuário não é dado de domínio.
- **FR-021**: A revogação de sessão DEVE ser exclusiva do perfil de recepção, e DEVE ser recusada
  aos perfis de operação e de gestão.
- **FR-022**: O e-mail de usuário DEVE ser único, e a segunda criação com o mesmo e-mail DEVE ser
  recusada com motivo claro.
- **FR-023**: A criação de usuário com perfil fora dos três previstos DEVE ser recusada.
- **FR-024**: Toda leitura e toda gravação DEVEM considerar a propriedade do usuário autenticado.
  Sessão de uma propriedade NÃO DEVE alcançar dado de outra.

**Bootstrap**

- **FR-025**: DEVE existir um comando executável, fora do painel, que crie a propriedade inicial,
  o usuário inicial de perfil de gestão e os parâmetros operacionais com valores padrão.
- **FR-026**: O comando NÃO DEVE criar nem alterar nada quando já houver propriedade cadastrada, e
  DEVE declarar explicitamente o motivo de não ter agido.
- **FR-027**: A senha inicial DEVE vir do ambiente de execução ou de entrada interativa. NÃO DEVE
  existir senha padrão embutida, e a senha NÃO DEVE aparecer em log nem em arquivo versionado.
- **FR-028**: Os parâmetros semeados pelo comando DEVEM incluir as durações de sessão por perfil
  exigidas pela FR-010.
- **FR-029**: O comando DEVE ser atômico: uma falha no meio NÃO DEVE deixar propriedade sem
  usuário nem usuário sem parâmetros.

**Registro e esquema**

- **FR-030**: O log NÃO DEVE registrar senha, token de sessão nem cabeçalho de cookie. DEVE
  registrar identificador de usuário, identificador de sessão, perfil, resultado e código de erro.
- **FR-031**: A estrutura de sessão exigida pela FR-005 não existe no esquema atual. A entrega
  DEVE incluir revisão nova de migração e a atualização correspondente do `04-schema.sql`, e o
  teste de conformidade da F0.2 DEVE continuar verde.

### Key Entities

- **Sessão** *(nova)*: vínculo entre um usuário e um dispositivo, com instante de criação, prazo
  de expiração e marca de revogação. Guarda uma forma irreversível do token, nunca o token
  apresentado pelo cliente. É o que torna a sessão revogável por dispositivo.
- **Usuário** *(existente)*: funcionário com nome, e-mail, hash de senha, perfil de recepção,
  operação ou gestão, e indicador de atividade. Não recebe coluna de auditoria de criação neste
  MVP.
- **Parâmetro do hotel** *(existente)*: passa a guardar as durações de sessão por perfil.
- **Hotel** *(existente)*: propriedade criada pelo comando de bootstrap; raiz do particionamento.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma instalação recém-migrada chega ao primeiro login bem-sucedido por um único
  comando, sem nenhum passo manual no banco.
- **SC-002**: 100% dos recursos protegidos recusam requisição sem sessão válida, comprovado por
  teste automatizado.
- **SC-003**: Nenhum caminho exposto permite ao perfil de operação obter dado cadastral de
  hóspede.
- **SC-004**: Nenhum caminho exposto permite ao perfil de gestão alterar reserva, hóspede,
  solicitação, consumo ou avaliação.
- **SC-005**: A revogação de uma sessão passa a valer na requisição imediatamente seguinte, sem
  janela de tolerância, e não afeta as outras sessões do mesmo usuário.
- **SC-006**: Um usuário de perfil de operação atravessa todo o período configurado sem
  reautenticar nenhuma vez.
- **SC-007**: Nenhuma senha e nenhum token de sessão são recuperáveis a partir do banco, do log
  ou de resposta da API — verificável por inspeção e por teste.
- **SC-008**: Nenhum prazo de sessão está fixado em código: alterar a configuração da propriedade
  altera o comportamento sem tocar o código.
- **SC-009**: Cada critério de aceite da fatia F0.3 do backlog tem ao menos um teste automatizado
  correspondente, e a suíte inteira fica verde.
- **SC-010**: O banco e o `04-schema.sql` continuam idênticos após a nova migração, comprovado
  pelo teste de conformidade já existente.

## Assumptions

- **Só backend nesta fatia.** Login, sessão, autorização, revogação e administração de usuários
  são comportamento de API. O painel React entra a partir da F1.1, quando houver tela com
  conteúdo para exibir depois do login.
- **A API e o painel compartilham origem.** É o que permite que o cookie restrito a requisições
  do próprio site dispense proteção adicional contra requisição forjada de outro site. Se em
  algum momento o painel passar a ser servido de outra origem, esta premissa precisa ser
  revisitada.
- **Contenção de tentativa repetida de senha fica fora desta fatia.** Escolha registrada, não
  esquecimento: hoje a hospedagem é local com túnel e o painel não está publicado na internet.
  Antes de qualquer exposição contínua, a contenção precisa entrar — e é onde o efeito da sessão
  longa amplifica a consequência.
- **Redefinição e troca de senha ficam fora desta fatia.** O caminho existente é a gestão
  desativar o usuário e criar outro. Assim como acontece com os valores de `parametro_hotel`,
  isso é limitação aceita do MVP e está registrada para não ser confundida com lacuna.
- **A listagem de sessões não registra último uso.** Atualizar um instante de uso a cada
  requisição custa uma escrita por leitura, e a decisão de revogar se sustenta com usuário,
  dispositivo e prazo (Artigo XI).
- **Os valores padrão dos parâmetros de duração são semeados pelo bootstrap** e alterados por
  SQL no MVP, coerente com a escolha já registrada para os demais parâmetros da propriedade.
- **O `00-ESTADO-DO-PROJETO.md` e a F0.3 do backlog precisam de correção nesta entrega**: o
  critério "alterar qualquer dado" era ambíguo o bastante para tornar impossível a administração
  de usuários, e foi reescrito para "dado de domínio", com a lista explícita.
- **Sessão longa é decisão com contrapartida aceita**, registrada no Artefato 5 §11.2: um
  dispositivo perdido mantém acesso até a revogação. A mitigação é a soma de duas coisas — o
  perfil de operação nunca alcança dado cadastral de hóspede, e a recepção revoga sem depender
  da gestão.
