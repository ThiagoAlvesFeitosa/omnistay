# Feature Specification: Redesenho da casca do painel e apresentação

**Feature Branch**: `037-redesenho-casca-painel`

**Created**: 2026-09-02

**Status**: Draft

**Input**: User description: "Redesenho da casca do painel e ajuste de
apresentação em todas as telas." Fonte da decisão:
`docs/ajustes-de-interface.md` (02/09/2026). Menu lateral no lugar do
superior; identidade da casa e da pessoa na lateral; menu agrupado por
área; tirar do menu o que é ação e não lugar; simulador com cara de
conversa e Enter para enviar; moeda e data no padrão brasileiro.
A sessão corrente passa a incluir o nome da casa, porque o cabeçalho
precisa dele.

Restrições já decididas no projeto: o sistema **não** se integra ao
sistema de gestão do hotel; autenticação, sessão e matriz de perfis
**já existem** e não mudam nesta fatia — o que a autorização recusa, a
tela continua sem oferecer; dado cadastral de hóspede não aparece para
quem não pode vê-lo; conteúdo de mensagem e senha continuam fora do
log; a palavra "extrato" não existe no produto; recepção e gestão
operam no computador, e a equipe operacional precisa continuar
utilizando a tela no celular; destinos e títulos das telas (Fila do
dia, Estadia, Chamados e pedidos, etc.) permanecem os já entregues —
esta fatia redesenha a **casca** e a **apresentação**, não inventa
módulo novo. Módulos por propriedade (F7.4) e canal de e-mail (F7.5)
permanecem fora.

## Clarifications

### Session 2026-09-02

- Q: Quando a tela mostra um momento que tem hora (última coleta, execução de retenção, mensagem), como esse texto deve aparecer? → A: Data de calendário `02/09/2026`; instante `02/09/2026 10:00`. Nas listas de chamados e de consumos, o tempo decorrido (“há 8 min”) continua porque mostra urgência, mas como complemento do instante, não no lugar dele: `02/09/2026 14:32 · há 8 min`.
- Q: Nas bolhas da conversa (simulador e Estadia), o horário de cada mensagem deve ser só a hora ou a data e a hora juntas? → A: Mensagem do mesmo dia de calendário mostra só a hora (`14:32`); mensagem de outro dia mostra data e hora (`02/09/2026 14:32`). A estadia dura dias: só a hora misturaria terça e quinta. Na demonstração, tudo no mesmo dia, o fio fica limpo.
- Q: Na Estadia, o fio deve ganhar os mesmos balões do simulador, ou só o texto do horário muda? → A: Mesmos balões nas duas telas, dois lados (hóspede × hotel). Resposta da recepção e mensagem automática ficam no lado do hotel; a distinção automático × recepção continua no rótulo de origem já entregue na F7.6 — sem terceiro estilo de balão.
- Q: Com o menu aberto no celular, como a pessoa fecha a navegação sem necessariamente ir a outro destino? → A: Fecha pelo mesmo botão que abriu, ao tocar no fundo (área de trabalho), e também ao escolher destino ou Sair.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A casca identifica a casa e a pessoa (Priority: P1)

Como funcionário autenticado, quero ver o nome do hotel em destaque,
a marca do produto em tom discreto, e no rodapé o meu nome com o
perfil (Recepção, Gestão ou Equipe) junto de Sair, para saber em
qual casa estou e que a matriz de permissões está valendo — sem o
nome solto num canto e sem onze itens espremidos numa faixa no topo.

**Why this priority**: É o que o vídeo e o balcão mostram o tempo
todo. Sem identidade da casa e do papel, o redesenho não entrega o
princípio da lista. É o primeiro bloco visível da fatia.

**Independent Test**: Pode ser testado autenticando cada um dos três
perfis, conferindo nome da casa no topo da navegação, marca OmniStay
abaixo, e no rodapé o nome da pessoa com o rótulo do perfil e Sair;
e conferindo que a sessão, ao entrar e ao ser consultada de novo,
traz o nome da casa dessa pessoa.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção numa casa cujo nome é conhecido,
   **When** o painel autenticado abre, **Then** a navegação permanente
   mostra esse nome da casa em destaque no topo, a marca **OmniStay**
   logo abaixo em tom mais discreto (marca do produto, não do
   cliente), e no rodapé o nome da pessoa, o rótulo **Recepção** e
   **Sair**.
2. **Given** uma sessão de gestão na mesma casa, **When** o painel
   abre, **Then** o nome da casa e a marca OmniStay aparecem como no
   cenário 1, e o rodapé mostra o nome da pessoa com o rótulo
   **Gestão** e Sair.
3. **Given** uma sessão da equipe operacional, **When** o painel
   abre, **Then** o rodapé mostra o nome da pessoa com o rótulo
   **Equipe** (não o jargão interno do cadastro) e Sair.
4. **Given** um funcionário sem sessão, **When** ele entra com
   credencial válida, **Then** a resposta da entrada já traz o nome
   da casa, e a casca consegue mostrar esse nome sem uma consulta
   extra inventada só para o cabeçalho.
5. **Given** um funcionário já reconhecido no dispositivo, **When**
   o painel consulta a sessão corrente, **Then** essa consulta também
   traz o nome da casa — o mesmo da propriedade ligada a essa
   sessão, nunca o de outra casa.

---

### User Story 2 - Navegar por área, sem ação no menu (Priority: P1)

Como funcionário, quero o menu agrupado nas áreas do trabalho
(Operação, Propriedade, Gestão), com o simulador separado no fim, e
sem item que seja só um botão de ação duplicado, para achar o
destino certo sem achar que "Nova reserva" no menu e o botão na fila
são coisas diferentes.

**Why this priority**: Onze itens numa lista plana não têm
hierarquia, e a redundância da nova reserva já confundiu no teste
real. Sem isso a lateral nova só muda de lugar o mesmo problema.

**Independent Test**: Pode ser testado autenticando recepção, gestão
e equipe, conferindo os grupos visíveis, os itens de cada um, a
ausência de Nova reserva no menu da recepção, e a presença do botão
de nova reserva na fila do dia.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção, **When** a navegação autenticada
   está visível, **Then** os destinos aparecem agrupados: **Operação**
   (fila do dia, Estadia, chamados e pedidos, consumos a lançar,
   saída do hóspede), **Propriedade** (catálogo, itens vendáveis,
   recado de boas-vindas), e **Simulador** separado no fim — sem
   grupo Gestão (não há destino de gestão para este perfil).
2. **Given** o desfecho do cenário 1, **When** a pessoa procura Nova
   reserva no menu, **Then** o item **não** está lá; **When** abre a
   fila do dia, **Then** o botão de nova reserva permanece onde a
   ação pertence.
3. **Given** uma sessão de gestão, **When** a navegação está visível,
   **Then** aparecem **Propriedade** (catálogo, itens vendáveis,
   recado de boas-vindas), **Gestão** (painel, mercado, usuários,
   retenção de dados) e **Simulador** no fim — sem fila, sem
   Estadia, sem chamados da recepção.
4. **Given** uma sessão da equipe operacional, **When** a navegação
   está visível, **Then** aparece **Operação** com meus chamados; não
   há Propriedade, Gestão nem Simulador; não há destino de ficha ou
   conversa.
5. **Given** qualquer perfil, **When** um grupo não tem nenhum
   destino permitido, **Then** o rótulo desse grupo não aparece.

---

### User Story 3 - A equipe usa o painel no celular (Priority: P1)

Como funcionário da equipe no celular, quero que a navegação não
coma a tela inteira: um botão abre e fecha o menu, tocar no fundo
também fecha, o trabalho (meus chamados) permanece utilizável, e
ao escolher um destino o menu fecha, para registrar no quarto sem
lutar com onze itens horizontais.

**Why this priority**: A lista de ajustes existe porque a faixa
superior já quebra em tela menor, e a tela da equipe **precisa**
continuar utilizável no celular. Sem isto a casca nova piora o
turno da operação.

**Independent Test**: Pode ser testado com sessão da equipe numa
largura de telefone: o conteúdo de meus chamados aparece sem a
lateral permanente; um controle abre a navegação; o mesmo controle,
tocar no fundo, escolher um destino ou Sair fecha essa navegação.

**Acceptance Scenarios**:

1. **Given** uma sessão da equipe numa tela estreita (celular),
   **When** meus chamados está aberto, **Then** a área de trabalho
   é a tela principal; a navegação **não** fica o tempo todo
   ocupando uma coluna.
2. **Given** o desfecho do cenário 1, **When** a pessoa aciona o
   controle de menu, **Then** vê a mesma identidade (casa, marca,
   nome, Equipe, Sair) e o destino meus chamados.
3. **Given** o menu aberto no celular, **When** a pessoa escolhe um
   destino ou Sair, **Then** o overlay de navegação fecha e o
   trabalho (ou a tela de entrada, no caso de Sair) fica à frente.
4. **Given** o menu aberto no celular, **When** a pessoa aciona de
   novo o mesmo controle que abriu, ou toca na área de trabalho
   (o fundo, fora da navegação), **Then** o overlay fecha e a
   tela em que já estava permanece — sem mudar de destino.
5. **Given** recepção ou gestão num computador (tela larga),
   **When** o painel está aberto, **Then** a navegação permanece
   visível ao lado do conteúdo, sem precisar abrir por botão.

---

### User Story 4 - O simulador parece conversa e envia com Enter (Priority: P1)

Como recepção ou gestão demonstrando o produto, quero o simulador
com a mesma tipografia do restante do painel, balões distintos para
hóspede e hotel (os mesmos dois lados na Estadia), horário em cada
mensagem (só a hora no dia de hoje; data e hora se for de outro
dia), lista de conversas no
mesmo estilo de cartão das outras telas, e Enter para enviar
(Shift+Enter quebra linha), para o vídeo não mostrar a tela menos
cuidada do sistema.

**Why this priority**: É a tela que mais aparece no vídeo e a menos
cuidada hoje. Sem isto o redesenho da casca deixa o momento
principal da demonstração com cara de rascunho.

**Independent Test**: Pode ser testado na tela do simulador com
sessão de recepção: conferir tipografia alinhada ao painel, os
dois lados de balão e o horário nas mensagens (hora só, se for de
hoje; data e hora, se for de outro dia); na Estadia, os mesmos
balões com o rótulo de origem que já existe; Enter disparando o
envio no simulador e Shift+Enter inserindo quebra de linha sem
enviar.

**Acceptance Scenarios**:

1. **Given** o simulador aberto, **When** a pessoa olha o texto da
   tela, **Then** a tipografia é a mesma família do restante do
   painel autenticado (não uma serifa exclusiva desta tela).
2. **Given** uma conversa do simulador com mensagens dos dois lados
   registradas no mesmo dia de calendário em que a pessoa olha,
   **When** o histórico está visível, **Then** cada mensagem tem
   balão distinguível (hóspede × hotel) e o horário **só com hora e
   minuto** (por exemplo **14:32**), sem a data.
3. **Given** o campo de escrever no simulador focado, **When** a
   pessoa pressiona Enter, **Then** a mensagem é enviada como no
   clique do botão de enviar; **When** pressiona Shift+Enter,
   **Then** há uma quebra de linha e **não** há envio.
4. **Given** a lista de conversas do simulador, **When** há reservas
   listadas, **Then** cada uma aparece em cartão no mesmo espírito
   visual das listas já usadas no painel (fila, chamados), não como
   um bloco tipográfico à parte.
5. **Given** uma conversa do simulador (ou da Estadia) com uma
   mensagem registrada noutro dia de calendário, **When** o
   histórico está visível, **Then** essa mensagem mostra **data e
   hora** (por exemplo **02/09/2026 14:32**), não só `14:32` — a
   recepcionista distingue a reclamação de hoje da de anteontem.
6. **Given** o fio da Estadia com mensagem do hóspede, resposta da
   recepção e mensagem automática, **When** o histórico está
   visível, **Then** há só dois lados de balão (hóspede × hotel);
   recepção e automático ficam no lado do hotel; a procedência
   continua no rótulo de origem já entregue, não num terceiro
   estilo de balão.

---

### User Story 5 - Moeda e data no padrão brasileiro (Priority: P1)

Como qualquer perfil que lê o painel, quero valores em **R$ 0,00**
e datas em **02/09/2026**, para a tela não denunciar protótipo com
`0.00` e `2026-09-02`.

**Why this priority**: Aparece em várias telas e é o que mais
denuncia o estágio atual. Sem padronizar agora, cada tela nova
repete o inglês de máquina.

**Independent Test**: Pode ser testado abrindo telas que já mostram
preço, data de calendário ou instante (consumos, itens vendáveis,
painel da gestão, mercado, fila do dia, retenção, chamados) e
conferindo o formato brasileiro na **leitura**; e por um teste da
apresentação compartilhada com exemplos fixos (R$ 9,00, 02/09/2026,
02/09/2026 14:32, e nas bolhas a hora só ou data e hora conforme o
dia).

**Acceptance Scenarios**:

1. **Given** uma tela que mostra um valor em dinheiro ao ler
   (lista, total, histórico), **When** o valor é nove reais,
   **Then** o texto visível é **R$ 9,00** (não `9.00` nem `9,00`
   sem o símbolo).
2. **Given** uma tela que mostra uma data de calendário ao ler
   (check-in previsto, coleta só de dia), **When** a data é 2 de
   setembro de 2026, **Then** o texto visível é **02/09/2026**
   (não `2026-09-02`).
3. **Given** uma tela que mostra um instante (coleta de mercado,
   execução de retenção), **When** o momento é 2 de setembro de
   2026 às 10:00, **Then** o texto visível é **02/09/2026 10:00**
   (não `2026-09-02T10:00` nem só a data).
4. **Given** a lista de chamados ou a de consumos, **When** um
   item foi aberto há oito minutos num instante conhecido,
   **Then** o texto visível traz o instante **e** o decorrido, no
   espírito **02/09/2026 14:32 · há 8 min** — o “há 8 min” não
   some e não substitui o relógio.
5. **Given** o fio da conversa (simulador ou Estadia) com uma
   mensagem de hoje e outra de outro dia, **When** o histórico está
   visível, **Then** a de hoje mostra só **14:32** e a de outro dia
   mostra **02/09/2026 14:32**; nenhum dos dois usa “há 8 min”.
6. **Given** duas telas diferentes que mostram preço, **When** o
   mesmo valor aparece nas duas, **Then** a grafia é a mesma —
   uma única regra de apresentação, não uma por tela.
7. **Given** um campo nativo de data do navegador (cadastro de
   reserva, por exemplo), **When** a pessoa preenche a data,
   **Then** o controle continua no formato que o navegador exige;
   a regra brasileira vale para o que a tela **mostra como texto**,
   não para o valor interno do calendário.

---

### Edge Cases

- Nome da casa ausente ou em branco: a área do nome permanece
  visível sem inventar um nome; não quebra a casca.
- Funcionário de uma casa não vê o nome de outra casa na sessão.
- Tela estreita na recepção (janela redimensionada): o mesmo
  comportamento de menu por botão da equipe (abre, fecha pelo
  botão, pelo fundo, por destino ou Sair); o conteúdo da fila
  continua sendo a área principal.
- Grupo com um único item (equipe: só meus chamados): o rótulo
  Operação aparece, o item também.
- Simulador sem mensagens: a lista vazia e o campo de escrever
  permanecem; Enter com campo vazio não inventa mensagem.
- Valor monetário zero: **R$ 0,00**, não um traço nem `0.00`.
- Data incompleta ou ilegível na origem: não se inventa dia; o
  vazio já tratado na tela permanece vazio.
- Instante sem relógio utilizável: mostra a data de calendário;
  não inventa `00:00`.
- Chamado ou consumo sem instante de abertura: o decorrido que já
  existia continua; não se fabrica `02/09/2026 14:32` vazio.
- Mensagem de conversa no mesmo dia de calendário em que a pessoa
  olha: só hora e minuto (`14:32`), sem data.
- Mensagem de conversa noutro dia (a estadia atravessa meia-noite):
  data e hora (`02/09/2026 14:32`); não se omite o dia.
- Bolha de conversa MUST NOT usar o relativo de urgência (“há 8
  min”); esse complemento é só das listas de chamados e consumos.
- Mensagem automática e resposta da recepção no mesmo fio: mesmo
  lado de balão (hotel); o rótulo de origem já existente as
  distingue. Não se inventa um terceiro estilo.
- Sessão expirada: volta à entrada; nome da casa some com o resto
  dos dados da sessão (já é regra da casca).
- Destino Estadia ou Saída sem reserva na rota: o estado vazio já
  existente (apontar para a fila) permanece; o item continua no
  menu como lugar, não como ação de criar.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Em tela larga, a navegação autenticada MUST ocupar uma
  coluna permanente ao lado do conteúdo, em altura inteira, no
  lugar da faixa de itens no topo.
- **FR-002**: Em tela estreita, a navegação MUST abrir por um
  controle explícito e MUST não permanecer como coluna fixa; a área
  de trabalho (em especial meus chamados da equipe) MUST continuar
  utilizável.
- **FR-002a**: Com a navegação estreita aberta, ela MUST fechar ao
  acionar de novo o mesmo controle, ao tocar na área de trabalho
  (fundo, fora da navegação), e ao escolher um destino ou Sair.
  Fechar pelo controle ou pelo fundo MUST NOT mudar o destino
  corrente.
- **FR-003**: O topo da navegação MUST mostrar o nome da casa da
  sessão em destaque.
- **FR-004**: Logo abaixo do nome da casa, a navegação MUST mostrar
  a marca **OmniStay** em tom discreto.
- **FR-005**: O rodapé da navegação MUST mostrar o nome da pessoa
  autenticada, o rótulo do perfil e o controle **Sair**.
- **FR-006**: Os rótulos de perfil visíveis MUST ser **Recepção**,
  **Gestão** e **Equipe**, nesta ordem de papéis já existentes.
- **FR-007**: A entrada bem-sucedida e a consulta da sessão
  corrente MUST incluir o nome da casa da propriedade ligada ao
  identificador de hotel da sessão, além dos dados de pessoa e
  perfil que já devolvem.
- **FR-008**: O nome da casa na sessão MUST vir da propriedade
  daquela sessão; MUST NOT vazar nome de outra casa.
- **FR-009**: Os destinos permitidos ao perfil MUST aparecer
  agrupados em **Operação**, **Propriedade** e **Gestão**, quando
  houver item; o **Simulador** MUST ficar separado, no fim, para
  quem pode usá-lo.
- **FR-010**: Um grupo sem nenhum destino permitido ao perfil MUST
  NOT mostrar o rótulo do grupo.
- **FR-011**: A composição de quem vê cada destino MUST permanecer
  a da matriz já entregue (recepção, equipe, gestão); esta fatia
  MUST NOT abrir tela que o perfil já não podia usar.
- **FR-012**: **Nova reserva** MUST NOT aparecer como item de menu.
  O botão na fila do dia MUST permanecer como o único caminho de
  menu/ação para cadastrar reserva.
- **FR-013**: Estadia e Saída do hóspede MUST permanecer como
  destinos de menu da recepção (são lugares, não o ato de criar).
  Meus chamados MUST permanecer o destino de menu da equipe.
- **FR-014**: No simulador, a tipografia MUST ser a mesma família
  do restante do painel autenticado.
- **FR-015**: No campo de mensagem do simulador, Enter MUST enviar
  e Shift+Enter MUST quebrar linha sem enviar.
- **FR-016**: Mensagens do simulador e da Estadia MUST ter balões
  distintos em **dois** lados (hóspede × hotel). Resposta da
  recepção e mensagem automática MUST usar o lado do hotel.
  MUST NOT haver um terceiro estilo de balão para distinguir
  automático de recepção: essa procedência MUST permanecer no
  rótulo de origem já entregue.
- **FR-016a**: Em cada bolha da conversa (simulador e Estadia), o
  horário visível MUST ser só hora e minuto (por exemplo **14:32**)
  quando a mensagem é do mesmo dia de calendário em que a pessoa
  olha; MUST ser data e hora (por exemplo **02/09/2026 14:32**)
  quando é de outro dia. MUST NOT usar o relativo “há 8 min” na
  bolha.
- **FR-017**: A lista de conversas do simulador MUST usar o mesmo
  espírito de cartão das outras listas do painel.
- **FR-018**: Todo valor monetário **lido** no painel (lista, total,
  histórico) MUST aparecer no padrão brasileiro com cifrão, por
  exemplo **R$ 9,00**.
- **FR-019**: Toda data de calendário **lida** no painel MUST
  aparecer como dia/mês/ano com dois dígitos no dia e no mês, por
  exemplo **02/09/2026**.
- **FR-019a**: Todo instante **lido** no painel **fora das bolhas
  de conversa** (coleta, execução de retenção, abertura de chamado
  ou consumo) MUST aparecer como data e hora, por exemplo
  **02/09/2026 14:32**, sem o formato `2026-09-02T14:32`. O horário
  da bolha segue FR-016a.
- **FR-019b**: Nas listas de chamados e de consumos, o tempo
  decorrido já visível (“há 8 min”) MUST permanecer ao lado do
  instante, no espírito **02/09/2026 14:32 · há 8 min**. MUST NOT
  substituir o instante pelo só relativo, nem o relativo pelo só
  instante.
- **FR-020**: A grafia de moeda, de data de calendário e de
  instante operacional MUST ser a mesma em todas as telas que as
  exibem (uma regra compartilhada, verificada por teste da própria
  apresentação). O horário da bolha segue FR-016a, não FR-019a.
- **FR-021**: Campos nativos de data do navegador MUST conservar o
  valor que o controle exige; FR-019 aplica-se ao texto visível, não
  ao valor interno do calendário.
- **FR-022**: Os fluxos já cobertos pelas telas autenticadas
  (entrada, fila, reserva, Estadia, chamados, consumos, catálogo,
  recado, painel, mercado, usuários, retenção, simulador) MUST
  continuar completáveis; testes de tela que descreviam o formato
  antigo de moeda ou data MUST passar a esperar o formato
  brasileiro, sem mudar o cenário que cobrem.
- **FR-023**: A casca nova (lateral, grupos, identidade, ausência
  de Nova reserva no menu, menu estreito) MUST ter cobertura de
  teste própria, além de manter verdes os testes de tela já
  existentes depois do ajuste de formato.

### Key Entities

- **Sessão corrente**: já identifica pessoa, perfil, casa
  (`id_hotel`) e validade. Nesta fatia passa a carregar também o
  **nome da casa**, lido da propriedade daquela sessão, para a
  casca exibir sem adivinhar.
- **Destino de navegação**: um lugar do painel (título, caminho,
  perfis que o veem). Não inclui a ação "Nova reserva".
- **Grupo de menu**: rótulo de área (Operação, Propriedade, Gestão)
  que só existe na tela se houver ao menos um destino visível;
  Simulador não é um desses três — fica à parte no fim.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Numa tela de balcão (computador), a pessoa autenticada
  vê todos os destinos do próprio perfil sem a navegação estourar
  para os lados nem cobrir o título da tela de trabalho.
- **SC-002**: Numa tela de telefone, a pessoa da equipe chega a
  meus chamados e opera a lista sem a navegação ocupar o turno
  inteiro; abre o menu e fecha em um gesto (o mesmo botão ou o
  toque no fundo), sem ser obrigada a escolher outro destino.
- **SC-003**: Qualquer um dos três perfis identifica, sem abrir
  outra tela, o nome da casa, que o produto é OmniStay, o próprio
  nome e o papel (Recepção, Gestão ou Equipe).
- **SC-004**: A recepção cadastra reserva a partir da fila do dia,
  não a partir de um segundo item de menu com o mesmo nome.
- **SC-005**: Quem demonstra o simulador envia mensagem com Enter,
  quebra linha com Shift+Enter, e distingue hóspede de hotel pelos
  dois lados de balão; o fio da Estadia usa os mesmos dois lados,
  com o rótulo de origem já existente para automático × recepção;
  o horário da bolha é só a hora no dia corrente e data e hora
  quando a mensagem é de outro dia.
- **SC-006**: Em amostragem das telas que já mostram preço, data
  ou instante, nenhum valor lido permanece no formato `0.00` ou
  `2026-09-02`; calendário aparece `02/09/2026`, instante
  `02/09/2026 14:32`, nas listas de chamados e consumos o decorrido
  continua visível junto do instante, e nas bolhas de conversa a
  mensagem de hoje não carrega a data.
- **SC-007**: Depois da mudança, os fluxos já testados das telas
  existentes continuam passando (cenário igual; só muda a
  expectativa de grafia quando a tela passou a mostrar moeda ou
  data em português).

## Assumptions

- Uma fatia só: casca, agrupamento, simulador e formato brasileiro
  saem juntos, porque fatiar multiplicaria retrabalho na mesma
  camada.
- **Só Nova reserva** sai do menu pelo critério "ação, não lugar".
  Estadia e Saída permanecem: são destinos (com estado vazio já
  existente quando falta a reserva na rota). Não se remove item que
  a lista de ajustes não nomeou.
- Composição dos grupos (recepção): Operação = fila do dia,
  Estadia, chamados e pedidos, consumos a lançar, saída do hóspede;
  Propriedade = catálogo, itens vendáveis, recado de boas-vindas;
  Simulador no fim. A lista original de ajustes não citava Estadia
  porque ainda se chamava ficha; o destino **Estadia** da F7.6 entra
  em Operação.
- Composição (gestão): Propriedade = os três destinos que a gestão
  já lê; Gestão = painel, mercado, usuários, retenção; Simulador no
  fim.
- Composição (equipe): só Operação / meus chamados.
- Largura "estreita" = uso em telefone ou janela equivalente, em
  que uma coluna permanente de navegação prejudicaria o trabalho.
  Larga = computador de balcão.
- Horário nas bolhas (simulador e Estadia): hora e minuto no fuso
  em que a tela já apresenta o restante do painel; sem segundos.
  “Mesmo dia” / “outro dia” é o dia de calendário desse relógio,
  não uma janela de 24 horas.
- Moeda: símbolo **R$**, dois decimais, vírgula decimal, ponto de
  milhar quando o valor passar de 999.
- Instante operacional (fora da bolha): `02/09/2026 14:32` (hora e
  minuto, sem segundos). Data de calendário sem relógio:
  `02/09/2026`. Bolha: `14:32` no dia corrente; `02/09/2026 14:32`
  noutro dia.
- Nas listas de chamados e de consumos (recepção, equipe e
  consumos a lançar), o relativo de urgência já existente permanece
  como complemento do instante, separado por ponto mediano.
- A apresentação compartilhada de moeda e data é a mesma regra em
  todo o painel autenticado; testes de unidade dessa regra
  substituem cópia da lógica em cada tela.
- Campos de **digitação** de preço podem continuar aceitando o
  número que a pessoa já digita hoje; o que FR-018 exige é o valor
  **lido** (tabela, cartão, total).
- O nome da casa já existe no cadastro da propriedade; não há
  tela nova para editá-lo aqui.
- Não se altera a matriz de operações nem se criam destinos novos.
- Enter no simulador envia; Enter na Estadia **não** envia (já
  decidido na F7.6 — o gesto lá é o botão). As duas telas não
  unificam o atalho.
- O fio da Estadia entra nesta fatia só na cara da conversa
  (dois lados de balão + horário). Os rótulos de origem, a janela
  de 24h e o envio pelo botão permanecem os da F7.6.

## Out of Scope

- Trocar a matriz de permissões ou criar perfil novo.
- Módulos ligados/desligados por propriedade (F7.4).
- Canal de e-mail (F7.5).
- Redesenho interno de cada formulário (campos da ficha, catálogo,
  usuários) além de casca, agrupamento, cara da conversa
  (simulador e Estadia), e formato de moeda/data.
- Terceiro estilo de balão para automático × recepção.
- Integração com o sistema de gestão do hotel.
- Tema escuro em tela cheia; o fundo escuro, se houver, é da
  coluna de navegação.
- Envio com Enter em qualquer tela que não seja o simulador.
- Relógio, idioma ou moeda configuráveis por hotel.
