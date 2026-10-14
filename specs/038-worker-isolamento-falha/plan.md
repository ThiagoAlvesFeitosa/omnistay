# Implementation Plan: O worker não para por causa de um trabalho

**Branch**: `038-worker-isolamento-falha` | **Date**: 2026-10-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/038-worker-isolamento-falha/spec.md`

## Summary

Exceção ao processar um trabalho **não** derruba o worker nem a
passagem: savepoint por item, falha gravada só com o **nome** da
classe, retentativa com o teto `tentativas_max_envio_mensagem`
(padrão 5) e o `backoff_apos` já usado na falha de envio. Rotinas
agendadas e expurgo isolam-se no ciclo. A recepção vê omissões na
Fila do dia (rótulo sky próprio, agrupado por omissão com contagem),
sem tela nova e sem “ciente”.

Decisões em [research.md](./research.md): reuso de
`registrar_falha_de_envio`; `obter_engine()` + `hide_parameters=True`;
`executar_ciclo` testável; revisão `0026` só na visão; catálogo de
frases no serviço. Sem Redis, sem parâmetro novo de espera, sem PMS.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de
desenvolvimento); TypeScript no `frontend/` já existente

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic,
pytest, Vitest. **Nenhuma dependência nova.** Sem Celery, Redis,
APScheduler

**Storage**: PostgreSQL 16. Tabela `trabalho` intocada. Visão
`vw_fila_do_dia` recriada na revisão `0026`. `parametro_hotel`
somente a chave já existente `tentativas_max_envio_mensagem`. `0001`
congelado; `docs/04-schema.sql` acompanha a visão

**Testing**: pytest — savepoint (exceção + seguinte na mesma
passagem), teto → `falha`, concluído preservado, unicidade da ficha,
CPF na mensagem da exceção ausente de log/campo, teto ilegível = 5,
ciclo com etapa forçada a falhar. Integração com banco real e
`IntegrityError`. Vitest — rótulos sky, agrupamento, ausência após
saída, mercado sem linha. Portas falsas. Relógio injetável onde a
espera for medida

**Target Platform**: Servidor Linux; desenvolvimento Windows.
Worker + API + SPA `/app`. Sem app nova

**Project Type**: Serviço web + worker. Ampliação pontual da Fila do
dia. Sem destino novo

**Performance Goals**: Um hotel no MVP; passagem continua limitada a
100 claims. Distintivos na mesma consulta da visão (subquery
agregada). Sem meta de throughput

**Constraints**: Sem PMS; sem operação nova na matriz; conteúdo e
parâmetros SQL fora do log; `id_hotel` no teto e na visão; worker
com `statement_timeout` da API; espera crescente = `backoff_apos`;
teto ausente/ilegível = 5

**Scale/Scope**: 0 tabelas novas, 0 tipos novos de trabalho, 1
revisão de visão, 1 campo JSON na linha da fila, 1 catálogo de
omissão, 1 extração `executar_ciclo`, correção do consumidor. Worker
e `TelaFila` são o núcleo

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Distintivo e retentativa não lêem PMS. Saída some o sinal pelo clique já existente |
| II — Na dúvida, humano vê | Falha definitiva vira rótulo na fila. Tipo sem frase cadastrada não inventa texto |
| III — Gravar antes de enviar | Savepoint desfaz efeito do trabalho que estourou; envio já gravado noutra passagem permanece. Sem novo canal |
| IV — Fila como verdade | Omissão está na linha da Fila do dia; não depende de push |
| V — Ausência humana visível | Sinal próprio, distinto dos quatro da 029. Sem “ciente” que esconda omissão |
| VI — Confirmação antes de tramitar | Intocado |
| VII — Não ser intrusivo | Zero recado novo ao hóspede |
| VIII — Minimização | Só nome da exceção; `hide_parameters=True`; teste com CPF na mensagem |
| IX — Garantias no banco | Status `falha` e UNIQUE de trabalho já existem. Visão só lê. Savepoint não substitui CHECK |
| X — Portas trocáveis | Testes com LLM/mensageria/fonte falsos. Sem porta nova |
| XI — Complexidade exige problema | Sem fila extra, sem lib, sem tela, sem chave de backoff. Extração do ciclo = problema presente (teste da US3) |
| XII — Teste primeiro | Cada FR com teste que falha por ausência |
| XIII — Parâmetro não é constante | Teto em `parametro_hotel` (padrão 5 já existente). Espera = regra técnica já usada na falha de envio — clarificação de 14/10 |
| XIV — Multi-tenant | Teto e visão filtrados por `id_hotel` do trabalho / da sessão |
| XV — Honestidade | Worker não promete ordem entre mensagens nem HA. Mercado sem reserva não aparece na fila. Tipo futuro sem frase não ganha rótulo inventado |

**Ponto de atenção 1 — transação única da passagem.** É o defeito
raiz do 18/09. Savepoint por trabalho é o mínimo que satisfaz FR-005
sem reescrever todos os testes que passam `conexao`.

**Ponto de atenção 2 — Artigo XIII vs espera crescente.** A spec
proíbe parâmetro novo de espera e manda reusar `backoff_apos`. Não é
número mágico introduzido aqui; é a curva já vigente na falha de
envio.

**Ponto de atenção 3 — `hide_parameters` e timeout no worker.** O
estado do projeto já lista os dois como pendentes da auditoria. Esta
fatia os fecha porque FR-007 e FR-011 os exigem. Worker passa a
`obter_engine()`; o `create_engine` solto em `__main__` some.

**Ponto de atenção 4 — conformidade do esquema.** Só a visão muda;
`04-schema.sql` e revisão `0026` juntos. `0001` congelado.

**Ponto de atenção 5 — documentação viva.** Ao implementar, o
achado alto “exceção derruba o worker” em
`docs/00-ESTADO-DO-PROJETO.md` deixa de ser pendência desta fatia —
atualizar o estado, não silenciar.

## Project Structure

### Documentation (this feature)

```text
specs/038-worker-isolamento-falha/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── isolamento-da-passagem.md
│   ├── ciclo-do-worker.md
│   ├── logs-e-erro.md
│   └── distintivos-fila-do-dia.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
app/
├── database.py                 # hide_parameters=True
├── fila/
│   ├── service.py              # teto ilegível → 5; registrar_falha reusado
│   └── repository.py           # reclamar ignora falha (já ignora)
├── modulos/hospedagem/
│   ├── schema.py               # omissoes[]
│   ├── service.py              # agrega catálogo de omissão
│   └── repository.py           # lê JSON da visão
worker/
├── consumidor.py               # savepoint + except por trabalho
└── __main__.py                 # executar_ciclo; obter_engine()
alembic/versions/0026_*.py      # vw_fila_do_dia
docs/04-schema.sql              # mesma visão
frontend/src/painel/
├── fila.ts                     # tipo omissoes
├── TelaFila.tsx                # rótulos sky
└── TelaFila.test.tsx
testes/unitarios/worker/
testes/unitarios/fila/
testes/integracao/              # unicidade + GET fila
```

**Structure Decision**: corrige o consumidor e o laço já existentes
(F1.2+, F6.1) e estende a linha da Fila do dia (029). Sem módulo
Python novo, sem segundo app, sem tipo novo em `trabalho`.

## Complexity Tracking

> Nenhum item: o Constitution Check passou nas duas passagens.
> Extração de `executar_ciclo` e o catálogo de omissões estão
> justificados no Artigo XI (problema presente: laço intocável e
> frases pedidas pela spec).
