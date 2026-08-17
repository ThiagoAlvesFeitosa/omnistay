# Quickstart — validar a entrega do Catálogo da Propriedade

Roteiro manual além da suíte. Contratos em [contracts/](./contracts/).

Comandos em PowerShell, na raiz do repositório. Use `curl.exe`.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. Hotel + usuários como no quickstart da F0.3 / F1.1
(recepção, gestão, operação). **Não** há migração nova nesta fatia: `catalogo_item` já
existe desde a `0001`.

API no ar. Sem worker.

---

## Cenário 1 — Recepção cadastra um fato em cada categoria

Com cookie de recepção:

```powershell
curl.exe -s -b cookies-recepcao.txt -c cookies-recepcao.txt -H "Content-Type: application/json" -d "{\"categoria\":\"horario\",\"titulo\":\"Cafe da manha\",\"conteudo\":\"7h as 10h\"}" http://127.0.0.1:8000/catalogo
```

Repita para `cardapio`, `servico`, `programacao` e `regra`.

**Esperado**: `201`, `ativo: true`, `id_catalogo_item` distinto. Categoria inválida ou
título em branco → `422`, nada gravado.

---

## Cenário 2 — Manutenção lista inativos; ativo omite

```powershell
curl.exe -s -b cookies-recepcao.txt http://127.0.0.1:8000/catalogo
curl.exe -s -b cookies-recepcao.txt -H "Content-Type: application/json" -X PATCH -d "{\"ativo\":false}" http://127.0.0.1:8000/catalogo/1
curl.exe -s -b cookies-recepcao.txt http://127.0.0.1:8000/catalogo/ativo
```

**Esperado**: GET de manutenção ainda mostra o item com `ativo: false`. GET ativo: o item
não aparece; as cinco chaves existem; categorias sem item são `[]`.

Reative com `"ativo": true` e confira o retorno ao GET ativo.

---

## Cenário 3 — Gestão consulta e não altera

Cookie de gestão, mesmos GETs: `200`. POST ou PATCH: `403`.

---

## Cenário 4 — Operação recusada; outro hotel isolado

Cookie de `staff`: GET e POST → `403`.

Com recepção do hotel B, GET `/catalogo` não lista itens do hotel A. PATCH no id do
hotel A → `404`.

---

## Cenário 5 — Sem apagar

```powershell
curl.exe -s -o NUL -w "%{http_code}" -b cookies-recepcao.txt -X DELETE http://127.0.0.1:8000/catalogo/1
```

**Esperado**: `405`. O item continua na manutenção.

---

## Suíte

```powershell
pytest testes/unitarios -q
pytest testes/integracao/test_catalogo.py -q
```

Unitários: validação (trim, categoria, título longo), política `ler_catalogo`, log sem
texto do fato, `CatalogoFalso`. Integração: rotas, isolamento, desativar/reativar, `CHECK`
se exercitado no repositório.
