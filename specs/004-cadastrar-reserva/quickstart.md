# Quickstart — validar a entrega de Cadastrar Reserva

Roteiro manual além da suíte. Contratos em [contracts/api-de-hospedagem.md](./contracts/api-de-hospedagem.md).

Comandos em PowerShell, na raiz do repositório. Use `curl.exe`.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente ou `.env`. É preciso existir hotel + usuário de recepção (bootstrap
cria só o gestor — crie a recepção com `POST /usuarios` autenticado como gestor, como no
quickstart da F0.3).

---

## Cenário 0 — Visão ampliada

```powershell
alembic current
docker compose exec db psql -U postgres -d omnistay -c "\d+ vw_fila_do_dia"
```

**Esperado**: revisão `0003_fila_do_dia` (ou `head` que a inclua). A visão lista
`telefone_contato` e `data_checkout_prevista` além das colunas anteriores.

---

## Cenário 1 — Recepção cria reserva válida

Autentique como recepção e guarde o cookie (ver quickstart F0.3). Depois:

```powershell
$sessao = "omnistay_sessao=<token-da-recepcao>"

curl.exe -i -X POST http://localhost:8000/reservas `
  -H "Content-Type: application/json" `
  -H "Cookie: $sessao" `
  -d "{\"nome\":\"Maria Silva\",\"telefone\":\"(11) 98765-4321\",\"data_checkin_prevista\":\"2026-08-20\",\"data_checkout_prevista\":\"2026-08-23\"}"
```

**Esperado**: `201`, `status` = `aguardando_cadastro`, `telefone_contato` = `5511987654321`.

No banco: uma linha em `reserva`, uma em `hospede`, uma em `reserva_hospede` com `titular` e
`ficha_completa = false`.

---

## Cenário 2 — Aparece na fila do dia

```powershell
curl.exe -i http://localhost:8000/fila-do-dia -H "Cookie: $sessao"
```

**Esperado**: `200`, item com o nome Maria Silva, telefone canônico, datas, status
`aguardando_cadastro`, `ficha_completa: false`.

---

## Cenário 3 — Telefone inválido e datas invertidas

```powershell
curl.exe -i -X POST http://localhost:8000/reservas `
  -H "Content-Type: application/json" -H "Cookie: $sessao" `
  -d "{\"nome\":\"X\",\"telefone\":\"123\",\"data_checkin_prevista\":\"2026-08-20\",\"data_checkout_prevista\":\"2026-08-23\"}"

curl.exe -i -X POST http://localhost:8000/reservas `
  -H "Content-Type: application/json" -H "Cookie: $sessao" `
  -d "{\"nome\":\"X\",\"telefone\":\"11987654321\",\"data_checkin_prevista\":\"2026-08-23\",\"data_checkout_prevista\":\"2026-08-20\"}"
```

**Esperado**: ambos `422`. Contagem de `reserva` no hotel **não** aumenta.

---

## Cenário 4 — Staff e gestor na fila e no cadastro

Autentique como `staff` e como `gestor` e repita o `POST /reservas` e o `GET /fila-do-dia`.

**Esperado**: `403` em todos. Nada gravado pelo staff/gestor. Gestão **não** vê a lista.

---

## Cenário 5 — Contagem de chegadas (gestão vê só o número)

Com pelo menos uma reserva cujo check-in previsto é **hoje**, autentique como gestor:

```powershell
$sessaoGestor = "omnistay_sessao=<token-do-gestor>"
curl.exe -i http://localhost:8000/indicadores/chegadas-do-dia -H "Cookie: $sessaoGestor"
```

**Esperado**: `200` e corpo apenas com `quantidade` (inteiro ≥ 1). Sem `itens`, sem nome, sem
telefone.

Repita como `staff`: **Esperado** `403`.

Repita como recepção: **Esperado** `200` com o mesmo número.

---

## Cenário 6 — Telefone repetido cria hóspede novo

Cadastre duas reservas com o **mesmo** telefone canônico e nomes diferentes.

**Esperado**: ambas `201`; no banco, **duas** linhas em `hospede` com o mesmo telefone e
`id_hospede` distintos.

---

## Cenário 7 — Isolamento entre hotéis

Com segundo hotel e recepção dele (ambiente de teste ou inserção controlada), crie uma reserva
em cada um e liste a fila em cada sessão.

**Esperado**: cada fila mostra só a reserva do próprio hotel. A contagem de cada sessão só
reflete o próprio hotel.

---

## Cenário 8 — Sem sessão

```powershell
curl.exe -i -X POST http://localhost:8000/reservas `
  -H "Content-Type: application/json" `
  -d "{\"nome\":\"X\",\"telefone\":\"11987654321\",\"data_checkin_prevista\":\"2026-08-20\",\"data_checkout_prevista\":\"2026-08-23\"}"

curl.exe -i http://localhost:8000/fila-do-dia
curl.exe -i http://localhost:8000/indicadores/chegadas-do-dia
```

**Esperado**: `401` nos três.

---

## Suíte automatizada

```powershell
pytest testes/unitarios -q
pytest testes/integracao -q
```

Unitários cobrem telefone, datas, serviço de reserva/fila/contagem; integração cobre rotas,
atomicidade, isolamento, telefone repetido e corpo mínimo da contagem.
