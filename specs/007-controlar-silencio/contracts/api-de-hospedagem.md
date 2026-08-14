# Contrato: API de hospedagem — acréscimos F1.4

Estende F1.1–F1.3. Autorização: [politica-de-autorizacao.md](./politica-de-autorizacao.md).
Modelo: [data-model.md](../data-model.md).

Não há endpoint novo. A verificação de silêncio não é HTTP.

---

## Convenções

| Tema | Regra |
| --- | --- |
| Lembrete / marcação | Feitos pelo agendador + worker — não por `POST /reservas` nem pelo webhook |
| Cadastro na fila | `estado_cadastro` passa a incluir `sem_cadastro_previo` |
| Logs | Sem dados pessoais |

---

## `GET /fila-do-dia` (vocabulário ampliado)

**Operação**: `ler_fila_do_dia` (inalterada)

### Saída `200` — item com silêncio persistente

```json
{
  "itens": [
    {
      "id_reserva": 42,
      "nome": "Maria Silva",
      "telefone_contato": "5511987654321",
      "data_checkin_prevista": "2026-08-16",
      "data_checkout_prevista": "2026-08-18",
      "status": "sem_cadastro_previo",
      "ficha_completa": false,
      "chegada_nao_confirmada": false,
      "status_envio_coleta": "enviada",
      "estado_cadastro": "sem_cadastro_previo"
    }
  ]
}
```

| Campo | Valores desta fatia | Significado |
| --- | --- | --- |
| `status` | passa a aparecer `sem_cadastro_previo` | Ciclo de vida |
| `estado_cadastro` | `aguardando` · `completa` · `parcial` · `leitura_humana` · **`sem_cadastro_previo`** | Desfecho operacional |

Demais campos: F1.1–F1.3.

---

## `GET /reservas/{id_reserva}/ficha`

Inalterado. Reserva em `sem_cadastro_previo` continua titular provisório (`ficha_completa`
falso); recepção lê o que houver. Operacional/gestão: `403`.

---

## O que esta API ainda não faz

- Confirmar check-in / `hospedado` (F2.2) — a transição **é permitida** no banco
- Editar prazos da propriedade
- Disparar lembrete por botão no painel
