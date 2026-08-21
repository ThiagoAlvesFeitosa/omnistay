# Feature Specification: Coleta Agendada de Mercado

**Feature Branch**: `021-coleta-agendada`

**Created**: 2026-08-21

**Status**: Draft

**Input**: User description: "Na periodicidade configurada para a propriedade, o
sistema consulta as fontes públicas dos concorrentes ativos e registra preço e
avaliação encontrados, sempre com a data da coleta. Coletas que falham são
registradas como falha, e não confundidas com ausência de valor. O coletor
respeita as diretivas de acesso da fonte, identifica-se honestamente e não
coleta dado pessoal de avaliadores."
(backlog F5.2)

Restrições já decididas no projeto (entrada do specify): o sistema **não** se
integra ao sistema de gestão do hotel nem altera tarifa da casa — observa,
não precifica; periodicidade mora na configuração da propriedade, nunca em
número mágico; só fonte **ativa** entra (contrato da fatia anterior); cada
coleta **insere** registro novo e jamais sobrescreve o anterior; falha é
primeiro registro, não silêncio; o coletor obedece diretivas de acesso
publicadas, identifica-se de forma reconhecível e **não** armazena nome,
texto nem qualquer dado pessoal de avaliador individual; conteúdo de
mensagem de hóspede nunca vai para log; esta fatia **não** monta o painel
de mercado (isso é a fatia seguinte).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preço e avaliação entram sozinhos, com data (Priority: P1)

Como gestão do hotel, quero que, na cadência configurada para a casa, o
sistema consulte as fontes públicas dos concorrentes que ainda estão ativos
e grave o preço e a nota agregada que aparecem sem login — sempre com a
data daquela consulta — para eu deixar de abrir site na mão e para cada
número ter origem no tempo, não parecer “o preço de agora” sem prova.

**Why this priority**: Sem coleta datada, o cadastro da fatia anterior é
lista morta. O produto desta fatia é a **série**: cada visita vira um
registro novo. Sobrescrever o valor anterior destruiria o movimento de
tarifa que a fatia seguinte vai mostrar.

**Independent Test**: Pode ser testado com uma propriedade cuja periodicidade
já venceu, ao menos um concorrente ativo com fonte pública simulada que
devolve preço e nota, rodando a verificação de coleta e conferindo: nasce
um registro novo daquele concorrente, com data, marcado como sucesso, com
os valores encontrados, e o registro anterior (se houver) permanece
inalterado.

**Acceptance Scenarios**:

1. **Given** uma propriedade com periodicidade configurada, um concorrente
   ativo e a janela desde a última coleta (ou desde nunca) já vencida,
   **When** o sistema verifica a coleta daquela propriedade, **Then** a
   fonte ativa é consultada e nasce um registro novo com a data da consulta,
   o preço e/ou a nota agregada encontrados e indicação de sucesso.
2. **Given** um concorrente que já tem ao menos um registro de coleta,
   **When** um ciclo devido ocorre de novo, **Then** o sistema insere um
   segundo registro e **não** altera o conteúdo nem a data do anterior.
3. **Given** um concorrente desativado na mesma propriedade, **When** o
   ciclo devido roda, **Then** a fonte inativa **não** é visitada e **não**
   nasce registro novo para ela.
4. **Given** uma propriedade sem nenhum concorrente ativo, **When** a
   verificação roda, **Then** o ciclo termina sem erro e sem registros
   órfãos — lista vazia não é falha de coleta.

---

### User Story 2 - Falha fica registrada e não se mistura com valor (Priority: P1)

Como gestão, quero que uma coleta que não conseguiu ler a fonte fique
gravada como **falha**, com a data da tentativa, sem apagar nem substituir
o número anterior — para eu nunca tratar “não coletou” como “preço zero”
nem como “o último valor ainda vale como se fosse de hoje”.

**Why this priority**: Preço de concorrente sem data, ou falha silenciosa
que deixa o número velho parecer atual, induz decisão errada com aparência
de fundamento. É pior do que não ter dado. O critério de aceite da fatia
exige distinguir os dois.

**Independent Test**: Pode ser testado com um concorrente que já teve uma
coleta bem-sucedida e cuja fonte, no ciclo seguinte, falha (indisponível,
sem dado público, ou recusada pelas diretivas), verificando: nasce registro
novo marcado como falha, sem preço nem nota apresentados como encontrados,
e o registro anterior permanece intacto, com a data antiga.

**Acceptance Scenarios**:

1. **Given** um concorrente ativo cuja fonte não devolve preço nem nota
   agregada públicos neste ciclo, **When** a coleta é tentada, **Then**
   nasce um registro novo com data, marcado como falha, **sem** preço nem
   nota apresentados como valor encontrado.
2. **Given** um concorrente com coleta anterior bem-sucedida, **When** o
   ciclo seguinte falha, **Then** o registro anterior permanece com os
   mesmos valores e a mesma data — a falha **não** apaga, **não** zera e
   **não** redata o sucesso antigo.
3. **Given** uma fonte que apresenta preço público **zero**, **When** a
   coleta obtém esse valor com sucesso, **Then** o registro nasce como
   sucesso com preço zero — zero encontrado **não** é gravado como falha.
4. **Given** uma fonte que devolve só o preço, ou só a nota agregada,
   **When** a coleta obtém esse único dado público, **Then** o registro
   nasce como sucesso com o campo obtido preenchido e o outro vazio —
   vazio no campo não obtido **não** transforma o ciclo em falha.

---

### User Story 3 - Coletor honesto: diretivas, identidade e sem dado de avaliador (Priority: P1)

Como hotel que vai defender este produto em banca e como responsável pelos
dados, quero que o coletor leia e obedeça as diretivas de acesso publicadas
pela fonte **antes** de recolher o conteúdo, que se identifique como o
coletor desta casa — sem se passar por visitante comum — e que grave só
preço e nota **agregada**, nunca nome, texto ou qualquer dado pessoal de
quem avaliou, para a inteligência de mercado não nascer de coleta
desonesta nem de dado de terceiro identificável.

**Why this priority**: A arquitetura já registrou que postura ética reduz
fontes viáveis e frequência, e que esse é o preço de um produto
comercializável. Coletar atrás de login, disfarçar a identidade ou guardar
comentário de hóspede alheio invalida a fatia mesmo que o número apareça.

**Independent Test**: Pode ser testado com fontes simuladas: uma que
publica diretiva permitindo o endereço, uma que proíbe, uma que exige
login, e uma página que mistura nota agregada com nomes e textos de
avaliadores — verificando visita só onde a diretiva permite, recusa
honesta onde proíbe ou exige autenticação, identidade reconhecível em
toda visita, e nenhum dado pessoal de avaliador persistido.

**Acceptance Scenarios**:

1. **Given** uma fonte ativa que publica diretiva **permitindo** a consulta
   automatizada daquele endereço, **When** o ciclo devido roda, **Then** o
   coletor lê a diretiva primeiro, identifica-se de forma honesta e, só
   então, consulta o conteúdo público.
2. **Given** uma fonte ativa cuja diretiva de acesso **proíbe** a coleta
   automatizada daquele endereço, **When** o ciclo devido roda, **Then** o
   coletor **não** recolhe o conteúdo da página, nasce registro de **falha**
   com a data da tentativa, e o dado anterior permanece.
3. **Given** uma fonte que só mostra preço ou avaliação depois de login,
   **When** o ciclo devido roda, **Then** o coletor **não** envia credencial,
   **não** contorna a autenticação, e registra falha.
4. **Given** uma página pública que exibe nota agregada junto com nomes e
   textos de avaliadores individuais, **When** a coleta tem sucesso,
   **Then** persistem só o preço público (se houver) e a nota agregada;
   nome, identificador, foto e texto de avaliador **não** são armazenados
   em lugar nenhum.
5. **Given** qualquer visita à fonte (diretiva ou conteúdo), **When** a
   identidade do coletor é inspecionada, **Then** ela é reconhecível como
   o coletor desta casa e **não** imita um navegador de pessoa física.

---

### User Story 4 - Periodicidade da casa, isolamento e fora do fluxo do hóspede (Priority: P1)

Como hotel, quero que a cadência venha da configuração da **minha**
propriedade, que o concorrente do vizinho nunca seja visitado no meu ciclo,
e que essa coleta rode em paralelo — sem mandar mensagem ao hóspede, sem
mudar a tarifa da casa e sem abrir o painel de mercado — para acompanhar
o mercado sem misturar inteligência com operação de balcão.

**Why this priority**: Periodicidade em constante de regra seria defeito
(toda casa teria a mesma fome de coleta). Cruzar hotel quebraria
multi-tenant. Empurrar coleta para o canal do hóspede violaria “não ser
intrusivo”. O painel com histórico visível é a fatia seguinte; esta só
deposita a série.

**Independent Test**: Pode ser testado com duas propriedades, periodicidades
diferentes, concorrentes só em uma delas, avançando o relógio, e verificando
quem é visitado, quando, e que nenhuma mensagem de hóspede nasce. Ausência
da chave de periodicidade deve impedir a coleta daquela casa sem inventar
intervalo.

**Acceptance Scenarios**:

1. **Given** uma propriedade com periodicidade configurada e coleta recente
   dentro dessa janela, **When** a verificação roda de novo, **Then** aquela
   fonte **não** é visitada outra vez — o ciclo só volta a coletar quando a
   janela vence.
2. **Given** duas propriedades com periodicidades diferentes, **When** o
   relógio avança só o bastante para vencer a janela da primeira, **Then**
   só a primeira coleta; a segunda permanece quieta até a própria janela.
3. **Given** concorrentes cadastrados só no hotel A, **When** o ciclo do
   hotel B roda, **Then** nenhuma fonte do hotel A é visitada e nenhum
   registro de coleta do hotel A é lido ou gravado no ciclo de B.
4. **Given** a chave de periodicidade ausente ou inválida (vazia, zero,
   negativa, não numérica) numa propriedade, **When** a verificação roda,
   **Then** aquela propriedade **não** coleta, nenhum intervalo é suposto,
   e o desfecho é explícito no registro operacional (não é silêncio
   disfarçado de “nada pendente”).
5. **Given** um ciclo de coleta em andamento, **When** se observa o canal
   do hóspede e a tarifa da casa, **Then** nenhuma mensagem é enviada ao
   hóspede, nenhuma tarifa própria é alterada e nenhum painel de mercado
   é montado.

---

### Edge Cases

- Propriedade recém-instalada, sem concorrente ativo: a verificação não
  falha; não cria registro de coleta sem alvo.
- Concorrente recém-cadastrado, ainda sem nenhuma coleta: está devido na
  próxima verificação da propriedade, desde que a periodicidade esteja
  configurada — não espera “um ciclo fantasma” anterior.
- Concorrente desativado no meio da janela: some da lista de fontes ativas
  e não é visitado, mesmo que a última coleta já seja antiga.
- Concorrente reativado depois de muito tempo: a última coleta (ainda que
  antiga) conta para a janela; se a periodicidade já venceu, coleta na
  próxima verificação.
- Dois hotéis com o mesmo endereço de fonte: cada um tem a própria série.
  Um ciclo não serve o outro; um não lê o registro do outro.
- Verificação coincidente (duas passagens ao mesmo tempo sobre o mesmo
  concorrente devido): o ciclo produz **um** registro novo daquela janela,
  não um par contemporâneo que pareça dois ciclos.
- Diretiva de acesso ausente ou ilegível: o coletor **não** trata ausência
  como permissão ampla. Sem diretiva compreensível que autorize aquele
  endereço, a visita ao conteúdo **não** ocorre e a coleta é falha.
- Fonte que responde, mas o conteúdo não é público sem interação (captcha,
  desafio, bloqueio): falha, sem contornar.
- Preço público zero é sucesso; ausência de preço e de nota agregada é
  falha. Os dois desfechos são distinguíveis no registro.
- Nota agregada fora da escala pública usual da casa (zero a cinco) não é
  convertida por chute: a nota daquele ciclo fica vazia. Se houver preço
  público, o ciclo ainda pode ser sucesso; se não houver nem preço nem
  nota confiável, é falha.
- Página com vários preços (categorias, datas, “a partir de”): o coletor
  registra o **preço público em destaque** que a fonte mostra a quem visita
  sem login — em geral a tarifa de partida anunciada. Não enumera todas as
  categorias nem tenta casar com o tipo de quarto da casa. Se esse valor
  único não for obtível, o preço daquele ciclo fica vazio.
- O texto integral da página, recortes de avaliação e identificadores
  de avaliador **não** são persistidos. O registro guarda preço, nota
  agregada, data e se houve sucesso.
- Logs da coleta registram hotel, identificador do concorrente e desfecho
  (sucesso, falha, recusa por diretiva, fonte indisponível). **Não**
  registram o texto da página, nome de avaliador nem conteúdo de mensagem
  de hóspede.
- Alterar a periodicidade vale para a **próxima** verificação. Não há
  replay de ciclos perdidos nem coleta em rajada para “pôr a série em dia”.
- Esta fatia **não** oferece botão de “coletar agora” no painel, **não**
  monta tela de preços, **não** sinaliza dado desatualizado para a gestão
  (isso é a fatia seguinte) e **não** examina contrato jurídico em
  linguagem natural da fonte. Quem cadastra continua responsável por não
  incluir fonte com proibição contratual expressa; o coletor recusa o que
  as **diretivas de acesso publicadas** já proíbem.
- Esta fatia **não** muda tarifa da casa, **não** consulta o outro sistema
  do hotel e **não** envia mensagem ao hóspede.
- Cadastro, edição e desativação de concorrente já existem; esta fatia não
  os redesenha. Remoção permanente continua inexistente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST verificar, por propriedade, se a coleta de
  mercado está devida segundo a periodicidade configurada para aquela
  casa, e MUST executar o ciclo só quando a janela tiver vencido.
- **FR-002**: A periodicidade MUST ser lida da configuração da propriedade
  (`periodicidade_coleta_mercado`), em horas. MUST NOT ser constante de
  regra de negócio. Propriedade nova MUST nascer com a chave já
  configurada. Ausência, vazio, zero, valor negativo ou não numérico MUST
  impedir a coleta daquela propriedade de forma explícita, sem assumir
  intervalo embutido.
- **FR-003**: O ciclo devido MUST consultar somente as fontes **ativas**
  daquela propriedade (o conjunto já definido pela fatia de cadastro).
  Fonte desativada MUST NOT ser visitada e MUST NOT gerar registro novo.
- **FR-004**: Cada ciclo devido de uma fonte ativa MUST **inserir** um
  registro novo de coleta, com a data e a hora da tentativa. MUST NOT
  atualizar, apagar ou redatar registro anterior da mesma fonte.
- **FR-005**: Coleta bem-sucedida MUST registrar indicação de sucesso e ao
  menos um entre: preço público encontrado ou nota agregada encontrada.
- **FR-006**: Coleta que não obtenha preço público nem nota agregada, que
  seja recusada por diretiva, que exija autenticação, que esteja
  indisponível ou cujo conteúdo não seja público MUST registrar indicação
  de falha, com a data da tentativa, **sem** apresentar preço ou nota como
  valor encontrado.
- **FR-007**: Falha MUST NOT apagar, zerar nem substituir o registro
  anterior. O dado antigo MUST permanecer com a data antiga.
- **FR-008**: Preço público zero MUST ser gravado como sucesso com valor
  zero, distinguível de falha e de campo vazio.
- **FR-009**: Antes de recolher o conteúdo, o coletor MUST ler as
  diretivas de acesso **publicadas pela fonte**. Se a diretiva proibir a
  coleta automatizada daquele endereço, ou se a diretiva estiver ausente
  ou ilegível a ponto de não autorizar, o coletor MUST NOT recolher o
  conteúdo e MUST registrar falha.
- **FR-010**: O coletor MUST identificar-se de forma honesta e
  reconhecível como o coletor desta casa em toda visita (diretiva e
  conteúdo). MUST NOT imitar navegador de pessoa física.
- **FR-011**: O coletor MUST consultar somente o que a fonte exibe sem
  autenticação. MUST NOT enviar credencial, MUST NOT contornar login,
  captcha ou bloqueio.
- **FR-012**: O coletor MUST persistir somente preço público e nota
  agregada, além da data e do desfecho. MUST NOT armazenar nome,
  identificador, foto ou texto de avaliador individual, nem o texto
  integral da página da fonte.
- **FR-013**: O coletor MUST visitar no máximo uma vez cada fonte ativa
  por ciclo devido. Visitas do mesmo ciclo MUST ser em sequência, não em
  rajada simultânea contra o mesmo anfitrião. O objetivo é acompanhar
  tarifa, não espelhar o site.
- **FR-014**: Concorrente nunca coletado MUST estar devido na primeira
  verificação em que a propriedade tenha periodicidade válida.
- **FR-015**: Toda leitura e toda escrita de coleta MUST considerar o
  hotel dono do concorrente. Coleta de um hotel MUST NOT ser visível nem
  gravada no ciclo de outro.
- **FR-016**: Duas verificações coincidentes sobre o mesmo concorrente
  devido MUST produzir um único registro daquela janela, não dois ciclos
  contemporâneos.
- **FR-017**: Esta fatia MUST NOT enviar mensagem ao hóspede, MUST NOT
  alterar tarifa da casa, MUST NOT consultar o sistema de gestão do hotel
  e MUST NOT montar o painel de mercado (consulta com histórico, variação
  e sinal de dado velho pertence à fatia seguinte).
- **FR-018**: Esta fatia MUST NOT oferecer, no painel, disparo manual de
  coleta. A superfície de uso é a verificação periódica (a mesma que os
  testes exercitam).
- **FR-019**: Logs MUST registrar identificador do concorrente, hotel e
  desfecho da tentativa. MUST NOT registrar o texto da página da fonte,
  texto de avaliador nem conteúdo de mensagem de hóspede.
- **FR-020**: O comportamento desta fatia MUST ser verificável sem visitar
  fonte real de terceiro: as fontes, as diretivas e os desfechos de rede
  MUST poder ser simulados. Dependência de site alheio no ar MUST NOT
  ser necessária para demonstrar o requisito.
- **FR-021**: Hotel sem fonte ativa MUST concluir a verificação sem erro
  e sem registro de coleta.
- **FR-022**: Mudança da periodicidade MUST valer a partir da verificação
  seguinte. MUST NOT disparar série retrospectiva para preencher lacunas.

### Key Entities

- **Concorrente ativo**: ficha já cadastrada, ainda marcada para
  acompanhamento. Só este conjunto é visitado. Inativo permanece no
  cadastro e fora do ciclo.
- **Fonte pública de consulta**: endereço da web informado pela gestão,
  onde preço e nota agregada aparecem sem login. Nesta fatia a fonte é
  visitada, sob as regras éticas abaixo.
- **Diretiva de acesso publicada**: instrução que a própria fonte publica
  para dizer o que um coletor automatizado pode ou não acessar. É lida
  antes do conteúdo. Ausência ou texto ilegível não vale como autorização.
- **Coleta de mercado**: um registro da série temporal de um concorrente.
  Sempre tem data e indicação de sucesso ou falha. Em sucesso, traz preço
  público e/ou nota agregada. Em falha, não apresenta valor encontrado.
  Nunca substitui o registro anterior.
- **Periodicidade da coleta**: intervalo, em horas, configurado por
  propriedade, que define quando a próxima visita às fontes ativas
  daquela casa está devida.
- **Nota agregada**: número público de reputação da fonte (escala de zero
  a cinco). Não é comentário, não é avaliador individual, não é média
  inventada pelo sistema a partir de textos.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos ciclos devidos com fonte ativa e conteúdo
  público permitido, nasce exatamente 1 registro novo daquele concorrente,
  com data e indicação de sucesso, contendo o preço e/ou a nota agregada
  encontrados.
- **SC-002**: Em 100% dos ciclos seguintes sobre o mesmo concorrente, o
  registro anterior permanece com os mesmos valores e a mesma data (0
  sobrescritas).
- **SC-003**: Em 100% das tentativas em que a fonte não rende dado público,
  a diretiva recusa, a fonte exige login ou está indisponível, nasce 1
  registro de falha com data e 0 valores apresentados como encontrados; o
  sucesso anterior, se existir, permanece intacto.
- **SC-004**: Em 100% das coletas com preço público zero, o registro é
  sucesso com zero — 0 desses casos são gravados como falha.
- **SC-005**: Em 100% das fontes desativadas, há 0 visitas e 0 registros
  novos no ciclo.
- **SC-006**: Em 100% das propriedades com periodicidade ainda dentro da
  janela, há 0 visitas novas às fontes já coletadas nessa janela.
- **SC-007**: Alterar a periodicidade muda o desfecho na verificação
  seguinte sem mudança de regra. Ausência ou valor inválido da chave
  produz 0 coletas naquela propriedade e 0 intervalos inventados.
- **SC-008**: Em verificação com dois hotéis, 0% das fontes e 0% dos
  registros de um aparecem no ciclo do outro.
- **SC-009**: Em 100% das fontes cuja diretiva proíbe a coleta daquele
  endereço, há 0 recolhimentos de conteúdo e 1 falha datada.
- **SC-010**: Em 100% das páginas que misturam nota agregada com dados de
  avaliador individual, 0 nomes, 0 textos e 0 identificadores de avaliador
  são persistidos.
- **SC-011**: Em 100% das visitas, a identidade do coletor é a desta casa
  e 0 visitas se passam por navegador de pessoa física.
- **SC-012**: Em 100% dos ciclos, 0 mensagens são enviadas a hóspede, 0
  tarifas da casa são alteradas e 0 telas de painel de mercado são
  exigidas para o desfecho existir.
- **SC-013**: O caminho fonte ativa devida → diretiva permite → sucesso
  datado → ciclo seguinte falha → sucesso antigo intacto é verificável de
  ponta a ponta sem fonte real de terceiro e sem o canal de mensagens.
- **SC-014**: Em 100% das execuções, logs operacionais não contêm o texto
  da página da fonte, texto de avaliador nem conteúdo de mensagem de
  hóspede.

## Assumptions

- A fatia F5.1 (cadastro de concorrentes e consulta de fontes ativas) está
  concluída. Esta fatia **não** recadastra concorrente; consome o conjunto
  de fontes ativas já definido. Inativo continua fora.
- A chave `periodicidade_coleta_mercado` já está prevista na configuração
  da propriedade. O bootstrap desta fatia passa a semeá-la. Valor padrão
  da instalação inicial: **24** (horas). É frequência baixa o bastante para
  acompanhar tarifa sem espelhar o site; a casa altera por configuração,
  sem tela nova neste MVP.
- Unidade da periodicidade é **hora**, no mesmo padrão das demais chaves
  operacionais da propriedade. Valor `24` = no máximo um ciclo por fonte
  a cada 24 horas, contado a partir da última tentativa daquela fonte
  (sucesso ou falha).
- Janela devida é por **fonte** (concorrente), com o intervalo da
  propriedade. Fonte nova, nunca coletada, está devida na próxima
  verificação válida. Não há carimbo único “última execução do hotel”
  que atrase fonte recém-incluída.
- Superfície de uso: a verificação periódica, no mesmo espírito das
  varreduras já existentes (silêncio, pulso, boas-vindas). Ligar o
  protótipo visual e o painel de mercado continuam fora do critério de
  pronto. A fatia F5.3 é quem mostra preço, data, variação e dado velho.
- Disparo manual “coletar agora” fica fora. Testes invocam a mesma
  verificação que o agendamento usa.
- **Termos de uso em linguagem jurídica** não são lidos automaticamente.
  Quem cadastra continua responsável por não incluir fonte com proibição
  contratual expressa (já registrado na F5.1). O que esta fatia recusa
  sozinha é o que as **diretivas de acesso publicadas** (o mecanismo que
  a fonte oferece a coletores) já proíbem, mais login, captcha e conteúdo
  não público. Ausência de diretiva compreensível não é licença.
- Preço coletado é o valor público em destaque para visitante anônimo, não
  o casamento com categoria de quarto da casa nem a enumeração da grade
  toda. Nota é agregada na escala de zero a cinco; escala diferente não é
  convertida por regra inventada.
- Coleta de mercado **não** usa o serviço de conversação por inteligência
  artificial para “interpretar” a página. Extrair preço e nota agregada do
  que a fonte publica é trabalho desta fatia; alucinar número a partir de
  texto livre violaria a honestidade do dado.
- A verificação desta fatia não visita site real. Rede, diretiva,
  permissão, login e o conteúdo relevante da página são simulados. É o
  mesmo princípio já usado para envio de mensagem e classificação:
  dependência de terceiro no ar não demonstra esta fatia.
- Esta fatia não muda tarifa da casa e não consulta o outro sistema do
  hotel. O OmniStay observa; a decisão de preço continua fora.
- A coleta roda em paralelo ao fluxo do hóspede. Não há recado, pulso,
  pesquisa nem chamado nascendo deste ciclo.
- Limitação honesta: fonte pode bloquear o coletor mesmo com diretiva
  permissiva; isso vira falha datada, não contorno. Cobertura completa de
  todas as centrais de reserva **não** é prometida.
