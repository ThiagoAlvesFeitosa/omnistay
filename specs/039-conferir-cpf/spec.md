# Feature Specification: Conferir o CPF antes de gravar

**Feature Branch**: `039-conferir-cpf`

**Created**: 2026-10-15

**Status**: Draft

**Input**: User description: "Quando o hóspede informa CPF na ficha, o
sistema confere o dígito verificador antes de aceitar o número. CPF
reprovado não é gravado: a ficha fica parcial, e a recepção confere o
documento com o hóspede, como já faz com qualquer ficha parcial. A
mesma conferência vale quando a recepção corrige a ficha no painel,
com aviso no momento de salvar. Os outros tipos de documento seguem
as regras atuais."
(backlog F9.2)

Restrições já decididas no projeto (entrada do specify): o sistema
**não** se integra ao sistema de gestão do hotel; foto de documento
não é aceita (Artigo VIII); conteúdo de mensagem e número de documento
**nunca** vão para log; na dúvida um humano vê — a ficha parcial já é
a ponte da recepção; esta fatia **só confere CPF** no momento de
aceitar o número, nos caminhos que a ficha já tem (coleta com o
hóspede e correção no painel). Unicidade por hotel (F9.3),
reconhecimento pelo telefone (F9.4) e pendência de colisão no painel
(F9.5) **não** entram aqui. RG e passaporte **não** ganham conferência
nova.

## Clarifications

### Session 2026-10-15

- Q: Quando a recepção tenta salvar a ficha com um CPF que não
  confere, a gravação inteira é recusada ou os outros campos daquele
  salvamento entram e só o CPF fica de fora? → A: Recusar o
  salvamento inteiro, com aviso no campo do CPF; o que a recepção
  digitou continua no formulário para ela corrigir só o CPF e salvar
  de novo, sem redigitar o resto. O que já estava gravado permanece.
- Q: Quando um CPF passa na conferência, o número é gravado sempre
  na mesma forma, ou exatamente como a pessoa digitou? → A: Gravar
  sempre só os onze dígitos depois de conferir; a ficha no painel e
  a cópia para o sistema de gestão mostram formatado
  (`000.000.000-00`). Os CPFs já gravados passam para a mesma forma
  na migração. Converter só quem não colide; os pares que cairiam
  no mesmo número ficam com a escrita original, sem apagar ninguém
  e sem mexer no índice único. A migração registra quantos pares
  ficaram de fora, só com os identificadores dos cadastros, nunca o
  CPF. Resolver quem é a mesma pessoa fica para a F9.3 e a F9.5.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - CPF inválido na ficha do hóspede não entra na base (Priority: P1)

Como operação do hotel, quero que um CPF com dígito trocado — digitado
pelo hóspede ou lido errado na coleta — **não** seja gravado. O número
cai fora da ficha, ela fica parcial, e a recepção confere o documento
com a pessoa, exatamente como já faz quando falta qualquer outro
campo.

**Why this priority**: É o defeito de 18/09: o número ia cru para a
base e só era notado se colidisse. Sem isto, a colisão trata dado
errado como se fosse outra pessoa, e um CPF malformado segue até a
submissão federal.

**Independent Test**: Pode ser testado enviando uma ficha cujo
documento é CPF com dígito verificador reprovado (os demais campos
podem estar preenchidos): o número **não** permanece gravado, a
reserva fica com ficha parcial, a recepção vê essa pendência como já
vê qualquer parcial, e **nenhuma** mensagem nova de correção é
disparada ao hóspede.

**Acceptance Scenarios**:

1. **Given** uma coleta em que o tipo de documento é CPF e o número
   tem os dígitos verificadores errados, **When** a ficha é
   consolidada, **Then** esse número **não** é gravado, a ficha fica
   **parcial**, e os demais campos utilizáveis permanecem.
2. **Given** uma ficha que só faltava o documento e o hóspede informa
   um CPF reprovado, **When** a consolidação termina, **Then** a
   reserva **não** passa a ficha completa — continua (ou passa a)
   parcial, visível na fila do dia como as demais parciais.
3. **Given** um CPF reprovado na coleta, **When** o processamento
   termina, **Then** o sistema **não** envia mensagem nova ao hóspede
   pedindo o documento de novo — a conferência é da recepção, como já
   é em qualquer ficha parcial.
4. **Given** um CPF com pontuação (pontos e hífen) cujos dígitos
   verificadores fecham, **When** a ficha é consolidada, **Then** o
   número é aceito da mesma forma que o mesmo CPF sem pontuação, e
   o que fica gravado são **só os onze dígitos**.

---

### User Story 2 - A recepção vê o recado na hora de salvar (Priority: P1)

Como recepcionista conferindo o documento com o hóspede, quero que um
CPF reprovado recuse **o salvamento inteiro**, com aviso **no campo
do CPF**, e que o que eu acabei de digitar **continue no formulário**
— para eu corrigir só o número e salvar de novo, sem redigitar o
resto, e sem gravar um número que a Receita não reconhece.

**Why this priority**: A F8.3 já deixa a recepção completar e
corrigir a ficha. Sem a mesma conferência nesse caminho, o WhatsApp
fica protegido e o painel continua gravando dígito trocado.

**Independent Test**: Pode ser testado abrindo a ficha no painel,
alterando outro campo e informando CPF reprovado: nada daquele clique
é gravado, o aviso aparece no campo do CPF, o formulário conserva o
que foi digitado, o que já estava persistido permanece, e um CPF
válido (com ou sem pontuação) salva normalmente.

**Acceptance Scenarios**:

1. **Given** a recepção editando a ficha com tipo CPF e número
   reprovado, **When** ela confirma a gravação, **Then** **nada**
   daquele salvamento é persistido, o aviso aparece **no campo do
   CPF** (o CPF não confere), e não se inventa valor.
2. **Given** a recepção alterou outros campos e informou CPF
   reprovado no mesmo salvamento, **When** a gravação é recusada,
   **Then** o que já estava gravado permanece, o que ela digitou
   **continua no formulário**, e ela corrige só o CPF e salva de novo
   sem redigitar o resto; a ficha continua parcial se o documento era
   o que faltava.
3. **Given** tipo CPF e número com dígitos verificadores válidos,
   **When** a recepção salva, **Then** o documento é aceito (gravado
   em onze dígitos), a ficha e a cópia mostram `000.000.000-00`, e,
   se era o último campo ausente, a ficha passa a completa — sem
   mensagem ao hóspede.
4. **Given** data de nascimento, CEP, telefone ou tipo de documento
   já recusados pelas regras atuais, **When** a recepção salva,
   **Then** essas recusas **continuam iguais**; só o CPF ganha a
   conferência nova.

---

### User Story 3 - Sequências artificiais e a massa de demonstração (Priority: P2)

Como quem demonstra o produto e como operação, quero que sequências
de um só dígito (como 111.111.111-11) sejam reprovadas — a Receita
não as reconhece — e que a massa de demonstração use só CPFs que
passam na conferência, para o tour não nascer com documento inválido.

**Why this priority**: Fecha o caso que “parece CPF” e o dado de
demonstração que hoje usa um número cujos dígitos não fecham. Não
bloqueia o caminho do hóspede nem o da recepção.

**Independent Test**: Pode ser testado tentando gravar 111.111.111-11
(e equivalentes de um só dígito) nos dois caminhos, e conferindo que
a demonstração só apresenta CPFs aceitos.

**Acceptance Scenarios**:

1. **Given** tipo CPF e número formado por onze dígitos iguais (com
   ou sem pontuação), **When** a ficha é consolidada ou salva no
   painel, **Then** o número é reprovado como qualquer outro CPF que
   não confere.
2. **Given** a massa de demonstração do produto, **When** um hóspede
   de demonstração tem tipo CPF, **Then** o número associado **passa**
   na conferência do dígito verificador.
3. **Given** tipo RG ou passaporte, **When** o número é informado
   (hóspede ou painel), **Then** as regras atuais de aceite
   permanecem; **não** se aplica dígito verificador de CPF.
4. **Given** cadastros antigos com tipo CPF, **When** a migração
   corre, **Then** os que não colidem passam a onze dígitos; os
   pares que cairiam no mesmo número **permanecem com a escrita
   original**; ninguém é apagado; o índice único não muda; o
   registro da migração traz a contagem e os identificadores, **sem**
   o CPF.

---

### Edge Cases

- CPF com espaços extras, pontos ou hífen: a conferência olha os
  dígitos; pontuação não reprova um número que fecha nem salva um
  que não fecha. Aceito, grava-se só os onze dígitos.
- A ficha no painel e o texto copiado para o sistema de gestão
  mostram o CPF formatado (`000.000.000-00`); o valor gravado
  continua sendo os onze dígitos.
- CPFs já gravados com tipo CPF passam à forma de onze dígitos na
  migração, **exceto** os pares que cairiam no mesmo número: esses
  ficam com a escrita original. Ninguém é apagado. O índice único
  não muda. A migração registra quantos pares ficaram de fora, só
  com identificadores de cadastro, nunca o CPF. Quem é a mesma
  pessoa fica para F9.3 e F9.5.
- Menos ou mais de onze dígitos, letras no lugar do número, campo
  vazio: o número não é gravado; trata-se como campo ausente ou
  ilegível, no mesmo espírito dos outros campos da ficha.
- Tipo de documento ausente ou que não é CPF: o número, se houver,
  segue as regras atuais daquele tipo — a conferência de CPF **não**
  corre.
- CPF válido na coleta e depois a recepção tenta trocar por um
  reprovado: o salvamento inteiro é recusado; o valor gravado válido
  permanece; o formulário conserva o que ela digitou.
- No painel, recusa de CPF **não** grava os demais campos daquele
  clique. Não é “salvar o resto e soltar o CPF”.
- Número reprovado **não** aparece em log, nem como “tentativa”, nem
  na mensagem de aviso técnico. O aviso à recepção no painel pode
  dizer que o CPF não confere, sem repetir o número em registro de
  log.
- Fichas já gravadas **não** têm o dígito revalidado em lote: só
  mudam de forma (onze dígitos) quando a conversão não colide. O
  próximo salvamento no painel recusa número ruim.
- Foto de documento continua inexistente como caminho de entrada.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Quando o tipo de documento é CPF, o sistema MUST
  conferir o dígito verificador **antes** de aceitar o número, tanto
  na ficha vinda do hóspede quanto na correção feita pela recepção.
- **FR-002**: CPF com dígito verificador válido MUST ser aceito com
  ou sem pontuação. O valor gravado MUST ser sempre os **onze
  dígitos**, sem pontuação. A ficha no painel e a cópia para o
  sistema de gestão MUST mostrar o número formatado
  (`000.000.000-00`).
- **FR-003**: CPF reprovado MUST NOT ser gravado. O campo de número
  fica de fora; a ficha permanece ou passa a **parcial**.
- **FR-004**: Sequências de um só dígito (onze dígitos iguais) MUST
  ser reprovadas.
- **FR-005**: CPF reprovado na coleta do hóspede MUST NOT disparar
  mensagem nova de correção. A pendência segue o fluxo já existente
  de ficha parcial (fila do dia e conferência humana).
- **FR-006**: No painel, tentativa de salvar CPF reprovado MUST
  recusar **o salvamento inteiro**. O aviso MUST aparecer no campo
  do CPF. O que a recepção digitou MUST permanecer no formulário
  para ela corrigir só o número e salvar de novo. O que já estava
  gravado MUST permanecer.
- **FR-007**: RG e passaporte MUST continuar sob as regras atuais de
  aceite; esta fatia MUST NOT inventar conferência para eles.
- **FR-008**: A massa de demonstração MUST usar apenas CPFs que
  passam na conferência, sempre que o tipo for CPF, gravados em
  onze dígitos.
- **FR-009**: O número de CPF MUST NOT aparecer em log, nem na
  recusa de gravação nem no registro da migração. Logs registram
  identificadores e o fato (recusa ou pares deixados de fora),
  nunca o documento.
- **FR-010**: Na coleta do hóspede, demais campos utilizáveis da
  ficha MUST permanecer quando só o CPF é recusado. No painel, a
  recusa MUST NOT persistir nenhum campo daquele salvamento. A
  recusa MUST NOT apagar o que já era válido nem inventar número.
- **FR-011**: As recusas já existentes da ficha (data de nascimento,
  CEP, telefone, tipo fora de RG/CPF/passaporte) MUST permanecer;
  esta fatia acrescenta a conferência de CPF, não as substitui.
- **FR-012**: CPFs já gravados com tipo CPF MUST passar à forma de
  onze dígitos na migração **quando a forma nova não colide** com
  outro cadastro. Pares que cairiam no mesmo número MUST permanecer
  com a escrita original. A migração MUST NOT apagar cadastro e
  MUST NOT alterar o índice único. MUST registrar a contagem de
  pares deixados de fora e os identificadores desses cadastros,
  nunca o CPF. Resolver quem é a mesma pessoa fica para F9.3 e
  F9.5.

### Key Entities

- **Ficha do titular**: os campos da pessoa na reserva, inclusive
  tipo e número de documento. Pode estar completa ou parcial. É o
  que o hóspede envia na coleta e o que a recepção lê e corrige.
- **CPF**: quando o tipo de documento é CPF, o número só entra na
  ficha se os dígitos verificadores conferem e não é sequência de um
  só dígito. Gravado em onze dígitos; exibido e copiado como
  `000.000.000-00`.
- **Ficha parcial**: estado já existente quando falta campo
  utilizável. CPF recusado conta como número ausente para esse
  estado. A recepção já a vê na fila do dia e a completa no painel.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% das gravações com tipo CPF e número reprovado
  (hóspede ou painel), o número **não** permanece na ficha.
- **SC-002**: Em 100% desses casos na coleta, a reserva fica visível
  como ficha parcial para a recepção, **sem** mensagem extra ao
  hóspede.
- **SC-003**: Em 100% das tentativas no painel com CPF reprovado, a
  gravação inteira é recusada, o aviso aparece no campo do CPF, o
  formulário conserva o que foi digitado, e nada daquele clique é
  gravado.
- **SC-004**: 100% dos CPFs da massa de demonstração passam na
  conferência.
- **SC-005**: 0 ocorrências de número de CPF em log, na recusa e
  na migração.
- **SC-006**: RG e passaporte aceitos hoje continuam aceitos; a
  fatia não aumenta a taxa de recusa desses tipos.
- **SC-007**: 100% dos CPFs antigos que não colidem passam a onze
  dígitos; 100% dos pares que colidiriam permanecem com a escrita
  original; o índice único segue intacto; o registro da migração
  traz a contagem e só identificadores.

## Assumptions

- A conferência é a da Receita Federal para CPF de onze dígitos
  (dois dígitos verificadores), aplicada ao que a pessoa informou,
  independentemente de pontuação. O que se grava, depois de
  conferir, são os onze dígitos.
- “Reprovado” cobre dígito verificador que não fecha, sequência de
  um só dígito, e quantidade de dígitos diferente de onze.
- O fluxo de ficha parcial (fila do dia, tela da ficha, ausência de
  reenvio ao hóspede) **já existe** (coleta e F8.2/F8.3); esta fatia
  não cria fila, tela nem mensagem nova — só passa a tratar CPF
  reprovado como campo não utilizável.
- Completar a ficha no painel continua sem confirmar chegada nem
  saída, e continua sem enviar mensagem ao hóspede.
- Não há correção em lote do **dígito** de fichas antigas: CPF já
  gravado só muda de forma (onze dígitos) quando não colide, não é
  revalidado nem apagado. O próximo salvamento no painel recusa
  número ruim.
- Pares antigos que cairiam no mesmo número não são fundidos nesta
  fatia. Colisão de documento, escopo de hóspede por hotel e
  reconhecimento pelo telefone ficam nas fatias F9.3–F9.5.
- Foto de documento permanece fora do produto.
- A palavra “extrato” não existe neste produto.
