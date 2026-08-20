# Contrato — API de consentimento

Sessão válida. Sempre o `id_hotel` da sessão. Finalidade desta fatia:
comunicações futuras (`comunicacao_marketing` no armazenamento).

Hóspede alcançável somente se existir `reserva_hospede` ligado a uma
`reserva` da propriedade da sessão. Caso contrário: `404` uniforme
(`{"detail": "Hospede nao encontrado."}`).

---

## `GET /hospedes/{id_hospede}/consentimento`

Operação: `ler_consentimento` (`recepcao`, `gestor`).

**Query:** `em` (instante ISO-8601, opcional). Ausente = agora.

**Resposta `200`:**

```json
{
  "id_hospede": 7,
  "finalidade": "comunicacao_marketing",
  "concedido": true,
  "momento": "2026-08-20T12:10:00.000Z",
  "origem": "pesquisa_checkout",
  "em": "2026-08-20T15:00:00.000Z"
}
```

Sem registro com `momento <= em`:

```json
{
  "id_hospede": 7,
  "finalidade": "comunicacao_marketing",
  "concedido": false,
  "momento": null,
  "origem": null,
  "em": "2026-03-01T00:00:00.000Z"
}
```

`concedido: false` **sem** `momento` significa ausência — não é recusa
gravada. Recusa gravada traz `momento` e `origem`.

`403` para `staff`. `401` sem sessão.

Esta rota **não** insere linha.

---

## `POST /hospedes/{id_hospede}/consentimento`

Operação: `registrar_consentimento` (`recepcao`, `gestor`).

**Corpo:**

```json
{
  "concedido": false,
  "origem": "solicitacao_titular"
}
```

| Campo | Valores |
| --- | --- |
| `concedido` | booleano obrigatório |
| `origem` | `painel` \| `solicitacao_titular` |

`pesquisa_checkout` **não** é aceita aqui (é só do worker da pesquisa).
Corpo inválido: `422`.

**Resposta `201`:** o registro recém-inserido (mesmos campos do GET, com
`momento` do servidor). Linhas anteriores intactas.

`403` para `staff`. `404` uniforme para outro hotel. Efeitos de erro:
nenhum INSERT.
