# Contrato: API da descrição de tom

Modelo: [data-model.md](../data-model.md). Política:
[politica-de-autorizacao.md](./politica-de-autorizacao.md).

Duas rotas no roteador de `propriedade`. Sessão por cookie
`omnistay_sessao`. `id_hotel` **somente** da sessão.

---

## `GET /propriedade/personalidade`

Operação: `ler_personalidade_assistente` (`recepcao`, `gestor`).

**Resposta `200`:**

```json
{
  "texto": ""
}
```

`texto` é o valor vigente depois do `strip` histórico (o que está no
banco). Chave ausente devolve `""`, não 404 — a casa opera com voz
padrão.

**Erros:**

| Código | Quando |
| --- | --- |
| `401` | Sessão ausente ou inválida |
| `403` | Perfil operacional (`staff`) |

---

## `PUT /propriedade/personalidade`

Operação: `alterar_personalidade_assistente` (só `gestor`).

**Corpo:**

```json
{
  "texto": "Seja breve e caloroso."
}
```

Campo obrigatório. `extra` proibido. `null` é inválido (422).

**Resposta `200`:** o mesmo formato do GET, com o texto **já
normalizado** (strip). `{"texto": ""}` quando a gestão gravou vazio ou
só espaços.

**Erros:**

| Código | Quando |
| --- | --- |
| `401` | Sessão ausente ou inválida |
| `403` | Recepção ou perfil operacional |
| `422` | Mais de 500 caracteres após strip; caractere de controle que não é quebra de linha nem tabulação |

`422` **não** grava. Valor anterior permanece.

Efeito de `200`, na mesma transação: `upsert` só da chave
`personalidade_assistente` daquele hotel. Nenhuma outra chave muda.
Nenhuma mensagem ao hóspede é refeita.

---

## O que estas rotas não fazem

- Não recebem `chave` nem `id_hotel` no corpo ou na URL
- Não editam o aviso de assistente virtual
- Não editam os três slots de boas-vindas
- Não disparam composição de dúvida
