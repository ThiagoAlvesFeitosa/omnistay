# Feature Specification: Receber e Interpretar a Ficha

**Feature Branch**: `006-receber-ficha`

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "O hóspede responde em texto livre, em uma única mensagem,
seguindo a lista numerada. O sistema extrai os campos, monta a ficha e a disponibiliza para
a recepção. Quando apenas parte dos campos é reconhecida, a ficha é consolidada com o que
veio e sinalizada como incompleta, sem que o sistema peça o restante por mensagem — o que
falta é completado no balcão. Quando nada é reconhecido, o texto original é preservado e
sinalizado para leitura humana."
(backlog F1.3)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Resposta completa vira ficha pronta (Priority: P1)

Como hóspede que respondeu à coleta com todos os campos da lista numerada em uma única
mensagem, quero que minha ficha seja montada e fique disponível para a recepção, para que
eu não precise preencher tudo de novo no balcão.

**Why this priority**: É o caminho feliz da pré-chegada e o valor principal desta fatia —
transformar texto livre em ficha utilizável no painel.

**Independent Test**: Pode ser testado enviando uma resposta que cobre todos os campos
pedidos na coleta e verificando que a ficha do titular fica completa, que o status da
reserva muda para o estado de ficha recebida, e que a fila do dia exibe essa indicação —
sem nenhuma mensagem adicional ao hóspede pedindo correção.

**Acceptance Scenarios**:

1. **Given** uma reserva em aguardo de cadastro com coleta já disparada, **When** o hóspede
   envia uma única mensagem de texto livre da qual o sistema reconhece todos os campos da
   ficha do titular, **Then** a ficha é consolidada como completa e a reserva passa ao
   status de ficha recebida.
2. **Given** uma ficha consolidada como completa, **When** a recepção consulta a fila do
   dia, **Then** aquela reserva aparece com indicação clara de que a ficha está pronta
   (estado de cadastro visível).
3. **Given** uma resposta completa processada com sucesso, **When** o fluxo termina,
   **Then** o sistema não envia ao hóspede nenhuma mensagem pedindo campos faltantes ou
   confirmação de preenchimento.

---

### User Story 2 - Resposta parcial sem nova cobrança no WhatsApp (Priority: P1)

Como hóspede que respondeu só parte dos itens da lista, quero que o que eu mandei seja
aproveitado e que o sistema não me cobrado de novo pelo WhatsApp, para que o restante seja
completado no balcão sem sensação de burocracia.

**Why this priority**: Decisão de escopo explícita da jornada: resposta parcial não dispara
nova rodada de mensagens. Sem isso, o produto vira formulário insistente e gasta mensagem.

**Independent Test**: Pode ser testado enviando uma mensagem da qual só parte dos campos é
reconhecida e verificando consolidação incompleta, status parcial, ausência de nova
mensagem ao hóspede e visibilidade na fila do dia.

**Acceptance Scenarios**:

1. **Given** uma reserva em aguardo de cadastro, **When** o hóspede envia uma mensagem da
   qual o sistema reconhece apenas parte dos campos da ficha, **Then** a ficha é
   consolidada com os campos reconhecidos, marcada como incompleta, e a reserva passa ao
   status de ficha parcial.
2. **Given** uma resposta parcial processada, **When** o fluxo de interpretação termina,
   **Then** o sistema não envia nenhuma mensagem pedindo os campos que faltaram.
3. **Given** uma ficha parcial consolidada, **When** a recepção consulta a fila do dia,
   **Then** a reserva aparece com indicação de cadastro incompleto, distinguível de ficha
   completa e de ainda aguardando resposta.

---

### User Story 3 - Texto irreconhecível preservado para humano (Priority: P1)

Como recepcionista, quero que uma resposta do hóspede que o sistema não consiga interpretar
continue disponível com o texto original e sinalizada para leitura humana, para que eu não
perca o que a pessoa mandou e possa completar a ficha no balcão.

**Why this priority**: “Na dúvida, um humano vê” e “a ficha nunca é descartada por falha de
interpretação” são regras do produto. Descarte silencioso destrói confiança.

**Independent Test**: Pode ser testado enviando texto do qual nenhum campo é reconhecido e
verificando preservação do texto original, sinalização para leitura humana e ausência de
nova cobrança automática ao hóspede.

**Acceptance Scenarios**:

1. **Given** uma reserva em aguardo de cadastro, **When** o hóspede envia uma mensagem da
   qual o sistema não reconhece nenhum campo da ficha, **Then** o texto original é
   preservado no histórico da conversa e a reserva/ficha fica sinalizada para leitura
   humana na fila do dia.
2. **Given** uma resposta irreconhecível processada, **When** o fluxo termina, **Then**
   nenhum campo inventado é gravado na ficha e nenhuma mensagem automática pede
   reenvio ou reformatação ao hóspede.
3. **Given** falha ou baixa confiança na interpretação, **When** o sistema decide o
   desfecho, **Then** a resposta do hóspede nunca é apagada nem descartada — permanece
   recuperável pela recepção.

---

### User Story 4 - Privacidade: idade não gravada e texto fora de log (Priority: P2)

Como titular dos dados e responsável pelo hotel, quero que a idade nunca seja armazenada
(apenas a data de nascimento, quando reconhecida) e que o conteúdo das mensagens não
apareça em log operacional, para cumprir minimização e evitar vazamento em trilhas técnicas.

**Why this priority**: Minimização de dados pessoais é princípio constitucional; idade
materializada é inconsistência no dia seguinte ao aniversário.

**Independent Test**: Pode ser testado com resposta que inclui data de nascimento e
inspecionando a ficha gravada (há data, não há idade) e os logs do processamento (sem
conteúdo de mensagem nem demais dados pessoais).

**Acceptance Scenarios**:

1. **Given** uma resposta da qual a data de nascimento é reconhecida, **When** a ficha é
   consolidada, **Then** a data de nascimento pode constar na ficha e a idade não é
   gravada em nenhum campo persistido.
2. **Given** qualquer processamento de recebimento ou interpretação, **When** o sistema
   registra log operacional, **Then** o conteúdo da mensagem e demais dados pessoais não
   aparecem no log — só identificadores, classificações e códigos de resultado.

---

### Edge Cases

- Mesma notificação de mensagem recebida entregue mais de uma vez (reenvio do canal): o
  sistema não consolida a ficha duas vezes nem altera o status duas vezes — o efeito
  observável permanece o de um único processamento.
- Mensagem recebida de telefone sem reserva em aguardo de cadastro no hotel correspondente:
  não consolida ficha de outra reserva; o tratamento fica limitado ao registro seguro do
  evento, sem inventar vínculo.
- Mensagem recebida após a reserva já ter ficha completa ou parcial: não sobrescreve a
  ficha consolidada nesta fatia (nova interpretação de mensagem posterior fica fora ou é
  tratada como não reabrindo o ciclo de coleta).
- Campos reconhecidos com formato inválido (documento ilegível, data impossível): o campo
  inválido não é gravado como fato; o restante reconhecido segue; a ficha reflete
  incompletude quando couber.
- Resposta que mistura itens fora de ordem ou com rótulos em vez de números: o sistema
  ainda tenta extrair; sucesso parcial ou total segue as mesmas regras de consolidação.
- Conteúdo que parece foto ou mídia sem texto utilizável: tratado como irreconhecível para
  fins de ficha (texto utilizável ausente); foto de documento nunca é aceita como fonte de
  cadastro.
- Interpretação indisponível ou falha técnica após a mensagem já ter sido gravada: a
  mensagem permanece; a reserva fica sinalizada para leitura humana; nada é descartado.
- Controle de silêncio / lembrete único (F1.4), check-in, transcrição para o PMS e respostas
  automáticas de atendimento **não** fazem parte desta fatia.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST receber a resposta do hóspede à coleta como texto livre em
  mensagem única vinculada à reserva correspondente (resolvida pelo telefone de contato /
  contexto da conversa da reserva em aguardo de cadastro).
- **FR-002**: Ao receber a mensagem, o sistema MUST gravar o evento e o conteúdo no
  histórico da conversa antes de qualquer interpretação ou consolidação de ficha.
- **FR-003**: O sistema MUST extrair da mensagem os campos da ficha do titular previstos na
  coleta: nome completo, profissão, data de nascimento, tipo e número de documento,
  endereço, CEP, cidade e telefone.
- **FR-004**: Quando todos os campos forem reconhecidos de forma utilizável, o sistema MUST
  consolidar a ficha como completa, marcar o vínculo do titular como ficha completa e
  transicionar a reserva de `aguardando_cadastro` para `ficha_recebida`.
- **FR-005**: Quando apenas parte dos campos for reconhecida de forma utilizável, o sistema
  MUST consolidar a ficha com os campos reconhecidos, mantê-la sinalizada como incompleta
  (`ficha_completa` falso) e transicionar a reserva para `ficha_parcial`.
- **FR-006**: Após resposta parcial, o sistema MUST NOT enviar ao hóspede nova mensagem
  pedindo os campos faltantes.
- **FR-007**: Quando nenhum campo for reconhecido de forma utilizável, o sistema MUST
  preservar o texto original no histórico, MUST NOT inventar valores de ficha e MUST
  sinalizar a reserva para leitura humana na fila do dia.
- **FR-008**: Em nenhuma hipótese de falha de interpretação ou de indisponibilidade do
  extrator a resposta do hóspede MUST ser descartada ou apagada após ter sido gravada.
- **FR-009**: A idade MUST NOT ser persistida em nenhum momento; somente a data de
  nascimento, quando reconhecida, pode constar na ficha.
- **FR-010**: Foto de documento ou mídia equivalente MUST NOT ser aceita como fonte de
  preenchimento da ficha.
- **FR-011**: A fila do dia da recepção MUST exibir, para cada reserva afetada, indicação
  do estado de cadastro distinguindo pelo menos: aguardando resposta, ficha completa,
  ficha parcial e sinalização para leitura humana quando a resposta for irreconhecível.
- **FR-012**: Reprocessamento do mesmo evento de mensagem recebida MUST NOT gerar segunda
  consolidação nem segunda transição de status observável.
- **FR-013**: Conteúdo de mensagem e demais dados pessoais NUNCA MUST aparecer em log de
  aplicação; logs registram apenas identificadores, classificações e códigos de resultado.
- **FR-014**: Esta fatia MUST NOT enviar lembrete por silêncio, confirmar check-in, abrir
  atendimento conversacional nem transcrever dados para o PMS — esses comportamentos
  pertencem a fatias seguintes ou à operação humana.
- **FR-015**: Consolidação e sinalização MUST ser visíveis ao perfil de recepção do hotel
  da reserva; dados cadastrais da ficha MUST NOT ser expostos a perfis que a política de
  acesso já impede de ler cadastro de hóspede.

### Key Entities

- **Mensagem recebida de coleta**: mensagem de entrada no histórico da conversa da reserva,
  com o texto livre enviado pelo hóspede após o pedido de cadastro.
- **Ficha do titular**: conjunto dos campos cadastrais do hóspede titular da reserva,
  consolidado a partir da mensagem; pode estar completa ou incompleta.
- **Estado de cadastro na fila**: indicação operacional vista pela recepção — aguardando
  resposta, ficha completa (`ficha_recebida`), ficha parcial (`ficha_parcial`) ou
  sinalização para leitura humana (texto preservado sem campos utilizáveis).
- **Evento de mensagem recebida**: notificação do canal de que o hóspede enviou texto;
  precisa ser tratada de forma idempotente quando reenviada.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das respostas das quais todos os campos são reconhecidos, a ficha do
  titular fica completa e a reserva aparece na fila do dia como ficha recebida.
- **SC-002**: Em 100% das respostas parciais processadas, a ficha fica incompleta com os
  campos reconhecidos, a reserva aparece como parcial na fila do dia, e 0 mensagens
  pedindo campos faltantes são enviadas ao hóspede.
- **SC-003**: Em 100% das respostas irreconhecíveis, o texto original permanece recuperável
  pela recepção e a reserva fica sinalizada para leitura humana; 0 fichas são descartadas.
- **SC-004**: Em 100% das fichas consolidadas a partir de data de nascimento, a idade não
  aparece como dado persistido.
- **SC-005**: Em reenvio do mesmo evento de mensagem recebida, 100% dos casos resultam em
  no máximo um efeito de consolidação/transição observável (sem duplicar status nem ficha).
- **SC-006**: Em 100% dos processamentos (sucesso, parcial, irreconhecível ou falha do
  extrator), logs operacionais não contêm o conteúdo da mensagem nem demais dados pessoais.
- **SC-007**: A recepção consegue distinguir, na fila do dia, os quatro desfechos de
  cadastro relevantes desta fatia (aguardando, completa, parcial, leitura humana) sem
  consultar outro sistema.
- **SC-008**: O caminho mensagem recebida → gravação → interpretação → consolidação /
  sinalização é verificável de ponta a ponta sem depender do canal real de mensagens nem de
  provedor externo obrigatório nos testes automatizados.

## Assumptions

- A fatia F1.2 (disparo da coleta, histórico de mensagem de saída, porta de mensageria,
  fila de trabalho) está concluída; esta fatia começa no recebimento da resposta do
  hóspede.
- Os campos da ficha são exatamente os pedidos na lista numerada da coleta (titular): nome
  completo, profissão, data de nascimento, tipo e número de documento, endereço, CEP,
  cidade e telefone.
- Os status de reserva usados são os da máquina de estados já modelada:
  `aguardando_cadastro` → `ficha_recebida` (completo) ou `ficha_parcial` (parcial). A
  sinalização “leitura humana” para texto irreconhecível é indicação operacional na fila /
  conversa; não cria um quinto status de ciclo de vida nesta fatia.
- Vocabulário legado da jornada (`aguardando_transcricao` / `parcial`) mapeia para
  `ficha_recebida` / `ficha_parcial` do modelo de dados — o painel mostra o significado
  operacional, não nomes internos.
- Extração a partir de texto livre pode usar classificação/interpretação assistida; nos
  testes automatizados o comportamento é determinístico via implementação falsa da porta
  de IA (sem chamada a provedor real).
- Recebimento chega por webhook do canal; a API grava e responde rápido; interpretação que
  dependa de trabalho demorado pode seguir o padrão “gravar antes, processar depois”
  já adotado no projeto — o planejamento detalha o mecanismo sem mudar os desfechos
  observáveis desta spec.
- Idempotência do evento de webhook reutiliza a garantia já prevista de unicidade do
  identificador externo do evento.
- Atualização da ficha do titular provisório criado na F1.1 (mesmo `hospede` / vínculo
  titular), não criação de um segundo titular.
- F1.4 (lembrete único e “chegará sem cadastro”), check-in, boas-vindas e atendimento
  conversacional ficam fora.
- Superfície de uso: comportamento observável pela API/painel já usados (fila do dia,
  histórico). Ligar o protótipo React continua fora do critério de pronto desta fatia.
- Mensagem posterior do hóspede após ficha já consolidada não reabre automaticamente o
  ciclo de coleta nesta fatia; se o canal entregar texto nesse estado, o mínimo é não
  corromper a ficha já consolidada.
