# Contrato: API do simulador

Três rotas. Cookie `omnistay_sessao`. Hotel = sessão — corpo e query
**não** carregam `id_hotel`.

Autorização: [politica-de-autorizacao.md](./politica-de-autorizacao.md).
Entrada: [entrada-simulada.md](./entrada-simulada.md). Modo:
[modo-e-fabrica.md](./modo-e-fabrica.md). Tela:
[tela-de-simulacao.md](./tela-de-simulacao.md).
Modelo: [data-model.md](../data-model.md).

---

## Convenções

| Tema | Regra |
| --- | --- |
| Autenticação | Cookie; ausência → `401` |
| Autorização | Perfil sem `usar_simulador` → `403` |
| Modo `real` | `409` corpo `{"codigo": "modo_real"}` |
| Outro hotel / id inexistente | `404` (mesma resposta) |
| Logs | `id_hotel`, `id_reserva`, `id_mensagem`, `id_externo`, modo, código. **Sem** `conteudo` |
| `id_hotel` no JSON | Ausente |

Datas em ISO-8601 com fuso.

---

## `GET /simulador/conversas`

**Operação**: `usar_simulador`

Lista reservas da propriedade para o apresentador escolher o fio.

### Saída `200`

```json
{
  "modo": "demonstracao",
  "conversas": [
    {
      "id_reserva": 12,
      "status": "hospedado",
      "nome_titular": "Marina",
      "telefone_contato": "5511999990000"
    }
  ]
}
```

| Campo | Regra |
| --- | --- |
| `modo` | Ecoa a configuração; nesta rota, em `real` a resposta é `409`, não `200` com lista |
| `conversas` | Todas as reservas do hotel da sessão (qualquer status). Ordem: `id_reserva` descendente |
| Hotel sem reserva | `"conversas": []` — não é erro |

Não é a fila do dia. Não omite reserva futura: a banca pode ter
cadastrado há dois minutos.

---

## `GET /simulador/conversas/{id_reserva}`

**Operação**: `usar_simulador`

Fio da conversa. Reserva de outro hotel ou inexistente → `404`.

### Saída `200`

```json
{
  "id_reserva": 12,
  "status": "hospedado",
  "nome_titular": "Marina",
  "telefone_contato": "5511999990000",
  "mensagens": [
    {
      "id_mensagem": 40,
      "direcao": "enviada",
      "conteudo": "Ola, Marina! ...",
      "status_envio": "enviada",
      "enviada_em": "2026-08-26T14:01:00+00:00"
    },
    {
      "id_mensagem": 41,
      "direcao": "recebida",
      "conteudo": "Qual o horario do cafe?",
      "status_envio": null,
      "enviada_em": "2026-08-26T14:02:00+00:00"
    }
  ]
}
```

| Campo | Regra |
| --- | --- |
| `mensagens` | Ordem `enviada_em`, depois `id_mensagem`. Inclui `pendente` e `falha` |
| `status_envio` | `null` quando `direcao = recebida` |
| `direcao` | Só `enviada` \| `recebida` |

---

## `POST /simulador/conversas/{id_reserva}/mensagens`

**Operação**: `usar_simulador`

Turno do hóspede. Processamento lento **não** ocorre nesta requisição
(Artigo III): grava evento + mensagem + trabalho e responde.

### Entrada

```json
{
  "texto": "Qual o horario do cafe?",
  "id_externo": "sim:550e8400-e29b-41d4-a716-446655440000"
}
```

| Campo | Regra |
| --- | --- |
| `texto` | Obrigatório; após `strip`, vazio → `400` `{"codigo": "texto_vazio"}` |
| `id_externo` | Obrigatório; vazio → `400` `{"codigo": "id_externo_ausente"}`. Tamanho máximo 80 (coluna) |

### Saídas

| Código | Quando |
| --- | --- |
| `201` | Primeira aceitação; corpo com `status` do serviço (`enfileirado`, etc.), `id_mensagem`, `id_reserva` |
| `200` | Mesmo `id_externo` já processado (idempotente); **sem** segunda mensagem |
| `400` | Texto vazio, `id_externo` ausente |
| `401` / `403` / `404` / `409` | Convenções |

```json
{
  "status": "enfileirado",
  "id_mensagem": 41,
  "id_reserva": 12
}
```

A resposta **não** inclui a resposta automática do hotel. Ela aparece
no GET depois que o worker processar, como no canal real.

---

## Recusa visível

| Situação | HTTP |
| --- | --- |
| Sem sessão | `401` |
| Staff (ou perfil sem operação) | `403` |
| Modo `real` | `409` `modo_real` |
| Reserva de outro hotel / inexistente | `404` |
| Texto vazio / id ausente | `400` |

PUT/PATCH/DELETE nestas URLs: `405`.
