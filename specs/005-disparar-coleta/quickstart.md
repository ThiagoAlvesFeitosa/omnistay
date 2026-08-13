# Quickstart — validar a entrega de Disparar Coleta

Roteiro manual além da suíte. Contratos em [contracts/](./contracts/).

Comandos em PowerShell, na raiz do repositório. Use `curl.exe`.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. Hotel + recepção como no quickstart da F1.1. Worker e API
devem usar a **porta falsa** de mensageria neste roteiro (padrão de desenvolvimento/teste).

---

## Cenário 0 — Esquema: `trabalho` e visão ampliada

```powershell
alembic current
docker compose exec db psql -U postgres -d omnistay -c "\d trabalho"
docker compose exec db psql -U postgres -d omnistay -c "\d+ vw_fila_do_dia"
```

**Esperado**: revisão que cria `trabalho` aplicada; visão lista `status_envio_coleta`.

---

## Cenário 1 — Cadastro enfileira sem enviar na requisição

Autentique como recepção. Com a porta falsa em modo “não envia sozinha” (só o worker envia):

```powershell
$sessao = "omnistay_sessao=<token-da-recepcao>"

curl.exe -i -X POST http://localhost:8000/reservas `
  -H "Content-Type: application/json" `
  -H "Cookie: $sessao" `
  -d "{\"nome\":\"Maria Silva\",\"telefone\":\"(11) 98765-4321\",\"data_checkin_prevista\":\"2026-08-13\",\"data_checkout_prevista\":\"2026-08-16\"}"
```

**Esperado**: `201` imediato. No banco, **antes** de rodar o worker:

- 1 linha em `mensagem` (`direcao = enviada`, `status_envio = pendente`);
- 1 linha em `trabalho` (`tipo = enviar_coleta`, `status = pendente`);
- reserva `aguardando_cadastro` intacta.

```powershell
curl.exe -i http://localhost:8000/fila-do-dia -H "Cookie: $sessao"
```

**Esperado**: item com `status_envio_coleta`: `pendente`.

---

## Cenário 2 — Worker envia com sucesso (porta falsa)

Dispare uma passagem do consumidor (comando documentado na implementação, ex.
`python -m worker` com uma iteração, ou helper de teste).

**Esperado**:

- `trabalho.status = concluido`
- `mensagem.status_envio = enviada`
- porta falsa registrou **um** envio para `5511987654321`
- `GET /fila-do-dia` → `status_envio_coleta`: `enviada`
- corpo da mensagem contém lista numerada, opcionalidade, finalidade, contato do
  responsável; único dado pessoal do hóspede no texto = primeiro nome `Maria`

---

## Cenário 3 — Falha de envio não apaga a reserva

Configure a porta falsa para falhar. Cadastre outra reserva e rode o worker até esgotar
tentativas (ou force `tentativas_max_envio_mensagem = 1` no hotel de teste).

**Esperado**:

- reserva ainda existe e aparece na fila
- `status_envio_coleta`: `falha` (ou `pendente` entre tentativas)
- `trabalho` em `falha` após o teto
- exatamente uma `mensagem` de coleta para aquela reserva (sem duplicar no retry)

---

## Cenário 4 — Retry não duplica pedido

Com falha na primeira tentativa e sucesso na segunda (porta falsa contável):

**Esperado**: um único registro de envio bem-sucedido na porta falsa; uma única `mensagem`;
fila mostra `enviada`.

---

## Cenário 5 — Cadastro recusado não enfileira

```powershell
curl.exe -i -X POST http://localhost:8000/reservas `
  -H "Content-Type: application/json" -H "Cookie: $sessao" `
  -d "{\"nome\":\"X\",\"telefone\":\"123\",\"data_checkin_prevista\":\"2026-08-13\",\"data_checkout_prevista\":\"2026-08-16\"}"
```

**Esperado**: `422`. Contagem de `trabalho` / `mensagem` do hotel **não** aumenta.

---

## Cenário 6 — Parâmetro de contato no bootstrap

```powershell
docker compose exec db psql -U postgres -d omnistay -c "SELECT chave, valor FROM parametro_hotel WHERE chave IN ('contato_responsavel_dados','tentativas_max_envio_mensagem');"
```

**Esperado**: ambas as chaves presentes no hotel bootstrap; contato não vazio.

---

## Suíte automatizada

```powershell
pytest testes/unitarios -q
pytest testes/integracao -q
```

Unitários: montagem do texto (privacidade), serviço de agendamento, fila com repositório
falso, worker com porta falsa (sucesso e falha). Integração: `POST` cria pendências; worker
contra banco real; fila do dia expõe status; falha não remove reserva; sem rede à Meta.
