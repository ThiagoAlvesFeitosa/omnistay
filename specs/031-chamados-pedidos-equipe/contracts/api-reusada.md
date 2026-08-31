# Contrato: API reusada (F8.4)

Nenhuma rota nova. Nenhuma mudança de schema. As telas são clientes
das operações abaixo. Detalhe HTTP original: F3.4–F3.7 e F8.3.

Autenticação: cookie `omnistay_sessao` via `credentials: "include"`.
Hotel: só o da sessão. A tela **não** envia `id_hotel`.

---

## `GET /solicitacoes`

Operação `ler_solicitacao_atribuida` (`recepcao`, `staff`, `gestor`).
Esta fatia só dispara o GET nas telas de recepção e de staff.

**200** — a tela lê de cada item, nesta ordem de array (já
`aberta_em` crescente):

`id_solicitacao`, `id_reserva`, `tipo`, `descricao`, `numero_quarto`,
`urgencia`, `janela_preferencia`, `status`, `aberta_em`,
`destaque_tempo_excedido`, `valor_praticado`, `status_lancamento`.

`itens: []` é lista vazia, não erro.

O JSON **não** traz nome, telefone, documento, endereço.

**401** — a casca trata (volta à entrada).

A tela não envia query nem corpo. **Não** reordena `itens`.

---

## `POST /solicitacoes/{id_solicitacao}/resolucao`

Operação `resolver_solicitacao` (`recepcao`, `staff`). Corpo vazio.

Disparado **somente** pelo botão rotulado **Resolvido**.

| Código | Efeito na tela |
| --- | --- |
| `200` | `GET /solicitacoes` de novo. O id some. Confirmação ao hóspede já foi agendada no servidor |
| `409` | Motivo visível (já resolvida, estado inadmissível, etc.); `GET` de novo; não afirmar resolvido |
| `404` | Sumiu ou é de outro hotel — recado genérico da API; `GET` de novo |
| `401` | Casca |
| `403` | Não ocorre na recepção/staff autenticados; gestão não monta a tela |

A tela **não** chama `POST .../lancamento`, `.../dispensa`,
`GET /consumos/pendentes`, nem `PUT` de ficha a partir desta lista.

---

## `GET /reservas/{id}/ficha` (só depois de navegar)

Operação `ler_dado_cadastral_de_hospede` (só `recepcao`). A lista
de chamados **não** busca ficha. Só `TelaFicha` após **Ver ficha**.

Staff: a casca não monta `TelaFicha`; zero GET.

---

## O que esta fatia não altera no HTTP

- Campos do item de `GET /solicitacoes`
- Recado de confirmação ao hóspede
- Cálculo de `destaque_tempo_excedido`
- `ORDER BY aberta_em`
- Matriz de `politica.py`
- Worker / fila de `enviar_confirmacao_resolucao`
