# Implementation Plan: Abrir Chamado de Reclamação

**Branch**: `014-abrir-chamado-reclamacao` | **Date**: 2026-08-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/014-abrir-chamado-reclamacao/spec.md`

## Summary

Depois de classificar `reclamacao_tecnica` (qualquer sentimento), o worker
consome `abrir_chamado_reclamacao`: grava um recado padrão (recebimento +
manutenção acionada; pergunta o horário só se ainda desconhecido), abre
`solicitacao` tipo `reclamacao` (quarto e janela extraídos do texto ou nulos,
sem valor), atualiza o JSON da recebida e envia em sessão. A confirmação é
inserida **antes** da solicitação na mesma transação; o envio é depois. A
equipe vê `GET /solicitacoes` com janela e destaque por tempo, sem ficha.
Fila do dia da recepção **não** muda. Zero `consumo`. Resposta posterior que
só informa horário preenche o mesmo chamado, sem LLM e sem segundo recado.

Decisões em [research.md](./research.md): tipo novo enfileirado na
classificação; `abrir_reclamacao` no módulo `atendimento` já existente;
atalho de janela injetado no classificar; sem LLM novo; `enviar_texto_sessao`
reutilizado; prazo `horas_destaque_chamado_aberto` em `parametro_hotel`.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary (já
no projeto). Portas `MensageriaGateway` existente (`enviar_texto_sessao`) e
relógio existente. **Nenhuma dependência nova.** Sem Redis, Celery ou provedor
de IA na suíte deste ramo

**Storage**: PostgreSQL 16. Reuso de `mensagem`, `trabalho`, `solicitacao`,
`reserva`, `parametro_hotel`. Revisão `0013_abrir_chamado_reclamacao`: CHECK do
tipo, índice único, semente do prazo. **Nenhuma tabela nova e nenhuma coluna
nova.** `vw_fila_do_dia` intocada

**Testing**: pytest. Unitários sem rede: extração de janela / `parece_resposta_de_horario`,
recado com e sem pergunta, classificar enfileira chamado sem INSERT, atalho de
janela não chama LLM, processador grava confirmação antes de `abrir_reclamacao`,
idempotência, destaque com relógio injetado, log sem texto. Integração com
PostgreSQL real: worker consome o tipo; `GET /solicitacoes` com reclamação +
janela + destaque; hotel B não vê A; unicidade no banco; pedido/dúvida não abrem
reclamação; zero `consumo`; sentimento neutro ainda abre

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em
contêiner. Nenhuma rota HTTP nova (estende o JSON de `GET /solicitacoes`).
Worker existente. Sem frontend

**Project Type**: Serviço web + worker. Sem React

**Performance Goals**: registro no worker, fora do webhook. Volume do MVP:
dezenas de reclamações por minuto; extração de quarto/janela é função pura

**Constraints**: HTTP do webhook **nunca** abre `solicitacao`; `id_hotel` em toda
leitura via reserva/sessão; reclamação, confirmação e janela nunca em log;
testes sem mensageria real; reserva não muda de status; zero `consumo`; staff
não lê ficha; prazo de destaque não é constante de código

**Scale/Scope**: 0 rotas HTTP novas, 0 operações novas na matriz, 0 métodos novos
nas portas, 1 tipo de trabalho, 1 ramo no worker, 1 chave de parâmetro, 1 revisão
Alembic. Sem React, sem resolver chamado, sem consumo, sem pulso

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas duas
passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Quarto e janela só do texto; não consulta inventário nem agenda da manutenção |
| II — Na dúvida, humano vê | Reclamação educada (sentimento não negativo) ainda vira chamado; quarto/janela ausentes não descartam |
| III — Gravar antes de enviar | Confirmação e `solicitacao` persistem antes de `enviar_texto_sessao` |
| IV — Fila como verdade | `GET /solicitacoes`; não depende de notificação |
| V — Ausência humana visível | Chamado aberto permanece; tempo excessivo é destacado; janela faltando não esconde |
| VI — Confirmação antes de tramitar | INSERT da enviada antes do INSERT da `solicitacao` na mesma transação; não espera o horário |
| VII — Não ser intrusivo | Um recado (confirmação + pergunta condicional); resposta de horário sem segundo texto |
| VIII — Minimização | Log sem texto/janela; staff/gestão sem ficha |
| IX — Garantias no banco | UNIQUE do trabalho por mensagem; UNIQUE de `id_mensagem_origem` (já na `0012`) |
| X — Portas trocáveis | Mensageria pela porta já existente; suíte com `MensageriaFalsa` |
| XI — Complexidade exige problema | Sem LLM novo, sem tipo extra para janela, sem React, sem coluna de destaque |
| XII — Teste primeiro | Cada FR com teste que falha por ausência; unitário de classificar continua sem INSERT |
| XIII — Parâmetro não é constante | `horas_destaque_chamado_aberto`; ausência não usa default no código |
| XIV — Multi-tenant | `abrir_reclamacao` / `listar_abertas` pelo hotel do trabalho/sessão |
| XV — Honestidade | Sem React, sem quarto/horário mágico, sem cobrança, extração conservadora de janela |

**Ponto de atenção 1 — classificar idempotente tem de enfileirar o chamado.** Se o
desfecho já existe e `abrir_chamado_reclamacao` ainda não, o caminho “já
classificada” insere o trabalho. Senão um crash entre eixos e enqueue perde o
gancho (mesmo defeito evitado na F3.3/F3.4).

**Ponto de atenção 2 — `test_reclamacao_nao_abre_chamado` deixa de ser “zero
enqueue”.** Continua verdadeiro que classificar **não** INSERT `solicitacao`.
Passa a ser verdadeiro que **enfileira** `abrir_chamado_reclamacao`. Pedido e
dúvida **não** ganham esse tipo.

**Ponto de atenção 3 — não ligar `precisa_atendimento_humano`.** Ar-condicionado
na fila da recepção treinaria ignorar o flag. A equipe lê `GET /solicitacoes`.

**Ponto de atenção 4 — atalho de janela antes do LLM.** `14h` não pode cair em
`fora_de_escopo` + flag humano. Injeção de `completar_janela`; `conversa` não
escreve `solicitacao`.

**Ponto de atenção 5 — payload da fila sem ficha.** `janela_preferencia` no JSON
é operacional (horário de reparo), não ficha. Continua proibido: nome, telefone,
documento. `id_reserva` é permitido. Janela **não** vai para log.

**Ponto de atenção 6 — não copiar backoff de LLM.** Este ramo não chama LLM no
consumo do chamado. Reagendar só a mensageria, depois de gravar. O atalho de
janela também não chama LLM.

**Ponto de atenção 7 — prazo ausente não inventa 2 horas.** Semente no bootstrap
e na migração; leitura sem chave → zero destaque + `prazo_ausente`.

## Project Structure

### Documentation (this feature)

```text
specs/014-abrir-chamado-reclamacao/
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
│   └── quarto-e-janela.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
alembic/versions/
├── 0013_abrir_chamado_reclamacao.py
└── sql/
    └── 0013_abrir_chamado_reclamacao.sql

app/
├── main.py                    # intocado (roteador atendimento já incluso)
├── portas/                    # intocado
├── adaptadores/               # intocado
└── modulos/
    ├── conversa/
    │   ├── service.py         # enfileira chamado; atalho de janela; processar_trabalho_abrir_chamado
    │   ├── repository.py      # UPDATE JSON da recebida (confirmacao_reclamacao / janela_registrada)
    │   └── texto_confirmacao_reclamacao.py
    ├── atendimento/
    │   ├── service.py         # abrir_reclamacao; completar_janela_se_resposta; destaque na listagem
    │   ├── repository.py      # inserir_reclamacao; UPDATE janela; SELECT janela
    │   ├── schema.py          # janela_preferencia, destaque_tempo_excedido
    │   ├── router.py          # mesmo GET; schema novo
    │   ├── quarto.py          # reutilizado
    │   └── janela.py          # extrair_janela_preferencia, parece_resposta_de_horario
    └── propriedade/
        └── service.py         # semente horas_destaque_chamado_aberto
app/fila/
├── repository.py              # tipo, unique, allowlist
└── service.py                 # enfileirar_abrir_chamado_reclamacao

worker/
└── consumidor.py              # ramo abrir_chamado_reclamacao; injeta abrir_reclamacao e completar_janela

testes/
├── unitarios/
│   ├── fila/                  # claim passa a consumir abrir_chamado_reclamacao
│   ├── modulos/conversa/
│   │   ├── test_classificar_mensagem.py  # enqueue chamado; atalho janela
│   │   ├── test_abrir_chamado.py
│   │   ├── test_texto_confirmacao_reclamacao.py
│   │   └── test_log_sem_conteudo.py
│   └── modulos/atendimento/
│       ├── test_janela.py
│       ├── test_abrir_reclamacao.py
│       └── test_listar_abertas.py        # janela + destaque
├── integracao/
│   ├── test_abrir_chamado.py
│   ├── test_solicitacoes.py             # reclamação no GET; destaque; isolamento
│   └── test_garantias_do_banco.py       # unicidade do trabalho novo
└── ...

docs/
├── 04-schema.sql
├── 04-modelagem-de-dados.md
└── 00-ESTADO-DO-PROJETO.md          # na implementação: F3.5
```

**Structure Decision**: monolito modular existente. Confirmação e envio em
`conversa`; `solicitacao` em `atendimento`; prazo em `propriedade`; fila só
abre o claim. Sem React, sem porta nova, sem LLM no ramo do chamado.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Marcar resolvido + aviso de conclusão | Chamado fica `aberta` | F3.6 |
| Consumo, valor, fila de lançamento | Reclamação nunca gera cobrança | F3.7 |
| Pulso / supressão por chamado aberto | Chamado existe; pulso não lê ainda | F3.8 |
| Quarto na reserva / inventário | Sem palavra-chave, quarto nulo | Fora (Artigo I) |
| Extração de janela por IA | Sem padrão, janela nula e visível | Fora (Artigo XI / XV) |
| Ack ao registrar o horário depois | Silêncio após a pergunta já feita | Fora (Artigo VII) |
| `GET` HTTP do histórico | Teste lê `mensagem` no banco | Fatia de UI |
| Tela React / Alert Center visual | Estado via `GET /solicitacoes` | Fatia de UI |
| Notificação push ao staff | Fila é a verdade | Fora (Artigo IV) |
| Ordem estrita entre mensagens | Cada trabalho é independente | Fora (Artigo XV) |

## Complexity Tracking

> Sem violações a justificar. Tabela omitida.
