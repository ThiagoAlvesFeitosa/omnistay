# Contrato — fila e worker do pulso

Modelo: [data-model.md](../data-model.md). Roteamento:
[roteamento-resposta.md](./roteamento-resposta.md). Mensageria:
[mensageria-pulso.md](./mensageria-pulso.md).

`POST /webhook` **não muda**. Dois tipos novos em `ck_trabalho_tipo`, os dois
na allowlist do worker nesta fatia.

---

## `enviar_pulso`

Enfileirado só pela varredura (não pelo webhook).

| | |
| --- | --- |
| Payload | `{id_reserva, id_mensagem}` |
| Unicidade | `uq_trabalho_enviar_pulso_reserva` |
| Processador | `processar_trabalho_enviar_pulso` em `conversa` |

Antes de chamar a porta: reavaliar elegibilidade. Inelegível → `concluido`
sem envio, log sem texto. Elegível → `enviar_pulso` na porta; sucesso marca
mensagem enviada; `FalhaDeEnvio` reagenda o **mesmo** trabalho.

---

## Depois de `classificar_mensagem`

Se **não** há pulso aguardando resposta (trabalho `enviar_pulso` com mensagem
já enviada **e** sem `avaliacao` de origem pulso), o classificar permanece
igual às F3.2–F3.5.

Se há pulso aguardando:

| Desfecho da classificação | Trabalho seguinte |
| --- | --- |
| `duvida_geral` / `pedido_de_servico` / `reclamacao_tecnica` classificados | os já existentes |
| outra intenção classificada | `registrar_resposta_pulso` |
| falha / formato inválido / indisponível | nenhum; encerrar pulso + humano |

Não executar dúvida, pedido nem chamado **dentro** de `classificar_mensagem`.

---

## `registrar_resposta_pulso`

| | |
| --- | --- |
| Payload | `{id_reserva, id_mensagem}` |
| Unicidade | `uq_trabalho_registrar_resposta_pulso_mensagem` |
| Processador | `processar_trabalho_registrar_resposta_pulso` |

Ordem na mesma transação, **antes** da porta:

**Positivo ou neutro**

1. INSERT enviada (reconhecimento único, sem afirmar satisfação)
2. `feedback.encerrar_pulso` (comentário, nota nula)
3. `enviar_texto_sessao`

**Negativo**

1. INSERT enviada (confirmação: o que acontece em seguida, sem horário)
2. `feedback.encerrar_pulso`
3. `atendimento.abrir_reclamacao` (janela nula)
4. `enviar_texto_sessao`

Caminho idempotente: se a enviada deste recado já existe para a mensagem de
origem, não insere segunda nem segunda avaliação.

Falha de envio: avaliação e chamado (se houver) permanecem; retoma só a
mensageria.

---

## Allowlist

Acrescentar `enviar_pulso` e `registrar_resposta_pulso` em `TIPOS_CONSUMIVEIS`
e no `reclamar_proximo` na **mesma** revisão em que o CHECK passa a aceitá-los.
Não consumir agora marcaría `tipo_desconhecido` e destruiria o gancho.

Ramo no `worker/consumidor.py` no mesmo passo.
