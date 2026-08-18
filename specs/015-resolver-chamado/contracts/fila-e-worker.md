# Contrato: fila e worker — F3.6

Mensageria: [mensageria-sessao.md](./mensageria-sessao.md). Modelo:
[data-model.md](../data-model.md). Atendimento:
[api-de-atendimento.md](./api-de-atendimento.md).

A fila é a tabela `trabalho`. Nenhum mecanismo paralelo. O clique HTTP **não**
espera o worker para responder `200`.

---

## Allowlist de claim (delta)

`reclamar_proximo` passa a considerar os tipos da F3.5 **e**:

- **`enviar_confirmacao_resolucao`**

Uma passagem (`python -m worker --uma-passagem`) reclama o item. Allowlist e
ramo no consumidor mudam juntos — nunca um dos dois sozinho. Sem o ramo, o
`else` `tipo_desconhecido` destruiria o gancho.

---

## Enfileirar (a partir do POST de resolução)

Quando `atendimento.resolver` conclui o `UPDATE`, chama
`conversa.agendar_confirmacao_resolucao`, que insere a enviada e:

```text
enfileirar_enviar_confirmacao_resolucao(
  id_hotel, id_reserva, id_solicitacao, id_mensagem
)
```

| Campo | Valor |
| --- | --- |
| `tipo` | `enviar_confirmacao_resolucao` |
| `payload` | `{id_reserva, id_solicitacao, id_mensagem}` — só IDs |
| Unicidade | `uq_trabalho_enviar_confirmacao_resolucao_solicitacao` |

O processador de classificar **não** enfileira este tipo. Abertura de
reclamação / pedido **não** muda.

`IntegrityError` no unique → desfecho `ja_agendada` (a resolução do UPDATE já
foi gravada na mesma transação só se o unique não abortar o INSERT… o
agendamento usa savepoint, no padrão das boas-vindas: unique no trabalho não
desfaz o `UPDATE` da solicitação).

---

## Tipo `enviar_confirmacao_resolucao` (consumo)

```text
claim enviar_confirmacao_resolucao
  → conversa.processar_trabalho_enviar_confirmacao_resolucao(gateway)
       localizar a enviada do payload (id_mensagem)
       se já enviada: concluir
       senão enviar_texto_sessao
       marcar trabalho concluido / reagendar só se envio falhar
```

`atendimento` **não** é chamada neste ramo (o status já é `resolvida`).
Catálogo e LLM **não** participam. `hospedagem` **não** é chamada.

| Desfecho | `trabalho.status` | `solicitacao.status` | Alert Center |
| --- | --- | --- | --- |
| envio ok | `concluido` | `resolvida` | item ausente |
| envio falha | `pendente` + backoff de mensageria | **permanece** `resolvida` | item ausente |
| Falha ao gravar no POST | transação do HTTP desfaz; sem trabalho | `aberta` | item visível |
| Já enviada | `concluido` | `resolvida` | item ausente |

Não usar `marcar_falha` para “chamado já resolvido” — este ramo **não** resolve.
`marcar_falha` / `reagendar` só para a porta de **envio**.

Se a enviada do payload não existir (corrupção): log com ids, **não** reabre a
solicitação, **não** inventa recado. Trabalho vai a `falha` operacional — caso
patológico, coberto por teste de ausência da mensagem.

---

## Recado padrão (conclusão)

Função pura em `conversa`: prenome + conclusão adequada ao `tipo` passado no
agendamento (já gravado na enviada). Sem catálogo, sem LLM, sem pergunta de
horário. Ver [mensageria-sessao.md](./mensageria-sessao.md).

---

## O que o worker desta fatia não faz

- `UPDATE` de `solicitacao` (isso é o POST)
- Inserir `consumo` ou abrir chamado novo
- Responder dúvida / registrar pedido / abrir reclamação (ramos inalterados)
- Interpretar ficha, coleta, lembrete ou boas-vindas
- Inferir check-in ou checkout
- Ligar `precisa_atendimento_humano`
- Disparar ou suprimir pulso
- Reabrir solicitação por falha de envio

---

## Reinício

Queda após o POST (resolvida + enviada pendente + trabalho): segundo claim só
envia, ou conclui se já enviada. Queda no meio do POST: transação desfaz;
item permanece aberto; o profissional clica de novo. Teste observável: POST
`200`, `--uma-passagem`, `SELECT` em `solicitacao`, `mensagem` e `trabalho`;
`GET /solicitacoes` sem o item.

---

## Logs

| Evento | Campos |
| --- | --- |
| `trabalho_claim` | `id_trabalho`, `tipo` — passa a aparecer para `enviar_confirmacao_resolucao` |
| `chamado_resolvido` | ids, `id_usuario`, `resultado=resolvido` (no serviço de atendimento, no POST) |
| `resolucao_recusada` | ids, `resultado` (`ja_resolvida` / `nao_encontrada` / `tipo_incompativel`) |
| `resolucao_ja_agendada` | ids, `resultado=ja_agendada` |
| `resolucao_envio_falhou` | ids, código da mensageria |

Ausentes em todos: descrição do chamado, texto da confirmação, telefone,
número de quarto, janela, nome do hóspede.
