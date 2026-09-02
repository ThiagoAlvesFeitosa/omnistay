# Contrato: mensageria na resposta da recepção

Porta `MensageriaGateway.enviar_texto_sessao` — a mesma das
outras enviadas em sessão (F3.3, F3.6, etc.).

| | |
| --- | --- |
| Destino | telefone da reserva |
| Corpo | `mensagem.conteudo` já persistido |
| Template / modelo aprovado | **não** |

Falha: `FalhaDeEnvio(codigo)` — nunca o texto no código. Testes
com `MensageriaFalsa`. Demonstração: `MensageriaSimulada` (a
resposta aparece no simulador como as demais).

O adaptador real **não** é chamado na suíte.
