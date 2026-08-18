# Contrato: fila e worker — F3.4

Mensageria: [mensageria-sessao.md](./mensageria-sessao.md). Modelo:
[data-model.md](../data-model.md). Atendimento:
[api-de-atendimento.md](./api-de-atendimento.md).

A fila é a tabela `trabalho`. Nenhum mecanismo paralelo. Webhook permanece o da F3.1.

---

## Allowlist de claim (delta)

`reclamar_proximo` passa a considerar os tipos da F3.3 **e**:

- **`registrar_pedido_servico`**

Uma passagem (`python -m worker --uma-passagem`) reclama o item. Allowlist e ramo no
consumidor mudam juntos — nunca um dos dois sozinho. Sem o ramo, o `else`
`tipo_desconhecido` destruiria o gancho.

---

## Enfileirar (a partir de classificar)

Quando `processar_trabalho_classificar_mensagem` grava `pedido_de_servico` +
`classificado` — inclusive no caminho “já classificada” se o trabalho de pedido
ainda não existir:

```text
enfileirar_registrar_pedido_servico(
  id_hotel, id_reserva, id_mensagem  # mensagem recebida
)
```

| Campo | Valor |
| --- | --- |
| `tipo` | `registrar_pedido_servico` |
| `payload` | `{id_reserva, id_mensagem}` — só IDs |
| Unicidade | `uq_trabalho_registrar_pedido_servico_mensagem` |

Outras intenções **não** chamam este enqueue. `abrir_servico` e
`MensageriaGateway` **não** participam do processador de classificar.
`responder_duvida` continua só para `duvida_geral`.

---

## Tipo `registrar_pedido_servico` (consumo)

```text
claim registrar_pedido_servico
  → se JSON da recebida já tem resposta confirmacao_pedido e id_solicitacao:
        se enviada ainda pendente: tentar envio; senão concluir
        não chamar abrir_servico
  → senão conversa.processar_trabalho_registrar_pedido(gateway, abrir_servico)
       gravar enviada (recado padrão)
       abrir_servico(...) → id_solicitacao tipo servico
       atualizar JSON da recebida
       enviar_texto_sessao
       marcar trabalho concluido / reagendar só se envio falhar após gravar
```

`hospedagem` **não** é chamada neste ramo. Catálogo e LLM **não** participam.

| Desfecho | `trabalho.status` | Sinal na fila do dia | `solicitacao` |
| --- | --- | --- | --- |
| registrado + envio ok | `concluido` | não muda | 1 linha `servico` |
| registrado + envio falha | `pendente` + backoff de mensageria | não muda | já gravada |
| Falha ao gravar | transação desfaz; reclaim | não | não |
| Já registrado | `concluido` (ou retry de envio) | não | a mesma |

Não usar `marcar_falha` para “pedido malformado” — quarto ausente **não** é erro;
a solicitação nasce mesmo assim. `marcar_falha` / `reagendar` só para a porta de
**envio**, como na coleta e na dúvida.

---

## Recado padrão (confirmação)

Função pura em `conversa` (mesmo espírito de `texto_aviso_duvida` / lembrete):
prenome + frase de que o pedido foi recebido e a equipe vai atender. Sem catálogo,
sem LLM, sem prazo, sem janela de preferência.

---

## Colaborador `abrir_servico`

Injetado pelo worker. Contrato:

```text
abrir_servico(
  conexao,
  id_hotel,          # do trabalho; MUST bater com reserva.id_hotel
  id_reserva,
  id_mensagem,       # origem
  descricao,         # conteudo da recebida
  numero_quarto,     # extraído ou None
  urgencia,          # eixo da mensagem ou 'media'
) -> id_solicitacao
```

Implementação em `atendimento`. Recusa (não insere) se a reserva não for daquele
hotel. Unicidade da origem: o banco rejeita o segundo INSERT.

---

## O que o worker desta fatia não faz

- Inserir `consumo` ou `solicitacao` tipo `reclamacao` / `consumo`
- Responder dúvida pelo catálogo (ramo `responder_duvida` inalterado)
- Abrir chamado de reclamação, perguntar horário, marcar resolvido
- Interpretar ficha, enviar coleta, lembrete ou boas-vindas (ramos inalterados)
- Inferir check-in ou checkout
- Ligar `precisa_atendimento_humano`
- Marcar `registrar_pedido_servico` como `falha` por quarto ausente

---

## Reinício

Queda após gravar enviada + solicitação + JSON: segundo claim vê
`confirmacao_pedido` e só envia se pendente, ou conclui. Queda antes de gravar:
item volta a `pendente` e registra de novo. Teste observável: uma passagem,
`SELECT` em `mensagem`, `solicitacao` e `trabalho`.

---

## Logs

| Evento | Campos |
| --- | --- |
| `trabalho_claim` | `id_trabalho`, `tipo` — passa a aparecer para `registrar_pedido_servico` |
| `pedido_registrado` | ids, `id_solicitacao`, `resultado=registrado` |
| `pedido_ja_registrado` | ids, `resultado=ja_registrado` |
| `pedido_envio_falhou` | ids, código da mensageria |

Ausentes em todos: conteúdo do pedido, texto da confirmação, descrição, telefone,
número de quarto.
