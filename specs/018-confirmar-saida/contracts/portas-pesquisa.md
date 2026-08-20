# Contrato — portas da pesquisa de saída

Nenhum teste instancia adaptador real (Meta ou provedor de IA).

---

## `MensageriaGateway.enviar_pesquisa_saida`

Assinatura no espírito de `enviar_pulso`:

- `telefone_destino`, `primeiro_nome`, `corpo`, `id_mensagem`, `id_reserva`
- sucesso → `ResultadoEnvio`
- falha → `FalhaDeEnvio(codigo)` sem eco do corpo

`MensageriaFalsa` registra `tipo=pesquisa_saida` (distinto de pulso,
boas-vindas e sessão). Teste de falha não ecoa o texto.

A ida **não** usa `enviar_texto_sessao`. Não há recado de agradecimento.

---

## `LLMProvider.interpretar_pesquisa_saida`

```text
interpretar_pesquisa_saida(texto) -> ResultadoPesquisaSaida
```

| Campo | Significado |
| --- | --- |
| `desfecho` | `completo` \| `parcial` \| `irreconhecivel` |
| `nota` | inteiro 1–5 ou nulo |
| `comentario` | texto ou nulo |
| `aceite` | `true` / `false` / nulo (não respondeu à pergunta) |

Porta caída → `FalhaDeExtracao(codigo)`, sem eco do texto. O domínio:

- descarta `nota` fora de 1–5
- **não** promove `aceite` nulo a falso
- **não** promove nota alta a aceite
- trata `FalhaDeExtracao` e desfecho `irreconhecivel` como leitura humana

`LLMFalso` devolve o fixture configurado pelo teste (completo, só nota, só
aceite, irreconhecível, ou levanta `FalhaDeExtracao`).

---

## Texto da pesquisa (domínio `conversa`)

Lista numerada de três itens, uma mensagem:

1. nota de 1 a 5
2. comentário, se quiser (opcional)
3. pergunta final específica: aceita receber comunicações futuras? sim ou não

Único dado pessoal: primeiro nome. Recusado no aceite do texto: as palavras
`extrato` e `conta`, oferta, desconto, convite de retorno, lista de pedidos
feitos pelo chat. Teste unitário inspeciona o corpo montado.
