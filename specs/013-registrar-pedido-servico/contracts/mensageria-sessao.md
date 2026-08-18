# Contrato: envio em sessão — confirmação de pedido

Fila: [fila-e-worker.md](./fila-e-worker.md).

A confirmação ao hóspede **não** usa template Utility. O hóspede acabou de escrever;
o texto sai na janela de sessão.

---

## Porta `MensageriaGateway`

**Nenhum método novo.** Reutiliza o da F3.3:

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
| Falha | não apaga a enviada nem a `solicitacao`; reagenda **envio** (não o registro) |

---

## Recado

Função pura `montar_confirmacao_pedido(*, nome_completo) -> str`. Prenome +
confirmação de recebimento e de que a equipe vai atender. Proibições testáveis:

- não cita horário, cardápio, regra ou item de catálogo
- não promete prazo (“em 10 minutos”, “ainda hoje”)
- não pergunta janela de preferência
- não inclui o texto original do pedido (o histórico já tem a recebida)

`MensageriaFalsa` já registra `tipo=sessao` + `corpo`. A suíte observa que o corpo
é o recado padrão, não o conteúdo do pedido.

Não reutilizar `enviar_coleta`, `enviar_lembrete` nem `enviar_boas_vindas`.
