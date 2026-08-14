# Quickstart — validar a entrega de Receber e Interpretar a Ficha

Roteiro manual além da suíte. Contratos em [contracts/](./contracts/).

Comandos em PowerShell, na raiz do repositório. Use `curl.exe`.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. Hotel + recepção como no quickstart da F1.1.
Mensageria e LLM em **portas falsas**. API e worker no ar (`uvicorn` / `python -m worker`).

Fluxo prévio (F1.2): existir reserva do dia com coleta já enviada (`status_envio_coleta =
enviada`) e `status = aguardando_cadastro`.

---

## Cenário 0 — Esquema: tipo `interpretar_ficha` e fila

```powershell
alembic current
docker compose exec db psql -U postgres -d omnistay -c "\d trabalho"
docker compose exec db psql -U postgres -d omnistay -c "\d+ vw_fila_do_dia"
```

**Esperado**: `trabalho.tipo` admite `interpretar_ficha`; visão lista `estado_cadastro`.

---

## Cenário 1 — Webhook grava e não interpreta na requisição

Com a reserva elegível e LLM falso ainda não consumido pelo worker, poste um evento
assinado (ou o helper de teste documentado na implementação) com texto completo da ficha.

**Esperado imediato (antes do worker):**

- `200` do webhook
- 1 linha nova em `evento_webhook`
- 1 `mensagem` `direcao = recebida` com o texto
- 1 `trabalho` `interpretar_ficha` `pendente`
- `reserva.status` ainda `aguardando_cadastro`

Reenvie o **mesmo** `id_externo`.

**Esperado**: `200`; contagem de mensagens/trabalhos/transições **inalterada**.

---

## Cenário 2 — Resposta completa

Configure o LLM falso para devolver os nove campos válidos. Rode uma passagem do worker.

```powershell
$sessao = "omnistay_sessao=<token-da-recepcao>"
curl.exe -i http://localhost:8000/fila-do-dia -H "Cookie: $sessao"
curl.exe -i http://localhost:8000/reservas/<id>/ficha -H "Cookie: $sessao"
```

**Esperado**:

- `reserva.status = ficha_recebida`, `ficha_completa = true`
- `estado_cadastro = completa`
- ficha com `data_nascimento` e **sem** campo idade
- zero mensagens novas de saída pedindo campos
- `classificacao_bruta.desfecho = completa`

---

## Cenário 3 — Resposta parcial sem cobrança

Novo evento (novo `id_externo`) com LLM falso devolvendo só parte dos campos.

**Esperado**: `ficha_parcial`, `ficha_completa = false`, `estado_cadastro = parcial`,
nenhum `enviar_coleta` novo, nenhuma mensagem de saída cobrando o restante.

---

## Cenário 4 — Irreconhecível → leitura humana

Evento com texto que o LLM falso marca como irreconhecível (ou mídia sem texto).

**Esperado**:

- texto (ou trilha) preservado em `mensagem`
- status permanece `aguardando_cadastro`
- `estado_cadastro = leitura_humana`
- nenhum campo inventado no titular
- nenhuma mensagem ao hóspede

---

## Cenário 5 — Falha do extrator

LLM falso lança indisponibilidade até esgotar tentativas (ou force max=1).

**Esperado**: mensagem permanece; desfecho `falha_extrator`; `leitura_humana` na fila;
reserva não apagada; sem ficha inventada.

---

## Cenário 6 — Privacidade no log

Dispare qualquer desfecho acima e inspecione logs da API/worker.

**Esperado**: apenas identificadores e códigos; sem corpo da mensagem e sem campos da ficha.

---

## Cenário 7 — Autorização da ficha

Com sessão de operacional ou gestão:

```powershell
curl.exe -i http://localhost:8000/reservas/<id>/ficha -H "Cookie: $sessao_outro"
```

**Esperado**: `403`.

---

## Suíte automatizada (smoke)

```powershell
pytest testes/unitarios -q
pytest testes/integracao -k "webhook or interpretar or fila_do_dia or ficha" -q
```

**Esperado**: verde, sem rede Meta/LLM real.
