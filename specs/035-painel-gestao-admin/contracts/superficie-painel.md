# Contrato: superfície — Painel

Destino `/app/indicadores`. Título **Painel**. Só gestão.
Computador. Sem `compacto`.

Um `GET /indicadores` ao montar. **Tentar de novo** no mesmo GET.
Zero POST.

---

## O que aparece

Quatro números rotulados:

| Rótulo | Campo |
| --- | --- |
| Chegadas hoje | `chegadas_hoje` |
| Hospedados | `hospedados` |
| Chamados em aberto | `chamados_abertos` |
| Consumo a lançar | `consumo_a_lancar` (valor em dinheiro) |

Sem gráfico. Sem fichas antecipadas. Sem nota média. Sem tabela
de reservas, chamados ou consumos. Sem nome de hóspede.

Zeros: estado de “sem movimento”, distinto de falha ao ler.

---

## O que não aparece

Alterar reserva, hóspede, chamado, consumo ou avaliação. Link
para fila do dia, ficha, alertas ou consumos **nesta** tela (o
menu da casca continua o da F8.1 para gestão: catálogo, mercado,
etc. — mas o Painel não lista pessoas).

---

## Falha

GET ilegível / 5xx: aviso de falha; **não** mostrar os quatro
zeros como se a casa estivesse vazia.
