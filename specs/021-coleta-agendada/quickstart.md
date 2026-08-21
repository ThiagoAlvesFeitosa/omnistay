# Quickstart — validar a Coleta Agendada

Roteiro depois de `/speckit-implement`. Contratos:
[fonte-publica.md](./contracts/fonte-publica.md),
[agendador-e-fila.md](./contracts/agendador-e-fila.md),
[registro-de-coleta.md](./contracts/registro-de-coleta.md).
Modelo: [data-model.md](./data-model.md).

Comandos na raiz do repositório. Sem fonte real de terceiro, sem React, sem
WhatsApp.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. Hotel + gestão como no quickstart da F0.3.
Migração desta fatia: `0020_coleta_agendada`. Concorrente ativo cadastrado
como na F5.1. Porta **falsa** configurada no teste (preço/nota ou falha).

```powershell
pytest testes/unitarios -q
pytest testes/integracao -q -k mercado
```

---

## 1. Semente da periodicidade

Hotel novo (bootstrap) tem `periodicidade_coleta_mercado = 24`. Hotel
migrado recebe a mesma chave na `0020` (idempotente).

```sql
SELECT valor FROM parametro_hotel
 WHERE id_hotel = :id AND chave = 'periodicidade_coleta_mercado';
```

**Esperado:** `24`. Apagar a chave e rodar a varredura: 0 trabalhos
`coletar_mercado`; log `periodicidade_ausente`.

---

## 2. Fonte ativa devida agenda exatamente um trabalho

Concorrente ativo, sem coleta anterior (ou última coleta mais velha que a
janela), periodicidade válida:

```powershell
python -m worker --verificar-mercado
```

**Esperado:** 1 `trabalho` `coletar_mercado` pendente com
`payload.id_concorrente`. Segunda passagem: 0 extras. Segundo INSERT
aberto do mesmo concorrente viola
`uq_trabalho_coletar_mercado_concorrente_aberto`.

`--uma-passagem` **não** cria esse trabalho (só o consome se já existir).

Inativo na mesma propriedade: 0 trabalhos para ele.

---

## 3. Consumo grava série, nunca sobrescreve

Com o trabalho pendente e a porta falsa devolvendo preço (ex. `150.00`) e
nota (`4.50`):

```powershell
python -m worker --uma-passagem
```

**Esperado:** 1 linha em `coleta_mercado`, `sucesso = true`, data preenchida,
trabalho `concluido`. A falsa foi consultada **depois** da diretiva
`permite`. Log com `id_concorrente` e desfecho, sem URL e sem HTML.

Segundo ciclo (avançar o relógio além de 24 h, verificar + consumir):

**Esperado:** 2 linhas; a primeira intacta (mesmo `id_coleta`, mesmos
valores, mesma data).

---

## 4. Falha datada ≠ preço zero

| Cenário na falsa | `sucesso` | `preco` | Anterior |
| --- | :---: | --- | --- |
| Diretiva `recusa` ou `ausente` | `false` | nulo | intacta |
| `indisponivel` / `exige_autenticacao` / `sem_dado` | `false` | nulo | intacta |
| Preço público `0` | `true` | `0` | — |

Diretiva que não permite: 0 chamadas a `coletar_publico`.

---

## 5. Isolamento e identidade

Dois hotéis, mesma URL cadastrada em ambos: cada um tem a própria série e
a própria periodicidade. Ciclo de B não visita ficha de A.

Identidade da falsa: reconhecível como coletor OmniStay, não como
navegador de pessoa.

---

## Suíte

```powershell
pytest testes/unitarios -q
pytest testes/integracao/test_coleta_mercado.py testes/integracao/test_garantias_do_banco.py -q
```

Unitários: janela devida, diretiva, falha vs zero, inativo, periodicidade
ausente, log sem conteúdo de página, política inalterada. Integração:
unicidade do trabalho aberto, INSERT da série, CHECK de sucesso, isolamento,
`--verificar-mercado` vs `--uma-passagem`.
