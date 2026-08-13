# Feature Specification: Disparar Coleta de Dados

**Feature Branch**: `005-disparar-coleta`

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "Ao registrar a reserva, o sistema envia ao hóspede uma mensagem
única solicitando os dados cadastrais em lista numerada, informando que o preenchimento
antecipado é opcional e serve para evitar espera na chegada. A mensagem declara a finalidade
da coleta e o contato do responsável pelos dados. O envio e a gravação da reserva são
independentes: falha no envio não pode desfazer a reserva."
(backlog F1.2)

Restrições de arquitetura já decididas no projeto (entrada do specify): o envio não acontece
na mesma requisição que grava a reserva — a reserva enfileira o envio de forma durável e um
processo separado consome a fila; todo envio passa por uma porta de mensageria com
implementação falsa nos testes automatizados; a mensagem é um template da categoria Utility
aprovado pelo provedor, e no MVP o número de envio é o de teste do provedor (limitado a
poucos destinatários).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Disparar a coleta ao cadastrar a reserva (Priority: P1)

Como hóspede que acabou de ter a reserva registrada, quero receber uma única mensagem pedindo
meus dados cadastrais em lista numerada, com a informação de que o preenchimento antecipado é
opcional e serve para evitar espera na chegada, para que eu possa completar a ficha antes de
chegar ao hotel — ou ignorar sem prejuízo.

**Why this priority**: Sem este disparo, a reserva cadastrada na F1.1 não inicia a jornada do
hóspede. É o primeiro contato do sistema com o titular dos dados e o gatilho de todo o
pré-check-in.

**Independent Test**: Pode ser testado cadastrando uma reserva válida e verificando que nasce
exatamente uma intenção de envio de coleta ligada a ela, que a mensagem entregue (via porta
falsa) contém a lista numerada, a opcionalidade e a finalidade, e que a reserva permanece
gravada independentemente do resultado do envio.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção que conclui o cadastro de uma reserva válida, **When** a
   reserva é gravada com sucesso, **Then** o sistema registra exatamente uma pendência de
   envio da mensagem de coleta para o telefone de contato daquela reserva.
2. **Given** uma pendência de coleta pronta para envio, **When** o processo de envio a
   processa com sucesso, **Then** o hóspede recebe uma mensagem com a lista numerada dos
   campos cadastrais do titular, a declaração de que o preenchimento antecipado é opcional e
   serve para evitar espera na chegada, a finalidade da coleta e o contato do responsável
   pelos dados.
3. **Given** uma reserva já registrada com disparo de coleta concluído, **When** ninguém
   altera aquela reserva, **Then** o sistema não dispara uma segunda mensagem de coleta para
   a mesma reserva.

---

### User Story 2 - Reserva sobrevive a falha de envio (Priority: P1)

Como recepcionista, quero que a reserva continue existindo e apareça na fila do dia mesmo
quando a mensagem de coleta falhar ao sair, e que o sistema marque aquela reserva para nova
tentativa, para que um problema de rede ou de mensageria nunca apague o trabalho que eu já
fiz no painel.

**Why this priority**: A independência entre gravação e envio é premissa constitucional
("gravar antes de enviar"). Se falha de envio desfizer a reserva, o hotel perde confiança no
produto no primeiro uso.

**Independent Test**: Pode ser testado forçando falha na porta de mensageria após o cadastro e
verificando que a reserva permanece, que o status de envio fica visível como falha ou
pendente de nova tentativa, e que uma nova execução do consumidor tenta de novo.

**Acceptance Scenarios**:

1. **Given** uma reserva acabada de cadastrar, **When** a tentativa de envio da coleta falha,
   **Then** a reserva permanece gravada no estado em que nasceu e continua na fila do dia.
2. **Given** um envio de coleta que falhou, **When** a recepção consulta a fila do dia,
   **Then** o estado de entrega da mensagem de coleta daquela reserva está visível (pendente,
   enviada, entregue ou falha).
3. **Given** um envio marcado para nova tentativa, **When** o processo de envio roda de novo e
   a mensageria responde com sucesso, **Then** o estado de entrega passa a refletir o envio
   bem-sucedido e continua existindo exatamente uma mensagem de coleta no histórico daquela
   reserva (sem duplicar o pedido ao hóspede por causa do retry).

---

### User Story 3 - Histórico e privacidade da primeira mensagem (Priority: P1)

Como responsável pelos dados do hotel e pela privacidade do hóspede, quero que toda mensagem
de coleta enviada fique registrada no histórico da conversa da reserva, e que o texto da
primeira mensagem não revele dado pessoal além do primeiro nome, para que um telefone
digitado errado não exponha a ficha de um hóspede a um terceiro.

**Why this priority**: O telefone errado é o ponto frágil nº 1 da jornada. Minimização na
primeira mensagem e trilha auditável do envio são exigências de transparência e de operação.

**Independent Test**: Pode ser testado inspecionando o histórico da conversa após um envio
bem-sucedido (via porta falsa) e verificando o conteúdo permitido e a presença do registro.

**Acceptance Scenarios**:

1. **Given** um envio de coleta bem-sucedido, **When** se consulta o histórico de mensagens
   da reserva, **Then** a mensagem enviada aparece como mensagem de saída com estado de
   entrega atualizado.
2. **Given** o texto da mensagem de coleta, **When** ele é montado para envio, **Then** o
   único dado pessoal do hóspede presente no corpo é o primeiro nome; telefone, documento,
   endereço e demais campos da ficha não aparecem.
3. **Given** qualquer processamento de envio (sucesso ou falha), **When** o sistema registra
   log operacional, **Then** o conteúdo da mensagem e demais dados pessoais não aparecem no
   log — só identificadores e códigos de resultado.

---

### User Story 4 - Transparência LGPD no primeiro contato (Priority: P2)

Como titular dos dados, quero que a primeira mensagem declare em linguagem clara a finalidade
da coleta e como falar com o responsável pelos dados do hotel, para saber por que meus dados
estão sendo pedidos e a quem recorrer.

**Why this priority**: É o aviso de privacidade do primeiro contato exigido pela jornada
(transparência). Sem isso, a coleta antecipada fica juridicamente incompleta mesmo que
funcione tecnicamente.

**Independent Test**: Pode ser testado lendo o conteúdo da mensagem gerada e verificando as
duas declarações obrigatórias.

**Acceptance Scenarios**:

1. **Given** a mensagem de coleta montada para uma reserva, **When** o texto é inspecionado,
   **Then** há uma declaração explícita da finalidade da coleta (cadastro antecipado para a
   hospedagem / evitar espera na chegada).
2. **Given** a mensagem de coleta montada para uma reserva de um hotel, **When** o texto é
   inspecionado, **Then** há um canal de contato do responsável pelos dados daquela
   propriedade (configurado para o hotel, não genérico do produto).

---

### Edge Cases

- Cadastro de reserva recusado (telefone inválido, datas inconsistentes, perfil sem
  permissão): nenhuma pendência de envio é criada.
- Duas reservas distintas com o mesmo telefone: cada uma dispara a própria coleta; não há
  fusão de envios.
- Falha transitória de mensageria seguida de sucesso no retry: o hóspede recebe uma única
  mensagem de coleta; o histórico não acumula pedidos duplicados ao titular.
- Após esgotar as tentativas configuradas de reenvio técnico: o estado permanece como falha
  visível na fila do dia; a reserva não é apagada nem cancelada.
- Processo de envio interrompido no meio: a pendência permanece recuperável; na retomada não
  se cria um segundo pedido de coleta para a mesma reserva.
- Hóspede com nome de um único prenome: a mensagem usa esse prenome; não inventa sobrenome.
- Interpretação da resposta do hóspede, consolidação da ficha, lembrete por silêncio e
  recebimento de webhook **não** fazem parte desta fatia (F1.3 / F1.4).
- Número de envio do MVP limitado ao ambiente de teste do provedor (poucos destinatários): a
  funcionalidade precisa funcionar com a porta falsa nos testes; a ligação ao ambiente de
  teste real do provedor é restrição de implantação, não critério para inventar outro canal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Ao gravar com sucesso uma reserva pelo fluxo da recepção, o sistema MUST
  registrar exatamente uma pendência de envio da mensagem de coleta de dados para o telefone
  de contato daquela reserva.
- **FR-002**: O envio da mensagem de coleta MUST NOT ocorrer na mesma operação síncrona que
  confirma a gravação da reserva ao usuário. A gravação MUST concluir com a reserva
  persistida e a intenção de envio duravelmente registrada; a entrega ao hóspede acontece em
  processamento posterior.
- **FR-003**: Falha no envio da coleta MUST NOT desfazer, cancelar nem alterar o estado de
  ciclo de vida da reserva já gravada.
- **FR-004**: Quando o envio falhar, o sistema MUST marcar a mensagem/pendência para nova
  tentativa e MUST expor o estado de entrega na fila do dia da recepção.
- **FR-005**: O retry técnico de um envio falho MUST NOT resultar em uma segunda mensagem de
  coleta distinta pedindo de novo os dados ao mesmo hóspede para a mesma reserva — no máximo
  uma coleta lógica por reserva neste fluxo.
- **FR-006**: Toda mensagem de coleta efetivamente enviada (ou tentada com registro) MUST
  aparecer no histórico de conversa da reserva como mensagem de saída, com estado de entrega
  (`pendente`, `enviada`, `entregue` ou `falha`).
- **FR-007**: A mensagem de coleta MUST solicitar os dados cadastrais do titular em lista
  numerada correspondente aos campos da ficha previstos para o cadastro antecipado (nome
  completo, profissão, data de nascimento, tipo e número de documento, endereço, CEP, cidade
  e telefone).
- **FR-008**: A mensagem MUST informar que o preenchimento antecipado é opcional e que serve
  para evitar espera na chegada; sem o preenchimento, o cadastro será feito na recepção.
- **FR-009**: A mensagem MUST declarar a finalidade da coleta e o canal de contato do
  responsável pelos dados da propriedade.
- **FR-010**: O corpo da mensagem de coleta MUST NOT conter dado pessoal do hóspede além do
  primeiro nome.
- **FR-011**: Conteúdo de mensagem e demais dados pessoais NUNCA MUST aparecer em log de
  aplicação; logs registram apenas identificadores, estados e códigos de erro.
- **FR-012**: O estado de entrega da mensagem de coleta MUST ser visível na fila do dia para
  o perfil de recepção do hotel da reserva.
- **FR-013**: Todo envio ao hóspede MUST passar por uma porta de mensageria substituível,
  de modo que o comportamento de sucesso e de falha possa ser exercitado sem depender da
  rede do provedor real.
- **FR-014**: A mensagem de coleta MUST ser do tipo operacional de utilidade (categoria
  Utility do canal), aprovada pelo provedor — nunca uma mensagem promocional/marketing.
- **FR-015**: Esta fatia MUST NOT interpretar a resposta do hóspede, consolidar ficha,
  alterar o status da reserva para além do que já nasceu na F1.1, nem enviar lembrete por
  silêncio — esses comportamentos pertencem às fatias seguintes.
- **FR-016**: Tentativa de cadastro de reserva que falha na validação MUST NOT criar
  pendência de envio nem registro de mensagem de coleta.

### Key Entities

- **Pendência de envio de coleta**: intenção durável, ligada a uma reserva, de entregar a
  mensagem de coleta ao telefone de contato. Nasce com a reserva e sobrevive a falhas de
  rede até ser concluída ou marcada como falha definitiva após tentativas.
- **Mensagem de coleta**: mensagem de saída no histórico da conversa da reserva, com texto
  (ou referência de template) da solicitação numerada, finalidade, opcionalidade e contato
  do responsável, e com estado de entrega observável.
- **Estado de entrega**: situação do envio vista pela recepção na fila do dia — pelo menos
  pendente, enviada, entregue e falha.
- **Porta de mensageria**: fronteira pela qual qualquer envio ao hóspede acontece; permite
  troca de provedor e testes sem rede externa.
- **Contato do responsável pelos dados**: canal configurado por propriedade, embutido na
  mensagem de primeiro contato.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos cadastros de reserva bem-sucedidos, nasce exatamente uma pendência
  de coleta ligada àquela reserva.
- **SC-002**: Em 100% dos casos em que o envio falha, a reserva permanece gravada e
  consultável na fila do dia após a falha.
- **SC-003**: Em verificação com falha forçada de mensageria, 100% das falhas ficam visíveis
  para a recepção pelo estado de entrega na fila do dia, sem necessidade de consultar outro
  sistema.
- **SC-004**: Após retries de um envio que eventualmente sucede, o hóspede recebe no máximo
  uma mensagem de coleta por reserva (0% de pedidos duplicados ao titular por causa de
  reprocessamento técnico).
- **SC-005**: Em 100% das mensagens de coleta montadas, o único dado pessoal do hóspede no
  corpo é o primeiro nome.
- **SC-006**: Em 100% das mensagens de coleta montadas, constam finalidade da coleta,
  opcionalidade do preenchimento antecipado e contato do responsável pelos dados da
  propriedade.
- **SC-007**: Em 100% dos envios bem-sucedidos (via porta de teste), a mensagem aparece no
  histórico da conversa da reserva com direção de saída e estado de entrega atualizado.
- **SC-008**: O caminho cadastro → pendência → envio (sucesso e falha) é verificável de ponta
  a ponta sem nenhuma chamada à rede do provedor real de mensagens.
- **SC-009**: Cadastros de reserva recusados por validação geram 0 pendências de coleta.

## Assumptions

- A fatia F1.1 (cadastrar reserva, fila do dia, telefone canônico, titular provisório) está
  concluída e é o gatilho deste disparo: não há outro caminho de criação de reserva no MVP.
- Os campos da lista numerada são os da ficha de cadastro já decididos no mapa de processos
  (titular da reserva). A interpretação da resposta é F1.3; aqui só se pede e se registra o
  pedido.
- O contato do responsável pelos dados é configurável por propriedade (parâmetro ou dado do
  hotel). Se ainda não existir valor cadastrado no bootstrap, o planejamento define o valor
  padrão mínimo para o hotel inicial — sem inventar um canal genérico do produto OmniStay.
- **Independência estrutural (decisão de arquitetura):** o envio não roda dentro da
  requisição que grava a reserva. A reserva registra a intenção de envio de forma durável
  (fila no banco, conforme Artefato 5) e um worker consome essa fila. Tratamento de erro
  síncrono na mesma requisição **não** satisfaz este requisito.
- **Divergência a conciliar no planejamento:** o Artefato 5 descreve a fila de trabalho no
  PostgreSQL, mas o esquema de referência atual (`04-schema.sql`) ainda não declara a tabela
  de fila. Esta fatia precisa introduzir (ou confirmar) essa estrutura com migração e
  atualização do documento de esquema na mesma entrega.
- **Porta de mensageria (decisão de arquitetura):** todo envio passa pela interface
  `MensageriaGateway`; testes usam implementação falsa; nenhum teste chama a API da Meta.
- **Template Utility e ambiente de teste (decisão de arquitetura / MVP):** a mensagem é um
  template da categoria Utility aprovado pela Meta. No MVP o número de envio é o de teste da
  Meta, limitado a poucos destinatários. A demonstração e a suíte automatizada não dependem
  desse limite — a porta falsa cobre o comportamento observável.
- Status de entrega na fila do dia reutiliza o vocabulário já modelado para mensagem de saída
  (`pendente`, `enviada`, `entregue`, `falha`). Se a view da fila ainda não expõe esse campo,
  o planejamento inclui a exposição sem inventar um segundo conceito de status.
- Recebimento de resposta do hóspede, consolidação da ficha, mudança de status para
  `aguardando_transcricao` / ficha completa, e o lembrete único por silêncio ficam fora —
  F1.3 e F1.4.
- Confirmações de entrega/leitura vindas do provedor (webhooks de status) podem enriquecer
  `entregue` depois; o mínimo desta fatia é tornar visíveis pelo menos pendente, enviada e
  falha após a tentativa de envio. Se o webhook de status de entrega não couber no prazo da
  fatia, o planejamento declara o recorte e mantém `enviada`/`falha` observáveis.
- Superfície de uso: o comportamento precisa ser observável pela API/painel já usados na
  F1.1 (fila do dia). Ligar o protótipo React continua fora do critério de pronto desta
  fatia, como na anterior.
