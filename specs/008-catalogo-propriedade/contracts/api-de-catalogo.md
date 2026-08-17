# Contrato: API de catálogo (F2.1)

Quatro rotas. Cookie de sessão `omnistay_sessao`. O hotel é **sempre** o da sessão —
corpo e query **não** carregam `id_hotel`.

Autorização: [politica-de-autorizacao.md](./politica-de-autorizacao.md).
Modelo: [data-model.md](../data-model.md).
Porta para fatias seguintes: [catalogo-repository.md](./catalogo-repository.md).

---

## Convenções

| Tema | Regra |
| --- | --- |
| Autenticação | Cookie; ausência → `401` |
| Autorização | Perfil sem permissão → `403` |
| Outro hotel / id inexistente | `404` (mesma resposta; não revela existência) |
| Validação | `422` com mensagem por campo / regra |
| Categorias | `horario` · `cardapio` · `servico` · `programacao` · `regra` |
| Logs | `id_catalogo_item`, `id_hotel`, `categoria`, ação — sem texto do fato |

---

## `POST /catalogo`

**Operação**: `alterar_catalogo`

Cria item ativo na propriedade da sessão.

### Entrada

```json
{
  "categoria": "horario",
  "titulo": "Cafe da manha",
  "conteudo": "Servido das 7h as 10h no restaurante."
}
```

| Campo | Obrigatório | Regra |
| --- | --- | --- |
| `categoria` | sim | Uma das cinco chaves |
| `titulo` | sim | Trim; 1 a 160 caracteres |
| `conteudo` | sim | Trim; não vazio |

Não aceita `ativo` na criação (nasce ativo). Não aceita `id_hotel`.

### Saída `201`

```json
{
  "id_catalogo_item": 12,
  "categoria": "horario",
  "titulo": "Cafe da manha",
  "conteudo": "Servido das 7h as 10h no restaurante.",
  "ativo": true
}
```

### Erros

| Situação | Status |
| --- | --- |
| Sessão ausente/inválida | `401` |
| Perfil não é recepção | `403` |
| Campo ausente, só espaços, categoria inválida, título > 160 | `422` |

---

## `GET /catalogo`

**Operação**: `ler_catalogo`

Lista de manutenção: ativos e inativos do hotel da sessão.

### Saída `200`

```json
{
  "itens": [
    {
      "id_catalogo_item": 12,
      "categoria": "horario",
      "titulo": "Cafe da manha",
      "conteudo": "Servido das 7h as 10h no restaurante.",
      "ativo": true
    }
  ]
}
```

Ordem: `categoria`, depois `id_catalogo_item`. Hotel sem itens: `"itens": []`.

---

## `GET /catalogo/ativo`

**Operação**: `ler_catalogo`

Catálogo ativo completo. As cinco chaves **sempre** existem; item inativo não aparece.

### Saída `200`

```json
{
  "horario": [
    {
      "id_catalogo_item": 12,
      "categoria": "horario",
      "titulo": "Cafe da manha",
      "conteudo": "Servido das 7h as 10h no restaurante."
    }
  ],
  "cardapio": [],
  "servico": [],
  "programacao": [],
  "regra": []
}
```

Itens dentro de cada categoria: `id_catalogo_item` crescente. Sem campo `ativo` (todos
são ativos). Propriedade vazia: cinco arrays vazios, não é erro.

---

## `PATCH /catalogo/{id_catalogo_item}`

**Operação**: `alterar_catalogo`

Altera título, conteúdo e/ou `ativo` de um item do hotel da sessão. Categoria não muda.

### Entrada

Pelo menos um campo:

```json
{
  "titulo": "Cafe da manha",
  "conteudo": "Servido das 6h30 as 10h.",
  "ativo": false
}
```

| Campo | Obrigatório | Regra |
| --- | --- | --- |
| `titulo` | não | Se presente: trim; 1 a 160 |
| `conteudo` | não | Se presente: trim; não vazio |
| `ativo` | não | `true` reativa; `false` desativa |
| `categoria` | — | Se enviado → `422` |

### Saída `200`

Mesmo formato do `201` de criação, com os valores atuais.

### Erros

| Situação | Status |
| --- | --- |
| Sessão ausente/inválida | `401` |
| Perfil não é recepção | `403` |
| Id inexistente **ou** de outro hotel | `404` |
| Corpo vazio, só espaços, `categoria` presente, título > 160 | `422` |

---

## `DELETE /catalogo/{id_catalogo_item}`

Não existe. Resposta `405`. O caminho suportado é `PATCH` com `"ativo": false`.

---

## Recusas por perfil (resumo)

| Rota | recepção | gestão | operação |
| --- | --- | --- | --- |
| `POST` / `PATCH` | sim | `403` | `403` |
| `GET /catalogo` e `GET /catalogo/ativo` | sim | sim | `403` |
