# Contrato: API de atendimento — Alert Center (delta F3.5)

Autorização: [politica-de-autorizacao.md](./politica-de-autorizacao.md). Modelo:
[data-model.md](../data-model.md).

`POST /webhook` não muda. `GET /fila-do-dia` não muda (nem o booleano humano).
Nenhuma rota nova. `GET /solicitacoes` da F3.4 permanece a superfície do Alert
Center e passa a listar também `tipo = reclamacao`.

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
tipo                 # servico | reclamacao  (consumo fora desta fatia)
descricao
numero_quarto        # string ou nulo
urgencia
janela_preferencia   # string ou nulo — NOVO nesta fatia
status               # aberta | em_andamento
aberta_em
destaque_tempo_excedido   # bool — NOVO; derivado, não coluna
```

`destaque_tempo_excedido` é `true` só quando `tipo = reclamacao` **e** o chamado
está aberto além de `horas_destaque_chamado_aberto` da propriedade. Pedido de
serviço: sempre `false` nesta fatia. Sem o prazo configurado: sempre `false`.

**Campos que este contrato proíbe** no item e em qualquer envelope da resposta:

- nome do hóspede
- telefone
- documento, endereço, CEP, cidade, data de nascimento, profissão
- conteúdo da ficha além do que já está em `descricao` (relato do problema)

`id_reserva` é identificador operacional. `janela_preferencia` é horário de
reparo informado pelo hóspede, não dado cadastral. Staff e gestão continuam
recusados em `GET /reservas/{id}/ficha`.

### Respostas

| Situação | HTTP |
| --- | --- |
| Lista (inclusive vazia) | **200** `{ "itens": [ ... ] }` |
| Sem sessão / sessão inválida | **401** |
| Perfil sem a operação | **403** — nesta fatia não há perfil autenticado recusado (os três têm a operação) |
| Hotel B autenticado | **200** com itens só de B (A não aparece) |

Não há 404 em coleção.

Testes da F3.4 que leem o item de serviço **ganham os dois campos novos**
(`janela_preferencia` nulo, `destaque_tempo_excedido` falso). Não se mantém o
JSON antigo sem eles.

---

## Superfícies que esta fatia não cria

- `GET /solicitacoes/{id}`
- `POST` / `PATCH` de atribuir, resolver ou cancelar (F3.6)
- Rota de `consumo` / lançamento (F3.7)
- `GET /reservas/{id}/mensagens`
- Campo novo em `GET /fila-do-dia`
- Notificação push ao staff
- Rota para editar `horas_destaque_chamado_aberto`

---

## Webhook e demais APIs

Intocados. A abertura do chamado é só worker. A suíte de conversa continua lendo
`mensagem` e `solicitacao` no banco de teste; o HTTP é a fila da equipe já
existente.
