# Contrato — API da lista de pedidos feitos pelo chat

Sessão válida. Sempre o `id_hotel` da sessão. Autorização:
[politica-de-autorizacao.md](./politica-de-autorizacao.md). Modelo:
[data-model.md](../data-model.md).

A URL e os rótulos **não** usam “extrato” nem “conta”.

---

## `GET /reservas/{id_reserva}/pedidos-feitos-pelo-chat`

Consulta ao vivo do recorte cobrável da reserva.

| | |
| --- | --- |
| Operação | `ler_pedidos_feitos_pelo_chat` |
| Quem | recepção e gestão da **própria** propriedade |
| Recorte | `consumo` da reserva com `status_lancamento` ∈ {`pendente`, `lancado`} |
| Ordem | `solicitacao.aberta_em` crescente, depois `id_solicitacao` |

Permitido em qualquer status da reserva da casa (a recepção pode olhar
antes do clique de saída). Não exige que a mensagem já tenha sido
enviada.

### Item

```text
id_solicitacao
descricao_item
valor_praticado
```

**Campos proibidos:** nome, telefone, documento, endereço,
`solicitacao.descricao`, `status_lancamento`, texto da mensagem.

### Envelope

```json
{
  "id_reserva": 42,
  "itens": [
    {
      "id_solicitacao": 7,
      "descricao_item": "Cerveja",
      "valor_praticado": 12.00
    }
  ],
  "total": 12.00
}
```

`total` é a soma dos `valor_praticado` de `itens` (0 se vazio). Duas
casas. Não é total da estadia.

### Respostas

| Situação | HTTP |
| --- | --- |
| Lista (inclusive vazia) | **200** |
| Sem sessão | **401** `{"detail": "Sessao ausente ou invalida."}` |
| Staff | **403** `{"detail": "Perfil sem permissao para esta operacao."}` |
| Reserva inexistente **ou** de outro hotel | **404** `{"detail": "Reserva nao encontrada."}` |

`404` para outro hotel é deliberado: não distingue “não existe” de “não é
sua”. Não há 404 por lista vazia.
