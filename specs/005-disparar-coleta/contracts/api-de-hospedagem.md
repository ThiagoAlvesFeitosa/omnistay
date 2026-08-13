# Contrato: API de hospedagem — acréscimos F1.2

Estende o contrato da F1.1 ([api-de-hospedagem.md](../../004-cadastrar-reserva/contracts/api-de-hospedagem.md)).
Autorização inalterada: [politica-de-autorizacao.md](./politica-de-autorizacao.md).
Modelo: [data-model.md](../data-model.md).

Nenhuma rota HTTP **nova** nesta fatia. O comportamento novo é colateral ao `POST /reservas`
já existente e visível no `GET /fila-do-dia`.

---

## Convenções adicionais

| Tema | Regra |
| --- | --- |
| Envio | Nunca na thread da requisição HTTP; só via `trabalho` + worker |
| Mensageria nos testes | Porta falsa; zero chamada ao provedor real |
| Logs | Sem `conteudo` de mensagem, sem telefone, sem nome |
| Status de coleta | Vocabulário de `mensagem.status_envio`: `pendente` · `enviada` · `entregue` · `falha` |

---

## `POST /reservas` (comportamento ampliado)

**Operação**: `alterar_reserva` (inalterada)

Entrada e corpo de resposta `201` **permanecem** os da F1.1 (sem campo novo obrigatório no
JSON de resposta).

### Efeito colateral obrigatório no sucesso

Na mesma transação da criação:

1. Existe exatamente uma `mensagem` de saída da reserva com `status_envio = pendente`.
2. Existe exatamente um `trabalho` `tipo = enviar_coleta` `status = pendente` apontando para
   essa mensagem e reserva.

A resposta `201` **não** espera o envio ao hóspede.

### Erros

Os mesmos da F1.1. Em qualquer `4xx` de validação/autorização: **zero** linhas novas em
`mensagem` e `trabalho`.

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
      "data_checkin_prevista": "2026-08-20",
      "data_checkout_prevista": "2026-08-23",
      "status": "aguardando_cadastro",
      "ficha_completa": false,
      "chegada_nao_confirmada": false,
      "status_envio_coleta": "pendente"
    }
  ]
}
```

| Campo novo | Significado |
| --- | --- |
| `status_envio_coleta` | Estado de entrega da mensagem de coleta; após o worker: tipicamente `enviada` ou `falha` |

Demais campos e erros: iguais à F1.1.

---

## O que esta API ainda não faz

- Não interpreta resposta do hóspede
- Não expõe endpoint de histórico completo de mensagens (o registro existe no banco; leitura
  HTTP dedicada pode vir com F1.3/painel)
- Não promove `status_envio` para `entregue` (sem webhook de status)
- Não envia lembrete por silêncio
