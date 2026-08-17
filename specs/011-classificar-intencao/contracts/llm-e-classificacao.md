# Contrato: LLM e classificação de intenção

Modelo: [data-model.md](../data-model.md). Fila: [fila-e-worker.md](./fila-e-worker.md).

A classificação **nunca** ocorre na thread HTTP. Só o worker, a partir de
`classificar_mensagem`.

---

## Porta `LLMProvider` (delta)

A porta da F1.3 permanece. Esta fatia acrescenta:

```text
classificar(texto) -> ResultadoClassificacao
```

`ResultadoClassificacao`:

- `intencao`, `sentimento`, `urgencia` — strings, podem ser vazias ou fora da taxonomia
- `bruto` — mapeamento da resposta completa (auditoria); **não** é o texto do hóspede
  copiado pela aplicação

Indisponível, recusa ou tempo esgotado:

```text
raise FalhaDeClassificacao(codigo)   # ex.: llm_indisponivel
```

`FalhaDeClassificacao` é distinta de `FalhaDeExtracao`. Código sem eco do texto.

Regras:

- Domínio e worker dependem só da porta.
- Testes usam `LLMFalso` com desfechos configuráveis (sucesso por intenção, inválido,
  indisponível). **Nenhum teste chama rede.**
- Validação da taxonomia é função pura em `conversa`, **depois** da porta.
- Log ao redor da chamada: `id_mensagem` / `id_trabalho` / código — nunca `texto`,
  nunca `bruto`.

`extrair_ficha` não é chamado neste tipo de trabalho. `classificar` não é chamado em
`interpretar_ficha`.

---

## Taxonomia (contrato de validação)

Intenção aceita:

`duvida_geral` · `pedido_de_servico` · `reclamacao_tecnica` · `upsell` ·
`solicitacao_de_checkout` · `fora_de_escopo`

Sentimento: `positivo` · `neutro` · `negativo`

Urgência: `baixa` · `media` · `alta`

Os três eixos obrigatórios. Qualquer omissão ou valor fora → `formato_invalido`.

Ramos **desta** fatia (depois de válida):

| Intenção | Desfecho gravado | Efeito extra |
| --- | --- | --- |
| `duvida_geral`, `pedido_de_servico`, `reclamacao_tecnica` | `classificado` | nenhum (F3.3–F3.5 executam depois) |
| `upsell`, `solicitacao_de_checkout`, `fora_de_escopo` | `encaminhado_humano` | sinal na fila do dia |

---

## Proibições da porta neste trabalho

- Consultar catálogo
- Gerar texto de resposta ao hóspede
- Persistir por conta própria (só o serviço grava)
