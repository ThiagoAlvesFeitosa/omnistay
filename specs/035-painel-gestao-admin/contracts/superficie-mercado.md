# Contrato: superfície — Mercado

Destino `/app/mercado`. Título **Mercado**. Só gestão.
Computador. Sem `compacto`. Somente leitura da série.

`GET /mercado` ao montar. Histórico: `GET /mercado/concorrentes/{id}`
**só** no clique da linha (controle explícito, não o hover).

---

## Visão atual

Cada concorrente: nome; preço e/ou nota do último sucesso, cada
um com a data da coleta; situação distinguível.

| `situacao` / dado | Marca na linha |
| --- | --- |
| `atual` | Sem marca de velho nem de falha |
| `desatualizado` com `ultima_falha` | Falha distinguível; valor do sucesso com data **antiga** |
| `desatualizado` sem falha posterior | Desatualizado; data do sucesso visível |
| `so_falha` | Falha; sem preço/nota como valor encontrado |
| `sem_coleta` | Ausência de coleta, distinta de falha e de zero |
| `cadencia_ausente` | Valores com data real; **não** como atual |

Preço zero de sucesso: zero datado, distinto de vazio.

Inativo: visível, distinguível. Sem apagar, sem desativar nesta
tela.

Sem linha da própria casa. Sem coluna de variação percentual.

---

## Histórico

Pontos em ordem de tempo. Falha intercalada aparece como tentativa
sem valor, com data — não como preço zero.

`404`: aviso; a visão atual permanece.

---

## O que não aparece

Cadastrar, corrigir, desativar, reativar concorrente. Coletar
agora. Corrigir preço ou nota na mão.

---

## Vazio e falha

`concorrentes: []`: lista vazia honesta. GET 5xx: falha, não vazio.
