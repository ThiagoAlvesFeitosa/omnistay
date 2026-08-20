# Contrato — fila, worker (delta F4.2)

## Tipo novo em `trabalho`

Incluído no `CHECK` e na allowlist de `reclamar_proximo` **na mesma
revisão** (`0018`). Consumir um tipo que o CHECK ainda não aceita, ou
aceitar no CHECK sem consumir, quebra o padrão das F3.1–F4.1.

| Tipo | Unicidade | Quem enfileira | Quem processa |
| --- | --- | --- | --- |
| `enviar_lista_pedidos_chat` | parcial por `id_reserva` | `hospedagem.confirmar_saida` → `atendimento.listar` (não vazio) → `conversa.agendar_lista_pedidos_chat` | `conversa.processar_trabalho_enviar_lista_pedidos_chat` |

`--uma-passagem` consome o tipo novo (é fila, não calendário). Nenhuma
flag nova no agendador. Recorte vazio: **não** enfileira.

Payload sem dado pessoal: só identificadores.

## Envio

Processador lê telefone da reserva, chama
`MensageriaGateway.enviar_lista_pedidos_chat` com o corpo **já gravado**,
espelha `status_envio`. Falha (`FalhaDeEnvio`): reagenda o mesmo id;
**não** reabre `encerrado`. Sucesso: `concluido`. Índice impede segundo
trabalho distinto.

## Webhook

**Intocado.** A lista não pede resposta. Não nasce
`classificar_mensagem` nem `interpretar_pesquisa_saida` por causa da
lista. Contestação escrita segue o roteamento da F4.1.

## Allowlist

Os testes da F4.1 que listam tipos consumíveis são **estendidos**, não
revertidos: `enviar_lista_pedidos_chat` passa a ser reclamável. Tipos de
estadia e da pesquisa continuam como estão.

Testes da F4.1 de `POST /saida` **sem** consumo cobrável continuam com
exatamente um `enviar_pesquisa_saida`. Com consumo cobrável, o mesmo
clique passa a gerar também `enviar_lista_pedidos_chat` — isso é a
fatia, não regressão.
