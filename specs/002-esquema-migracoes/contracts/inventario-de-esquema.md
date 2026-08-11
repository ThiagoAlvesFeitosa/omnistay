# Contrato — Inventário de esquema

Esta fatia não expõe interface HTTP nem comando ao usuário final: ela cria estrutura de banco.
O único contrato que ela publica é interno e vale a pena fixar, porque duas verificações
distintas (FR-017 e FR-018) e toda migração futura vão depender dele: **a forma do inventário
extraído de um banco**.

## Propósito

Permitir comparar dois bancos por estrutura, e não por texto de SQL. O inventário é o que se
extrai de um banco; comparar dois inventários responde se dois bancos têm o mesmo esquema.

## Forma

Um dicionário com seis chaves fixas. Cada valor é um conjunto ordenado de tuplas de texto, de
modo que a comparação seja determinística e a diferença seja legível ao falhar.

```python
Inventario = dict[str, list[tuple[str, ...]]]
```

| Chave | Tupla | Ordenação |
| --- | --- | --- |
| `tabelas` | `(tabela, coluna, tipo, nulabilidade, valor_padrao)` | por tabela, depois por coluna |
| `restricoes` | `(tabela, nome, definicao)` | por tabela, depois por nome |
| `indices` | `(tabela, nome, definicao)` | por tabela, depois por nome |
| `triggers` | `(tabela, nome, momento, evento, orientacao, condicao_when, funcao_chamada)` | por tabela, depois por nome |
| `funcoes` | `(nome, corpo_completo)` | por nome |
| `visoes` | `(nome, consulta_completa)` | por nome |

As definições vêm sempre das funções de reconstrução do próprio PostgreSQL — `pg_get_constraintdef`,
`pg_get_triggerdef`, `pg_get_functiondef`, `pg_get_viewdef`, `indexdef` — para que os dois lados
passem pela mesma normalização e diferenças de escrita não virem falha.

## O corpo dos objetos programáveis entra no inventário

Não basta nome e assinatura. A máquina de estados da reserva vive dentro do corpo de
`fn_valida_transicao_reserva`: alguém pode acrescentar uma transição permitida, ou remover uma
proibida, sem mudar o nome da função, a assinatura ou a trigger que a chama. Um inventário que
guardasse só a identidade desses objetos deixaria passar exatamente a alteração mais perigosa que
o esquema pode sofrer — e é essa proteção que o Artigo IX pede que more no banco.

| Objeto | O que é capturado | Como |
| --- | --- | --- |
| Função | Corpo completo, incluindo a lógica de transição | `pg_get_functiondef(oid)`; alternativa equivalente é `prosrc` normalizado, junto com linguagem e tipo de retorno |
| Visão | Consulta completa, incluindo colunas derivadas como `chegada_nao_confirmada` | `pg_get_viewdef(oid, true)`, com a forma legível que o PostgreSQL normaliza |
| Trigger | Momento (`BEFORE`/`AFTER`), evento e colunas (`UPDATE OF status`), orientação (`FOR EACH ROW`), cláusula `WHEN` e função chamada | Decomposto de `pg_get_triggerdef(oid)` ou lido de `pg_trigger` campo a campo |

A trigger é decomposta em campos, e não guardada como um texto único, para que a falha diga qual
aspecto mudou — trocar `BEFORE UPDATE OF status` por `BEFORE UPDATE` desarma a proteção sem
alterar mais nada, e a mensagem de erro precisa nomear isso.

Comparar corpo completo torna o teste sensível a reformatação da função. É o comportamento
desejado: reformatar a função exige reaplicar o documento e a migração juntos, que é justamente o
acordo que a FR-018 existe para forçar.

## Escopo

- Somente o esquema `public`.
- A tabela `alembic_version` é **excluída**, porque existe apenas no lado migrado.
- Comentários (`COMMENT ON`) ficam fora do inventário nesta fatia: são documentação, e incluí-los
  faria a comparação falhar por texto de comentário em vez de por estrutura.

## Uso

| Verificação | Comparação |
| --- | --- |
| FR-017 — nada falta | Todo item do inventário de referência está no inventário migrado |
| FR-018 — nada difere | Os dois inventários são iguais, chave por chave, nos dois sentidos |

A mensagem de falha nomeia a chave, o que falta e o que sobra. Um teste que só diz "os esquemas
diferem" não ajuda ninguém a corrigir a divergência.
