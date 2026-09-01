# Contrato: API reusada (F8.6)

Nenhuma rota nova. Nenhuma mudança de schema. As telas são clientes
das operações abaixo. Detalhe HTTP original: F2.1, F3.7, F7.3.

Autenticação: cookie `omnistay_sessao` via `credentials: "include"`.
Hotel: só o da sessão. A tela **não** envia `id_hotel`.

---

## `GET /catalogo`

Operação `ler_catalogo` (`recepcao`, `gestor`). Staff: a casca não
dispara.

**200** — `itens[]` com `id_catalogo_item`, `categoria`, `titulo`,
`conteudo`, `ativo`. Ordem da API: categoria, depois id. A tela
filtra pela aba; **não** reordena o restante.

`itens: []` é lista vazia, não erro.

A tela não envia query. **Não** chama `GET /catalogo/ativo`.

---

## `POST /catalogo`

Operação `alterar_catalogo` (só `recepcao`). Corpo: `categoria`
(chave da aba visível), `titulo`, `conteudo`.

Disparado **somente** pelo controle de novo item, na recepção.

| Código | Efeito na tela |
| --- | --- |
| `201` | `GET /catalogo` de novo. O item nasce ativo na aba |
| `422` | Motivo visível; nada criado |
| `403` | Não ocorre na recepção; gestão não vê o controle |
| `401` | Casca |

---

## `PATCH /catalogo/{id_catalogo_item}`

Operação `alterar_catalogo` (só `recepcao`).

| Botão | Corpo |
| --- | --- |
| **Editar** (linha ativa) | `titulo` e/ou `conteudo` — nunca `categoria` |
| **Desativar** | `{ "ativo": false }` |
| **Reativar** | `{ "ativo": true }` |

| Código | Efeito na tela |
| --- | --- |
| `200` | `GET /catalogo` de novo |
| `404` | Recado genérico; `GET` de novo |
| `422` | Motivo visível; estado anterior permanece |
| `405` em DELETE | A tela **não** chama DELETE |

---

## `GET /itens-vendaveis`

Operação `ler_catalogo` (`recepcao`, `gestor`).

**200** — `itens[]` com `id_item_vendavel`, `nome`, `preco_atual`,
`ativo` (`atualizado_em` ignorado na UI). Sem descrição.

`itens: []` é lista vazia honesta.

Proxy Vite precisa encaminhar este prefixo (ver research §7).

---

## `POST /itens-vendaveis`

Operação `alterar_catalogo` (só `recepcao`). Corpo: `nome`,
`preco_atual` (≥ 0).

| Código | Efeito na tela |
| --- | --- |
| `201` | `GET /itens-vendaveis` de novo |
| `409` | Motivo visível (nome ativo duplicado); nada criado |
| `422` | Motivo visível (nome vazio / preço inválido) |

---

## `PATCH /itens-vendaveis/{id_item_vendavel}`

Operação `alterar_catalogo` (só `recepcao`).

| Botão | Corpo |
| --- | --- |
| **Editar** preço | `{ "preco_atual": … }` sem obrigar `nome` |
| **Editar** nome | `{ "nome": … }` sem obrigar `preco_atual` |
| **Editar** os dois | ambos |
| **Desativar** / **Reativar** | `{ "ativo": false }` / `{ "ativo": true }` |

`409` ao reativar com nome já usado por outro ativo: motivo
visível; o item permanece desativado.

---

## `GET /propriedade/boas-vindas`

Operação `ler_texto_de_boas_vindas` (`recepcao`, `gestor`).

**200** — `cafe`, `wifi`, `checkout`, `convite`. `null` → input
vazio.

---

## `PUT /propriedade/boas-vindas`

Operação `alterar_texto_de_boas_vindas` (só `recepcao`). Corpo: os
**quatro** campos. Atômico.

Disparado **somente** por **Salvar**.

| Código | Efeito na tela |
| --- | --- |
| `200` | Substituir os quatro valores pelo corpo; **zero** mensagem ao hóspede |
| `422` | `detail` visível (campo + motivo, sem ecoar o texto); valores anteriores intactos |
| `403` | Gestão não vê **Salvar** |

A tela **não** valida quebra de linha / tabulação / cinco espaços
por conta própria. A API é a fonte da verdade (FR-015).

---

## O que esta fatia não altera no HTTP

- Campos dos JSON de catálogo, item vendável e recado
- `GET /catalogo/ativo` e a porta de LLM
- Disparo / recuperação do recado de chegada
- Matriz de `politica.py`
- Worker
