# Contrato: API de hospedagem — delta da fila do dia (F3.2)

Autorização: [politica-de-autorizacao.md](./politica-de-autorizacao.md). Modelo:
[data-model.md](../data-model.md).

Nenhuma rota nova. `POST /webhook` não muda.

---

## `GET /fila-do-dia`

Já existente; `ler_fila_do_dia`; só recepção.

Cada item passa a incluir:

```json
{
  "id_reserva": 1,
  "status": "hospedado",
  "precisa_atendimento_humano": true
}
```

| Campo | Tipo | Semântica |
| --- | --- | --- |
| `precisa_atendimento_humano` | boolean | `true` só se a reserva está `hospedado` e há mensagem recebida com classificação de intenção em desfecho humano (`encaminhado_humano`, `formato_invalido`, `indisponivel`) |

Demais campos do item **inalterados**. Reservas em cadastro (`aguardando_cadastro`,
ficha, etc.) devolvem `false` — o sinal de ficha irreconhecível continua em
`estado_cadastro = leitura_humana`, não neste booleano.

Classificação `classificado` (dúvida, serviço, reclamação) **não** liga o flag:
essas mensagens aguardam F3.3–F3.5.

Gestão e operacional: a rota continua recusando (`ler_fila_do_dia`). Não há
`GET /indicadores/...` para esta pendência.

---

## Superfícies que esta fatia não cria

- `GET /reservas/{id}/mensagens`
- `POST` de “marcar atendimento humano como visto”
- Qualquer envio ao hóspede
