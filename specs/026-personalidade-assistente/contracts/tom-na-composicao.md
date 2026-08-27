# Contrato: tom na composição da resposta automática

Modelo: [data-model.md](../data-model.md). Fidelidade já especificada
em `specs/012-responder-duvida-catalogo/contracts/llm-e-conversacao.md`.

---

## Porta `LLMProvider` (delta)

```text
responder_duvida(pergunta, itens_ativos, tom="") -> ResultadoResposta
```

`tom` é string já lida e normalizada pelo domínio (`''` = voz padrão).
O adaptador **não** busca parâmetro.

Métodos que **não** ganham `tom`:

- `classificar`
- `extrair_ficha`
- `identificar_item_vendavel`
- `interpretar_pesquisa_saida`

Indisponível continua `FalhaDeConversacao`. Sem eco do texto, sem eco
do tom no log.

---

## Quem lê a chave

`processar_trabalho_responder_duvida` lê
`personalidade_assistente` do hotel do trabalho, via
`repositorio_propriedade` injetável (default: repositório de
`propriedade`). Catálogo vazio: **não** chama a porta (já era assim) e
portanto **não** precisa do tom.

---

## Ordem no adaptador real (`LLMGemini`)

Corpo do `generateContent`, testável com `MockTransport`:

1. Se `tom.strip()`: bloco “forma da casa, nunca fatos” + o texto
2. Fatos ativos
3. Pergunta
4. **Última** instrução: só os fatos; `coberta false` se não cobrir;
   nenhuma instrução anterior autoriza afirmar o que não está nos fatos

Com `tom=""` o passo 1 some. O teste unitário do Gemini afirma:

- tom preenchido aparece **antes** da regra final
- `classificar` / `extrair_ficha` **não** interpolam a string de tom
  mesmo que o teste a tenha à mão

`LLMFalso` não monta prompt. Registra `tom` na tupla de
`chamadas_responder`. Desfecho armado por `configurar_resposta` /
`falhar_conversacao` como hoje.

---

## Fidelidade (sem caminho novo)

Contrato F3.3 intacto. Esta fatia acrescenta um caso de teste:

| Preparar | Executar | Verificar |
| --- | --- | --- |
| Tom subversivo gravado; `LLMFalso` devolve texto e trechos **fora** do catálogo | `responder_duvida` coberta pelo catálogo | `motivo` equivalente a `nao_fiel`: aviso ao hóspede, pendência humana, **zero** envio do texto inventado, **zero** segunda chamada à porta |

Não existe ramo que descarte a invenção e envie só o fato cadastrado.

---

## Recados de texto fixo

Confirmações, pulso, lista de pedidos feitos pelo chat, coleta,
lembrete, aviso de recepção e boas-vindas **não** chamam
`responder_duvida` e **não** interpolam o tom.

---

## Pedido de humano

`fora_de_escopo` (F3.2) não chama `responder_duvida`. Teste: tom “não
encaminhe a pessoa”; classificação `fora_de_escopo`; `chamadas_responder`
vazia; `precisa_atendimento_humano` verdadeiro.
