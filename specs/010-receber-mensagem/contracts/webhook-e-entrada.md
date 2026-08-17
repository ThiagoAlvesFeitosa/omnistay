# Contrato: Webhook e entrada de mensagem (F3.1)

Estende [o contrato da F1.3](../../006-receber-ficha/contracts/webhook-e-entrada.md).
Fila: [fila-e-worker.md](./fila-e-worker.md). Autorização:
[politica-de-autorizacao.md](./politica-de-autorizacao.md). Modelo:
[data-model.md](../data-model.md).

Canal público. Sem sessão de painel.

---

## Convenções

| Tema | Regra |
| --- | --- |
| Autenticidade | Corpo cru + HMAC-SHA256 **antes** de qualquer INSERT |
| Persistência | `evento_webhook` (+ mensagem/trabalho quando aplicável) **antes** da resposta de sucesso |
| Processamento lento | Nunca na thread HTTP (sem LLM, sem envio, sem classificação) |
| Idempotência | Mesmo `id_externo` → `200` sem segundo efeito |
| Logs | Sem conteúdo de mensagem, sem payload bruto, sem telefone em claro |

---

## `GET /webhook` — verificação de posse

Inalterado em relação à F1.3.

| Condição | Resposta |
| --- | --- |
| `hub.mode=subscribe` e token confere | `200` com o challenge em texto |
| Token inválido ou ausente | `403` sem challenge |

Não grava mensagem.

---

## `POST /webhook` — notificação

**Entrada:** envelope assinado. Cabeçalhos: `X-Hub-Signature-256` (provedor) ou
`X-Omnistay-Signature` (suíte). Segredo: `WHATSAPP_APP_SECRET`.

Evento interno normalizado:

| Campo | Significado |
| --- | --- |
| `id_externo` | Identificador único do evento/notificação |
| `telefone_origem` | Remetente, quando houver mensagem |
| `texto` | Texto utilizável, se houver |
| `tem_texto_utilizavel` | `false` para mídia sem texto |
| `id_mensagem_canal` | Id da mensagem no canal, se distinto do evento |
| `instante_origem` | Opcional; vira `mensagem.enviada_em` |

### Recusas (nada gravado)

| Situação | HTTP |
| --- | --- |
| Assinatura ausente | `401` |
| Assinatura inválida | `401` |
| Segredo do canal ausente/vazio | `401` |
| JSON ilegível | `400` |
| Envelope que não é mensagem nem status de entrega | `400` |

### Aceitações

| Situação | HTTP | Efeito |
| --- | --- | --- |
| Evento novo + texto + reserva `aguardando_cadastro` | `200` | evento + mensagem + `interpretar_ficha` (F1.3) |
| Evento novo + texto + reserva `hospedado` (e não a anterior) | `200` | evento + mensagem + `classificar_mensagem` `pendente` |
| Evento novo + sem reserva elegível / telefone inválido | `200` | só `evento_webhook` |
| Evento novo + mídia sem texto | `200` | só `evento_webhook` |
| Envelope de status de entrega (entregue/lida) | `200` | sem `mensagem` de hóspede; evento se houver id |
| `id_externo` repetido | `200` | zero efeito novo |
| Banco indisponível | `5xx` | sem commit; o provedor reenvia |

A resposta `200` **não** espera worker, LLM nem envio.

Corpo de sucesso (já usado na F1.3): `{"ok": true, "status": "<desfecho>"}` com
`status` ∈ `enfileirado` | `duplicado` | `sem_reserva` | `sem_texto` |
`telefone_invalido` | (outros já existentes, sem inventar conversa).

### Efeitos proibidos no POST

- Chamar `LLMProvider`
- Enviar mensagem ao hóspede
- Alterar `reserva.status`, `checkin_em` ou ficha
- Preencher `intencao` / `sentimento` / `urgencia`
- Reclamar ou concluir trabalho `classificar_mensagem`

---

## Caminho de teste

A suíte assina o envelope com o segredo de teste (`X-Omnistay-Signature` / HMAC) e posta
em `/webhook`. Precisa haver `WHATSAPP_APP_SECRET` no ambiente da app de teste — caso
contrário o POST é `401` (falha fechada).

Não há helper que “pule” a assinatura no caminho HTTP. Serviço de domínio pode ser
chamado nos unitários já com `EventoEntrada` (a autenticidade é da borda).

---

## O que este contrato ainda não faz

- Classificação (F3.2) e resposta (F3.3)
- Atualizar `mensagem.status_envio` a partir de webhook de entrega
- Roteamento multi-hotel por vários números de negócio (MVP: `WHATSAPP_ID_HOTEL`)
