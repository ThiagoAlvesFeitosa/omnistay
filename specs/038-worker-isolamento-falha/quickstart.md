# Quickstart: isolamento de falha no worker

Validação local da F9.1. Implementação e lista de testes ficam em
`tasks.md` (ainda não gerado).

## Pré-requisitos

- PostgreSQL 16 da suíte (mesmo `DATABASE_URL` do `.env`)
- `python -m pytest` e `npm test` no `frontend/` como no restante do
  repositório
- Portas falsas: não chamar Gemini nem WhatsApp

Contratos: [isolamento-da-passagem.md](./contracts/isolamento-da-passagem.md),
[ciclo-do-worker.md](./contracts/ciclo-do-worker.md),
[logs-e-erro.md](./contracts/logs-e-erro.md),
[distintivos-fila-do-dia.md](./contracts/distintivos-fila-do-dia.md).
Modelo: [data-model.md](./data-model.md). Catálogo de frases:
[research.md](./research.md) §6.

## Setup

```bash
# na raiz
alembic upgrade head   # inclui 0026 (visão da fila)
```

Não há variável de ambiente nova. Não há chave nova em
`parametro_hotel`. Teto ausente = 5.

## O que tem de ficar verde

```bash
pytest testes/unitarios/worker testes/unitarios/fila -q
pytest -k isolamento -q
pytest testes/integracao -q -k "fila_do_dia or worker or interpretar_ficha"
cd frontend && npm test -- --run src/painel/TelaFila.test.tsx src/painel/fila.ts
```

Nomes esperados (comportamento, em português), no espírito:

- trabalho com exceção é reagendado e o seguinte da mesma passagem corre
- no teto o status fica falha e não é reclamado de novo
- concluído antes do erro do outro permanece concluído
- unicidade ao consolidar ficha não encerra o worker
- registro e log com IntegrityError cuja mensagem tem CPF **não**
  repetem o CPF
- teto ilegível usa 5
- falha na passagem ainda roda expurgo e as verificações do ciclo
- falha numa verificação não pula as outras
- linha da fila mostra rótulo sky próprio; mercado em falha não altera
  linha; dois tipos = dois rótulos; mesmo tipo = contagem
- após saída confirmada o rótulo some

## Sinais de pronto

- `python -m worker --uma-passagem` não morre se um trabalho estoura
- modo contínuo: uma rotina que levanta exceção não impede o expurgo
  daquele ciclo
- `GET /fila-do-dia` traz `omissoes` (lista, possivelmente vazia)
- nenhum teste chama rede externa
