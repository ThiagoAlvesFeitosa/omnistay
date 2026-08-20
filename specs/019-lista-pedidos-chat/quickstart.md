# Quickstart — F4.2 Lista de Pedidos Feitos pelo Chat

Validação ponta a ponta **depois** de `/speckit-implement`. Contratos:
[api-de-saida.md](./contracts/api-de-saida.md),
[api-de-pedidos.md](./contracts/api-de-pedidos.md),
[fila-e-worker.md](./contracts/fila-e-worker.md),
[portas-lista.md](./contracts/portas-lista.md).
Modelo: [data-model.md](./data-model.md).

## Pré-requisitos

- PostgreSQL 16 e `DATABASE_URL`
- Migrações até `0018_lista_pedidos_chat`
- Sem WhatsApp real — `MensageriaFalsa`

```bash
pytest testes/unitarios -q
pytest testes/integracao -q -k "saida or pedidos"
```

## 1. Clique sem consumo cobrável: só a pesquisa

Reserva `hospedado` **sem** consumo (ou só serviço / só dispensado), cookie
de recepção:

```http
POST /reservas/{id}/saida
```

**Esperado:** `200`, `pesquisa=agendada`, `lista=ausente`. Uma linha
`trabalho` `enviar_pesquisa_saida`. **Zero** `enviar_lista_pedidos_chat`.
GET da lista: `200`, `itens: []`, `total: 0`.

## 2. Clique com consumo cobrável: pesquisa e lista, distintas

Mesma reserva com um consumo pendente (bar) e um pedido de toalha:

```http
POST /reservas/{id}/saida
```

**Esperado:** `200`, `lista=agendada`. Dois trabalhos: pesquisa **e**
`enviar_lista_pedidos_chat`. Uma mensagem de lista cujo corpo contém
“pedidos feitos pelo chat”, a descrição e o valor praticado do bar, o
total desses itens, e **não** a toalha. Substrings `extrato` e `conta`
ausentes. Segundo clique: `409`, 0 trabalhos extras.

INSERT manual duplicado do tipo lista: violação de
`uq_trabalho_enviar_lista_pedidos_chat_reserva`.

## 3. Valor histórico

Consumo gravado a 12,00; item vendável reajustado para 20,00; depois o
checkout.

**Esperado:** lista (mensagem e GET) mostra 12,00 — não 20,00.

## 4. Envio, falha e painel

Com o trabalho de lista pendente, `python -m worker --uma-passagem` marca
enviada via falsa (`tipo=lista_pedidos_chat`). Falha da falsa: reserva
permanece `encerrado`; o **mesmo** trabalho é retomado; GET do painel ainda
lista o item.

```http
GET /reservas/{id}/pedidos-feitos-pelo-chat
```

**Esperado:** recepção e gestão `200` com os cobráveis. Staff `403`. Hotel B
no id do hotel A: `404`.

## 5. Dispensado e pendente

Pendente + lançado entram. Dispensado não entra. Lançar depois do envio
**não** gera segunda lista.

## Fora deste guia

Tela React, débito no outro sistema da casa, intenção “me manda o que
pedi” durante a estadia, backfill de reservas já encerradas.
