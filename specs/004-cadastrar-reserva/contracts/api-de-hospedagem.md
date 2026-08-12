# Contrato: API de hospedagem (F1.1)

Três rotas. Todas exigem cookie de sessão válido (`omnistay_sessao`). O hotel é sempre o da
sessão — o corpo e a query **não** carregam `id_hotel`.

Detalhe de autorização: [politica-de-autorizacao.md](./politica-de-autorizacao.md).
Modelo: [data-model.md](../data-model.md).

---

## Convenções

| Tema | Regra |
| --- | --- |
| Autenticação | Cookie `omnistay_sessao`; ausência → `401` |
| Autorização | Operação exigida na rota; perfil sem permissão → `403` |
| Datas | ISO `YYYY-MM-DD` |
| Telefone na entrada | Livre (máscara tolerada); na saída e no banco: canônico `55…` só dígitos |
| Erros de validação | `422` com mensagem clara por campo / regra |
| Logs | Nunca registram nome nem telefone |
| Minimização | Lista nominada e contagem são rotas separadas; a contagem nunca embute itens |

---

## `POST /reservas`

**Operação**: `alterar_reserva`

Cria a reserva com titular provisório **novo** na mesma transação. Telefone já existente no
banco **não** reaproveita hóspede — sempre `INSERT` de `hospede`.

### Entrada

```json
{
  "nome": "Maria Silva",
  "telefone": "(11) 98765-4321",
  "data_checkin_prevista": "2026-08-20",
  "data_checkout_prevista": "2026-08-23"
}
```

| Campo | Obrigatório | Regra |
| --- | --- | --- |
| `nome` | sim | Não vazio após trim |
| `telefone` | sim | Normalizável para brasileiro com DDD (ver research §3) |
| `data_checkin_prevista` | sim | Data válida; pode ser no passado |
| `data_checkout_prevista` | sim | Estritamente posterior ao check-in |

### Saída `201`

```json
{
  "id_reserva": 42,
  "id_hotel": 1,
  "nome": "Maria Silva",
  "telefone_contato": "5511987654321",
  "data_checkin_prevista": "2026-08-20",
  "data_checkout_prevista": "2026-08-23",
  "status": "aguardando_cadastro"
}
```

### Erros

| Situação | Status | Observação |
| --- | --- | --- |
| Sessão ausente/inválida | `401` | |
| Perfil não é recepção | `403` | Nada gravado |
| Campo ausente / em branco | `422` | Indica o campo |
| Telefone inválido | `422` | Mensagem orienta formato brasileiro com DDD |
| Checkout ≤ check-in | `422` | Declara inconsistência das datas |

---

## `GET /fila-do-dia`

**Operação**: `ler_fila_do_dia` (só recepção)

Lista reservas ativas do hotel da sessão, com nome e telefone, ordenadas pela data de check-in
prevista (mais próxima primeiro), depois por `id_reserva`.

### Entrada

Sem corpo. Sem query obrigatória nesta fatia. A visão `vw_fila_do_dia` já restringe a
reservas com `data_checkin_prevista <= CURRENT_DATE` (e fora de encerrado/cancelada): chega
hoje, atrasada ou hospedada. Reserva futura não aparece.

### Saída `200`

```json
{
  "itens": [
    {
      "id_reserva": 42,
      "nome": "Maria Silva",
      "telefone_contato": "5511987654321",
      "data_checkin_prevista": "2026-08-20",
      "data_checkout_prevista": "2026-08-23",
      "status": "aguardando_cadastro",
      "ficha_completa": false,
      "chegada_nao_confirmada": false
    }
  ]
}
```

| Campo | Significado |
| --- | --- |
| `nome` | `nome_completo` do titular (provisório ou consolidado) |
| `ficha_completa` | Sempre `false` para reservas só desta fatia |
| `chegada_nao_confirmada` | `true` quando check-in previsto já passou e status não é hospedado/cancelado |

Itens com status `encerrado` ou `cancelada` **não** aparecem.

### Erros

| Situação | Status |
| --- | --- |
| Sessão ausente/inválida | `401` |
| Perfil sem permissão (`staff`, `gestor`) | `403` |

Hotel sem reservas ativas: `200` com `itens: []` — não é erro.

---

## `GET /indicadores/chegadas-do-dia`

**Operação**: `ler_indicadores` (recepção e gestão)

Devolve **apenas a quantidade** de reservas do hotel da sessão com check-in previsto para a
data corrente (`CURRENT_DATE`) e status diferente de `encerrado` e `cancelada`.

### Entrada

Sem corpo. Sem query. A data é sempre o dia corrente do servidor/banco — sem parâmetro que
permita varrer outros dias nesta fatia.

### Saída `200`

```json
{
  "quantidade": 12
}
```

O corpo **não** contém lista, nome, telefone, identificador de reserva nem qualquer outro
campo. Cliente de gestão que precise do número usa esta rota; **nunca** a fila filtrada no
frontend.

### Erros

| Situação | Status |
| --- | --- |
| Sessão ausente/inválida | `401` |
| Perfil sem permissão (`staff`) | `403` |

Zero chegadas no dia: `200` com `quantidade: 0`.

---

## O que esta API não faz (ainda)

- Não envia mensagem ao hóspede
- Não aceita edição nem cancelamento
- Não devolve ficha cadastral completa
- Não aceita `id_hotel` no corpo ou na query
- Não reaproveita hóspede existente pelo telefone
- Não devolve à gestão nenhum recorte da fila nominada
