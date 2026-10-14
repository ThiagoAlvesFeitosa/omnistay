# Feature Specification: O worker não para por causa de um trabalho

**Feature Branch**: `038-worker-isolamento-falha`

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "Um erro inesperado ao processar um trabalho da
fila não interrompe o worker. O trabalho que falhou é registrado como tal e
volta a ser tentado com espera crescente, até o limite de tentativas da
propriedade; ao atingir o limite, fica marcado como falha. Os demais
trabalhos continuam sendo processados, e o que já foi concluído não é
desfeito. As rotinas agendadas — lembretes, boas-vindas, pulso, coleta de
mercado e expurgo por retenção — seguem rodando mesmo que o processamento
de mensagens falhe, e uma não impede a outra. O registro da falha nunca
contém dado pessoal."
(backlog F9.1)

Restrições já decididas no projeto (entrada do specify): o sistema **não**
se integra ao sistema de gestão do hotel; a fila é a fonte da verdade
(Artigo IV); gravar e comunicar são operações separadas (Artigo III);
conteúdo de mensagem e dado pessoal **nunca** vão para log (Artigo VIII);
prazos, limites e intervalos vêm da configuração da propriedade, nunca de
número mágico no código; na dúvida um humano vê — descarte silencioso de
trabalho não é opção; esta fatia **corrige o consumidor e o laço já
existentes** (a partir do envio da coleta e do expurgo), sem inventar
tela nova, operação nova na matriz de perfis nem canal novo. Conferência de
CPF (F9.2), hóspede por hotel (F9.3), reconhecimento pelo telefone (F9.4) e
pendência de colisão no painel (F9.5) **não** entram aqui.

## Clarifications

### Session 2026-10-14

- Q: Quando um trabalho atinge o limite de tentativas e fica em falha, o que a recepção precisa ver no painel nesta fatia? → A: Distintivo na Fila do dia, na linha da reserva afetada, **com sinal próprio** — distinto dos três sinais de pendência que a fila já tem e do “aguardando a recepção” (regra da 029: cada pendência com sinal próprio). Vale para todo trabalho ligado a uma reserva; coleta de mercado, sem reserva, fica só no registro do trabalho. O sinal não mostra o erro técnico nem dado pessoal, só o que deixou de acontecer (por exemplo “ficha não processada” ou “mensagem do hóspede sem resposta”). Permanece até a saída da estadia. Sem botão de “ciente” (seria operação nova). Sem destino, lista ou menu novos.
- Q: Se a mesma reserva tiver dois trabalhos em falha definitiva, o que a linha da Fila do dia mostra? → A: Agrupado por tipo: um rótulo para cada **coisa que deixou de acontecer**, todos visíveis na mesma linha. Falhas repetidas do mesmo tipo viram um rótulo só, com a contagem (por exemplo “2 mensagens do hóspede sem resposta”).
- Q: De onde vêm o teto de tentativas e a espera crescente, e o que acontece se o teto faltar na propriedade? → A: O teto continua sendo o parâmetro já usado na falha de envio, com o padrão **5**. A espera crescente é a **mesma regra** que a fila já aplica quando o envio falha. MUST NOT criar parâmetro novo de espera. Limite ausente ou ilegível usa o padrão 5, em vez de falhar.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Um trabalho com erro não derruba o resto da fila (Priority: P1)

Como operação do hotel, quero que um trabalho da fila que estoura — por
exemplo a consolidação da ficha que esbarra numa unicidade de documento —
fale sozinho: fica registrado, volta a ser tentado com espera crescente até
o teto da casa, e depois fica em falha, **sem** parar o worker e **sem**
desfazer o que já tinha sido concluído na mesma passagem.

**Why this priority**: É o defeito que, em 18/09/2026, derrubou o worker no
simulador. Sem isto, qualquer erro das fatias seguintes da Fase 9 (e
qualquer erro ainda não visto) volta a desligar lembrete, pulso, coleta e
expurgo junto.

**Independent Test**: Pode ser testado enfileirando um trabalho que
provoca erro inesperado (incluindo violação de unicidade ao consolidar
ficha, no espírito do caso de 18/09) seguido de outro trabalho saudável na
mesma passagem: o primeiro é reagendado com uma tentativa a mais e espera
maior; o segundo é processado; o worker não encerra; um trabalho já
concluído antes do erro permanece concluído.

**Acceptance Scenarios**:

1. **Given** uma passagem com um trabalho cujo processamento lança
   exceção inesperada e outro trabalho ainda pendente na fila,
   **When** a passagem corre, **Then** o que falhou é reagendado (uma
   tentativa a mais, próxima tentativa mais tarde que a anterior) e o
   seguinte é processado na **mesma** passagem.
2. **Given** um trabalho que já atingiu o limite de tentativas da
   propriedade, **When** o processamento falha de novo (ou o limite é
   alcançado nessa falha), **Then** o status fica de **falha** e esse
   trabalho **não** volta a ser reclamado.
3. **Given** um trabalho já **concluído** nesta ou em passagem anterior,
   **When** outro trabalho da mesma passagem falha, **Then** o
   concluído permanece concluído — o erro de um não desfaz o outro.
4. **Given** o caso de 18/09 — unicidade ao consolidar a ficha —,
   **When** o worker processa esse trabalho na primeira passagem e nas
   seguintes, **Then** o worker **não** encerra em nenhuma delas; o
   trabalho segue o ciclo de tentativa e, se o teto for atingido, fica
   em falha.

---

### User Story 2 - O registro da falha não vaza dado pessoal (Priority: P1)

Como titular dos dados e como operação do hotel, quero que o registro da
falha (no trabalho e no log) traga só o **nome** da exceção, nunca a
mensagem do banco, nunca parâmetros da consulta e nunca CPF, telefone ou
texto de conversa — para o diagnóstico existir sem repetir o vazamento de
18/09, em que o CPF ia na mensagem de erro.

**Why this priority**: O Artigo VIII e o achado da auditoria: capturar
erro sem esta regra grava o documento do hóspede. Sem isto a US1
"funciona" e ainda assim viola minimização.

**Independent Test**: Pode ser testado provocando uma exceção cuja
mensagem contém um CPF (e, se couber, parâmetros de consulta): o campo de
erro do trabalho e o log correspondente mostram o nome da exceção e
**não** o CPF, **não** a mensagem completa e **não** os parâmetros.

**Acceptance Scenarios**:

1. **Given** um processamento que falha com uma exceção cuja mensagem
   contém um CPF, **When** a falha é registrada, **Then** o registro no
   trabalho e no log contém o nome da exceção e **não** contém o CPF nem
   a mensagem da exceção.
2. **Given** uma falha originada numa consulta, **When** o erro é
   gravado, **Then** os parâmetros da consulta **não** aparecem no
   registro nem no log.
3. **Given** um trabalho em falha definitiva, **When** alguém inspeciona
   o registro, **Then** não há conteúdo de mensagem de hóspede nesse
   registro.

---

### User Story 3 - Mensagens e rotinas agendadas não se derrubam (Priority: P1)

Como operação do hotel, quero que o ciclo do worker trate a passagem de
mensagens, os lembretes, as boas-vindas, o pulso, a coleta de mercado e o
expurgo por retenção como etapas **isoladas**: se uma falhar, as outras do
mesmo ciclo ainda rodam — sobretudo o expurgo, que hoje cai junto quando
o worker morre no meio das mensagens.

**Why this priority**: A auditoria da Fase 6 (achados 3.2, 3.3 e 3.12):
expurgo no mesmo laço que as mensagens. Sem isolamento, a F9.1 só tapa a
fila e deixa a retenção declarada novamente refém de um erro de ficha.

**Independent Test**: Pode ser testado forçando falha na passagem de
mensagens e verificando que expurgo e as verificações agendadas do mesmo
ciclo ainda executam; e forçando falha em uma verificação agendada sem
impedir as demais nem a passagem.

**Acceptance Scenarios**:

1. **Given** uma falha na passagem de trabalhos de mensagem no ciclo,
   **When** o ciclo segue, **Then** o expurgo por retenção **e** as
   verificações agendadas (lembretes, boas-vindas, pulso, coleta de
   mercado) **ainda** ocorrem nesse ciclo.
2. **Given** uma falha em **uma** das rotinas agendadas (por exemplo
   só a coleta de mercado), **When** o ciclo segue, **Then** as outras
   rotinas agendadas e o expurgo **não** são pulados por causa dessa
   falha.
3. **Given** uma falha no expurgo, **When** o ciclo segue, **Then** a
   passagem de mensagens e as demais verificações agendadas **não**
   deixam de ocorrer por causa dessa falha.

---

### User Story 4 - A recepção vê o que deixou de acontecer (Priority: P1)

Como recepção no turno, quero um distintivo **próprio** na Fila do dia
quando um trabalho ligado àquela reserva chegou ao teto de tentativas,
para a omissão não sumir no mesmo visual de chegada vencida, recado não
enviado, saída não confirmada ou “aguardando a recepção” — a próxima
ação é outra.

**Why this priority**: Artigo V e a regra da 029 (cada pendência com
sinal próprio). Sem isto a US1 deixa o worker no ar e a recepção não
sabe que a ficha ou a mensagem parou.

**Independent Test**: Pode ser testado com uma reserva na fila do dia
e um trabalho vinculado em falha definitiva: a linha mostra um
rótulo do que deixou de acontecer, distinto dos quatro sinais já
existentes; o texto não contém CPF, telefone, conteúdo de mensagem
nem nome de exceção; após a saída confirmada da estadia, o sinal não
aparece mais nessa reserva.

**Acceptance Scenarios**:

1. **Given** uma reserva visível na Fila do dia e um trabalho **ligado
   a essa reserva** em falha definitiva, **When** a recepção olha a
   linha, **Then** aparece um distintivo próprio, visualmente distinto
   de chegada vencida, recado de boas-vindas não enviado, saída não
   confirmada e “aguardando a recepção”.
2. **Given** o distintivo visível, **When** a pessoa lê o texto,
   **Then** ele descreve o que deixou de acontecer (espírito “ficha
   não processada” ou “mensagem do hóspede sem resposta”) e **não**
   mostra erro técnico, nome de exceção nem dado pessoal.
3. **Given** um trabalho de coleta de mercado em falha definitiva
   (sem reserva), **When** a recepção olha a Fila do dia, **Then**
   essa falha **não** aparece como distintivo de linha; permanece só
   no registro do trabalho.
4. **Given** o distintivo numa estadia ainda não encerrada, **When** a
   saída é confirmada, **Then** o sinal deixa de aparecer para essa
   reserva. MUST NOT haver controle de “ciente” nem operação nova só
   para silenciar o distintivo.
5. **Given** na mesma reserva um trabalho de ficha em falha e um de
   mensagem em falha (tipos distintos do que deixou de acontecer),
   **When** a recepção olha a linha, **Then** os dois rótulos
   aparecem na mesma linha, cada um nomeando a sua omissão.
6. **Given** dois trabalhos do **mesmo** tipo em falha definitiva na
   mesma reserva, **When** a recepção olha a linha, **Then** há um
   só rótulo desse tipo, com a contagem (espírito “2 mensagens do
   hóspede sem resposta”), não duas frases iguais.

---

### Edge Cases

- Trabalho que falha **antes** de qualquer efeito observável: reagendado
  como os demais; não inventa conclusão.
- Trabalho que falha **depois** de efeito parcial no próprio trabalho:
  o resultado desse trabalho não é tratado como concluído; a próxima
  tentativa segue as regras de idempotência já existentes da fila (não
  duplicar envio cuja unicidade o banco já garante).
- Fila só com trabalhos em falha definitiva: a passagem não os reclama;
  o worker permanece no ar para rotinas agendadas e trabalhos novos.
- Limite de tentativas ausente ou ilegível na propriedade: usa o
  **padrão já existente (5)**, o mesmo do teto de envio; MUST NOT
  abortar a passagem nem o ciclo por causa disso. Sem parâmetro novo
  de espera.
- Consulta ou processamento que se alonga: um trabalho não segura o
  ciclo inteiro sem limite de tempo; ao estourar, vale o mesmo ciclo de
  tentativa da US1, com registro sem parâmetros de consulta (US2).
- Várias propriedades: o teto é o da **propriedade do trabalho**,
  não de outra casa; a espera crescente segue a regra da fila, sem
  chave nova.
- Trabalho em falha **sem** reserva (coleta de mercado): sem
  distintivo na Fila do dia.
- Distintivo some com a **saída confirmada** da estadia, não com um
  gesto de “ciente”.
- Tentativas ainda em curso (ainda não é falha definitiva): a Fila
  do dia MUST NOT usar o distintivo desta fatia — continua o estado
  atual da reserva.
- Vários trabalhos em falha na mesma reserva: um rótulo por tipo do
  que deixou de acontecer; o mesmo tipo agrega e mostra a quantidade.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Um erro inesperado ao processar um trabalho da fila
  MUST NOT encerrar o worker nem abortar a passagem inteira.
- **FR-002**: O trabalho que lançou a exceção MUST ser registrado como
  tentativa falha, com o contador de tentativas incrementado, e MUST
  ser reagendado com espera **crescente** (cada nova tentativa mais
  tarde que a anterior), até o limite de tentativas da propriedade.
- **FR-003**: Ao atingir o limite de tentativas da propriedade, o
  trabalho MUST ficar com status de **falha** e MUST NOT voltar a ser
  reclamado.
- **FR-004**: Os demais trabalhos pendentes da mesma passagem MUST
  continuar a ser processados após a falha de um.
- **FR-005**: Trabalho já **concluído** MUST permanecer concluído
  quando outro trabalho falha — o efeito de um MUST NOT desfazer o do
  outro.
- **FR-006**: O caso de unicidade ao consolidar ficha (18/09) MUST ser
  coberto pelos FR-001 a FR-005 na primeira passagem e nas seguintes.
- **FR-007**: O erro gravado no trabalho e o evento de log
  correspondente MUST ser o **nome** da exceção. MUST NOT incluir a
  mensagem da exceção, MUST NOT incluir parâmetros de consulta, MUST
  NOT incluir CPF, telefone, conteúdo de mensagem nem qualquer outro
  dado pessoal. Teste obrigatório com exceção cuja mensagem contém CPF.
- **FR-008**: O teto de tentativas MUST ser o parâmetro da
  propriedade **já usado** na falha de envio, cujo padrão existente
  é **5**. A espera crescente MUST ser a **mesma regra técnica** que
  a fila já usa quando o envio falha. MUST NOT criar parâmetro novo
  de espera. Se o teto estiver ausente ou ilegível, MUST aplicar o
  padrão 5 — MUST NOT falhar o ciclo por parâmetro faltando.
- **FR-009**: Falha na passagem de mensagens MUST NOT impedir, no mesmo
  ciclo, o expurgo por retenção nem as verificações agendadas
  (lembretes, boas-vindas, pulso, coleta de mercado).
- **FR-010**: Falha em uma rotina agendada MUST NOT impedir as demais
  nem o expurgo; falha no expurgo MUST NOT impedir a passagem nem as
  demais rotinas.
- **FR-011**: O processamento de cada trabalho MUST ter limite de
  tempo por consulta, no mesmo espírito já existente na API, de modo
  que uma consulta pendurada não segure o ciclo; o registro dessa
  falha segue o FR-007 (sem parâmetros de consulta).
- **FR-012**: Esta fatia MUST NOT acrescentar destino de painel, item
  de menu, operação nova na matriz de perfis (incluindo qualquer
  “ciente” ou equivalente) nem canal de mensagem. A pendência de
  **colisão de documento** permanece da F9.5.
- **FR-013**: Trabalho em falha definitiva **ligado a uma reserva**
  MUST produzir na Fila do dia, na linha dessa reserva, um distintivo
  **próprio**, distinto dos sinais já existentes: chegada vencida,
  recado de boas-vindas não enviado, saída não confirmada e
  “aguardando a recepção”.
- **FR-014**: O texto do distintivo MUST descrever o que deixou de
  acontecer, no espírito dos exemplos “ficha não processada” e
  “mensagem do hóspede sem resposta”. MUST NOT exibir erro técnico,
  nome de exceção, CPF, telefone, conteúdo de mensagem nem outro dado
  pessoal.
- **FR-015**: Coleta de mercado (e qualquer trabalho sem reserva)
  MUST NOT aparecer como distintivo na Fila do dia; a falha permanece
  só no registro do trabalho.
- **FR-016**: O distintivo MUST permanecer enquanto a estadia não
  tiver saída confirmada, e MUST desaparecer após essa confirmação.
  MUST NOT existir ação só para marcar ciência.
- **FR-017**: Na mesma linha, MUST haver um rótulo por tipo do que
  deixou de acontecer, todos visíveis. Falhas definitivas do mesmo
  tipo na mesma reserva MUST colapsar num único rótulo com a
  **contagem** (espírito “2 mensagens do hóspede sem resposta”).
  MUST NOT repetir o mesmo texto uma vez por trabalho.

### Key Entities

- **Trabalho da fila**: unidade de processamento assíncrono da
  propriedade (envio, interpretação, classificação, etc.). Tem status
  (pendente, em processamento, concluído, falha), contagem de
  tentativas, instante da próxima tentativa e registro da última
  falha. O payload já carrega identificadores, não texto pessoal.
- **Passagem**: um ciclo de reclamação e processamento de trabalhos
  elegíveis (pendentes cuja próxima tentativa já venceu).
- **Ciclo do worker**: a passagem de mensagens mais as rotinas
  agendadas (lembretes, boas-vindas, pulso, coleta de mercado) e o
  expurgo por retenção. Cada etapa é isolada das outras nesta fatia.
- **Configuração da propriedade**: o teto de tentativas já existente
  para falha de envio (padrão 5, por hotel). A espera crescente não
  é chave nova — reusa a regra da fila na falha de envio.
- **Distintivo de trabalho em falha**: um ou mais rótulos na linha da
  Fila do dia, agrupados pelo tipo do que deixou de acontecer, com
  contagem quando o mesmo tipo se repete; não é os quatro sinais já
  entregues nem a pendência de colisão da F9.5.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Numa passagem com um trabalho que estoura e outro
  saudável em seguida, o saudável é processado **na mesma passagem**;
  o worker permanece no ar.
- **SC-002**: Depois do teto de tentativas da casa, o trabalho em
  falha **não** é reclamado de novo em nenhuma passagem seguinte
  observada no teste.
- **SC-003**: Trabalho concluído antes do erro de outro permanece
  concluído em 100% dos casos cobertos pelos testes da fatia.
- **SC-004**: Com uma exceção cuja mensagem contém CPF, o registro da
  falha e o log **não** contêm o CPF, a mensagem nem parâmetros de
  consulta — em 100% das asserções da US2.
- **SC-005**: Com a passagem de mensagens forçada a falhar, expurgo e
  cada verificação agendada nomeada nesta spec ainda executam no mesmo
  ciclo; com uma única rotina agendada forçada a falhar, as outras e o
  expurgo ainda executam.
- **SC-006**: Com trabalho em falha definitiva ligado a uma reserva
  da Fila do dia, a linha mostra o distintivo próprio em 100% dos
  casos cobertos; o texto não contém dado pessoal nem nome de
  exceção; após confirmar a saída, o sinal some. Coleta de mercado em
  falha não altera nenhuma linha da fila.
- **SC-007**: Com dois tipos distintos em falha na mesma reserva, a
  linha mostra os dois rótulos. Com duas falhas do mesmo tipo, mostra
  um rótulo e a contagem, nunca duas cópias do mesmo texto.

## Assumptions

- O worker, a fila durável, os tipos de trabalho e as rotinas
  agendadas **já existem**; esta fatia muda o isolamento de erro, não
  o catálogo de tipos.
- “Espera crescente” é a regra que a fila **já aplica** na falha de
  envio (cada nova tentativa mais tarde que a anterior). Não se cria
  parâmetro novo nem fórmula paralela nesta fatia.
- A Fila do dia já lista a reserva; esta fatia acrescenta só os
  rótulos na linha, reusando a consulta que a recepção já faz. O
  catálogo de frases por tipo (além dos exemplos da sessão de 14/10)
  e a concordância no plural da contagem ficam no planejamento,
  desde que FR-014 e FR-017 sejam respeitados.
- Idempotência já garantida no banco (unicidade por tipo de trabalho)
  continua valendo nas retentativas; esta fatia não relaxa essas
  restrições.
- Testes desta fatia usam portas falsas e não chamam provedor de IA
  nem mensageria reais.

## Out of Scope

- Validar dígito de CPF (F9.2).
- `id_hotel` em hóspede e unicidade de documento por hotel (F9.3).
- Reconhecer retorno pelo telefone (F9.4).
- Tela “é a mesma pessoa” / pendência de colisão (F9.5).
- Redis, fila externa, orquestrador ou processo à parte só para
  expurgo.
- Integração com PMS ou SNRHos.
- Mudar o que o hóspede lê nas mensagens já especificadas.
