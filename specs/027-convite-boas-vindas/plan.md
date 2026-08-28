# Implementation Plan: Linha de convite no recado de boas-vindas

**Branch**: `027-convite-boas-vindas` | **Date**: 2026-08-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/027-convite-boas-vindas/spec.md`

## Summary

O recado de chegada ganha um quarto texto, `boas_vindas_convite`, no
mesmo molde de café, wi-fi e checkout. A recepção grava pela rota já
existente; a frase fixa do produto sai; o aviso de assistente virtual
permanece antes da última linha, que passa a ser o convite da casa.
Ausência bloqueia o envio e acende a fila. Propriedade nova e já
instalada nascem com semente. A porta de mensageria leva cinco
variáveis, para o canal real também entregar a linha da casa.

Decisões em [research.md](./research.md): chave e semente; GET/PUT com
`convite`; tupla de cinco; template Meta republicado; revisão `0023`.
Sem módulo novo, sem React, sem operação nova na matriz.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Pydantic,
pytest, Alembic, httpx (MockTransport no unitário do WhatsApp).
**Nenhuma** lib nova. Porta `MensageriaGateway.enviar_boas_vindas`
muda a tupla de 4 para 5 valores

**Storage**: PostgreSQL 16. Nenhuma tabela nova. Revisão `0023`:
`INSERT` de `boas_vindas_convite` por hotel; `COMMENT` atualizado.
`docs/04-schema.sql` no mesmo commit. `0001`…`0022` intactos. Sem
`ALTER` de coluna

**Testing**: pytest. Unitários: validação do convite (vazio, `\n`,
tab, 5 espaços, 256 caracteres, `strip`); GET/PUT com quatro campos;
política inalterada (recepção grava, gestão lê, staff recusado);
montagem (última linha = convite, aviso antes, frase antiga ausente,
sem `?` obrigatório); agendar bloqueado por convite ausente;
`len(variaveis) == 5`; WhatsApp com MockTransport (cinco parâmetros,
zero rede); log sem valor. Integração: bootstrap semeia a chave;
conformidade do esquema; chegada com quatro válidos grava recado com
a linha da casa; slot convite apagado → fila; recuperação na janela.
**Nenhum** teste chama Graph nem PMS

**Target Platform**: Servidor Linux; desenvolvimento Windows +
PostgreSQL em contêiner. API: as duas rotas de `/propriedade/boas-vindas`
já existentes. Worker e agendador existentes (leem a lista de chaves
ampliada)

**Project Type**: Serviço web + worker. Sem tela nova

**Performance Goals**: uma leitura a mais na mesma consulta de
parâmetros (quarta chave na lista). Volume de envio inalterado

**Constraints**: teto 255 no convite (igual aos três); PUT atômico dos
quatro; aviso não editável; log sem valor de slot; testes sem rede;
sem PMS; template Meta com cinco variáveis é passo humano — a suíte
prova o payload

**Scale/Scope**: 1 chave, 1 revisão Alembic, 0 operações novas na
matriz, 0 rotas novas, 1 parâmetro na função pura, tupla da porta 4→5.
0 tabelas, 0 tipos de trabalho, 0 telas

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Convite não infere chegada/saída nem lançamento |
| II — Na dúvida, humano vê | Não classifica nem responde dúvida; só o recado de chegada |
| III — Gravar antes de enviar | Intocado. Montagem continua antes do trabalho de envio |
| IV — Fila como verdade | `boas_vindas_nao_enviadas` já existente; convite vazio a acende |
| V — Ausência humana visível | Slot vazio visível na fila; check-in não é desfeito |
| VI — Confirmação antes de tramitar | Fora de escopo (não abre chamado) |
| VII — Não ser intrusivo | Sem mensagem proativa nova; um recado por reserva |
| VIII — Minimização | Log sem convite, sem corpo, sem texto de hóspede |
| IX — Garantias no banco | `UNIQUE (id_hotel, chave)`; unicidade do trabalho intacta; semente na migração |
| X — Portas trocáveis | Tupla cresce na interface; três adaptadores; domínio não importa WhatsApp |
| XI — Complexidade exige problema | Sem SDK, sem rota nova, sem operação nova, sem fila nova |
| XII — Teste primeiro | Cada FR com teste que falha por ausência; zero Graph |
| XIII — Parâmetro não é constante | Convite em `parametro_hotel`; aviso permanece constante de produto |
| XIV — Multi-tenant | `id_hotel` da sessão na gravação; da reserva no envio |
| XV — Honestidade | Canal real só está pronto com o template de cinco variáveis aprovado; até lá o Graph recusa, não entrega a frase antiga. A suíte não finge que a Meta já aprovou |

**Ponto de atenção 1 — fixtures de três slots.** `_semear_boas_vindas`,
bootstrap, `test_agendar_boas_vindas`, `test_log_sem_conteudo`,
`test_ia_real_aviso` (`len == 4`) e o PUT de integração da F2.2 quebram
até ganharem o quarto campo. É o vermelho certo, não regressão a
contornar.

**Ponto de atenção 2 — `?` na última linha.** Dois unitários da F7.1
exigem exatamente uma interrogação. A spec aposenta essa regra. Os
testes mudam de asserção; não se mantém a `?` na semente só para eles
passarem.

**Ponto de atenção 3 — conformidade do esquema.** Incluir
`boas_vindas_convite` no `COMMENT` **e** em `04-schema.sql` no mesmo
commit da 0023.

**Ponto de atenção 4 — template Meta.** Código manda cinco parâmetros
com o nome `boas_vindas`. Aprovar o corpo no painel da Meta é passo
humano, documentado no contrato de montagem. Sem variável de ambiente
nova para o nome do template.

**Ponto de atenção 5 — PUT antigo.** Cliente que ainda manda três campos
toma `422`. Não há período de compatibilidade: o recado sem convite
seria a frase antiga de novo.

## Project Structure

### Documentation (this feature)

```text
specs/027-convite-boas-vindas/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-de-boas-vindas.md
│   ├── politica-de-autorizacao.md
│   ├── montagem-e-porta.md
│   └── logs.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
docs/04-schema.sql                           # COMMENT com boas_vindas_convite
alembic/versions/0023_convite_boas_vindas.py
alembic/versions/sql/0023_convite_boas_vindas.sql

app/
├── portas/mensageria.py                     # tupla de 5
├── adaptadores/
│   ├── mensageria_falsa.py                  # registra convite
│   ├── mensageria_simulada.py               # assinatura
│   └── mensageria_whatsapp.py               # itera a tupla (já faz)
├── modulos/
│   ├── propriedade/
│   │   ├── service.py                       # chave, semente, gravar 4
│   │   ├── schema.py                        # campo convite
│   │   └── router.py                        # passa convite no PUT
│   └── conversa/
│       ├── texto_boas_vindas.py             # parâmetro convite
│       └── service.py                       # 4 chaves; tupla de 5

testes/
├── unitarios/
│   ├── modulos/propriedade/test_slots_boas_vindas.py
│   ├── modulos/propriedade/test_bootstrap.py
│   ├── modulos/conversa/test_texto_boas_vindas.py
│   ├── modulos/conversa/test_agendar_boas_vindas.py
│   ├── modulos/conversa/test_log_sem_conteudo.py
│   └── adaptadores/test_mensageria_whatsapp.py   # novo, MockTransport
└── integracao/
    ├── test_bootstrap.py
    ├── test_confirmar_chegada.py
    ├── test_boas_vindas_envio.py
    └── test_ia_real_aviso.py
```

**Structure Decision**: monólito existente. Sem módulo novo. Sem
frontend. Revisão `0023` (0022 é a personalidade).

## Complexity Tracking

> Sem violações a justificar. Tabela omitida.
