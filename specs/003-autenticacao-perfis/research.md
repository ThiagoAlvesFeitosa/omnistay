# Fase 0 — Pesquisa e decisões técnicas: Autenticação e Perfis

Cada seção registra a decisão, por que ela foi tomada e o que foi rejeitado. As divergências
documentais encontradas no caminho estão consolidadas na seção 13.

---

## 1. Algoritmo de derivação da senha

**Decisão**: PBKDF2-HMAC-SHA256 da biblioteca padrão (`hashlib.pbkdf2_hmac`), com sal aleatório por
usuário e 600.000 iterações. O valor guardado carrega o algoritmo, o número de iterações e o sal:

```
pbkdf2_sha256$<iteracoes>$<sal em base64>$<derivado em base64>
```

A comparação usa `hmac.compare_digest`, nunca `==`, coerente com o que a regra de segurança do
projeto já exige para a assinatura do webhook.

**Rationale**: o formato autodescritivo permite elevar as iterações depois sem invalidar as senhas
existentes — a verificação usa o número gravado na linha, e só a criação usa o número corrente.
600.000 é a recomendação vigente do OWASP para PBKDF2-HMAC-SHA256.

**Alternativas consideradas**:

- **bcrypt** e **Argon2id** são preferíveis em tese, e Argon2id é o primeiro da recomendação do
  OWASP. Foram rejeitados por um motivo concreto deste projeto, não por gosto: ambos são pacotes
  compilados, e a máquina roda **Python 3.14** — o risco de wheel ausente está registrado como
  decisão da F0.1. Trocar uma dependência que pode não instalar por uma função da biblioteca
  padrão é exatamente o que o Artigo XI pede.
- **SHA-256 puro** foi rejeitado: hash rápido sobre senha escolhida por humano é quebrável por
  força bruta, e a regra de segurança do projeto exige derivação lenta.

**Consequência**: o número de iterações vira configuração (`SENHA_ITERACOES`, padrão 600.000), o
que permite baixá-lo na suíte de testes. Sem isso, cada teste que autentica pagaria centenas de
milissegundos e o ciclo de TDD ficaria lento o bastante para ser evitado — que é o modo como
disciplina de teste morre.

---

## 2. Formato da sessão: token opaco, não JWT

**Decisão**: a sessão é um token aleatório opaco de 32 bytes (`secrets.token_urlsafe`), sem
significado próprio. O banco guarda apenas o **SHA-256 do token**; o valor original existe somente
no cookie do cliente.

**Rationale**: a FR-014 exige que a revogação valha na requisição seguinte, sem janela de
tolerância. Um JWT é verificável sem consultar o banco — é justamente essa a sua vantagem — e por
isso não é revogável: seria preciso manter uma lista de revogados consultada a cada requisição, o
que reintroduz a consulta ao banco e ainda soma a complexidade de assinar, verificar e versionar o
token. Com a linha de sessão já sendo consultada, o JWT não acrescenta nada.

Guardar o hash em vez do token atende à FR-007: vazamento da tabela de sessões não equivale a
vazamento de acesso.

**Por que SHA-256 aqui e derivação lenta na senha**: derivação lenta existe para tornar caro
adivinhar segredo de baixa entropia. Um token de 256 bits aleatórios não é adivinhável, e pagar
derivação lenta a cada requisição autenticada seria custo sem benefício.

**Divergência documental**: o Artefato 5 §11.3 e a regra `30-seguranca-lgpd.mdc` listam
`JWT_SECRET` como segredo para "assinatura das sessões do painel". Com esta decisão, esse segredo
deixa de existir. Ver seção 13.

---

## 3. Transporte: cookie, e o que isso implica

**Decisão**: cookie `omnistay_sessao` com `HttpOnly`, `Secure`, `SameSite=Strict` e `Path=/`,
definido pela API na criação da sessão e removido no encerramento. O prazo do cookie acompanha o
prazo da sessão gravada.

**Rationale**: `HttpOnly` tira o token do alcance de qualquer script na página, o que importa
especialmente porque a sessão do perfil operacional dura semanas. `SameSite=Strict` impede que
requisição partida de outro site carregue o cookie, o que cobre falsificação de requisição sem
precisar de token anti-CSRF — uma peça a menos, dado que API e painel compartilham origem.

**Duas consequências práticas, registradas para não virarem surpresa**:

1. **Nos testes**, um cookie `Secure` não é reenviado sobre `http://`. O cliente de teste do
   FastAPI precisa ser criado com `base_url="https://testserver"`. É a alternativa a criar um
   interruptor de configuração para desligar o `Secure` — interruptor que, esquecido ligado em
   produção, entrega a sessão em texto claro.
2. **No desenvolvimento do painel** (F1.1), servidor de desenvolvimento em outra porta continua
   sendo o mesmo site para efeito de `SameSite`, mas é outra origem para efeito de CORS: o painel
   precisará enviar credenciais explicitamente e a API precisará permiti-las, ou o servidor de
   desenvolvimento precisará repassar as chamadas. Decisão que pertence à F1.1; fica registrada
   aqui porque nasce desta escolha.

Em `http://localhost` os navegadores atuais tratam a origem como contexto seguro e aceitam cookie
`Secure`, então o desenvolvimento local não exige certificado.

---

## 4. Estrutura da tabela de sessão

**Decisão**: tabela `sessao` com usuário, hash do token, rótulo do dispositivo, instante de criação,
instante de expiração e instante de revogação. Detalhes em [data-model.md](./data-model.md).

**A sessão não guarda `id_hotel` próprio.** O hotel vem do usuário por junção.

**Rationale**: o Artigo XIV exige `id_hotel` nas tabelas de domínio e considerado em toda consulta.
A segunda metade é cumprida — listagem e revogação filtram pelo hotel do usuário. A primeira foi
deliberadamente não seguida à letra porque duplicar a coluna cria a possibilidade de uma sessão
apontar para hotel diferente do dono, e a única forma de o banco impedir isso seria chave
estrangeira composta, que exigiria acrescentar uma restrição de unicidade à tabela `usuario` já
existente. A junção entrega a mesma garantia sem estrutura nova e sem estado inconsistente
possível. Registrado como ponto de atenção no plano, não como violação: nenhuma migração futura
fica devendo por causa disso.

**A expiração é gravada na criação**, não calculada na leitura. Assim, mudar a duração configurada
afeta as sessões seguintes e não as existentes — comportamento previsto na spec, e que também evita
que uma redução de prazo derrube toda a equipe no meio do turno.

---

## 5. Duração da sessão como parâmetro da propriedade

**Decisão**: três chaves em `parametro_hotel`, semeadas pelo bootstrap:

| Chave | Valor padrão | Por quê |
| --- | --- | --- |
| `duracao_sessao_recepcao_horas` | `12` | Cobre um turno inteiro sem cobrir o turno seguinte |
| `duracao_sessao_gestor_horas` | `12` | Mesmo raciocínio; o perfil é de consulta |
| `duracao_sessao_staff_horas` | `720` | Trinta dias. É a decisão de sessão longa por dispositivo |

**Rationale**: o Artigo XIII proíbe prazo em constante de código. A leitura por perfil, e não uma
duração única, é o que permite ao perfil operacional durar semanas sem que a recepção também dure.

Os valores são padrão de instalação, sujeitos a ajuste com o hotel — como já acontece com as
outras chaves. Alteração por SQL no MVP, escolha registrada na spec.

**Rejeitado**: guardar a duração em coluna da tabela `usuario`. Duração é política da propriedade,
não atributo de pessoa, e por usuário produziria o cenário em que ninguém sabe por que a sessão de
um funcionário dura diferente da do colega.

---

## 6. A revisão de migração

**Decisão**: revisão `0002_sessao`, no mesmo formato da `0001` — arquivo SQL companheiro congelado
em `alembic/versions/sql/0002_sessao.sql`, executado por cursor cru. O mesmo bloco de DDL é
acrescentado a `docs/04-schema.sql`, na seção 1, depois de `usuario`.

**Rationale**: manter uma única forma de descrever esquema no projeto. O bloco tem índice parcial e
`COMMENT ON`, que em chamadas do Alembic ficam como `op.execute()` de qualquer modo — então a
transcrição só acrescentaria uma segunda descrição a manter em acordo.

**Diferença em relação à `0001`: esta revisão tem `downgrade` de verdade** — `DROP TABLE sessao`.
A inicial não podia ter, porque reverter equivalia a descartar o banco; aqui a reversão é exata e
custa duas linhas. Sessão é dado descartável por natureza: reverter derruba os logins, não perde
histórico.

**Verificação**: o teste de conformidade da F0.2 já compara, nos dois sentidos, o banco migrado com
o documento. Ele passa a proteger esta tabela sem nenhuma linha nova de teste — era o objetivo de
tê-lo construído. Se o bloco entrar na revisão e não no documento, ou vice-versa, a suíte fica
vermelha.

---

## 7. Unidade de trabalho: o repositório recebe a conexão

**Decisão**: as funções de repositório passam a receber a conexão como primeiro parâmetro. O
roteador abre a transação por requisição, por dependência do FastAPI, e a fecha ao final. O comando
de bootstrap abre uma única transação e chama os serviços dentro dela.

**Rationale**: esta é a primeira fatia que precisa de duas escritas coerentes entre si. Desativar
um usuário e invalidar as sessões dele não pode acontecer pela metade, e o bootstrap tem de criar
hotel, usuário e parâmetros de uma vez — a FR-029 exige exatamente isso. O repositório da F0.1
chamava `obter_engine()` por conta própria, o que serve para uma consulta isolada de saúde e não
serve para transação.

Também é o que permite ao bootstrap atravessar dois módulos — `acesso` governa `usuario` e
`sessao`, `propriedade` governa `hotel` e `parametro_hotel` — sem que nenhum deles escreva na tabela
do outro: quem coordena é o comando, e a transação é dele.

**Rejeitado**: sessão do ORM do SQLAlchemy com padrão de unidade de trabalho implícita. Traria
mapeamento de entidades que o projeto não usa (seção 12) para resolver um problema que uma
transação explícita resolve.

---

## 8. Como testar autorização de recursos que ainda não existem

**O problema**: a FR-018 exige que o perfil operacional seja recusado ao ler dado cadastral de
hóspede, e a FR-019 que a gestão seja recusada ao alterar dado de domínio. Nenhum desses recursos
existe: hóspede chega na F1.3, reserva na F1.1, solicitação na F3.4. Criá-los agora seria implementar
fatia fora de ordem.

**Decisão em três camadas**:

1. **A política é uma decisão pura**, em `politica.py`: uma função que recebe perfil e operação
   nomeada e devolve permitido ou recusado. As operações de hóspede e de domínio já estão nomeadas
   na matriz, e são testadas por unidade — sem HTTP, sem banco. A matriz publicada está em
   [contracts/politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md).
2. **Os recursos desta fatia exercitam o mecanismo de ponta a ponta**: gestão cria usuário e
   recepção não; recepção revoga sessão e gestão não. Isso prova que a política está de fato
   ligada às rotas, e não apenas correta em isolamento.
3. **Uma varredura de rotas protege as fatias seguintes**: um teste percorre todas as rotas
   registradas na aplicação e falha se alguma que não esteja na lista explícita de rotas públicas
   deixar de exigir sessão. Quando a F1.1 acrescentar reservas e esquecer a guarda, a suíte
   acusa — e é o que sustenta honestamente a SC-002.

A terceira camada é a que importa a longo prazo: transforma "não esquecer de proteger a rota" de
disciplina humana em verificação de máquina, na mesma linha do Artigo IX.

---

## 9. Relógio injetável

**Decisão**: uma função `agora()` em `app/comum/relogio.py`, injetada nos serviços como argumento
com valor padrão — o mesmo padrão que o serviço de saúde da F0.1 já usa para a verificação de
conectividade.

**Rationale**: a US4 precisa verificar que a sessão continua válida depois de horas e que expira
depois do prazo. Sem relógio injetável, restariam duas opções ruins: esperar de verdade, ou gravar
uma expiração no passado e testar um caminho diferente do que a produção percorre.

---

## 10. Recusa indistinguível, inclusive no tempo

**Decisão**: quando o e-mail não existe, a autenticação **ainda executa** uma derivação contra um
hash de referência descartável, e só então recusa. A resposta é idêntica nos dois casos.

**Rationale**: a FR-003 pede recusas indistinguíveis. Sem esse cuidado, elas seriam distinguíveis
pelo tempo: e-mail inexistente responderia em milissegundos e senha errada em algumas centenas
deles, porque só o segundo caso paga a derivação lenta. É o mesmo raciocínio que levou o projeto a
exigir comparação em tempo constante no webhook — e o custo aqui é uma linha.

---

## 11. Identificação do dispositivo

**Decisão**: campo opcional `dispositivo` no corpo da autenticação, guardado como rótulo livre. Na
ausência, o agente do cliente truncado em 120 caracteres.

**Rationale**: a recepção precisa reconhecer qual linha revogar. "Celular da manutenção" é útil; uma
cadeia de agente de navegador é pior, mas melhor que nada. Não há verificação de que o dispositivo é
mesmo aquele — a lista serve para decidir o que revogar, não para autenticar, e prometer mais que
isso seria contrário ao Artigo XV.

---

## 12. Ausência de mapeamento de entidades

**Decisão**: continuar com SQL textual sobre SQLAlchemy Core, como nas fatias anteriores. A camada
`model` descrita no `AGENTS.md` permanece vazia.

**Rationale**: o esquema é descrito no documento de referência e aplicado por migração. Declarar as
tabelas outra vez em classes criaria uma terceira descrição do mesmo esquema a manter em acordo — o
argumento que já levou a F0.2 a rejeitar a transcrição do DDL em chamadas do Alembic. É divergência
com o `AGENTS.md`, que lista `model` como "mapeamento das tabelas", e por isso está na seção 13 em
vez de ficar implícita.

---

## 13. Divergências documentais encontradas

Nenhuma pode ser contornada em silêncio. A correção proposta entra como tarefa da fatia.

| Artefato | O que diz hoje | Correção proposta |
| --- | --- | --- |
| `docs/04-schema.sql` | Não tem tabela de sessão | Acrescentar o bloco de `sessao` na seção 1 e as chaves de duração ao comentário de `parametro_hotel` |
| `docs/04-modelagem-de-dados.md` | DER e dicionário sem `sessao` | Acrescentar a entidade, com classificação LGPD dos campos, e o relacionamento com `usuario` |
| `docs/05-arquitetura.md` §11.2 | Descreve perfis e sessão longa, sem dizer como a sessão existe | Registrar token opaco, cookie e revogação por linha de sessão |
| `docs/05-arquitetura.md` §11.3 | Lista `JWT_SECRET` como segredo | Remover: com token opaco não há nada a assinar. Nenhum segredo novo entra no lugar |
| `.cursor/rules/30-seguranca-lgpd.mdc` | Mesma lista com `JWT_SECRET` | Mesma remoção, e acrescentar que senha usa derivação lenta com parâmetros gravados na própria linha |
| `docs/backlog.md` F0.3 | Critério dizia "alterar qualquer dado" | **Já corrigido** na fase de especificação, com a lista de dados de domínio |
| `AGENTS.md` | Lista `model` como camada de mapeamento das tabelas | Registrar que o projeto não mapeia tabelas em ORM e que a camada permanece vazia |
| `.env.example` | Sem as chaves desta fatia | Acrescentar `SENHA_ITERACOES` e `BOOTSTRAP_SENHA_INICIAL`, sem valor |

**Sobre o `JWT_SECRET`**: é o caso que a orientação do projeto previu. A documentação foi escrita
antes da execução, e a escolha de JWT era razoável no papel — só não sobrevive ao encontro com o
requisito de revogação imediata que o próprio Artefato 5 §11.2 declara na mesma página.
