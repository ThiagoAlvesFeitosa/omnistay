# Modelo de dados — F4.2 Lista de Pedidos Feitos pelo Chat

Nenhuma tabela nova. `consumo.valor_praticado` e `consumo.descricao_item`
já existem na `0015`. Revisão `0018_lista_pedidos_chat`.

---

## Recorte cobrável (consulta, não entidade nova)

Uma linha da lista é um `consumo` da reserva cujo
`status_lancamento` ∈ {`pendente`, `lancado`}.

| Fonte | Uso |
| --- | --- |
| `consumo.descricao_item` | rótulo visível do item |
| `consumo.valor_praticado` | valor da hora do pedido; imutável no reajuste |
| `solicitacao.id_reserva` | recorte da estadia |
| `solicitacao.aberta_em` | ordem cronológica |
| `reserva.id_hotel` | isolamento |

**Fora do recorte:** `solicitacao.tipo = servico` (não há `consumo`);
`status_lancamento = dispensado`; consumo de outro hotel.

**Proibido no recorte desta fatia:** `solicitacao.descricao` (DPC),
`status_lancamento` na mensagem e no GET desta lista, ficha cadastral.

Hotel chega sempre por junção com `reserva`. `id_hotel` no `WHERE`.

### Total

Soma aritmética dos `valor_praticado` das linhas do recorte, duas casas.
Não é persistido. Não é “total da estadia”.

---

## Trabalho `enviar_lista_pedidos_chat`

| Campo | Valor |
| --- | --- |
| `tipo` | `enviar_lista_pedidos_chat` |
| `payload` | `{id_reserva, id_mensagem}` |
| Unicidade | parcial por reserva |

Pendente → worker envia o `mensagem.conteudo` já gravado; `concluido` no
sucesso; falha de mensageria reagenda o **mesmo** id. Índice
`uq_trabalho_enviar_lista_pedidos_chat_reserva`.

Não existe trabalho quando o recorte é vazio.

---

## Mensagem de saída

Uma `mensagem` `direcao = enviada` por lista agendada, corpo montado no
enfileiramento, `status_envio` no ciclo já vigente (`pendente` → `enviada`
/ `falha`). O único dado pessoal no corpo é o prenome.

---

## Reserva (sem coluna nova)

`confirmar_saida` inalterado na máquina de estados. Chamado aberto e
consumo pendente continuam **não** bloqueando. Esta fatia só acrescenta
efeitos colaterais na mesma transação: pesquisa (já F4.1) + lista se
houver cobrável.

---

## Delta de esquema (`0018`)

```sql
ALTER TABLE trabalho DROP CONSTRAINT ck_trabalho_tipo;
ALTER TABLE trabalho ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN (
        /* tipos já vigentes até 0017, mais: */
        'enviar_lista_pedidos_chat'
    ));

CREATE UNIQUE INDEX uq_trabalho_enviar_lista_pedidos_chat_reserva
    ON trabalho ( ((payload->>'id_reserva')::bigint) )
    WHERE tipo = 'enviar_lista_pedidos_chat';
```

A lista literal do CHECK na revisão **repete todos os tipos vigentes**
(padrão F4.1 / `0017`) e acrescenta o novo. `docs/04-schema.sql` espelha.

Nenhuma coluna em `consumo`. Nenhum parâmetro novo. Nenhuma mudança na
`vw_fila_do_dia`.

---

## Transições

Esta fatia **não** altera `status_lancamento` nem `reserva.status`.
Lançar/dispensar depois do envio não gera evento de conversa.

Webhook e `interpretar_pesquisa_saida` ficam como na F4.1.
