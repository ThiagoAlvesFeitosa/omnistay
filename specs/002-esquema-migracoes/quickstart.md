# Guia de validação — Esquema e Migrações

Como comprovar, do zero, que esta fatia funciona. Cada cenário corresponde a critérios de aceite
da spec e é executável sem passo manual além dos comandos abaixo.

## Pré-requisitos

- Python 3.11+ com as dependências do projeto instaladas (`pip install -e ".[dev]"`).
- Docker, para subir o PostgreSQL 16.
- Variável `DATABASE_URL` definida. Copie `.env.example` para `.env` e ajuste se necessário.

```powershell
docker compose up -d
Copy-Item .env.example .env
```

Aguarde o banco ficar saudável antes de seguir:

```powershell
docker compose ps
```

## Cenário 0 — O ambiente sobe do zero (SC-001)

Fecha uma pendência aberta desde a fatia F0.1: o ambiente nunca foi levantado a partir do nada,
sempre a partir de um volume que já existia. Derrube o volume e reconstrua.

```powershell
docker compose down -v
docker compose up -d
docker compose ps
```

Esperado: o volume é removido, o contêiner sobe com banco vazio e o healthcheck fica saudável sem
nenhuma intervenção. Nenhum passo manual entre `down -v` e um banco pronto para receber a
migração.

Os cenários seguintes assumem este ponto de partida.

## Cenário 1 — Banco vazio chega ao esquema atual (SC-001, US1)

```powershell
alembic upgrade head
```

Esperado: o comando termina sem erro, e as tabelas passam a existir.

```powershell
docker compose exec postgres psql -U postgres -d omnistay -c "\dt"
```

Esperado: as dezesseis tabelas de domínio mais `alembic_version`.

## Cenário 2 — Aplicar de novo não faz nada (SC-004, US1)

```powershell
alembic upgrade head
```

Esperado: termina sem erro e sem executar nenhuma revisão, porque o banco já está em `head`.

## Cenário 3 — A versão do esquema é consultável (US3)

```powershell
alembic current
```

Esperado: a revisão corrente é exibida.

## Cenário 4 — Versão insuficiente do servidor aborta antes de criar qualquer coisa (FR-020)

O projeto provisiona apenas PostgreSQL 16, e subir um servidor antigo só para este cenário não se
justifica. A decisão da guarda é uma função pura, exercitada com número de versão simulado:

```powershell
pytest testes/unitarios/test_guarda_de_versao.py -v
```

Esperado: abaixo de `160000`, erro explícito nomeando a versão encontrada e a exigida; de
`160000` em diante, segue. Contra o servidor real da máquina, o Cenário 1 já comprova o caminho
positivo — se a guarda recusasse a versão 16, a migração não teria aplicado.

## Cenário 5 — O banco recusa dado inválido por conta própria (SC-003, US2)

```powershell
pytest testes/integracao/test_garantias_do_banco.py -v
```

Esperado: passam os testes de valor fora do domínio, transição de estado inválida, unicidade do
identificador externo de webhook e transição válida aceita. Os detalhes de cada garantia estão em
[data-model.md](./data-model.md).

## Cenário 6 — Documento e banco não divergem (SC-002, SC-005)

```powershell
pytest testes/integracao/test_conformidade_do_esquema.py -v
```

Esperado: passam a verificação de que nada do documento falta no banco migrado (FR-017) e a de
que os dois inventários são idênticos (FR-018). A forma do inventário comparado está em
[contracts/inventario-de-esquema.md](./contracts/inventario-de-esquema.md).

Para ver a verificação fazer o seu trabalho, acrescente uma coluna a `docs/04-schema.sql` sem
escrever a migração correspondente e rode de novo: o teste deve falhar nomeando a coluna que
sobra no documento. Faça o mesmo com uma transição a mais no corpo de
`fn_valida_transicao_reserva` — o teste também deve falhar, porque o corpo das funções entra na
comparação. Desfaça as alterações em seguida.

## Cenário 6b — O documento aplica à mão, sozinho (FR-016)

O documento não tem mais `BEGIN;`/`COMMIT;`: o controle de transação é de quem aplica. Aplicado
com a flag correta, ele leva um banco vazio ao mesmo esquema.

```powershell
docker compose exec postgres createdb -U postgres conferencia_manual
Get-Content docs/04-schema.sql | docker compose exec -T postgres psql -U postgres -d conferencia_manual --single-transaction
```

Esperado: aplica sem erro. Sem `--single-transaction`, uma falha no meio deixaria estrutura pela
metade — que é por que a flag está registrada no cabeçalho do documento.

```powershell
docker compose exec postgres dropdb -U postgres conferencia_manual
```

## Cenário 7 — Suíte sem banco não passa por suíte verificada (FR-019)

Com o banco desligado:

```powershell
docker compose stop
pytest testes -q
```

Esperado: os testes que dependem de banco aparecem como pulados, com o motivo declarado.

```powershell
$env:EXIGIR_POSTGRES = "1"; pytest testes -q
```

Esperado: os mesmos testes agora quebram a suíte, com a mensagem dizendo que o banco era exigido
e não respondeu. O pytest os reporta como `ERROR` e não como `FAILED`, porque a decisão acontece
na preparação do teste — o que importa é que a suíte não fica verde.

```powershell
Remove-Item Env:EXIGIR_POSTGRES; docker compose start
```

## Verificação completa da entrega

Do zero absoluto, na ordem, sem reaproveitar nada de execução anterior:

```powershell
docker compose down -v
docker compose up -d
alembic upgrade head
$env:EXIGIR_POSTGRES = "1"; pytest
```

Esperado: tudo verde, sem nenhum teste pulado, partindo de um volume recém-criado.
