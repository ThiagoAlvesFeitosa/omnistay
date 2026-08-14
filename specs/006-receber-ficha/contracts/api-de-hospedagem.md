# Contrato: API de hospedagem — acréscimos F1.3

Estende F1.1/F1.2. Autorização: [politica-de-autorizacao.md](./politica-de-autorizacao.md).
Modelo: [data-model.md](../data-model.md).

---

## Convenções

| Tema | Regra |
| --- | --- |
| Consolidação | Feita pelo worker após extração — não por este POST de webhook |
| Cadastro na fila | Campo `estado_cadastro` distingue os quatro desfechos da spec |
| Logs | Sem dados pessoais da ficha |

---

## `GET /fila-do-dia` (campo novo)

**Operação**: `ler_fila_do_dia` (inalterada)

### Saída `200` (item ampliado)

```json
{
  "itens": [
    {
      "id_reserva": 42,
      "nome": "Maria Silva",
      "telefone_contato": "5511987654321",
      "data_checkin_prevista": "2026-08-13",
      "data_checkout_prevista": "2026-08-16",
      "status": "ficha_recebida",
      "ficha_completa": true,
      "chegada_nao_confirmada": false,
      "status_envio_coleta": "enviada",
      "estado_cadastro": "completa"
    }
  ]
}
```

| Campo novo | Valores | Significado |
| --- | --- | --- |
| `estado_cadastro` | `aguardando` · `completa` · `parcial` · `leitura_humana` | Desfecho operacional do cadastro antecipado |

Demais campos: F1.1/F1.2.

---

## `GET /reservas/{id_reserva}/ficha` (nova)

**Operação**: leitura de ficha do titular — apenas **recepção** do hotel da reserva.
Operacional e gestão: `403` (dado cadastral).

### Saída `200`

```json
{
  "id_reserva": 42,
  "id_hospede": 7,
  "ficha_completa": true,
  "status_reserva": "ficha_recebida",
  "estado_cadastro": "completa",
  "nome_completo": "Maria Silva",
  "profissao": "Engenheira",
  "data_nascimento": "1990-05-12",
  "tipo_documento": "rg",
  "numero_documento": "1234567",
  "endereco": "Rua A, 100",
  "cep": "01310100",
  "cidade": "Sao Paulo",
  "telefone": "5511987654321"
}
```

**Proibido no JSON**: qualquer campo `idade` ou equivalente.

### Erros

| Situação | HTTP |
| --- | --- |
| Sem sessão / perfil indevido | `401` / `403` |
| Reserva de outro hotel | `404` (ou `403` alinhado ao padrão multi-tenant existente) |
| Reserva inexistente | `404` |

---

## O que esta API ainda não faz

- Edição manual da ficha no painel
- Botão “copiar para o PMS”
- Check-in / mudança para `hospedado`
