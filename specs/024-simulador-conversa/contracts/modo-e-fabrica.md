# Contrato: modo de canal e fábrica de mensageria

Configuração e escolha do adaptador. API da tela:
[api-do-simulador.md](./api-do-simulador.md). Entrada:
[entrada-simulada.md](./entrada-simulada.md). Autorização:
[politica-de-autorizacao.md](./politica-de-autorizacao.md).

---

## Configuração

| Chave | Valores | Onde |
| --- | --- | --- |
| `MENSAGERIA_MODO` | `demonstracao` \| `real` | Ambiente / `.env`. Sem valor versionado |

Não é `parametro_hotel`. Um valor por processo.

Ausente, vazio ou outro texto: `construir_mensageria` **falha alto**
(exceção de configuração). O worker não envia “no escuro”.

`.env.example` lista a chave **sem valor**.

---

## Fábrica

```text
construir_mensageria(config) → MensageriaGateway
```

| Modo | Classe | Rede |
| --- | --- | --- |
| `demonstracao` | `MensageriaSimulada` | Nenhuma |
| `real` | `MensageriaWhatsapp` | Graph API (já existente; suíte **não** instancia) |

`python -m worker` (sem injeção) usa a fábrica. `processar_uma_passagem`
continua aceitando `gateway=` — a suíte injeta `MensageriaFalsa`.

O módulo `conversa.service` **não** importa classe de adaptador.

---

## `MensageriaSimulada`

Implementa o Protocol completo (`enviar_coleta`, `enviar_lembrete`,
`enviar_boas_vindas`, `enviar_texto_sessao`, `enviar_pulso`,
`enviar_pesquisa_saida`, `enviar_lista_pedidos_chat`).

- Sucesso: `ResultadoEnvio(id_externo="sim-{id_mensagem}")`
- Não chama HTTP
- Não tem `falhar_sempre` / `falhas_restantes` (isso é da falsa de teste)
- Não grava tabela própria: o texto já está em `mensagem` **antes** da
  chamada (Artigo III). O sucesso só autoriza `status_envio = enviada`

Falha só se o teste futuro a injetar como porta falsa — a classe de
runtime não oferece gancho de falha.

---

## `MensageriaFalsa` (fora do runtime desta fatia)

Permanece na suíte. Não é o adaptador de `demonstracao`. Tem ganchos de
falha para backoff. Worker de produção/demo **não** a instancia.

---

## `MensageriaWhatsapp`

Já existe. Esta fatia **passa a escolhê-lo** quando o modo é `real`.
Nenhum teste o instancia. `httpx` vira dependência principal para o
processo subir nesse modo.

---

## Isolamento

| Modo | Saída ao hóspede | POST da tela |
| --- | --- | --- |
| `demonstracao` | Só `MensageriaSimulada` | Autorizado (sessão + operação) |
| `real` | Só `MensageriaWhatsapp` | `409 modo_real` |

Não há mistura de adaptadores no mesmo processo.

---

## Logs

`modo=%s` (valor da configuração), classe escolhida, `id_mensagem`,
código de falha de configuração. **Sem** corpo de mensagem.
