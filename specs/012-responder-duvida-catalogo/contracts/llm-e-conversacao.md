# Contrato: LLM e conversação a partir do catálogo

Modelo: [data-model.md](../data-model.md). Catálogo:
[catalogo-na-resposta.md](./catalogo-na-resposta.md). Fila:
[fila-e-worker.md](./fila-e-worker.md).

A conversação **nunca** ocorre na thread HTTP. Só o worker, a partir de
`responder_duvida`. `classificar` **não** gera texto ao hóspede.

---

## Porta `LLMProvider` (delta)

A porta da F1.3 / F3.2 permanece. Esta fatia acrescenta:

```text
responder_duvida(pergunta, itens_ativos) -> ResultadoResposta
```

`ResultadoResposta`:

- `coberta` — se o catálogo dado cobre a pergunta
- `texto` — resposta em linguagem natural; ignorado quando não coberta
- `trechos_citados` — trechos que o redator afirma ter tirado dos itens; o domínio
  valida **depois** da porta

Indisponível, recusa ou tempo esgotado:

```text
raise FalhaDeConversacao(codigo)   # ex.: llm_indisponivel
```

`FalhaDeConversacao` é distinta de `FalhaDeClassificacao` e de `FalhaDeExtracao`.
Código sem eco do texto.

Regras:

- Domínio e worker dependem só da porta.
- Testes usam `LLMFalso` com desfechos configuráveis (coberta fiel, não coberta, não
  fiel, indisponível). **Nenhum teste chama rede.**
- Fidelidade é função pura em `conversa`, **depois** da porta — o adaptador pode
  devolver trechos mentirosos; o domínio recusa.
- Log ao redor da chamada: `id_mensagem` / `id_trabalho` / código — nunca pergunta,
  nunca `texto`, nunca trechos, nunca conteúdo de item.

`extrair_ficha` e `classificar` não são chamados neste tipo de trabalho.
`responder_duvida` não é chamado em `interpretar_ficha` nem em `classificar_mensagem`.

Catálogo vazio: o serviço **não** invoca a porta.

---

## Fidelidade (contrato de validação)

Entrada: `ResultadoResposta` + tupla de `ItemCatalogo` ativos daquele hotel.

| Condição | Efeito |
| --- | --- |
| `coberta is False` | não coberta; `texto` não enviado |
| `coberta is True` e (`texto` vazio ou trechos vazios) | não fiel → não coberta |
| algum trecho, após `strip`/`casefold`, não é substring de `titulo + " " + conteudo` de nenhum item | não fiel → não coberta |
| algum trecho não aparece no `texto` | não fiel → não coberta |
| todos os trechos no catálogo **e** no `texto` | coberta; envia `texto` |

Não existe “resposta parcial”: mistura de fato cadastrado com fato ausente (trecho
órfão) recusa o texto inteiro.

---

## `LLMFalso` (delta)

Configuração **separada** da ficha e da classificação:

- `configurar_resposta(ResultadoResposta)`
- `falhar_conversacao = True` → `FalhaDeConversacao`

Padrão sem configuração: itens vazios → `coberta=False`; senão `coberta=True` com
texto e trechos do primeiro item.

`chamadas_responder` (ou equivalente) registra que foi chamado, **sem** logar a
pergunta.

---

## Proibições da porta neste trabalho

- Persistir por conta própria (só o serviço grava)
- Enviar mensagem (só `MensageriaGateway`)
- Ler catálogo de outro hotel (recebe só os itens já filtrados)
