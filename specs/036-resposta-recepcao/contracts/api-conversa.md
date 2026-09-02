# Contrato: GET conversa da estadia

Autenticação: cookie `omnistay_sessao`. Hotel: só o da sessão.
A tela **não** envia `id_hotel`.

Operação `ler_conversa_da_estadia` (só `recepcao`).

---

## `GET /reservas/{id_reserva}/conversa`

**200**

```json
{
  "id_reserva": 12,
  "janela": {
    "aberta": true,
    "motivo": null
  },
  "mensagens": [
    {
      "id_mensagem": 40,
      "direcao": "recebida",
      "origem": "hospede",
      "conteudo": "tem berco?",
      "status_envio": null,
      "em": "2026-09-02T18:01:00+00:00"
    },
    {
      "id_mensagem": 41,
      "direcao": "enviada",
      "origem": "automatico",
      "conteudo": "A recepção vai atender.",
      "status_envio": "enviada",
      "entrega": "enviada",
      "nova_tentativa": false,
      "em": "2026-09-02T18:01:05+00:00"
    }
  ]
}
```

`mensagens` em ordem de `em` crescente. `origem`: `hospede` |
`automatico` | `recepcao`. Em enviadas, `entrega` é `enviando`
(`status_envio=pendente`), `enviada` (`enviada`/`entregue`) ou
`falhou` (`falha`). `nova_tentativa` é verdadeiro quando `entrega`
é `falhou` e o trabalho ainda não está `concluido`. Recebidas:
`entrega` e `nova_tentativa` nulos. `janela.motivo` quando fechada:
`nunca_escreveu` | `sem_mensagem_recente`. Lista vazia é `200`
com `mensagens: []`, não é falha.

**401** — casca volta à entrada.

**403** — `staff` / `gestor`.

**404** — reserva inexistente ou de outro hotel (recado genérico,
igual à ficha).

Sem query. Sem corpo.

A tela **não** usa este GET para montar os nove campos.
