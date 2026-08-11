# Feature Specification: Esquema e Migrações

**Feature Branch**: `002-esquema-migracoes`

**Created**: 2026-08-11

**Status**: Draft

**Input**: User description: "O esquema de dados do sistema precisa ser criado de forma
versionada e reproduzível, de modo que qualquer ambiente possa ser levantado do zero até o
estado atual, e que mudanças futuras sejam aplicadas em ordem. O esquema de referência está
documentado em `04-schema.sql`." (backlog F0.2)

## Clarifications

### Session 2026-08-11

- Q: O `docs/04-schema.sql` deve ser o artefato que a migração executa, ou um documento paralelo
  mantido em acordo? → A: A migração executa o próprio arquivo de referência; documento e banco
  são o mesmo artefato.
- Q: (revisado no planejamento) A revisão inicial não pode ler o arquivo vivo, porque ele passa a
  descrever o esquema já alterado por migrações posteriores e a segunda revisão falharia. → A: A
  revisão inicial carrega uma cópia congelada do SQL, byte a byte idêntica ao documento no momento
  da criação; `docs/04-schema.sql` segue sendo o documento vivo do esquema atual, e o teste da
  FR-018 é o que impede a divergência — a duplicação deixa de ser risco porque quem confere é a
  máquina, não a disciplina.
- Q: Como se comprova que 100% das estruturas existem após a aplicação? → A: Teste automatizado
  que compara o inventário de estruturas do banco migrado com as nomeadas no documento de
  referência; além disso, um teste que extrai o esquema do banco migrado e falha se divergir do
  documento, protegendo também as migrações futuras.
- Q: O que acontece com os testes que exigem banco real quando não há PostgreSQL alcançável? →
  A: Pulam por padrão, mas um sinal explícito de ambiente exige a execução e faz o pulo virar
  falha.
- Q: A migração deve verificar a versão do servidor antes de aplicar? → A: Sim — verificar a
  versão mínima antes de aplicar qualquer coisa e abortar com mensagem explícita, com a versão
  mínima declarada em um único número (PostgreSQL 16).
- Q: O esquema nasce como uma migração só ou dividido por domínio? → A: Uma única migração cria
  o esquema inteiro, em uma transação.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Levantar um ambiente do zero (Priority: P1)

Como desenvolvedor ou responsável por implantação, quero levar um banco vazio até o estado
atual do esquema com uma única operação, para que qualquer ambiente — máquina nova,
ambiente de avaliação, reinstalação após falha — seja reproduzível sem passos manuais.

**Why this priority**: Sem isso, nenhuma funcionalidade posterior pode ser desenvolvida ou
testada. É o pré-requisito de toda a Fase 1 em diante.

**Independent Test**: Pode ser testado isoladamente apontando para um banco vazio, aplicando
a migração e verificando que as estruturas do esquema de referência existem.

**Acceptance Scenarios**:

1. **Given** um banco de dados vazio, **When** a migração é aplicada, **Then** todas as
   tabelas, restrições, índices, a trigger de transição e a visão de apoio descritas no
   esquema de referência passam a existir.
2. **Given** um banco já no estado atual, **When** a migração é aplicada novamente,
   **Then** nenhuma alteração é feita e nenhum erro é reportado.
3. **Given** um banco vazio, **When** a migração falha no meio da aplicação, **Then** o banco
   não fica em estado parcial.

---

### User Story 2 - O banco recusa dado inválido por conta própria (Priority: P1)

Como responsável pela integridade dos dados, quero que as regras de domínio, de ciclo de vida
e de unicidade sejam impostas pelo próprio banco, para que script de correção, importação ou
acesso direto não consigam corromper o histórico.

**Why this priority**: É a razão de o Artigo IX existir. Uma migração que cria apenas tabelas,
sem as garantias, entrega a estrutura e não a proteção — e o defeito só aparece quando o
histórico já foi corrompido.

**Independent Test**: Pode ser testado isoladamente tentando gravar valores inválidos
diretamente no banco migrado e verificando que cada tentativa é recusada.

**Acceptance Scenarios**:

1. **Given** o esquema aplicado, **When** se tenta gravar um valor fora do domínio permitido
   em um campo restrito, **Then** o banco recusa a operação.
2. **Given** uma reserva em determinado estado, **When** se tenta mudá-la para um estado que
   não é alcançável a partir do atual, **Then** o banco recusa a transição.
3. **Given** um evento de webhook já registrado, **When** se tenta registrar um segundo evento
   com o mesmo identificador externo, **Then** o banco recusa a segunda inserção.
4. **Given** uma reserva em determinado estado, **When** se faz uma transição de estado
   permitida, **Then** a operação é aceita.

---

### User Story 3 - Evoluir o esquema em ordem (Priority: P2)

Como desenvolvedor, quero que mudanças futuras de esquema sejam aplicadas em ordem
determinística e que o banco saiba em que versão está, para que ambientes em estágios
diferentes convirjam sem intervenção manual.

**Why this priority**: Só passa a valer a partir da segunda alteração de esquema. A entrega
inicial já precisa deixar o mecanismo pronto, mas o valor é diferido.

**Independent Test**: Pode ser testado isoladamente consultando a versão registrada no banco
antes e depois de aplicar a migração.

**Acceptance Scenarios**:

1. **Given** um banco migrado, **When** se consulta o estado de versionamento, **Then** a
   versão corrente é identificável.
2. **Given** um banco em uma versão anterior, **When** a migração é aplicada, **Then** apenas
   as mudanças ainda não aplicadas são executadas, na ordem definida.
3. **Given** uma migração futura que altera o esquema sem atualizar o documento de referência,
   **When** a verificação de conformidade roda sobre um banco limpo e migrado, **Then** a
   divergência é apontada e a verificação falha.

---

### Edge Cases

- O que acontece ao aplicar a migração em um banco que já está no estado atual? Nada muda e
  nenhum erro é reportado.
- O que acontece se a aplicação for interrompida no meio? O banco não fica parcialmente
  migrado.
- O que acontece se a suíte rodar sem banco alcançável? Os testes que dependem dele são pulados
  com motivo declarado — a menos que o ambiente exija a execução, caso em que a suíte falha, para
  que uma suíte verde sem banco nunca seja confundida com entrega verificada.
- O que acontece se o servidor de banco não atender à versão mínima exigida pelo esquema? A
  aplicação falha com mensagem explícita, sem deixar estrutura pela metade.
- O esquema de referência foi escrito sem execução real. Divergências entre o documento e o
  que o banco aceita são esperadas nesta fatia e precisam ser corrigidas no documento, não
  contornadas na migração.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE permitir levar um banco vazio ao estado atual do esquema por uma
  única operação, sem passos manuais.
- **FR-002**: A migração DEVE criar todas as tabelas descritas no esquema de referência.
- **FR-003**: A migração DEVE criar as restrições de domínio que limitam os valores aceitos
  nos campos de perfil, categoria, status, direção, intenção, sentimento, urgência, tipo e
  origem.
- **FR-004**: A migração DEVE criar as restrições de coerência entre campos, incluindo data de
  saída posterior à de entrada, valor de consumo não negativo e nota de avaliação dentro da
  faixa permitida.
- **FR-005**: A migração DEVE criar a validação de transição de estado da reserva no próprio
  banco, de modo que uma transição não prevista seja recusada independentemente da aplicação.
- **FR-006**: A migração DEVE criar a restrição de unicidade do identificador externo de
  evento de webhook, que é o mecanismo de idempotência do sistema.
- **FR-007**: A migração DEVE criar os índices e a visão de apoio descritos no esquema de
  referência.
- **FR-008**: O banco DEVE registrar em que versão de esquema se encontra.
- **FR-009**: Aplicar a migração em um banco já atualizado NÃO DEVE alterar nada nem reportar
  erro.
- **FR-010**: Uma falha durante a aplicação NÃO DEVE deixar o banco em estado parcial.
- **FR-011**: A configuração de acesso ao banco DEVE vir de variável de ambiente, e nenhum
  valor de conexão pode estar registrado em arquivo versionado.
- **FR-012**: DEVE existir teste automatizado que comprove a recusa de um valor fora do
  domínio permitido.
- **FR-013**: DEVE existir teste automatizado que comprove a recusa de uma transição de estado
  inválida de reserva.
- **FR-014**: DEVE existir teste automatizado que comprove a recusa da segunda inserção do
  mesmo identificador externo de evento de webhook.
- **FR-015**: Toda divergência encontrada entre o esquema de referência e o comportamento real
  do banco DEVE ser corrigida no documento de referência na mesma entrega.
- **FR-016**: A migração inicial DEVE aplicar o SQL do documento de referência tal como ele está
  no momento da criação da migração, sem que ninguém reescreva o esquema em outra forma de
  descrição. O acordo entre documento e banco NÃO pode depender de vigilância humana: é a
  verificação automática da FR-018 que o sustenta.
- **FR-017**: DEVE existir teste automatizado que compare o inventário de estruturas do banco
  migrado — tabelas, restrições, índices, trigger e visão — com as estruturas nomeadas no
  documento de referência, e que falhe quando alguma estiver ausente.
- **FR-018**: DEVE existir teste automatizado que, partindo de um banco limpo, aplique todas as
  migrações, extraia o esquema resultante e falhe se ele divergir do documento de referência.
  Este teste vale para toda migração futura, não só para a inicial.
- **FR-019**: Os testes que exigem banco real DEVEM ser pulados, com motivo declarado, quando
  não houver banco alcançável; e DEVEM falhar em vez de pular quando o ambiente sinalizar
  explicitamente que a execução contra banco real é exigida.
- **FR-020**: A aplicação da migração DEVE verificar a versão do servidor de banco antes de
  executar qualquer comando de esquema e DEVE abortar com mensagem explícita, sem criar nenhuma
  estrutura, quando a versão for anterior à mínima exigida.
- **FR-021**: A versão mínima exigida DEVE ser PostgreSQL 16, declarada em um único lugar e
  refletida no documento de referência, que hoje declara "PostgreSQL 14+".
- **FR-022**: O esquema inicial DEVE ser criado por uma única migração, aplicada em uma
  transação, de modo que a atomicidade exigida pela FR-010 seja garantida pelo próprio banco.

### Key Entities

O esquema cobre seis domínios. Os detalhes de campos e restrições estão no documento de
referência; aqui fica apenas o que cada entidade representa.

- **Hotel**: propriedade hoteleira. Raiz do particionamento por propriedade.
- **Usuário**: funcionário com perfil de recepção, operação ou gestão.
- **Parâmetro do hotel**: configuração operacional por propriedade, chave e valor.
- **Item de catálogo**: fato da propriedade que o atendimento automatizado pode afirmar.
- **Hóspede**: ficha cadastral, com os campos digitados pelo hóspede.
- **Reserva**: registro com telefone e datas, com ciclo de vida controlado por estados.
- **Reserva–Hóspede**: associação entre uma reserva e seus hóspedes, com indicação de titular.
- **Consentimento**: histórico de concessões e revogações, uma linha por evento.
- **Mensagem**: troca com o hóspede, com classificação e estado de envio.
- **Evento de webhook**: registro bruto da notificação recebida, com identificador externo
  único.
- **Solicitação**: entidade única para reclamação, serviço operacional e consumo.
- **Consumo**: especialização de solicitação, com valor praticado e estado de lançamento.
- **Avaliação**: resposta do hóspede ao pulso do segundo dia ou à pesquisa de saída.
- **Concorrente**: propriedade acompanhada pela inteligência de mercado.
- **Coleta de mercado**: série temporal de preço e avaliação de um concorrente.
- **Fila do dia**: visão de apoio que alimenta a tela inicial do turno da recepção.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um banco vazio chega ao estado atual do esquema em uma única operação, sem
  nenhum passo manual.
- **SC-002**: 100% das tabelas, restrições, índices, trigger e visão descritos no documento de
  referência existem no banco após a aplicação, comprovado por teste automatizado que compara o
  inventário do banco com o documento.
- **SC-003**: As três garantias exigidas — domínio de valor, transição de estado e unicidade de
  evento — possuem teste automatizado que falha na ausência da migração e passa após ela.
- **SC-004**: Aplicar a migração duas vezes seguidas produz o mesmo resultado da primeira
  aplicação, sem erro.
- **SC-005**: Não resta nenhuma diferença entre o documento de referência e o esquema
  efetivamente aplicado, e a ausência de diferença é verificada automaticamente a cada execução
  da suíte — a partir de banco limpo, migrado e com o esquema extraído para comparação.

## Assumptions

- A migração cria apenas estrutura. Nenhum dado é inserido: cadastro de propriedade, usuários
  e parâmetros operacionais são objeto de fatias posteriores.
- Os testes das três garantias operam contra um banco real, porque restrição, trigger e
  unicidade são justamente o que não se consegue verificar com dependência falsa.
- O documento `docs/04-schema.sql` descreve sempre o esquema atual completo e é a fonte de onde
  o SQL da migração inicial sai. A migração carrega uma cópia congelada dele, porque uma revisão
  que lesse o arquivo vivo passaria a criar o esquema já alterado por revisões posteriores.
  Ninguém reescreve o esquema em outra forma de descrição, e a verificação automática da FR-018
  é o que mantém documento e banco em acordo ao longo do tempo.
- O documento de referência declara "PostgreSQL 14+", anterior à versão adotada pelo projeto. A
  entrega fixa a versão mínima em 16, verifica-a antes de aplicar e corrige o documento.
- Reversão de uma migração é desejável mas não é critério de aceite desta fatia, já que a
  primeira migração parte de banco vazio e a reversão equivale a descartar o banco.
- O expurgo por retenção citado nos comentários do esquema é uma fatia própria (F6.1) e não
  entra aqui: esta fatia cria a estrutura, não o comportamento de retenção.
