# Contrato: API reusada (F8.5)

Nenhuma rota nova. Nenhuma mudança de schema. As telas são clientes
das operações abaixo. Detalhe HTTP original: F3.7, F4.1, F4.2, F8.3.

Autenticação: cookie `omnistay_sessao` via `credentials: "include"`.
Hotel: só o da sessão. A tela **não** envia `id_hotel`.

---

## `GET /consumos/pendentes`

Operação `ler_solicitacao_atribuida` (`recepcao`, `staff`, `gestor`).
Esta fatia só dispara o GET na recepção (Consumos a lançar e o
aviso da saída).

**200** — a tela lê de cada item, nesta ordem de array (já
`aberta_em` crescente):

`id_solicitacao`, `id_reserva`, `descricao_item`, `numero_quarto`,
`valor_praticado`, `status_lancamento`, `aberta_em`.

`itens: []` é lista vazia, não erro.

O JSON **não** traz nome, telefone, documento, endereço.

A tela não envia query nem corpo. **Não** reordena `itens`. **Não**
filtra por reserva nesta lista (o recorte da estadia é só o aviso
em `TelaSaida`).

---

## `POST /solicitacoes/{id_solicitacao}/lancamento`

Operação `lancar_consumo` (só `recepcao`). Corpo vazio.

Disparado **somente** pelo botão **Marcar lançado**.

| Código | Efeito na tela |
| --- | --- |
| `200` | `GET /consumos/pendentes` de novo. O id some. Zero recado ao hóspede |
| `409` | Motivo visível (`Este consumo ja foi lancado.` / `... dispensado.`); `GET` de novo |
| `404` | Sumiu ou é de outro hotel — recado genérico da API; `GET` de novo |
| `401` | Casca |
| `403` | Não ocorre na recepção autenticada; staff/gestão não montam a tela |

---

## `POST /solicitacoes/{id_solicitacao}/dispensa`

A mesma operação `lancar_consumo`. Corpo vazio.

Disparado **somente** pelo botão **Dispensar**.

Códigos iguais ao lançamento. `200` tira da fila e do recorte
cobrável da saída. **Não** consta como lançado. Zero recado ao
hóspede.

---

## `GET /reservas/{id_reserva}/pedidos-feitos-pelo-chat`

Operação `ler_pedidos_feitos_pelo_chat` (`recepcao`, `gestor`).
Só a recepção dispara nesta fatia.

**200** — `itens[]` com `descricao_item` e `valor_praticado`;
`total` do envelope. Sem `status_lancamento`. Sem nome.

`itens: []` é lista vazia honesta na saída.

**404** — reserva inexistente ou de outro hotel. Recado genérico.

A tela **não** pede status por item e **não** soma por conta
própria quando o envelope já traz `total`.

---

## `POST /reservas/{id_reserva}/saida`

Operação `confirmar_fase_da_reserva` (só `recepcao`). Corpo vazio.

Disparado **somente** pelo botão **Confirmar saída** em
`TelaSaida`, e só se a ficha disser `status_reserva === hospedado`.

| Código | Efeito na tela |
| --- | --- |
| `200` | Estadia encerrada; botão some; pesquisa/lista ao hóspede já agendadas no servidor |
| `409` | Motivo visível; não afirma encerrado |
| `404` | Recado genérico |
| `401` | Casca |

Consumo pendente **não** muda esses códigos — o aviso não trava.

A fila do dia **não** dispara este POST.

---

## `GET /reservas/{id}/ficha`

Operação `ler_dado_cadastral_de_hospede` (só `recepcao`). Só
`TelaSaida` com id (nome + status) e `TelaFicha` após **Ver ficha**.
A lista financeira **não** busca ficha até a navegação.

---

## `GET /fila-do-dia`

Operação `ler_fila_do_dia`. A tela passa a **usar**
`saida_nao_confirmada` (já no JSON). Datas da estadia na saída, se
o id ainda estiver nos itens.

---

## O que esta fatia não altera no HTTP

- Campos dos itens de pendentes, pedidos, ficha e fila
- Recado de pesquisa e de lista ao hóspede
- `ORDER BY aberta_em` dos pendentes
- Matriz de `politica.py`
- Worker / fila de `enviar_pesquisa_saida` e
  `enviar_lista_pedidos_chat`
