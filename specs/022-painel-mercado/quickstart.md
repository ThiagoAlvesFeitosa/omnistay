# Quickstart — validar o Painel de Mercado

Roteiro depois de `/speckit-implement`. Contratos:
[api-de-painel.md](./contracts/api-de-painel.md),
[situacao-do-dado.md](./contracts/situacao-do-dado.md),
[politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md).
Modelo: [data-model.md](./data-model.md).

Comandos na raiz do repositório. Use `curl.exe`. Sem worker, sem fonte
real, sem React, sem WhatsApp.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. Hotel + usuários como no quickstart da F0.3
(recepção, gestão, operação). **Não** há migração nova nesta fatia.

Concorrente cadastrado (F5.1). Linhas em `coleta_mercado` inseridas na
suíte ou no SQL de apoio — **não** dispare `--verificar-mercado` para
provar o painel. Periodicidade da propriedade: `24`.

API no ar.

```powershell
pytest testes/unitarios -q
pytest testes/integracao -q -k painel_mercado
```

---

## 1. Gestão vê a comparação datada

Com cookie de gestão, depois de um sucesso gravado (ex. preço `150.00`,
nota `4.50`, `coletado_em` há menos de 24 h):

```powershell
curl.exe -s -b cookies-gestao.txt http://127.0.0.1:8000/mercado
```

**Esperado**: `200`. O concorrente aparece com `ultimo_sucesso` contendo
preço, nota e `coletado_em`. `situacao` é `atual`. Nenhum número vem sem
data. `periodicidade_horas` é `24`. Hotel sem ficha: `"concorrentes": []`.

---

## 2. Dado velho e falha posterior não se disfarçam

Avançar o relógio (teste) além de 24 h desde o último sucesso, ou gravar
uma falha **depois** do sucesso, e repetir o GET.

**Esperado**: o preço/nota do sucesso permanecem com a **data do sucesso**.
`situacao` é `desatualizado`. Se houve falha posterior, `ultima_falha`
traz a data da tentativa; `preco` da falha **não** aparece como `0`.

Apagar a chave `periodicidade_coleta_mercado` (ou torná-la inválida) e
consultar: `periodicidade_horas` é `null`; concorrente com sucesso fica
`cadencia_ausente`; nada é `atual`.

---

## 3. Histórico mostra a variação e a falha intercalada

```powershell
curl.exe -s -b cookies-gestao.txt http://127.0.0.1:8000/mercado/concorrentes/1
```

**Esperado**: `200`, `coletas` em ordem cronológica crescente. Sucessos
com os valores originais; falha no meio com `sucesso: false` e preços
nulos. Id de outro hotel → `404`.

---

## 4. Recepção, operação e escrita recusadas

Cookie de recepção ou de `staff`: os dois GETs → `403`.

```powershell
curl.exe -s -o NUL -w "%{http_code}" -b cookies-gestao.txt -X POST http://127.0.0.1:8000/mercado
curl.exe -s -o NUL -w "%{http_code}" -b cookies-gestao.txt -X DELETE http://127.0.0.1:8000/mercado/concorrentes/1
```

**Esperado**: `405`. Nenhuma linha nova nem alterada em `coleta_mercado`.
Nenhum trabalho `coletar_mercado` criado. Nenhuma mensagem ao hóspede.

---

## 5. Isolamento

Com gestão do hotel B, `GET /mercado` não lista concorrentes do hotel A.
`GET /mercado/concorrentes/{id-de-A}` → `404`.

---

## Suíte

```powershell
pytest testes/unitarios -q
pytest testes/integracao/test_painel_mercado.py testes/unitarios/modulos/acesso/test_politica.py -q
```

Unitários: `situacao` (janela, falha posterior, cadência ausente, zero vs
vazio, sem coleta), política `ler_mercado`, log sem preço/nota/URL.
Integração: rotas, perfis, `404`/`405`, inativo visível, isolamento, GET
não dispara coleta.
