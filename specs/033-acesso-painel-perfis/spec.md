# Feature Specification: Acesso ao painel por perfil

**Feature Branch**: `033-acesso-painel-perfis`

**Created**: 2026-09-01

**Status**: Draft

**Input**: User description: "Funcionários do hotel acessam o painel com
credenciais próprias e enxergam apenas o que o seu papel permite."
(backlog F0.3 — o texto completo da fatia acrescenta: a recepção vê
reservas, fichas e confirmações de fase; a equipe operacional vê
somente os chamados atribuídos, sem acesso a dados cadastrais de
hóspedes; a gestão vê painéis de consulta, sem poder alterar dados de
domínio; a equipe operacional acessa pelo celular e não deve
precisar autenticar a cada chamado.)

Restrições já decididas no projeto (entrada do specify): o sistema
**não** se integra ao sistema de gestão do hotel; há exatamente três
papéis — recepção, equipe operacional e gestão; senha nunca aparece
em texto legível; conteúdo de mensagem nunca vai para log; toda
consulta de domínio considera a propriedade do funcionário, mesmo
com uma única casa cadastrada; prazo de sessão vem da configuração
da propriedade, por perfil, nunca de constante; administrar usuário
não é dado de domínio — a gestão cria e desativa funcionários; a
recepção revoga sessão de dispositivo, porque urgência não pode
depender do gerente de madrugada; a equipe operacional permanece
reconhecida no mesmo aparelho por período longo, com a
contrapartida aceita de que um aparelho perdido mantém acesso até a
revogação. A tela de entrada, o menu e o destino inicial de cada
papel são da casca do painel (F8.1) — esta fatia é o contrato de
quem entra, quanto permanece reconhecido e o que cada papel pode
alcançar.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dar o primeiro acesso a uma instalação nova (Priority: P1)

Como responsável pela instalação, quero levar um sistema recém-preparado
ao estado em que existe uma propriedade, um usuário capaz de entrar e os
parâmetros operacionais com valores padrão, para que o painel possa ser
usado sem que ninguém precise gravar dados à mão no banco.

**Why this priority**: Sem o primeiro hotel e o primeiro usuário de
gestão, ninguém autentica. O painel exige credencial, a credencial
exige propriedade, e nada cria o primeiro hotel. Sem esta história,
as demais são inalcançáveis fora dos testes.

**Independent Test**: Pode ser testado sobre uma instalação só com o
esquema aplicado, executando o comando de instalação e conferindo que
a propriedade, o usuário de gestão e os parâmetros passaram a existir
e que o login com aquela credencial é aceito.

**Acceptance Scenarios**:

1. **Given** uma instalação sem propriedade cadastrada, **When** o
   comando de instalação é executado com a senha inicial fornecida
   pelo ambiente, **Then** passam a existir a propriedade, um usuário
   de perfil de gestão e os parâmetros operacionais com valores
   padrão — inclusive as durações de sessão por perfil.
2. **Given** um sistema que já tem propriedade cadastrada, **When** o
   comando é executado de novo, **Then** nada é criado nem alterado e
   o motivo é declarado explicitamente.
3. **Given** um ambiente que não fornece a senha inicial, **When** o
   comando é executado, **Then** ele falha com mensagem explícita e
   não cria usuário nenhum — em nenhuma hipótese assume uma senha
   padrão.

---

### User Story 2 - Entrar com credencial própria e ser barrado sem ela (Priority: P1)

Como funcionário do hotel, quero entrar com o e-mail e a senha que me
foram dados e permanecer reconhecido nas ações seguintes; e, como
responsável pelos dados da casa, quero que qualquer recurso protegido
recuse quem não tem sessão válida, sem devolver dado nenhum.

**Why this priority**: É o que transforma o painel em sistema com
acesso controlado. Nenhuma tela posterior pode expor dado de hóspede
antes disso existir.

**Independent Test**: Pode ser testado autenticando com credencial
válida, usando a sessão obtida para alcançar um recurso protegido, e
conferindo que a mesma ação sem sessão é recusada.

**Acceptance Scenarios**:

1. **Given** um funcionário ativo com credencial válida, **When** ele
   se autentica, **Then** a sessão é estabelecida naquele dispositivo
   e a ação seguinte a um recurso protegido é aceita.
2. **Given** uma ação sem sessão, **When** ela alcança um recurso
   protegido, **Then** é recusada sem que nenhum dado seja devolvido.
3. **Given** um e-mail que não existe e um e-mail existente com senha
   errada, **When** ambos tentam autenticar, **Then** as duas recusas
   são indistinguíveis entre si.
4. **Given** um usuário desativado, **When** ele tenta autenticar com
   a senha correta, **Then** o acesso é recusado da mesma forma, sem
   mensagem especial de desativação.
5. **Given** uma sessão estabelecida, **When** o funcionário encerra
   a sessão, **Then** ela deixa de ser aceita nas ações seguintes.

---

### User Story 3 - Cada perfil alcança apenas o que lhe cabe (Priority: P1)

Como responsável pelos dados pessoais dos hóspedes, quero que a equipe
operacional não alcance ficha cadastral, que a gestão não altere dado
de domínio e que a recepção opere reservas, fichas e confirmações de
fase, para que a minimização de dados deixe de depender de disciplina
de uso e passe a ser imposta pelo sistema.

**Why this priority**: É a razão de existirem três papéis.
Autenticação sem autorização entrega porta com chave e nenhuma parede.
É o sentido da frase “enxergam apenas o que o seu papel permite”.

**Independent Test**: Pode ser testado autenticando com cada perfil e
verificando, para cada um, um caminho permitido e um caminho recusado.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção, **When** ela lê reserva, ficha
   ou confirma fase (chegada ou saída), **Then** a operação é aceita
   na própria propriedade.
2. **Given** uma sessão de equipe operacional, **When** ela tenta ler
   dado cadastral de hóspede (nome, telefone, documento ou ficha),
   **Then** a leitura é recusada.
3. **Given** uma sessão de equipe operacional, **When** ela lê os
   chamados atribuídos à operação, **Then** a leitura é aceita e
   nenhum campo cadastral de hóspede aparece.
4. **Given** uma sessão de gestão, **When** ela consulta painéis
   agregados (indicadores, mercado, retenção), **Then** a consulta é
   aceita.
5. **Given** uma sessão de gestão, **When** ela tenta alterar reserva,
   hóspede, solicitação, consumo ou avaliação, **Then** a alteração é
   recusada.
6. **Given** uma sessão de gestão, **When** ela cria ou desativa um
   usuário, **Then** a operação é aceita, porque administrar usuário
   não é dado de domínio.
7. **Given** uma sessão vinculada a uma propriedade, **When** ela
   tenta alcançar dado de outra propriedade, **Then** o acesso é
   recusado.

---

### User Story 4 - A equipe operacional não reautentica a cada chamado (Priority: P2)

Como profissional de manutenção com as mãos ocupadas, quero continuar
reconhecido no meu celular por um período longo, para não digitar
e-mail e senha cada vez que preciso marcar um chamado como resolvido.

**Why this priority**: Se o acesso for trabalhoso, o profissional
resolve o problema e não marca como resolvido — e o hóspede nunca
recebe a confirmação. Depende da história 2 para existir.

**Independent Test**: Pode ser testado configurando durações distintas
por perfil e verificando que a sessão da equipe operacional continua
válida além do prazo das demais.

**Acceptance Scenarios**:

1. **Given** um usuário de perfil operacional autenticado no mesmo
   dispositivo, **When** o tempo avança dentro do período configurado
   para aquele perfil, **Then** ele continua reconhecido sem
   autenticar de novo.
2. **Given** uma sessão cujo prazo já passou, **When** o identificador
   ainda é apresentado, **Then** a ação é recusada.
3. **Given** durações diferentes configuradas para os perfis da
   propriedade, **When** as sessões são criadas, **Then** cada uma
   expira segundo a configuração do seu perfil, e nenhum prazo vem de
   constante no código.

---

### User Story 5 - Cortar o acesso de um dispositivo perdido (Priority: P2)

Como recepcionista de plantão, quero revogar a sessão de um dispositivo
específico no momento em que soube do extravio, para que o acesso cesse
imediatamente sem depender de ninguém e sem derrubar os outros
dispositivos da equipe.

**Why this priority**: É a mitigação da contrapartida aceita na sessão
longa. Sem ela, um celular perdido mantém acesso por semanas.

**Independent Test**: Pode ser testado estabelecendo duas sessões do
mesmo usuário, revogando uma e conferindo que ela é recusada enquanto
a outra continua válida.

**Acceptance Scenarios**:

1. **Given** duas sessões ativas do mesmo usuário em dispositivos
   diferentes, **When** a recepção revoga uma delas, **Then** a
   revogada é recusada na ação seguinte e a outra continua sendo
   aceita.
2. **Given** uma sessão já revogada ou já expirada, **When** a
   recepção tenta revogá-la de novo, **Then** nada acontece e nenhum
   erro é reportado.
3. **Given** uma sessão de outra propriedade, **When** a recepção
   tenta revogá-la, **Then** a operação é recusada.
4. **Given** uma sessão de perfil operacional ou de gestão, **When**
   ela tenta revogar qualquer sessão, **Then** a operação é recusada.

---

### User Story 6 - Cadastrar e desligar funcionários (Priority: P2)

Como gestão do hotel, quero cadastrar os funcionários com o perfil de
cada um e desativar quem deixou a equipe, para que o acesso ao sistema
acompanhe a realidade do quadro de pessoal.

**Why this priority**: É o que dá ao comando de instalação um caminho
de saída — sem esta história, existe um único usuário e nenhum outro
perfil pode ser exercido fora dos testes. Fica em P2 porque a fatia já
entrega valor com o usuário inicial.

**Independent Test**: Pode ser testado criando um usuário de cada
perfil com uma sessão de gestão e conferindo que cada um autentica; e
desativando um usuário com sessão ativa.

**Acceptance Scenarios**:

1. **Given** uma sessão de gestão, **When** um usuário é criado com
   e-mail, nome, perfil e senha inicial, **Then** ele passa a
   autenticar com aquela credencial.
2. **Given** um e-mail já cadastrado, **When** se tenta criar outro
   usuário com o mesmo e-mail, **Then** a criação é recusada com
   motivo claro.
3. **Given** um perfil fora dos três previstos, **When** se tenta
   criar o usuário, **Then** a criação é recusada.
4. **Given** um usuário com sessões ativas, **When** ele é desativado,
   **Then** suas sessões deixam de ser aceitas.

---

### Edge Cases

- Identificador de sessão forjado ou adulterado: a ação é recusada
  como qualquer outra sem sessão válida.
- A sessão existe mas o usuário foi desativado no intervalo: o acesso
  é cortado — a validade depende do usuário continuar ativo, não
  apenas do prazo.
- Encerrar sessão sem ter sessão: a operação não produz erro e não
  tem efeito.
- Comando de instalação interrompido no meio: não resta propriedade
  sem usuário nem usuário sem parâmetros — ou tudo passa a existir,
  ou nada.
- Sessão criada antes de uma mudança na duração configurada: a
  duração é fixada no momento da criação; alterar a configuração
  afeta as sessões seguintes, não as existentes.
- O mesmo usuário autentica no mesmo dispositivo duas vezes: a
  segunda autenticação cria uma sessão nova, sem invalidar a
  anterior — que continua revogável individualmente.
- Tentativa repetida de adivinhar senha não é contida nesta fatia.
  É escolha registrada, não esquecimento: ver Assumptions.

## Requirements *(mandatory)*

### Functional Requirements

**Autenticação**

- **FR-001**: O sistema DEVE autenticar funcionário por credencial
  própria, formada por e-mail e senha.
- **FR-002**: A senha DEVE ser armazenada exclusivamente como
  resultado de derivação lenta. Em nenhum momento pode existir senha
  em texto legível no banco, em log, em resposta ao cliente ou em
  arquivo versionado.
- **FR-003**: A recusa por senha errada e a recusa por e-mail
  inexistente DEVEM ser indistinguíveis entre si, para que o sistema
  não revele quais e-mails estão cadastrados.
- **FR-004**: Usuário desativado NÃO DEVE conseguir autenticar.
- **FR-005**: A autenticação bem-sucedida DEVE criar um registro de
  sessão vinculado ao usuário e ao dispositivo, com instante de
  criação e instante de expiração.
- **FR-006**: O identificador de sessão NÃO DEVE ser acessível a
  script no navegador, NÃO DEVE viajar em canal inseguro quando o
  acesso for seguro, e NÃO DEVE acompanhar pedido originado de outro
  site. O cliente NÃO DEVE guardar o identificador em armazenamento
  acessível a script.
- **FR-007**: O valor guardado no registro de sessão NÃO DEVE
  permitir reconstruir o identificador apresentado pelo cliente:
  vazamento dos registros de sessão não pode equivaler a vazamento de
  acesso.
- **FR-008**: Todo recurso protegido DEVE recusar ação sem sessão
  válida, sem devolver nenhum dado do domínio.
- **FR-009**: O usuário DEVE poder encerrar a própria sessão, o que
  a invalida no servidor e a remove do dispositivo.

**Duração da sessão**

- **FR-010**: A duração da sessão DEVE vir da configuração da
  propriedade, por perfil, e NÃO DEVE existir prazo fixado em código.
- **FR-011**: O perfil operacional DEVE permanecer reconhecido no
  mesmo dispositivo por período longo, sem reautenticação durante o
  prazo configurado.
- **FR-012**: Sessão cujo prazo já passou DEVE ser recusada, ainda
  que o identificador seja apresentado.

**Revogação**

- **FR-013**: O perfil de recepção DEVE poder listar as sessões
  ativas da própria propriedade, identificando usuário, dispositivo
  e prazo.
- **FR-014**: O perfil de recepção DEVE poder revogar uma sessão
  específica, e a revogação DEVE valer já na ação seguinte daquela
  sessão, sem janela de tolerância.
- **FR-015**: Revogar sessão já revogada ou já expirada NÃO DEVE
  produzir erro nem efeito adicional.
- **FR-016**: Revogar uma sessão NÃO DEVE afetar as outras sessões
  do mesmo usuário.
- **FR-017**: Desativar um usuário DEVE invalidar todas as sessões
  dele.

**Autorização por perfil**

- **FR-018**: O perfil de recepção DEVE poder ler reserva e ficha e
  confirmar fase (chegada e saída) da própria propriedade.
- **FR-019**: O perfil operacional DEVE receber recusa ao tentar ler
  dado cadastral de hóspede.
- **FR-020**: O perfil operacional DEVE poder ler os chamados
  atribuídos à operação, sem receber campo cadastral de hóspede.
- **FR-021**: O perfil de gestão DEVE poder consultar painéis
  agregados e DEVE receber recusa ao tentar alterar dado de domínio,
  entendido como reserva, hóspede, solicitação, consumo e avaliação.
- **FR-022**: O perfil de gestão DEVE poder criar e desativar
  usuário, porque administração de usuário não é dado de domínio.
- **FR-023**: A revogação de sessão DEVE ser exclusiva do perfil de
  recepção, e DEVE ser recusada aos perfis operacional e de gestão.
- **FR-024**: O e-mail de usuário DEVE ser único, e a segunda
  criação com o mesmo e-mail DEVE ser recusada com motivo claro.
- **FR-025**: A criação de usuário com perfil fora dos três previstos
  DEVE ser recusada.
- **FR-026**: Toda leitura e toda gravação DEVEM considerar a
  propriedade do usuário autenticado. Sessão de uma propriedade NÃO
  DEVE alcançar dado de outra.

**Instalação inicial**

- **FR-027**: DEVE existir um comando executável, fora do painel, que
  crie a propriedade inicial, o usuário inicial de perfil de gestão
  e os parâmetros operacionais com valores padrão.
- **FR-028**: O comando NÃO DEVE criar nem alterar nada quando já
  houver propriedade cadastrada, e DEVE declarar explicitamente o
  motivo de não ter agido.
- **FR-029**: A senha inicial DEVE vir do ambiente de execução ou de
  entrada interativa. NÃO DEVE existir senha padrão embutida, e a
  senha NÃO DEVE aparecer em log nem em arquivo versionado.
- **FR-030**: Os parâmetros semeados pelo comando DEVEM incluir as
  durações de sessão por perfil exigidas pela FR-010.
- **FR-031**: O comando DEVE ser atômico: uma falha no meio NÃO DEVE
  deixar propriedade sem usuário nem usuário sem parâmetros.

**Registro**

- **FR-032**: O log NÃO DEVE registrar senha, identificador de sessão
  apresentado ao cliente nem conteúdo de mensagem. DEVE registrar
  identificador de usuário, identificador interno de sessão, perfil,
  resultado e código de erro.

**Fora desta fatia**

- **FR-033**: Esta fatia NÃO DEVE construir a tela de entrada, o menu
  por perfil nem o destino inicial visível (casca do painel, F8.1).
  NÃO DEVE cadastrar reserva, confirmar fase pela tela, editar ficha,
  resolver chamado, lançar consumo, alterar catálogo nem consultar
  mercado pela tela. NÃO DEVE integrar-se ao sistema de gestão do
  hotel.

### Key Entities

- **Sessão**: vínculo entre um usuário e um dispositivo, com instante
  de criação, prazo de expiração e marca de revogação. Guarda uma
  forma irreversível do identificador, nunca o valor apresentado pelo
  cliente. É o que torna a sessão revogável por dispositivo.
- **Usuário**: funcionário com nome, e-mail, senha derivada, um dos
  três perfis (recepção, operação ou gestão) e indicador de
  atividade. Não recebe registro de auditoria de criação neste
  recorte.
- **Parâmetro do hotel**: guarda as durações de sessão por perfil,
  além dos demais prazos operacionais da propriedade.
- **Hotel**: propriedade criada pelo comando de instalação; raiz do
  particionamento. Toda sessão e todo usuário pertencem a um hotel.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma instalação recém-preparada chega ao primeiro login
  bem-sucedido por um único comando, sem nenhum passo manual no banco.
- **SC-002**: 100% dos recursos protegidos recusam ação sem sessão
  válida, comprovado por teste automatizado.
- **SC-003**: Nenhum caminho exposto permite ao perfil operacional
  obter dado cadastral de hóspede.
- **SC-004**: Nenhum caminho exposto permite ao perfil de gestão
  alterar reserva, hóspede, solicitação, consumo ou avaliação.
- **SC-005**: A revogação de uma sessão passa a valer na ação
  imediatamente seguinte, sem janela de tolerância, e não afeta as
  outras sessões do mesmo usuário.
- **SC-006**: Um usuário de perfil operacional atravessa todo o
  período configurado sem reautenticar nenhuma vez.
- **SC-007**: Nenhuma senha e nenhum identificador de sessão
  apresentado ao cliente são recuperáveis a partir do banco, do log
  ou de resposta ao cliente — verificável por inspeção e por teste.
- **SC-008**: Nenhum prazo de sessão está fixado em código: alterar a
  configuração da propriedade altera o comportamento sem tocar o
  código.
- **SC-009**: Cada critério de aceite da fatia F0.3 do backlog tem ao
  menos um teste automatizado correspondente, e a suíte inteira fica
  verde.

## Assumptions

- **Esta fatia é o contrato de acesso, não a casca visível.** Login,
  sessão, autorização, revogação, administração de usuários e o
  comando de instalação são o recorte. A tela de entrada, o menu e o
  destino inicial de cada papel já foram especificados na F8.1.
- **O painel e o servidor compartilham origem.** É o que permite que
  o identificador de sessão, restrito a pedidos do próprio site,
  dispense proteção adicional contra pedido forjado de outro site. Se
  o painel passar a ser servido de outra origem, esta premissa
  precisa ser revisitada.
- **Contenção de tentativa repetida de senha fica fora desta fatia.**
  Escolha registrada, não esquecimento: hoje a hospedagem é local e o
  painel não está publicado na internet. Antes de qualquer exposição
  contínua, a contenção precisa entrar — e é onde o efeito da sessão
  longa amplifica a consequência.
- **Redefinição e troca de senha ficam fora desta fatia.** O caminho
  existente é a gestão desativar o usuário e criar outro. Limitação
  aceita do recorte, registrada para não ser confundida com lacuna.
- **A listagem de sessões não registra último uso.** Atualizar um
  instante de uso a cada ação custa uma escrita por leitura, e a
  decisão de revogar se sustenta com usuário, dispositivo e prazo.
- **Os valores padrão das durações são semeados pelo comando de
  instalação** e, no recorte atual, alterados pela configuração da
  propriedade — não por constante no código.
- **Sessão longa é decisão com contrapartida aceita**: um dispositivo
  perdido mantém acesso até a revogação. A mitigação é a soma de duas
  coisas — o perfil operacional nunca alcança dado cadastral de
  hóspede, e a recepção revoga sem depender da gestão.
- **Relação com a spec já existente.** O mesmo comportamento foi
  especificado em `specs/003-autenticacao-perfis` e está marcado como
  concluído no estado do projeto. Esta spec reitera o contrato F0.3
  a partir do texto colado no `/specify`. Planejar ou implementar de
  novo só se justifica se o recorte for reaberto de propósito; o
  próximo passo natural do backlog operacional restante é a F8.6
  (catálogo, itens vendáveis e recado de boas-vindas no painel).
