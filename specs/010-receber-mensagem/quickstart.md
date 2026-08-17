# Quickstart — validar a entrega de Receber Mensagem com Segurança

Roteiro manual além da suíte. Contratos em [contracts/](./contracts/).

Comandos em PowerShell, na raiz do repositório. Use `curl.exe`.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. `WHATSAPP_APP_SECRET` **obrigatório** — sem ele o `POST
/webhook` responde `401`. `WHATSAPP_VERIFY_TOKEN` para o `GET`. `WHATSAPP_ID_HOTEL` do
hotel de teste.

Hotel + recepção como nos quickstarts anteriores. API no ar. Worker **não** precisa
classificar nada nesta fatia; uma passagem serve só para provar que o tipo novo
permanece pendente.

Reserva **hospedada** (F2.2): criar reserva, chegar a um estado que admite check-in
(`ficha_recebida` / `ficha_parcial` / `sem_cadastro_previo`) e `POST /reservas/{id}/chegada`.

---

## Cenário 0 — Esquema

```powershell
alembic current
```

No banco:

```sql
INSERT INTO trabalho (id_hotel, tipo, payload, status)
VALUES (1, 'classificar_mensagem', '{"id_reserva": 1, "id_mensagem": 1, "id_evento": 1}', 'pendente');
```

**Esperado:** insert aceito. Segundo insert com o mesmo `id_mensagem` viola
`uq_trabalho_classificar_mensagem_mensagem`. Limpe a linha de teste depois.

---

## Cenário 1 — Estadia: grava e responde sem classificar

Com a reserva hospedada e o telefone de contato conhecido, poste um envelope **assinado**
com texto novo (`id_externo` inédito).

**Esperado imediato (antes / independente do worker):**

- HTTP `200`, `status` de enfileirado
- 1 linha em `evento_webhook`
- 1 `mensagem` `direcao = recebida` com o texto, `id_reserva` da hospedada
- 1 `trabalho` `classificar_mensagem` `pendente`
- `reserva.status` continua `hospedado`
- `intencao`, `sentimento`, `urgencia` nulos
- nenhuma mensagem `enviada` nova nesta requisição

---

## Cenário 2 — Recusas de autenticidade

Repita o POST do cenário 1 em três variantes, cada uma com `id_externo` novo:

| Variante | Esperado |
| --- | --- |
| Sem cabeçalho de assinatura | `401`; zero linhas novas |
| Assinatura inválida | `401`; zero linhas novas |
| Segredo vazio no processo da API | `401`; zero linhas novas |

O histórico da reserva do cenário 1 permanece com uma única mensagem recebida daquele
teste.

---

## Cenário 3 — Reenvio inócuo

Reposte o **mesmo** corpo e o **mesmo** `id_externo` do cenário 1, com assinatura válida.

**Esperado:** `200`; `status` de duplicado; contagem de `mensagem` recebida e de
`classificar_mensagem` **inalterada**.

---

## Cenário 4 — Worker não come o trabalho

Com o item `pendente` do cenário 1:

```powershell
python -m worker --uma-passagem
```

```sql
SELECT tipo, status FROM trabalho
 WHERE tipo = 'classificar_mensagem'
 ORDER BY id_trabalho DESC LIMIT 1;
```

**Esperado:** `status = pendente`. Nenhum `trabalho_claim` desse tipo no log. Outros tipos
pendentes (coleta, boas-vindas) podem ser consumidos na mesma passagem.

Reiniciar a API e repetir o `SELECT` — a linha continua lá.

---

## Cenário 5 — F1.3 intacta e telefone sem estadia

1. Reserva em `aguardando_cadastro` + texto assinado → continua nascendo
   `interpretar_ficha`, **não** `classificar_mensagem`.
2. Telefone desconhecido + texto assinado → só `evento_webhook`; zero mensagem; status da
   reserva existente inalterado.
3. Reserva `ficha_recebida` ainda **sem** check-in + texto assinado → só evento; **não**
   vira `hospedado`.

---

## Cenário 6 — Log sem conteúdo

Dispare os desfechos acima e inspecione o log da API.

**Esperado:** identificadores (`id_evento`, `id_mensagem`, `id_trabalho`, `id_reserva`,
`id_externo`, `id_hotel`) e códigos. **Ausente:** o texto enviado, o telefone em claro, o
JSON cru do envelope.

---

## Cenário 7 — Posse do canal

```powershell
curl.exe -i "http://127.0.0.1:8000/webhook?hub.mode=subscribe&hub.verify_token=TOKEN_CORRETO&hub.challenge=abc"
curl.exe -i "http://127.0.0.1:8000/webhook?hub.mode=subscribe&hub.verify_token=errado&hub.challenge=abc"
```

**Esperado:** primeiro `200` com corpo `abc`; segundo `403`.
