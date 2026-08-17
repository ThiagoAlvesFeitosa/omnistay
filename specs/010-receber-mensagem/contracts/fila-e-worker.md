# Contrato: fila e worker — F3.1

Webhook: [webhook-e-entrada.md](./webhook-e-entrada.md). Modelo:
[data-model.md](../data-model.md).

A fila é a tabela `trabalho` já existente. Nenhum mecanismo paralelo.

---

## Tipo `classificar_mensagem`

```text
enfileirar_classificar_mensagem(
    conexao, *, id_hotel, id_reserva, id_mensagem, id_evento
) -> id_trabalho
```

| Campo | Valor |
| --- | --- |
| `tipo` | `classificar_mensagem` |
| `status` inicial | `pendente` |
| `payload` | `{id_reserva, id_mensagem, id_evento}` — só IDs |
| Unicidade | `uq_trabalho_classificar_mensagem_mensagem` (parcial por `id_mensagem`) |

Segundo INSERT para a mesma `id_mensagem` é recusado pelo banco. A aplicação trata como
já enfileirado — não vaza erro de unicidade ao provedor.

---

## Allowlist de claim

`reclamar_proximo` só considera:

- `enviar_coleta`
- `interpretar_ficha`
- `enviar_lembrete`
- `enviar_boas_vindas`

`classificar_mensagem` **não** entra. Uma passagem do worker (`python -m worker
--uma-passagem`) deixa o item `pendente`, com o mesmo `id_trabalho`.

O consumidor **não** ganha ramo nesta fatia. F3.2 acrescenta o tipo à allowlist e o
despacho no mesmo passo — nunca um dos dois sozinho.

---

## O que o worker desta fatia não faz

- Classificar
- Enviar mensagem
- Marcar `classificar_mensagem` como `concluido` ou `falha`
- Inferir check-in

---

## Reinício

Mensagem em `mensagem` e trabalho `pendente` são linhas de banco. Queda da API ou do
worker não as apaga. Teste observável: webhook → passagem do worker → `SELECT` ainda
`pendente` (não é preciso matar o processo de verdade).

---

## Logs

Eventos permitidos (identificadores, nunca texto):

| Evento | Campos |
| --- | --- |
| `webhook_enfileirado` | `id_evento`, `id_mensagem`, `id_trabalho`, `id_reserva` (já existe; vale para estadia) |
| `webhook_duplicado` | `id_externo` |
| `webhook_sem_reserva` / `webhook_sem_texto` / `webhook_telefone_invalido` | `id_evento`, `id_hotel` |
| `trabalho_claim` | `id_trabalho`, `tipo` — **não** deve aparecer para `classificar_mensagem` nesta fatia |
