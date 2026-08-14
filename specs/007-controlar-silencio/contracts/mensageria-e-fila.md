# Contrato: porta MensageriaGateway e fila do lembrete

Estende [mensageria-e-fila da F1.2](../../005-disparar-coleta/contracts/mensageria-e-fila.md).
Modelo: [data-model.md](../data-model.md).

Contrato interno (domínio ↔ adaptadores ↔ worker). Não é rota HTTP.

---

## `MensageriaGateway` — operação nova `enviar_lembrete`

Mesma forma de `enviar_coleta`:

| Campo | Semântica |
| --- | --- |
| `telefone_destino` | Canônico `55…` |
| `primeiro_nome` | Único dado pessoal permitido no corpo |
| `corpo` | Texto já montado do lembrete |
| `id_mensagem` / `id_reserva` | Correlação; **não** logar PII |

| Resultado | Efeito no worker |
| --- | --- |
| Sucesso (+ `id_externo` opcional) | `mensagem.status_envio = enviada`; `enviada_em = agora` |
| Falha tipada (sem corpo) | Tentativas / backoff ou `falha` definitiva; **não** cria segunda mensagem |

`MensageriaFalsa` registra o envio de modo distinguível da coleta (`tipo = lembrete` ou
lista equivalente). Nenhum teste instancia o adaptador WhatsApp.

`enviar_coleta` permanece; o lembrete **não** a reutiliza pelo nome.

---

## Texto observável do lembrete

O corpo gravado em `mensagem.conteudo` MUST conter:

1. Saudação com **apenas** o primeiro nome
2. Declaração de que o cadastro antecipado é **opcional**
3. Declaração de que, sem ele, o preenchimento será feito na recepção

MUST NOT conter: lista numerada da ficha (já foi na coleta), telefone, documento, endereço,
sobrenome além do que o primeiro nome expõe.

---

## Trabalho `enviar_lembrete`

| Campo | Valor |
| --- | --- |
| `tipo` | `enviar_lembrete` |
| `payload` | `id_reserva`, `id_mensagem` |
| Claim | Mesmo `FOR UPDATE SKIP LOCKED` da F1.2 |
| Unicidade | No máximo um por `id_reserva` (índice parcial) |

Nascimento (mesma TX): mensagem pendente + trabalho pendente + `reenvio_realizado = true`.

### Claim / concluir / falhar

Igual à coleta. Retry **não** insere nova `mensagem` nem novo trabalho.

---

## Orquestração no worker (consumo)

```text
claim enviar_lembrete
  → conversa: ler mensagem + telefone
  → gateway.enviar_lembrete(...)
  → sucesso: status_envio enviada + enviada_em; trabalho concluido
  → falha: reagendar ou falha; reserva intacta
```

`LLMProvider` **não** participa deste tipo.

---

## Ajuste compartilhado com a coleta

Todo sucesso de envio (`enviar_coleta` e `enviar_lembrete`) atualiza `enviada_em`. O t0 do
silêncio é o sucesso da **coleta**.
