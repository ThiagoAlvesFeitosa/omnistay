# Feature Specification: Catálogo, itens vendáveis e recado de boas-vindas

**Feature Branch**: `034-catalogo-vendaveis-recado`

**Created**: 2026-09-01

**Status**: Draft

**Input**: User description: "A recepção mantém o catálogo da
propriedade organizado por categoria — horários, cardápio, serviços,
programação e regras —, cadastra e ajusta os itens vendáveis com
seus preços, e edita os quatro campos do recado de boas-vindas:
café, wi-fi, horário de saída e a linha de convite. Itens do
catálogo e itens vendáveis são desativados em vez de apagados, e
item desativado deixa de ser considerado pelo atendimento
automático. Valor recusado pela regra de formato é avisado no
momento de salvar, não no momento de enviar."
(backlog F8.6)

Restrições já decididas no projeto (entrada do specify): esta fatia
**não altera o comportamento já entregue fora das telas** — catálogo
por categoria, item vendável com preço próprio, recado de quatro
campos, desativar sem apagar, item inativo fora do atendimento
automático e recusa de formato ao gravar **já existem** (F2.1, F2.2,
F3.7, F7.3); a casca já nomeia **Catálogo**, **Itens vendáveis** e
**Recado de boas-vindas** (F8.1), hoje só com título; recepção
edita; gestão apenas lê; perfil operacional recebe recusa; preço de
item vendável é campo próprio, editado sem reescrever texto; os
campos de boas-vindas recusam quebra de linha, tabulação e mais de
quatro espaços seguidos; só a tela da equipe é pensada para celular
— estas três são de computador; o que a autorização recusa, a tela
não oferece; rótulos do recado (café, wi-fi, saída, convite)
permanecem congelados — a casa edita o conteúdo de cada linha, não
quais linhas existem; o aviso de assistente virtual continua texto
fixo do produto, não editável aqui; o sistema **não** se integra ao
sistema de gestão do hotel; conteúdo de mensagem, senha e
identificador de sessão continuam fora do log. Painel da gestão
(indicadores, mercado, usuários, retenção) permanece em F8.7.
Personalidade da assistente permanece fora desta fatia.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manter o catálogo por categoria, sem apagar (Priority: P1)

Como recepcionista no computador do balcão, quero abrir **Catálogo**,
ver os fatos da casa agrupados em horários, cardápio, serviços,
programação e regras, criar e corrigir um item (título e conteúdo) e
desativá-lo quando deixar de valer — nunca apagá-lo — para o hotel
atualizar o que afirma sem perder o histórico e sem o atendimento
automático continuar falando o que já retirou.

**Why this priority**: Sem esta tela, configurar o que a assistente
pode afirmar continua sendo trabalho fora do painel. É o primeiro
critério de aceite da fatia e o depósito visível de controle de
alucinação.

**Independent Test**: Pode ser testado autenticando como recepção
numa propriedade com itens ativos e inativos em categorias distintas,
abrindo Catálogo, conferindo o agrupamento pelas cinco categorias,
criando um item na categoria visível, editando título e conteúdo,
desativando e reativando, e conferindo que não existe caminho de
apagamento e que o inativo permanece visível na manutenção, marcado
como desativado.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção e itens de catálogo da própria
   propriedade em mais de uma das cinco categorias, **When** a
   pessoa abre Catálogo, **Then** vê os itens organizados pelas
   categorias horários, cardápio, serviços, programação e regras,
   cada um com título, conteúdo e situação distinguível (ativo ou
   desativado).
2. **Given** a categoria visível no momento, **When** a recepção
   cadastra um item com título e conteúdo visíveis, **Then** o item
   nasce ativo naquela categoria e aparece na lista seguinte.
3. **Given** um item ativo da própria casa, **When** a recepção
   altera título e/ou conteúdo e confirma, **Then** a lista seguinte
   mostra o texto novo e o item permanece ativo.
4. **Given** um item ativo, **When** a recepção o desativa, **Then**
   ele permanece na manutenção marcado como desativado, sem
   desaparecer, e a tela não oferece apagar.
5. **Given** um item desativado, **When** a recepção o reativa,
   **Then** ele volta a aparecer como ativo, com o conteúdo que
   tinha ao ser reativado.
6. **Given** título ou conteúdo em branco ou só com espaços, ou
   tentativa de categoria fora das cinco, **When** a recepção tenta
   salvar, **Then** o item não é gravado e o aviso aparece na hora,
   nesta tela — não depois, no atendimento ao hóspede.

---

### User Story 2 - Cadastrar e ajustar item vendável pelo preço próprio (Priority: P1)

Como recepcionista, quero abrir **Itens vendáveis**, cadastrar o que
o hotel cobra pelo chat e corrigir o preço num campo só dele — sem
reescrever o nome para mudar o valor — e desativar o que saiu de
linha, para o valor informado ao hóspede ser o mesmo que a casa
cobrará, e nunca um número inventado pelo atendimento automático.

**Why this priority**: Preço em texto corrido é o modo de o número
informado divergir do cobrado. Campo próprio é critério de aceite
explícito da fatia.

**Independent Test**: Pode ser testado autenticando como recepção,
criando um item com nome e preço, alterando só o preço, desativando e
reativando, tentando preço negativo e nome duplicado entre ativos, e
conferindo recusa visível ao salvar, sem caminho de apagamento.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção, **When** a pessoa abre Itens
   vendáveis, **Then** vê os itens da própria casa — ativos e
   desativados — cada um com nome, preço atual e situação
   distinguível.
2. **Given** nome visível e preço válido (zero ou positivo),
   **When** a recepção cadastra, **Then** o item nasce ativo e o
   preço aparece no campo próprio, separado do nome.
3. **Given** um item ativo, **When** a recepção altera só o preço e
   confirma, **Then** a lista seguinte mostra o preço novo e o nome
   permanece o mesmo, sem a pessoa ter reescrito o texto do item
   para mudar o valor.
4. **Given** um item ativo, **When** a recepção o desativa, **Then**
   ele permanece na lista marcado como desativado; a tela não
   oferece apagar.
5. **Given** um item desativado, **When** a recepção o reativa,
   **Then** ele volta a aparecer como ativo, com o preço que tinha.
6. **Given** preço negativo, nome em branco ou nome já usado por
   outro item ativo da casa, **When** a recepção tenta salvar,
   **Then** a gravação é recusada e o aviso aparece nesta tela, no
   momento de salvar.

---

### User Story 3 - Editar os quatro campos do recado, com recusa na hora (Priority: P1)

Como recepcionista, quero abrir **Recado de boas-vindas** e editar
os quatro campos da casa — café, wi-fi, horário de saída e a linha
de convite — sabendo na hora se o texto será recusado pelo formato,
para o erro aparecer para quem pode corrigir e não coincidir com o
envio ao hóspede.

**Why this priority**: Validar só no envio faz a falha aparecer
quando o hóspede já chegou. Critério de aceite da fatia e decisão
já registrada no recado curto.

**Independent Test**: Pode ser testado autenticando como recepção,
lendo os quatro campos já gravados, salvando um conjunto válido,
tentando cada recusa de formato (quebra de linha, tabulação, mais
de quatro espaços seguidos, vazio) e conferindo que o aviso aparece
ao salvar, o valor anterior permanece, e nenhum recado é disparado
por esta tela.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção, **When** a pessoa abre Recado
   de boas-vindas, **Then** vê os quatro campos — café, wi-fi,
   horário de saída e linha de convite — com os valores atuais da
   propriedade, cada um em uma linha, sem poder acrescentar ou
   remover campo.
2. **Given** os quatro campos com texto visível e formato aceito,
   **When** a recepção salva, **Then** a leitura seguinte devolve
   os mesmos textos (espaços só nas extremidades podem ter sido
   removidos) e o aviso de sucesso é desta tela, não de um envio
   ao hóspede.
3. **Given** um campo com quebra de linha, com tabulação, com mais
   de quatro espaços seguidos, vazio ou só espaços, **When** a
   recepção tenta salvar, **Then** a gravação é recusada na hora,
   o valor anterior permanece, e o aviso deixa claro o que foi
   recusado — sem esperar o envio ao hóspede.
4. **Given** esta tela, **When** a recepção olha os rótulos,
   **Then** continua vendo café, wi-fi, horário de saída e convite;
   não há como trocar o nome de um campo nem incluir o aviso de
   assistente virtual como texto editável.
5. **Given** um recado já enviado a um hóspede, **When** a recepção
   altera e salva os campos, **Then** nenhum segundo recado de
   chegada nasce por causa deste salvamento; o texto novo vale para
   chegadas seguintes (o envio continua sendo o clique de confirmar
   chegada, já existente).

---

### User Story 4 - Gestão lê; equipe operacional nem chega à tela (Priority: P1)

Como responsável pelos fatos da casa, quero que a gestão consulte
catálogo, itens vendáveis e recado sem poder alterar, e que o perfil
operacional seja recusado nos três destinos — sem dado da
propriedade e sem tela em branco — para a minimização e a matriz de
papéis valerem também no painel.

**Why this priority**: Critério de aceite explícito. Tela que oferece
o que a autorização recusa ensina o funcionário a tentar o caminho
errado.

**Independent Test**: Pode ser testado autenticando gestão e abrindo
os três destinos (leitura visível, sem controles de gravar,
desativar ou criar); autenticando perfil operacional e tentando os
três endereços (recusa sem conteúdo e sem pedido de manutenção); e
confirmando que a recepção vê os controles de edição.

**Acceptance Scenarios**:

1. **Given** uma sessão de gestão, **When** a pessoa abre Catálogo,
   Itens vendáveis ou Recado de boas-vindas, **Then** lê o conteúdo
   da própria propriedade e não vê criar, editar, desativar,
   reativar nem salvar.
2. **Given** a mesma sessão de gestão, **When** tenta gravar pelo
   que a tela não oferece, **Then** nada é alterado — a tela não
   apresenta o controle; se o endereço for forçado, a recusa já
   existente da autorização vale e o valor anterior permanece.
3. **Given** uma sessão de perfil operacional, **When** tenta abrir
   qualquer um dos três destinos, **Then** é recusada sem ver item
   de catálogo, preço, recado nem tela vazia, e a tela não dispara
   a consulta de manutenção.
4. **Given** o menu, **When** cada perfil autenticado o inspeciona,
   **Then** recepção e gestão vêem os três destinos; o perfil
   operacional não vê nenhum dos três.

---

### User Story 5 - Item desativado some do atendimento, não do histórico (Priority: P2)

Como recepcionista que tirou um fato ou um preço de linha, quero
confirmar na própria tela que desativar é o caminho — e que o item
inativo deixa de ser o que o atendimento automático considera —
sem a ilusão de que apaguei o passado.

**Why this priority**: Fecha o critério “item desativado deixa de
ser considerado pelo atendimento automático” na superfície que a
recepção usa. O comportamento no atendimento já existe; esta
história garante que a tela não oferece atalho que o contradiga.

**Independent Test**: Pode ser testado desativando um fato de
catálogo e um item vendável pela tela, conferindo a marca de
desativado na manutenção, a ausência de apagar, e que a consulta
já usada pelo atendimento (catálogo ativo / itens vendáveis ativos)
omite os dois — sem esta fatia redefinir essa consulta.

**Acceptance Scenarios**:

1. **Given** um fato de catálogo ativo visível em Catálogo, **When**
   a recepção o desativa nesta tela, **Then** ele some da fonte que
   o atendimento automático já usa para afirmar fato, e continua
   visível na manutenção desta tela como desativado.
2. **Given** um item vendável ativo, **When** a recepção o desativa
   nesta tela, **Then** ele deixa de entrar na identificação de
   pedido cobrado já existente, e continua visível na manutenção
   como desativado.
3. **Given** qualquer item de catálogo ou vendável, **When** a
   recepção procura apagar, **Then** o controle não existe.

---

### Edge Cases

- Catálogo ou itens vendáveis sem nenhum cadastro: lista vazia
  honesta, distinta de falha ao ler.
- Categoria visível sem itens, havendo itens em outra: a categoria
  da vez mostra vazio; as demais continuam alcançáveis.
- Item de catálogo desativado: a linha oferece reativar; não oferece
  apagar. Edição de título e conteúdo nesta tela é dos itens ativos
  (Editar na linha ativa).
- Item vendável desativado: a linha oferece reativar; preço e nome
  da linha ativa continuam editáveis pelo controle de editar.
- Reativar item vendável cujo nome já está em uso por outro ativo da
  casa: recusa visível ao salvar; o item permanece desativado.
- Um dos quatro campos de boas-vindas inválido e os outros válidos:
  nada é gravado; os quatro valores anteriores permanecem.
- Quatro espaços seguidos num campo de boas-vindas: aceitos. Cinco
  ou mais: recusados ao salvar.
- Falha ao ler: estado distinto de lista vazia; a tela não finge
  que a casa não tem catálogo, preço nem recado.
- Falha ao salvar: o estado anterior permanece visível; o aviso não
  é apresentado como “enviado ao hóspede”.
- Sessão de outro hotel: nenhum item nem recado alheio aparece.
- Perfil operacional no computador (não só no celular): os três
  destinos continuam recusados; o recorte não muda por tamanho de
  tela.
- Recepção ou gestão no celular: as três telas funcionam, mas esta
  fatia não promete layout de mão.
- Aviso de assistente virtual e nome do hóspede: não são campos
  desta tela. A tela não inventa prévia com nome de hóspede.
- Mapa de telas com coluna “descrição” no item vendável: o recurso
  já existente não tem esse campo. Esta fatia não o cria.

## Requirements *(mandatory)*

### Functional Requirements

**Catálogo**

- **FR-001**: A recepção DEVE poder abrir Catálogo e ver os fatos da
  própria propriedade, ativos e desativados, organizados nas cinco
  categorias: horários, cardápio, serviços, programação e regras.
- **FR-002**: Cada item na lista DEVE mostrar título, conteúdo e
  situação distinguível (ativo ou desativado).
- **FR-003**: A recepção DEVE poder criar item na categoria visível,
  com título e conteúdo obrigatórios e com texto visível. Item novo
  DEVE nascer ativo.
- **FR-004**: A recepção DEVE poder editar título e conteúdo de item
  ativo da própria casa. A tela NÃO DEVE oferecer trocar a categoria
  de um item já gravado.
- **FR-005**: A recepção DEVE poder desativar e reativar item da
  própria casa. A tela NÃO DEVE oferecer remoção permanente.
- **FR-006**: Contagem visível DEVE distinguir quantos itens da
  categoria (ou da lista apresentada) estão ativos e quantos
  desativados, sem inventar número.

**Itens vendáveis**

- **FR-007**: A recepção DEVE poder abrir Itens vendáveis e ver os
  itens da própria propriedade, ativos e desativados, cada um com
  nome, preço atual em campo próprio e situação distinguível.
- **FR-008**: A recepção DEVE poder cadastrar item vendável com nome
  e preço (zero ou positivo). Item novo DEVE nascer ativo. A tela
  NÃO DEVE exigir reescrever o nome para informar o preço.
- **FR-009**: A recepção DEVE poder alterar o preço atual sem
  alterar o nome, e alterar o nome sem alterar o preço, em campos
  separados.
- **FR-010**: A recepção DEVE poder desativar e reativar item
  vendável. A tela NÃO DEVE oferecer remoção permanente.
- **FR-011**: A tela NÃO DEVE apresentar campo de descrição de item
  vendável que o recurso existente não possui.

**Recado de boas-vindas**

- **FR-012**: A recepção DEVE poder abrir Recado de boas-vindas e
  ver os quatro campos atuais da propriedade: café, wi-fi, horário
  de saída e linha de convite.
- **FR-013**: A recepção DEVE poder salvar os quatro campos de uma
  vez. Salvamento bem-sucedido NÃO DEVE disparar recado ao hóspede.
- **FR-014**: Quebra de linha, tabulação, mais de quatro espaços
  seguidos, vazio ou só espaços em qualquer um dos quatro campos
  DEVE recusar o salvamento na hora, nesta tela, com aviso claro do
  que foi recusado. O valor anterior DEVE permanecer.
- **FR-015**: Quatro espaços seguidos DEVEM ser aceitos. A tela NÃO
  DEVE recusar o que a gravação já existente aceita, nem aceitar o
  que ela recusa.
- **FR-016**: A tela NÃO DEVE permitir acrescentar, remover ou
  renomear campo do recado. O aviso de assistente virtual NÃO DEVE
  ser editável nesta tela.

**Recusa visível ao salvar**

- **FR-017**: Toda recusa de formato, campo obrigatório, preço
  inválido ou nome duplicado entre itens vendáveis ativos DEVE
  aparecer no momento de salvar, na tela em que a pessoa gravou.
  NÃO DEVE ser adiada ao envio de mensagem ao hóspede nem ao
  atendimento automático.
- **FR-018**: Lista vazia e falha ao ler DEVEM ser estados
  distintos. Falha NÃO DEVE ser apresentada como “a casa não tem
  catálogo / item / recado”.

**Perfis, dispositivo e honestidade**

- **FR-019**: Gestão DEVE poder abrir os três destinos e ler o
  conteúdo da própria propriedade. NÃO DEVE ver criar, editar,
  desativar, reativar nem salvar.
- **FR-020**: Perfil operacional NÃO DEVE ver os três destinos no
  menu. Tentativa pelo endereço DEVE ser recusada sem conteúdo e
  sem disparar a consulta de manutenção.
- **FR-021**: Recepção DEVE ver os três destinos no menu, com os
  controles de edição. Gestão DEVE ver os três destinos no menu,
  só para leitura. O que o perfil não pode usar NÃO DEVE aparecer
  como ação na tela.
- **FR-022**: As três telas NÃO DEVEM usar o recorte compacto da
  equipe no celular. São telas de computador.
- **FR-023**: Toda leitura e toda gravação DEVEM considerar a
  propriedade do funcionário. Sessão de um hotel NÃO DEVE mostrar
  nem alterar item ou recado de outro.

**Fora desta fatia**

- **FR-024**: Esta fatia NÃO DEVE alterar regra de catálogo ativo,
  identificação de item vendável, valor praticado já gravado,
  disparo ou recuperação do recado de chegada, confirmação de
  chegada ou saída, fila do dia, personalidade da assistente,
  prazo de sessão nem matriz de permissões. DEVE reusar as
  operações já existentes; NÃO DEVE criar recurso novo de
  manutenção.
- **FR-025**: Esta fatia NÃO DEVE integrar-se ao sistema de gestão
  do hotel, NÃO DEVE lançar consumo e NÃO DEVE responder pergunta
  de hóspede a partir da tela.
- **FR-026**: Log desta fatia NÃO DEVE registrar senha, conteúdo de
  mensagem de hóspede, texto completo do fato, preço como texto
  livre nem identificador de sessão apresentado ao cliente. PODE
  registrar identificador de usuário, de item, perfil e código de
  recusa.

### Key Entities

- **Catálogo**: tela da recepção (leitura da gestão) com os fatos
  da propriedade por categoria. Única fonte que o atendimento
  automático já usa para afirmar. Não é a lista de itens cobrados.
- **Categoria**: um de cinco valores fechados — horários, cardápio,
  serviços, programação, regras. Não há categoria livre.
- **Item de catálogo**: fato com título, conteúdo e situação
  (ativo ou desativado). Desativar retira da fonte do atendimento;
  não apaga.
- **Itens vendáveis**: tela da recepção (leitura da gestão) com o
  que a casa cobra pelo chat. Fonte do preço vigente. Distinta do
  catálogo de fatos.
- **Item vendável**: nome, preço atual em campo próprio e situação.
  Desativar retira da identificação de pedido cobrado; não apaga;
  não altera valor já praticado em pedido antigo.
- **Recado de boas-vindas**: tela da recepção (leitura da gestão)
  com os quatro campos da casa. Salvar configura; não envia.
- **Campos do recado**: café, wi-fi, horário de saída e linha de
  convite. Uma linha cada. Rótulos congelados. Formato recusado ao
  salvar, não ao enviar.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A recepção conclui, em uma visita ao painel, criar ou
  corrigir um fato de catálogo, um item vendável com preço próprio
  e os quatro campos do recado, sem sair do sistema e sem passo
  fora da tela.
- **SC-002**: 100% das tentativas de apagar item de catálogo ou
  item vendável pela tela falham por ausência do controle — o
  caminho visível é desativar.
- **SC-003**: Depois de desativar pela tela, 100% desses itens
  deixam de ser considerados pelo atendimento automático já
  existente (fato inativo fora do catálogo ativo; item vendável
  inativo fora da identificação de pedido cobrado).
- **SC-004**: 100% das recusas de formato dos campos de
  boas-vindas aparecem ao salvar nesta tela, com o valor anterior
  intacto, e 0% coincidem com o instante de envio ao hóspede.
- **SC-005**: Em 100% das sessões de gestão, as três telas mostram
  o conteúdo e nenhum controle de alteração; em 100% das sessões
  operacionais, os três destinos são recusados sem conteúdo.
- **SC-006**: Alterar o preço de um item vendável pela tela não
  exige reescrever o nome: o valor vive em campo próprio em 100%
  dos casos de edição de preço.
- **SC-007**: Cada critério de aceite da fatia F8.6 do backlog tem
  ao menos um cenário nesta spec, exercitável na tela.

## Assumptions

- **Só tela nesta fatia.** As operações de manutenção, a omissão
  do inativo no atendimento automático e a recusa de formato ao
  gravar já existem. Esta fatia as torna visíveis no painel e
  mostra o aviso no momento de salvar. Não reabre F2.1, F2.2,
  F3.7 nem F7.3.
- **Três destinos, não uma tela só.** A casca já nomeia Catálogo,
  Itens vendáveis e Recado de boas-vindas. Esta fatia preenche os
  três, no lugar do título sozinho.
- **Gestão no menu.** A casca hoje lista os três destinos só para
  recepção. “Gestão apenas lê” só é alcançável se a gestão vir os
  destinos e abrir em modo leitura. Esta fatia acrescenta os três
  ao menu da gestão, sem controles de edição. Perfil operacional
  continua sem eles. Não é F8.7 (indicadores, mercado, usuários,
  retenção).
- **Mapa de telas vs recurso existente.** O rascunho mostra
  “descrição” na lista de itens vendáveis. O cadastro já entregue
  tem nome, preço e situação — não descrição. Esta fatia segue o
  recurso existente e não inventa o campo (Artigo XI e a restrição
  de não alterar o comportamento já entregue fora das telas).
- **Categoria na criação.** Item novo de catálogo nasce na
  categoria que a pessoa está vendo. Trocar categoria depois
  continua fora, como na manutenção já entregue.
- **Prévia com nome de hóspede fica fora.** O rascunho ilustra o
  recado com um nome. Esta fatia não monta mensagem fictícia nem
  dispara envio. Os quatro campos rotulados bastam.
- **Campo vazio no recado continua bloqueando o envio na chegada**,
  com sinalização já existente na fila do dia. Esta tela só grava;
  não reabre a recuperação das boas-vindas.
- **Consumos já lançados não mudam de valor** quando o preço atual
  é reajustado nesta tela — retrato já gravado na F3.7.
- **Personalidade da assistente, módulos por propriedade e canal
  de e-mail** permanecem fora.
- **Testes desta fatia exercitam a tela** (o que cada perfil vê e
  o aviso ao salvar). Não reescrevem a suíte do atendimento
  automático; SC-003 aproveita o comportamento já coberto lá,
  visível depois da desativação feita pela tela.
