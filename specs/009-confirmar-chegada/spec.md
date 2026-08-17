# Feature Specification: Confirmar Chegada e Boas-vindas

**Feature Branch**: `009-confirmar-chegada`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "A recepção confirma a chegada do hóspede no painel. Isso
registra o momento real da entrada e dispara o pacote de boas-vindas com a programação, o
cardápio, os serviços e os horários da propriedade. A confirmação só é possível para
reservas que ainda não foram encerradas ou canceladas. Reservas cuja data prevista de
entrada já passou sem confirmação são destacadas na fila do dia."
(backlog F2.2)

Restrições já decididas no projeto (entrada do specify): a transição de fase é disparada
pelo clique da recepção, nunca por integração com o sistema de gestão do hotel; a
confirmação persiste o estado e a intenção de envio de forma durável antes de qualquer
entrega ao hóspede; falha de envio não desfaz o check-in; o pacote de boas-vindas só afirma
fato configurado pela propriedade, nunca inventado; a mensagem é operacional de utilidade,
sem oferta comercial — oferta em template separado, fora desta fatia.

## Clarifications

### Session 2026-08-17

- Q: When the hotel has several published facts in schedule, menu, services, and hours, must the welcome pack include every active item in those four categories? → A: Não. O pacote é uma mensagem curta (template de utilidade): confirma a chegada, leva até três informações de entrada configuradas pela propriedade (horário do café, wi-fi, horário do checkout) e termina com um convite a perguntar pelo mesmo canal. Uma única pergunta ao final; texto fixo antes de cada variável. O catálogo completo não entra no template — responde sob demanda na janela de 24h (F3.3). Variável de template não pode carregar catálogo inteiro (quebra de linha, tabulação ou mais de 4 espaços seguidos). Regras da casa continuam fora.
- Q: How does the property choose the at most three pieces of arrival information that go into that short message? → A: Três slots nomeados na configuração da propriedade (café, wi-fi, checkout) — chaves `boas_vindas_cafe`, `boas_vindas_wifi`, `boas_vindas_checkout`. Texto fixo do template fica congelado na aprovação; slots móveis exigiriam novo template. Validar ao salvar (recusar quebra de linha, tabulação, mais de 4 espaços seguidos). Os três são obrigatórios; semeados na instalação. Slot vazio: a mensagem não sai e a reserva é sinalizada na fila do dia. Check-in não é desfeito.
- Q: After reception fills the three slots, should the welcome still go out for a guest who already checked in while a slot was empty? → A: Sim, com dois limites. (1) A passagem automática só envia para reserva `hospedado` **e** com `data_checkin_prevista` igual ao dia corrente — boas-vindas tem validade curta, e sem o limite encher os slots dias depois dispararia rajada de template pago, inclusive para quem já saiu. Reserva mais antiga mantém a sinalização na fila e não recebe envio automático; a recepção decide. (2) “Exatamente um pacote” é garantia de unicidade no banco, não verificação em código — duas execuções simultâneas do worker enviariam duas vezes. Reaproveitar a fila e o worker da F1.2, sem mecanismo novo.
- **Correção (17/08/2026, no planejamento).** A resposta da terceira pergunta definiu a janela
  de validade como `data_checkin_prevista` igual ao dia corrente. O eixo estava errado: hóspede
  que chega às 23h30 com slot vazio, slots preenchidos às 23h40 e varredura às 00h05 sai da
  elegibilidade porque o dia civil virou — e o pacote nunca sai, sem erro nenhum. A janela
  passa a ser contada **a partir do instante real do check-in** (`checkin_em`), com duração
  configurada pela propriedade e padrão de 12 horas. A intenção da decisão original
  (boas-vindas têm validade curta; completar a configuração não pode disparar rajada para quem
  já saiu) permanece intacta — muda o que se mede.
- Q: Who may edit the three welcome slots — reception, management, or both? → A: Recepção grava; gestão só lê; perfil operacional recusado — igual ao catálogo. A permissão é por grupo de chaves, não pela configuração inteira: operação própria (`alterar_texto_de_boas_vindas`) cobrindo exclusivamente `boas_vindas_cafe`, `boas_vindas_wifi` e `boas_vindas_checkout`. Não criar permissão genérica de alterar configuração da propriedade: ali convivem texto operacional de balcão (da recepção) e parâmetro de comportamento (`horas_ate_reenvio`, janela de corte, duração de sessão, periodicidade de coleta), que é da gestão e entra em fatia futura como operação própria. Permissão pela tabela faria a recepção herdar por acidente o poder de mudar como o sistema se comporta com o hóspede.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confirmar a chegada no painel (Priority: P1)

Como recepcionista, quero confirmar no painel que o hóspede chegou, para o sistema registrar
o instante real da entrada e passar a reserva para hospedado — o hotel passa a tratar aquela
pessoa como já no estabelecimento, e o clique humano continua sendo a única ponte com o que
aconteceu no balcão.

**Why this priority**: Sem este clique, nada dispara e o sistema continua achando que a
pessoa não chegou. É a travessia de fronteira da chegada: o produto não se integra ao
sistema de gestão do hotel, então a confirmação é ação da recepção, não detecção automática.

**Independent Test**: Pode ser testado autenticando como recepção, confirmando a chegada de
uma reserva elegível, e verificando que o status passa a hospedado, que o momento real da
entrada fica registrado e é distinto da data prevista, e que a reserva deixa de aparecer
como chegada atrasada na fila do dia.

**Acceptance Scenarios**:

1. **Given** uma sessão autenticada de perfil de recepção e uma reserva da propriedade da
   sessão em estado a partir do qual a chegada é permitida (ficha completa, ficha parcial ou
   chegará sem cadastro prévio), **When** a recepção confirma a chegada, **Then** a reserva
   passa a hospedado e o momento real da entrada fica gravado.
2. **Given** uma confirmação de chegada bem-sucedida, **When** se consulta o momento
   registrado, **Then** ele corresponde ao instante da confirmação — não à data prevista de
   entrada.
3. **Given** uma reserva cuja data prevista de entrada já passou e que estava destacada como
   chegada não confirmada, **When** a recepção confirma a chegada, **Then** o destaque
   desaparece na consulta seguinte da fila do dia.

---

### User Story 2 - Disparar o pacote curto de boas-vindas (Priority: P1)

Como hóspede que acabou de ser recebido no balcão, quero receber em seguida uma mensagem
curta que confirma a chegada, traz o horário do café, o wi-fi e o horário do checkout e me
convida a perguntar o que eu quiser por ali — para eu ter o essencial na subida ao quarto
e saber que o restante se pede na conversa, sem um mural de cardápio no primeiro recado e
sem promoção disfarçada de utilidade.

**Why this priority**: É o valor visível da chegada para o hóspede e o que abre a janela
de conversa. Despejar o catálogo no template é inviável no canal (variável não aceita
quebra de linha nem texto corrido longo) e reclassificaria o recado; o catálogo completo
responde depois, sob demanda (F3.3).

**Independent Test**: Pode ser testado confirmando a chegada de uma reserva cuja propriedade
tem informações de entrada configuradas, inspecionando a mensagem entregue (via porta falsa
de mensageria) e verificando: confirmação de chegada, as três informações de entrada
(café, wi-fi, checkout), convite a perguntar, ausência de catálogo completo, ausência de
oferta e unicidade do disparo.

**Acceptance Scenarios**:

1. **Given** uma confirmação de chegada bem-sucedida, **When** o envio do pacote é
   processado, **Then** o hóspede recebe exatamente uma mensagem curta de boas-vindas no
   telefone de contato da reserva, confirmando a chegada, com café, wi-fi e checkout da
   propriedade e um convite a perguntar pelo mesmo canal.
2. **Given** o texto do pacote montado para envio, **When** ele é inspecionado, **Then** cada
   fato afirmado é uma informação de entrada configurada pela propriedade, originada do que
   a casa publica — nenhum fato é inventado; o catálogo ativo completo não aparece no corpo;
   a categoria regras não entra.
3. **Given** o texto do pacote montado para envio, **When** ele é inspecionado, **Then** não
   há oferta comercial, desconto, promoção, convite de compra nem linguagem de marketing —
   só boas-vindas operacionais — e o recado termina com uma única pergunta/convite a tirar
   dúvidas, com texto fixo antes de cada informação variável.
4. **Given** uma reserva cuja chegada já foi confirmada e cujo pacote já foi disparado,
   **When** ninguém altera aquela reserva, **Then** o sistema não dispara um segundo pacote
   de boas-vindas para a mesma reserva.

---

### User Story 3 - Recusar confirmação inválida sem corromper o ciclo (Priority: P1)

Como recepcionista, quero que o sistema recuse confirmar chegada de reserva já encerrada,
já cancelada, já hospedada ou ainda só aguardando cadastro, com recusa clara, para um clique
no lugar errado não reabrir estadia, não hospedar quem foi cancelado e não pular a máquina
de estados já vigente.

**Why this priority**: A garantia de transição mora no ciclo de vida da reserva. Confirmar o
que não pode ser confirmado corromperia o histórico — exatamente o que a regra de estados
existe para impedir.

**Independent Test**: Pode ser testado tentando confirmar chegada em cada estado recusado e
verificando que o status não muda, que o momento de entrada não é gravado (ou permanece o
já existente, no caso de já hospedado) e que nenhum pacote de boas-vindas nasce.

**Acceptance Scenarios**:

1. **Given** uma reserva encerrada ou cancelada, **When** a recepção tenta confirmar a
   chegada, **Then** a operação é recusada, o status permanece e nenhum pacote é disparado.
2. **Given** uma reserva já hospedada, **When** a recepção confirma de novo, **Then** a
   operação é recusada, o momento de entrada já registrado permanece intacto e um segundo
   pacote não é criado.
3. **Given** uma reserva ainda aguardando cadastro (nem ficha consolidada, nem marcada como
   chegará sem cadastro prévio), **When** a recepção tenta confirmar a chegada, **Then** a
   operação é recusada — a máquina de estados vigente não admite esse salto.
4. **Given** uma reserva de ficha parcial ou marcada como chegará sem cadastro prévio,
   **When** a recepção confirma a chegada, **Then** a confirmação é aceita: ficha incompleta
   ou ausência de cadastro prévio não bloqueiam o check-in no balcão.

---

### User Story 4 - Destacar na fila quem deveria ter chegado e não foi confirmado (Priority: P1)

Como recepcionista, quero ver destacadas na fila do dia as reservas cuja data prevista de
entrada já passou e que ainda não foram confirmadas, para o clique esquecido não falhar em
silêncio — o sistema não sabe se a pessoa chegou, mas sabe que deveria ter chegado.

**Why this priority**: A ausência de ação humana precisa ser visível. Sem o destaque, o
hóspede simplesmente não recebe as boas-vindas e ninguém reclama de uma mensagem que não
chegou. Esta fatia torna a omissão perceptível; não a elimina.

**Independent Test**: Pode ser testado consultando a fila do dia com uma reserva atrasada
sem confirmação, uma reserva do dia ainda no horário e uma já hospedada, e verificando que
só a atrasada não confirmada aparece destacada.

**Acceptance Scenarios**:

1. **Given** uma reserva da propriedade da sessão cuja data prevista de entrada é anterior
   ao dia corrente e cujo status ainda não é hospedado nem cancelado, **When** a recepção
   consulta a fila do dia, **Then** aquela reserva aparece com destaque distinguível de
   chegada não confirmada.
2. **Given** uma reserva cuja data prevista de entrada é o dia corrente e que ainda não foi
   confirmada, **When** a recepção consulta a fila do dia, **Then** a reserva aparece na
   fila, porém sem o destaque de atraso — o dia previsto ainda não venceu.
3. **Given** uma reserva já hospedada ou cancelada, **When** a fila do dia é consultada,
   **Then** ela não aparece como chegada não confirmada (hospedada pode permanecer na fila
   do turno sem o destaque de omissão; cancelada não integra a fila).

---

### User Story 5 - Isolar a confirmação por hotel e por perfil (Priority: P1)

Como responsável pelos dados da propriedade, quero que só a recepção do próprio hotel
confirme chegada, que gestão e operação recebam recusa, e que a reserva de um hotel nunca
seja hospedada por sessão de outro, para o clique de fronteira não vazar entre casas nem
cair em perfil de consulta.

**Why this priority**: Multi-tenant e autorização já existem; esta fatia é a primeira que
dispara a transição para hospedado e precisa herdar essas fronteiras. Gestão não altera dado
de domínio; operação não opera o balcão.

**Independent Test**: Pode ser testado tentando confirmar chegada com cada perfil e com
sessão de outro hotel, verificando recusas e isolamento, sem disparar pacote nos caminhos
recusados.

**Acceptance Scenarios**:

1. **Given** uma reserva do hotel A, **When** uma sessão do hotel B tenta confirmar a
   chegada, **Then** a operação é recusada sem revelar que a reserva existe, e o status não
   muda.
2. **Given** uma sessão de perfil de gestão ou operacional, **When** tenta confirmar a
   chegada de uma reserva da própria propriedade, **Then** a operação é recusada.
3. **Given** uma sessão de recepção, **When** confirma a chegada de uma reserva elegível da
   própria propriedade, **Then** a operação é aceita.

---

### User Story 6 - Guardar as três informações de entrada da propriedade (Priority: P1)

Como recepcionista, quero gravar o horário do café, o wi-fi e o horário do checkout da casa
em três campos curtos da propriedade, e ser recusada na hora se o texto for vazio ou
inválido para o canal, para o recado de chegada ter sempre as três variáveis preenchidas e
o erro aparecer na configuração — não quando o hóspede já está no balcão.

**Why this priority**: O template de utilidade tem três variáveis com rótulo fixo. Variável
vazia ou com quebra de linha é recusada pelo canal. Validar só no envio faria a falha
coincidir com a chegada, que é exatamente o silêncio que esta fatia existe para evitar.

**Independent Test**: Pode ser testado gravando os três valores válidos, tentando gravar
vazio ou com quebra de linha/tabulação/espaços demais, e confirmando uma chegada com slot
ausente: check-in ocorre, mensagem não sai, fila do dia sinaliza. Completar os slots em
seguida faz o pacote sair para quem chegou no mesmo dia — e não faz sair para quem chegou
antes.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção, **When** grava os três campos (café, wi-fi, checkout)
   com texto visível e sem quebra de linha, tabulação nem mais de quatro espaços seguidos,
   **Then** os valores ficam na configuração daquela propriedade e passam a ser os usados
   no pacote seguinte.
2. **Given** uma tentativa de gravar qualquer um dos três campos vazio, só com espaços, com
   quebra de linha, com tabulação ou com mais de quatro espaços seguidos, **When** a
   recepção confirma a gravação, **Then** a alteração é recusada na hora e o valor anterior
   permanece.
3. **Given** uma propriedade cuja instalação acabou de ocorrer, **When** se consulta a
   configuração, **Then** os três campos já existem preenchidos (não vazios), prontos para
   o hotel substituir pelo texto real da casa.
4. **Given** uma reserva elegível e pelo menos um dos três campos vazio ou ausente, **When**
   a recepção confirma a chegada, **Then** a reserva fica hospedada, o pacote **não** é
   enviado, e a fila do dia apresenta indicação distinguível de que as boas-vindas não
   saíram — distinta do destaque de chegada atrasada não confirmada.
5. **Given** uma sessão de gestão, **When** consulta os três campos, **Then** a leitura é
   permitida; **When** tenta gravar qualquer um deles, **Then** a alteração é recusada. Uma
   sessão de perfil operacional é recusada na leitura e na gravação, e uma sessão de outro
   hotel não alcança os campos da propriedade alheia.
6. **Given** uma sessão de recepção autorizada a gravar os três campos, **When** tenta
   alterar um parâmetro de comportamento da propriedade (por exemplo o prazo de reenvio ou a
   janela de corte), **Then** a permissão concedida nesta fatia não a alcança.

---

### User Story 7 - Recuperar as boas-vindas recentes depois de completar a configuração (Priority: P2)

Como recepcionista que descobriu pela fila que as boas-vindas não saíram, quero que
preencher os três campos faça a mensagem sair sozinha para quem acabou de chegar — e não para
quem chegou dias atrás — para o hóspede que está no hotel agora receber o recado sem eu
clicar de novo, e para completar a configuração não virar uma rajada de mensagens tardias.

**Why this priority**: Sem a recuperação, a sinalização na fila mostra a falha mas o hóspede
nunca recebe nada, e a conversa não abre. Sem o limite de validade, encher os slots depois
de dias dispararia recado pago para gente que já fez checkout — pior do que o silêncio.

**Independent Test**: Pode ser testado com duas reservas hospedadas sem boas-vindas — uma com
check-in de minutos atrás, outra com check-in de dias atrás — completando os três slots e
verificando que apenas a recente recebe exatamente um pacote, e que a antiga continua
sinalizada e sem envio. O caso da virada de dia (check-in poucos minutos antes da meia-noite,
processamento poucos minutos depois) tem de continuar elegível.

**Acceptance Scenarios**:

1. **Given** uma reserva hospedada cujo check-in foi confirmado dentro da janela de validade
   configurada e cujas boas-vindas não saíram por slot ausente, **When** os três slots passam
   a estar preenchidos e válidos e o processamento seguinte ocorre, **Then** aquela reserva
   recebe exatamente um pacote de boas-vindas e deixa de constar como boas-vindas não
   enviadas.
2. **Given** uma reserva hospedada cujo check-in é anterior à janela de validade e cujas
   boas-vindas não saíram, **When** os três slots passam a estar preenchidos e o
   processamento seguinte ocorre, **Then** nenhum pacote é enviado automaticamente e a
   sinalização na fila permanece — a decisão de enviar (se ainda fizer sentido) fica com a
   recepção.
3. **Given** uma reserva que já recebeu o pacote de boas-vindas, **When** o processamento de
   recuperação roda de novo, ou roda em paralelo, **Then** nenhum segundo pacote é criado
   para aquela reserva.
4. **Given** uma reserva cujo check-in foi confirmado poucos minutos antes da virada do dia
   civil, **When** o processamento de recuperação ocorre poucos minutos depois da virada —
   portanto em outro dia, com a data prevista de entrada já no passado — **Then** a reserva
   continua elegível e recebe o pacote: a janela conta do instante do check-in, não do
   calendário.

---

### Edge Cases

- Falha no envio do pacote depois da confirmação: a reserva permanece hospedada, o momento
  de entrada permanece gravado, a pendência fica visível para nova tentativa; o check-in não
  é desfeito.
- Retry técnico de um envio que eventualmente sucede: o hóspede recebe no máximo um pacote
  de boas-vindas por reserva; o histórico não acumula um segundo recado de chegada.
- Duas execuções simultâneas do processamento de envio para a mesma reserva: apenas um
  pacote passa a existir; a segunda é recusada pela garantia de unicidade do armazenamento,
  não por conferência prévia em código.
- Um ou mais slots de entrada vazios ou ausentes no momento da confirmação: o check-in
  ocorre; o pacote **não** sai; a reserva aparece sinalizada na fila do dia. Não se monta
  mensagem com variável em branco.
- Slots completados depois: reserva hospedada cujo check-in ocorreu dentro da janela de
  validade recebe o pacote na passagem seguinte; reserva com check-in anterior à janela não
  recebe envio automático e mantém a sinalização na fila.
- Virada do dia civil entre o check-in e o processamento: não afeta a elegibilidade. Chegada às
  23h30, slots preenchidos às 23h40 e passagem às 00h05 continuam dentro da janela — medir por
  data de calendário faria o pacote nunca sair, sem erro nenhum.
- Chegada antecipada (check-in confirmado antes da data prevista de entrada): elegível para a
  recuperação, porque a janela conta do check-in. Enquanto a data prevista não chega, a reserva
  não aparece na fila do dia, então a sinalização de boas-vindas não enviadas só fica visível a
  partir daquele dia.
- Reserva hospedada sem instante de check-in registrado (só alcançável por escrita direta no
  armazenamento): não é elegível ao envio automático. Ausência de instante não é tratada como
  chegada recente.
- Reserva já encerrada (checkout feito) que nunca recebeu boas-vindas: não recebe envio
  automático — deixou de estar hospedada.
- Valor com quebra de linha, tabulação ou mais de quatro espaços seguidos: recusado na
  gravação da configuração, não na tentativa de envio ao hóspede.
- Catálogo ativo completo da propriedade: não é copiado para o pacote, mesmo que exista
  item nas cinco categorias.
- Configuração de outro hotel: não entra no pacote nem na consulta da propriedade da sessão.
- Único dado pessoal do hóspede no corpo do pacote: o primeiro nome; telefone, documento,
  endereço e demais campos da ficha não aparecem.
- Dois hóspedes na mesma reserva: o pacote vai ao telefone de contato da reserva (titular),
  uma vez — não há um pacote por acompanhante.
- Duas reservas distintas no mesmo telefone: cada confirmação dispara o próprio pacote.
- Confirmação de reserva futura (data prevista ainda não chegou): permitida se o estado for
  elegível — chegada antecipada no balcão não espera o calendário. Continua recusada se o
  estado for inválido.
- Reserva de ficha parcial: confirmação permitida; o balcão completa o que faltar no fluxo
  tradicional, fora desta fatia.
- Conteúdo da mensagem nunca aparece em log; logs registram identificadores, hotel, resultado
  da transição e código de envio.
- Inferência por mensagem recebida de hóspede ainda não confirmado, confirmação em lote ao
  fim do pico e tela React do painel **não** fazem parte desta fatia.
- Checkout, cancelamento, classificação de mensagem do hóspede, resposta a dúvida e pulso do
  segundo dia **não** fazem parte desta fatia.
- Oferta comercial, desconto de hospedagem e template de marketing **não** fazem parte
  desta fatia nem via anexo no pacote de boas-vindas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A recepção MUST poder confirmar a chegada de uma reserva da própria
  propriedade que esteja em ficha recebida (completa), ficha parcial ou chegará sem cadastro
  prévio.
- **FR-002**: A confirmação bem-sucedida MUST alterar o status da reserva para hospedado e
  MUST gravar o momento real da entrada (instante da confirmação, não a data prevista).
- **FR-003**: Ficha parcial e marcação de chegará sem cadastro prévio MUST NOT impedir a
  confirmação de chegada.
- **FR-004**: Confirmação MUST ser recusada quando a reserva estiver encerrada, cancelada,
  já hospedada ou ainda aguardando cadastro. A recusa MUST deixar claro que a operação não
  ocorreu. Status e momento de entrada MUST permanecer como estavam.
- **FR-005**: Tentativa recusada MUST NOT criar pendência de envio nem mensagem de
  boas-vindas.
- **FR-006**: A confirmação MUST concluir com a reserva persistida no novo estado. Quando os
  três slots de entrada estão preenchidos e válidos, a intenção de envio do pacote MUST ser
  registrada de forma durável e a entrega MUST acontecer em processamento posterior — não
  na mesma operação síncrona que confirma o clique à recepção.
- **FR-007**: Falha no envio do pacote MUST NOT desfazer o status hospedado nem apagar o
  momento de entrada já gravado.
- **FR-008**: O retry técnico de um envio falho MUST NOT resultar em um segundo pacote de
  boas-vindas distinto para a mesma reserva — no máximo um pacote lógico por reserva neste
  fluxo. A unicidade MUST ser garantida pelo armazenamento (restrição de unicidade), não por
  verificação prévia em código: duas execuções simultâneas do processamento MUST resultar em
  um único pacote.
- **FR-009**: Ao confirmar a chegada com os três slots válidos, o sistema MUST registrar
  exatamente uma pendência de envio do pacote de boas-vindas para o telefone de contato
  daquela reserva.
- **FR-010**: O pacote MUST ser uma mensagem curta que (a) confirma a chegada, (b) inclui
  exatamente as três informações de entrada da propriedade — café, wi-fi e checkout — e
  (c) termina convidando o hóspede a perguntar o que quiser pelo mesmo canal. MUST haver
  exatamente uma pergunta/convite ao final, com texto fixo imediatamente antes de cada
  informação variável.
- **FR-011**: Cada fato afirmado no pacote MUST ser o valor configurado do slot
  correspondente daquela propriedade, sem invenção. Configuração de outro hotel MUST NOT
  aparecer. O catálogo ativo completo MUST NOT ser incluído no corpo do pacote — a resposta
  sob demanda a partir do catálogo pertence à fatia posterior de dúvida (F3.3).
- **FR-012**: O pacote MUST NOT conter oferta comercial, desconto, promoção, convite de
  compra nem linguagem de marketing. Boas-vindas e oferta comercial permanecem em recados
  separados; a oferta não entra nesta fatia.
- **FR-013**: A categoria regras MUST NOT entrar no pacote de boas-vindas.
- **FR-014**: O corpo do pacote MUST NOT conter dado pessoal do hóspede além do primeiro
  nome.
- **FR-015**: Todo envio ao hóspede MUST passar por uma porta de mensageria substituível, de
  modo que sucesso e falha possam ser exercitados sem rede de provedor real.
- **FR-016**: O pacote efetivamente enviado (ou tentado com registro) MUST aparecer no
  histórico de conversa da reserva como mensagem de saída, com estado de entrega observável
  (pendente, enviada, entregue ou falha).
- **FR-017**: A fila do dia da recepção MUST destacar de forma distinguível a reserva cuja
  data prevista de entrada é anterior ao dia corrente e cujo status ainda não é hospedado
  nem cancelado (chegada não confirmada).
- **FR-018**: Após confirmação bem-sucedida, a reserva MUST deixar de constar como chegada
  não confirmada na consulta seguinte da fila do dia.
- **FR-019**: Reserva do dia corrente ainda não confirmada MUST aparecer na fila do dia sem
  o destaque de atraso.
- **FR-020**: Toda leitura e toda confirmação MUST considerar o hotel da sessão. Reserva de
  um hotel MUST NOT ser visível como confirmável nem alterável por outro.
- **FR-021**: Confirmar chegada MUST ser exclusivo do perfil de recepção. Gestão e perfil
  operacional MUST receber recusa.
- **FR-022**: Tentativa de confirmar reserva de outro hotel MUST ser recusada sem confirmar
  que a reserva existe.
- **FR-023**: Conteúdo de mensagem e demais dados pessoais NUNCA MUST aparecer em log;
  logs registram identificadores, hotel, resultado da transição e código de erro.
- **FR-024**: Esta fatia MUST NOT realizar checkout, cancelar reserva, classificar mensagem
  de hóspede, responder dúvida, disparar pulso, inferir chegada a partir de mensagem
  recebida, nem oferecer confirmação em lote.
- **FR-025**: Esta fatia MUST NOT ligar o protótipo visual do painel como critério de
  pronto. O comportamento MUST ser observável pela operação de confirmação, pela
  configuração dos três slots e pela fila do dia já usadas nas fatias de hospedagem.
- **FR-026**: A propriedade MUST ter exatamente três slots de entrada, nomeados e de
  rótulo fixo: café, wi-fi e checkout. MUST NOT haver slots móveis nem substituição por
  item de catálogo escolhido na hora — isso quebraria o texto fixo do template já
  aprovado.
- **FR-027**: A recepção MUST poder ler e gravar os três slots da própria propriedade.
  Gestão MUST poder ler e MUST NOT gravar. Perfil operacional MUST receber recusa. Slot
  de um hotel MUST NOT ser visível nem alterável por outro.
- **FR-027a**: A autorização de gravação MUST ser específica desses três slots, não da
  configuração da propriedade como um todo. Parâmetro de comportamento do sistema (prazo de
  reenvio, janela de corte, duração de sessão, periodicidade de coleta) MUST permanecer fora
  do que esta permissão alcança, e MUST NOT se tornar alterável pela recepção como efeito
  desta fatia.
- **FR-028**: A gravação de um slot MUST ser recusada na hora se o valor for vazio, só
  espaços, contiver quebra de linha, tabulação, ou mais de quatro espaços seguidos. A
  recusa MUST ocorrer na configuração, não no envio ao hóspede.
- **FR-029**: A instalação inicial MUST semear os três slots com texto não vazio e válido
  para o canal, para a primeira confirmação não depender de alguém lembrar de cadastrar.
- **FR-030**: Se, no momento da confirmação, qualquer slot estiver vazio ou ausente, o
  sistema MUST NOT enviar o pacote e MUST sinalizar a reserva na fila do dia com indicação
  distinguível de boas-vindas não enviadas. O status hospedado e o momento de entrada
  MUST permanecer. Essa indicação MUST ser distinta do destaque de chegada não confirmada.
- **FR-031**: Quando os três slots passarem a estar preenchidos e válidos, o processamento
  seguinte MUST enviar exatamente um pacote para cada reserva que esteja hospedada, cujo
  instante real de check-in esteja dentro da janela de validade das boas-vindas, e que ainda
  não tenha recebido boas-vindas.
- **FR-031a**: A janela de validade MUST ser contada a partir do instante real do check-in, e
  MUST NOT ser expressa como data de calendário. Virada do dia civil entre o check-in e o
  processamento MUST NOT retirar a reserva da elegibilidade.
- **FR-031b**: A duração da janela MUST vir da configuração da propriedade, não de constante
  no código, no mesmo padrão dos demais prazos operacionais. A propriedade sem o valor
  configurado MUST ficar sem envio de recuperação, com registro do prazo ausente — nunca com
  um prazo suposto.
- **FR-032**: Esse envio de recuperação MUST NOT alcançar reserva cujo check-in seja anterior
  à janela de validade, ainda que ela nunca tenha recebido boas-vindas. Tal reserva MUST
  manter a sinalização na fila do dia; a decisão de enviar permanece humana e fora do
  automático desta fatia.
- **FR-032a**: Reserva hospedada sem instante de check-in registrado MUST NOT ser alcançada
  pelo envio de recuperação.
- **FR-033**: O envio de recuperação MUST usar a mesma fila durável e o mesmo processamento
  posterior já existentes para mensagens ao hóspede. Esta fatia MUST NOT introduzir
  mecanismo de fila, agendador ou canal novo.

### Key Entities

- **Reserva**: registro da estadia, com status de ciclo de vida, data prevista de entrada e
  momento real de check-in. Nesta fatia, a transição relevante é para hospedado.
- **Momento real de entrada**: instante em que a recepção confirmou a chegada; distinto da
  data prevista.
- **Pacote de boas-vindas**: recado operacional curto e único, ligado a uma reserva:
  confirma a chegada, leva as três informações de entrada (café, wi-fi, checkout) e convoca
  o hóspede a perguntar pelo mesmo canal. Sem oferta comercial e sem o catálogo completo.
- **Slots de entrada**: três valores curtos da configuração da propriedade — café, wi-fi e
  checkout. Obrigatórios, de rótulo fixo, um por variável do recado. Não são itens do
  catálogo.
- **Catálogo ativo**: conjunto de fatos publicados da propriedade. Nesta fatia não é
  despejado no pacote; permanece a fonte para afirmações posteriores sob demanda (F3.3).
- **Pendência de envio de boas-vindas**: intenção durável de entregar o pacote ao telefone
  de contato. Nasce com a confirmação e sobrevive a falha de rede.
- **Chegada não confirmada**: indicação na fila do dia de que a data prevista de entrada já
  passou e a reserva ainda não está hospedada nem cancelada. Torna visível o clique
  esquecido; não substitui o clique.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das confirmações aceitas, a reserva fica hospedada e o momento real
  da entrada fica gravado, distinto da data prevista.
- **SC-002**: Em 100% das tentativas sobre reserva encerrada, cancelada, já hospedada ou
  ainda aguardando cadastro, a operação é recusada, o status não avança para hospedado
  (permanece o que já era) e nascem 0 pacotes de boas-vindas.
- **SC-003**: Em 100% das confirmações aceitas com os três slots válidos, nasce exatamente
  uma pendência de pacote de boas-vindas ligada àquela reserva. Em 100% das confirmações
  aceitas com algum slot vazio ou ausente, nascem 0 envios ao hóspede e 100% dessas
  reservas aparecem sinalizadas na fila do dia.
- **SC-004**: Em 100% dos casos em que o envio falha, a reserva permanece hospedada e
  consultável após a falha, com o momento de entrada intacto.
- **SC-005**: Após retries de um envio que eventualmente sucede, o hóspede recebe no máximo
  um pacote de boas-vindas por reserva (0% de recados duplicados de chegada por
  reprocessamento técnico). Em tentativa de registrar um segundo pacote para a mesma
  reserva, inclusive de execuções concorrentes, 100% das segundas tentativas são recusadas
  pelo armazenamento.
- **SC-006**: Em 100% dos pacotes montados, há exatamente as 3 informações de entrada
  (café, wi-fi, checkout) da propriedade da reserva, 0 cópias do catálogo ativo completo,
  0 fatos inventados e 0 valores de outro hotel; 100% dos pacotes confirmam a chegada e
  terminam com um convite a perguntar.
- **SC-007**: Em 100% dos pacotes montados, há 0 ofertas comerciais, descontos, promoções ou
  convites de compra.
- **SC-008**: Em 100% dos pacotes montados, o único dado pessoal do hóspede no corpo é o
  primeiro nome.
- **SC-009**: Em verificação com reserva cuja data prevista já venceu e status ainda não é
  hospedado nem cancelado, 100% das consultas da fila do dia a apresentam com o destaque de
  chegada não confirmada; após a confirmação, 0% das consultas seguintes a mantêm com esse
  destaque.
- **SC-010**: Em verificação com dois hotéis, 100% das tentativas de confirmar reserva
  alheia são recusadas; 0 reservas do hotel A mudam de status por sessão do hotel B.
- **SC-011**: Em verificação com sessão de gestão e com sessão operacional, 100% das
  tentativas de confirmar chegada são recusadas.
- **SC-012**: O caminho confirmação → hospedado → pacote (sucesso e falha) é verificável de
  ponta a ponta sem chamada à rede do provedor real de mensagens e sem tela visual nova.
- **SC-013**: A recepção conclui a confirmação de uma chegada elegível em uma única
  interação, sem etapas intermediárias obrigatórias no painel.
- **SC-014**: Em 100% das tentativas de gravar slot vazio, só com espaços, com quebra de
  linha, tabulação ou mais de quatro espaços seguidos, a gravação é recusada e o valor
  anterior permanece.
- **SC-014a**: Em verificação com sessão de recepção, 100% das tentativas de alterar
  parâmetro de comportamento da propriedade (prazo de reenvio, janela de corte, duração de
  sessão, periodicidade de coleta) continuam sem caminho autorizado nesta fatia; a permissão
  concedida alcança apenas os três slots de boas-vindas.
- **SC-015**: Após a instalação inicial, 100% das propriedades têm os três slots presentes
  e não vazios.
- **SC-016**: Ao completar os três slots, 100% das reservas hospedadas cujo check-in está
  dentro da janela de validade e que não receberam boas-vindas recebem exatamente um pacote na
  passagem seguinte, e 0% das reservas cujo check-in é anterior à janela recebem envio
  automático.
- **SC-016a**: Em verificação com check-in registrado poucos minutos antes da virada do dia
  civil e processamento poucos minutos depois, 100% dessas reservas recebem o pacote — 0% de
  perda por mudança de data de calendário.

## Assumptions

- As fatias F1.1 (reserva e fila do dia), F1.2 (envio durável via porta de mensageria),
  F1.3 (ficha completa/parcial), F1.4 (chegará sem cadastro prévio) e F2.1 (catálogo ativo)
  estão concluídas. Esta fatia dispara o clique que aquelas fatias deixaram preparado.
  Observação de honestidade: com o recado curto, **o envio não lê o catálogo** — a dependência
  de F2.1 deixou de ser funcional nesta fatia e passou a ser de sequência, porque a conversa
  que o recado abre só tem o que responder na F3.3 se houver fatos publicados.
- A máquina de estados já vigente é a fonte da elegibilidade: para hospedado somente a
  partir de ficha recebida, ficha parcial ou sem cadastro prévio. O critério do backlog
  (“recusar encerrada ou cancelada”) é o mínimo; a recusa de ainda aguardando cadastro e de
  já hospedado segue a máquina já garantida no banco e não a reabre. Reserva recém-criada no
  mesmo dia permanece aguardando cadastro até ficha ou até o fluxo de silêncio — esta fatia
  não inventa um atalho.
- O destaque de chegada não confirmada já existe na fila do dia (data prevista anterior ao
  dia corrente, status diferente de hospedado e de cancelado). Esta fatia o torna critério
  de aceite da chegada: a confirmação o desliga, e a omissão continua visível enquanto o
  clique não acontece.
- **Independência estrutural (já decidida):** o envio não roda dentro da operação que
  confirma o clique. A confirmação registra a intenção de envio de forma durável e um
  processamento posterior entrega. Tratamento de erro síncrono na mesma operação **não**
  satisfaz FR-006.
- **Porta de mensageria (já decidida):** todo envio passa pela interface substituível;
  testes usam implementação falsa; nenhum teste chama o provedor real.
- **Template de utilidade e oferta separada (já decidida):** o pacote é recado operacional
  de utilidade. Boas-vindas e oferta comercial permanecem em templates separados; a oferta
  de retorno continua fora do MVP. Embutir desconto no pacote é defeito desta fatia, não
  evolução.
- Um único pacote curto por reserva, não uma mensagem por categoria nem o catálogo inteiro
  numa variável. O canal rejeita variável vazia, com quebra de linha, tabulação ou mais de
  quatro espaços seguidos; despejar o catálogo no template não é enviável. O catálogo
  completo responde sob demanda na janela de 24 horas (F3.3).
- Os três slots vivem na configuração já usada por propriedade (`parametro_hotel`), com as
  chaves `boas_vindas_cafe`, `boas_vindas_wifi` e `boas_vindas_checkout`. Não há tabela nova.
  O limite curto do valor (o mesmo da configuração existente) força a brevidade exigida pelo
  canal. O texto semeado na instalação é um placeholder válido, para o hotel substituir pelo
  fato real da casa antes de hóspede verdadeiro — o valor literal da semente é detalhe de
  planejamento.
- **Permissão por grupo de chaves (já decidida):** a autorização entra como operação própria
  restrita a essas três chaves (`alterar_texto_de_boas_vindas`, só recepção), no padrão de
  `alterar_catalogo`. **Não** se cria permissão genérica de alterar `parametro_hotel`: a
  tabela guarda duas naturezas — texto operacional de balcão, que é da recepção, e parâmetro
  de comportamento (prazo de reenvio, janela de corte, duração de sessão, periodicidade de
  coleta), que é da gestão e ganha operação própria em fatia futura. Permissão pela tabela
  daria à recepção, por acidente, o poder de mudar como o sistema se comporta com o hóspede.
- Regras da casa não entram no pacote; permanecem no catálogo para a fatia de dúvida (F3.3).
- Slot vazio não bloqueia o check-in e **não** degrada o recado com variável em branco: a
  mensagem não sai, e a omissão fica visível na fila.
- **Validade curta das boas-vindas:** o envio de recuperação vale só para quem fez check-in
  dentro da janela configurada (padrão de 12 horas contadas do instante do check-in). Recado de
  chegada que chega dias depois é pior do que não chegar, e sem esse limite completar a
  configuração dispararia uma rajada de mensagens pagas, inclusive para hóspede que já fez
  checkout. **A janela não é medida em dia de calendário:** hóspede que chega às 23h30 e
  processamento que roda às 00h05 estão a 35 minutos de distância, e nenhuma regra de validade
  honesta os separa.
- **Unicidade no armazenamento (já decidida):** “exatamente um pacote por reserva” é
  restrição de unicidade, no mesmo padrão da idempotência do webhook. Conferência prévia em
  código não satisfaz FR-008, porque duas execuções simultâneas do processamento passariam
  as duas pela verificação.
- **Sem mecanismo novo:** a fila durável e o processamento posterior são os já existentes
  para mensagens ao hóspede. Nenhum agendador, fila externa ou canal novo entra nesta fatia.
- Acompanhantes não recebem pacote próprio; o telefone de contato da reserva é o destino.
- Inferência por mensagem de hóspede ainda não confirmado e confirmação em lote (mitigações
  adicionais da jornada) ficam fora — esta fatia entrega a detecção de divergência temporal
  na fila, que já é o máximo exigido pelo backlog. Ampliar mitigação é fatia futura, não
  atalho aqui.
- Checkout (`encerrado`), cancelamento pela recepção e regime de conversa da estadia
  (receber mensagem, classificar, responder) pertencem a fatias posteriores. Status
  hospedado é o sinal de que a conversa *pode* entrar em regime ativo; esta fatia não
  implementa esse regime.
- Superfície de uso: operação de confirmação, gravação dos três slots e fila do dia.
  Ligar o protótipo React continua fora do critério de pronto, no mesmo padrão das fatias
  anteriores.
- Isolamento por propriedade vale mesmo com uma única propriedade cadastrada.
