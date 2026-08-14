# Feature Specification: Controlar o Silêncio

**Feature Branch**: `007-controlar-silencio`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Passado o intervalo configurado para a propriedade sem resposta
do hóspede, o sistema envia um único lembrete, explicando que o cadastro antecipado é
opcional e que sem ele o preenchimento será feito na recepção. Persistindo o silêncio, o
sistema para de insistir e sinaliza na fila do dia que aquela reserva chegará sem cadastro
prévio. Os prazos são configuráveis por propriedade, não fixos."
(backlog F1.4)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Um único lembrete quando o hóspede não responde (Priority: P1)

Como hóspede que recebeu o pedido de cadastro e ainda não respondeu, quero receber no máximo
um lembrete — explicando que o preenchimento antecipado é opcional e que, sem ele, a ficha
será feita na recepção — para não ser cobrado de novo pelo canal depois disso.

**Why this priority**: Não ser intrusivo é requisito do produto, não preferência. Sem o teto
de um único reenvio, a pré-chegada vira insistência e gasta mensagem; sem o lembrete, quem
só esqueceu nunca é avisado.

**Independent Test**: Pode ser testado com uma reserva em aguardo de cadastro cuja coleta já
foi enviada, avançando o relógio além do intervalo da propriedade sem nenhuma resposta do
hóspede, e verificando que nasce exatamente uma mensagem de lembrete com o texto exigido —
e que uma segunda verificação posterior não gera segunda mensagem.

**Acceptance Scenarios**:

1. **Given** uma reserva em aguardo de cadastro cuja mensagem de coleta já foi enviada e o
   hóspede ainda não respondeu, **When** transcorre o intervalo até o reenvio configurado
   para aquela propriedade, **Then** o sistema envia exatamente uma mensagem de lembrete ao
   telefone de contato, declarando que o cadastro antecipado é opcional e que, sem ele, o
   preenchimento será feito na recepção.
2. **Given** uma reserva que já recebeu o lembrete, **When** o silêncio continua e o sistema
   verifica de novo as pendências, **Then** nenhum segundo lembrete é enviado.
3. **Given** o texto do lembrete montado para envio, **When** ele é inspecionado, **Then** o
   único dado pessoal do hóspede presente no corpo é o primeiro nome; telefone, documento,
   endereço e demais campos da ficha não aparecem.

---

### User Story 2 - Silêncio persistente visível na fila, sem bloquear a chegada (Priority: P1)

Como recepcionista, quero ver na fila do dia quais reservas chegarão sem cadastro prévio
depois que o segundo prazo se esgotar sem resposta, para eu me preparar para preencher a
ficha no balcão — e quero que isso não impeça o check-in normal.

**Why this priority**: A ausência de ação do hóspede precisa ser visível no painel (a fila é
a fonte da verdade). Marcar e parar de insistir degrada com segurança para o fluxo
tradicional; bloquear a chegada quebraria a operação.

**Independent Test**: Pode ser testado avançando o relógio até o segundo prazo (janela de
corte antes da data prevista de entrada) sem resposta do hóspede, após o lembrete já ter
sido tratado, e verificando o status operacional, a indicação na fila do dia e a
permanência da reserva como elegível para confirmação de chegada.

**Acceptance Scenarios**:

1. **Given** uma reserva ainda em aguardo de cadastro, já lembrada, sem resposta do hóspede,
   **When** entra a janela de corte configurada para a propriedade (horas antes da data
   prevista de entrada), **Then** a reserva passa ao status de chegará sem cadastro prévio e
   o sistema não envia nenhuma mensagem adicional cobrando o cadastro.
2. **Given** uma reserva marcada como chegará sem cadastro prévio, **When** a recepção
   consulta a fila do dia, **Then** aquela reserva aparece com indicação clara e
   distinguível de “ainda aguardando resposta”, ficha completa, ficha parcial e leitura
   humana.
3. **Given** uma reserva marcada como chegará sem cadastro prévio, **When** se observa o
   ciclo de vida, **Then** ela permanece em estado a partir do qual a confirmação de chegada
   é permitida — a marcação não cancela, não encerra e não impede o check-in posterior.

---

### User Story 3 - Resposta no meio do caminho cancela o lembrete (Priority: P1)

Como hóspede que responde depois da coleta e antes do fim dos prazos, quero que o sistema
não me mande o lembrete (se eu já respondi) e não me marque como silêncio (se eu respondi
depois do lembrete), para o produto respeitar que eu já participei.

**Why this priority**: O critério de aceite da fatia é explícito: resposta entre os prazos
cancela o lembrete pendente. Insistir depois de uma resposta — completa, parcial ou mesmo
irreconhecível — contradiz “não ser intrusivo” e a fatia de interpretação já entregue.

**Independent Test**: Pode ser testado enviando uma resposta do hóspede antes do primeiro
prazo e verificando ausência de lembrete; e enviando resposta após o lembrete mas antes da
janela de corte e verificando que a reserva não é marcada como chegará sem cadastro.

**Acceptance Scenarios**:

1. **Given** uma reserva em aguardo de cadastro cuja coleta já foi enviada e o primeiro prazo
   ainda não venceu, **When** o hóspede envia qualquer resposta (completa, parcial ou
   irreconhecível), **Then** o lembrete pendente não é enviado.
2. **Given** uma reserva que já recebeu o lembrete e ainda não entrou na janela de corte,
   **When** o hóspede envia qualquer resposta, **Then** a reserva não é marcada como chegará
   sem cadastro prévio — o desfecho segue a interpretação da ficha (completa, parcial ou
   leitura humana).
3. **Given** uma reserva já consolidada como ficha completa ou parcial, **When** os prazos de
   silêncio vencem, **Then** o sistema não envia lembrete e não sobrescreve o status para
   chegará sem cadastro prévio.

---

### User Story 4 - Prazos da propriedade, não do produto (Priority: P2)

Como gestor da propriedade, quero que o intervalo até o lembrete e a janela de corte antes
da entrada prevista sejam configuração daquele hotel, para um hotel de passagem curta e um
de estadia longa não compartilharem o mesmo ritmo de cobrança.

**Why this priority**: Parâmetro operacional não é constante de código. Os dois prazos existem
na configuração da propriedade desde a modelagem; esta fatia é a primeira que os usa de
fato.

**Independent Test**: Pode ser testado com duas propriedades (ou a mesma propriedade com
valores distintos em execuções separadas) e verificando que o momento do lembrete e o
momento da marcação acompanham os valores configurados — não um intervalo embutido no
comportamento.

**Acceptance Scenarios**:

1. **Given** uma propriedade com intervalo até o reenvio configurado em um valor A, **When**
   o silêncio dura menos que A, **Then** nenhum lembrete é enviado.
2. **Given** a mesma situação com o intervalo alterado para um valor B distinto, **When** o
   silêncio atinge B, **Then** o lembrete é enviado nesse novo ritmo, sem exigir mudança de
   regra de negócio.
3. **Given** duas propriedades com janelas de corte diferentes, **When** cada uma tem uma
   reserva silenciosa na respectiva janela, **Then** cada uma é marcada no prazo da própria
   propriedade.

---

### Edge Cases

- Coleta ainda não enviada (pendente ou falha de envio): o sistema não envia lembrete de uma
  mensagem que o hóspede não recebeu; na janela de corte, a reserva ainda pode ser marcada
  como chegará sem cadastro prévio para a recepção se preparar.
- Reserva criada já dentro da janela de corte (entrada prevista muito próxima): o sistema
  não envia lembrete e marca como chegará sem cadastro prévio quando a verificação ocorrer
  — prioriza não ser intrusivo e tornar a omissão visível.
- Data prevista de entrada já passou e a reserva segue em aguardo de cadastro: não envia
  lembrete; marca como chegará sem cadastro prévio.
- Falha transitória no envio do lembrete: a reserva permanece; o sistema tenta de novo o
  mesmo lembrete sem criar um segundo pedido ao hóspede.
- Reserva cancelada, hospedada, encerrada, com ficha completa ou parcial: fora do controle
  de silêncio.
- Resposta irreconhecível ou falha de interpretação (já sinalizada para leitura humana):
  conta como resposta; cancela lembrete e impede a marcação por silêncio.
- Duas reservas distintas no mesmo telefone: cada uma tem o próprio ciclo de silêncio.
- Verificação periódica que não rodou no instante exato do prazo: o efeito (lembrete ou
  marcação) ocorre na verificação seguinte; atraso da verificação não gera mensagem extra
  nem perde a marcação.
- Conteúdo de mensagem e demais dados pessoais não aparecem em log operacional.
- Confirmação de chegada (pacote de boas-vindas), catálogo, atendimento conversacional e
  tela para editar os prazos no painel **não** fazem parte desta fatia.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST verificar periodicamente as reservas em aguardo de cadastro de
  cada propriedade e aplicar as regras de lembrete e de marcação descritas nesta spec.
- **FR-002**: O intervalo até o lembrete MUST ser lido da configuração da propriedade
  (`horas_ate_reenvio`). A janela de corte antes da data prevista de entrada MUST ser lida
  da configuração da propriedade (`horas_corte_antes_checkin`). Nenhum dos dois prazos MUST
  ser constante de regra de negócio.
- **FR-003**: Cada propriedade nova MUST nascer com os dois prazos já configurados (valores
  padrão do bootstrap). Ausência da chave na propriedade MUST falhar de forma explícita, não
  assumir um número embutido.
- **FR-004**: O relógio do primeiro prazo MUST contar a partir do envio bem-sucedido da
  mensagem de coleta daquela reserva.
- **FR-005**: Quando o primeiro prazo vencer sem nenhuma mensagem recebida do hóspede para
  aquela reserva, e a reserva ainda estiver em aguardo de cadastro, e ainda não estiver na
  janela de corte nem com data de entrada prevista já vencida, o sistema MUST enviar
  exatamente um lembrete.
- **FR-006**: O lembrete MUST declarar, em linguagem clara, que o cadastro antecipado é
  opcional e que, sem ele, o preenchimento será feito na recepção.
- **FR-007**: O sistema MUST NOT enviar um segundo lembrete de cadastro para a mesma
  reserva, em nenhuma hipótese — inclusive nova verificação, nova tentativa técnica após
  falha de envio já sucedida, ou reexecução após interrupção.
- **FR-008**: O único dado pessoal do hóspede permitido no corpo do lembrete é o primeiro
  nome.
- **FR-009**: Quando a reserva ainda estiver em aguardo de cadastro, sem resposta do
  hóspede, e a janela de corte da propriedade for atingida (ou a data prevista de entrada já
  tiver passado), o sistema MUST transicionar a reserva para `sem_cadastro_previo` e MUST
  NOT enviar nova mensagem cobrando o cadastro.
- **FR-010**: Reserva em `sem_cadastro_previo` MUST permanecer elegível para confirmação de
  chegada posterior (transição já prevista para `hospedado`); a marcação MUST NOT cancelar
  nem encerrar a reserva.
- **FR-011**: Qualquer mensagem recebida do hóspede naquela reserva, enquanto o ciclo de
  silêncio estiver aberto, MUST cancelar o lembrete ainda não enviado e MUST impedir a
  transição para `sem_cadastro_previo`.
- **FR-012**: Reserva já em `ficha_recebida` ou `ficha_parcial` MUST ficar fora do lembrete e
  da marcação por silêncio.
- **FR-013**: A fila do dia da recepção MUST exibir indicação distinguível de que a reserva
  chegará sem cadastro prévio, além dos estados já existentes (aguardando, completa,
  parcial, leitura humana).
- **FR-014**: Gravação da intenção de enviar o lembrete MUST ocorrer antes da tentativa de
  envio; falha de envio MUST NOT apagar a reserva nem gerar um segundo lembrete distinto ao
  hóspede.
- **FR-015**: Conteúdo de mensagem e demais dados pessoais NUNCA MUST aparecer em log de
  aplicação; logs registram apenas identificadores e códigos de resultado.
- **FR-016**: Lembrete e marcação MUST respeitar o hotel da reserva: prazo e fila de um
  hotel MUST NOT afetar o outro.
- **FR-017**: Esta fatia MUST NOT confirmar check-in, enviar pacote de boas-vindas, abrir
  atendimento conversacional, transcrever dados para o PMS nem oferecer tela de edição dos
  prazos — alterar prazo no MVP permanece configuração da propriedade (já existente), não
  funcionalidade nova de painel.

### Key Entities

- **Lembrete de cadastro**: única mensagem proativa de reenvio da coleta, enviada após o
  primeiro prazo de silêncio; explica opcionalidade e o fallback no balcão.
- **Indicador de reenvio já realizado**: marca de domínio na reserva que garante o teto de
  um lembrete (`reenvio_realizado`).
- **Status `sem_cadastro_previo`**: estado da reserva após o segundo prazo sem resposta;
  significado operacional “chegará sem cadastro prévio”; permite check-in posterior.
- **Prazos da propriedade**: `horas_ate_reenvio` (intervalo desde o envio da coleta até o
  lembrete) e `horas_corte_antes_checkin` (janela, em horas, antes da data prevista de
  entrada, a partir da qual o sistema para de insistir e marca a reserva).
- **Fila do dia**: visão operacional da recepção; passa a distinguir o desfecho de silêncio
  dos demais estados de cadastro.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das reservas elegíveis que permanecem em silêncio até o primeiro
  prazo, o hóspede recebe exatamente um lembrete com a declaração de opcionalidade e de
  preenchimento na recepção.
- **SC-002**: Em 100% das reservas que já receberam o lembrete, uma nova verificação não
  gera segunda mensagem de lembrete (0 reenvios extras).
- **SC-003**: Em 100% das reservas que permanecem em silêncio até a janela de corte (ou com
  data de entrada já vencida), a recepção vê na fila do dia a indicação de que chegarão sem
  cadastro prévio, sem consultar outro sistema.
- **SC-004**: Em 100% das respostas do hóspede ocorridas antes do primeiro prazo, 0
  lembretes são enviados para aquela reserva.
- **SC-005**: Em 100% das respostas ocorridas após o lembrete e antes da janela de corte, 0
  reservas são marcadas como chegará sem cadastro prévio.
- **SC-006**: 100% das reservas marcadas como chegará sem cadastro prévio permanecem em
  estado que admite confirmação de chegada; 0 são canceladas ou encerradas só por causa do
  silêncio.
- **SC-007**: Alterar o intervalo ou a janela de corte da propriedade muda o momento do
  lembrete e da marcação na verificação seguinte, sem alteração de regra; duas propriedades
  com prazos diferentes não compartilham o ritmo.
- **SC-008**: Em 100% dos processamentos (lembrete enviado, falha de envio, marcação ou
  cancelamento por resposta), logs operacionais não contêm conteúdo de mensagem nem demais
  dados pessoais.
- **SC-009**: O caminho silêncio → no máximo um lembrete → marcação visível na fila (ou
  cancelamento por resposta) é verificável de ponta a ponta sem depender do canal real de
  mensagens.

## Assumptions

- A fatia F1.3 (receber e interpretar a ficha) está concluída; esta fatia começa no silêncio
  após a coleta já disparada.
- Os dois prazos já estão previstos na configuração da propriedade; o bootstrap desta fatia
  passa a semeá-los. Valores padrão adotados na instalação inicial: 24 horas até o lembrete
  e 12 horas de corte antes da data prevista de entrada. O hotel altera por configuração da
  propriedade (sem tela nova no MVP), não por mudança de código.
- A data prevista de entrada é uma data civil, sem hora. A janela de corte conta horas para
  trás a partir do início do dia previsto de entrada (00:00 dessa data). Exemplo: entrada em
  16/08 e corte de 12 horas → a marcação torna-se devida a partir de 15/08 12:00.
- Vocabulário da jornada (“chegará sem cadastro” / `chegara_sem_cadastro` no fluxo de
  dados) mapeia para o status já modelado `sem_cadastro_previo`. O painel mostra o
  significado operacional.
- “Resposta” é qualquer mensagem recebida do hóspede naquela reserva — inclusive as que a
  F1.3 classifica como parciais, irreconhecíveis ou com falha de interpretação.
- O indicador `reenvio_realizado` já existe na reserva e permanece a garantia de lembrete
  único; esta fatia é a primeira a gravá-lo como verdadeiro.
- A transição `aguardando_cadastro` → `sem_cadastro_previo` e a transição posterior para
  `hospedado` já são válidas na máquina de estados; esta fatia dispara a primeira, não
  implementa o clique de check-in (F2.2).
- Verificação periódica das pendências: a cadência operacional já decidida na arquitetura é
  na ordem de uma vez por hora. Atraso de até um ciclo não justifica segundo lembrete.
- Envio do lembrete segue o padrão já adotado: gravar a intenção de forma durável, enviar
  depois pela porta de mensageria, implementação falsa nos testes automatizados.
- Superfície de uso: comportamento observável pela fila do dia, histórico da conversa e
  status da reserva. Ligar o protótipo React continua fora do critério de pronto.
- Tela para editar `parametro_hotel` no painel permanece fora (lacuna já registrada: no MVP
  o valor é semeado e alterado por configuração, não por formulário).
- Check-in, boas-vindas, catálogo e atendimento conversacional ficam fora.
