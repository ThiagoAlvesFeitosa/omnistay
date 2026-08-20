# Contrato — API de saída (delta F4.2)

Sessão válida (cookie `omnistay_sessao`). Sempre o `id_hotel` da sessão.
A rota e a operação do clique **não mudam**.

---

## `POST /reservas/{id_reserva}/saida` (delta)

Operação: `confirmar_fase_da_reserva` (já existente; só `recepcao`).
Corpo vazio. Códigos de erro da F4.1 inalterados (`401`, `403`, `404`,
`409`).

**Resposta `200`:**

```json
{
  "id_reserva": 42,
  "status": "encerrado",
  "checkout_em": "2026-08-20T12:04:11.220Z",
  "pesquisa": "agendada",
  "lista": "agendada"
}
```

| Campo | Valores |
| --- | --- |
| `pesquisa` | inalterado (F4.1) |
| `lista` | `agendada` \| `ausente` \| `ja_agendada` |

`lista` é o desfecho do **registro** da pendência, não da entrega.
`ausente` = recorte cobrável vazio naquele instante: **zero** mensagem e
**zero** trabalho de lista; a pesquisa segue. `ja_agendada` só na corrida
em que outra execução gravou o trabalho no mesmo instante — o checkout
segue válido.

**Efeitos de um `200`, na mesma transação (além da F4.1):**

1. Se existir ao menos um consumo cobrável da reserva: `mensagem` de
   saída pendente com o texto da lista **e** `trabalho`
   `enviar_lista_pedidos_chat` com `{id_reserva, id_mensagem}`
2. Se o recorte for vazio: nenhum dos dois

Chamado aberto e consumo pendente **não** alteram esses efeitos (o
pendente **entra** na lista).

**Efeitos de `403`, `404` e `409`:** nenhum — inclusive zero lista.
