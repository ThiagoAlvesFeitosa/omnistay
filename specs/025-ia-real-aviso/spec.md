# Feature Specification: IA real e aviso de assistente virtual

**Feature Branch**: `025-ia-real-aviso`

**Created**: 2026-08-26

**Status**: Draft

**Input**: User description: "O sistema conversa com um serviço de modelo de linguagem
real para classificar mensagens e redigir respostas, no lugar da implementação falsa
que hoje o worker utiliza. Escolher entre o serviço real e o falso é configuração,
não mudança de código. Falha, demora excessiva ou resposta em formato inválido do
serviço não perdem a mensagem: ela segue para atendimento humano, como já acontece
hoje. A primeira mensagem de cada estadia informa ao hóspede que o atendimento
inicial é feito por uma assistente virtual e que uma pessoa da recepção assume
quando necessário. Esse aviso é texto fixo do produto, não configurável pela
propriedade."
(backlog F7.1 + aviso de assistente virtual da F7.2)

Restrições já decididas no projeto (entrada do specify): a porta de modelo de
linguagem e o adaptador controlado já existem — esta fatia acrescenta o adaptador
real e a escolha por configuração do ambiente, no mesmo molde da escolha do canal
de mensageria; a chave de acesso vem do ambiente, nunca de arquivo versionado, e
nunca aparece em log; nenhum teste chama o serviço real nem depende de rede;
conteúdo de mensagem de hóspede continua fora do log; na dúvida um humano vê;
gravar vem antes de enviar; o sistema não se integra ao sistema de gestão do
hotel. Personalidade configurável pela propriedade e linha de convite no recado
de boas-vindas permanecem fora.

## Clarifications

### Session 2026-08-26

- Q: Com o ambiente em modo de inteligência real, o serviço de linguagem
  precisa dar resultado útil em todos os usos já existentes (ficha, intenção,
  resposta pelo catálogo, item vendável e pesquisa de saída), ou só em
  classificar a mensagem e redigir a resposta? → A: Todos os usos já existentes
  passam pelo serviço real e precisam de resultado útil. Se o dia apertar,
  classificar, responder e extrair ficha são os três da jornada de
  demonstração e levam o refinamento; identificar item vendável e pesquisa de
  saída podem ficar com prompt menos refinado, porque a falha já cai em humano
  por construção das fatias anteriores — não é comportamento novo.
- Q: Se o modo de inteligência estiver ausente, for desconhecido, ou o modo
  real estiver sem chave de acesso, o processamento inteiro deixa de subir,
  ou só o trabalho que precisa do cérebro falha? → A: O processamento recusa
  subir: modo ausente, desconhecido, ou real sem chave impedem qualquer
  trabalho daquele ambiente. Sem queda silenciosa para o adaptador
  controlado. Testes injetam o adaptador e não passam por essa recusa.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A conversa pensa de verdade (Priority: P1)

Como hóspede já hospedado — e como quem demonstra o sistema — quero que uma
pergunta coberta pelo catálogo da casa receba resposta automática composta a
partir desses fatos, e que um pedido ou uma reclamação sejam classificados de
verdade, para a conversa deixar de cair sempre no recado “a recepção vai
atender”.

**Why this priority**: Sem inteligência real, o argumento central do produto não
aparece. É a fatia que mais muda a demonstração: o canal já pode ser a tela; o
que falta é o cérebro.

**Independent Test**: Pode ser testado com o ambiente em modo de inteligência
real no caminho de execução, e com um serviço de linguagem **controlado** na
verificação automatizada (nunca o serviço de rede), partindo de uma dúvida
coberta pelo catálogo ativo: a resposta automática chega ao hóspede e afirma só
o que está nesse catálogo. O mesmo roteiro com o serviço controlado configurado
para devolver classificação e redação válidas prova que a escolha de modo não
altera a regra de negócio.

**Acceptance Scenarios**:

1. **Given** uma mensagem de estadia cuja dúvida está coberta pelo catálogo
   ativo da propriedade e o modo de inteligência apto a classificar e redigir,
   **When** o processamento conclui, **Then** o hóspede recebe resposta
   automática fiel a esse catálogo, e nenhum chamado de “recepção vai atender”
   nasce só porque o cérebro deixou de ser o adaptador controlado.
2. **Given** uma mensagem de pedido de serviço ou de reclamação técnica, **When**
   o serviço de linguagem devolve classificação válida, **Then** o desfecho é o
   já especificado das fatias de pedido e de reclamação (confirmação ao hóspede
   antes da tramitação) — não o encaminhamento genérico de “não entendi”.
3. **Given** uma resposta de ficha da pré-chegada, **When** o serviço de
   linguagem devolve extração válida, **Then** a ficha é consolidada como nas
   fatias já entregues — não fica irreconhecível só porque o cérebro passou a
   ser o serviço real.
4. **Given** o mesmo texto de hóspede e a mesma situação de reserva, **When** o
   processamento corre uma vez com inteligência real e outra com inteligência
   controlada (ambos devolvendo o mesmo resultado válido), **Then** os desfechos
   de negócio coincidem; só a origem da classificação, da redação e da extração
   difere.

---

### User Story 2 - Alternar o cérebro é configuração (Priority: P1)

Como responsável pelo ambiente, quero escolher entre o serviço real de linguagem
e o adaptador controlado **sem alterar código**, e quero que essa escolha seja
independente da escolha do canal com o hóspede (tela de demonstração ou
provedor real), para a banca ver inteligência de verdade com canal simulado, e
para o desenvolvimento local continuar sem rede.

**Why this priority**: Critério de aceite explícito da fatia e o mesmo princípio
da porta trocável já usado no canal. Misturar “trocar o cérebro” com “reeditar
o sistema” tornaria a demonstração um produto de palco.

**Independent Test**: Pode ser testado alterando só a configuração do ambiente
e observando qual implementação atende classificação e redação; conferindo
que canal e inteligência variam em qualquer combinação; e tentando subir
com modo ausente ou real sem chave — nenhum trabalho corre.

**Acceptance Scenarios**:

1. **Given** a necessidade de demonstrar com inteligência real ou de desenvolver
   sem rede, **When** o responsável altera a configuração de modo de
   inteligência do ambiente, **Then** o cérebro usado passa a ser o escolhido,
   **sem** mudança de código e **sem** um segundo conjunto de regras de hotel.
2. **Given** o canal em modo de demonstração e a inteligência em modo real,
   **When** o hóspede pergunta pela tela, **Then** a classificação e a redação
   usam o cérebro real (ou o controlado, se essa for a configuração), e o
   recado de saída aparece na tela — as duas escolhas não se forçam.
3. **Given** o canal em modo real e a inteligência em modo controlado, **When**
   uma mensagem de estadia é processada, **Then** o cérebro continua o
   controlado e o envio segue pelo provedor de mensageria — uma troca não
   arrasta a outra.
4. **Given** modo de inteligência ausente, vazio ou desconhecido, **When** se
   tenta subir o processamento daquele ambiente, **Then** nenhum trabalho
   corre — nem coleta, nem lembrete, nem boas-vindas, nem classificação.
   Não há queda silenciosa para o adaptador controlado nem chamada ao
   serviço real sem escolha explícita.
5. **Given** modo de inteligência real e chave de acesso ausente, **When** se
   tenta subir o processamento, **Then** o desfecho é o mesmo do cenário 4:
   o ambiente não sobe; não chama o serviço sem credencial e não finge o
   adaptador controlado.

---

### User Story 3 - Falha, demora ou lixo não perdem a mensagem (Priority: P1)

Como hóspede e como hotel, quero que falha do serviço de linguagem, demora além
do aceitável ou resposta em formato inválido não apaguem o que eu mandei nem
inventem uma resposta: a mensagem permanece e uma pessoa da recepção vê que
precisa atender, como já acontece hoje quando o classificador controlado falha.

**Why this priority**: É o caso obrigatório da constituição (“na dúvida, um
humano vê”) aplicado ao serviço real. Sem ele, ligar a inteligência de verdade
introduziria um modo de perda que o adaptador controlado não tinha.

**Independent Test**: Pode ser testado com o serviço controlado configurado
para indisponível, para demora além do limite, e para resultado malformado, em
classificação e em redação, verificando: texto original no histórico,
encaminhamento humano visível à recepção, zero resposta inventada, trabalho
não deixado em espera infinita contra o serviço.

**Acceptance Scenarios**:

1. **Given** uma mensagem de estadia já gravada e o serviço de linguagem
   indisponível, **When** o trabalho é processado, **Then** a mensagem
   permanece no histórico, o hóspede não recebe resposta inventada, e a
   recepção da propriedade vê pendência humana — o mesmo desfecho já
   especificado para classificador ou redator indisponível.
2. **Given** o serviço de linguagem que não devolve resultado dentro do tempo
   aceitável, **When** o trabalho é processado, **Then** o desfecho é o de
   indisponibilidade (encaminhamento humano), e o processamento **não** fica
   preso esperando o serviço — o restante da fila continua.
3. **Given** uma resposta do serviço em formato inválido (campos faltando,
   valores fora da taxonomia, redação que não é o resultado estruturado),
   **When** o trabalho é processado, **Then** aquele resultado **não** é usado
   para decidir ramo automático; a mensagem vai a humano e o bruto recebido
   permanece recuperável para auditoria, sem ir para o log.
4. **Given** qualquer um dos três desfechos, **When** a aplicação é
   reiniciada em seguida, **Then** a mensagem original continua recuperável e
   a pendência humana continua visível.

---

### User Story 4 - O hóspede sabe com quem fala (Priority: P1)

Como hóspede que acaba de ter a chegada confirmada, quero que a primeira
mensagem da minha estadia diga, em texto claro, que o atendimento inicial é
feito por uma assistente virtual e que uma pessoa da recepção assume quando
necessário, para eu não descobrir isso no meio da conversa nem achar que falo
com a recepção o tempo todo.

**Why this priority**: É postura do produto, não escolha do hotel. Sem o aviso,
ligar a inteligência real omite um fato que o hóspede tem o direito de saber.
O campo de tom da casa fica para fatia posterior; esta entrega só o aviso.

**Independent Test**: Pode ser testado confirmando a chegada de uma reserva
elegível com os recados de entrada preenchidos e inspecionando a primeira
mensagem da estadia: o aviso está lá, com as duas ideias (assistente virtual e
pessoa que assume), e a propriedade **não** tem como alterar esse trecho.

**Acceptance Scenarios**:

1. **Given** uma confirmação de chegada bem-sucedida com o recado de
   boas-vindas apto a sair, **When** o envio é processado, **Then** a mensagem
   de boas-vindas — primeira da estadia — informa que o atendimento inicial é
   feito por uma assistente virtual e que uma pessoa da recepção assume quando
   necessário.
2. **Given** o texto dessa primeira mensagem, **When** ele é inspecionado,
   **Then** o aviso é o texto fixo do produto: a propriedade não o edita, não
   o omite e não o substitui por outro. Os três slots de entrada (café, wi-fi,
   checkout) continuam os da casa.
3. **Given** a mesma reserva depois do primeiro recado, **When** o hóspede
   recebe respostas seguintes da estadia (dúvida, confirmação de pedido,
   pulso), **Then** o aviso **não** é repetido em cada uma — foi a primeira
   mensagem, não uma assinatura.
4. **Given** coleta ou lembrete da pré-chegada, **When** essas mensagens são
   enviadas, **Then** o aviso de assistente virtual **não** aparece nelas: a
   estadia ainda não começou.

---

### User Story 5 - Chave e conversa fora do log (Priority: P2)

Como titular dos dados e responsável pelo hotel, quero que a chave de acesso
ao serviço de linguagem nunca apareça em arquivo versionado nem em log, e que
o texto do hóspede continue fora do log mesmo quando o serviço real classifica
ou redige, para um repositório ou um arquivo técnico não virarem segredo nem
cópia da conversa.

**Why this priority**: Minimização de dados pessoais e proteção do segredo de
acesso. Ligar o serviço real aumenta a tentação de registrar prompt, resposta
e chave para depurar — isso é defeito, não diagnóstico.

**Independent Test**: Pode ser testado nos desfechos de sucesso, indisponível,
demora e formato inválido, inspecionando logs e a árvore versionada: há
identificadores, modo de inteligência e códigos; não há chave, não há texto
de hóspede, não há corpo da resposta do serviço.

**Acceptance Scenarios**:

1. **Given** classificação ou redação bem-sucedida com inteligência real ou
   controlada, **When** o sistema registra log operacional, **Then** aparecem
   identificadores, a propriedade, o modo de inteligência e o resultado — e
   não o conteúdo da mensagem, não o texto enviado ao serviço e não a chave
   de acesso.
2. **Given** falha, demora ou formato inválido, **When** o sistema registra
   log operacional, **Then** há código de resultado e identificadores, sem a
   chave, sem o texto do hóspede e sem copiar a resposta bruta do serviço
   para o log.
3. **Given** o repositório do produto, **When** se inspecionam arquivos
   versionados, **Then** nenhuma chave de acesso ao serviço de linguagem está
   neles. O nome da configuração pode existir num exemplo, **sem** valor.

---

### Edge Cases

- A escolha de inteligência cobre **todos** os usos já existentes da porta
  (interpretar ficha, classificar intenção, redigir dúvida, reconhecer item
  vendável, ler pesquisa de saída). Não há um modo real só para classificar e
  controlado para o resto. Se o tempo de implementação apertar, identificar
  item vendável e ler pesquisa de saída podem ter extração menos refinada:
  a falha continua o encaminhamento humano já construído — não se inventa
  ramo novo nem se deixa esses usos no adaptador controlado.
- Quota esgotada, recusa de acesso ou limite de chamadas do serviço real
  são indisponibilidade: encaminhamento humano, sem retentativa indefinida
  contra o serviço.
- Demora além do aceitável é o mesmo desfecho de indisponibilidade. O tempo
  aceitável é configuração de plataforma, não parâmetro da propriedade.
- Resposta do serviço com fato fora do catálogo ativo continua recusada pelo
  domínio já especificado (aviso ao hóspede + chamado), mesmo com cérebro
  real. Ligar o serviço real **não** afrouxa a regra do catálogo.
- Reprocessar trabalho já concluído (classificação, redação, ficha) não gera
  segunda chamada observável ao serviço nem segundo efeito no hóspede.
- Falha ao gravar o resultado: a mensagem original permanece; o trabalho
  continua recuperável; não se envia texto que ainda não foi gravado.
- Boas-vindas bloqueadas por slot vazio: o aviso viaja **com** o recado de
  chegada, não sozinho. Completar os slots na janela de validade envia o
  recado já com o aviso; não se manda o aviso numa mensagem avulsa.
- Dois hóspedes na mesma reserva: um recado de chegada, um aviso — no
  telefone de contato, como as boas-vindas.
- Hotel A não usa catálogo, chave nem conversa do hotel B.
- Modo de inteligência inválido não é corrigido em silêncio para controlado
  nem para real. O ambiente recusa subir; coleta e boas-vindas também não
  saem — não há “só o cérebro falha”.
- Inteligência em modo real sem chave de acesso no ambiente: o mesmo
  desfecho — o ambiente **não** sobe (nem chama o serviço sem credencial,
  nem finge o adaptador controlado).
- Verificação automatizada injeta o adaptador controlado e não passa pela
  recusa de subida. A recusa vale para o processamento que lê a
  configuração do ambiente.
- Esta fatia **não** cria campo de tom da propriedade, **não** acrescenta
  linha de convite editável no recado, **não** muda a taxonomia de intenção,
  **não** muda os três slots de entrada, **não** troca o canal de mensageria
  e **não** se integra ao sistema de gestão do hotel.
- Pedido do hóspede para falar com uma pessoa continua o encaminhamento já
  existente (fora de escopo / atendimento humano). Esta fatia não acrescenta
  um ramo novo de “quero humano”; só declara, na primeira mensagem, que isso
  acontece quando necessário.
- Limitação honesta: o serviço real em camada gratuita pode recusar por
  excesso de chamadas num intervalo curto. O sistema não promete resposta
  automática ininterrupta; promete degradar para humano sem perder a
  mensagem.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O ambiente MUST operar em exatamente um modo de inteligência
  por vez: real (serviço de modelo de linguagem) ou controlado (adaptador
  determinístico já existente). A escolha MUST ser configuração do ambiente.
  MUST NOT exigir alteração de código para alternar.
- **FR-002**: A escolha de inteligência MUST ser independente da escolha de
  canal com o hóspede. Qualquer combinação dos dois modos MUST ser válida.
- **FR-003**: Modo de inteligência ausente, vazio ou desconhecido MUST
  impedir a subida do processamento daquele ambiente: MUST NOT correr
  nenhum trabalho (coleta, lembrete, boas-vindas, classificação, redação
  ou demais). MUST NOT cair em silêncio para o adaptador controlado nem
  chamar o serviço real sem escolha explícita.
- **FR-004**: Em modo real, **todos** os usos já existentes da porta de
  linguagem (interpretar ficha, classificar intenção, redigir dúvida,
  reconhecer item vendável, ler pesquisa de saída) MUST passar pelo serviço
  real e MUST ser capazes de devolver resultado útil. Em modo controlado,
  MUST passar pelo adaptador determinístico. MUST NOT existir híbrido
  (parte real, parte controlado) no mesmo ambiente.
- **FR-004a**: Classificar, redigir resposta e extrair ficha MUST ter
  resultado útil no caminho de demonstração. Identificar item vendável e
  ler pesquisa de saída MUST igualmente passar pelo serviço real; falha
  desses dois MUST reutilizar o encaminhamento humano já especificado nas
  fatias anteriores — MUST NOT construir comportamento novo de fallback.
- **FR-005**: Regras de negócio da estadia MUST ser as mesmas nos dois modos.
  MUST NOT existir atalho, resposta inventada, pulo de confirmação ou
  afrouxamento da regra do catálogo só porque o cérebro é o serviço real.
- **FR-006**: Quando o serviço de linguagem estiver indisponível, recusar a
  chamada, esgotar a quota ou demorar além do tempo aceitável, o sistema
  MUST preservar a mensagem, MUST encaminhar para atendimento humano visível
  à recepção da propriedade, MUST NOT enviar resposta inventada, e MUST NOT
  deixar o processamento preso à espera do serviço.
- **FR-007**: O tempo aceitável de espera pelo serviço MUST ser configuração
  de plataforma, não parâmetro da propriedade. MUST NOT ser constante oculta
  de regra de hotel.
- **FR-008**: Quando a resposta do serviço for inválida (formato, eixos
  incompletos, valores fora da taxonomia, redação que não é o resultado
  estruturado), o sistema MUST comportar-se como falha (encaminhamento
  humano, sem ramo automático) e MUST preservar a resposta completa recebida
  para auditoria — MUST NOT copiá-la para o log.
- **FR-009**: Os desfechos de FR-006 e FR-008 MUST reutilizar os encaminhamentos
  humanos já especificados nas fatias de classificar, responder dúvida,
  interpretar ficha, reconhecer item vendável e ler pesquisa de saída. MUST
  NOT inventar um quarto destino.
- **FR-010**: A primeira mensagem de cada estadia (o recado de boas-vindas
  enviado após a confirmação de chegada) MUST informar que o atendimento
  inicial é feito por uma assistente virtual e que uma pessoa da recepção
  assume quando necessário.
- **FR-011**: O texto desse aviso MUST ser fixo do produto. A propriedade
  MUST NOT poder editá-lo, omiti-lo ou substituí-lo. MUST NOT nascer slot
  novo na configuração da casa para esse fim.
- **FR-012**: O aviso MUST aparecer uma única vez por estadia, na primeira
  mensagem. MUST NOT ser repetido nas respostas seguintes nem nas mensagens
  de pré-chegada (coleta e lembrete).
- **FR-013**: Se as boas-vindas não saírem por slot de entrada vazio, o aviso
  MUST viajar com o recado quando ele sair — MUST NOT ser enviado sozinho.
- **FR-014**: Os três slots de entrada, o convite a perguntar e a proibição
  de oferta comercial no recado de chegada MUST permanecer como já
  especificados. O aviso acresce; não substitui.
- **FR-015**: A chave de acesso ao serviço de linguagem MUST vir somente do
  ambiente. MUST NOT aparecer em arquivo versionado (um exemplo MAY listar o
  **nome** da configuração, sem valor). MUST NOT aparecer em log.
- **FR-016**: Em modo real, ausência da chave de acesso MUST impedir a
  subida do processamento daquele ambiente, com o mesmo alcance de FR-003
  (nenhum trabalho corre). MUST NOT chamar o serviço sem credencial e
  MUST NOT fingir o adaptador controlado.
- **FR-017**: Conteúdo de mensagem de hóspede, texto enviado ao serviço,
  resposta bruta do serviço e demais dados pessoais NUNCA MUST aparecer em
  log operacional; logs registram identificadores, a propriedade, o modo de
  inteligência e códigos de resultado.
- **FR-018**: A verificação desta fatia MUST ser possível sem o serviço real
  de linguagem: um adaptador controlado devolve resultados previsíveis
  (sucesso, indisponível, demora, inválido) sem rede. Nenhum teste MUST
  chamar o serviço real nem depender de rede.
- **FR-019**: Reprocessar trabalho já concluído MUST NOT produzir segundo
  efeito observável nem segunda chamada desnecessária ao serviço.
- **FR-020**: Resolução MUST considerar a propriedade da reserva; conversa,
  catálogo e pendência de um hotel MUST NOT vazar para outro.
- **FR-021**: Esta fatia MUST NOT criar campo de tom da assistente, MUST NOT
  acrescentar linha de convite editável no recado de chegada, MUST NOT
  alterar a taxonomia de intenção, MUST NOT confirmar chegada ou saída por
  conta própria e MUST NOT integrar-se ao sistema de gestão do hotel.
- **FR-022**: Persistência da mensagem MUST continuar ocorrendo antes da
  tentativa de envio. Falha do serviço de linguagem MUST NOT apagar
  histórico já gravado.

### Key Entities

- **Modo de inteligência**: configuração do ambiente — real (serviço de
  modelo de linguagem) ou controlado (adaptador determinístico). Um por vez;
  independente do modo de canal; não é atributo da reserva nem da
  propriedade.
- **Serviço de modelo de linguagem**: origem externa da classificação e da
  redação quando o modo é real. O domínio não o conhece; fala com a porta já
  existente.
- **Adaptador controlado**: implementação determinística já usada em teste e
  em desenvolvimento sem rede. Continua existindo; deixa de ser o único
  cérebro do processamento de produção.
- **Aviso de assistente virtual**: frase fixa do produto, na primeira
  mensagem de cada estadia, informando que o atendimento inicial é por
  assistente virtual e que uma pessoa da recepção assume quando necessário.
  Não é parâmetro da propriedade.
- **Encaminhamento humano**: pendência visível à recepção, já especificada
  nas fatias de classificação e de dúvida. Nasce também quando o serviço
  real falha, demora ou devolve lixo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Alternar entre inteligência real e controlada exige 0 alteração
  de código e 0 segundo conjunto de regras de hotel.
- **SC-002**: Em roteiro equivalente nos dois modos (mesmo texto, mesma
  reserva equivalente, mesmo resultado válido do cérebro), 100% dos desfechos
  de negócio coincidem. A única diferença observável é a origem da
  classificação, da redação e da extração. Em modo real, 100% dos cinco usos
  já existentes da porta passam pelo serviço real — 0 híbrido com o
  adaptador controlado.
- **SC-003**: Em 100% dos casos de serviço indisponível, quota esgotada,
  demora além do aceitável ou resposta inválida, a mensagem original
  permanece, a recepção da propriedade vê pendência humana, o hóspede recebe
  0 respostas inventadas, e 0 processamentos ficam presos à espera do
  serviço.
- **SC-004**: Em 100% dos recados de boas-vindas enviados, o hóspede é
  informado de que o atendimento inicial é por assistente virtual e de que
  uma pessoa da recepção assume quando necessário. Em 100% das mensagens
  seguintes da mesma estadia e em 100% das mensagens de pré-chegada, esse
  aviso não se repete.
- **SC-005**: Em 100% das propriedades, 0% conseguem editar, omitir ou
  substituir o aviso por configuração da casa.
- **SC-006**: Em 100% dos registros operacionais desta fatia, 0 chaves de
  acesso, 0 conteúdos de mensagem de hóspede e 0 corpos de resposta do
  serviço aparecem em log. Em 100% dos arquivos versionados, 0 chaves de
  acesso estão presentes.
- **SC-007**: 100% dos testes automatizados desta fatia concluem sem chamar
  o serviço real e sem depender de rede.
- **SC-008**: Em verificação com dois hotéis, 0% das conversas, catálogos ou
  pendências de um são afetados ou visíveis no outro.
- **SC-009**: Em verificação das quatro combinações (canal real/demonstração
  × inteligência real/controlada), 100% são aceitas; nenhuma combinação força
  a outra escolha.
- **SC-010**: O caminho configuração de inteligência → classificação e
  redação pelo cérebro escolhido → falha degradando a humano → primeira
  mensagem da estadia com o aviso é verificável sem o serviço real de
  linguagem e sem o sistema de gestão do hotel.
- **SC-011**: Em 100% das tentativas de subir com modo ausente, desconhecido
  ou real sem chave, 0 trabalhos correm (coleta, lembrete, boas-vindas e
  classificação inclusive). 0 quedas silenciosas para o adaptador
  controlado.

## Assumptions

- As fatias F3.2 (classificar), F3.3 (responder pelo catálogo) e F6.2
  (simulador de conversa) estão concluídas. Os encaminhamentos humanos, a
  regra do catálogo, a confirmação antes da tramitação e a escolha do canal
  já existem. Esta fatia **não** os redesenha: troca a origem do cérebro e
  acrescenta o aviso na primeira mensagem da estadia.
- **Um modo de inteligência por ambiente em execução**, no mesmo molde da
  escolha do canal. Não há botão por reserva, por hotel nem por mensagem.
- **Canal e cérebro são eixos independentes.** A demonstração à banca usa
  canal simulado e inteligência real; o desenvolvimento local pode usar os
  dois controlados. Nenhuma combinação é proibida.
- **A porta e o adaptador controlado já existem.** O processamento de
  produção hoje instancia o controlado diretamente. Esta fatia passa a
  escolhê-lo (ou o real) pela configuração, como já faz com o canal.
- **Recusa de subida (já decidida).** Modo ausente, desconhecido, ou real
  sem chave impedem **qualquer** trabalho daquele ambiente — o mesmo molde
  da escolha do canal. A falha aparece na hora, não na primeira pergunta do
  hóspede. Testes injetam o adaptador controlado e não passam por essa
  recusa.
- **Um interruptor para todos os usos da porta.** Interpretar ficha,
  classificar, redigir, reconhecer item vendável e ler pesquisa de saída
  seguem o mesmo modo e, em modo real, o mesmo serviço. Não há meio-termo
  por tipo de trabalho (um uso no real e outro no controlado).
- **Prioridade de refinamento (já decidida).** A jornada de demonstração
  atravessa classificar, responder e extrair ficha: esses três levam o
  cuidado do prompt. Identificar item vendável e pesquisa de saída podem
  ficar menos refinados; a falha deles já cai em humano por construção
  das fatias anteriores. Isso **não** autoriza deixá-los no adaptador
  controlado quando o modo é real.
- **Tempo aceitável de espera** é configuração de plataforma (como o modo
  do canal), com valor definido no planejamento. Não entra em parâmetro da
  propriedade: não é prazo de hotel, é limite para não travar o
  processamento.
- **O aviso vive no recado de boas-vindas**, que é a primeira mensagem da
  estadia. Texto fixo do produto, uma vez, sem slot novo. Redação de
  referência, testável pelas duas ideias obrigatórias: *“O atendimento
  inicial é feito por uma assistente virtual. Uma pessoa da recepção assume
  quando necessário.”* O planejamento pode ajustar a frase desde que as duas
  ideias permaneçam.
- **Personalidade da assistente (tom configurável) fica fora.** É o restante
  da F7.2, cortado de propósito nesta semana. A porta permanece pronta para
  o campo de tom entrar depois, sem retrabalho desta fatia.
- **Linha de convite editável no recado (F7.3) fica fora.** O convite a
  perguntar já existente permanece; não se acrescenta quarto slot.
- **Verificação sem rede.** Testes usam o adaptador controlado para sucesso,
  indisponibilidade, demora e formato inválido. Nenhum teste consome chamada
  do serviço real. O caminho de execução em modo real é exercitado com um
  duplo que finge o serviço — não com a rede.
- **Chave só no ambiente.** O exemplo de configuração lista o nome da chave
  sem valor, no padrão já adotado para as demais credenciais.
- **O provedor concreto e a camada gratuita** são escolha de planejamento.
  O domínio não os conhece. Trocar de provedor depois não pode exigir
  reescrever regra de hotel.
- Superfície de uso: comportamento observável no histórico da conversa, na
  primeira mensagem da estadia, no encaminhamento visível à recepção e na
  configuração do ambiente. Ligar tela nova do painel operacional continua
  fora.
- Limitação honesta (Artigo XV): camada gratuita tem limite de chamadas por
  minuto. Estouro não quebra o sistema — degrada para “a recepção vai
  atender”. Não há alta disponibilidade do serviço de linguagem, e o clique
  humano de chegada continua necessário para o aviso sair.
