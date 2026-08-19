# Contrato: fila e worker — registro de consumo (delta F3.7)

Modelo: [data-model.md](../data-model.md). Identificação:
[identificacao-e-preco.md](./identificacao-e-preco.md). Mensageria:
[mensageria-sessao.md](./mensageria-sessao.md).

`POST /webhook` **não muda**. Não nasce tipo novo em `trabalho`. O claim
`registrar_pedido_servico` (F3.4) ganha o fork de identificação.

---

## Enfileiramento (inalterado na classificação)

Quando `classificar_mensagem` grava `pedido_de_servico` + `desfecho =
classificado`, continua inserindo `registrar_pedido_servico` com
`{id_reserva, id_mensagem}` na mesma transação. Dúvida e reclamação **não**
geram este trabalho.

Caminho idempotente de classificar: se a intenção é `pedido_de_servico` e o
trabalho ainda não existe para aquela mensagem, enfileira antes de só concluir.

---

## Processador `registrar_pedido_servico` (esta fatia)

Allowlist e ramo **já existem**. O worker passa a injetar, além de
`abrir_servico` e do gateway:

- `listar_itens_ativos(id_hotel)` → tupla `(id, nome)` sem preço
- `identificar_item_vendavel` (porta)
- `abrir_consumo(...)`

### Ordem no caminho `unico`

Na mesma transação, **antes** da porta de envio:

1. Identificar (ou pular a porta se a lista estiver vazia → `nenhum`)
2. Ler `preco_atual` uma vez; calcular valor
3. INSERT enviada (`confirmacao_consumo`)
4. `abrir_consumo`
5. UPDATE JSON da recebida (`resposta = confirmacao_consumo`, ids)
6. `enviar_texto_sessao`

Falha no INSERT desfaz confirmação e consumo. Falha no envio preserva os dois
e reagenda **só** a mensageria. Trabalho `concluido` após envio ok.

### Caminho `nenhum`

Idêntico à F3.4: enviada `confirmacao_pedido`, `abrir_servico`, zero `consumo`.
Não chama a porta se a lista de itens ativos for vazia.

### Caminho humano (`ambiguo` / `FalhaDeIdentificacao` / formato inválido)

1. INSERT enviada (`aviso_identificacao`) — sem valor
2. UPDATE JSON: `desfecho` `item_ambiguo` ou `identificacao_indisponivel`
3. Enviar; concluir o trabalho — **não** deixar `pendente` nem `falha` por causa
   da IA (padrão F3.2/F3.3)

Zero `solicitacao`. Flag `precisa_atendimento_humano = true`.

### Idempotência do processador

| JSON da recebida já tem | Ação |
| --- | --- |
| `resposta = confirmacao_consumo` e `id_solicitacao` | não identifica de novo; não abre segundo consumo; retoma envio se a enviada ainda está `pendente` |
| `resposta = confirmacao_pedido` e `id_solicitacao` | F3.4: não abre segundo serviço |
| `resposta = aviso_identificacao` | não identifica de novo; retoma envio do aviso se pendente |

`IntegrityError` no unique de origem: trata como já registrado.

---

## O que o worker desta fatia **não** faz

- Novo tipo na allowlist
- Lançar ou dispensar (são HTTP síncronos, sem fila)
- Chamar a porta de identificação no webhook
- Copiar backoff de `interpretar_ficha`
- Ligar `precisa_atendimento_humano` no caminho `unico` ou `nenhum`
- Enviar recado no POST de lançamento

---

## Eventos de log (sem texto)

| Evento | Quando |
| --- | --- |
| `consumo_registrado` | caminho `unico` gravado |
| `consumo_ja_registrado` | reprocessamento |
| `consumo_envio_falhou` | mensageria após gravar |
| `identificacao_humana` | ambíguo / indisponível / inválido |
| `pedido_registrado` | caminho `nenhum` (evento já existente da F3.4) |

Campos: ids e `resultado`. Ausentes: conteúdo, recado, descrição, valor.
