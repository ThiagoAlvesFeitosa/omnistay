# Contrato: API reusada (F8.3)

Autenticação: cookie `omnistay_sessao` via `credentials: "include"`.
Hotel: só o da sessão. A tela **não** envia `id_hotel`.

Detalhe HTTP original: F1.3 (`GET` da ficha) e F4.1 (consentimento).
Esta fatia **não** muda o JSON de leitura.

---

## `GET /reservas/{id_reserva}/ficha`

Operação `ler_ficha_de_hospede` (só `recepcao`).

**200** — a tela lê: `id_reserva`, `id_hospede`, `ficha_completa`,
`status_reserva`, `estado_cadastro`, e os nove campos. Sem `idade`.

**401** — a casca trata (volta à entrada).

**403** — `staff` / `gestor`; a casca não monta esta tela para eles.

**404** — reserva inexistente ou de outro hotel (recado genérico).

A tela não envia query nem corpo.

---

## `GET /hospedes/{id_hospede}/consentimento`

Operação `ler_consentimento` (`recepcao`, `gestor`). Nesta fatia só a
recepção chama, depois de ter `id_hospede` da ficha. Sem query `em`
(vigente = agora).

A tela distingue: aceite com data; recusa com data; `concedido: false`
sem `momento` = nunca registrado.

**403** para staff. **404** uniforme se o hóspede não é da casa.

---

## `POST /hospedes/{id_hospede}/consentimento`

Operação `registrar_consentimento` (`recepcao`, `gestor`). Nesta fatia
só a recepção, origem **sempre** `painel`.

```json
{ "concedido": false, "origem": "painel" }
```

`concedido: true` registra aceite no balcão. `pesquisa_checkout` não
é aceita aqui (`422`).

**201** — vigente novo; histórico intacto. A tela refaz o GET (ou
usa o corpo do 201) e não dispara mensagem.

---

## O que esta fatia não chama

- `POST /reservas/{id}/chegada` e `.../saida`
- Webhook, simulador, catálogo, solicitações
- Qualquer URL de sistema de gestão do hotel
