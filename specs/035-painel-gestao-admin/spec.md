# Feature Specification: Painel da gestão, mercado e administração

**Feature Branch**: `035-painel-gestao-admin`

**Created**: 2026-09-01

**Status**: Draft

**Input**: User description: "A gestão vê indicadores agregados da
operação, o comparativo de mercado com os concorrentes cadastrados,
a relação de usuários com criação e desativação, e o registro das
execuções de expurgo por retenção. Nenhum dado cadastral de hóspede
aparece em nenhuma dessas telas."
(backlog F8.7)

Restrições já decididas no projeto (entrada do specify): esta fatia
**não altera o comportamento já entregue fora das telas** — contagem
sem lista nominada, painel de mercado somente leitura da série
coletada, cadastro de concorrente sem apagar, criar e desativar
usuário, desativar sem apagar, comprovante de retenção com data,
tipo e quantidade **já existem** (F1.1, F5.1, F5.3, F0.3, F6.1); a
casca já nomeia **Painel**, **Mercado**, **Usuários** e **Retenção
de dados** só para a gestão (F8.1), hoje só com título; a gestão
consulta dado de domínio e não o altera; administrar usuário não é
dado de domínio; revogar sessão é da recepção, não da gestão; a
equipe operacional não vê dado cadastral de hóspede; senha nunca
aparece em texto legível; conteúdo de mensagem nunca vai para log;
toda consulta considera a propriedade do funcionário; só a tela da
equipe é pensada para celular — estas quatro são de computador; o
que a autorização recusa, a tela não oferece; o sistema **não** se
integra ao sistema de gestão do hotel e **não** mostra a tarifa da
própria casa. Módulos por propriedade, canal de e-mail e
personalidade da assistente permanecem fora. Configurações da
propriedade (ligar e desligar módulo) permanecem fora.

## Clarifications

### Session 2026-09-02

- Q: Which aggregated numbers should the management Panel show in this slice? → A: Four operational numbers: arrivals today, currently staying, open tickets, consumption still to post. Advance-registration rate and 30-day average score stay out.
- Q: How should currently staying, open tickets, and consumption still to post be counted? → A: Staying = in house now. Open tickets = unresolved complaints and service only. Consumption still to post = money total of items waiting to be posted.
- Q: Should Mercado in this slice only show the comparison, or also let gestão add and adjust who the house tracks? → A: Comparison only: dated prices and notes, failed collection marked, history. Adding or editing competitors stays outside this slice.
- Q: After gestão deactivates a staff account, should this screen also let them turn that same account back on? → A: Deactivate only. Deactivated people stay on the list. No reactivate. Returning to work means a new account (and a different email).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver números da operação, nunca pessoas (Priority: P1)

Como gestão na sala, quero abrir **Painel** e ver contagens da
operação de agora — chegadas de hoje, hospedados no momento,
chamados em aberto e consumo ainda a lançar — sem nome, telefone,
documento nem lista de hóspedes, para dimensionar equipe sem virar
recepção.

**Why this priority**: É o destino inicial da gestão e o primeiro
critério de aceite da fatia. Número agregado serve; lista nominada
na gestão quebraria a minimização.

**Independent Test**: Pode ser testado autenticando como gestão numa
propriedade com movimento conhecido, abrindo Painel, conferindo que
cada indicador é um número (quantidade ou valor em dinheiro) e que a tela
não apresenta nome de hóspede, telefone, documento, quarto nem
identificador de reserva; autenticando recepção e equipe e
confirmando que este destino não aparece para eles.

**Acceptance Scenarios**:

1. **Given** uma sessão de gestão e movimento na própria
   propriedade, **When** a pessoa abre Painel, **Then** vê os
   quatro indicadores agregados: chegadas de hoje, hospedados no
   momento (reservas em casa agora), chamados em aberto
   (reclamações e pedidos de serviço ainda não resolvidos, sem
   consumo faturável) e consumo ainda a lançar (soma em dinheiro
   do que espera lançamento) — cada um como número, sem lista por
   baixo. Não vê proporção de fichas antecipadas nem nota média.
2. **Given** o mesmo Painel, **When** a gestão inspeciona o que a
   tela mostra, **Then** não há nome, telefone, documento, data de
   nascimento, endereço nem qualquer outro campo da ficha de
   hóspede, nem linha nominada de reserva, chamado ou consumo.
3. **Given** um hotel sem movimento no recorte (zero chegadas, zero
   hospedados, zero chamados, zero consumo a lançar), **When** a
   gestão abre Painel, **Then** os números aparecem como zero —
   distinto de falha ao ler.
4. **Given** esta tela, **When** a gestão procura alterar reserva,
   hóspede, chamado, consumo ou avaliação, **Then** a tela não
   oferece esse caminho.

---

### User Story 2 - Comparar o mercado com falha visível (Priority: P1)

Como gestão, quero abrir **Mercado** e ver, de uma vez, o preço e a
nota mais recentes de cada concorrente que a casa acompanha — cada
número com a data da coleta — e quero que coleta falhada apareça
marcada, sem o número antigo se passar por dado de agora, para
decidir tarifa sem abrir site na mão e sem tratar falha como preço
atual.

**Why this priority**: Critério de aceite explícito da fatia. Dado
velho apresentado como atual é pior do que ausência.

**Independent Test**: Pode ser testado autenticando como gestão numa
propriedade com concorrentes em situações distintas (sucesso
recente, sucesso antigo, falha depois de sucesso, só falha, ainda
nunca coletado), abrindo Mercado e conferindo nome, valores datados,
marca de falha ou de desatualizado, e ausência da tarifa da própria
casa.

**Acceptance Scenarios**:

1. **Given** uma sessão de gestão e concorrentes cadastrados com ao
   menos uma coleta bem-sucedida, **When** a pessoa abre Mercado,
   **Then** cada concorrente da própria casa aparece com o nome e
   com o preço e/ou a nota da última coleta bem-sucedida, e **cada**
   valor traz a data daquela coleta.
2. **Given** um concorrente cuja tentativa mais recente falhou,
   havendo sucesso anterior, **When** a gestão olha a linha,
   **Then** a falha está marcada de forma distinguível; o valor
   exibido, se houver, continua sendo o do sucesso, com a data
   antiga — não redatado, não zerado, não apresentado como atual.
3. **Given** um concorrente só com falhas, ou ainda nunca coletado,
   **When** a gestão olha a linha, **Then** não aparece preço nem
   nota como valor encontrado; a situação (falha ou ausência de
   coleta) é explícita; nenhum zero é inventado.
4. **Given** esta tela, **When** a gestão procura a tarifa da
   própria casa na comparação, **Then** essa linha não existe — o
   sistema não consulta o outro sistema do hotel e não inventa o
   preço próprio.
5. **Given** esta tela, **When** a gestão procura corrigir, apagar
   ou “atualizar na mão” um preço ou nota coletados, **Then** o
   caminho não é oferecido.
6. **Given** esta tela, **When** a gestão procura cadastrar,
   corrigir, desativar ou reativar um concorrente, **Then** o
   caminho não é oferecido — a manutenção de quem acompanhar
   permanece fora desta fatia.

---

### User Story 3 - Cadastrar e desligar funcionários, sem apagar (Priority: P1)

Como gestão, quero abrir **Usuários**, ver quem tem acesso à casa,
criar funcionário com nome, e-mail, um dos três perfis e senha no
mínimo exigido, e desativar quem saiu da equipe — sem apagar o
registro e sem revogar sessão nesta tela — para o quadro de pessoal
acompanhar a realidade sem a gestão herdar urgência de dispositivo
perdido.

**Why this priority**: Critérios de aceite explícitos: criar exige
perfil e senha com o mínimo; desativar não apaga; revogar sessão
não aparece para a gestão.

**Independent Test**: Pode ser testado autenticando como gestão,
vendo ativos e desativados, criando um usuário de cada perfil com
senha no mínimo, tentando senha curta e e-mail repetido (recusa na
hora), desativando outro funcionário (permanece na lista marcado),
tentando desativar a si mesmo (recusa), conferindo que não há
reativar nem revogar sessão, e tentando criar de novo com o
e-mail de um desativado (recusa).

**Acceptance Scenarios**:

1. **Given** uma sessão de gestão, **When** a pessoa abre Usuários,
   **Then** vê os funcionários da própria propriedade — ativos e
   desativados — cada um com nome, e-mail, perfil e situação
   distinguível, sem senha visível.
2. **Given** nome, e-mail ainda não usado, um dos três perfis
   (recepção, equipe operacional ou gestão) e senha com ao menos o
   mínimo exigido, **When** a gestão confirma a criação, **Then** o
   novo usuário nasce ativo, aparece na lista e passa a autenticar
   com aquela credencial.
3. **Given** senha abaixo do mínimo, e-mail já cadastrado, perfil
   fora dos três ou campo obrigatório em branco, **When** a gestão
   tenta criar, **Then** a criação é recusada na hora, nesta tela,
   com aviso claro; nenhum usuário novo entra.
4. **Given** um usuário ativo que não é a própria sessão, **When** a
   gestão o desativa, **Then** ele permanece na lista marcado como
   desativado; a tela não oferece apagar; as sessões daquela pessoa
   deixam de ser aceitas.
5. **Given** a própria linha da gestão autenticada, **When** ela
   procura desativar a si mesma, **Then** o controle não é
   oferecido — ou a tentativa é recusada — e a sessão continua.
6. **Given** esta tela, **When** a gestão procura revogar sessão de
   um dispositivo, **Then** o controle não existe. Revogar sessão
   continua sendo da recepção, em outro lugar.
7. **Given** um usuário desativado, **When** a gestão procura
   reativá-lo, **Then** o controle não existe. Para voltar a ter
   acesso, é preciso criar um usuário novo, com outro e-mail — o
   e-mail do desativado continua ocupado.

---

### User Story 4 - Mostrar que o expurgo aconteceu (Priority: P1)

Como gestão responsável pelos dados da casa, quero abrir **Retenção
de dados** e ver quando a passagem rodou, o que foi tratado e
quantos registros de cada tipo — sem o texto pessoal — para
conseguir demonstrar cumprimento numa fiscalização ou numa banca,
em vez de dizer só que “o sistema faz”.

**Why this priority**: Critério de aceite explícito. Sem esta tela,
o comprovante existe e a gestão continua saindo para consultá-lo
fora do painel.

**Independent Test**: Pode ser testado autenticando como gestão
depois de passagens com quantidades conhecidas (incluindo uma
passagem com zeros), abrindo Retenção de dados e conferindo data,
tipo e quantidade, ausência de nome de hóspede e ausência de botão
para disparar expurgo agora.

**Acceptance Scenarios**:

1. **Given** uma sessão de gestão e ao menos uma passagem já
   registrada na propriedade, **When** a pessoa abre Retenção de
   dados, **Then** vê cada execução com data e hora, os tipos
   tratados (conteúdo livre anonimizado e fichas apagadas, nas
   quantidades de cada espécie) e a quantidade de registros —
   inclusive quando a quantidade é zero.
2. **Given** a política da casa, **When** a gestão olha o topo da
   tela, **Then** vê os prazos vigentes — ficha após a saída e
   conversas — como informação, sem poder alterá-los nesta tela.
3. **Given** esta tela, **When** a gestão procura um nome, telefone,
   documento, mensagem ou comentário de hóspede, **Then** nada
   disso aparece — só instante, tipo e quantidade.
4. **Given** esta tela, **When** a gestão procura disparar o
   expurgo agora, **Then** o controle não existe. A passagem
   continua automática.

---

### User Story 5 - Só a gestão chega; os outros perfis nem vêem o menu (Priority: P1)

Como responsável pelos dados da propriedade, quero que recepção e
equipe operacional sejam recusadas nestes quatro destinos — sem
número, sem concorrente, sem lista de funcionários, sem
comprovante e sem tela em branco — e que nenhuma destas telas
carregue ficha de hóspede, para a minimização valer também no
painel da gestão.

**Why this priority**: Fecha o enunciado da fatia e o critério de
que lista nominada de hóspede não é servida à gestão. Tela que
oferece o que a autorização recusa ensina o caminho errado.

**Independent Test**: Pode ser testado autenticando recepção e
equipe, conferindo ausência dos quatro destinos no menu e recusa
ao forçar o endereço; autenticando gestão e conferindo os quatro
no menu, sem dado cadastral de hóspede em nenhum.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção ou de equipe operacional,
   **When** a pessoa inspeciona o menu, **Then** não vê Painel,
   Mercado, Usuários nem Retenção de dados.
2. **Given** a mesma sessão, **When** tenta abrir qualquer um dos
   quatro endereços, **Then** é recusada sem ver indicador,
   concorrente, usuário da casa, comprovante nem tela vazia, e a
   tela não dispara a consulta correspondente.
3. **Given** uma sessão de gestão, **When** inspeciona o menu,
   **Then** vê os quatro destinos e cai em Painel como tela
   inicial do papel.
4. **Given** qualquer uma das quatro telas numa sessão de gestão,
   **When** a pessoa procura dado cadastral de hóspede, **Then**
   não há — nem como campo, nem como lista escondida atrás de um
   número.

---

### Edge Cases

- Hotel sem concorrente cadastrado: Mercado devolve lista vazia
  honesta, distinta de falha ao ler.
- Concorrente desativado: permanece visível no comparativo,
  distinguível como inativo, com a série intacta. A tela de
  comparação não oferece apagar.
- Periodicidade de coleta ausente ou inválida: os valores
  continuam com as datas reais; nenhum número é apresentado como
  atual.
- Preço público zero em sucesso: aparece como zero datado,
  distinguível de vazio e de falha.
- Hotel sem nenhuma passagem de retenção ainda: lista vazia
  honesta, distinta de falha; os prazos vigentes continuam
  visíveis.
- Passagem em que nada venceu: a linha existe com quantidades
  zero — cumprimento também se demonstra assim.
- Único usuário de gestão da casa: não consegue desativar a si
  mesmo; a casa não fica sem gestão por este caminho.
- Funcionário desativado tenta autenticar: o acesso continua
  recusado, como já é regra — esta tela não cria exceção.
- Senha no mínimo exatamente: aceita. Um caractere a menos:
  recusa na hora.
- E-mail já usado em outra propriedade: a unicidade já existente
  vale; a recusa aparece nesta tela.
- E-mail de usuário desativado na própria casa: continua ocupado.
  Criar outro com o mesmo endereço é recusado. Não há reativar.
- Sessão de outro hotel: nenhum indicador, concorrente, usuário
  ou comprovante alheio aparece.
- Recepção ou gestão no celular: as quatro telas funcionam, mas
  esta fatia não promete layout de mão.
- Equipe operacional no computador: os quatro destinos
  continuam recusados; o recorte não muda por tamanho de tela.
- Gráfico de série de mensagens e chamados ilustrado no rascunho
  de telas: não faz parte desta fatia.
- Linha “você” com a tarifa da própria casa no rascunho de
  mercado: não faz parte desta fatia.
- Percentual de variação em sete dias ilustrado no rascunho: não
  é calculado aqui; a variação se observa pelos valores datados
  e, se a gestão abrir o histórico já existente de um
  concorrente, pela série no tempo.
- Proporção de fichas antecipadas e nota média de trinta dias
  ilustradas no rascunho do Painel: não fazem parte desta fatia.
- Consumo faturável ainda pendente de lançamento: entra só na
  soma em dinheiro de “consumo ainda a lançar”. Não aumenta
  “chamados em aberto”.
- Cadastro de concorrente (criar, corrigir, desativar) já existe
  fora das telas e **permanece fora** desta fatia. Mercado aqui é
  só o comparativo. Coleta na hora e visita à fonte continuam
  fora.
- Listagem e revogação de sessão de dispositivo: continuam da
  recepção e **fora** destas quatro telas. Esta fatia não cria a
  tela de sessões da recepção.

## Requirements *(mandatory)*

### Functional Requirements

**Painel**

- **FR-001**: A gestão DEVE poder abrir Painel e ver quatro
  indicadores agregados da própria propriedade, cada um com este
  recorte: **chegadas de hoje** — quantidade de reservas com
  entrada prevista para o dia corrente, ainda não encerradas nem
  canceladas (contagem já existente); **hospedados no momento** —
  quantidade de reservas em casa agora; **chamados em aberto** —
  quantidade de reclamações e pedidos de serviço ainda não
  resolvidos, **sem** consumo faturável; **consumo ainda a
  lançar** — soma em dinheiro dos itens que ainda esperam
  lançamento. NÃO DEVE mostrar proporção de fichas antecipadas nem
  nota média.
- **FR-002**: Cada indicador DEVE ser um número (quantidade ou
  valor). A tela NÃO DEVE apresentar lista nominada de reserva,
  hóspede, chamado ou consumo, nem servir essa lista para a gestão
  filtrar depois.
- **FR-003**: Zero DEVE ser distinguível de falha ao ler. Falha NÃO
  DEVE ser apresentada como “a casa não tem movimento”.
- **FR-004**: A tela NÃO DEVE oferecer alterar reserva, hóspede,
  solicitação, consumo ou avaliação.
- **FR-005**: A tela NÃO DEVE apresentar gráfico de série temporal
  de mensagens ou chamados. O rascunho ilustra o gráfico; o
  critério desta fatia é o número agregado.

**Mercado**

- **FR-006**: A gestão DEVE poder abrir Mercado e ver cada
  concorrente da própria propriedade com nome e com o preço e/ou a
  nota da última coleta bem-sucedida, quando houver, cada valor
  com a data da coleta.
- **FR-007**: Concorrente cuja coleta falhou DEVE aparecer marcado
  de forma distinguível. O valor de um sucesso anterior DEVE
  permanecer com a data antiga. NÃO DEVE ser redatado, zerado nem
  apresentado como dado atual.
- **FR-008**: Ausência de coleta e falha sem sucesso anterior NÃO
  DEVEM inventar zero como preço ou nota.
- **FR-009**: A tela NÃO DEVE exibir nem comparar a tarifa da
  própria casa.
- **FR-010**: A tela NÃO DEVE oferecer corrigir, apagar, redatar
  ou substituir registro coletado. NÃO DEVE disparar coleta nem
  visitar fonte.
- **FR-011**: A gestão DEVE poder consultar o histórico já
  existente de um concorrente da própria casa, em ordem de tempo,
  com falha distinta de preço zero.
- **FR-012**: A tela de Mercado NÃO DEVE oferecer cadastrar,
  corrigir, desativar nem reativar concorrente. Essa manutenção
  permanece fora desta fatia.

**Usuários**

- **FR-013**: A gestão DEVE poder abrir Usuários e ver os
  funcionários da própria propriedade, ativos e desativados, cada
  um com nome, e-mail, perfil e situação distinguível. A senha NÃO
  DEVE aparecer.
- **FR-014**: A gestão DEVE poder criar usuário com nome, e-mail,
  um dos três perfis e senha inicial. A senha DEVE ter ao menos o
  mínimo já exigido pelo acesso (doze caracteres). Usuário novo
  DEVE nascer ativo.
- **FR-015**: Senha abaixo do mínimo, e-mail já cadastrado, perfil
  fora dos três ou campo obrigatório ausente DEVE recusar a
  criação na hora, nesta tela.
- **FR-016**: A gestão DEVE poder desativar usuário da própria
  casa. Desativar NÃO DEVE apagar o registro. As sessões daquela
  pessoa DEVEM deixar de ser aceitas.
- **FR-017**: A tela NÃO DEVE oferecer reativar usuário
  desativado. Voltar a ter acesso exige um cadastro novo, com
  e-mail diferente — o e-mail do desativado permanece único e
  ocupado.
- **FR-018**: A tela NÃO DEVE oferecer desativar a própria sessão
  autenticada. A tentativa, se forçada, DEVE ser recusada.
- **FR-019**: A tela NÃO DEVE oferecer listar nem revogar sessão
  de dispositivo. Essa urgência permanece da recepção.

**Retenção de dados**

- **FR-020**: A gestão DEVE poder abrir Retenção de dados e ver as
  execuções da própria propriedade, cada uma com data e hora, tipo
  tratado e quantidade de registros — inclusive quantidade zero.
- **FR-021**: A tela DEVE informar os prazos vigentes da política
  (ficha após a saída e conteúdo de conversa) como leitura. NÃO
  DEVE oferecer alterá-los nem disparar expurgo agora.
- **FR-022**: Comprovante e tela NÃO DEVEM mostrar nome, telefone,
  documento, mensagem, comentário nem qualquer outro dado
  cadastral ou conteúdo livre de hóspede.

**Perfis, dispositivo e honestidade**

- **FR-023**: Recepção e perfil operacional NÃO DEVEM ver os quatro
  destinos no menu. Tentativa pelo endereço DEVE ser recusada sem
  conteúdo e sem disparar a consulta.
- **FR-024**: Gestão DEVE ver os quatro destinos no menu. Painel
  DEVE continuar sendo a tela inicial desse papel.
- **FR-025**: Nenhuma das quatro telas DEVE apresentar dado
  cadastral de hóspede.
- **FR-026**: As quatro telas NÃO DEVEM usar o recorte compacto da
  equipe no celular. São telas de computador.
- **FR-027**: Toda leitura e toda gravação DEVEM considerar a
  propriedade do funcionário. Sessão de um hotel NÃO DEVE mostrar
  nem alterar indicador, concorrente, usuário ou comprovante de
  outro.

**Fora desta fatia**

- **FR-028**: Esta fatia NÃO DEVE alterar regra de contagem já
  existente, série coletada, cadastro de concorrente, política de
  senha, desativar usuário, passagem automática de retenção,
  prazo de sessão nem matriz de permissões de dado de domínio.
  Onde a consulta agregada ainda não existir como número puro,
  DEVE nascer como número puro — NÃO DEVE reusar lista nominada
  da recepção.
- **FR-029**: Esta fatia NÃO DEVE integrar-se ao sistema de gestão
  do hotel, NÃO DEVE alterar tarifa da casa, NÃO DEVE enviar
  mensagem ao hóspede, NÃO DEVE ligar ou desligar módulo, NÃO DEVE
  editar personalidade da assistente e NÃO DEVE construir a tela
  de sessões da recepção.
- **FR-030**: Log desta fatia NÃO DEVE registrar senha, conteúdo
  de mensagem de hóspede, identificador de sessão apresentado ao
  cliente, texto de página de fonte nem dado cadastral de
  hóspede. PODE registrar identificador de usuário, de
  concorrente, perfil, quantidades de retenção e código de
  recusa.

### Key Entities

- **Painel**: tela inicial da gestão com números da operação.
  Dimensiona; não identifica hóspede. Distinta da fila do dia.
- **Indicador agregado**: quantidade ou valor da propriedade, sem
  lista por baixo. Nesta fatia: chegadas de hoje; hospedados (em
  casa agora); chamados em aberto (reclamação e serviço não
  resolvidos, sem consumo); consumo a lançar (soma em dinheiro do
  pendente). Proporção de fichas antecipadas e nota média ficam
  fora.
- **Mercado**: tela da gestão com o comparativo dos concorrentes
  já cadastrados. Somente leitura da série coletada. Não é a
  manutenção de quem acompanhar.
- **Concorrente da propriedade**: ficha que a casa escolheu
  acompanhar. Ativo entra na coleta; inativo permanece na
  consulta. Não é a própria casa.
- **Coleta falhada**: tentativa sem valor encontrado. Aparece
  marcada; não substitui o sucesso anterior nem se disfarça de
  atual.
- **Usuários**: tela da gestão com o quadro de acesso da casa.
  Criar e desativar são autoridade. Revogar sessão não mora aqui.
- **Funcionário**: nome, e-mail, um dos três perfis e situação
  (ativo ou desativado). Desativar não apaga e não reativa.
  Senha nunca é exibida. Não é hóspede.
- **Retenção de dados**: tela da gestão com o comprovante das
  passagens automáticas. Demonstra cumprimento; não dispara
  expurgo.
- **Comprovante de retenção**: uma execução — quando, o quê e
  quantos. Sem o conteúdo tratado.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A gestão conclui, em uma visita ao painel, ver os
  números da operação, o comparativo de mercado, a lista de
  usuários e o comprovante de retenção, sem sair do sistema e sem
  passo fora da tela.
- **SC-002**: Em 100% das sessões de gestão nestas quatro telas, 0
  campos cadastrais de hóspede (nome, telefone, documento,
  nascimento) são apresentados, e 0 listas nominadas de reserva
  ou de chamado são servidas para montar um indicador.
- **SC-003**: Em 100% dos concorrentes com coleta falhada, a falha
  está marcada e o valor anterior, se houver, permanece com a
  data antiga — 0 desses valores aparecem como se fossem de agora.
- **SC-004**: 100% das tentativas de criar usuário sem perfil
  válido ou com senha abaixo do mínimo falham na hora, nesta
  tela. 100% das desativações pela tela deixam o registro
  visível; 0 oferecem apagar; 0 oferecem reativar.
- **SC-005**: Em 100% das execuções visíveis em Retenção de dados,
  data, tipo e quantidade estão presentes (quantidade pode ser
  zero). 0 disparos manuais de expurgo existem na tela.
- **SC-006**: Em 100% das sessões de gestão, revogar sessão não
  aparece. Em 100% das sessões de recepção e de equipe
  operacional, os quatro destinos são recusados sem conteúdo.
- **SC-007**: Em 100% das comparações de mercado nesta tela, a
  tarifa da própria casa não aparece.
- **SC-008**: Cada critério de aceite da fatia F8.7 do backlog tem
  ao menos um cenário nesta spec, exercitável na tela.

## Assumptions

- **Quatro destinos, não uma tela só.** A casca já nomeia Painel,
  Mercado, Usuários e Retenção de dados só para a gestão, hoje
  com título sozinho. Esta fatia preenche os quatro.
- **Números do Painel (clarificado em 2026-09-02).** Quatro
  indicadores: chegadas de hoje (contagem já existente); hospedados
  no momento (reservas em casa agora); chamados em aberto
  (reclamações e pedidos de serviço não resolvidos — consumo
  faturável não entra nesta conta); consumo ainda a lançar (soma
  em dinheiro do que espera lançamento, não a quantidade de
  itens). Cada um como número, nunca lista. O gráfico de trinta
  dias, a proporção de fichas antecipadas e a nota média do
  rascunho ficam fora. Onde a consulta ainda devolveria lista
  nominada se reusada da recepção, esta fatia exige o número puro
  — a gestão não recebe a fila para filtrar no painel.
- **Mercado reusa o comparativo já entregue.** Data na coleta,
  falha marcada, desatualizado, histórico e recusa de escrita da
  série já existem. Esta fatia os torna visíveis. A linha “você”
  com tarifa da casa e o percentual de variação em sete dias do
  rascunho **não** entram: o primeiro contradiz a premissa de não
  se integrar ao outro sistema do hotel; o segundo não é produto
  da coleta já entregue.
- **Manutenção de concorrente fica fora desta superfície
  (clarificado em 2026-09-02).** O rascunho traz uma aba ao lado
  do comparativo; o enunciado e o critério de aceite pedem só a
  comparação com falha marcada. Criar, corrigir, desativar e
  reativar concorrente continuam onde já existem, fora do painel.
  Disparo manual de coleta continua fora.
- **Relação de usuários precisa da lista visível
  (clarificado em 2026-09-02).** Criar e desativar já existem; a
  lista na tela é o que falta para a “relação” do enunciado.
  Reativar, embora no rascunho, **não entra**. Desativar não
  apaga; o e-mail continua único, então quem volta precisa de
  conta nova com outro e-mail. Troca de senha de um usuário já
  existente continua fora.
- **Mínimo de senha** é o já exigido no acesso: doze caracteres.
  Esta fatia não inventa regra nova; mostra a recusa na hora.
- **Revogar sessão não ganha tela nesta fatia.** O critério é que
  a gestão não a veja. A tela da recepção para listar e revogar
  dispositivo, se ainda for só consulta fora do painel, permanece
  para fatia futura.
- **Comprovante de retenção já existe.** Esta fatia o mostra.
  Prazos vigentes aparecem como leitura; editar prazo e disparar
  agora continuam fora. O rascunho agrupa tipos em linhas
  (“conversas”, “fichas”); a tela pode apresentar as quantidades
  já gravadas por espécie, sem inventar tipo que o comprovante
  não tem.
- **Testes desta fatia exercitam a tela** (o que cada perfil vê,
  a marca de falha, a recusa ao criar, a ausência de dado
  cadastral). Não reescrevem a suíte da coleta, da retenção nem
  do acesso; aproveitam o comportamento já coberto lá.
- **Módulos por propriedade, canal de e-mail, personalidade da
  assistente e configurações da propriedade** permanecem fora, no
  mesmo corte já declarado no backlog da semana.
