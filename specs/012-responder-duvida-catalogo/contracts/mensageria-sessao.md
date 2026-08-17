# Contrato: envio em sessão (resposta automática e aviso)

Fila: [fila-e-worker.md](./fila-e-worker.md).

A resposta ao hóspede nesta fatia **não** usa template Utility. O hóspede acabou de
escrever; o texto sai na janela de sessão.

---

## Porta `MensageriaGateway` (delta)

Método novo; os três templates da F1.2 / F1.4 / F2.2 permanecem.

```text
enviar_texto_sessao(
  telefone_destino,
  corpo,
  id_mensagem,
  id_reserva,
) -> ResultadoEnvio
```

`corpo` já está gravado em `mensagem.conteudo` **antes** da chamada (Artigo III).
`FalhaDeEnvio(codigo)` sem eco do texto.

| Resultado | Efeito no worker |
| --- | --- |
| Sucesso (+ `id_externo` opcional) | `mensagem.status_envio = enviada`; trabalho `concluido` |
| Falha | não apaga a enviada; reagenda **envio** (não a conversação) |

---

## Implementações

| Adaptador | Comportamento |
| --- | --- |
| `MensageriaFalsa` | registra `tipo=sessao` e `corpo`; suíte observa o texto |
| WhatsApp Cloud | `type: text` com o corpo; **nenhum teste instancia** |

Não reutilizar `enviar_coleta`, `enviar_lembrete` nem `enviar_boas_vindas`.

Log ao redor: `id_mensagem` / `id_reserva` / código de falha — nunca `corpo`, nunca
telefone em claro como conteúdo principal do evento (o destino canônico já é dado
operacional da reserva; o log desta fatia não o repete).

---

## Fora desta fatia

- Template novo aprovado na Meta
- Reabrir conversa fora da janela de 24h
- Webhook de status `entregue`
