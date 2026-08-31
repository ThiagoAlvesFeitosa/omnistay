# Contrato: API reusada (F8.2)

Nenhuma rota nova. Nenhuma mudança de schema. A tela é cliente das
três operações abaixo. Detalhe HTTP original: F1.1 e F2.2.

Autenticação: cookie `omnistay_sessao` via `credentials: "include"`.
Hotel: só o da sessão. A tela **não** envia `id_hotel`.

---

## `GET /fila-do-dia`

Operação `ler_fila_do_dia` (só `recepcao`).

**200** — a tela lê de cada item:

`id_reserva`, `nome`, `telefone_contato`, `data_checkin_prevista`,
`data_checkout_prevista`, `status`, `estado_cadastro`,
`chegada_nao_confirmada`, `boas_vindas_nao_enviadas`.

`itens: []` é turno vazio, não erro.

**401** — a casca trata (volta à entrada).

**403** — `staff` / `gestor`; a casca não monta esta tela para eles.

A tela não envia query nem corpo.

---

## `POST /reservas`

Operação `alterar_reserva` (só `recepcao`).

**Corpo** (só estes campos):

```json
{
  "nome": "Marina Duarte",
  "telefone": "(11) 98765-4321",
  "data_checkin_prevista": "2026-08-31",
  "data_checkout_prevista": "2026-09-02"
}
```

Sem `email`. Datas ISO `YYYY-MM-DD`. Telefone com máscara aceita;
o servidor devolve canônico.

| Código | Efeito na tela |
| --- | --- |
| `201` | Depois, `GET /fila-do-dia`. Se `id_reserva` está em `itens`, a linha é do turno; senão, aviso de entrada futura |
| `422` | Mensagem do campo; nada na lista |
| `401` / `403` | Casca / não ocorre na recepção autenticada |

---

## `POST /reservas/{id_reserva}/chegada`

Operação `confirmar_fase_da_reserva` (só `recepcao`). Corpo vazio.

Disparado **somente** pelo botão rotulado, e somente se
`status ∈ {ficha_recebida, ficha_parcial, sem_cadastro_previo}`.

| Código | Efeito na tela |
| --- | --- |
| `200` | `GET /fila-do-dia` de novo. Linha vira `hospedado`; `chegada_nao_confirmada` some; `boas_vindas_nao_enviadas` pode passar a `true` |
| `409` | Motivo visível; `GET` de novo; não afirmar hospedado |
| `404` | Reserva sumiu ou é de outro hotel — mesmo recado genérico da API; `GET` de novo |
| `401` | Casca |

A tela **não** chama `POST /reservas/{id}/saida`, ficha, nem
`PUT /propriedade/boas-vindas`.

---

## O que esta fatia não altera no HTTP

- Forma canônica do telefone
- Máquina de estados
- Campos extras em `ItemFilaDoDia`
- `GET /indicadores/chegadas-do-dia` (não entra no resumo)
