# Contrato: API de item vendável

Modelo: [data-model.md](../data-model.md). Autorização:
[politica-de-autorizacao.md](./politica-de-autorizacao.md). Identificação:
[identificacao-e-preco.md](./identificacao-e-preco.md).

Recurso da propriedade, distinto do catálogo de fatos (`/catalogo`). Preço em
campo numérico. Sem apagamento permanente.

Operações **já existentes**: escrita `alterar_catalogo` (recepção); leitura
`ler_catalogo` (recepção e gestão). Staff recusado nas duas.

---

## Item (resposta)

```text
id_item_vendavel
nome
preco_atual          # string ou número decimal com duas casas; nunca negativo
ativo
atualizado_em
```

Sem `id_hotel` no JSON (é o da sessão). Sem ficha de hóspede.

---

## `POST /itens-vendaveis`

Cria ativo na propriedade da sessão. Corpo: `nome`, `preco_atual` (>= 0).

| Situação | HTTP |
| --- | --- |
| Criado | **201** com o item |
| Nome ativo duplicado no hotel | **409** `{"detail": "Ja existe item vendavel ativo com este nome."}` |
| Preço negativo / nome vazio | **422** |
| Staff ou gestão | **403** |
| Sem sessão | **401** |

---

## `GET /itens-vendaveis`

Manutenção: ativos e inativos da propriedade. Recepção e gestão: **200**.
Staff: **403**. Hotel B não vê A.

---

## `PATCH /itens-vendaveis/{id_item_vendavel}`

Recepção. Campos opcionais: `nome`, `preco_atual`, `ativo`.

| Situação | HTTP |
| --- | --- |
| Ok | **200** com o item atualizado |
| Inexistente ou outro hotel | **404** `{"detail": "Item vendavel nao encontrado."}` |
| Nome ativo duplicado | **409** |
| Preço negativo | **422** |
| Staff ou gestão | **403** |

Desativar: `ativo = false`. Reativar: `ativo = true` (sujeito ao unique de
nome). **Não** há `DELETE`.

Reajuste de `preco_atual` **não** altera `consumo.valor_praticado` já gravado.

---

## Efeito na identificação

Só `ativo = true` entra em `itens_ativos`. Item de A nunca entra no prompt de
B. O worker lê esta tabela; HTTP de manutenção **não** passa pela porta de LLM.

---

## Superfícies que esta fatia não cria

- Preço no `/catalogo` de fatos
- `DELETE /itens-vendaveis/{id}`
- Rota pública (sem sessão) de cardápio cobrado
- Histórico de preços além do retrato em `consumo`
