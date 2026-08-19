# Contrato: API de atendimento — consumo e lançamento (delta F3.7)

Autorização: [politica-de-autorizacao.md](./politica-de-autorizacao.md). Modelo:
[data-model.md](../data-model.md). Item vendável:
[api-de-item-vendavel.md](./api-de-item-vendavel.md).

`POST /webhook` intocado. `GET /fila-do-dia` só muda o booleano humano por trás
(dois desfechos novos); o JSON do item da fila **não** ganha campo.

---

## `GET /solicitacoes` (delta)

Mesma lista `aberta` / `em_andamento`. Cada item **ganha** duas chaves:

| Campo | Reclamação / serviço | Consumo |
| --- | --- | --- |
| `valor_praticado` | `null` | número com duas casas |
| `status_lancamento` | `null` | `pendente` (nesta lista; se já lançado e ainda aberto, o valor correspondente) |

Campos proibidos continuam: nome, telefone, documento, endereço. `tipo` passa a
poder ser `consumo`.

Staff vê o valor para entregar. Gestão vê. Ninguém vê ficha.

---

## `GET /consumos/pendentes`

Fila destacada da passagem de turno financeira.

| | |
| --- | --- |
| Operação | `ler_solicitacao_atribuida` |
| Quem | recepção, staff, gestão da **própria** propriedade |
| Filtro | `consumo.status_lancamento = 'pendente'` e `reserva.id_hotel` da sessão |
| Ordem | `aberta_em` crescente |

Inclui consumo **já resolvido no quarto**. Não inclui serviço nem reclamação.
Não inclui `lancado` nem `dispensado`.

### Item

```text
id_solicitacao
id_reserva
descricao
descricao_item
numero_quarto          # string ou nulo
valor_praticado
status_lancamento      # sempre pendente nesta lista
aberta_em
resolvida_em           # nulo se o quarto ainda não fechou
```

**Campos proibidos:** nome, telefone, documento, endereço, texto da confirmação.

### Respostas

| Situação | HTTP |
| --- | --- |
| Lista (inclusive vazia) | **200** `{ "itens": [ ... ] }` |
| Sem sessão | **401** |
| Hotel B autenticado | **200** só com itens de B |

Não há 404 em coleção. Os três perfis autenticados desta operação recebem 200.

---

## `POST /solicitacoes/{id_solicitacao}/lancamento`

Marca pendente como lançado. Operação: `lancar_consumo` (só recepção).

**Corpo da requisição:** vazio.

**Resposta `200`:**

```json
{
  "id_solicitacao": 7,
  "status_lancamento": "lancado",
  "id_usuario_lancamento": 3,
  "lancado_em": "2026-08-19T14:32:07.481Z"
}
```

Sem ficha, sem `descricao`, sem valor no envelope (o valor não muda; quem precisa
já o viu na lista).

**Erros:**

| Código | Quando | Corpo |
| --- | --- | --- |
| `401` | Sessão ausente ou inválida | `{"detail": "Sessao ausente ou invalida."}` |
| `403` | Staff ou gestão | `{"detail": "Perfil sem permissao para esta operacao."}` |
| `404` | Inexistente, outro hotel, ou não é consumo | `{"detail": "Solicitacao nao encontrada."}` |
| `409` | Já `lancado` ou já `dispensado` | `{"detail": "<motivo legível>"}` |

Motivos de `409` (estáveis):

| Situação | Detalhe |
| --- | --- |
| Já lançado | `Este consumo ja foi lancado.` |
| Já dispensado | `Este consumo ja foi dispensado.` |

Efeitos de `200`, na mesma transação: `status_lancamento = lancado`, autor e
instante preenchidos. `solicitacao.status` intocado. Nenhuma mensagem ao
hóspede. Item some de `GET /consumos/pendentes`.

---

## `POST /solicitacoes/{id_solicitacao}/dispensa`

Mesma operação `lancar_consumo`. Mesmos 401/403/404. `200` com
`status_lancamento = "dispensado"` e os mesmos campos de autor/instante.
`409` nos mesmos terminais. **Não** consta como lançado.

---

## `POST /solicitacoes/{id_solicitacao}/resolucao` (delta)

Aceita `tipo = consumo`. O `409` “deste tipo não pode ser resolvida nesta
operação” **deixa de existir**.

Corpo `200`: `tipo` pode ser `consumo`. `confirmacao` igual à F3.6. Resolução
**não** altera `status_lancamento`. Item some de `GET /solicitacoes` e **permanece**
em `GET /consumos/pendentes` se ainda `pendente`.

Gestão continua `403`. Hotel B, `404`. Já resolvida, `409`.

---

## Superfícies que esta fatia não cria

- `GET /solicitacoes/{id}`
- Recado HTTP de lançamento
- Integração / verificação no sistema de gestão do hotel
- `GET /reservas/{id}/mensagens`
- Campo novo no JSON de `GET /fila-do-dia`
- Tela React
- Lista de pedidos no checkout (F4.2)
