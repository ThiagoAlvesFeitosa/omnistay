# Contrato: fila e worker — F3.5

Mensageria: [mensageria-sessao.md](./mensageria-sessao.md). Modelo:
[data-model.md](../data-model.md). Atendimento:
[api-de-atendimento.md](./api-de-atendimento.md). Quarto e janela:
[quarto-e-janela.md](./quarto-e-janela.md).

A fila é a tabela `trabalho`. Nenhum mecanismo paralelo. Webhook permanece o da F3.1.

---

## Allowlist de claim (delta)

`reclamar_proximo` passa a considerar os tipos da F3.4 **e**:

- **`abrir_chamado_reclamacao`**

Uma passagem (`python -m worker --uma-passagem`) reclama o item. Allowlist e ramo no
consumidor mudam juntos — nunca um dos dois sozinho. Sem o ramo, o `else`
`tipo_desconhecido` destruiria o gancho.

---

## Enfileirar (a partir de classificar)

Quando `processar_trabalho_classificar_mensagem` grava `reclamacao_tecnica` +
`classificado` — inclusive no caminho “já classificada” se o trabalho de chamado
ainda não existir:

```text
enfileirar_abrir_chamado_reclamacao(
  id_hotel, id_reserva, id_mensagem  # mensagem recebida da reclamação
)
```

| Campo | Valor |
| --- | --- |
| `tipo` | `abrir_chamado_reclamacao` |
| `payload` | `{id_reserva, id_mensagem}` — só IDs |
| Unicidade | `uq_trabalho_abrir_chamado_reclamacao_mensagem` |

Outras intenções **não** chamam este enqueue. `abrir_reclamacao` e
`MensageriaGateway` **não** participam do processador de classificar no caminho
feliz da reclamação — só o enqueue.

`responder_duvida` continua só para `duvida_geral`. `registrar_pedido_servico`
continua só para `pedido_de_servico`.

Sentimento negativo, neutro ou positivo: os três enfileiram.

---

## Atalho de janela (ainda no trabalho `classificar_mensagem`)

Antes de chamar o LLM, o processador de classificar consulta (colaborador
injetado) se a reserva tem reclamação aberta sem janela. Se o texto
`parece_resposta_de_horario`:

```text
completar_janela_se_resposta(...) → id_solicitacao
gravar desfecho janela_registrada na recebida atual
concluir classificar_mensagem
não chamar LLM
não enfileirar abrir_chamado_reclamacao
não enviar mensagem
```

Não existe tipo `registrar_janela_preferencia`. Queda no meio: o trabalho de
classificar volta a `pendente`; o segundo claim vê janela já preenchida (no-op)
ou ainda nula (completa).

Se `parece_resposta_de_horario` é falso, classifica como hoje. Nova
`reclamacao_tecnica` enfileira chamado **próprio**.

---

## Tipo `abrir_chamado_reclamacao` (consumo)

```text
claim abrir_chamado_reclamacao
  → se JSON da recebida já tem resposta confirmacao_reclamacao e id_solicitacao:
        se enviada ainda pendente: tentar envio; senão concluir
        não chamar abrir_reclamacao
  → senão conversa.processar_trabalho_abrir_chamado(gateway, abrir_reclamacao)
       janela = extrair_janela_preferencia(conteudo)
       quarto = extrair_numero_quarto(conteudo)
       gravar enviada (recado padrão; perguntar horário só se janela nula)
       abrir_reclamacao(...) → id_solicitacao tipo reclamacao
       atualizar JSON da recebida
       enviar_texto_sessao
       marcar trabalho concluido / reagendar só se envio falhar após gravar
```

`hospedagem` **não** é chamada neste ramo. Catálogo e LLM **não** participam.

| Desfecho | `trabalho.status` | Sinal na fila do dia | `solicitacao` |
| --- | --- | --- | --- |
| aberto + envio ok | `concluido` | não muda | 1 linha `reclamacao` |
| aberto + envio falha | `pendente` + backoff de mensageria | não muda | já gravada |
| Falha ao gravar | transação desfaz; reclaim | não | não |
| Já aberto | `concluido` (ou retry de envio) | não | a mesma |

Não usar `marcar_falha` para “chamado malformado” — quarto ou janela ausentes
**não** são erro. `marcar_falha` / `reagendar` só para a porta de **envio**.

---

## Recado padrão (confirmação)

Função pura em `conversa`: prenome + recebimento + manutenção acionada. Pergunta
de horário **somente** se a janela extraída for nula. Sem catálogo, sem LLM, sem
prazo de conserto.

---

## Colaborador `abrir_reclamacao`

Injetado pelo worker. Contrato:

```text
abrir_reclamacao(
  conexao,
  id_hotel,              # do trabalho; MUST bater com reserva.id_hotel
  id_reserva,
  id_mensagem,           # origem
  descricao,             # conteudo da recebida
  numero_quarto,         # extraído ou None
  urgencia,              # eixo da mensagem ou 'media'
  janela_preferencia,    # extraída ou None
) -> id_solicitacao
```

Implementação em `atendimento`. Recusa (não insere) se a reserva não for daquele
hotel. Unicidade da origem: o banco rejeita o segundo INSERT.

## Colaborador `completar_janela_se_resposta`

Injetado no processador de classificar. Contrato:

```text
completar_janela_se_resposta(
  conexao,
  id_hotel,
  id_reserva,
  texto,
) -> id_solicitacao | None
```

`None` se não houver reclamação aberta sem janela, se o texto não parecer
resposta de horário, ou se a reserva for de outro hotel. Não envia mensagem.

---

## O que o worker desta fatia não faz

- Inserir `consumo` ou `solicitacao` tipo `servico` / `consumo` neste ramo
- Responder dúvida pelo catálogo (ramo `responder_duvida` inalterado)
- Registrar pedido de serviço (ramo `registrar_pedido_servico` inalterado)
- Marcar resolvido
- Interpretar ficha, enviar coleta, lembrete ou boas-vindas (ramos inalterados)
- Inferir check-in ou checkout
- Ligar `precisa_atendimento_humano`
- Marcar `abrir_chamado_reclamacao` como `falha` por quarto ou janela ausentes
- Disparar ou suprimir pulso

---

## Reinício

Queda após gravar enviada + solicitação + JSON: segundo claim vê
`confirmacao_reclamacao` e só envia se pendente, ou conclui. Queda antes de
gravar: item volta a `pendente` e registra de novo. Teste observável: uma
passagem, `SELECT` em `mensagem`, `solicitacao` e `trabalho`.

---

## Logs

| Evento | Campos |
| --- | --- |
| `trabalho_claim` | `id_trabalho`, `tipo` — passa a aparecer para `abrir_chamado_reclamacao` |
| `chamado_aberto` | ids, `id_solicitacao`, `resultado=aberto` |
| `chamado_ja_aberto` | ids, `resultado=ja_aberto` |
| `chamado_envio_falhou` | ids, código da mensageria |
| `janela_registrada` | ids, `id_solicitacao`, `resultado=janela_registrada` |
| `prazo_ausente` | `id_hotel`, chave |

Ausentes em todos: conteúdo da reclamação, texto da confirmação, descrição,
telefone, número de quarto, janela em texto livre.
