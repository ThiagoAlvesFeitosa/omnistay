# Feature Specification: Cada hóspede pertence a um hotel

**Feature Branch**: `040-hospede-por-hotel`

**Created**: 2026-10-16

**Status**: Draft

**Input**: User description: "Cada hóspede passa a pertencer a um
hotel. O mesmo documento pode existir em hotéis diferentes sem
conflito, porque cada hotel é o controlador dos dados dos seus
hóspedes. Dentro de um mesmo hotel, o documento continua único.
Quando a recepção tenta gravar um documento que já pertence a outro
hóspede do mesmo hotel, o aviso diz qual é esse hóspede, para que
ela possa conferir."
(backlog F9.3)

Restrições já decididas no projeto (entrada do specify): o sistema
**não** se integra ao sistema de gestão do hotel (Artigo I); foto de
documento não é aceita e conteúdo de mensagem **nunca** vai para log
(Artigo VIII); `id_hotel` em tabela de domínio e em toda consulta é
obrigatório mesmo com uma propriedade só (Artigo XIV); consentimento
é por controlador — um hotel não lê nem apaga cadastro de outro;
unicidade de documento **dentro** do hotel permanece; o aviso de
documento repetido **só** nomeia hóspede do mesmo hotel. Reconhecer
quem volta pelo telefone (F9.4) e a pendência “é a mesma pessoa”
(F9.5) **não** entram aqui. Conferência de CPF (F9.2) já existe e
não muda.

## Clarifications

### Session 2026-10-16

- Q: Quando a recepção grava um documento que já é de outro hóspede desta casa, o aviso precisa só do nome, ou também de um caminho para abrir a ficha dessa pessoa? → A: O aviso traz o nome e um caminho para abrir a ficha já gravada desta casa, do mesmo jeito que a Fila do dia já abre ficha. Vale só para quem já pode ler ficha (recepção) e só dentro do mesmo hotel; sem mostrar o documento no aviso.
- Q: O teste que falha se um cadastro existir sem hotel vale só para o hóspede, ou também para mensagem, consentimento e o vínculo da reserva? → A: O teste olha a estrutura do cadastro, não os dados: toda tabela tem o identificador do hotel ou é filha, por vínculo obrigatório, de uma que tem (o filho segue o pai). O hóspede hoje reprova, porque só chega ao hotel pelo vínculo com a reserva, e passa depois desta fatia. Exceção só se nomeada no próprio teste, com o motivo. Assim pega tabela nova sem dono, sem pôr o hotel em tudo.
- Q: Se um hóspede antigo não tem nenhuma reserva, e portanto nenhum hotel, o que a migração faz, já que todo hóspede passa a precisar de um hotel? → A: Se existe um único hotel, esse hóspede fica dele. Se existem dois ou mais, a migração registra os identificadores (nunca o documento) e não inventa dono.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - O mesmo documento em dois hotéis não se atropela (Priority: P1)

Como operação de duas casas distintas, quero que cada hóspede
pertença ao hotel que é o controlador daqueles dados. O mesmo
documento em hotéis diferentes **não** é conflito: cada casa tem o
próprio cadastro. Só dentro da **mesma** casa o documento continua
único.

**Why this priority**: É o defeito de 18/09 e a lacuna do Artigo XIV:
o cadastro de hóspede era global. Sem o escopo, consentimento e
expurgo atravessam clientes, e um documento de outro hotel impede a
ficha desta casa.

**Independent Test**: Pode ser testado cadastrando o mesmo documento
em dois hotéis: os dois salvam. No mesmo hotel, a segunda tentativa
é recusada. Consultas, consentimento e expurgo de um hotel não
alcançam o cadastro do outro. A verificação estrutural (hotel em
cada tabela ou filho obrigatório de quem tem) falha no hóspede
antes desta fatia e passa depois.

**Acceptance Scenarios**:

1. **Given** dois hotéis e o mesmo tipo e número de documento,
   **When** cada recepção grava a ficha do titular da sua casa,
   **Then** as duas gravações **sucedem**; cada hotel fica com o
   próprio cadastro.
2. **Given** um documento já gravado no hotel A, **When** a recepção
   do hotel B consulta fichas, consentimento ou a fila, **Then**
   **não** vê o hóspede do hotel A nem o documento dele.
3. **Given** um hóspede do hotel A com consentimento registrado,
   **When** o hotel B consulta ou altera consentimento, **Then** o
   registro do hotel A **permanece** e o hotel B **não** o lê como
   se fosse seu.
4. **Given** cadastros já existentes sem hotel no hóspede, **When**
   a migração corre, **Then** cada cadastro passa a pertencer ao
   hotel das suas reservas; ninguém fica sem hotel; reservas de um
   hotel **não** apontam para cadastro de outro.

---

### User Story 2 - A recepção vê quem já tem aquele documento na casa (Priority: P1)

Como recepcionista gravando a ficha no balcão, quero que um
documento já usado por **outro** hóspede **deste** hotel seja
recusado, e que o aviso **nomeie** essa pessoa e me leve à ficha
já gravada, para eu conferir no balcão em vez de ler só
“documento em uso”.

**Why this priority**: O recado atual não permite navegar até
ninguém. Nomear só é seguro depois do escopo por hotel — do
contrário o aviso revelaria hóspede de outro cliente.

**Independent Test**: Pode ser testado tentando gravar, no painel do
mesmo hotel, um documento que já pertence a outro titular: a
gravação é recusada, o aviso traz o nome e o caminho para a ficha
dessa pessoa (sem o documento), e uma tentativa equivalente no
outro hotel **não** cita esse nome nem esse caminho.

**Acceptance Scenarios**:

1. **Given** o hotel A com um hóspede já cadastrado com aquele
   documento, **When** a recepção do hotel A tenta gravar o mesmo
   tipo e número em **outro** hóspede, **Then** a gravação é
   **recusada** e o aviso **nomeia** o hóspede que já tem o
   documento e oferece o **mesmo tipo de caminho** que a fila do
   dia já usa para abrir a ficha dessa pessoa.
2. **Given** o mesmo documento no hotel B (outra casa), **When** a
   recepção do hotel A tenta gravar e é recusada por colisão **no
   A**, **Then** o aviso **não** nomeia o hóspede do hotel B nem
   oferece caminho para a ficha dele.
3. **Given** a recusa, **When** a recepção lê o aviso, **Then**
   identifica a pessoa pelo nome, abre a ficha já gravada nesta
   casa, e **não** vê o número do documento no aviso; o número
   **não** vai para log.
4. **Given** perfil que já não pode alterar ficha (equipe
   operacional ou gestão), **When** tenta gravar, **Then** a recusa
   de permissão **permanece**; esta fatia não abre a ficha para
   outros perfis.

---

### User Story 3 - Consentimento e expurgo param no controlador (Priority: P1)

Como hotel que é o controlador, quero que o consentimento que registrei
e o expurgo da ficha **não** alcancem hóspede de outra casa. Cada
relógio de retenção e cada histórico de aceite ficam na propriedade
dona do cadastro.

**Why this priority**: É o argumento de privacidade da fatia. Escopo
só no documento, sem este recorte, deixaria o expurgo e o
consentimento atravessando clientes.

**Independent Test**: Pode ser testado com dois hotéis, cada um com
seu hóspede (mesmo documento permitido): revogar ou expurgar no A
não altera cadastro, consentimento nem comprovante do B.

**Acceptance Scenarios**:

1. **Given** dois cadastros com o mesmo documento em hotéis
   diferentes, **When** o hotel A revoga o consentimento do seu
   hóspede, **Then** o consentimento do hotel B **não** muda.
2. **Given** o prazo de retenção da ficha vencido só no hotel A,
   **When** o expurgo da ficha corre, **Then** apaga (ou contabiliza)
   a ficha do hotel A e **não** a do hotel B.
3. **Given** o comprovante de retenção, **When** uma passagem
   termina, **Then** as contagens são **por hotel**; o hotel B não
   herda o que o A processou.

---

### Edge Cases

- Hóspede sem tipo ou sem número de documento: a unicidade de
  documento **não** se aplica; dois cadastros sem documento no mesmo
  hotel continuam possíveis, como hoje.
- Mesmo número com **tipos** diferentes (RG num hotel, CPF noutro, ou
  os dois no mesmo hotel): não é o mesmo documento; cada par tipo +
  número é único **dentro** do hotel.
- Hóspede já existente ligado a reservas de **mais de um** hotel na
  migração: vira **um cadastro por hotel**, com a ficha copiada para
  cada casa; as reservas de cada hotel passam a apontar para o
  cadastro daquela casa. Consentimento já registrado permanece no
  cadastro do hotel que o obteve; a outra casa **não** herda aceite
  que não registrou. Ninguém é apagado.
- Hóspede sem nenhuma reserva na migração: se existe **um** hotel,
  o cadastro fica dele. Se existem **dois ou mais**, a migração
  **não** inventa dono: registra os identificadores desses
  cadastros (nunca o documento) para correção humana, sem atribuir
  a outro cliente e sem apagar ninguém.
- Coleta pelo canal (WhatsApp/simulador) que tentaria gravar
  documento já usado **no mesmo** hotel: a unicidade por hotel vale
  igual; esta fatia **não** cria a pendência “é a mesma pessoa”
  (F9.5) nem a pergunta se os dados continuam os mesmos (F9.4).
- Aviso de colisão **nunca** inclui hóspede, nome, documento ou
  caminho para ficha de outro hotel, nem em tela nem em log. O
  número do documento **não** aparece no aviso.
- Quem já não pode ler ficha **não** recebe o caminho nem o nome
  do outro hóspede por esta fatia: a recusa de permissão permanece.
- Número de documento **não** aparece em log (Artigo VIII), nem na
  recusa nem na migração. Logs usam identificadores de cadastro,
  hotel e o fato (recusa ou atribuição).
- Consultas de domínio (ficha, fila, consentimento, expurgo)
  continuam filtradas pelo hotel da sessão, mesmo com uma única
  propriedade cadastrada.
- Cadastro mínimo da reserva (nome e telefone, ainda sem documento)
  continua criando um hóspede **daquele** hotel; não reaproveita
  cadastro de outra casa. Reaproveitar quem volta pelo telefone é
  F9.4.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Todo hóspede MUST pertencer a exatamente um hotel. O
  cadastro MUST NOT existir sem esse vínculo.
- **FR-002**: O mesmo tipo e número de documento MUST poder existir
  em hotéis diferentes, cada um com o próprio cadastro, sem recusa.
- **FR-003**: Dentro do mesmo hotel, o par tipo + número de
  documento MUST permanecer único quando ambos estão preenchidos. A
  garantia MUST valer no cadastro, não só no caminho feliz da
  aplicação (Artigo IX).
- **FR-004**: Quando a recepção tenta gravar um documento que já
  pertence a outro hóspede **do mesmo hotel**, o sistema MUST
  recusar a gravação. O aviso MUST nomear esse hóspede e MUST
  oferecer um caminho para abrir a ficha já gravada desta casa, do
  mesmo jeito que a fila do dia já abre ficha. MUST NOT mostrar o
  número do documento no aviso.
- **FR-005**: O aviso de documento repetido MUST NOT nomear, nem
  dar caminho, nem dar a entender hóspede de outro hotel. Só quem
  já pode ler ficha (recepção) vê nome e caminho; demais perfis
  continuam com a recusa de permissão.
- **FR-006**: Consultas e alterações de ficha, consentimento e
  expurgo MUST considerar o hotel. Consentimento e expurgo de um
  hotel MUST NOT alcançar hóspede de outro.
- **FR-007**: A migração dos cadastros já existentes MUST atribuir
  cada hóspede ao hotel das suas reservas. Hóspede ligado a
  reservas de mais de um hotel MUST virar um cadastro por hotel.
  Hóspede sem reserva MUST ficar do único hotel, se só houver um;
  se houver dois ou mais, MUST registrar os identificadores (nunca
  o documento) e MUST NOT inventar dono. MUST NOT apagar cadastro
  para “resolver” o escopo.
- **FR-008**: Um teste de verificação MUST olhar a **estrutura** do
  cadastro, não os dados (Artigo XIV): cada tabela MUST ter o
  identificador do hotel **ou** ser filha, por vínculo obrigatório,
  de uma tabela que o tem (o filho segue o pai). O hóspede hoje
  MUST reprovar nessa regra (só chega ao hotel pelo vínculo com a
  reserva) e MUST passar depois desta fatia. Exceção MUST ser
  nomeada no próprio teste, com o motivo. Tabela nova sem dono
  MUST falhar o teste, sem exigir o identificador do hotel em
  todo filho.
- **FR-009**: Número de documento, conteúdo de mensagem e dado de
  outro hotel MUST NOT aparecer em log. Recusa e migração registram
  identificadores e o fato.
- **FR-010**: Perfis, telas e recusas de permissão da ficha (F8.3)
  MUST permanecer. Esta fatia MUST NOT abrir cadastro de hóspede a
  quem já não o vê, nem criar tela nova de vínculo (F9.5).
- **FR-011**: A conferência de CPF (F9.2) MUST permanecer: número
  aceito continua em onze dígitos; recusa de dígito continua
  distinta da recusa por documento já usado na casa.

### Key Entities

- **Hóspede**: ficha cadastral da pessoa. Passa a pertencer a um
  hotel. Tipo e número de documento, quando preenchidos, são únicos
  **naquele** hotel.
- **Hotel**: controlador dos dados dos seus hóspedes. Não lê, não
  altera e não expurga cadastro de outra casa.
- **Reserva**: já pertence a um hotel; na migração, é o vínculo que
  diz a que casa o hóspede existente deve ficar (ou ser copiado).
- **Consentimento**: histórico por hóspede e portanto por
  controlador. Não atravessa hotel.
- **Aviso de documento repetido**: recusa visível à recepção quando
  o documento já é de outro hóspede da **mesma** casa; traz o nome
  dessa pessoa e o caminho para a ficha já gravada, como a fila do
  dia. Sem o número do documento.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das tentativas, dois hotéis gravam o mesmo
  documento sem recusa entre casas.
- **SC-002**: Em 100% das tentativas no mesmo hotel, documento já
  usado por outro hóspede é recusado; o aviso nomeia essa pessoa e
  permite abrir a ficha já gravada desta casa, sem mostrar o
  documento.
- **SC-003**: Em 0% dos avisos de documento repetido aparece nome ou
  identificação de hóspede de outro hotel.
- **SC-004**: Em 100% dos casos de consentimento ou expurgo, a ação
  de um hotel não altera cadastro, aceite nem comprovante do outro.
- **SC-005**: 100% dos hóspedes com reserva após a migração
  pertencem ao hotel das suas reservas; cadastro ligado a mais de
  um hotel na origem vira um por casa. Com um hotel só, 100% dos
  cadastros sem reserva ficam dele. Com dois ou mais, 0 desses
  cadastros recebem dono inventado; 100% dos identificadores
  entram no registro da migração, sem o documento.
- **SC-006**: A verificação estrutural do Artigo XIV falha enquanto
  o hóspede não tiver hotel próprio; depois desta fatia, passa.
  100% das tabelas ou têm o identificador do hotel ou são filhas,
  por vínculo obrigatório, de uma que tem — salvo exceção nomeada
  no teste, com o motivo.
- **SC-007**: 0 ocorrências de número de documento em log, na
  recusa e na migração.

## Assumptions

- “Pertencer a um hotel” significa: o cadastro de hóspede tem dono
  único (o controlador), e toda leitura ou escrita de ficha,
  consentimento e expurgo usa esse dono. Não é integração com o
  sistema de gestão da casa.
- A unicidade é do par tipo + número **dentro** do hotel, só quando
  os dois campos estão preenchidos — o mesmo recorte que hoje vale
  no cadastro global.
- O aviso à recepção usa o **nome** do hóspede já cadastrado na
  casa e o mesmo tipo de caminho que a fila do dia já usa para
  abrir a ficha. Não lista todas as estadias e **não** mostra o
  documento. Só recepção, só o mesmo hotel.
- Hóspede com reservas em mais de um hotel na migração vira um
  cadastro por hotel (pergunta já prevista no backlog da Fase 9).
  Consentimento não se copia para a casa que não o registrou.
- A verificação do Artigo XIV é estrutural (formato do cadastro),
  não uma varredura de linhas. Consentimento e mensagem continuam
  filhos do cadastro que já tem hotel; não ganham o identificador
  nesta fatia. Exceção à regra só existe se o próprio teste a
  nomear, com o motivo.
- A base de demonstração tem um hotel: hóspede sem reserva, nesse
  caso, fica dessa casa. A regra para dois ou mais hotéis (listar
  identificadores, não inventar dono) existe para não misturar
  controladores se a base crescer.
- F9.4 (telefone na pré-chegada) e F9.5 (vincular no painel) não
  abrem nesta fatia. A colisão no mesmo hotel, no balcão, continua
  recusa nomeada; a coleta não ganha tela nova.
- Foto de documento permanece fora do produto. A palavra “extrato”
  não existe neste produto.
- Prazos de retenção (ficha 5 anos após checkout, conversas 12
  meses) não mudam; só o alcance do expurgo, que passa a respeitar
  o hotel dono do cadastro.
