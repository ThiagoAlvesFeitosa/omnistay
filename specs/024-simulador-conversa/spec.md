# Feature Specification: Simulador de Conversa

**Feature Branch**: `024-simulador-conversa`

**Created**: 2026-08-26

**Status**: Draft

**Input**: User description: "Existe um modo de demonstração em que as
mensagens trocadas com o hóspede aparecem em uma tela de simulação em vez
de serem enviadas pelo provedor real, permitindo demonstrar o sistema
completo sem depender de rede externa nem de número de telefone. O
comportamento do sistema é idêntico nos dois modos."
(backlog F6.2)

Restrições já decididas no projeto (entrada do specify): o canal de
demonstração é **substituto do provedor de mensageria**, não um produto
paralelo com regras próprias — o mesmo domínio atende o hóspede real e o
hóspede da tela; alternar entre modo real e modo de demonstração é
**configuração do ambiente**, não alteração de código nem atalho por
mensagem; gravar vem antes de enviar; na dúvida um humano vê; confirmação
ao hóspede acontece antes da tramitação; conteúdo de mensagem **nunca**
vai para log; o sistema não se integra ao sistema de gestão do hotel e
não infere chegada nem saída; a demonstração à banca **não** depende de
túnel, de número de telefone nem da disponibilidade do provedor no dia.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver a conversa na tela, sem telefone (Priority: P1)

Como quem apresenta o sistema à banca, quero que cada recado que o hotel
enviaria ao hóspede apareça numa **tela de simulação** — coleta, lembrete,
boas-vindas, resposta de dúvida, confirmação de pedido ou reclamação,
pulso, pesquisa de saída e lista de pedidos feitos pelo chat — para eu
mostrar a jornada inteira sem chip, sem aplicativo de mensagens e sem
contar com a rede do provedor na hora da defesa.

**Why this priority**: Sem superfície visível, o modo de demonstração não
existe: a mensagem some num adaptador invisível, e a banca não vê o
hóspede. É o critério de aceite da fatia e o que a arquitetura prometeu
quando isolou o canal atrás de uma porta trocável.

**Independent Test**: Pode ser testado colocando o ambiente em modo de
demonstração, disparando um envio que no modo real iria ao hóspede
(por exemplo a coleta ao cadastrar a reserva) e conferindo: o texto
aparece na tela de simulação daquela conversa; o provedor real **não**
é acionado; a reserva e a pendência de envio existem como no modo real.

**Acceptance Scenarios**:

1. **Given** o ambiente em modo de demonstração e uma reserva recém
   cadastrada com disparo de coleta, **When** o envio da coleta é
   processado com sucesso, **Then** o texto da coleta aparece na tela de
   simulação da conversa daquele hóspede, e nenhuma mensagem é entregue
   pelo provedor real.
2. **Given** o mesmo ambiente e uma reserva cuja chegada acaba de ser
   confirmada com os recados de entrada preenchidos, **When** o envio de
   boas-vindas é processado, **Then** o recado de boas-vindas aparece na
   mesma tela, distinguível da coleta.
3. **Given** uma resposta automática de dúvida, uma confirmação de pedido
   ou de reclamação, um pulso, uma pesquisa de saída ou a lista de
   pedidos feitos pelo chat, **When** cada um desses envios é processado
   em modo de demonstração, **Then** o texto correspondente aparece na
   tela daquela conversa — nenhum tipo de recado da jornada some só
   porque o canal não é o provedor real.
4. **Given** dois envios sucessivos para o mesmo hóspede, **When** ambos
   são processados, **Then** a tela mostra os dois em ordem cronológica,
   com direção “hotel → hóspede” visível.

---

### User Story 2 - Falar como o hóspede na mesma tela (Priority: P1)

Como apresentador, quero digitar na tela de simulação **como se eu fosse
o hóspede** da reserva escolhida, e quero que o sistema grave, classifique
e responda exatamente como faria se o texto tivesse chegado pelo canal
real, para a banca ver dúvida, pedido, reclamação e ficha sem um aparelho
na mesa.

**Why this priority**: Ver só o que o hotel manda é um painel de log, não
uma conversa. A demonstração precisa do turno do hóspede. Se a entrada
simulada desviar para um caminho especial, a banca vê um sistema que não
é o que será operado no hotel.

**Independent Test**: Pode ser testado com uma reserva hospedada em modo
de demonstração, enviando pela tela um texto de dúvida coberta pelo
catálogo e outro de pedido de serviço, e conferindo: ambos entram no
histórico daquela reserva; a dúvida recebe resposta fiel ao catálogo na
própria tela; o pedido recebe confirmação na tela **antes** de existir
chamado; o chamado nasce como no modo real.

**Acceptance Scenarios**:

1. **Given** o modo de demonstração, uma reserva hospedada e a tela
   aberta na conversa desse hóspede, **When** o apresentador envia um
   texto como hóspede, **Then** a mensagem é gravada no histórico da
   reserva com direção “hóspede → hotel” e segue o mesmo processamento
   posterior que uma mensagem autêntica do canal real.
2. **Given** um texto de dúvida cuja resposta está no catálogo ativo da
   propriedade, **When** o processamento conclui, **Then** a resposta
   aparece na tela de simulação, fiel ao catálogo, sem inventar fato
   fora dele.
3. **Given** um texto de pedido de serviço ou de reclamação, **When** o
   processamento conclui, **Then** a confirmação de recebimento aparece
   na tela **antes** de o chamado existir, e em seguida o chamado nasce
   com o mesmo tipo e as mesmas regras do modo real.
4. **Given** uma reserva ainda aguardando cadastro, **When** o
   apresentador envia pela tela a resposta da ficha, **Then** a
   interpretação da ficha ocorre como no canal real — completa, parcial
   ou ilegível — e nenhuma mensagem de estadia (dúvida, pedido,
   reclamação) é inventada no lugar da ficha.
5. **Given** o apresentador ainda não escolheu qual conversa/hóspede da
   demonstração, **When** tenta enviar texto como hóspede, **Then** o
   envio é recusado: a mensagem não entra em reserva nenhuma.

---

### User Story 3 - O sistema demonstrado é o mesmo sistema (Priority: P1)

Como banca e como hotel, quero que alternar entre modo real e modo de
demonstração seja **só configuração do ambiente**, e que nenhuma regra de
negócio mude — pulso continua suprimido com chamado aberto, pergunta fora
do catálogo continua indo a humano, reenvio da coleta continua uma única
vez —, para a apresentação não vender um produto que só existe no palco.

**Why this priority**: Critério de aceite explícito da fatia e artigo da
constituição: o simulador é outro canal, não outro conjunto de regras.
Superprometer na defesa é o defeito mais caro deste trabalho.

**Independent Test**: Pode ser testado repetindo o mesmo roteiro de
hóspede (mesmo texto, mesma reserva equivalente) nos dois modos e
conferindo os mesmos desfechos de negócio; e conferindo que a troca de
modo não exigiu alterar regra, tela operacional nem “versão de
demonstração” do hotel.

**Acceptance Scenarios**:

1. **Given** um ambiente configurado em modo de demonstração e outro em
   modo real, **When** o mesmo texto de hóspede é processado em reservas
   equivalentes, **Then** classificação, confirmação, abertura ou não de
   chamado, resposta de catálogo ou encaminhamento a humano são os
   mesmos; só o destino da mensagem de saída difere (tela versus
   provedor real).
2. **Given** um chamado de reclamação em aberto e estadia com pulso
   elegível pelo relógio, **When** a passagem do pulso corre em modo de
   demonstração, **Then** o pulso **não** dispara — a mesma supressão do
   modo real.
3. **Given** uma pergunta fora do catálogo ativo, **When** é enviada pela
   tela em modo de demonstração, **Then** o hóspede **não** recebe
   resposta inventada; o caso vai à fila humana como no modo real.
4. **Given** a necessidade de apresentar à banca ou de operar com o
   provedor real, **When** o responsável altera a configuração de modo
   do ambiente, **Then** o canal usado passa a ser o escolhido, **sem**
   mudança de código e **sem** um segundo conjunto de regras de hotel.

---

### User Story 4 - Um modo não contamina o outro (Priority: P2)

Como responsável pelo hotel, quero que o modo real **recuse** mensagem
injetada pela tela de simulação, e que o modo de demonstração **não**
dispare envio pelo provedor real, para uma apresentação local não vazar
para hóspede de verdade e para um ambiente em produção não aceitar
conversa falsa digitada na tela.

**Why this priority**: O endereço de conversa do hóspede é sensível.
Misturar os canais quebraria a garantia de autenticidade do modo real e
a promessa de isolamento da demonstração.

**Independent Test**: Pode ser testado tentando enviar pela tela com o
ambiente em modo real (recusa, zero histórico, zero trabalho) e
disparando um envio ao hóspede com o ambiente em modo de demonstração
(aparece na tela, zero entrega pelo provedor real).

**Acceptance Scenarios**:

1. **Given** o ambiente em modo real, **When** alguém tenta enviar um
   texto de hóspede pela tela de simulação, **Then** o envio é recusado:
   nenhuma mensagem entra no histórico, nenhum trabalho é enfileirado,
   nenhuma reserva é alterada.
2. **Given** o ambiente em modo de demonstração, **When** o sistema
   processa um envio ao hóspede, **Then** o texto fica visível na tela
   daquela conversa e o provedor real **não** é acionado para aquele
   envio.
3. **Given** o ambiente em modo real, **When** a tela de simulação é
   consultada, **Then** ela não opera como canal de conversa: não
   substitui o provedor nem aceita turno de hóspede.
4. **Given** duas propriedades, **When** a demonstração corre na
   propriedade A, **Then** conversa, reserva e tela da propriedade B
   permanecem intocadas.

---

### Edge Cases

- Reservar a conversa da demonstração: a tela opera sobre uma reserva
  **já cadastrada** da propriedade (telefone e datas existentes). Não
  cria hóspede fantasma só para o palco.
- Reserva em `aguardando_cadastro` versus `hospedado`: a tela não
  atravessa essa fronteira. Ficha continua ficha; mensagem de estadia
  continua mensagem de estadia — o mesmo recorte do canal real.
- Reenvio do mesmo identificador de entrada simulada: não gera segunda
  mensagem nem segundo processamento.
- Texto vazio na tela: recusado; não nasce mensagem nem trabalho.
- Hóspede/telefone que não pertence a reserva ativa da propriedade:
  recusado; não cria conversa órfã.
- Falha ao “entregar” na tela (superfície indisponível): a reserva e a
  mensagem gravada permanecem; o envio fica pendente de nova tentativa,
  como qualquer falha de canal — gravar não desfaz.
- Troca de modo no meio de uma conversa: o histórico já gravado
  permanece; envios seguintes seguem o modo vigente. Não há mistura
  simultânea dos dois canais no mesmo ambiente.
- O duplo usado nos testes automatizados, que engole envio sem tela,
  **não** satisfaz esta fatia: a banca precisa ver o texto. Teste sem
  pessoa na frente continua usando o duplo invisível; a demonstração
  usa a tela.
- Classificador de intenção e fatos do catálogo **não** ganham modo
  especial de palco nesta fatia. Continuam os já configurados do
  ambiente. Só o canal com o hóspede é substituído.
- Esta fatia **não** reconstrói o painel operacional completo
  (fila do dia, catálogo, mercado, retenção). Cadastro de reserva,
  confirmação de chegada e de saída, resolução de chamado e demais
  cliques de funcionário permanecem as operações autenticadas já
  entregues.
- Esta fatia **não** envia nada pelo provedor real, **não** exige
  número de telefone do apresentador, **não** depende de túnel nem
  de disponibilidade do provedor, **não** se integra ao sistema de
  gestão do hotel e **não** altera regra de pulso, catálogo, retenção
  ou lançamento de consumo.
- Logs da demonstração registram identificadores, modo do canal e
  códigos de recusa. **Não** registram o texto da conversa.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O ambiente MUST operar em exatamente um modo de canal por
  vez: real ou demonstração. A escolha MUST ser configuração do
  ambiente. MUST NOT exigir alteração de código para alternar.
- **FR-002**: Em modo de demonstração, todo recado que o sistema
  enviaria ao hóspede MUST aparecer na tela de simulação da conversa
  daquela reserva. MUST NOT ser entregue pelo provedor real.
- **FR-003**: A tela de simulação MUST exibir os turnos em ordem
  cronológica, distinguindo direção (hóspede → hotel e hotel →
  hóspede) e MUST permitir ao apresentador escolher a conversa a
  partir de uma reserva já cadastrada da propriedade.
- **FR-004**: Em modo de demonstração, texto enviado pela tela como
  hóspede MUST ser gravado no histórico da reserva escolhida e MUST
  seguir o mesmo processamento posterior (ficha ou classificação e
  desfechos da estadia) que uma mensagem chegada pelo canal real.
- **FR-005**: Confirmação de pedido e de reclamação MUST aparecer na
  tela **antes** da criação do chamado, como no modo real.
- **FR-006**: Pergunta coberta pelo catálogo ativo MUST receber na tela
  resposta fiel ao catálogo. Pergunta fora do catálogo MUST NOT
  receber resposta inventada; MUST seguir à fila humana.
- **FR-007**: Regras de negócio da estadia MUST ser as mesmas nos dois
  modos. MUST NOT existir atalho, pulo de confirmação, pulso liberado
  ou resposta inventada só porque o canal é a tela.
- **FR-008**: Em modo real, envio pela tela de simulação MUST ser
  recusado: zero mensagem no histórico, zero trabalho enfileirado,
  zero efeito na reserva.
- **FR-009**: Em modo real, a tela de simulação MUST NOT substituir o
  provedor nem operar como canal de conversa.
- **FR-010**: Entrada pela tela MUST exigir conversa escolhida
  (reserva da propriedade). Sem escolha, texto vazio ou telefone sem
  reserva da casa, MUST recusar.
- **FR-011**: Reapresentação do mesmo identificador de entrada
  simulada MUST NÃO gerar segunda mensagem nem segundo processamento.
- **FR-012**: Persistência da mensagem MUST ocorrer antes da tentativa
  de mostrá-la na tela. Falha de entrega na tela MUST NOT apagar
  reserva nem histórico já gravado; MUST permanecer recuperável para
  nova tentativa.
- **FR-013**: A tela MUST estar disponível para sessão autenticada da
  propriedade em modo de demonstração (recepção ou gestão). Perfil
  operacional de staff MUST receber recusa de uso da tela como canal.
  Visitante sem sessão MUST receber recusa.
- **FR-014**: Toda leitura e toda escrita da conversa simulada MUST
  considerar o hotel da sessão. Dado de um hotel MUST NOT aparecer
  nem ser alterado no outro.
- **FR-015**: Coleta, lembrete, boas-vindas, texto de sessão (resposta
  e confirmação), pulso, pesquisa de saída e lista de pedidos feitos
  pelo chat MUST todos ser visíveis na tela quando enviados em modo
  de demonstração. MUST NOT faltar tipo da jornada só por não haver
  provedor.
- **FR-016**: Esta fatia MUST NOT alterar catálogo, parâmetro de
  comportamento, regra de pulso, retenção, mercado, lançamento de
  consumo nem transição de fase da reserva. MUST NOT integrar-se ao
  sistema de gestão do hotel.
- **FR-017**: Logs MUST registrar identificadores, modo do canal e
  códigos. MUST NOT registrar conteúdo de mensagem.
- **FR-018**: O painel operacional completo (fila, chamados, mercado,
  retenção) MUST permanecer fora do critério de pronto visual desta
  fatia. O critério visual desta fatia é a **tela de simulação da
  conversa**.
- **FR-019**: Classificador e fonte de fatos da propriedade MUST
  permanecer os já configurados do ambiente. Esta fatia MUST
  substituir somente o canal com o hóspede.

### Key Entities

- **Modo de canal**: configuração do ambiente — real (provedor de
  mensageria) ou demonstração (tela de simulação). Um por vez; não é
  atributo da reserva nem botão por mensagem.
- **Tela de simulação**: superfície em que o apresentador vê os recados
  do hotel e digita o turno do hóspede. Só opera como canal em modo de
  demonstração.
- **Conversa da demonstração**: o fio de mensagens de **uma** reserva
  já cadastrada da propriedade, escolhida na tela. Telefone e datas
  são os da reserva; não há hóspede paralelo só de palco.
- **Turno do hóspede**: texto digitado na tela, gravado e processado
  como mensagem de entrada daquela reserva.
- **Turno do hotel**: recado que o sistema enviaria ao hóspede;
  em demonstração torna-se visível na tela em vez de sair pelo
  provedor real.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em modo de demonstração, 100% dos recados ao hóspede
  processados com sucesso (coleta, lembrete, boas-vindas, sessão,
  pulso, pesquisa de saída, lista de pedidos feitos pelo chat)
  aparecem na tela da conversa correspondente. 0 desses envios são
  entregues pelo provedor real.
- **SC-002**: Em roteiro equivalente nos dois modos (mesmo texto de
  hóspede, mesma situação de reserva), 100% dos desfechos de negócio
  coincidem (classificação, confirmação antes do chamado, resposta
  de catálogo ou encaminhamento a humano, supressão de pulso). A
  única diferença observável é o destino da mensagem de saída.
- **SC-003**: Um apresentador consegue percorrer, numa única sessão
  de demonstração e **sem** número de telefone, **sem** rede do
  provedor e **sem** túnel: coleta visível → resposta de ficha →
  chegada com boas-vindas visíveis → dúvida respondida pelo catálogo
  → pedido confirmado na tela com chamado nascido depois → saída com
  pesquisa e lista de pedidos feitos pelo chat visíveis na tela.
- **SC-004**: Alternar entre modo real e modo de demonstração exige
  0 alteração de código e 0 segundo conjunto de regras de hotel.
- **SC-005**: Em modo real, 100% das tentativas de injetar turno de
  hóspede pela tela são recusadas, com 0 linha nova no histórico e
  0 trabalho enfileirado.
- **SC-006**: Em verificação com dois hotéis, 0% das conversas e 0%
  das telas de um são afetadas ou visíveis no outro.
- **SC-007**: Em sessão de staff operacional ou sem sessão, 100% das
  tentativas de usar a tela como canal são recusadas. Em sessão de
  recepção ou gestão da própria propriedade, em modo de demonstração,
  a tela opera.
- **SC-008**: Em 100% dos registros operacionais desta fatia, 0
  conteúdo de mensagem de hóspede ou de recado ao hóspede aparece
  em log.
- **SC-009**: Reapresentar o mesmo identificador de entrada simulada
  gera 0 segunda mensagem e 0 segundo processamento. Texto vazio ou
  sem conversa escolhida gera 0 mensagem.
- **SC-010**: Falha ao exibir na tela não apaga reserva nem
  histórico já gravado em 100% dos casos. O caminho configuração de
  demonstração → conversa visível → turno do hóspede processado com
  as mesmas regras → isolamento do modo real é verificável sem o
  provedor de mensageria e sem o sistema de gestão do hotel.

## Assumptions

- As fatias de conversa e de estadia até F6.1 estão concluídas. Esta
  fatia **não** cria coleta, classificação, catálogo, pulso, pesquisa
  de saída nem lista de pedidos: só passa a **mostrá-los** (e a
  aceitar o turno do hóspede) num canal visível quando o ambiente
  está em demonstração.
- **Um modo por ambiente em execução.** Não há botão por reserva nem
  mistura simultânea de provedor real e tela. A troca é configuração
  aplicada ao ambiente (típica de quem sobe a demonstração ou o
  hotel de verdade), não um atalho na conversa.
- **A tela é o critério visual desta fatia.** Fatias anteriores
  aceitaram operação autenticada sem interface gráfica nova. Aqui a
  banca precisa ver a conversa; canal sem tela não cumpre o objetivo.
  Isso **não** inclui reconstruir o painel da recepção, do staff ou
  da gestão em interface gráfica — esses cliques continuam as
  operações autenticadas já existentes.
- **Quem demonstra opera os dois lados.** O apresentador, autenticado
  como recepção ou gestão, cadastra reserva, confirma chegada e
  saída e resolve chamado pelas operações já entregues, e usa a tela
  para o papel do hóspede. Perfil operacional de staff não usa a
  tela como canal (não é o apresentador da banca nem o dono da
  conversa).
- **Reserva real da propriedade.** Não há cadastro especial “hóspede
  de demo”. O telefone da reserva identifica a conversa, como no
  canal real, mesmo que nenhum aparelho exista.
- **Só o canal com o hóspede é substituído.** Classificação de
  intenção e fatos do catálogo seguem os provedores já configurados
  no ambiente. Confiabilidade da banca pode usar o classificador
  determinístico já existente nos testes; isso não é escopo novo
  desta fatia.
- **Duplo invisível dos testes ≠ tela.** A suíte continua podendo
  engolir envio sem superfície. O modo de demonstração é o que torna
  o envio visível a uma pessoa.
- **Entrada simulada não usa a prova de autenticidade do provedor
  real** — essa prova não existe sem o provedor. O equivalente de
  segurança é: a tela só injeta conversa em modo de demonstração,
  com sessão autenticada da propriedade, sobre reserva daquele
  hotel. Em modo real, a prova do provedor permanece a da fatia de
  recebimento seguro.
- **Processamento continua depois de gravar.** A resposta do hotel
  aparece na tela após o trabalho posterior, como no modo real. A
  demonstração não exige resposta síncrona na mesma ação de digitar.
- Limitação honesta (Artigo XV): a demonstração local não prova que
  o provedor real entregará no dia da defesa; prova que o **mesmo**
  sistema de hotel opera sem ele. Não há alta disponibilidade, não
  há garantia de ordem entre mensagens concorrentes, e os cliques de
  funcionário (chegada, saída, resolução) continuam necessários —
  a tela não os automatiza.
