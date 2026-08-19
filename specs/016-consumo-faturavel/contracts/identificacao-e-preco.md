# Contrato: identificação e preço

Porta: `LLMProvider.identificar_item_vendavel`. O domínio valida o resultado
e **lê o preço no banco depois**. Suíte: `LLMFalso`, sem rede.

---

## Entrada

```text
identificar_item_vendavel(texto: str, itens_ativos: tuple[(id, nome), ...])
```

- `texto` é o conteúdo da mensagem recebida — a porta **não** loga
- `itens_ativos` só do `id_hotel` da reserva, `ativo = TRUE`, **sem**
  `preco_atual`
- Lista vazia: o serviço **não** chama a porta; trata como `nenhum`

---

## Saída válida

| `desfecho` | `id_item_vendavel` | `quantidade` | Efeito no domínio |
| --- | --- | --- | --- |
| `unico` | id ∈ `itens_ativos` | inteiro >= 1 | consumo com `preco_atual * quantidade` |
| `nenhum` | nulo | ignorado | serviço operacional (F3.4) |
| `ambiguo` | nulo | ignorado | humano, sem consumo |

Qualquer outro formato (id fora da tupla, quantidade < 1, dois ids, string no
lugar do id, `unico` sem id) → `FalhaDeIdentificacao` → mesmo tratamento de
indisponível.

`FalhaDeIdentificacao(codigo)` não ecoa o texto. Códigos estáveis para teste:
`indisponivel`, `tempo_esgotado`, `recusa`.

---

## Preço (fora da porta)

Na mesma transação, **depois** de `unico`:

```text
valor_praticado = item.preco_atual * quantidade
```

`preco_atual` é `NUMERIC`, nunca `float`. Reajuste de `item_vendavel` **depois**
do commit não altera `consumo.valor_praticado`.

A confirmação ao hóspede usa **esse** `valor_praticado`, não uma segunda leitura
e não um número devolvido pelo modelo.

Item desativado entre a listagem e o INSERT: o `id` deixa de estar na tupla da
próxima execução; nesta transação, se a linha ainda estiver visível e ativa no
`SELECT` de preço, vale o snapshot. Se o `SELECT` de preço não achar linha
ativa, tratar como humano — não inventar preço e não cair em toalha.

---

## Falso da suíte

Configurável por teste: `unico` (id + quantidade), `nenhum`, `ambiguo`, ou
levantar `FalhaDeIdentificacao`. Padrão da suíte **não** deve casar item
vendável por acidente nos testes da F3.4 (toalha): propriedade sem item ativo
→ porta não chamada.

---

## Fora deste contrato

- O modelo devolver `valor`
- Itens de outro hotel no prompt
- Vários ids distintos como `unico` (isso é `ambiguo`)
- Busca por palavra-chave no lugar da porta
