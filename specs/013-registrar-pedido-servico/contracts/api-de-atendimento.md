# Contrato: API de atendimento — fila de solicitações

Autorização: [politica-de-autorizacao.md](./politica-de-autorizacao.md). Modelo:
[data-model.md](../data-model.md).

`POST /webhook` não muda. `GET /fila-do-dia` não muda (nem o booleano humano).

---

## `GET /solicitacoes`

Lista a fila da equipe operacional da propriedade da sessão.

| | |
| --- | --- |
| Operação | `ler_solicitacao_atribuida` |
| Quem | recepção, staff (equipe operacional), gestão — da **própria** propriedade |
| Filtro | `reserva.id_hotel` = hotel da sessão; `status IN ('aberta', 'em_andamento')` |
| Ordem | `aberta_em` crescente |

### Item (mesmo JSON para os três perfis)

```text
id_solicitacao
id_reserva
tipo                 # nesta fatia: servico
descricao
numero_quarto        # string ou nulo
urgencia
status               # aberta | em_andamento
aberta_em
```

**Campos que este contrato proíbe** no item e em qualquer envelope da resposta:

- nome do hóspede
- telefone
- documento, endereço, CEP, cidade, data de nascimento, profissão
- conteúdo da ficha além do que já está em `descricao` (texto do pedido)

`id_reserva` é identificador operacional. Não substitui ficha: staff e gestão
continuam recusados em `GET /reservas/{id}/ficha`.

### Respostas

| Situação | HTTP |
| --- | --- |
| Lista (inclusive vazia) | **200** `{ "itens": [ ... ] }` |
| Sem sessão / sessão inválida | **401** |
| Perfil sem a operação | **403** — nesta fatia não há perfil autenticado recusado (os três têm a operação) |
| Hotel B autenticado | **200** com itens só de B (A não aparece) |

Não há 404 em coleção.

---

## Superfícies que esta fatia não cria

- `GET /solicitacoes/{id}`
- `POST` / `PATCH` de atribuir, resolver ou cancelar (F3.6)
- Rota de `consumo` / lançamento (F3.7)
- `GET /reservas/{id}/mensagens`
- Campo novo em `GET /fila-do-dia`
- Notificação push ao staff

---

## Webhook e demais APIs

Intocados. O registro do pedido é só worker. A suíte de conversa continua lendo
`mensagem` e `solicitacao` no banco de teste; o HTTP novo é a fila da equipe.
