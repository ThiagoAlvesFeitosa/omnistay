# Contrato: fila e worker — F3.2

LLM: [llm-e-classificacao.md](./llm-e-classificacao.md). Modelo:
[data-model.md](../data-model.md). Webhook permanece o da F3.1.

A fila é a tabela `trabalho`. Nenhum mecanismo paralelo.

---

## Allowlist de claim (delta)

`reclamar_proximo` passa a considerar:

- `enviar_coleta`
- `interpretar_ficha`
- `enviar_lembrete`
- `enviar_boas_vindas`
- **`classificar_mensagem`**

Uma passagem (`python -m worker --uma-passagem`) **reclama** o item. Allowlist e ramo
no consumidor mudam juntos — nunca um dos dois sozinho.

Os testes da F3.1 que exigiam item `pendente` após a passagem são invertidos nesta
fatia (ver [research.md](../research.md) §1).

---

## Tipo `classificar_mensagem` (consumo)

Payload inalterado: `{id_reserva, id_mensagem, id_evento}` — só IDs.

```text
claim classificar_mensagem
  → se já houver classificacao_intencao com desfecho: marcar concluido; não chamar LLM
  → senão conversa.processar_trabalho_classificar_mensagem(llm)
       ler mensagem (id_hotel do trabalho)
       llm.classificar(texto)
       validar taxonomia
       gravar eixos + classificacao_bruta (conteudo intocado)
       marcar trabalho concluido
```

`MensageriaGateway` **não** participa. `CatalogoRepository` **não** participa.
`hospedagem` **não** é chamada neste ramo (nenhuma transição de reserva, nenhuma
consolidação de ficha).

| Desfecho | `trabalho.status` | Retentativa de LLM |
| --- | --- | --- |
| `classificado` | `concluido` | não |
| `encaminhado_humano` | `concluido` | não |
| `formato_invalido` | `concluido` | não |
| `indisponivel` | `concluido` | não |
| Falha ao gravar | transação desfaz; reclaim por expiração devolve a `pendente` | sim (gravar, não o LLM) |

Não usar `marcar_falha` / `reagendar` para classificador indisponível ou inválido.

---

## O que o worker desta fatia não faz

- Enviar mensagem ao hóspede
- Inserir `solicitacao` ou `consumo`
- Interpretar ficha (`interpretar_ficha` permanece o ramo da F1.3)
- Inferir check-in ou checkout
- Consultar catálogo
- Marcar `classificar_mensagem` como `falha` no caminho feliz de escala humana

---

## Reinício

Mensagem (com ou sem eixos) e trabalho são linhas de banco. Queda no meio: ou a
gravação não entrou (item volta a `pendente` e classifica de novo) ou já entrou
(segundo claim vê o desfecho e só conclui). Teste observável sem matar processo:
configurar o falso, uma passagem, `SELECT` em `mensagem` e `trabalho`.

---

## Logs

| Evento | Campos |
| --- | --- |
| `trabalho_claim` | `id_trabalho`, `tipo` — passa a aparecer para `classificar_mensagem` |
| `mensagem_classificada` | `id_mensagem`, `id_reserva`, `id_hotel`, `desfecho`, `intencao` (quando houver) |
| `classificacao_indisponivel` | `id_mensagem`, `id_trabalho`, `id_hotel`, código |
| `classificacao_formato_invalido` | `id_mensagem`, `id_trabalho`, `id_hotel` |

Ausentes em todos: conteúdo da mensagem, telefone, `bruto`, payload do modelo.
