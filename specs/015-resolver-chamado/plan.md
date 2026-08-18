# Implementation Plan: Resolver Chamado e Confirmar

**Branch**: `015-resolver-chamado` | **Date**: 2026-08-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/015-resolver-chamado/spec.md`

## Summary

A equipe (recepção ou staff) marca a pendência aberta como resolvida num
clique: `POST /solicitacoes/{id}/resolucao`. Na mesma transação o sistema
grava quem resolveu e quando, insere o recado padrão de conclusão e enfileira
`enviar_confirmacao_resolucao`. O worker só envia. Falha de envio **não**
reabre o chamado. O segundo clique é `409`. Gestão recebe `403`; hotel B,
`404`. Pedido de serviço e reclamação fecham; consumo não. `GET /solicitacoes`
já é a passagem de turno — o item resolvido some da lista.

Decisões em [research.md](./research.md): padrão da chegada (F2.2), não o da
abertura (F3.4/F3.5); `resolver` em `atendimento` e `agendar` em `conversa`;
trigger de transição + CHECK de autor; `enviar_texto_sessao` sem template
Utility (limitação honesta se a janela de 24h já fechou).

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary (já
no projeto). Porta `MensageriaGateway` existente (`enviar_texto_sessao`) e
relógio existente. **Nenhuma dependência nova.** Sem Redis, Celery, LLM ou
método novo na porta

**Storage**: PostgreSQL 16. Reuso de `solicitacao`, `mensagem`, `trabalho`,
`reserva`, `usuario`. Revisão `0014_resolver_chamado`: CHECK do tipo de
trabalho, índice único, trigger de transição, CHECK de autor. **Nenhuma tabela
nova e nenhuma coluna nova.** `vw_fila_do_dia` intocada

**Testing**: pytest. Unitários sem rede: `resolver` grava autor/instante e só
então agenda; segundo resolve recusa sem agendar; gestão nem chega no serviço
se o teste for de rota (`403`); recado por tipo sem “extrato”; processador não
reabre nem duplica enviada; log sem texto. Integração com PostgreSQL real:
POST staff/recepção `200` e item some do GET; `409` no segundo clique; hotel B
`404`; trigger rejeita reabrir; unique do trabalho; falha de envio preserva
`resolvida`; serviço também fecha; zero `consumo`

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em
contêiner. Uma rota HTTP nova. Worker existente. Sem frontend

**Project Type**: Serviço web + worker. Sem React

**Performance Goals**: o clique é um UPDATE + INSERT; o envio é fora do HTTP.
Volume do MVP: dezenas de resoluções por minuto

**Constraints**: HTTP **nunca** chama a porta de mensageria; `id_hotel` em todo
UPDATE/SELECT via join com `reserva`; descrição e recado nunca em log; testes
sem mensageria real; reserva não muda de status; staff não lê ficha; gestão
não resolve; envio falho não reabre

**Scale/Scope**: 1 rota HTTP nova, 0 operações novas na matriz, 0 métodos novos
nas portas, 1 tipo de trabalho, 1 ramo no worker, 1 revisão Alembic. Sem React,
sem atribuir, sem cancelar, sem consumo, sem pulso, sem `GET` por id

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas duas
passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Não consulta inventário nem status de quarto no PMS; reserva intocada |
| II — Na dúvida, humano vê | Não se aplica a classificação; o clique humano **é** o fechamento |
| III — Gravar antes de enviar | Resolução + enviada persistem no POST; `enviar_texto_sessao` só no worker |
| IV — Fila como verdade | `GET /solicitacoes`; notificação de staff não existe e não é necessária |
| V — Ausência humana visível | Sem clique, o item permanece na passagem de turno (com destaque da F3.5) |
| VI — Confirmação antes de tramitar | Vale na **abertura**. Aqui o fato já ocorreu; gravar resolução antes do recado evita avisar fechamento inexistente |
| VII — Não ser intrusivo | Um recado de conclusão, não campanha; sem pergunta de horário de novo |
| VIII — Minimização | Log sem texto; resposta HTTP sem ficha; staff resolve sem cadastro |
| IX — Garantias no banco | Unique do trabalho; trigger de transição; CHECK de autor + instante |
| X — Portas trocáveis | Mensageria pela porta já existente; suíte com `MensageriaFalsa` |
| XI — Complexidade exige problema | Sem GET por id, sem atribuir, sem template Utility, sem React, sem coluna nova |
| XII — Teste primeiro | Cada FR com teste que falha por ausência |
| XIII — Parâmetro não é constante | Nenhum prazo novo; destaque permanece o da F3.5 |
| XIV — Multi-tenant | UPDATE/SELECT pelo hotel da sessão; B não vê A |
| XV — Honestidade | Sem React; janela de sessão fechada = envio falha e retenta, chamado permanece resolvido; produto não infere conserto |

**Ponto de atenção 1 — ordem inversa da F3.4/F3.5.** Abrir chamado confirma
antes de tramitar. Resolver tramita (grava) antes de confirmar. Teste de ordem
do processador da abertura **não** se copia; o teste desta fatia é: no
instante em que a enviada existe, `status` já é `resolvida`.

**Ponto de atenção 2 — allowlist e ramo no mesmo passo.** Incluir
`enviar_confirmacao_resolucao` em `TIPOS_CONSUMIVEIS` sem o `elif` no
consumidor marca `tipo_desconhecido` e queima o gancho (precedente F3.2–F3.5).

**Ponto de atenção 3 — `GET /solicitacoes` não ganha campo.** A asserção nova
é ausência do item. Não se lista resolvidas na passagem de turno.

**Ponto de atenção 4 — `atendimento` não envia.** Docstring atual (“sem
mensageria”) permanece: o serviço chama `agendar_confirmacao` injetado, que
grava mensagem + trabalho. A porta só é tocada no worker.

**Ponto de atenção 5 — savepoint no agendar.** Unique do trabalho não pode
desfazer o `UPDATE` já feito na mesma transação. Espelho de
`agendar_boas_vindas`. O segundo clique do usuário **não** chega aqui: o
`UPDATE` condicional devolve zero linhas e vira `409`.

**Ponto de atenção 6 — janela de 24h.** Recado de resolução pode sair horas
depois da última mensagem do hóspede. Sem template Utility nesta fatia. Falha
de envio = FR-013, não reabertura. Registrar em
[docs/00-ESTADO-DO-PROJETO.md](../../docs/00-ESTADO-DO-PROJETO.md) na
implementação.

## Project Structure

### Documentation (this feature)

```text
specs/015-resolver-chamado/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-de-atendimento.md
│   ├── fila-e-worker.md
│   ├── mensageria-sessao.md
│   └── politica-de-autorizacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
alembic/versions/
├── 0014_resolver_chamado.py
└── sql/
    └── 0014_resolver_chamado.sql

app/
├── main.py                    # intocado (roteador atendimento já incluso)
├── portas/                    # intocado
├── adaptadores/               # intocado
└── modulos/
    ├── conversa/
    │   ├── service.py         # agendar_confirmacao_resolucao; processar envio
    │   ├── repository.py      # INSERT enviada com JSON confirmacao_resolucao
    │   └── texto_confirmacao_resolucao.py
    └── atendimento/
        ├── service.py         # resolver
        ├── repository.py      # UPDATE condicional; SELECT para recusa
        ├── schema.py          # ResolucaoResposta
        └── router.py          # POST /solicitacoes/{id}/resolucao
app/fila/
├── repository.py              # tipo, unique, allowlist
└── service.py                 # enfileirar_enviar_confirmacao_resolucao

worker/
└── consumidor.py              # ramo enviar_confirmacao_resolucao

testes/
├── unitarios/
│   ├── fila/
│   ├── modulos/conversa/
│   │   ├── test_confirmacao_resolucao.py
│   │   ├── test_texto_confirmacao_resolucao.py
│   │   └── test_log_sem_conteudo.py          # eventos novos
│   └── modulos/atendimento/
│       ├── test_resolver.py
│       └── test_listar_abertas.py            # item resolvido some
├── integracao/
│   ├── test_resolver_chamado.py
│   ├── test_solicitacoes.py                  # GET após POST
│   └── test_garantias_do_banco.py            # trigger + unique + CHECK autor
└── ...

docs/
├── 04-schema.sql
├── 04-modelagem-de-dados.md
└── 00-ESTADO-DO-PROJETO.md          # na implementação: F3.6
```

**Structure Decision**: monolito modular existente. Status em `atendimento`;
mensagem e envio em `conversa`; fila só abre o claim. Sem React, sem porta
nova, sem LLM.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Atribuir / `em_andamento` como clique | Quem clicou é o responsável | Fora (Artigo XI / backlog) |
| Cancelar solicitação | Status `cancelada` inacessível por API | Fora |
| `GET /solicitacoes/{id}` | Fato histórico no `200` do POST e no banco | Fatia de UI |
| Tela React / passagem de turno agregada | Estado via GET já existente + POST | Fatia de UI |
| Template Utility de resolução | Se a janela de 24h fechou, envio falha e retenta | Se a demo provar a necessidade |
| Consumo, valor, fila de lançamento | Tipo `consumo` recusado com `409` | F3.7 |
| Pulso / supressão | Resolver tira o insumo; pulso não lê ainda | F3.8 |
| Reabrir chamado | Trigger rejeita | Fora |
| Inferir que o quarto foi atendido | Sem clique, permanece aberto | Fora (Artigo V) |
| Notificação push ao staff | Fila é a verdade | Fora (Artigo IV) |

## Complexity Tracking

> Sem violações a justificar. Tabela omitida.
