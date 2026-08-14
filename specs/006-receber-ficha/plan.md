# Implementation Plan: Receber e Interpretar a Ficha

**Branch**: `006-receber-ficha` | **Date**: 2026-08-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-receber-ficha/spec.md`

## Summary

O hóspede responde à coleta em texto livre. O webhook grava o evento (idempotente), a
mensagem de entrada e um trabalho `interpretar_ficha` na mesma transação, e responde
rápido. O worker extrai campos via `LLMProvider` (falso nos testes), consolida o titular
provisório e transiciona a reserva para `ficha_recebida` ou `ficha_parcial`. Resposta
irreconhecível ou falha do extrator preserva o texto, não inventa campos, não manda nova
mensagem ao hóspede e sinaliza leitura humana na fila do dia. Idade nunca é persistida.

Decisões em [research.md](./research.md): gravar+enfileirar no webhook; porta LLM + falsa;
orquestração no worker (sem ciclo conversa↔hospedagem); desfecho em
`classificacao_bruta` + `estado_cadastro` na fila; ampliação do `CHECK` de `trabalho.tipo`.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary, httpx (já
no projeto). **Nenhuma dependência nova.** `LLMProvider` falso na suíte; adaptador real de
LLM pode entrar depois sem mudar o domínio (Artigo X / XI)

**Storage**: PostgreSQL 16. Reuso de `evento_webhook`, `mensagem`, `hospede`,
`reserva_hospede`, `reserva`, `trabalho`. Revisão Alembic: ampliar `ck_trabalho_tipo` com
`interpretar_ficha`; índice de unicidade do trabalho de interpretação por mensagem; visão /
contrato da fila com `estado_cadastro`

**Testing**: pytest. Unitários sem rede (extração/validação de campos, serviço de
recebimento, consolidação, LLM falso, log sem conteúdo). Integração com PostgreSQL real:
webhook idempotente; completo / parcial / irreconhecível; falha do extrator; fila do dia;
nenhuma mensagem de cobrança ao hóspede

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em contêiner.
API + worker (já existentes)

**Project Type**: Serviço web + worker. Sem frontend nesta fatia

**Performance Goals**: Webhook responde em segundos (grava + enfileira). Interpretação
assíncrona no worker — volume do MVP (dezenas/minuto)

**Constraints**: Interpretação nunca na thread HTTP do webhook; `id_hotel` em toda consulta;
conteúdo de mensagem nunca em log; testes sem provedor real de IA nem Meta; foto de
documento rejeitada; idade não persistida; parcial sem nova mensagem ao hóspede

**Scale/Scope**: 1 porta nova (`LLMProvider`), 1 tipo de trabalho, router de webhook em
`conversa`, consolidação em `hospedagem`, acréscimo à fila do dia, 1 endpoint de leitura da
ficha para recepção. Sem React

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas duas passagens,
sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Ficha fica no OmniStay; transcrição ao PMS continua humana |
| II — Na dúvida, humano vê | Irreconhecível / falha do extrator → leitura humana; sem resposta inventada |
| III — Gravar antes de processar | Webhook grava evento + mensagem + trabalho; LLM só no worker |
| IV — Fila como verdade | Estado na fila do dia / histórico recupera o alerta; WhatsApp é conveniência |
| V — Ausência humana visível | Leitura humana e ficha parcial ficam perceptíveis na fila |
| VI — Confirmação antes de tramitar | Não se aplica a solicitação/reclamação nesta fatia; coleta não gera confirmação automática de “pedido” |
| VII — Não ser intrusivo | Parcial/irreconhecível **não** disparam nova mensagem; lembrete é F1.4 |
| VIII — Minimização | Sem foto de documento; sem idade persistida; log sem conteúdo |
| IX — Garantias no banco | `UNIQUE` em `evento_webhook`; trigger de transição; `CHECK` de tipo de trabalho |
| X — Portas trocáveis | `LLMProvider` + falsa; domínio sem adaptador concreto |
| XI — Complexidade exige problema | Sem fila externa; reusa `trabalho`; sem lib nova de NLP |
| XII — Teste primeiro | Cada desfecho com teste que falha por ausência |
| XIII — Parâmetro não é constante | Sem novo prazo mágico nesta fatia (F1.4 trará lembrete) |
| XIV — Multi-tenant | Resolução de reserva e consolidação sempre com `id_hotel` |
| XV — Honestidade | Sem React; sem atendimento conversacional; sem sobrescrita de ficha já consolidada |

**Ponto de atenção 1 — ciclo entre módulos.** `hospedagem` já importa `conversa` (agendar
coleta). Interpretação **não** pode fazer `conversa` importar `hospedagem`. O **worker**
orquestra: extrai via `conversa` + consolida via `hospedagem` (lição F0.3 / F1.2).

**Ponto de atenção 2 — sinal “leitura humana”.** Não há quinto status de ciclo de vida. O
desfecho fica em `mensagem.classificacao_bruta` e na projeção `estado_cadastro` da fila
(reseach §5).

**Ponto de atenção 3 — webhook público.** Assinatura + desafio GET são obrigatórios na
arquitetura; a suíte exercita o contrato com segredo de teste, sem rede Meta.

## Project Structure

### Documentation (this feature)

```text
specs/006-receber-ficha/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── webhook-e-entrada.md
│   ├── api-de-hospedagem.md
│   ├── llm-e-fila.md
│   └── politica-de-autorizacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
app/
├── portas/
│   ├── mensageria.py              # Já existe
│   └── llm.py                     # Protocol LLMProvider (extrair_ficha)
├── adaptadores/
│   ├── mensageria_falsa.py        # Já existe
│   ├── llm_falso.py               # Desfechos determinísticos por fixture
│   └── llm_*.py                   # Opcional / ambiente real — suíte não instancia
├── fila/
│   ├── repository.py              # + tipo interpretar_ficha + unicidade
│   └── service.py                 # + enfileirar_interpretar_ficha
├── comum/
│   └── telefone.py                # Reusado na correlação inbound
└── modulos/
    ├── conversa/
    │   ├── router.py              # GET/POST webhook
    │   ├── service.py             # Receber evento, gravar entrada, extrair (sem consolidar)
    │   ├── repository.py          # evento_webhook, mensagem recebida, classificacao_bruta
    │   ├── schema.py              # Payloads normalizados de entrada (teste/contrato)
    │   ├── texto_coleta.py        # CAMPOS_FICHA reusado como alvo da extração
    │   └── validacao_ficha.py     # Funções puras: data, documento, CEP — sem idade
    ├── hospedagem/
    │   ├── service.py             # consolidar_ficha_titular / transição de status
    │   ├── repository.py          # UPDATE hospede + ficha_completa + status reserva
    │   ├── schema.py              # ItemFilaDoDia.estado_cadastro; FichaTitularResposta
    │   └── router.py              # GET /reservas/{id}/ficha (recepção)
    └── acesso/
        └── politica.py            # Confirmar operação de leitura de ficha

worker/
└── consumidor.py                  # Branch interpretar_ficha: LLM → conversa → hospedagem

alembic/versions/
├── 0006_interpretar_ficha.py
└── sql/
    └── 0006_interpretar_ficha.sql

testes/
├── unitarios/
│   ├── adaptadores/ ou portas/
│   │   └── test_llm_falso.py
│   ├── fila/
│   └── modulos/
│       ├── conversa/
│       │   ├── test_receber_mensagem.py
│       │   ├── test_extracao_ficha.py
│       │   ├── test_validacao_ficha.py
│       │   └── test_log_sem_conteudo.py   # Estende cenários de entrada
│       └── hospedagem/
│           └── test_consolidar_ficha.py
└── integracao/
    ├── test_webhook_coleta.py           # Idempotência + gravação
    ├── test_interpretar_ficha.py        # Completo / parcial / irreconhecível / falha LLM
    └── test_fila_do_dia.py              # estado_cadastro

docs/
├── 04-schema.sql                        # CHECK trabalho + visão estado_cadastro
└── 04-modelagem-de-dados.md             # Se necessário alinhar narrativa
```

**Structure Decision**: monolito modular existente. `conversa` passa a ser dono de webhook +
entrada; `hospedagem` continua dono de `hospede`/`reserva`; worker orquestra para evitar
ciclo de import. Sem frontend.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Lembrete por silêncio / `sem_cadastro_previo` | Só resposta do hóspede consolida | F1.4 |
| Atendimento conversacional (dúvida, pedido, reclamação) | Mensagem fora de `aguardando_cadastro` não abre fluxo F3 | Fatias P3 |
| Sobrescrita de ficha já consolidada | Segunda mensagem não reabre coleta | Evolução futura se necessário |
| Webhook de status de entrega → `entregue` | Continua fora | Fatia de status Meta |
| Tela React | Estado via API | Fatia de UI |
| Adaptador LLM real obrigatório na suíte | Porta falsa determina desfechos | Operação / sandbox |
| Auxílios de cópia para o PMS | Transcrição manual | Fora do MVP (Artefato 2) |

## Complexity Tracking

> Sem violações a justificar. Tabela omitida.
