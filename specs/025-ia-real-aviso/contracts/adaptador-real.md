# Contrato: adaptador real da porta `LLMProvider`

Porta: `app/portas/llm.py` (**sem** método novo). Fábrica:
[modo-e-fabrica-llm.md](./modo-e-fabrica-llm.md). Log:
[logs-e-segredo.md](./logs-e-segredo.md).

A suíte **não** chama o host do serviço. Testes injetam `httpx.Client`
com transportador falso.

---

## Transporte

```text
POST https://generativelanguage.googleapis.com/v1beta/models/{LLM_MODELO}:generateContent
Header: x-goog-api-key: <GEMINI_API_KEY>
Header: Content-Type: application/json
Timeout: LLM_TIMEOUT_SECONDS
```

Chave **não** vai na query. `response_mime_type`: `application/json`.

Um POST por invocação de método da porta. Sem lote, sem stream.

---

## Métodos e JSON esperado

O adaptador extrai o texto da primeira parte do candidato e faz
`json.loads`. Campos ausentes viram `None` / vazio; o **domínio** valida
taxonomia e fidelidade.

### `extrair_ficha(texto) → ResultadoExtracao`

JSON: `desfecho` (`completa` \| `parcial` \| `irreconhecivel`) e
`campos` (mapa; chaves só as da ficha; **sem** `idade`).

Prioridade de prompt: demonstração.

### `classificar(texto) → ResultadoClassificacao`

JSON: `intencao`, `sentimento`, `urgencia` (strings da taxonomia da
F3.2). `bruto` = o objeto parseado (auditoria na mensagem, **não** no
log).

Prioridade de prompt: demonstração.

### `responder_duvida(pergunta, itens_ativos) → ResultadoResposta`

JSON: `coberta` (bool), `texto` (string ou nulo), `trechos_citados`
(lista de strings). O adaptador **não** filtra fidelidade — o serviço de
conversa já recusa trecho órfão.

`itens_ativos` entram no prompt como fatos da **daquela** propriedade.
Catálogo vazio: o domínio **não** chama a porta (F3.3).

Prioridade de prompt: demonstração.

### `identificar_item_vendavel(texto, itens_ativos) → ResultadoIdentificacao`

JSON: `desfecho` (`unico` \| `nenhum` \| `ambiguo`),
`id_item_vendavel` (int ou nulo), `quantidade` (int ou nulo).

Prompt pode ser mais simples. Falha de transporte → `FalhaDeIdentificacao`.

### `interpretar_pesquisa_saida(texto) → ResultadoPesquisaSaida`

JSON: `desfecho` (`completo` \| `parcial` \| `irreconhecivel`), `nota`,
`comentario`, `aceite`.

Prompt pode ser mais simples. Falha de transporte → `FalhaDeExtracao`
(o domínio da pesquisa já trata essa exceção).

---

## Falhas de transporte

| HTTP / cliente | Exceção do método chamado | `codigo` |
| --- | --- | --- |
| Timeout | `FalhaDeClassificacao` / `FalhaDeConversacao` / `FalhaDeExtracao` / `FalhaDeIdentificacao` conforme o método | `llm_tempo_esgotado` |
| Rede, 5xx, resposta vazia | idem | `llm_indisponivel` |
| 401, 403 | idem | `llm_recusa` |
| 429 | idem | `llm_quota` |
| Corpo não-JSON ou sem candidato | idem | `llm_formato_invalido` |

`codigo` nunca ecoa o texto do hóspede nem a chave.

JSON bem formado com valor fora da taxonomia: **não** é exceção da
porta; devolve `Resultado*` e o domínio marca `formato_invalido`.

---

## Proibições

- Importar SDK Google
- Logar prompt, resposta, chave ou `texto`
- Consultar catálogo por conta própria (só usa a tupla recebida)
- Persistir (só o serviço grava)
- Retry interno contra o serviço (a primeira falha escala, já no domínio)
- Chamar a porta a partir do router HTTP
