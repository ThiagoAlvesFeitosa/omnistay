# Feature Specification: Cadastrar Reserva

**Feature Branch**: `004-cadastrar-reserva`

**Created**: 2026-08-12

**Status**: Draft

**Input**: User description: "A recepção registra uma nova reserva informando apenas nome,
telefone de contato e as datas previstas de entrada e saída. O telefone é validado no momento
da digitação, porque um dígito errado faz a comunicação inteira falhar ou chegar a um terceiro.
A reserva nasce aguardando o cadastro do hóspede e passa a constar na fila do dia da recepção."
(backlog F1.1)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registrar reserva com três campos (Priority: P1)

Como recepcionista, quero cadastrar uma reserva digitando apenas o nome de quem vem, o telefone
de contato e as datas previstas de entrada e saída, para que o OmniStay passe a acompanhar aquela
estadia sem eu repetir o cadastro completo que já faço no PMS.

**Why this priority**: É o ponto de entrada de todo o produto. Sem reserva cadastrada, não há
coleta de ficha, conversa, chamado nem indicador. O atrito aqui decide se o hotel usa o sistema
ou o abandona.

**Independent Test**: Pode ser testado autenticando como recepção, enviando os três campos
válidos e verificando que a reserva existe, nasce aguardando cadastro e aparece na fila do dia
do hotel da sessão.

**Acceptance Scenarios**:

1. **Given** uma sessão autenticada de perfil de recepção, **When** a pessoa informa nome,
   telefone válido e datas em que a saída é posterior à entrada, **Then** a reserva é gravada e
   nasce no estado de aguardando o cadastro do hóspede.
2. **Given** uma reserva acabada de registrar com check-in previsto para o dia corrente,
   **When** a recepção consulta a fila do dia do próprio hotel, **Then** aquela reserva aparece
   com o nome informado, o telefone de contato, as datas e o status de aguardando cadastro.
3. **Given** uma sessão de recepção, **When** a pessoa tenta gravar sem nome, sem telefone ou
   sem uma das datas, **Then** a reserva não é criada e a mensagem deixa claro o que falta.

---

### User Story 2 - Impedir telefone inválido e datas inconsistentes (Priority: P1)

Como responsável pela comunicação com o hóspede, quero que o sistema recuse telefone em formato
inválido e data de saída anterior ou igual à de entrada no momento em que a recepção digita,
para que o erro de origem não contamine o restante do processo.

**Why this priority**: Telefone errado é a falha de origem identificada na jornada — mensagem
que não chega ou que chega a um terceiro. Datas invertidas corrompem a fila do dia e qualquer
disparo temporal posterior.

**Independent Test**: Pode ser testado isoladamente tentando cadastrar com telefone inválido e
com datas inconsistentes, verificando recusa explícita e ausência de registro.

**Acceptance Scenarios**:

1. **Given** uma sessão de recepção, **When** o telefone informado não passa na validação de
   formato (incluindo DDD), **Then** a reserva não é criada e a mensagem de recusa é clara o
   bastante para a pessoa corrigir sem adivinhar a regra.
2. **Given** uma sessão de recepção, **When** a data de saída é anterior ou igual à data de
   entrada, **Then** a reserva não é criada e a inconsistência das datas é declarada.
3. **Given** um telefone inválido ou datas inconsistentes, **When** a tentativa é recusada,
   **Then** nenhum registro parcial de reserva fica persistido.

---

### User Story 3 - Isolar a fila por hotel e por perfil (Priority: P1)

Como responsável pelos dados do hotel, quero que a fila do dia mostre apenas reservas da
propriedade da sessão e que só a recepção possa cadastrar e ver nome e telefone, para que um
hotel nunca veja a agenda de outro e perfis sem autoridade operacional não alterem reserva nem
leiam quem chega.

**Why this priority**: Multi-tenant e autorização já existem desde a autenticação; esta fatia
é a primeira que grava dado de domínio e precisa herdar essas fronteiras, não reinventá-las.

**Independent Test**: Pode ser testado criando reservas em dois hotéis e tentando listar ou
cadastrar com cada perfil, verificando isolamento e recusas.

**Acceptance Scenarios**:

1. **Given** reservas cadastradas em dois hotéis distintos, **When** a recepção de um hotel
   consulta a fila do dia, **Then** só aparecem as reservas daquele hotel.
2. **Given** uma sessão de perfil operacional (`staff`), **When** ela tenta cadastrar uma
   reserva ou ler a fila, **Then** a operação é recusada e nada é gravado nem devolvido.
3. **Given** uma sessão de perfil de gestão, **When** ela tenta cadastrar uma reserva ou ler a
   fila nominada, **Then** a operação é recusada — gestão não altera dado de domínio e não recebe
   nome nem telefone.
4. **Given** uma requisição sem sessão válida, **When** ela tenta cadastrar, listar a fila ou
   ler a contagem, **Then** é recusada sem devolver dado de reserva.

---

### User Story 4 - Contagem de chegadas sem dado de hóspede (Priority: P2)

Como gestão, quero ver quantas chegadas estão previstas para hoje, sem ver quem são, para
dimensionar a equipe do turno sem acessar dado cadastral.

**Why this priority**: Fecha o buraco deixado ao negar a fila à gestão — o número importa; a
identidade não. Sem esta história, a gestão ficaria cega ou alguém “resolveria” no frontend
vazando a lista.

**Independent Test**: Pode ser testado criando reservas com check-in hoje e consultando a
contagem como gestão, verificando que a resposta traz só o número e que a fila nominada continua
recusada.

**Acceptance Scenarios**:

1. **Given** N reservas ativas do hotel com check-in previsto para a data corrente, **When** a
   gestão consulta a contagem de chegadas do dia, **Then** recebe exatamente N e nenhum outro
   campo além da quantidade.
2. **Given** uma sessão de gestão, **When** ela consulta a contagem, **Then** a resposta não
   contém nome, telefone, identificador de reserva nem lista de itens.
3. **Given** uma sessão de `staff`, **When** ela consulta a contagem, **Then** é recusada.

---

### Edge Cases

- Telefone com espaços, parênteses ou hífens digitados pela recepção: a validação considera o
  número útil (dígitos), não a máscara visual, e a forma canônica gravada é única para o mesmo
  número.
- Telefone com código do país (`+55`) e telefone só com DDD nacional são aceitos quando
  representam o mesmo formato válido brasileiro; números estrangeiros ficam fora do MVP.
- Check-in previsto no passado: a reserva ainda pode ser cadastrada (hóspede que chega sem ter
  sido lançado a tempo), e a fila a destaca como chegada ainda não confirmada quando a data já
  passou e o status ainda não é hospedado nem cancelado.
- Check-out no dia seguinte ao check-in (uma diária) é válido; saída no mesmo dia não é.
- Nome com um único prenome é aceito — a ficha completa virá depois; nesta fatia o nome só
  identifica a reserva na fila.
- Duas reservas com o mesmo telefone: **sempre** criam hóspede novo cada uma (casal, telefone de
  empresa). Não há reaproveitamento de cadastro pelo número. O mesmo indivíduo físico pode ficar
  duplicado; consolidação por pessoa, se existir um dia, será passo explícito.
- Cancelamento de reserva, edição após o cadastro e disparo de mensagem ao hóspede **não**
  fazem parte desta fatia.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST permitir que um usuário autenticado com perfil de recepção
  registre uma reserva informando exclusivamente nome, telefone de contato e datas previstas de
  entrada e saída.
- **FR-002**: O sistema MUST recusar o registro quando qualquer um dos três campos estiver
  ausente ou em branco, com mensagem que indique o campo faltante.
- **FR-003**: O sistema MUST validar o telefone de contato no momento do registro, exigindo
  formato brasileiro utilizável em mensageria (DDD + número), e MUST recusar formato inválido
  com mensagem clara.
- **FR-004**: O sistema MUST recusar o registro quando a data de saída for anterior ou igual à
  data de entrada.
- **FR-005**: Toda reserva criada por este fluxo MUST nascer no estado de aguardando o cadastro
  do hóspede — nenhum outro estado inicial é permitido neste caminho.
- **FR-006**: Após o registro, a reserva MUST aparecer na fila do dia da recepção do hotel da
  sessão, com nome, telefone de contato, datas previstas e status visíveis.
- **FR-007**: A fila do dia MUST listar apenas reservas do hotel vinculado à sessão
  autenticada; reserva de outro hotel NUNCA aparece.
- **FR-008**: A fila do dia MUST excluir reservas já encerradas ou canceladas, e MUST sinalizar
  quando a data de check-in prevista já passou sem confirmação de chegada.
- **FR-009**: A fila do dia MUST ordenar as reservas pela data prevista de entrada (mais próxima
  primeiro), para espelhar a urgência do turno.
- **FR-010**: O sistema MUST recusar cadastro de reserva e leitura da fila nominada a perfis
  que não sejam recepção (`staff` e `gestor`), sem gravar nem devolver dado de hóspede.
- **FR-011**: O sistema MUST recusar cadastro, consulta da fila e consulta da contagem a
  requisições sem sessão válida.
- **FR-012**: O nome informado no cadastro MUST identificar a reserva na fila do dia mesmo
  antes de existir ficha cadastral completa do hóspede.
- **FR-013**: Conteúdo de telefone e nome NUNCA MUST aparecer em log de aplicação; logs, se
  houver, registram apenas identificadores e códigos de erro.
- **FR-014**: Esta fatia MUST NOT enviar mensagem ao hóspede nem alterar o estado da reserva
  para além do nascimento em aguardando cadastro — coleta por WhatsApp é fatia seguinte.
- **FR-015**: O sistema MUST oferecer contagem de chegadas do dia (reservas ativas com check-in
  previsto para a data corrente) aos perfis que já podem ler indicadores (recepção e gestão),
  devolvendo somente a quantidade — sem nome, telefone, identificador de reserva ou lista.
- **FR-016**: A contagem de chegadas MUST ser endpoint distinto da fila nominada; MUST NOT
  depender de o cliente receber a lista e filtrar no frontend.
- **FR-017**: Cada cadastro de reserva MUST criar um registro de hóspede novo, mesmo quando já
  existir hóspede com o mesmo telefone canônico. Reaproveitamento automático pelo número é
  proibido.

### Key Entities

- **Reserva**: registro mínimo da estadia prevista — telefone de contato, datas de entrada e
  saída previstas, status do ciclo de vida. Nasce antes de existir ficha completa de hóspede.
  Pertence a exatamente um hotel.
- **Nome de contato da reserva**: o nome digitado pela recepção na criação; identifica a
  pessoa na fila do dia até a ficha consolidada existir. Não é a ficha cadastral completa.
- **Fila do dia**: visão operacional da recepção com as reservas ativas do hotel, ordenadas
  pela chegada prevista, com status de cadastro e alerta de chegada não confirmada.
- **Hotel da sessão**: propriedade à qual o usuário autenticado pertence; delimita criação e
  listagem.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma recepcionista autentica e conclui o cadastro de uma reserva válida (três
  campos) em menos de 1 minuto, do início do formulário até a reserva visível na fila.
- **SC-002**: Em 100% das tentativas com telefone em formato inválido, o sistema recusa e
  nenhuma reserva é criada.
- **SC-003**: Em 100% das tentativas com data de saída anterior ou igual à de entrada, o
  sistema recusa e nenhuma reserva é criada.
- **SC-004**: 100% das reservas criadas por este fluxo nascem no estado de aguardando cadastro
  e aparecem na fila do dia do hotel correto na consulta seguinte.
- **SC-005**: Em verificação com dois hotéis, 0% das reservas de um hotel aparecem na fila do
  outro.
- **SC-006**: Em verificação com sessão de `staff` e de `gestor`, 100% das tentativas de
  cadastro de reserva e de leitura da fila nominada são recusadas.
- **SC-007**: A recepção identifica na fila, sem consulta extra, se cada reserva ainda aguarda
  cadastro e se a chegada prevista já passou sem confirmação.
- **SC-008**: Em verificação com gestão autenticada, a contagem de chegadas do dia devolve só
  o número correto; 0% das respostas contém nome, telefone ou lista de reservas.
- **SC-009**: Duas reservas cadastradas com o mesmo telefone resultam em dois registros de
  hóspede distintos em 100% dos casos.

## Assumptions

- Autenticação, sessão em cookie e matriz de perfis da fatia F0.3 estão disponíveis; esta fatia
  apenas passa a exercitar a operação de alterar/consultar reserva para o perfil de recepção.
- O painel é a superfície de uso: a recepção cadastra e consulta a fila por interface do
  produto. O detalhe de ligar o protótipo React existente versus entregar primeiro o
  comportamento observável atrás do painel fica para o planejamento — o critério de aceite é o
  comportamento, não a tecnologia.
- Formato de telefone aceito no MVP: número brasileiro com DDD (celular 11 dígitos ou fixo 10
  dígitos, com ou sem prefixo `+55`). Número internacional fica fora de escopo.
- O nome digitado na criação é o que a fila exibe; a ficha cadastral completa (documento,
  endereço etc.) nasce nas fatias de coleta e interpretação (F1.2 / F1.3), não aqui.
- **Divergência a conciliar no planejamento:** o backlog e a jornada exigem nome + telefone +
  datas no cadastro, e a fila do dia precisa exibir um nome; o esquema de referência concentra
  `nome_completo` na ficha de hóspede e não tem campo de nome na tabela de reserva. O plano
  desta fatia deve resolver essa lacuna (sem inventar integração com PMS) e, se houver mudança
  de modelo, atualizar o esquema documentado na mesma entrega.
- Disparo da mensagem de coleta, status de entrega no WhatsApp, reenvio por silêncio e
  interpretação da ficha estão explicitamente fora — dependem desta fatia e são F1.2+.
- Não há cancelamento nem edição de reserva nesta fatia.
- Telefone repetido sempre cria hóspede novo (casal / telefone de empresa). Consolidação por
  pessoa, se um dia existir histórico individual, será passo explícito — não deduplicação
  silenciosa.
- A garantia de datas (saída depois da entrada) e o estado inicial de aguardando cadastro devem
  permanecer coerentes com as regras já descritas no modelo de dados; o planejamento confirma
  o que já está garantido no banco versus o que a aplicação ainda precisa impor na borda.
- A contagem de chegadas reutiliza a permissão `ler_indicadores` já definida na F0.3; não cria
  perfil novo nem concede à gestão acesso à fila nominada.
