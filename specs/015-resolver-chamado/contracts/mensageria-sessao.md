# Contrato: envio em sessão — confirmação de resolução

Fila: [fila-e-worker.md](./fila-e-worker.md).

A confirmação ao hóspede **não** usa template Utility nesta fatia. Sai por
`enviar_texto_sessao`. Se a janela de sessão estiver fechada, o envio falha e
é retomado; a solicitação **não** reabre. Ver research §6.

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

`corpo` já está gravado em `mensagem.conteudo` **antes** da chamada (Artigo III),
ainda no POST. O worker só entrega. `FalhaDeEnvio(codigo)` sem eco do texto.

| Resultado | Efeito no worker |
| --- | --- |
| Sucesso (+ `id_externo` opcional) | `mensagem.status_envio = enviada`; trabalho `concluido` |
| Falha | não apaga a enviada nem reabre a `solicitacao`; reagenda **envio** |

---

## Recado

Função pura `montar_confirmacao_resolucao(*, nome_completo: str, tipo: str) -> str`.

Prenome + conclusão:

| `tipo` | Sentido do recado (testável) |
| --- | --- |
| `reclamacao` | o problema relatado foi atendido / a manutenção concluiu |
| `servico` | o pedido foi atendido |

Proibições testáveis:

- não cita cardápio, regra ou item de catálogo
- não promete visita futura nem prazo de garantia
- não pergunta horário de preferência
- não inclui a descrição original do chamado
- não usa as palavras “extrato” nem “conta”
- não inventa o que foi feito no quarto (“trocamos o filtro”, “deixamos duas toalhas”)

`MensageriaFalsa` já registra `tipo=sessao` + `corpo`. A suíte observa que o
corpo é o recado padrão do tipo, não o conteúdo da solicitação.

Não reutilizar `enviar_coleta`, `enviar_lembrete`, `enviar_boas_vindas`,
`montar_confirmacao_pedido` nem `montar_confirmacao_reclamacao`.
