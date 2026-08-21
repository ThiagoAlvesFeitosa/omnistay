# Feature Specification: Painel de Mercado

**Feature Branch**: `022-painel-mercado`

**Created**: 2026-08-21

**Status**: Draft

**Input**: User description: "A gestão consulta os preços e avaliações coletados,
com a data de cada coleta sempre visível, e acompanha a variação ao longo do
tempo. Dado antigo é exibido com indicação explícita de quando foi coletado."
(backlog F5.3)

Restrições já decididas no projeto (entrada do specify): o sistema **não** se
integra ao sistema de gestão do hotel nem altera tarifa da casa — observa e
mostra, não precifica; cada valor coletado **carrega a data da coleta por
exigência de uso**, não de auditoria; preço sem carimbo é pior do que ausência
de dado; falha de coleta **não** apaga o número anterior e **não** o faz
parecer de hoje; gestão **não** inventa nem corrige preço ou nota coletados
(somente leitura do que a coleta gravou); cadastro de quem acompanhar já existe
e **não** é redesenhado aqui; esta fatia **não** visita fonte, **não** dispara
coleta e **não** envia mensagem ao hóspede; conteúdo de mensagem de hóspede
nunca vai para log.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Comparar o mercado sem sair do sistema (Priority: P1)

Como gestão do hotel, quero abrir o painel e ver, de uma vez, o preço e a
nota agregada mais recentes de cada concorrente que a casa acompanha — cada
número com a data e a hora em que foi coletado — para decidir tarifa sem
abrir site na mão e sem tratar um valor órfão como “o preço de agora”.

**Why this priority**: É o objetivo da fatia. Cadastro e coleta já existem;
sem esta consulta, a série fica no depósito e a gestão continua saindo do
sistema. Um número sem data é o defeito que o depósito de mercado existe
para impedir.

**Independent Test**: Pode ser testado autenticando como gestão numa
propriedade com ao menos dois concorrentes que já tenham coleta bem-sucedida
em datas diferentes, consultando o painel de mercado e verificando: cada
concorrente aparece com nome, preço e/ou nota da última coleta **bem-sucedida**
(se houver), e **todo** valor exibido traz a data daquela coleta — nenhum
número aparece sem carimbo.

**Acceptance Scenarios**:

1. **Given** uma sessão autenticada de perfil de gestão e uma propriedade
   com concorrentes que já tiveram ao menos uma coleta bem-sucedida,
   **When** a gestão consulta o painel de mercado, **Then** cada concorrente
   daquela propriedade aparece com o nome e com o preço e/ou a nota
   agregada da última coleta bem-sucedida, e **cada** um desses valores
   exibe a data e a hora da coleta correspondente.
2. **Given** um concorrente cuja última coleta bem-sucedida tem preço e
   nota, **When** o painel é consultado, **Then** os dois valores aparecem
   e **ambos** carregam a mesma data daquela coleta — não há valor
   “atual” sem data ao lado de outro datado.
3. **Given** um concorrente que só teve sucesso com preço (nota vazia) ou
   só com nota (preço vazio), **When** o painel é consultado, **Then** o
   campo obtido aparece com a data da coleta e o campo não obtido permanece
   vazio — vazio **não** é apresentado como zero.
4. **Given** um concorrente cuja coleta bem-sucedida encontrou preço
   público **zero**, **When** o painel é consultado, **Then** o zero
   aparece como valor, com a data da coleta — distinguível de campo vazio
   e de falha.

---

### User Story 2 - Dado velho não se disfarça de atual (Priority: P1)

Como gestão, quero que um número cuja coleta já passou da cadência da casa
venha **sinalizado como desatualizado**, e que uma tentativa recente que
falhou deixe o valor anterior no lugar **com o carimbo antigo visível** —
nunca redatado, nunca zerado, nunca apresentado como se fosse de hoje —
para eu não decidir tarifa em cima de um preço que já envelheceu.

**Why this priority**: O critério de aceite da fatia exige sinalizar dado
desatualizado, além de mostrar a data. Data sozinha informa; o sinal
impede a leitura apressada. A documentação já registrou: falha mantém o
dado anterior com o carimbo antigo visível. Confundir os dois é pior do
que não ter painel.

**Independent Test**: Pode ser testado com três concorrentes da mesma
propriedade: um com sucesso dentro da periodicidade; um com último sucesso
mais antigo que a periodicidade; um com sucesso antigo seguido de falha
recente — verificando sinal de desatualizado só onde cabe, data antiga
intacta no valor ainda exibido, e falha visível sem substituir o número
por zero.

**Acceptance Scenarios**:

1. **Given** um concorrente cuja última coleta bem-sucedida está **dentro**
   da periodicidade configurada da propriedade, **When** a gestão consulta
   o painel, **Then** o valor aparece com a data da coleta e **não** é
   sinalizado como desatualizado.
2. **Given** um concorrente cuja última coleta bem-sucedida é **mais
   antiga** do que a periodicidade da propriedade, **When** a gestão
   consulta o painel, **Then** o valor continua visível com a data antiga
   **e** vem sinalizado como desatualizado.
3. **Given** um concorrente com coleta bem-sucedida antiga e uma tentativa
   **posterior** marcada como falha, **When** a gestão consulta o painel,
   **Then** o preço e/ou a nota do sucesso anterior permanecem, com a data
   daquele sucesso (não a da falha); o valor **não** é apagado nem zerado;
   a falha posterior é distinguível; o conjunto é tratado como
   desatualizado.
4. **Given** um concorrente que só tem tentativas falhas, nunca um sucesso,
   **When** a gestão consulta o painel, **Then** não aparece preço nem
   nota como valor encontrado; a falha mais recente aparece com a data da
   tentativa; nenhum zero é inventado.

---

### User Story 3 - Acompanhar a variação ao longo do tempo (Priority: P1)

Como gestão, quero ver o histórico de coletas de cada concorrente em ordem
de tempo — sucessos com preço e/ou nota e data, falhas como falha datada,
nunca como preço zero — para observar se a tarifa subiu, caiu ou ficou
parada, em vez de enxergar só o último número.

**Why this priority**: A série temporal é o produto real da inteligência
de mercado. Um valor único, mesmo datado, não mostra movimento. Falha
desenhada como zero fabricaria uma queda que não existiu.

**Independent Test**: Pode ser testado com um concorrente que tenha três
sucessos em datas e preços diferentes e uma falha no meio, consultando o
histórico e verificando: os quatro pontos aparecem na ordem das coletas;
os sucessos trazem os valores originais e as datas originais; a falha
não entra como zero; nenhum ponto antigo foi alterado.

**Acceptance Scenarios**:

1. **Given** um concorrente com várias coletas bem-sucedidas em datas
   distintas, **When** a gestão consulta o histórico daquele concorrente,
   **Then** cada sucesso aparece com preço e/ou nota daquele ciclo e com
   a respectiva data, em ordem cronológica, permitindo ver se o valor
   subiu, caiu ou se manteve.
2. **Given** uma falha intercalada entre dois sucessos, **When** o
   histórico é consultado, **Then** a falha aparece como tentativa sem
   valor encontrado, com a data da tentativa — **não** como preço zero e
   **não** omitida a ponto de colar os dois sucessos como se fossem
   consecutivos sem intervalo.
3. **Given** o histórico já gravado, **When** a gestão consulta de novo
   depois de uma coleta nova (sucesso ou falha), **Then** os pontos
   anteriores permanecem com os mesmos valores e as mesmas datas; o ponto
   novo se acrescenta — o painel **não** reescreve o passado.
4. **Given** dois concorrentes da mesma propriedade, **When** a gestão
   consulta o histórico, **Then** a série de um não se mistura com a do
   outro.

---

### User Story 4 - Somente leitura, só a gestão, só a própria casa (Priority: P1)

Como responsável pelos dados da propriedade, quero que o painel de mercado
seja consulta — a gestão **não** corrige, apaga nem “atualiza na mão”
nenhum registro coletado — que recepção e operação sejam recusadas, e que
o concorrente do hotel vizinho nunca apareça, para a inteligência de
mercado não virar planilha editável nem vazar estratégia.

**Why this priority**: O critério de aceite exige que gestão não altere
registro coletado. O papel da gestão neste depósito é estritamente de
leitura: a decisão de preço acontece fora. Multi-tenant e recusa de
balcão já valem no cadastro; o painel herda as fronteiras.

**Independent Test**: Pode ser testado consultando o painel com gestão da
própria casa (permitido, sem caminho de alteração da série), tentando
alterar um registro coletado, tentando com recepção e operação, e
consultando a partir de outro hotel — verificando recusas e isolamento.

**Acceptance Scenarios**:

1. **Given** uma sessão de perfil de gestão da propriedade, **When** ela
   consulta o painel e o histórico dos próprios concorrentes, **Then** a
   operação é permitida.
2. **Given** a mesma sessão de gestão, **When** tenta criar, alterar,
   apagar, redatar ou substituir qualquer registro de coleta, **Then** a
   operação **não** é oferecida — o caminho suportado é só consulta.
3. **Given** uma sessão de perfil de recepção ou operacional, **When**
   tenta consultar ou alterar o painel de mercado, **Then** a operação é
   recusada.
4. **Given** coletas gravadas no hotel A, **When** uma sessão do hotel B
   consulta o próprio painel, **Then** nenhum concorrente e nenhuma
   coleta do hotel A aparecem.
5. **Given** uma sessão de gestão do hotel A, **When** tenta consultar o
   histórico de um concorrente que pertence ao hotel B, **Then** a
   consulta é recusada sem confirmar que o concorrente existe.

---

### Edge Cases

- Propriedade sem concorrente cadastrado: o painel devolve consulta vazia
  e explícita — não é erro; a casa ainda não escolheu quem acompanhar.
- Concorrente cadastrado e ainda nunca coletado: aparece na visão atual
  sem preço nem nota, com indicação explícita de que ainda não houve
  coleta — não é zero e não é “desatualizado” de um valor que não existe.
- Concorrente desativado: permanece visível no painel da propriedade,
  distinguível como inativo, com o último sucesso (se houver) e o
  histórico intactos. Desativar não apaga a série. Some da coleta futura;
  não some da consulta.
- Último sucesso dentro da periodicidade, mas já existe falha **depois**:
  o valor exibido é o do sucesso, com a data do sucesso; o conjunto não
  é tratado como atual — a tentativa de renovar falhou. Sinal de
  desatualizado aplica.
- Periodicidade da propriedade ausente ou inválida: o painel **ainda**
  mostra os valores com as datas reais. Não marca nenhum número como
  atual. Não inventa limiar de “velho” a partir de um intervalo embutido.
  O sinal de desatualizado fica explícito como “cadência não configurada”
  (ou equivalente), nunca como se a casa tivesse uma janela padrão.
- Preço público zero em sucesso: exibido como zero datado. Falha: sem
  valor encontrado. Os dois permanecem distinguíveis no painel e no
  histórico.
- Nota vazia com preço preenchido (e o inverso): o campo vazio não vira
  zero na exibição nem no histórico.
- Dois hotéis com o mesmo endereço de fonte: cada um vê só a própria
  série. O painel de um não lê a coleta do outro.
- Esta fatia **não** dispara coleta, **não** visita fonte, **não** altera
  a lista de concorrentes (criar, editar, desativar, reativar continuam
  na fatia de cadastro) e **não** oferece “coletar agora”.
- Esta fatia **não** mostra nem compara a tarifa da própria casa. O
  sistema não consulta o outro sistema do hotel e não inventa o preço
  próprio. A comparação é entre concorrentes coletados. A decisão de
  tarifa continua fora.
- Esta fatia **não** envia mensagem ao hóspede, **não** abre chamado e
  **não** mistura Market Intel com fila do dia, pulso ou pesquisa.
- Tela visual nova do protótipo (composição gráfica do painel) **não**
  faz parte do critério de pronto desta fatia. O comportamento observável
  é a consulta autenticada: visão atual datada, sinal de desatualizado e
  histórico da série.
- Logs da consulta registram hotel, identificador do concorrente e ação
  de leitura. **Não** registram o texto de página de fonte, nome de
  avaliador nem conteúdo de mensagem de hóspede.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A gestão MUST poder consultar o painel de mercado da
  propriedade da sessão: cada concorrente da casa, com nome e com o preço
  e/ou a nota agregada da última coleta **bem-sucedida**, quando houver.
- **FR-002**: Todo preço ou nota exibido MUST carregar a data e a hora da
  coleta da qual foi lido. MUST NOT existir valor numérico de mercado no
  painel sem esse carimbo.
- **FR-003**: A visão atual MUST usar a última coleta **bem-sucedida** do
  concorrente como fonte do preço e da nota. Tentativa posterior falha
  MUST NOT apagar, zerar nem redatar esse sucesso.
- **FR-004**: Campo não obtido numa coleta bem-sucedida (preço vazio ou
  nota vazia) MUST permanecer vazio na exibição. MUST NOT ser apresentado
  como zero.
- **FR-005**: Preço público zero de uma coleta bem-sucedida MUST ser
  exibido como zero, com a data da coleta, distinguível de vazio e de
  falha.
- **FR-006**: Quando a última coleta bem-sucedida for mais antiga do que
  a periodicidade configurada da propriedade (`periodicidade_coleta_mercado`),
  o painel MUST sinalizar aquele concorrente como **desatualizado**, além
  de mostrar a data.
- **FR-007**: Quando existir tentativa de coleta **posterior** à última
  bem-sucedida e essa tentativa for falha, o painel MUST manter o sucesso
  anterior com a data antiga, MUST tornar a falha distinguível e MUST
  sinalizar o conjunto como desatualizado.
- **FR-008**: Concorrente só com falhas MUST aparecer sem preço nem nota
  como valor encontrado, com a data da falha mais recente visível. MUST
  NOT inventar zero.
- **FR-009**: Concorrente ainda nunca coletado MUST aparecer sem preço nem
  nota, com indicação explícita de ausência de coleta — distinta de falha
  e de desatualizado de um valor existente.
- **FR-010**: A gestão MUST poder consultar o histórico de coletas de um
  concorrente da própria propriedade, em ordem cronológica, cobrindo a
  série completa já gravada.
- **FR-011**: Cada ponto do histórico MUST distinguir sucesso (com preço
  e/ou nota e data) de falha (sem valor encontrado, com data da
  tentativa). Falha MUST NOT aparecer como preço zero.
- **FR-012**: O painel MUST NOT alterar, apagar, redatar ou substituir
  registro de coleta. Gestão MUST NOT ter caminho para inventar ou
  corrigir preço ou nota coletados.
- **FR-013**: Consultar o painel de mercado (visão atual e histórico)
  MUST ser exclusivo do perfil de gestão.
- **FR-014**: Recepção e perfil operacional MUST receber recusa ao tentar
  ler ou alterar o painel de mercado.
- **FR-015**: Toda leitura MUST considerar o hotel da sessão. Coleta e
  concorrente de um hotel MUST NOT ser visíveis na consulta de outro.
  Tentativa de ler concorrente alheio MUST ser recusada sem confirmar que
  a ficha existe.
- **FR-016**: Concorrente desativado MUST permanecer consultável no painel
  da propriedade, distinguível como inativo, com a série intacta.
- **FR-017**: Propriedade sem concorrentes MUST devolver consulta vazia
  explícita, sem erro.
- **FR-018**: Periodicidade ausente ou inválida MUST NOT inventar limiar.
  O painel ainda MUST mostrar valores com as datas reais e MUST NOT
  marcar nenhum número como atual.
- **FR-019**: Esta fatia MUST NOT disparar coleta, MUST NOT visitar fonte,
  MUST NOT alterar cadastro de concorrente, MUST NOT alterar tarifa da
  casa, MUST NOT consultar o sistema de gestão do hotel e MUST NOT enviar
  mensagem ao hóspede.
- **FR-020**: Esta fatia MUST NOT exibir nem comparar a tarifa da própria
  casa. A comparação visível é entre os concorrentes coletados.
- **FR-021**: Logs MUST registrar identificador do concorrente, hotel e
  ação de consulta. MUST NOT registrar conteúdo de mensagem de hóspede,
  texto de página da fonte nem dado de avaliador individual.

### Key Entities

- **Painel de mercado**: consulta da gestão sobre o que já foi coletado
  na propriedade. Informativo, não transacional: mostra números datados;
  não muda tarifa da casa e não aceita correção manual da série.
- **Visão atual**: o retrato de cada concorrente no momento da consulta —
  último sucesso (preço e/ou nota), data daquele sucesso, sinal de
  desatualizado quando couber, e falha posterior distinguível se existir.
- **Histórico de coleta**: a série temporal de um concorrente, ponto a
  ponto, na ordem em que as tentativas ocorreram. É o que permite observar
  variação.
- **Coleta de mercado**: um ponto da série, já gravado pela fatia
  anterior. Sempre tem data e indicação de sucesso ou falha. Em sucesso,
  traz preço público e/ou nota agregada. Em falha, não apresenta valor
  encontrado. O painel só lê.
- **Dado desatualizado**: valor ainda exibido cuja última coleta
  bem-sucedida já passou da periodicidade da propriedade, ou cujo ciclo
  seguinte já falhou. Continua visível com a data antiga; nunca é
  apresentado como atual.
- **Concorrente da propriedade**: ficha já cadastrada, ativa ou inativa.
  Inativo permanece na consulta com a série; não volta à coleta enquanto
  estiver desativado.
- **Periodicidade da coleta**: intervalo, em horas, configurado por
  propriedade. Nesta fatia, é o limiar que distingue atual de
  desatualizado. Não é redefinido aqui.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos valores de preço ou nota apresentados no painel,
  a data da coleta correspondente está visível. 0 números de mercado
  aparecem sem carimbo.
- **SC-002**: Em 100% das consultas com último sucesso mais antigo que a
  periodicidade da propriedade, o concorrente vem sinalizado como
  desatualizado **e** o valor permanece com a data antiga.
- **SC-003**: Em 100% dos casos com sucesso antigo seguido de falha
  posterior, o painel mantém o sucesso (valores e data originais), torna
  a falha distinguível e não apresenta o conjunto como atual. 0 desses
  sucessos são apagados, zerados ou redatados.
- **SC-004**: Em 100% dos históricos com falha intercalada, a falha
  aparece como tentativa sem valor encontrado. 0 falhas são exibidas como
  preço zero.
- **SC-005**: Em verificação com dois hotéis, 0% dos concorrentes e 0%
  das coletas de um aparecem no painel do outro.
- **SC-006**: Em sessão de recepção ou operacional, 100% das tentativas
  de ler o painel de mercado são recusadas. Em sessão de gestão da
  própria propriedade, 100% das consultas previstas são permitidas e
  100% das tentativas de alterar registro coletado são recusadas ou
  inexistentes.
- **SC-007**: A gestão obtém a comparação datada da propriedade em uma
  única consulta da visão atual, sem etapas intermediárias obrigatórias
  e sem sair do sistema para abrir a fonte.
- **SC-008**: O caminho visão atual datada → sinal de desatualizado no
  vencido → histórico com variação visível → falha posterior sem destruir
  o sucesso antigo é verificável de ponta a ponta sem visitar fonte, sem
  disparar coleta e sem o canal de mensagens.
- **SC-009**: Em 100% das execuções desta fatia, 0 coletas são disparadas,
  0 fontes são visitadas, 0 tarifas da casa são alteradas e 0 mensagens
  são enviadas a hóspede.
- **SC-010**: Em 100% das execuções, logs operacionais não contêm
  conteúdo de mensagem de hóspede, texto de página da fonte nem dado de
  avaliador individual.

## Assumptions

- As fatias F5.1 (cadastro de concorrentes) e F5.2 (coleta agendada) estão
  concluídas. Esta fatia **não** recadastra concorrente e **não** coleta:
  lê a série já gravada. Inativo continua fora da coleta e **dentro** da
  consulta, para o histórico não desaparecer ao desativar.
- **Quem consulta é a gestão.** Inteligência de mercado é processo da
  gestão, não do balcão. Recepção e operação não leem o painel. A gestão
  **escreve** a lista de quem acompanhar (fatia anterior) e **só lê**
  preço e nota coletados. “Perfil de gestão não altera nenhum registro”
  refere-se à série coletada, não ao cadastro de concorrente.
- **Limiar de desatualizado** é a periodicidade já configurada da
  propriedade (`periodicidade_coleta_mercado`, em horas). Não se cria
  chave nova nem número mágico. Sucesso mais recente há menos tempo que
  esse intervalo, sem falha posterior: atual. Sucesso mais antigo que o
  intervalo, ou sucesso seguido de falha posterior: desatualizado. Sem a
  chave válida, nada é apresentado como atual.
- **Visão atual lê o último sucesso**, não a última tentativa. Falha
  posterior fica visível ao lado, com a data da tentativa, para não
  parecer que o sistema parou de tentar nem que o número velho foi
  renovado.
- **Variação** é observada pela série em ordem de tempo. Esta fatia não
  calcula índice de mercado, média entre concorrentes nem percentual de
  variação como produto obrigatório. Ver os pontos sucessivos datados é
  o que o critério de aceite pede.
- **A tarifa da própria casa não entra na comparação.** O OmniStay não
  lê o outro sistema do hotel e não tem, neste MVP, o preço de quarto da
  casa como fato coletado. Prometer “quanto estamos em relação ao
  mercado” seria superpromessa. A gestão compara os concorrentes e decide
  fora.
- Superfície de uso: consulta autenticada da visão atual e do histórico.
  Ligar o protótipo visual continua fora do critério de pronto, no mesmo
  padrão das fatias já entregues. Disparo manual de coleta continua fora.
- O painel não notifica a gestão quando uma coleta nova chega. A persona
  consulta em cadência semanal ou quinzenal; a fila visível aqui é a
  própria consulta. Notificação perdida não pode ser o único lugar do
  número — e nesta fatia o único lugar é o painel.
- Dado de avaliador individual continua fora: o painel mostra nota
  agregada, nunca nome, texto ou foto de quem avaliou.
- Esta fatia não muda tarifa da casa, não consulta o outro sistema do
  hotel e não envia mensagem ao hóspede. O Market Intel permanece
  informativo, em paralelo ao fluxo de estadia.
- Limitação honesta: o painel só mostra o que a coleta honesta conseguiu
  gravar. Fonte bloqueada, diretiva que recusa ou concorrente nunca
  coletado aparecem como ausência ou falha datada, não como cobertura
  completa do mercado.
