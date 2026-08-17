# Implementation Plan: Confirmar Chegada e Boas-vindas

**Branch**: `009-confirmar-chegada` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-confirmar-chegada/spec.md`

## Summary

A recepção confirma a chegada no painel: a reserva passa para `hospedado`, o instante real
fica em `checkin_em`, e nasce **uma** pendência durável de recado curto de boas-vindas —
confirmação da chegada, três informações de entrada da propriedade (café, wi-fi, checkout) e
convite a perguntar pelo mesmo canal. O envio acontece no worker; falha de envio não desfaz o
check-in. Estado que a máquina de estados não admite é recusado. Slot vazio não bloqueia o
check-in: a mensagem não sai e a fila do dia sinaliza a omissão.

Decisões em [research.md](./research.md): `confirmar_fase_da_reserva` **já existe** na matriz
(nenhuma operação nova para o clique); duas operações novas só para os três slots
(`alterar_texto_de_boas_vindas`, `ler_texto_de_boas_vindas`); `POST /reservas/{id}/chegada`
com `409` para estado não admitido; transição por `UPDATE` guardado (`rowcount` decide) com a
trigger como garantia; slots em `parametro_hotel`, validados na gravação; tipo de trabalho
`enviar_boas_vindas` com índice único parcial por reserva — é essa a unicidade exigida;
recuperação pelo agendador já existente, com a janela de validade contada do `checkin_em` e o
prazo em `parametro_hotel`; coluna derivada `boas_vindas_nao_enviadas` em `vw_fila_do_dia`.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary (já no
projeto). **Nenhuma dependência nova** — nem APScheduler, nem fila externa

**Storage**: PostgreSQL 16. Revisão `0008_confirmar_chegada`: tipo `enviar_boas_vindas` no
`ck_trabalho_tipo`, índice `uq_trabalho_enviar_boas_vindas_reserva`, coluna derivada
`boas_vindas_nao_enviadas` na `vw_fila_do_dia`, semeadura idempotente das quatro chaves.
**Nenhuma tabela e nenhuma coluna nova** — `reserva.checkin_em` já existe

**Testing**: pytest. Unitários sem rede: validação dos slots, montagem do texto, política,
log sem conteúdo, decisão de agendar, elegibilidade da recuperação com relógio controlado
(inclusive a virada de dia). Integração com PostgreSQL real: transições aceitas e recusadas,
segunda tentativa de agendar (índice recusa, aplicação trata como já enviado), `GET`/`PUT`
dos slots, perfis, isolamento entre hotéis, fila do dia, recuperação dentro e fora da janela,
quatro chaves presentes após bootstrap em banco migrado

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em contêiner. API e
worker; sem frontend

**Project Type**: Serviço web + worker existente. Sem React

**Performance Goals**: Confirmação é um `UPDATE` por chave primária mais dois `INSERT`. A
varredura de recuperação percorre reservas `hospedado` sem recado, filtrando a janela em
memória — dezenas por propriedade

**Constraints**: `id_hotel` da sessão em toda consulta; log sem conteúdo de mensagem e sem
valor de slot; nenhum teste chama provedor real; check-in nunca desfeito por falha de envio;
variável de template sem quebra de linha, tabulação, 5+ espaços seguidos nem vazio; janela de
validade medida do instante do check-in, nunca por data de calendário

**Scale/Scope**: 3 rotas HTTP novas, 2 operações novas na matriz, 4 chaves novas de
`parametro_hotel`, 1 método novo na porta de mensageria (+ 2 implementações), 1 tipo de
trabalho, 1 revisão Alembic, 1 varredura no agendador. Sem React, sem checkout, sem
classificação de mensagem

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas duas passagens,
sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | A chegada existe porque a recepção clicou. Nada detectado, nada importado |
| II — Na dúvida, humano vê | Slot ausente e reserva antiga sem boas-vindas terminam em sinalização na fila, nunca em mensagem degradada |
| III — Gravar antes de enviar | Transição, mensagem pendente e trabalho na mesma transação; envio depois, no worker |
| IV — Fila como verdade | O trabalho `enviar_boas_vindas` é o registro; a fila do dia mostra a omissão |
| V — Ausência humana visível | `chegada_nao_confirmada` (clique esquecido) e `boas_vindas_nao_enviadas` (slot vazio), distintas |
| VI — Confirmação antes de tramitar | O recado **é** a confirmação ao hóspede; nada tramita antes dele |
| VII — Não ser intrusivo | Um recado por reserva, garantido por índice único; recuperação limitada à janela de validade do check-in |
| VIII — Minimização | Corpo com o primeiro nome e nada mais do hóspede; log com identificadores |
| IX — Garantias no banco | Unicidade por índice parcial; transição pela trigger; `CHECK` de status |
| X — Portas trocáveis | `enviar_boas_vindas` na porta; falso nos testes; provedor real nunca chamado |
| XI — Complexidade exige problema | Sem tabela nova, sem lib nova, sem agendador novo; relógio injetável só onde há prazo a vencer |
| XII — Teste primeiro | Cada FR com teste que falha por ausência antes da implementação |
| XIII — Parâmetro não é constante | Os três textos **e** a janela de validade vêm de `parametro_hotel`; nada de literal no código |
| XIV — Multi-tenant | `id_hotel` no `UPDATE`, na leitura dos slots e na fila |
| XV — Honestidade | Sem React, sem checkout, sem envio manual para reserva antiga — seção própria |

**Ponto de atenção 1 — FR-033 e o agendador.** A spec proíbe "mecanismo de fila, agendador ou
canal novo". A recuperação entra como **uma função na varredura que já existe**
(`worker/agendador.py`, criado na F1.4), acionada pela flag do `python -m worker`. Nenhum
processo, nenhuma biblioteca de agendamento, nenhum tipo de execução novo.

**Ponto de atenção 2 — a operação de autorização já existia.** `confirmar_fase_da_reserva`
está na matriz desde a F0.3 sem consumidor. Esta fatia é a primeira a usá-la. As duas
operações novas cobrem **apenas** os três slots, como a clarificação exigiu; nenhuma permissão
genérica sobre `parametro_hotel` nasce aqui (SC-014a).

**Ponto de atenção 3 — `aguardando_cadastro` recusa a chegada.** A trigger só admite
`hospedado` a partir de `ficha_recebida`, `ficha_parcial` ou `sem_cadastro_previo`. Se o
hóspede aparecer no balcão antes de a varredura de silêncio marcar `sem_cadastro_previo`, a
confirmação é recusada com `409`. Isso é o que a spec pede (FR-004, cenário 3 da história 3) e
o que a máquina de estados garante — **não** é atalho a criar aqui. Se na operação real isso
incomodar, o lugar de resolver é uma fatia de "marcar chegada sem cadastro no balcão", com
spec própria.

**Ponto de atenção 4 — histórico e variáveis lidos em momentos diferentes.** O texto vai para
`mensagem.conteudo` na confirmação; as variáveis do template são lidas no envio. Editar um
slot nesse intervalo faz o histórico guardar o valor antigo. Risco aceito e justificado em
[research.md](./research.md) §14 — a alternativa duplicaria o texto na fila.

**Ponto de atenção 5 — não há rota de envio manual.** FR-032 mantém a decisão sobre reserva
fora da janela com a recepção, "fora do automático desta fatia". A fatia entrega a
**sinalização**, não o botão. Registrado na seção de ausências para não parecer esquecimento.

**Ponto de atenção 6 — o eixo da janela foi corrigido depois da clarificação.** A resposta
original definia a elegibilidade por `data_checkin_prevista = CURRENT_DATE`. Isso abria uma
falha silenciosa: chegada às 23h30 com slot vazio, slots preenchidos às 23h40, varredura às
00h05 — a reserva saía da elegibilidade pela virada do dia civil e o pacote nunca saía, sem erro
nenhum. A janela passou a contar do `checkin_em`, com duração em `parametro_hotel`
(`horas_validade_boas_vindas`, padrão `12`). A intenção da decisão original permanece; mudou o
que se mede. Correção registrada na spec, em [research.md](./research.md) §11 e em
`docs/00-ESTADO-DO-PROJETO.md`.

**Ponto de atenção 7 — chegada antecipada é elegível mas invisível.** Com o eixo no
`checkin_em`, a reserva confirmada antes da data prevista passa a receber a recuperação (o
critério antigo a excluía — segundo furo que a correção fecha). Porém a `vw_fila_do_dia` só
mostra `data_checkin_prevista <= CURRENT_DATE`, então, se o slot estiver vazio nesse caso, a
sinalização só aparece quando a data prevista chega. Alargar a cláusula da visão mexeria na fila
do turno inteira e não é escopo desta fatia.

## Project Structure

### Documentation (this feature)

```text
specs/009-confirmar-chegada/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-de-chegada.md
│   ├── boas-vindas-fila-e-porta.md
│   ├── politica-de-autorizacao.md
│   └── agendador-de-recuperacao.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
alembic/versions/
├── 0008_confirmar_chegada.py                # revisão: aplica o SQL, downgrade explícito
└── sql/
    └── 0008_confirmar_chegada.sql           # cópia congelada do delta

app/
├── portas/
│   └── mensageria.py                        # + enviar_boas_vindas (4 variáveis)
├── adaptadores/
│   ├── mensageria_falsa.py                  # + enviar_boas_vindas
│   └── mensageria_whatsapp.py               # + template boas_vindas
├── fila/
│   ├── repository.py                        # + enfileirar_enviar_boas_vindas
│   └── service.py                           # + enfileirar_enviar_boas_vindas
├── bootstrap.py                             # (sem mudança; a semeadura é no service)
└── modulos/
    ├── acesso/
    │   └── politica.py                      # + alterar/ler_texto_de_boas_vindas
    ├── propriedade/
    │   ├── repository.py                    # + upsert_parametro, ler_parametros
    │   ├── service.py                        # + slots: ler, gravar, validar, semear
    │   ├── schema.py                        # + BoasVindasEntrada/Resposta
    │   └── router.py                        # + GET/PUT /propriedade/boas-vindas
    ├── conversa/
    │   ├── texto_boas_vindas.py             # novo: montagem pura
    │   ├── service.py                       # + agendar_boas_vindas, processar_trabalho_*
    │   └── repository.py                    # (reusa inserir_mensagem_enviada_pendente)
    └── hospedagem/
        ├── repository.py                    # + confirmar_chegada (UPDATE guardado)
        ├── service.py                       # + confirmar_chegada
        ├── schema.py                        # + ChegadaResposta, + campo na fila
        └── router.py                        # + POST /reservas/{id}/chegada

worker/
├── agendador.py                             # + verificar_boas_vindas_pendentes
├── consumidor.py                            # + despacho de enviar_boas_vindas
└── __main__.py                              # + --verificar-boas-vindas

testes/
├── suporte/
│   └── ambiente_de_acesso.py                # + _semear_boas_vindas (valores distintos)
├── unitarios/
│   ├── modulos/
│   │   ├── acesso/test_politica.py          # estende: duas operações novas
│   │   ├── conversa/test_texto_boas_vindas.py    # novo: corpo, convite, sem oferta
│   │   ├── conversa/test_agendar_boas_vindas.py  # novo: decisão, com falsos
│   │   ├── conversa/test_log_sem_conteudo.py     # estende: eventos de boas-vindas
│   │   ├── propriedade/test_slots_boas_vindas.py # novo: validação na gravação
│   │   ├── propriedade/test_bootstrap.py         # estende: quatro chaves
│   │   └── hospedagem/test_confirmar_chegada.py  # novo: decisão e recusa
│   ├── adaptadores/test_mensageria_falsa.py # estende: enviar_boas_vindas
│   └── worker/
│       ├── test_recuperar_boas_vindas.py    # novo: elegibilidade pela janela do checkin_em
│       └── test_cli_worker.py               # estende: --verificar-boas-vindas
└── integracao/
    ├── test_confirmar_chegada.py            # rotas, 409, perfis, isolamento, fila
    ├── test_boas_vindas_slots.py            # GET/PUT, recusas, isolamento
    ├── test_boas_vindas_envio.py            # worker envia, falha, segunda tentativa
    ├── test_bootstrap.py                    # quatro chaves após instalação em banco migrado
    ├── test_fila_do_dia.py                  # estende: as duas sinalizações
    ├── test_garantias_do_banco.py           # estende: índice único e transição
    ├── test_conformidade_do_esquema.py      # vigia o delta 0008
    └── test_rotas_protegidas.py             # as três rotas novas exigem 401

docs/
├── 04-schema.sql                            # delta 0008 aplicado ao documento
└── 00-ESTADO-DO-PROJETO.md                  # F2.2 concluída; chaves novas na tabela
```

**Structure Decision**: monolito modular existente, sem camada nova. Cada trabalho no módulo
que governa a tabela: `hospedagem` (reserva), `conversa` (mensagem), `propriedade`
(parametro_hotel), `app/fila` (trabalho). `hospedagem → conversa` por parâmetro injetável, na
mesma forma que `criar_reserva` já usa; nenhum import em sentido contrário.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Envio manual de boas-vindas para reserva fora da janela | Fica sinalizada na fila; ninguém envia | Fatia futura, se a operação pedir |
| Sinalização de slot vazio em chegada antecipada | Elegível ao envio, mas fora da fila até a data prevista | Fatia de UI / revisão da visão |
| Rota para a recepção ajustar `horas_validade_boas_vindas` | Semeada em 12; muda por SQL ou pela fatia de parâmetros | Fatia de parâmetros da gestão |
| Confirmação em lote no fim do pico | Um clique por reserva | Fatia futura (mitigação da jornada §9.1) |
| Inferência de chegada por mensagem recebida | Reserva não confirmada continua não confirmada | Fatia futura |
| Chegada de reserva ainda em `aguardando_cadastro` | Recusa com `409` até a varredura marcar sem cadastro prévio | Spec própria, se necessário |
| Resposta a dúvida a partir do catálogo | O recado convida a perguntar; ninguém responde ainda | F3.3 |
| Checkout, cancelamento, pulso, classificação de mensagem | Fora | F2.3+ |
| Oferta comercial no recado | Fora por decisão econômica (reclassificação de template) | Fatia de mercado |
| Tela React da confirmação e dos slots | Estado via API | Fatia de UI |
| Validação do texto no momento do envio como regra própria | A mesma função pura é reusada; não há segunda regra | — |

## Complexity Tracking

> Sem violações a justificar. Tabela omitida.
