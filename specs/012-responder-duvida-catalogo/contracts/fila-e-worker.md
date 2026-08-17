# Contrato: fila e worker — F3.3

LLM: [llm-e-conversacao.md](./llm-e-conversacao.md). Mensageria:
[mensageria-sessao.md](./mensageria-sessao.md). Modelo:
[data-model.md](../data-model.md).

A fila é a tabela `trabalho`. Nenhum mecanismo paralelo. Webhook permanece o da F3.1.

---

## Allowlist de claim (delta)

`reclamar_proximo` passa a considerar os tipos da F3.2 **e**:

- **`responder_duvida`**

Uma passagem (`python -m worker --uma-passagem`) reclama o item. Allowlist e ramo no
consumidor mudam juntos — nunca um dos dois sozinho. Sem o ramo, o `else`
`tipo_desconhecido` destruiria o gancho.

Os testes da F3.2 cuja passagem completa observava dúvida geral **sem** envio são
atualizados nesta fatia (ver [research.md](../research.md) §1).

---

## Enfileirar (a partir de classificar)

Quando `processar_trabalho_classificar_mensagem` grava `duvida_geral` +
`classificado` — inclusive no caminho “já classificada” se o trabalho de resposta
ainda não existir:

```text
enfileirar_responder_duvida(
  id_hotel, id_reserva, id_mensagem  # mensagem recebida
)
```

| Campo | Valor |
| --- | --- |
| `tipo` | `responder_duvida` |
| `payload` | `{id_reserva, id_mensagem}` — só IDs |
| Unicidade | `uq_trabalho_responder_duvida_mensagem` |

Outras intenções **não** chamam este enqueue. `CatalogoRepository` e
`MensageriaGateway` **não** participam do processador de classificar.

---

## Tipo `responder_duvida` (consumo)

```text
claim responder_duvida
  → se JSON da recebida já tem resposta automatica|aviso:
        se enviada ainda pendente: tentar envio; senão concluir
        não chamar LLM
  → senão conversa.processar_trabalho_responder_duvida(llm, catalogo, gateway)
       listar_ativos(id_hotel)
       se vazio → aviso + desfecho duvida_nao_coberta (sem LLM)
       senão llm.responder_duvida(pergunta, itens)
       validar fidelidade
       gravar enviada (texto fiel ou aviso padrão)
       atualizar JSON da recebida
       enviar_texto_sessao
       marcar trabalho concluido (redação) / reagendar só se envio falhar após gravar
```

`hospedagem` **não** é chamada neste ramo.

| Desfecho de redação | `trabalho.status` | LLM de novo | Sinal na fila |
| --- | --- | --- | --- |
| automática fiel | `concluido` (após envio ok) | não | não |
| não coberta / não fiel / vazio / indisponível | `concluido` (após gravar aviso) | não | sim (`duvida_nao_coberta`) |
| Falha ao gravar | transação desfaz; reclaim | não (ainda não chamou com sucesso persistido) | não |
| Falha de envio após gravar | `pendente` + backoff de mensageria | não | já gravado (aviso ou automática) |

Não usar `marcar_falha` para conversação indisponível — isso recolocaria o LLM em
loop. `marcar_falha` / `reagendar` só para a porta de **envio**, como na coleta.

---

## Recado padrão (aviso)

Função pura em `conversa` (mesmo espírito de `texto_lembrete`): prenome + frase de
que a recepção vai atender. Sem fato de catálogo, sem LLM.

---

## O que o worker desta fatia não faz

- Inserir `solicitacao` ou `consumo`
- Responder pedido de serviço ou reclamação
- Interpretar ficha, enviar coleta, lembrete ou boas-vindas (ramos inalterados)
- Inferir check-in ou checkout
- Marcar `responder_duvida` como `falha` no caminho de escala humana por catálogo

---

## Reinício

Queda após gravar enviada + JSON: segundo claim vê `resposta` e só envia se
pendente, ou conclui. Queda antes de gravar: item volta a `pendente` e redige de
novo. Teste observável: uma passagem, `SELECT` em `mensagem` e `trabalho`.

---

## Logs

| Evento | Campos |
| --- | --- |
| `trabalho_claim` | `id_trabalho`, `tipo` — passa a aparecer para `responder_duvida` |
| `duvida_respondida` | `id_mensagem`, `id_reserva`, `id_hotel`, `resultado=automatica` |
| `duvida_nao_coberta` | ids, `resultado=aviso` (cobre vazio / não coberta) |
| `resposta_nao_fiel` | ids, `resultado=nao_fiel` |
| `conversacao_indisponivel` | ids, código |
| `duvida_ja_respondida` | ids |

Ausentes em todos: pergunta, resposta, trechos, título/conteúdo de item, telefone.
