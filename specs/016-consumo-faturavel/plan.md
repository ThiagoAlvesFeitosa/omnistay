# Implementation Plan: Consumo Faturável e Fila de Lançamento

**Branch**: `016-consumo-faturavel` | **Date**: 2026-08-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/016-consumo-faturavel/spec.md`

## Summary

O processador já existente de `registrar_pedido_servico` passa a identificar o
pedido contra os **itens vendáveis ativos** da propriedade **antes** de abrir
solicitação. Correspondência única: confirmação com o valor lido do banco,
`solicitacao` tipo `consumo` + linha filha `pendente`. Nenhuma correspondência:
caminho da F3.4 (serviço sem cobrança). Ambígua ou IA caída: aviso sem preço e
`precisa_atendimento_humano`. A recepção lança ou dispensa; staff entrega e
resolve o quarto sem isso significar lançamento. Fila destacada:
`GET /consumos/pendentes`.

Decisões em [research.md](./research.md): sem tipo novo de trabalho; método novo
na porta de LLM que **não** emite preço; tabela `item_vendavel` (não coluna em
`catalogo_item`); trigger de especialização e de transição de lançamento;
`lancar_consumo` ligada nesta fatia.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary (já
no projeto). Portas `MensageriaGateway` (`enviar_texto_sessao`) e `LLMProvider`
(método novo `identificar_item_vendavel`). **Nenhuma biblioteca nova.** Sem Redis,
Celery ou provedor real na suíte

**Storage**: PostgreSQL 16. Reuso de `solicitacao`, `consumo` (tabela já na
`0001`, ainda sem escritor), `mensagem`, `trabalho`, `reserva`. Nova tabela
`item_vendavel`. Revisão `0015_consumo_faturavel`: tabela, CHECKs, triggers,
visão da fila do dia. **Nenhum tipo novo em `trabalho`.** `vw_fila_do_dia` só
ganha desfechos humanos novos

**Testing**: pytest. Unitários sem rede: identificação (único / nenhum /
ambíguo / indisponível), recado com valor e sem “extrato”, `abrir_consumo`
grava pendente, lançar/dispensar com autor, resolver consumo não lança, item
vendável CRUD, log sem texto. Integração com PostgreSQL real: worker no
caminho cobrado e no da toalha; `GET /consumos/pendentes`; POST lançamento
só recepção; reajuste não reescreve histórico; trigger rejeita especialização
e transição inválidas; hotel B isolado

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em
contêiner. Rotas HTTP novas no módulo `atendimento` e em `propriedade`. Worker
existente. Sem frontend

**Project Type**: Serviço web + worker. Sem React

**Performance Goals**: identificação e registro no worker, fora do webhook.
Lançamento é um UPDATE. Volume do MVP: dezenas de pedidos cobrados por minuto

**Constraints**: HTTP do webhook **nunca** identifica nem abre `consumo`; preço
**nunca** sai do modelo; `id_hotel` em toda leitura; pedido, confirmação e
descrição nunca em log; testes sem mensageria real nem LLM real; reserva não
muda de status; staff não lê ficha nem lança; gestão não lança nem edita item
vendável; lançamento não dispara recado novo

**Scale/Scope**: 1 tabela nova, 0 tipos novos de trabalho, 1 método novo na
porta de LLM, 1 operação da matriz ligada (`lancar_consumo`), rotas de item
vendável + fila de pendências + lançar/dispensar, 1 revisão Alembic. Sem
React, sem lista no checkout (F4.2), sem débito no PMS

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas duas
passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Lançar é clique; o sistema não verifica nem debita o PMS. Quarto só do texto |
| II — Na dúvida, humano vê | Ambíguo / IA caída / formato inválido → aviso sem preço + flag na fila do dia. Modelo não escreve valor |
| III — Gravar antes de enviar | Confirmação + `solicitacao` + `consumo` persistem antes de `enviar_texto_sessao` |
| IV — Fila como verdade | `GET /consumos/pendentes` e `GET /solicitacoes`; não depende de notificação |
| V — Ausência humana visível | Pendente permanece na fila destacada até lançar ou dispensar |
| VI — Confirmação antes de tramitar | INSERT da enviada **antes** do INSERT de `solicitacao`/`consumo` na mesma transação |
| VII — Não ser intrusivo | Só responde a quem acabou de pedir; lançar/dispensar não mandam recado novo |
| VIII — Minimização | Log sem texto; staff/gestão sem ficha; valor na fila é operacional |
| IX — Garantias no banco | Trigger de especialização; trigger de transição de lançamento; CHECK de autor no terminal; UNIQUE de origem já existe |
| X — Portas trocáveis | Identificação pela porta; suíte com `LLMFalso` e `MensageriaFalsa` |
| XI — Complexidade exige problema | Sem tipo novo de trabalho, sem Redis, sem React, sem intenção nova no classificador |
| XII — Teste primeiro | Cada FR com teste que falha por ausência |
| XIII — Parâmetro não é constante | Sem prazo novo; preço é dado do item vendável, não constante de código |
| XIV — Multi-tenant | Item, consumo e filas pelo hotel da sessão/trabalho |
| XV — Honestidade | Sem React; lançar não prova que o PMS recebeu; um item por mensagem; quantidade honesta (ver research) |

**Ponto de atenção 1 — o processador da F3.4 passa a chamar LLM.** Os testes
que prometiam “este ramo não chama a porta” **invertem**, no mesmo espírito da
F3.2 ao passar a consumir `classificar_mensagem`. Lista vazia de itens
vendáveis **não** chama a porta (espelho da F3.3 com catálogo vazio).

**Ponto de atenção 2 — toalha continua sem `consumo`.** `nenhum` item →
`abrir_servico` inalterado. Os testes da F3.4 de pedido sem cobrança
permanecem; o que muda é o caso com item vendável ativo correspondente.

**Ponto de atenção 3 — não ligar o flag humano no caminho cobrado nem na
toalha.** Só ambíguo / indisponível / formato inválido. Consumo pendente de
lançamento vive em `GET /consumos/pendentes`, não na fila do dia da recepção.

**Ponto de atenção 4 — `tipo = consumo` deixa de ser `409` no resolver.** Os
testes da F3.6 que recusavam consumo **invertem**: resolvem o quarto e o
lançamento permanece `pendente`. O recado de conclusão **não** afirma
lançamento nem usa “extrato”/“conta”.

**Ponto de atenção 5 — não copiar backoff de `interpretar_ficha`.** Falha de
identificação conclui o trabalho e encaminha a humano (padrão F3.2/F3.3).
Reagendar só a mensageria, depois de gravar.

**Ponto de atenção 6 — preço fora do prompt.** A porta recebe `id` + `nome`.
O valor é lido de `item_vendavel.preco_atual` **depois**, na mesma transação
da confirmação e do `INSERT` em `consumo`.

**Ponto de atenção 7 — `atendimento` não envia e `propriedade` não abre
consumo.** Worker/conversa orquestra: lê itens, identifica, lê preço, grava
enviada, chama `abrir_consumo`. Sem ciclo de import.

## Project Structure

### Documentation (this feature)

```text
specs/016-consumo-faturavel/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── fila-e-worker.md
│   ├── mensageria-sessao.md
│   ├── api-de-atendimento.md
│   ├── api-de-item-vendavel.md
│   ├── identificacao-e-preco.md
│   └── politica-de-autorizacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
alembic/versions/
├── 0015_consumo_faturavel.py
└── sql/
    └── 0015_consumo_faturavel.sql

app/
├── portas/llm.py              # identificar_item_vendavel + FalhaDeIdentificacao
├── adaptadores/               # LLMFalso devolve identificação configurável
└── modulos/
    ├── conversa/
    │   ├── service.py         # fork no processador registrar_pedido
    │   ├── repository.py      # JSON confirmacao_consumo / aviso_identificacao
    │   └── texto_confirmacao_consumo.py
    ├── atendimento/
    │   ├── service.py         # abrir_consumo; lancar; dispensar; resolver consumo
    │   ├── repository.py
    │   ├── schema.py          # valor + status_lancamento; filas novas
    │   └── router.py          # GET pendentes; POST lancamento; POST dispensa
    ├── propriedade/
    │   ├── service.py         # CRUD item vendável; listar ativos
    │   ├── repository.py
    │   ├── schema.py
    │   └── router.py          # /itens-vendaveis
    └── acesso/politica.py     # intocada (lancar_consumo / catalogo já existem)
app/fila/                      # intocada (mesmo tipo registrar_pedido_servico)

worker/
└── consumidor.py              # injeta identificar + abrir_consumo + listar itens

testes/
├── unitarios/
│   ├── portas/ / adaptadores/ # identificação no falso
│   ├── modulos/conversa/
│   │   ├── test_registrar_pedido.py     # fork nenhum → serviço
│   │   ├── test_registrar_consumo.py
│   │   ├── test_texto_confirmacao_consumo.py
│   │   └── test_log_sem_conteudo.py
│   ├── modulos/atendimento/
│   │   ├── test_abrir_consumo.py
│   │   ├── test_lancar.py
│   │   ├── test_dispensar.py
│   │   ├── test_resolver.py             # consumo resolve sem lançar
│   │   └── test_listar_pendentes.py
│   └── modulos/propriedade/
│       └── test_item_vendavel.py
├── integracao/
│   ├── test_registrar_consumo.py
│   ├── test_registrar_pedido.py         # toalha continua sem consumo
│   ├── test_consumos_pendentes.py
│   ├── test_resolver_chamado.py         # consumo deixa de ser 409
│   └── test_garantias_do_banco.py       # especialização + transição + CHECK
└── ...

docs/
├── 04-schema.sql
├── 04-modelagem-de-dados.md
└── 00-ESTADO-DO-PROJETO.md          # na implementação: F3.7
```

**Structure Decision**: monolito modular existente. Itens vendáveis em
`propriedade`; `consumo` em `atendimento`; confirmação e identificação em
`conversa`; fila só reusa o claim da F3.4. Sem React, sem tipo novo de
trabalho, sem débito no PMS.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Lista “pedidos feitos pelo chat” ao hóspede | Consumo existe; a lista não é apresentada | F4.2 |
| Intenção nova no classificador | Continua `pedido_de_servico`; a identificação distingue | Fora (Artigo XI) |
| Vários itens distintos na mesma mensagem | Cai em ambíguo → humano | Fora (Artigo XV) |
| Débito / verificação no PMS | Clique registra a afirmação humana | Fora (Artigo I) |
| Recado ao hóspede no lançar/dispensar | Já recebeu o valor na confirmação de recebimento | Fora (Artigo VII) |
| `GET /solicitacoes/{id}` | Fato no `200` do POST e nas listas | Fatia de UI |
| Tela React / passagem de turno visual | Estado via GET de pendências + GET de abertas | Fatia de UI |
| Notificação push | Fila é a verdade | Fora (Artigo IV) |
| Apagar item vendável | Só desativar | Fora (espelho F2.1) |
| Pulso / checkout / pesquisa | Intocados | F3.8 / F4.1 |

## Complexity Tracking

> Sem violações a justificar. Tabela omitida.
