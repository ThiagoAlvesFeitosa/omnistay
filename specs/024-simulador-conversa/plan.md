# Implementation Plan: Simulador de Conversa

**Branch**: `024-simulador-conversa` | **Date**: 2026-08-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/024-simulador-conversa/spec.md`

## Summary

Modo de demonstração em que o hóspede da banca vive numa tela: todo
recado que iria ao provedor aparece no fio, e o apresentador digita o
turno do hóspede. O hotel é o mesmo — classificação, confirmação antes
do chamado, pulso, catálogo. Só o canal muda.

Decisões em [research.md](./research.md): `MENSAGERIA_MODO`
(`demonstracao` \| `real`) na configuração de plataforma; fábrica
`MensageriaSimulada` / `MensageriaWhatsapp`; worker deixa de instanciar
`MensageriaFalsa`; entrada reusa `receber_evento_entrada`; tela lê
`mensagem`; operação `usar_simulador`; React mínimo em `frontend/`;
**sem** tabela e **sem** revisão Alembic. Webhook HMAC da F3.1 não
muda.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento);
TypeScript no frontend mínimo

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core (já no projeto).
`httpx` promovido a dependência principal (o adaptador WhatsApp já o
importa). Frontend: Vite + React + TypeScript — stack já decidida, pasta
ainda inexistente. **Nenhuma** fila, cache ou lib de UI. Sem WebSocket

**Storage**: PostgreSQL 16. **Nenhuma tabela nova.** Reuso de `mensagem`,
`evento_webhook`, `reserva`, `trabalho`. UNIQUE de `id_externo` na
entrada. `0001`…`0021` intactos

**Testing**: pytest. Unitários: fábrica, matriz `usar_simulador`, serviço
recusa modo `real`, idempotência, log sem conteúdo. Integração com
PostgreSQL real: GET/POST autenticados, isolamento entre hotéis, worker
com `MensageriaSimulada` torna o recado visível no GET, `MensageriaFalsa`
permanece injetada no restante da suíte. **Nenhum** teste instancia
WhatsApp nem abre navegador

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL
em contêiner. API + worker + uma página no mesmo origin (proxy Vite ou
`/demo/` estático)

**Project Type**: Serviço web + worker + **uma** tela de conversa. Sem
painel operacional React

**Performance Goals**: Um hotel no MVP; GET do fio é lista da reserva
(dezenas de mensagens). Polling ~1 s na página aberta. Sem meta de
throughput

**Constraints**: Um modo por processo; domínio sem `if` de canal;
`id_hotel` da sessão em toda consulta; log sem conteúdo; cookie F0.3
intocado; confirmação antes do chamado intacta; pergunta fora do
catálogo continua humana; tela recusa em modo `real`

**Scale/Scope**: 1 chave de ambiente, 1 fábrica, 1 adaptador novo, 1
operação na matriz, 3 rotas, 1 página React. Sem migração, sem tipo
novo na fila, sem módulo novo

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Tela não infere chegada/saída. Cliques de fase permanecem os já entregues |
| II — Na dúvida, humano vê | Entrada cai no mesmo classificador; fora do catálogo não inventa |
| III — Gravar antes de enviar | POST da tela grava e enfileira; recado do hotel só depois do worker. Texto já está em `mensagem` antes da porta de saída |
| IV — Fila como verdade | Worker existente; a tela só lê. Sem push |
| V — Ausência humana visível | `pendente`/`falha` aparecem no fio. Chegada/saída continuam clique |
| VI — Confirmação antes de tramitar | Mesmo worker das F3.4/F3.5; a tela não abre chamado no POST |
| VII — Não ser intrusivo | Nenhum recado proativo novo; só troca o destino dos já existentes |
| VIII — Minimização | Sem hóspede fantasma; log sem conteúdo; foto continua recusada |
| IX — Garantias no banco | UNIQUE de `evento_webhook`; sem tabela nova a garantir |
| X — Portas trocáveis | É a fatia: fábrica + `MensageriaSimulada`. Domínio sem adaptador concreto |
| XI — Complexidade exige problema | Sem WebSocket, sem módulo, sem buffer, sem kit UI. React existe porque a spec exige tela e a stack já o escolheu. `httpx` já era import do WhatsApp |
| XII — Teste primeiro | Cada FR com teste que falha por ausência |
| XIII — Parâmetro não é constante | Modo **não** é `parametro_hotel` (é canal de plataforma, pesquisa §1) |
| XIV — Multi-tenant | `id_hotel` da sessão; `404` cruzado |
| XV — Honestidade | Tela ≠ WhatsApp; demo local não prova entrega da Meta; webhook+túnel junto com demo pode misturar entrada; sem painel operacional nesta fatia |

**Ponto de atenção 1 — `MensageriaFalsa` no worker.** O `__main__` hoje
engole envio. Fechar isso é o Artigo X cumprido, não regressão da suíte
(a suíte injeta a porta).

**Ponto de atenção 2 — gestão vê telefone na lista.** A F0.3 recusa
cadastro à gestão nas rotas de hospedagem. Aqui a spec entrega a tela
também à gestão; o contrato limita ao mínimo para escolher o fio. Ficha
completa continua recusada.

**Ponto de atenção 3 — webhook intocado.** Isolamento do modo real é a
tela `409` + adaptador sem Graph API. Recusar HMAC em demo quebraria a
F3.1 sem benefício local (não há túnel). Limitação na pesquisa §4.

## Project Structure

### Documentation (this feature)

```text
specs/024-simulador-conversa/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── modo-e-fabrica.md
│   ├── api-do-simulador.md
│   ├── entrada-simulada.md
│   ├── politica-de-autorizacao.md
│   └── tela-de-simulacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
app/
├── config.py                            # mensageria_modo
├── main.py                              # StaticFiles /demo/ se dist existir
├── adaptadores/
│   ├── mensageria_simulada.py           # novo
│   ├── mensageria_falsa.py              # suíte; worker não instancia
│   ├── mensageria_whatsapp.py           # escolhido em modo real
│   └── fabrica_mensageria.py            # construir_mensageria
└── modulos/
    ├── acesso/politica.py               # usar_simulador
    └── conversa/
        ├── router.py                    # + rotas /simulador
        ├── service.py                   # lista/fio/turno; chama receber_evento_entrada
        ├── repository.py                # listar mensagens da reserva no hotel
        └── schema.py                    # DTOs da tela

worker/
├── __main__.py                          # fábrica em vez de MensageriaFalsa()
└── consumidor.py                        # default da fábrica só se gateway omitido

frontend/                                # novo, mínimo
├── package.json
├── vite.config.ts                       # proxy para uvicorn
├── index.html
└── src/
    ├── main.tsx
    └── TelaSimulacao.tsx

testes/
├── unitarios/
│   ├── adaptadores/test_fabrica_mensageria.py
│   ├── adaptadores/test_mensageria_simulada.py
│   └── modulos/
│       ├── acesso/test_politica.py      # estende
│       └── conversa/test_simulador.py
└── integracao/
    └── test_simulador_conversa.py
```

**Structure Decision**: monólito já existente + pasta `frontend/` prevista
no Artefato 5 e ainda vazia. Simulador mora em `conversa` (dono de
`mensagem`). Sem módulo novo. Sem `alembic/versions/0022_*`.

## Complexity Tracking

> Sem violações a justificar. React entra porque a spec exige tela e a
> constituição/stack já o nomeiam — não é um quarto runtime. Tabela
> omitida.
