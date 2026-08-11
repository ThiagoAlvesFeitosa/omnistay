# Pesquisa — Esquema e Migrações

Fase 0 do plano. Cada seção resolve uma incógnita técnica levantada no contexto ou uma
divergência encontrada entre o documento de referência e o que o banco aceita.

---

## 1. Como uma revisão aplica o SQL do documento sem reescrevê-lo

**Decisão**: a revisão inicial carrega o SQL em um arquivo companheiro versionado,
`alembic/versions/sql/0001_esquema_inicial.sql`, criado como cópia byte a byte de
`docs/04-schema.sql` no momento da criação da revisão. A função `upgrade()` lê esse arquivo e o
executa em uma chamada só.

**Justificativa**: a spec pedia originalmente que a revisão lesse `docs/04-schema.sql`
diretamente. Isso quebra na segunda migração: o documento passa a descrever o esquema já
alterado, e a revisão inicial recriaria um banco onde a revisão seguinte tentaria aplicar uma
alteração já presente. O que a decisão preserva é o essencial — ninguém reescreve o esquema em
outra forma de descrição, como chamadas `op.create_table()` — e o que a substitui é melhor: a
conformidade entre documento e banco passa a ser verificada por máquina (seção 5) em vez de
depender de o desenvolvedor lembrar.

**Alternativas consideradas**:

- *Ler `docs/04-schema.sql` em tempo de execução*: rejeitada pelo motivo acima. Uma revisão cujo
  efeito muda quando outro arquivo é editado não é reproduzível, que é justamente a promessa da
  fatia.
- *Gerar `docs/04-schema.sql` a partir do banco*: rejeitada porque o documento carrega 30+
  `COMMENT ON` com justificativa de projeto, cabeçalho autoral e seções comentadas que nenhuma
  extração reproduz. Transformá-lo em artefato gerado destruiria a documentação para resolver um
  problema que o teste de conformidade já resolve.
- *Transcrever o esquema em operações do Alembic*: rejeitada. A trigger, a função `plpgsql`, a
  visão e os índices parciais não têm representação natural nessas operações, e a transcrição
  seria uma segunda descrição do esquema a manter em acordo à mão.

---

## 2. Divergência: o documento abre e fecha a própria transação

**Divergência encontrada**: `docs/04-schema.sql` começa com `BEGIN;` (linha 14) e termina com
`COMMIT;` (linha 467). O Alembic já envolve cada revisão em uma transação; executar o script como
está faria o `COMMIT` fechar a transação da migração antes de o Alembic gravar a versão aplicada,
deixando o banco com o esquema criado e sem registro de versão — exatamente o estado parcial que
a FR-010 proíbe.

**Correção proposta no documento** (conforme FR-015): remover `BEGIN;` e `COMMIT;` de
`docs/04-schema.sql` e acrescentar ao cabeçalho um comentário registrando que o controle de
transação é de quem aplica, com a forma recomendada de aplicação à mão:

```sql
-- O controle de transacao e de quem aplica este arquivo.
-- Aplicacao manual: psql --single-transaction -f docs/04-schema.sql
-- Aplicacao pelo Alembic: a revisao ja executa dentro de uma transacao.
```

Sem esse comentário, remover o `BEGIN;` parece descuido e alguém o coloca de volta. A flag
`--single-transaction` é usada no `quickstart.md` sempre que o documento é aplicado direto.

**Consequência para a FR-010**: PostgreSQL executa DDL dentro de transação. Com o `COMMIT`
removido e uma única revisão (FR-022), a atomicidade sai de graça — qualquer falha desfaz tudo,
sem tratamento nosso.

---

## 3. Divergência: versão do SGBD declarada

**Divergência encontrada**: o cabeçalho do documento declara `SGBD: PostgreSQL 14+`, enquanto a
stack do projeto fixa PostgreSQL 16 e o `docker-compose.yml` sobe `postgres:16`.

**Correção proposta no documento**: trocar por `SGBD: PostgreSQL 16`. Não se trata de contradizer
o que estava escrito: "14+" não é falso, é compatibilidade nunca verificada. O documento passa a
declarar apenas a versão que o teste exercita, que é o único compromisso que a entrega pode
sustentar — e o Artigo XV pede exatamente isso.

**Decisão sobre a verificação (FR-020)**: a checagem roda em `alembic/env.py`, antes de
`run_migrations()`, e não dentro da revisão. Assim vale para toda migração futura sem precisar ser
repetida em cada arquivo, e aborta antes de qualquer comando de esquema. A leitura é
`SELECT current_setting('server_version_num')` — inteiro como `160004`, sem análise de texto de
versão.

A decisão fica separada da leitura, em uma função pura que recebe o número e levanta o erro. Sem
essa separação, o único jeito de exercitar a guarda seria manter um servidor PostgreSQL antigo só
para o teste — dependência de infraestrutura que o Artigo XI não justifica para verificar uma
comparação de inteiros.

**Alternativa considerada**: checar dentro de `upgrade()` da revisão inicial. Rejeitada porque a
garantia se perderia na primeira revisão em que alguém esquecesse de repetir a checagem.

---

## 4. Executar um script com várias instruções em uma chamada

**Decisão**: usar o cursor do driver diretamente — `cursor.execute(sql)` sobre a conexão crua —
e não `exec_driver_sql`.

**Justificativa**: o driver `psycopg2` aceita várias instruções em um único `execute`, o que
mantém o script indivisível — não precisamos quebrá-lo em instruções, o que exigiria um
analisador de SQL capaz de entender o `$$ ... $$` da função `plpgsql`.

**Armadilha identificada, e onde ela realmente mora**: a função `fn_valida_transicao_reserva`
contém `%` na mensagem do `RAISE EXCEPTION`. O `psycopg2` só interpreta `%` quando recebe
parâmetros — e a primeira versão desta decisão supunha que `exec_driver_sql(sql)`, sem argumentos,
não passaria nenhum. **Não é o que acontece**: o SQLAlchemy 2.0 encaminha um dicionário vazio, o
psycopg2 tenta a interpolação e a execução falha com
`immutabledict is not a sequence`. Verificado na implementação.

A forma que funciona é pegar a conexão crua do driver e executar sem coleção alguma de
parâmetros:

```python
conexao_crua = engine.raw_connection()   # ou op.get_bind().connection na migração
cursor = conexao_crua.cursor()
cursor.execute(sql)
```

A alternativa de dobrar os `%` do script para `%%` foi rejeitada: mudaria o corpo da função
gravado no banco, e o `%` faz parte da mensagem de erro que o hóspede jamais vê mas o
desenvolvedor precisa ler. Pelo mesmo motivo evitamos `sqlalchemy.text()`, que trataria `:algo`
como parâmetro nomeado e reescreveria o script.

---

## 5. Como comparar o esquema aplicado com o documento (FR-017 e FR-018)

**Decisão**: não comparar texto. Aplicar os dois lados em bancos descartáveis distintos e
comparar inventários estruturais extraídos do catálogo do PostgreSQL:

1. Banco A: criado vazio, recebe `alembic upgrade head`.
2. Banco B: criado vazio, recebe `docs/04-schema.sql` na versão em vigor.
3. De cada um extrai-se o mesmo inventário via `pg_catalog`, e os dois são comparados como
   conjuntos ordenados. Qualquer diferença falha o teste, nomeando o que sobra e o que falta.

**Justificativa**: comparar texto de SQL não funciona — indentação, ordem de restrições e a
forma como o PostgreSQL normaliza uma expressão de `CHECK` produzem diferenças que não são
divergência de esquema. Fazendo o próprio PostgreSQL normalizar os dois lados, a comparação passa
a ser sobre estrutura, e não sobre escrita. Como o inventário é extraído do banco, o teste
também pega o que o servidor aceitou de forma diferente do que o autor escreveu.

**O que entra no inventário**:

| Item | Fonte | Forma normalizada |
| --- | --- | --- |
| Tabelas e colunas | `information_schema.columns` | nome, tipo, nulabilidade, valor padrão |
| Restrições | `pg_constraint` | nome e `pg_get_constraintdef()` |
| Índices | `pg_indexes` | nome e `indexdef` |
| Triggers | `pg_trigger` | nome, momento, evento e colunas, orientação, cláusula `WHEN`, função chamada |
| Funções | `pg_proc` | nome e **corpo completo** via `pg_get_functiondef()` |
| Visões | `pg_class` | nome e **consulta completa** via `pg_get_viewdef(oid, true)` |

Os objetos programáveis entram com o corpo, e não só com a identidade: a máquina de estados da
reserva mora dentro de `fn_valida_transicao_reserva`, e uma transição acrescentada ou removida ali
não muda nome nem assinatura. Sem o corpo, o teste deixaria passar a alteração mais perigosa que o
esquema pode sofrer. O detalhamento está em
[contracts/inventario-de-esquema.md](./contracts/inventario-de-esquema.md).

Sequências criadas por `BIGSERIAL` e os índices implícitos de chave primária entram
naturalmente, já que ambos os lados passam pelo mesmo caminho.

**Decisão sobre isolamento**: bancos descartáveis, criados e removidos por fixture de sessão
(`CREATE DATABASE` a partir de uma conexão de manutenção), e não esquemas dentro do mesmo banco.
O SQL do documento não qualifica objetos por esquema; com dois esquemas seria preciso manipular
`search_path` e depois remover o nome do esquema de toda definição extraída antes de comparar.
Com dois bancos, ambos os lados vivem em `public` e a comparação é direta. O usuário do
`docker-compose` é superusuário, então `CREATE DATABASE` está disponível.

**Alternativa considerada**: `pg_dump --schema-only` nos dois lados e comparação de texto.
Rejeitada por duas razões: depende do binário `pg_dump` presente na máquina e com versão
compatível com o servidor, o que é frágil no Windows; e reintroduz a comparação textual que a
decisão acima evita.

**Relação entre FR-017 e FR-018**: o mesmo mecanismo atende às duas. A FR-017 é a asserção de
presença — nenhuma estrutura do documento falta no banco migrado; a FR-018 é a asserção de
igualdade nos dois sentidos, que também pega estrutura a mais no banco. Implementadas como dois
testes sobre o mesmo par de inventários, para que a falha diga qual das duas quebrou.

---

## 6. Pular ou falhar quando não há banco (FR-019)

**Decisão**: manter o marcador `postgres` já registrado em `pyproject.toml` e a função
`postgres_disponivel()` já existente em `testes/conftest.py`. Acrescentar a variável de ambiente
`EXIGIR_POSTGRES`: quando ela estiver definida como `1` e o banco não responder, os testes
marcados falham com mensagem explícita em vez de serem pulados.

**Justificativa**: reaproveita o que a fatia 001 já deixou pronto e não acrescenta dependência.
O ponto de decisão fica em `pytest_collection_modifyitems`, em um lugar só, em vez de espalhado
por cada teste.

**Alternativa considerada**: uma opção de linha de comando (`--exigir-postgres`). Rejeitada
porque variável de ambiente atravessa igual em execução local, em script de verificação e em
integração contínua futura, sem precisar mudar como o comando é chamado.

---

## 7. Divergência a resolver na implementação: credencial em arquivo versionado

**Divergência encontrada**: `testes/conftest.py` traz
`postgresql+psycopg2://postgres:omnistay@localhost:5432/omnistay` como padrão embutido. A FR-011
diz que nenhum valor de conexão pode estar registrado em arquivo versionado.

**Decisão**: o padrão embutido sai do `conftest.py`. A URL de teste passa a vir de
`DATABASE_URL`, e `.env.example` documenta o valor de desenvolvimento — que é o comportamento que
a FR-011 descreve e o que a regra de segurança do projeto exige. Quando a variável não estiver
definida, os testes marcados são pulados pelo mecanismo da seção 6, com a mesma mensagem do caso
"banco inalcançável".

**Justificativa**: a credencial é de desenvolvimento local e sem valor real, mas a regra não
distingue — e um padrão embutido que funciona silenciosamente é justamente como uma credencial
real acaba versionada mais tarde.
