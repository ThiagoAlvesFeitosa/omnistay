# Contrato — portas da lista de pedidos feitos pelo chat

Nenhum teste instancia adaptador real (Meta). Não há método novo no
`LLMProvider`.

---

## `MensageriaGateway.enviar_lista_pedidos_chat`

Assinatura no espírito de `enviar_pesquisa_saida`:

- `telefone_destino`, `primeiro_nome`, `corpo`, `id_mensagem`, `id_reserva`
- sucesso → `ResultadoEnvio`
- falha → `FalhaDeEnvio(codigo)` sem eco do corpo

`MensageriaFalsa` registra `tipo=lista_pedidos_chat` (distinto de
pesquisa de saída, pulso, boas-vindas e sessão). Teste de falha não ecoa
o texto.

A ida **não** usa `enviar_texto_sessao`. Não há recado de correção, de
agradecimento nem de “está correto?”.

Adaptador WhatsApp declara o método (como os demais) e nenhum teste o
instancia.

---

## Texto da lista (domínio `conversa`)

Montagem pura a partir do prenome e da sequência
`(descricao_item, valor_praticado)`. Formato de moeda idêntico ao da
confirmação de consumo (`R$ 12,00`).

O corpo MUST:

1. Usar o rótulo **pedidos feitos pelo chat**
2. Listar cada item cobrável com descrição e valor praticado
3. Incluir `Total dos pedidos feitos pelo chat` com a soma desses itens
4. Deixar explícito que a lista cobre somente o que foi pedido pelo chat
5. Usar no máximo o primeiro nome como dado pessoal

O corpo MUST NOT:

- conter as substrings `extrato` ou `conta` (qualquer capitalização)
- perguntar se os itens estão corretos
- convidar a pagar por aquele canal
- citar oferta, desconto ou retorno
- incluir serviço sem cobrança ou consumo dispensado
- incluir `solicitacao.descricao` (texto do hóspede)

Teste unitário inspeciona o corpo montado — inclusive a recusa das
palavras proibidas e a presença do rótulo e da frase de alcance.

---

## Log

Eventos `lista_pedidos_agendada`, `lista_pedidos_ausente`,
`lista_pedidos_enviada`, `envio_tentativa_falhou` com ids, hotel,
contagem de itens quando couber. Nunca corpo, nunca descrição de item,
nunca valor por extenso.
