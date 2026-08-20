# Contrato — API de saída

Sessão válida (cookie `omnistay_sessao`). Sempre o `id_hotel` da sessão.

---

## `POST /reservas/{id_reserva}/saida`

Confirma a saída. Operação: `confirmar_fase_da_reserva` (já existente; só
`recepcao`).

**Corpo da requisição:** vazio.

**Resposta `200`:**

```json
{
  "id_reserva": 42,
  "status": "encerrado",
  "checkout_em": "2026-08-20T12:04:11.220Z",
  "pesquisa": "agendada"
}
```

| Campo | Valores |
| --- | --- |
| `status` | Sempre `encerrado` num `200` |
| `checkout_em` | Instante da confirmação, com fuso |
| `pesquisa` | `agendada` \| `ja_agendada` |

`pesquisa` é o desfecho do **registro** da pendência, não da entrega.
`ja_agendada` só na corrida em que outra execução gravou o trabalho no mesmo
instante — o checkout segue válido.

**Erros:**

| Código | Quando | Corpo |
| --- | --- | --- |
| `401` | Sessão ausente ou inválida | `{"detail": "Sessao ausente ou invalida."}` |
| `403` | Perfil não é recepção | `{"detail": "Perfil sem permissao para esta operacao."}` |
| `404` | Reserva inexistente **ou** de outro hotel | `{"detail": "Reserva nao encontrada."}` |
| `409` | Estado não admite (ainda não hospedada, já encerrada, cancelada) | `{"detail": "<motivo legível>"}` |

`404` para outro hotel é deliberado: não distingue “não existe” de “não é
sua”.

**Efeitos de um `200`, na mesma transação:**

1. `reserva.status = 'encerrado'`, `reserva.checkout_em = now()`
2. `mensagem` de saída pendente com o texto da pesquisa **e** `trabalho`
   `enviar_pesquisa_saida` com `{id_reserva, id_mensagem}`

Chamado aberto e consumo pendente **não** alteram esses efeitos.

**Efeitos de `403`, `404` e `409`:** nenhum.

Motivos de `409` (espelho da chegada):

| `status` atual | `detail` |
| --- | --- |
| `encerrado` | `A saida desta reserva ja foi confirmada.` |
| `cancelada` | `Reserva cancelada nao pode ter a saida confirmada.` |
| qualquer não-`hospedado` restante | `A saida so pode ser confirmada depois da entrada.` |

---

## `GET /fila-do-dia` (delta)

Mesma rota e operação `ler_fila_do_dia`. Cada item ganha:

```json
{
  "saida_nao_confirmada": true,
  "pesquisa_saida_leitura_humana": false
}
```

`saida_nao_confirmada` é mutuamente exclusivo de `chegada_nao_confirmada`.
Pode coexistir com `boas_vindas_nao_enviadas`.

Encerrada só aparece na lista se `pesquisa_saida_leitura_humana` for
verdadeiro. Depois da confirmação, `saida_nao_confirmada` é falso (a reserva
deixou de estar hospedada).
