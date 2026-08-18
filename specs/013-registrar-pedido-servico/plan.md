# Implementation Plan: Registrar Pedido de Serviço

**Branch**: `013-registrar-pedido-servico` | **Date**: 2026-08-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/013-registrar-pedido-servico/spec.md`

## Summary

Depois de classificar `pedido_de_servico`, o worker consome
`registrar_pedido_servico`: grava um recado padrão de confirmação, abre
`solicitacao` tipo `servico` (quarto extraído do texto ou nulo, sem valor),
atualiza o JSON da recebida e envia em sessão. A confirmação é inserida **antes**
da solicitação na mesma transação; o envio é depois. A equipe vê
`GET /solicitacoes` sem ficha cadastral. Fila do dia da recepção **não** muda.
Zero `consumo`. Reprocessar a mesma mensagem não duplica.

Decisões em [research.md](./research.md): tipo novo enfileirado na classificação;
módulo `atendimento` mínimo injetado no processador de `conversa`; sem LLM novo;
`enviar_texto_sessao` reutilizado; unicidade no trabalho e em
`id_mensagem_origem`.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary (já
no projeto). Portas `MensageriaGateway` existente (`enviar_texto_sessao`).
**Nenhuma dependência nova.** Sem Redis, Celery ou provedor de IA na suíte deste
ramo

**Storage**: PostgreSQL 16. Reuso de `mensagem`, `trabalho`, `solicitacao`,
`reserva`. Revisão `0012_registrar_pedido_servico`: CHECK do tipo, dois índices
únicos. **Nenhuma tabela nova e nenhuma coluna nova.** `vw_fila_do_dia` intocada

**Testing**: pytest. Unitários sem rede: extração de quarto, recado padrão,
classificar só enfileira, processador grava confirmação antes de `abrir_servico`,
idempotência, log sem texto, política já permite a operação. Integração com
PostgreSQL real: worker consome o tipo; `GET /solicitacoes` para staff/recepção/
gestão sem ficha; hotel B não vê A; unicidade no banco; dúvida/reclamação não
abrem serviço; zero `consumo`

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em
contêiner. Uma rota HTTP nova. Worker existente. Sem frontend

**Project Type**: Serviço web + worker. Sem React

**Performance Goals**: registro no worker, fora do webhook. Volume do MVP: dezenas
de pedidos por minuto; extração de quarto é função pura sobre o texto

**Constraints**: HTTP do webhook **nunca** abre `solicitacao`; `id_hotel` em toda
leitura via reserva/sessão; pedido e confirmação nunca em log; testes sem
mensageria real; reserva não muda de status; zero `consumo`; staff não lê ficha

**Scale/Scope**: 1 rota HTTP nova, 0 operações novas na matriz, 0 métodos novos nas
portas, 1 tipo de trabalho, 1 ramo no worker, 1 módulo (`atendimento`) no tamanho
mínimo, 1 revisão Alembic. Sem React, sem resolver chamado, sem consumo

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas duas
passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Quarto só do texto da mensagem; não consulta inventário nem lança cobrança |
| II — Na dúvida, humano vê | Não se aplica a “inventar fato”; quarto ausente não descarta — a fila operacional vê a pendência |
| III — Gravar antes de enviar | Confirmação e `solicitacao` persistem antes de `enviar_texto_sessao` |
| IV — Fila como verdade | `GET /solicitacoes`; não depende de notificação |
| V — Ausência humana visível | Pedido aberto permanece na lista até F3.6 resolver |
| VI — Confirmação antes de tramitar | INSERT da enviada antes do INSERT da `solicitacao` na mesma transação |
| VII — Não ser intrusivo | Só responde a quem acabou de pedir; sem mensagem proativa nova |
| VIII — Minimização | Log sem texto; staff/gestão sem ficha; descrição na fila é o pedido (operacional) |
| IX — Garantias no banco | UNIQUE do trabalho por mensagem; UNIQUE de `id_mensagem_origem` |
| X — Portas trocáveis | Mensageria pela porta já existente; suíte com `MensageriaFalsa` |
| XI — Complexidade exige problema | Sem LLM novo, sem método novo na porta, sem React, sem trigger de `consumo` (F3.7) |
| XII — Teste primeiro | Cada FR com teste que falha por ausência; unitário de classificar continua sem envio |
| XIII — Parâmetro não é constante | Sem prazo novo; confirmação é recado fixo |
| XIV — Multi-tenant | `abrir_servico` / `listar_abertas` pelo hotel do trabalho/sessão |
| XV — Honestidade | Sem React, sem quarto mágico, sem cobrança, sem ordem entre mensagens |

**Ponto de atenção 1 — classificar idempotente tem de enfileirar o pedido.** Se o
desfecho já existe e `registrar_pedido_servico` ainda não, o caminho “já
classificada” insere o trabalho. Senão um crash entre eixos e enqueue perde o
gancho (mesmo defeito evitado na F3.3).

**Ponto de atenção 2 — `test_pedido_e_reclamacao_nao_enfileiram_responder`
permanece.** Pedido **não** gera `responder_duvida`. O enqueue novo é outro
callback; reclamação continua sem os dois.

**Ponto de atenção 3 — não ligar `precisa_atendimento_humano`.** Toalha na fila
da recepção treinaria ignorar o flag. A equipe operacional lê `GET /solicitacoes`.

**Ponto de atenção 4 — payload da fila sem ficha.** Teste de staff autenticado
falha se o JSON trouxer nome ou telefone. `id_reserva` é permitido.

**Ponto de atenção 5 — não copiar backoff de LLM.** Este ramo não chama LLM.
Reagendar só a mensageria, depois de gravar.

**Ponto de atenção 6 — módulo `atendimento` é o previsto, não uma peça extra.**
Arquitetura já o nomeia como dono de `solicitacao`. Nasce mínimo (abrir + listar).
Worker injeta; sem ciclo `conversa` ↔ `atendimento`.

## Project Structure

### Documentation (this feature)

```text
specs/013-registrar-pedido-servico/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── fila-e-worker.md
│   ├── mensageria-sessao.md
│   ├── api-de-atendimento.md
│   ├── politica-de-autorizacao.md
│   └── quarto-e-descricao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
alembic/versions/
├── 0012_registrar_pedido_servico.py
└── sql/
    └── 0012_registrar_pedido_servico.sql

app/
├── main.py                    # include roteador atendimento
├── portas/                    # intocado
├── adaptadores/               # intocado (enviar_texto_sessao já existe)
└── modulos/
    ├── conversa/
    │   ├── service.py         # enfileira ao classificar; processar_trabalho_registrar_pedido
    │   ├── repository.py      # UPDATE JSON da recebida; INSERT enviada
    │   └── texto_confirmacao_pedido.py
    └── atendimento/           # NOVO
        ├── service.py         # abrir_servico, listar_abertas
        ├── repository.py
        ├── schema.py
        ├── router.py          # GET /solicitacoes
        └── quarto.py          # extrair_numero_quarto
app/fila/
├── repository.py              # tipo, unique, allowlist
└── service.py                 # enfileirar_registrar_pedido_servico

worker/
└── consumidor.py              # ramo registrar_pedido_servico; injeta abrir_servico

testes/
├── unitarios/
│   ├── fila/                  # claim passa a consumir registrar_pedido_servico
│   ├── modulos/conversa/
│   │   ├── test_classificar_mensagem.py  # enqueue pedido; sem envio
│   │   ├── test_registrar_pedido.py
│   │   ├── test_texto_confirmacao_pedido.py
│   │   └── test_log_sem_conteudo.py
│   └── modulos/atendimento/
│       ├── test_quarto.py
│       ├── test_abrir_servico.py
│       └── test_listar_abertas.py
├── integracao/
│   ├── test_registrar_pedido.py
│   ├── test_solicitacoes.py             # GET staff/recepção/gestão/isolamento
│   └── test_garantias_do_banco.py       # unicidade origem + tipo trabalho
└── ...

docs/
├── 04-schema.sql
├── 04-modelagem-de-dados.md
└── 00-ESTADO-DO-PROJETO.md          # na implementação: F3.4
```

**Structure Decision**: monolito modular existente. Confirmação e envio em
`conversa`; `solicitacao` em `atendimento`; fila só abre o claim. Sem React, sem
porta nova, sem LLM neste ramo.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Chamado de reclamação / janela de preferência | Reclamação só tem eixos | F3.5 |
| Marcar resolvido + aviso de conclusão | Pedido fica `aberta` | F3.6 |
| Consumo, valor, fila de lançamento | Pedido nunca gera cobrança aqui | F3.7 |
| Quarto na reserva / inventário | Sem palavra-chave, quarto nulo | Fora (Artigo I) |
| Extração de quarto por IA (“estou no 402”) | User Story 4 | Fora (Artigo XI / XV) |
| `GET` HTTP do histórico | Teste lê `mensagem` no banco | Fatia de UI |
| Tela React / Alert Center visual | Estado via `GET /solicitacoes` | Fatia de UI |
| Notificação push ao staff | Fila é a verdade | Fora (Artigo IV) |
| Ordem estrita entre mensagens | Cada trabalho é independente | Fora (Artigo XV) |

## Complexity Tracking

> Sem violações a justificar. Tabela omitida.
