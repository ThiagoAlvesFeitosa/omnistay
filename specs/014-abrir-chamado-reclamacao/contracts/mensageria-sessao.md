# Contrato: envio em sessão — confirmação de reclamação

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

Função pura `montar_confirmacao_reclamacao(*, nome_completo, perguntar_horario: bool) -> str`.

Prenome + confirmação de que a mensagem foi recebida e de que a manutenção está
sendo acionada. Se `perguntar_horario` é verdadeiro, o **mesmo** recado pergunta
o horário de preferência para o atendimento. Proibições testáveis:

- não cita cardápio, regra ou item de catálogo
- não promete prazo de conserto (“em 10 minutos”, “ainda hoje o técnico vai”)
- não pergunta horário quando `perguntar_horario` é falso (janela já extraída)
- não inclui o texto original da reclamação (o histórico já tem a recebida)

`MensageriaFalsa` já registra `tipo=sessao` + `corpo`. A suíte observa que o corpo
é o recado padrão, não o conteúdo da reclamação.

Completar a janela depois **não** chama a porta.

Não reutilizar `enviar_coleta`, `enviar_lembrete`, `enviar_boas_vindas` nem
`montar_confirmacao_pedido`.
