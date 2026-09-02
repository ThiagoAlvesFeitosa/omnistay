# Contrato: fila e worker

Mensageria: [mensageria-sessao.md](./mensageria-sessao.md).

A fila é a tabela `trabalho`. O POST **não** espera o worker para
responder `201`.

---

## Allowlist

`reclamar_proximo` passa a incluir **`enviar_resposta_recepcao`**.

Uma passagem (`python -m worker --uma-passagem`) reclama o item.
Allowlist e ramo no consumidor mudam juntos.

---

## Enfileirar (a partir do POST)

O serviço de conversa, na mesma transação do INSERT da enviada:

```text
enfileirar_enviar_resposta_recepcao(
  id_hotel, id_reserva, id_mensagem
)
```

| Campo | Valor |
| --- | --- |
| `tipo` | `enviar_resposta_recepcao` |
| `payload` | `{id_reserva, id_mensagem}` |
| Unicidade | `uq_trabalho_enviar_resposta_recepcao_mensagem` |

---

## Processar

1. Ler `conteudo` da `mensagem` `id_mensagem` (já gravado).
2. `enviar_texto_sessao` com telefone da reserva.
3. Sucesso: `status_envio = enviada`, trabalho `concluido`.
4. Falha de canal: `registrar_falha_de_envio` (retry da fila);
   se a fila for para `falha`, `status_envio = falha`.
5. Sem telefone: `falha` / `telefone_ausente` — texto permanece.

O processador **não** altera `solicitacao`. **Não** monta recado
padrão. **Não** lê o texto do POST de novo.

---

## Retry visível

Enquanto o trabalho retenta, a mensagem continua `pendente` ou
passa a `falha` no esgotamento. Recarregar a Estadia mostra o
estado. A recepção **não** redige de novo para o mesmo
`id_mensagem`.
