# Quickstart — validar a entrega do Cadastro de Concorrentes

Roteiro manual além da suíte. Contratos em [contracts/](./contracts/).

Comandos em PowerShell, na raiz do repositório. Use `curl.exe`.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. Hotel + usuários como no quickstart da F0.3
(recepção, gestão, operação). Esta fatia **tem** migração nova:
`0019_cadastrar_concorrentes` (índice único da fonte, CHECK da URL, índice
parcial de ativos).

API no ar. Sem worker. Nenhuma chamada à URL cadastrada.

---

## Cenário 1 — Gestão cadastra um concorrente

Com cookie de gestão:

```powershell
curl.exe -s -b cookies-gestao.txt -c cookies-gestao.txt -H "Content-Type: application/json" -d "{\"nome\":\"Hotel Praia Norte\",\"url_fonte\":\"https://www.exemplo.com/hotel-praia-norte\"}" http://127.0.0.1:8000/concorrentes
```

**Esperado**: `201`, `ativo: true`, `id_concorrente` preenchido. Nome em
branco, `mailto:x@y.com` ou `www.exemplo.com` sem esquema → `422`, nada
gravado. Segunda POST com a mesma URL (ou só mudando maiúsculas) → `409`.

---

## Cenário 2 — Manutenção lista inativos; ativos omitem

```powershell
curl.exe -s -b cookies-gestao.txt http://127.0.0.1:8000/concorrentes
curl.exe -s -b cookies-gestao.txt -H "Content-Type: application/json" -X PATCH -d "{\"ativo\":false}" http://127.0.0.1:8000/concorrentes/1
curl.exe -s -b cookies-gestao.txt http://127.0.0.1:8000/concorrentes/ativos
```

**Esperado**: GET de manutenção ainda mostra a ficha com `ativo: false`. GET
ativos: a ficha não aparece; hotel sem ativo devolve `"fontes": []`.

Reative com `"ativo": true` e confira o retorno ao GET ativos. POST de outra
ficha com a URL da desativada → `409` (reativar, não duplicar).

---

## Cenário 3 — Recepção e operação recusadas

Cookie de recepção ou de `staff`: GET, POST e PATCH → `403`.

---

## Cenário 4 — Outro hotel isolado

Com gestão do hotel B, GET `/concorrentes` não lista fichas do hotel A. PATCH
no id do hotel A → `404`. A mesma URL pode ser cadastrada no hotel B (`201`).

---

## Cenário 5 — Sem apagar e sem visitar a fonte

```powershell
curl.exe -s -o NUL -w "%{http_code}" -b cookies-gestao.txt -X DELETE http://127.0.0.1:8000/concorrentes/1
```

**Esperado**: `405`. A ficha continua na manutenção. Nenhuma linha nova em
`coleta_mercado`.

---

## Suíte

```powershell
pytest testes/unitarios -q
pytest testes/integracao/test_concorrentes.py testes/integracao/test_garantias_do_banco.py -q
```

Unitários: validação (trim, URL, credencial na URL, tamanho), política das
duas operações novas, log sem nome/URL. Integração: rotas, desativar/reativar,
isolamento, `409`, `405`, unicidade e CHECK no banco, cadastro não grava
coleta.
