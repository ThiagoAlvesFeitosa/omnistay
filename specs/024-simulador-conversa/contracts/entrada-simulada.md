# Contrato: entrada simulada = o mesmo `receber_evento_entrada`

O POST da tela não classifica, não chama LLM e não envia recado. Só
abre a porta autenticada para o serviço que o webhook já usa.

API: [api-do-simulador.md](./api-do-simulador.md).
Modelo: [data-model.md](../data-model.md).

---

## Sequência

1. Router valida sessão, operação, modo `demonstracao`, corpo.
2. Serviço carrega a reserva `{id}` **do hotel da sessão**. Ausente →
   recusa de “não encontrada” (o router traduz `404`).
3. Monta `EventoEntrada`:
   - `id_externo` = o do cliente
   - `telefone_origem` = `reserva.telefone_contato`
   - `texto` = texto já validado
   - `tem_texto_utilizavel` = true
   - `id_mensagem_canal` = o mesmo `id_externo`
4. Chama `receber_evento_entrada(..., id_hotel=sessão)`.
5. Devolve o `status` que o serviço já devolve (`enfileirado`,
   `duplicado`, `sem_reserva`, …).

**Não** chama `POST /webhook`. **Não** verifica HMAC da Meta.

---

## Idempotência

O UNIQUE de `evento_webhook.id_externo` permanece a garantia. Segunda
chamada com o mesmo id: `receber_evento_entrada` devolve `duplicado`;
a API responde `200` sem nova linha de `mensagem` e sem novo trabalho.

O cliente da tela gera o id **antes** de enviar e reusa em retry.

---

## Resolver de reserva

Igual ao webhook. O telefone da reserva **escolhida** alimenta o
resolver; a prioridade (`aguardando_cadastro` → `hospedado` → pesquisa
de saída → encerrada) **não** é furada por `id_reserva`.

Se o telefone casar com outra reserva da casa, o comportamento é o do
canal real (mesmo telefone, duas estadias). A tela escolhe *qual
telefone usar*, não um atalho de INSERT.

`id_hotel` é o da **sessão**, nunca `whatsapp_id_hotel`.

---

## O que esta porta não faz

- Não interpreta ficha nem classifica (worker).
- Não confirma pedido/reclamação nesta requisição (worker, mesma ordem
  da F3.4/F3.5: confirmação **antes** do chamado).
- Não altera status da reserva.
- Não envia pelo provedor real.

---

## Logs

`simulador_entrada id_reserva=%s id_externo=%s status=%s` — sem texto.
