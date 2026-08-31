# Contrato: resumo do turno

Função pura sobre `itens` de `GET /fila-do-dia`. Sem chamada HTTP
própria. Teste em `fila.test.ts`, sem DOM.

---

## Partição

Cada item entra em **exatamente uma** conta. A soma das três é
`itens.length`.

```text
hospedados          = count(status === "hospedado")
entrada_vencida     = count(chegada_nao_confirmada === true)
hoje_sem_confirmar  = count(status !== "hospedado"
                            && chegada_nao_confirmada === false)
```

Invariante já do backend: `hospedado` ⇒ `chegada_nao_confirmada === false`.
Logo `hospedados ∩ entrada_vencida = ∅`.

---

## Rótulos na tela

Linguagem da spec, não nomes de coluna:

| Conta | Texto visível (sentido) |
| --- | --- |
| `hoje_sem_confirmar` | chegadas de hoje ainda não confirmadas |
| `hospedados` | já hospedados |
| `entrada_vencida` | entrada vencida sem confirmação |

Hospedado com recado não enviado conta em **hospedados**, não em
entrada vencida.

---

## Estados especiais

| Entrada | Resumo |
| --- | --- |
| `itens: []` | 0, 0, 0 — só neste caso o zero significa turno vazio |
| Falha de `GET` | **não** renderizar este resumo como 0, 0, 0 |
| Ainda carregando | **não** tratar como turno vazio |

---

## O que este contrato não é

`GET /indicadores/chegadas-do-dia` conta outro recorte (entrada
prevista = hoje, inclusive já hospedado, sem isolado de vencida).
Não alimentar o topo da fila com esse número.
