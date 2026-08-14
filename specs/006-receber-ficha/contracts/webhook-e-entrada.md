# Contrato: Webhook e entrada de mensagem

Autorização do painel: [politica-de-autorizacao.md](./politica-de-autorizacao.md).
Fila/LLM: [llm-e-fila.md](./llm-e-fila.md). Modelo: [data-model.md](../data-model.md).

Este contrato cobre o canal de **entrada** do hóspede. Não autentica sessão de painel.

---

## Convenções

| Tema | Regra |
| --- | --- |
| Persistência | `evento_webhook` (+ mensagem/trabalho quando aplicável) **antes** da resposta de sucesso |
| Interpretação | Nunca na thread HTTP; só via `trabalho` + worker + `LLMProvider` |
| Idempotência | Mesmo `id_externo` → `200` sem segundo efeito |
| Logs | Sem conteúdo de mensagem, sem payload bruto, sem telefone em claro |

---

## `GET /webhook` — verificação de posse

**Entrada**: parâmetros de desafio do provedor (hub.mode, hub.verify_token, hub.challenge —
nomes conforme integração).

| Condição | Resposta |
| --- | --- |
| Token confere | `200` com o challenge |
| Token inválido | `403` (ou `401`) sem challenge |

---

## `POST /webhook` — notificação de mensagem

**Entrada**: envelope do provedor assinado. O router valida a assinatura e normaliza para um
evento interno com pelo menos:

| Campo interno | Significado |
| --- | --- |
| `id_externo` | Identificador único do evento/notificação |
| `telefone_origem` | Número do remetente |
| `texto` | Texto utilizável, se houver |
| `tem_texto_utilizavel` | `false` para mídia sem texto / foto de documento |

### Respostas

| Situação | HTTP | Efeito |
| --- | --- | --- |
| Assinatura inválida | `401`/`403` | Nada gravado |
| Evento novo + texto + reserva em `aguardando_cadastro` | `200` | `evento_webhook` + `mensagem` recebida + `trabalho` `interpretar_ficha` |
| Evento novo + sem reserva elegível / sem texto utilizável | `200` | `evento_webhook` (e sem consolidação); mídia sem texto não cria ficha |
| `id_externo` repetido | `200` | Sem nova mensagem, sem novo trabalho, sem segunda transição |
| Banco indisponível | `5xx` | Sem commit; o provedor pode reenviar |

A resposta `200` **não** espera o LLM.

### Efeitos proibidos no POST

- Chamar `LLMProvider`
- Enviar mensagem ao hóspede (cobrança de campos, confirmação de ficha, etc.)
- Alterar `reserva.status` ou campos de `hospede` na thread HTTP

---

## Caminho de teste

A suíte pode:

1. Assinar um envelope mínimo com o segredo de teste e postar em `/webhook`, ou  
2. Expor helper interno de teste que injeta o evento já normalizado **desde que** preserve
   as mesmas invariantes (idempotência, gravação antes do worker, sem LLM na requisição).

O critério observável é o da tabela de respostas acima.

---

## O que este contrato ainda não faz

- Webhooks de status de entrega (`entregue`)
- Roteamento multi-hotel por vários números de negócio (MVP: um hotel)
- Classificação de intenções de atendimento (F3)
