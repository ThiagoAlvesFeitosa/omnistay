# Contrato: API de hospedagem — delta da fila do dia (F3.3)

Autorização: [politica-de-autorizacao.md](./politica-de-autorizacao.md). Modelo:
[data-model.md](../data-model.md).

Nenhuma rota nova. `POST /webhook` não muda. `GET /catalogo` / `GET /catalogo/ativo`
não mudam.

---

## `GET /fila-do-dia`

Já existente; `ler_fila_do_dia`; só recepção. O item **já** inclui
`precisa_atendimento_humano`. Esta fatia só amplia a regra por trás do booleano:

| `precisa_atendimento_humano` | Quando |
| --- | --- |
| `true` | hospedado com mensagem recebida em desfecho `encaminhado_humano`, `formato_invalido`, `indisponivel` **ou `duvida_nao_coberta`** |
| `false` | dúvida coberta (`classificado` + `resposta = automatica`), ou sem pendência humana da F3.2 |

Nenhum campo JSON novo. Gestão e operacional continuam recusados nesta rota.

Dúvida coberta **não** liga o flag. Dúvida não coberta liga **depois** de o aviso
estar gravado no histórico (mesma transação que o desfecho).

---

## Superfícies que esta fatia não cria

- `GET /reservas/{id}/mensagens`
- `POST` de “marcar atendimento humano como visto”
- Rota de `solicitacao` / Alert Center
- Qualquer operação nova na matriz
