# Contrato: situação do dado no painel

Como a visão atual classifica cada concorrente. O histórico **não** usa
este contrato: ele devolve a série crua.

Modelo: [data-model.md](../data-model.md).
API: [api-de-painel.md](./api-de-painel.md).

A classificação é **derivada na leitura**. Nada é gravado em
`coleta_mercado`. Relógio e periodicidade são os da consulta, não os da
coleta original.

---

## Entradas

Para um concorrente da propriedade da sessão:

| Entrada | Definição |
| --- | --- |
| `ultimo_sucesso` | Linha com `sucesso = true` de maior `(coletado_em, id_coleta)`, ou nenhuma |
| `ultima_linha` | Linha de maior `(coletado_em, id_coleta)` da série (qualquer `sucesso`) |
| `ultima_falha` | Se `ultima_linha` existe e `sucesso = false`: o `coletado_em` dela. Senão: nenhuma |
| `P` | Inteiro ≥ 1 lido de `periodicidade_coleta_mercado`. Qualquer outro valor (ausente, vazio, não numérico, ≤ 0) → `P` inválido |
| `agora` | Instante da consulta (injetável nos testes) |

`ultima_coleta` da F5.2 (último ponto sem filtrar sucesso) **não** é o
preço exibido.

---

## Valores de `situacao`

Exatamente um por concorrente:

| Valor | Condição (primeira que casar, nesta ordem) |
| --- | --- |
| `sem_coleta` | Não existe nenhuma linha na série |
| `so_falha` | Não existe `ultimo_sucesso` (todas as linhas são falha) |
| `cadencia_ausente` | Existe `ultimo_sucesso` **e** `P` é inválido |
| `desatualizado` | Existe `ultimo_sucesso` **e** `P` é válido **e** (`agora >= ultimo_sucesso.coletado_em + P horas` **ou** existe `ultima_falha`) |
| `atual` | Existe `ultimo_sucesso` **e** `P` é válido **e** `agora < ultimo_sucesso.coletado_em + P horas` **e** não existe `ultima_falha` |

A ordem evita ambiguidades: ausência de sucesso nunca é `desatualizado`
(não há valor para envelhecer). `cadencia_ausente` nunca é `atual`.

O `>=` da janela é o mesmo da F5.2 (“coleta devida”). No instante em que
a fonte voltaria a ser visitada, o número deixa de ser `atual`.

---

## O que a visão atual mostra junto com `situacao`

| Campo | Regra |
| --- | --- |
| `ultimo_sucesso.preco` / `nota_media` / `coletado_em` | Só da linha de sucesso; `null` no campo não obtido; zero permanece zero |
| `ultima_falha.coletado_em` | Só quando a linha mais recente da série é falha |
| Preço ou nota de linha com `sucesso = false` | **Nunca** |

Assim: sucesso antigo + falha nova → número e data **do sucesso**, falha
visível pela data em `ultima_falha`, `situacao = desatualizado`.

---

## Periodicidade no envelope da lista

`GET /mercado` inclui `periodicidade_horas`: o inteiro `P` quando válido,
`null` quando inválido. Não se devolve a string crua do parâmetro. Não se
substitui `null` por `24`.

---

## O que este contrato não faz

- Não dispara coleta quando `desatualizado`.
- Não calcula variação percentual.
- Não compara com a tarifa da própria casa.
- Não persiste `situacao` para a consulta seguinte (o relógio anda).
