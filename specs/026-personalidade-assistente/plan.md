# Implementation Plan: Personalidade da assistente e aviso de IA

**Branch**: `026-personalidade-assistente` | **Date**: 2026-08-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/026-personalidade-assistente/spec.md`

## Summary

A propriedade passa a guardar um tom em texto livre. Esse tom entra só
na composição da resposta automática de dúvida coberta, **antes** da
regra do catálogo. Injeção que inventa fato reutiliza o encaminhamento
`nao_fiel` já existente. Gestão lê e grava por operações próprias, sem
tela. O aviso de assistente virtual da F7.1 permanece intocado.

Decisões em [research.md](./research.md): chave
`personalidade_assistente`; `valor` alargado a `VARCHAR(500)`; porta
`responder_duvida(..., tom="")`; prompt Gemini com regra por último;
revisão `0022`. Sem módulo novo, sem React, sem sétima intenção.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Pydantic,
pytest, Alembic. Porta `LLMProvider` ganha parâmetro `tom` **somente**
em `responder_duvida`. **Nenhuma** lib nova

**Storage**: PostgreSQL 16. Nenhuma tabela nova. Revisão `0022`:
`ALTER` de `parametro_hotel.valor` para `VARCHAR(500)`; `INSERT` da
chave vazia por hotel; `COMMENT` atualizado. `docs/04-schema.sql` no
mesmo commit. `0001`…`0021` intactos

**Testing**: pytest. Unitários: validação do tom (vazio, 500, 501,
quebra de linha, nulo), política (gestão grava, recepção lê, staff
recusado), fábrica/Gemini com MockTransport (tom no prompt **antes** da
regra final; classificar **sem** tom), `LLMFalso` registra `tom`,
domínio passa a chave e recusa redação inventada pelo ramo `nao_fiel`,
aviso de boas-vindas inalterado, log sem tom e sem conteúdo. Integração:
GET/PUT `/propriedade/personalidade` com cookie de gestão; 403
recepção/staff na gravação; bootstrap semeia chave vazia; conformidade
do esquema. **Nenhum** teste chama rede

**Target Platform**: Servidor Linux; desenvolvimento Windows +
PostgreSQL em contêiner. API HTTP desta fatia: duas rotas novas no
roteador de `propriedade`. Worker existente (ramo `responder_duvida`)

**Project Type**: Serviço web + worker. Sem tela nova

**Performance Goals**: uma leitura da chave por trabalho de dúvida
coberta; zero chamada extra à porta quando a redação não é fiel.
Volume inalterado em relação à F3.3

**Constraints**: teto 500; tom só em `responder_duvida`; fidelidade
depois da porta; sem operação genérica de parâmetro; log sem tom, sem
texto de hóspede, sem redação; testes sem rede; aviso F7.1 intocado;
sem PMS

**Scale/Scope**: 1 chave, 1 `ALTER` de coluna, 2 operações na matriz, 2
rotas, 1 parâmetro na porta, 1 revisão Alembic. 0 tabelas, 0 tipos de
trabalho, 0 telas

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Tom e aviso não inferem chegada/saída nem lançamento |
| II — Na dúvida, humano vê | Redação não fiel (injeção) reusa `nao_fiel`; fora de escopo intocado |
| III — Gravar antes de enviar | Intocado. A composição continua no worker, depois da mensagem recebida |
| IV — Fila como verdade | Sem tipo novo; pendência humana continua na fila do dia |
| V — Ausência humana visível | Injeção e pedido de pessoa continuam visíveis à recepção |
| VI — Confirmação antes de tramitar | Intacta. O tom não abre chamado |
| VII — Não ser intrusivo | Sem mensagem proativa nova; aviso permanece dentro do recado de chegada |
| VIII — Minimização | Log sem texto, sem tom, sem redação. Foto continua recusada |
| IX — Garantias no banco | `VARCHAR(500)` + `UNIQUE (id_hotel, chave)`. Sem tabela paralela |
| X — Portas trocáveis | Domínio passa `tom`; adaptadores não leem `parametro_hotel` |
| XI — Complexidade exige problema | Sem SDK, sem fila, sem módulo, sem “limpar e enviar” |
| XII — Teste primeiro | Cada FR com teste que falha por ausência; zero chamada ao serviço real |
| XIII — Parâmetro não é constante | Tom em `parametro_hotel`, não literal no código |
| XIV — Multi-tenant | `id_hotel` da sessão na gravação; da reserva na composição |
| XV — Honestidade | Contraste literário entre casas não é garantia; fidelidade sim. Aviso no WhatsApp real continua a exigir republicar o template Meta |

**Ponto de atenção 1 — unitários de `responder_duvida`.** Hoje a
função recebe `object()` como conexão e não lê parâmetro. Passar a ler
sem injetar o repositório de propriedade quebra a suíte. A injeção é o
mesmo padrão da coleta, não um mecanismo novo.

**Ponto de atenção 2 — `chamadas_responder`.** A tupla ganha o tom.
Asserções que só testam lista vazia ou `len` seguem válidas; as que
desempacotarem dois itens precisam do terceiro.

**Ponto de atenção 3 — conformidade do esquema.** Alargar `valor` e
acrescentar a chave no `COMMENT` **e** em `04-schema.sql` no mesmo
commit da revisão. Documento e banco divergentes falham o teste de
inventário — de propósito.

**Ponto de atenção 4 — aviso.** Não reeditar `texto_boas_vindas.py`
salvo regressão. O PUT de tom **não** altera o recado de chegada.

## Project Structure

### Documentation (this feature)

```text
specs/026-personalidade-assistente/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-de-personalidade.md
│   ├── politica-de-autorizacao.md
│   ├── tom-na-composicao.md
│   └── logs.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
docs/04-schema.sql                           # valor VARCHAR(500); COMMENT
alembic/versions/0022_personalidade_assistente.py
alembic/versions/sql/0022_personalidade_assistente.sql

app/
├── portas/llm.py                            # responder_duvida(..., tom="")
├── adaptadores/
│   ├── llm_falso.py                         # registra tom
│   └── llm_gemini.py                        # tom no prompt; regra por último
├── modulos/
│   ├── acesso/politica.py                   # duas operações novas
│   ├── propriedade/
│   │   ├── schema.py                        # entrada/resposta {texto}
│   │   ├── service.py                       # validar + ler/gravar chave
│   │   └── router.py                        # GET/PUT /propriedade/personalidade
│   └── conversa/service.py                  # lê chave; passa tom; nao_fiel intacto

testes/
├── unitarios/
│   ├── modulos/acesso/test_politica.py
│   ├── modulos/propriedade/test_personalidade.py
│   ├── modulos/propriedade/test_bootstrap.py
│   ├── modulos/conversa/test_responder_duvida.py
│   ├── modulos/conversa/test_texto_boas_vindas.py  # regressão do aviso
│   └── adaptadores/test_llm_gemini.py
└── integracao/
    └── test_personalidade_assistente.py
```

**Structure Decision**: monólito existente. Sem módulo novo. Sem
frontend. Revisão `0022` é a primeira desta fatia (F7.1 não migrou).

## Complexity Tracking

> Sem violações a justificar. Tabela omitida.
