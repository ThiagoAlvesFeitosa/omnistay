---

description: "Task list for feature implementation"
---

# Tasks: Autenticação e Perfis

**Input**: Design documents from `/specs/003-autenticacao-perfis/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. O Artigo XII não admite código de produção sem teste que falhe antes, e a
spec nomeia o comportamento a verificar em praticamente todos os requisitos.

**Organization**: Tarefas agrupadas por história de usuário, na ordem de prioridade da spec.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US6)

## Como ver os testes falharem nesta fatia

Três situações merecem cuidado, senão o ciclo vira formalidade:

**A migração.** O teste de conformidade construído na F0.2 é o "ver falhar" da tabela nova, e vem de
graça: acrescentar o bloco de `sessao` ao `docs/04-schema.sql` **antes** de criar a revisão deixa a
suíte vermelha, porque o banco migrado passa a divergir do documento. A revisão é o que a devolve ao
verde. Fazer na ordem inversa é o que faz o teste passar de primeira sem provar nada.

**As garantias do banco.** `UNIQUE` e `CHECK` não são código nosso. Como na fatia anterior, cada
teste de garantia roda **duas vezes**: contra banco descartável sem a revisão `0002`, onde precisa
falhar, e contra o banco com ela, onde precisa passar.

**A autorização de recursos que ainda não existem.** As FR-018 e FR-019 falam de hóspede e de dados
de domínio, cujas rotas chegam na F1.1 e adiante. Elas são entregues como política pura testada por
unidade e como varredura de rotas — ver [research.md](./research.md) seção 8. Nenhuma tarefa aqui
cria rota de hóspede, reserva ou solicitação: seria implementar fatia fora de ordem.

---

## Phase 1: Setup

**Purpose**: Configuração e lugar para o código novo

- [X] T001 [P] Registrar `SENHA_ITERACOES` e `BOOTSTRAP_SENHA_INICIAL` em `.env.example`, **sem
      valor**, cada uma com comentário dizendo para que serve — a primeira como parâmetro de custo
      da derivação, a segunda como senha do gestor inicial, usada uma única vez
- [X] T002 [P] Acrescentar `senha_iteracoes: int = 600_000` a `app/config.py`, com comentário
      registrando que é parâmetro de segurança de plataforma e não de propriedade, e que a suíte de
      testes o reduz para manter o ciclo rápido ([research.md](./research.md) seção 1)
- [X] T003 [P] Criar os pacotes vazios `app/modulos/acesso/__init__.py` e
      `app/modulos/propriedade/__init__.py`
- [X] T004 [P] Criar os pacotes de teste `testes/unitarios/comum/__init__.py`,
      `testes/unitarios/modulos/acesso/__init__.py` e
      `testes/unitarios/modulos/propriedade/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: A tabela de sessão, as primitivas de segurança e o aparato de teste do qual todas as
histórias dependem

**⚠️ CRÍTICO**: nenhuma história começa antes desta fase. T009 precisa vir antes de T011 e T012 —
congelar a cópia a partir de um documento ainda não atualizado grava o erro para sempre.

- [X] T005 Escrever o teste da derivação de senha em `testes/unitarios/comum/test_seguranca.py`: a
      mesma senha derivada duas vezes produz valores diferentes (sal por usuário); a conferência
      aceita a senha certa e recusa a errada; o valor gravado carrega algoritmo, iterações e sal; e
      um valor gravado com número menor de iterações continua conferindo, porque a verificação usa o
      número da própria linha. Rodar e ver falhar (FR-002)
- [X] T006 Escrever o teste do token de sessão em `testes/unitarios/comum/test_seguranca.py`: dois
      tokens gerados nunca coincidem; o hash é estável para o mesmo token; e o token **não é
      recuperável** a partir do hash — o teste registra a propriedade que a FR-007 exige. Rodar e
      ver falhar
- [X] T007 Implementar `app/comum/seguranca.py` com derivação PBKDF2-HMAC-SHA256, conferência em
      tempo constante com `hmac.compare_digest`, geração de token opaco com `secrets.token_urlsafe`
      e hash SHA-256 do token, até T005 e T006 passarem ([research.md](./research.md) seções 1 e 2)
- [X] T008 [P] Criar `app/comum/relogio.py` com `agora()` devolvendo instante em UTC. Sem teste
      próprio: é uma linha, e o que ela entrega — ser substituível — é exercitado pelos testes de
      expiração da US4
- [X] T009 Acrescentar o bloco `CREATE TABLE sessao`, seus comentários e o índice parcial a
      `docs/04-schema.sql`, na seção 1, depois de `usuario`, exatamente como está em
      [data-model.md](./data-model.md). Rodar a suíte e **ver o teste de conformidade da F0.2 ficar
      vermelho** — é o "ver falhar" da migração (FR-031)
- [X] T010 Acrescentar as três chaves de duração de sessão ao `COMMENT ON TABLE parametro_hotel` em
      `docs/04-schema.sql`, junto das chaves já previstas
- [X] T011 Congelar a cópia do bloco em `alembic/versions/sql/0002_sessao.sql`, idêntica ao que
      entrou no documento, incluindo os comentários e o índice
- [X] T012 Criar a revisão `alembic/versions/0002_sessao.py`, com `down_revision =
      "0001_esquema_inicial"`, executando o arquivo companheiro por cursor cru como faz a revisão
      inicial, e com `downgrade` real (`DROP TABLE sessao`) — aqui a reversão é exata e não equivale
      a descartar o banco. Rodar até o teste de conformidade voltar ao verde (FR-031)
- [X] T013 Escrever o teste das garantias da tabela em
      `testes/integracao/test_garantias_da_sessao.py`: `token_hash` repetido é recusado;
      `expira_em` anterior ou igual a `criada_em` é recusado; `revogada_em` anterior a `criada_em` é
      recusado; e sessão apontando para usuário inexistente é recusada pela chave estrangeira.
      Exercitar contra banco descartável **sem** a revisão `0002`, onde falha, e contra o banco com
      ela, onde passa (Artigo IX)
- [X] T014 Criar `testes/suporte/ambiente_de_acesso.py`: fixture que entrega banco descartável já
      migrado, cria duas propriedades, um usuário de cada perfil em cada uma, e semeia os parâmetros
      de duração — é o cenário de que quase todo teste de integração desta fatia precisa, inclusive
      os de isolamento entre propriedades
- [X] T015 Ajustar `testes/conftest.py` para que o cliente de teste use `base_url="https://
      testserver"`. Sem isso, o cookie marcado como `Secure` é aceito e nunca reenviado, e todo teste
      autenticado falharia por um motivo que não é o do teste ([research.md](./research.md) seção 3)
- [X] T016 Acrescentar a `testes/conftest.py` a redução de `SENHA_ITERACOES` para a suíte, no mesmo
      lugar onde as demais variáveis de ambiente de teste são definidas, com comentário explicando
      que o custo real vive na configuração de produção

**Checkpoint**: a tabela existe, o documento e o banco estão em acordo, e há como montar um cenário
de teste. As histórias podem começar.

---

## Phase 3: User Story 1 - Dar o primeiro acesso a uma instalação nova (Priority: P1) 🎯 MVP

**Goal**: Um sistema recém-migrado passa a ter propriedade, gestor e parâmetros, por um comando.

**Independent Test**: sobre banco apenas migrado, executar o comando e verificar que a propriedade,
o usuário de gestão e as três chaves de duração passaram a existir, com a senha gravada derivada.

### Tests for User Story 1 ⚠️

> Escrever primeiro. Rodar. Ver falhar — não existe nem o serviço nem o comando.

- [X] T017 [P] [US1] Teste unitário do serviço de criação inicial em
      `testes/unitarios/modulos/propriedade/test_bootstrap.py`, com repositórios falsos: cria
      propriedade, usuário de perfil `gestor` e as três chaves de duração com os valores padrão de
      [data-model.md](./data-model.md) (FR-025, FR-028)
- [X] T018 [P] [US1] Teste unitário da recusa em `testes/unitarios/modulos/propriedade/
      test_bootstrap.py`: havendo propriedade cadastrada, nada é criado e a recusa declara o motivo
      (FR-026)
- [X] T019 [P] [US1] Teste de integração em `testes/integracao/test_bootstrap.py`: contra banco
      migrado, o comando grava a senha **derivada** — o valor da coluna não contém a senha em claro,
      e a conferência aceita a senha usada (FR-002, FR-027)
- [X] T020 [P] [US1] Teste de atomicidade em `testes/integracao/test_bootstrap.py`: forçando falha
      depois da criação da propriedade, não sobra propriedade, usuário nem parâmetro — a verificação
      é o banco vazio, não a mensagem de erro (FR-029)
- [X] T021 [P] [US1] Teste em `testes/integracao/test_bootstrap.py` de que a senha inicial **não
      aparece** na saída do comando nem em nenhum registro de log emitido durante a execução (FR-027,
      FR-030)

### Implementation for User Story 1

- [X] T022 [US1] Criar `app/comum/transacao.py` com um gerenciador de contexto sobre
      `engine.begin()`, para que uma sequência de escritas seja atômica sem que cada repositório
      abra conexão por conta própria ([research.md](./research.md) seção 7)
- [X] T023 [US1] Criar `app/modulos/propriedade/repository.py` com inserção de propriedade, inserção
      de parâmetro e verificação de existência de propriedade, todas recebendo a conexão como
      primeiro parâmetro
- [X] T024 [US1] Criar `app/modulos/acesso/repository.py` com inserção de usuário e busca por
      e-mail, recebendo a conexão. Nenhuma outra função ainda — as demais chegam com as histórias
      que precisam delas
- [X] T025 [US1] Criar `app/modulos/acesso/service.py` com a criação de usuário, que deriva a senha
      antes de chamar o repositório. O módulo `propriedade` não escreve em `usuario`: chama este
      serviço, como manda a regra de fronteira do `AGENTS.md`
- [X] T026 [US1] Criar `app/modulos/propriedade/service.py` com a criação inicial da propriedade,
      coordenando as três escritas dentro de uma transação, até T017, T018 e T020 passarem
- [X] T027 [US1] Criar `app/bootstrap.py` como entrada de linha de comando com `argparse`: nome e
      telefone da propriedade, nome e e-mail do gestor; senha lida de `BOOTSTRAP_SENHA_INICIAL` ou,
      na ausência, de `getpass` sem eco; falha explícita quando não há nenhuma das duas, **sem senha
      padrão**; código de saída diferente de zero na recusa (FR-025, FR-027)

**Checkpoint**: uma instalação nova tem por onde começar. É o desbloqueio do impasse registrado no
estado do projeto.

---

## Phase 4: User Story 2 - Entrar no painel e ser barrado sem sessão válida (Priority: P1)

**Goal**: Autenticar cria sessão em cookie; recurso protegido recusa quem não a tem.

**Independent Test**: autenticar com a credencial criada pelo bootstrap, alcançar
`GET /sessoes/atual`, e verificar que a mesma chamada sem cookie é recusada.

### Tests for User Story 2 ⚠️

- [X] T028 [P] [US2] Teste unitário do serviço de autenticação em
      `testes/unitarios/modulos/acesso/test_service_de_sessao.py`, com repositórios falsos e relógio
      fixo: credencial correta cria sessão com `expira_em` igual a agora mais a duração do perfil, e
      grava o hash do token, nunca o token (FR-005)
- [X] T029 [P] [US2] Teste unitário das recusas no mesmo arquivo: senha errada, usuário inativo e
      e-mail inexistente recusam. No caso do e-mail inexistente, verificar que a derivação **ainda
      assim é executada** — é o que impede distinguir os casos pelo tempo (FR-003, FR-004)
- [X] T030 [P] [US2] Teste de integração da autenticação em `testes/integracao/test_autenticacao.py`:
      `POST /sessoes` responde 201 e define o cookie `omnistay_sessao` com `HttpOnly`, `Secure`,
      `SameSite=Strict`, `Path=/` e `Max-Age` coerente com `expira_em`. Verificar atributo por
      atributo, conforme [contracts/api-de-acesso.md](./contracts/api-de-acesso.md) (FR-006)
- [X] T031 [P] [US2] Teste em `testes/integracao/test_autenticacao.py` de que o token **não aparece**
      no corpo da resposta de autenticação, em nenhum campo (FR-006, FR-007)
- [X] T032 [P] [US2] Teste em `testes/integracao/test_autenticacao.py` de que as recusas são
      indistinguíveis: e-mail inexistente, senha errada e usuário desativado produzem o mesmo status
      e o mesmo corpo, byte a byte (FR-003)
- [X] T033 [P] [US2] Teste do recurso protegido em `testes/integracao/test_autenticacao.py`:
      `GET /sessoes/atual` responde 200 com sessão válida e 401 sem cookie, com cookie forjado e com
      cookie de sessão inexistente — sempre a mesma mensagem (FR-008)
- [X] T034 [P] [US2] Teste do encerramento em `testes/integracao/test_autenticacao.py`:
      `DELETE /sessoes/atual` responde 204, remove o cookie, marca a sessão como revogada e a
      requisição seguinte com o mesmo cookie recebe 401. Chamar sem sessão também responde 204
      (FR-009)
- [X] T035 [P] [US2] Teste de log em `testes/integracao/test_autenticacao.py`: capturando os
      registros emitidos durante autenticação bem-sucedida e malsucedida, nenhum contém a senha, o
      token ou o cabeçalho de cookie; e o registro existente traz identificador e resultado (FR-030)

### Implementation for User Story 2

- [X] T036 [US2] Criar `app/modulos/acesso/schema.py` com os contratos de entrada e saída de
      autenticação e de sessão atual, conforme [contracts/api-de-acesso.md](./contracts/api-de-acesso.md).
      Nenhum campo de senha ou token nas saídas
- [X] T037 [US2] Acrescentar a `app/modulos/propriedade/repository.py` e a
      `app/modulos/propriedade/service.py` a leitura da duração de sessão por perfil, com **falha
      explícita** quando a chave não existir para a propriedade — assumir um prazo padrão seria o
      número mágico que o Artigo XIII proíbe (FR-010)
- [X] T038 [US2] Acrescentar a `app/modulos/acesso/repository.py` a inserção de sessão, a busca por
      hash do token trazendo usuário e perfil, e a revogação de uma sessão
- [X] T039 [US2] Acrescentar a `app/modulos/acesso/service.py` a autenticação e o encerramento, com
      relógio injetado, derivação contra hash de referência quando o e-mail não existe, e cálculo da
      expiração a partir da duração do perfil, até T028 e T029 passarem
- [X] T040 [US2] Criar `app/modulos/acesso/dependencias.py` com a dependência que lê o cookie,
      resolve a sessão válida — não revogada, não expirada, de usuário ativo — e devolve usuário e
      perfil; 401 idêntico em todos os casos de falha
- [X] T041 [US2] Acrescentar a `app/comum/transacao.py` a dependência de transação por requisição, e
      usá-la nas rotas que escrevem
- [X] T042 [US2] Criar `app/modulos/acesso/router.py` com `POST /sessoes`, `DELETE /sessoes/atual` e
      `GET /sessoes/atual`, e registrá-lo em `app/main.py`, até T030 a T035 passarem

**Checkpoint**: o sistema tem acesso controlado. Nenhuma fatia posterior pode expor dado de hóspede
antes disto existir.

---

## Phase 5: User Story 3 - Cada perfil alcança apenas o que lhe cabe (Priority: P1)

**Goal**: A política de perfis existe, está ligada às rotas e protege também as rotas futuras.

**Independent Test**: verificar a matriz por unidade e, pela varredura, que nenhuma rota fora da
lista pública dispensa sessão.

> As recusas por perfil em rotas concretas são verificadas nas histórias que criam essas rotas —
> listagem e revogação na US5, cadastro de usuário na US6. Aqui entra o mecanismo e a garantia que
> vale para as fatias seguintes.

### Tests for User Story 3 ⚠️

- [X] T043 [P] [US3] Teste unitário da matriz completa em
      `testes/unitarios/modulos/acesso/test_politica.py`: as catorze operações de
      [contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md) contra os três
      perfis, incluindo `ler_dado_cadastral_de_hospede` recusada ao perfil operacional e
      `alterar_reserva` recusada à gestão. Ver falhar (FR-018, FR-019)
- [X] T044 [P] [US3] Teste em `testes/unitarios/modulos/acesso/test_politica.py` de que operação
      desconhecida é **recusada**, não permitida por omissão — erro de digitação no nome de uma
      operação não pode abrir porta
- [X] T045 [P] [US3] Teste de varredura em `testes/integracao/test_rotas_protegidas.py`: percorrer
      todas as rotas registradas na aplicação e falhar se alguma fora da lista pública fechada —
      `GET /health`, `POST /sessoes` e `DELETE /sessoes/atual` — não exigir sessão. A mensagem de
      falha nomeia a rota desprotegida (FR-008, SC-002)

### Implementation for User Story 3

- [X] T046 [US3] Criar `app/modulos/acesso/politica.py` com a matriz de perfil por operação como
      decisão pura, recusando operação desconhecida, até T043 e T044 passarem
- [X] T047 [US3] Acrescentar a `app/modulos/acesso/dependencias.py` a exigência de operação, que
      devolve 403 para perfil sem permissão — distinto do 401 de sessão ausente, porque o cliente
      precisa saber se reautentica ou se aquele caminho não é dele
- [X] T048 [US3] Aplicar a exigência de operação às rotas existentes e ajustar o que a varredura
      apontar, até T045 passar

**Checkpoint**: a política existe e não depende de ninguém lembrar de aplicá-la.

---

## Phase 6: User Story 4 - A equipe operacional não reautentica a cada chamado (Priority: P2)

**Goal**: Cada perfil tem seu prazo, vindo da configuração da propriedade, e prazo vencido não vale.

**Independent Test**: configurar durações distintas por perfil e verificar que a sessão de operação
dura além das demais, e que sessão vencida é recusada.

### Tests for User Story 4 ⚠️

- [X] T049 [P] [US4] Teste unitário em `testes/unitarios/modulos/acesso/test_service_de_sessao.py`:
      com relógio injetado, sessões dos três perfis nascem com expirações diferentes, cada uma
      conforme a chave da propriedade (FR-010, FR-011)
- [X] T050 [P] [US4] Teste unitário no mesmo arquivo: alterar a duração configurada **não** muda a
      expiração de sessão já criada — o prazo é fixado na criação (FR-005)
- [X] T051 [P] [US4] Teste unitário no mesmo arquivo: faltando a chave de duração do perfil, a
      autenticação falha com erro explícito, em vez de assumir um prazo (Artigo XIII)
- [X] T052 [P] [US4] Teste de integração em `testes/integracao/test_sessoes.py`: sessão com
      `expira_em` no passado recebe 401 mesmo apresentando o cookie, e o `Max-Age` do cookie de um
      usuário de operação reflete a duração longa configurada (FR-012)

### Implementation for User Story 4

- [X] T053 [US4] Ajustar `app/modulos/acesso/service.py` e `app/modulos/acesso/dependencias.py` para
      que a expiração seja lida por perfil, verificada em toda requisição e refletida no `Max-Age`,
      até T049 a T052 passarem

**Checkpoint**: o profissional de manutenção não digita senha a cada chamado, e ninguém tem prazo
fixado em código.

---

## Phase 7: User Story 5 - Cortar o acesso de um dispositivo perdido (Priority: P2)

**Goal**: A recepção lista as sessões da propriedade e revoga uma delas, com efeito imediato.

**Independent Test**: com duas sessões do mesmo usuário, revogar uma e verificar que só ela cai.

### Tests for User Story 5 ⚠️

- [X] T054 [P] [US5] Teste de listagem em `testes/integracao/test_sessoes.py`: `GET /sessoes` com
      sessão de recepção responde 200 com usuário, perfil, dispositivo e prazos — e **nenhum token
      nem hash de token** em qualquer campo (FR-013)
- [X] T055 [P] [US5] Teste de recusa por perfil em `testes/integracao/test_sessoes.py`: perfis de
      operação e de gestão recebem 403 ao listar e ao revogar (FR-021)
- [X] T056 [P] [US5] Teste de revogação em `testes/integracao/test_sessoes.py`: `DELETE
      /sessoes/{id}` responde 204, a sessão alvo recebe 401 **na requisição imediatamente seguinte**,
      e a outra sessão do mesmo usuário continua respondendo 200 (FR-014, FR-016)
- [X] T057 [P] [US5] Teste de idempotência em `testes/integracao/test_sessoes.py`: revogar sessão já
      revogada ou já expirada responde 204, sem erro e sem efeito adicional (FR-015)
- [X] T058 [P] [US5] Teste de isolamento em `testes/integracao/test_sessoes.py`: revogar sessão de
      usuário de outra propriedade responde 404 — o mesmo que sessão inexistente, para não revelar
      que existe em outro hotel (FR-024)

### Implementation for User Story 5

- [X] T059 [US5] Acrescentar a `app/modulos/acesso/repository.py` a listagem de sessões ativas por
      propriedade, com junção em `usuario`, e a revogação por identificador restrita à propriedade
      ([data-model.md](./data-model.md))
- [X] T060 [US5] Acrescentar a `app/modulos/acesso/service.py` a listagem e a revogação, com relógio
      injetado para decidir o que ainda está ativo
- [X] T061 [US5] Acrescentar a `app/modulos/acesso/schema.py` a saída da listagem, sem nenhum campo
      derivado do token
- [X] T062 [US5] Acrescentar a `app/modulos/acesso/router.py` as rotas `GET /sessoes` e `DELETE
      /sessoes/{id_sessao}`, exigindo a operação correspondente, até T054 a T058 passarem

**Checkpoint**: a contrapartida da sessão longa passa a ter mitigação real, disponível a quem está
de plantão.

---

## Phase 8: User Story 6 - Cadastrar e desligar funcionários (Priority: P2)

**Goal**: A gestão cria os usuários dos três perfis e desliga quem saiu, derrubando o acesso.

**Independent Test**: com sessão de gestão, criar um usuário de cada perfil e verificar que
autenticam; desativar um com sessão ativa e verificar que ele cai.

### Tests for User Story 6 ⚠️

- [X] T063 [P] [US6] Teste de criação em `testes/integracao/test_usuarios.py`: `POST /usuarios` com
      sessão de gestão responde 201, o usuário nasce na propriedade de quem o criou e passa a
      autenticar. A senha não volta no corpo, nem derivada (FR-020)
- [X] T064 [P] [US6] Teste de recusa por perfil em `testes/integracao/test_usuarios.py`: recepção e
      operação recebem 403 ao criar e ao desativar usuário (FR-020, FR-021)
- [X] T065 [P] [US6] Teste de validação em `testes/integracao/test_usuarios.py`: e-mail já cadastrado
      responde 409; perfil fora dos três previstos e senha com menos de doze caracteres respondem 422
      (FR-022, FR-023)
- [X] T066 [P] [US6] Teste de desativação em `testes/integracao/test_usuarios.py`: `DELETE
      /usuarios/{id}` responde 204, as duas sessões ativas do alvo passam a receber 401, e nova
      autenticação com a senha correta também é recusada (FR-004, FR-017)
- [X] T067 [P] [US6] Teste em `testes/integracao/test_usuarios.py` de que a gestão **não** pode
      desativar o próprio usuário autenticado, respondendo 409 — sem isso, o único gestor de uma
      propriedade pode deixá-la sem quem administre, recriando o impasse que o bootstrap resolve
- [X] T068 [P] [US6] Teste de isolamento em `testes/integracao/test_usuarios.py`: desativar usuário
      de outra propriedade responde 404 (FR-024)
- [X] T069 [P] [US6] Teste unitário em `testes/unitarios/modulos/acesso/test_service_de_usuario.py`:
      a desativação e a revogação das sessões acontecem na mesma transação — falha na segunda não
      deixa o usuário desativado com sessões vivas (FR-017)

### Implementation for User Story 6

- [X] T070 [US6] Acrescentar a `app/modulos/acesso/repository.py` a desativação de usuário e a
      revogação em massa das sessões de um usuário
- [X] T071 [US6] Acrescentar a `app/modulos/acesso/service.py` a validação de criação — perfil,
      tamanho mínimo de senha, e-mail único e propriedade herdada de quem cria — e a desativação
      transacional que derruba as sessões, até T069 passar
- [X] T072 [US6] Acrescentar a `app/modulos/acesso/schema.py` os contratos de criação e de saída de
      usuário, sem nenhum campo de senha na saída
- [X] T073 [US6] Acrescentar a `app/modulos/acesso/router.py` as rotas `POST /usuarios` e `DELETE
      /usuarios/{id_usuario}`, com os códigos de resposta do contrato, até T063 a T068 passarem

**Checkpoint**: as seis histórias estão completas e o acesso ao sistema acompanha o quadro de
pessoal.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Fechar as divergências documentais levantadas na Fase 0 e validar a entrega inteira

- [X] T074 [P] Acrescentar a entidade `sessao` a `docs/04-modelagem-de-dados.md`: no DER, no
      dicionário de dados com a classificação LGPD campo a campo, e o relacionamento com `usuario`
      ([research.md](./research.md) seção 13)
- [X] T075 [P] Atualizar `docs/05-arquitetura.md` §11.2 com o desenho da sessão — token opaco,
      cookie e revogação por linha — e as três chaves de duração
- [X] T076 [P] Remover `JWT_SECRET` da tabela de segredos de `docs/05-arquitetura.md` §11.3,
      registrando em uma linha por que ele deixou de existir: token opaco não tem o que assinar, e
      JWT não atenderia à revogação imediata que o próprio §11.2 exige
- [X] T077 [P] Remover `JWT_SECRET` da lista de segredos de `.cursor/rules/30-seguranca-lgpd.mdc` e
      acrescentar, na seção de senhas, que a derivação guarda algoritmo, iterações e sal na própria
      linha
- [X] T078 [P] Registrar em `AGENTS.md` o módulo `acesso` na lista de módulos e a decisão de o
      projeto não mapear tabelas em ORM, com a camada `model` permanecendo vazia
      ([research.md](./research.md) seção 12)
- [X] T079 Executar o [quickstart.md](./quickstart.md) inteiro, do Cenário 0 à verificação final,
      partindo de `docker compose down -v`, e corrigir qualquer passo que não confira
- [X] T080 Executar a suíte completa com `EXIGIR_POSTGRES=1` e confirmar verde sem nenhum teste
      pulado
- [X] T081 [P] Atualizar `docs/00-ESTADO-DO-PROJETO.md`: fatia F0.3 concluída, as decisões desta
      entrega na tabela de decisões de implementação, e a baixa das lacunas de bootstrap
- [X] T082 [P] Marcar a fatia F0.3 como concluída em `docs/backlog.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Fase 1)**: sem dependências
- **Foundational (Fase 2)**: depende do Setup e **bloqueia todas as histórias**
- **US1 (Fase 3)**: depende da Fase 2. É o MVP
- **US2 (Fase 4)**: depende da US1, que fornece a propriedade, o usuário e os parâmetros sem os quais
  não há o que autenticar
- **US3 (Fase 5)**: depende da US2, que fornece a primeira rota protegida a guardar
- **US4 (Fase 6)**: depende da US2
- **US5 (Fase 7)**: depende da US3, porque a recusa por perfil é o que restringe a revogação à
  recepção
- **US6 (Fase 8)**: depende da US3 pelo mesmo motivo, e da US5 para verificar que a desativação
  derruba as sessões pela via observável
- **Polish (Fase 9)**: depende de tudo

Esta fatia tem mais acoplamento entre histórias do que o ideal, e o motivo é honesto: autenticação,
autorização e sessão são um mecanismo só, fatiado por valor entregue e não por independência
técnica. A US1 é a única verdadeiramente isolada.

### Dependências internas relevantes

- T011 e T012 dependem de T009 e T010 — congelar antes de corrigir o documento grava o erro
- T013 depende de T012 para a metade verde do teste, e de banco sem migração para a vermelha
- Todos os testes de integração dependem de T014 e T015
- T028 a T035 dependem de T007, que fornece derivação e token
- T039 depende de T037: a expiração sai da duração configurada
- T045 é a única tarefa que precisa ser reexecutada a cada rota nova, em qualquer fatia futura
- T053 ajusta o que T039 e T040 criaram; não é código novo, é o prazo passando a valer
- T066 depende de T059 e T070

### Ordem dentro de cada história

Teste escrito, rodado e visto falhando antes da implementação, sem exceção. Nas garantias de banco,
"ver falhar" significa rodar contra banco sem a revisão `0002`.

### Parallel Opportunities

- T001 a T004 no Setup, todas em arquivos distintos
- T005 e T006 **não** são paralelas: mesmo arquivo
- T017 a T021 entre si; T028 a T035 entre si; T054 a T058 entre si; T063 a T069 entre si
- T074 a T078 no Polish, todas em arquivos distintos
- T009 e T010 **não** são paralelas: mesmo arquivo

---

## Parallel Example: User Story 2

```bash
# Escrever os testes da US2 juntos, antes de qualquer implementação:
Task: "Teste unitário do serviço de autenticação em testes/unitarios/modulos/acesso/test_service_de_sessao.py"
Task: "Teste de atributos do cookie em testes/integracao/test_autenticacao.py"
Task: "Teste de recusas indistinguíveis em testes/integracao/test_autenticacao.py"
Task: "Teste do recurso protegido em testes/integracao/test_autenticacao.py"
Task: "Teste de encerramento de sessão em testes/integracao/test_autenticacao.py"
Task: "Teste de log sem senha nem token em testes/integracao/test_autenticacao.py"
```

---

## Implementation Strategy

### MVP primeiro (US1 e US2)

1. Fase 1 e Fase 2 — a tabela existe e o documento continua em acordo com o banco
2. Fase 3: US1 — a instalação ganha propriedade e gestor
3. Fase 4: US2 — o gestor entra e o que não tem sessão é barrado
4. **PARAR E VALIDAR**: os cenários 1 a 5 do [quickstart.md](./quickstart.md) passam à mão
5. Seguir para US3, que é o que impede a F1.1 de nascer sem guarda

Diferente da fatia anterior, o MVP aqui são **duas** histórias: o bootstrap sozinho cria dados que
ninguém consegue usar, e a autenticação sozinha não tem credencial com que ser exercitada fora dos
testes.

### Entrega incremental

1. Setup e Foundational → tabela de sessão e primitivas de segurança
2. US1 → a instalação tem primeiro acesso
3. US2 → o painel tem acesso controlado (MVP)
4. US3 → a autorização existe e protege as fatias futuras
5. US4 → o prazo por perfil passa a valer
6. US5 → o dispositivo perdido é cortável
7. US6 → o quadro de pessoal entra no sistema

### Estratégia com um só desenvolvedor

As marcações [P] indicam ausência de dependência, e servem para escolher a próxima tarefa sem
esperar, não para trabalho simultâneo. A ordem numérica é uma sequência válida do começo ao fim.

---

## Notes

- Commit após cada tarefa ou grupo lógico, com mensagem descritiva
- Senha, token e cabeçalho de cookie nunca vão para log, inclusive em teste
- Toda consulta filtra pela propriedade do usuário da sessão, mesmo havendo um único hotel
- Nenhuma dependência nova entra no projeto nesta fatia
- Nenhuma tarefa aqui cria rota de hóspede, reserva ou solicitação: a autorização dessas rotas é
  entregue como política declarada e como varredura, e as rotas chegam nas suas fatias
