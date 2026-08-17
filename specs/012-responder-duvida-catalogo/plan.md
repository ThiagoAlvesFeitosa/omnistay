# Implementation Plan: Responder Dúvida a partir do Catálogo

**Branch**: `012-responder-duvida-catalogo` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/012-responder-duvida-catalogo/spec.md`

## Summary

Depois de classificar `duvida_geral`, o worker consome `responder_duvida`: lê o
catálogo ativo da propriedade pela porta, pede ao `LLMProvider` um texto só com
esses fatos, valida trechos citados e envia em sessão. Se o catálogo não cobre, se
a redação não é fiel, se está vazio ou se a conversação falha, grava um aviso
padrão de que a recepção vai atender **antes** de marcar
`desfecho = duvida_nao_coberta` — o mesmo booleano da fila do dia, sem
`solicitacao`. Catálogo de outro hotel nunca entra. Trabalho termina `concluido`
em todo desfecho de redação; retentativa só de envio.

Decisões em [research.md](./research.md): tipo novo enfileirado na classificação;
conversação distinta de classificar; fidelidade por trechos; chamado = desfecho na
visão; `enviar_texto_sessao`; inversão pontual dos testes da F3.2 cuja passagem
completa via dúvida geral sem envio.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary (já
no projeto). Portas `LLMProvider`, `CatalogoRepository` e `MensageriaGateway`
existentes. **Nenhuma dependência nova.** Sem Redis, Celery, busca vetorial ou
provedor de IA na suíte

**Storage**: PostgreSQL 16. Reuso de `mensagem`, `trabalho`, `catalogo_item`,
`vw_fila_do_dia`. Revisão `0011_responder_duvida_catalogo`: CHECK do tipo, índice
único, visão com `duvida_nao_coberta`. **Nenhuma tabela e nenhuma coluna nova em
tabela-base**

**Testing**: pytest. Unitários sem rede: fidelidade (fiel / trecho órfão / trechos
vazios), catálogo vazio sem chamar LLM, isolamento por hotel, aviso padrão sem fato,
idempotência se já respondeu, classificar só enfileira, `LLMFalso` não quebra ficha
nem classificação, log sem texto. Integração com PostgreSQL real: worker consome o
tipo; coberta não liga o sinal; não coberta liga; F3.2 de outras intenções intacta;
teste da F3.2 de dúvida geral + passagem completa é atualizado

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em
contêiner. API intocada neste fluxo (exceto o significado do booleano já exposto).
Worker existente. Sem frontend

**Project Type**: Serviço web + worker. Sem React

**Performance Goals**: conversação no worker, fora do webhook. Volume do MVP:
dezenas de dúvidas por minuto; catálogo de dezenas de itens curtos no prompt

**Constraints**: HTTP do webhook **nunca** chama conversação; `id_hotel` em toda
leitura de catálogo e gravação; pergunta, resposta e itens nunca em log; testes sem
provedor real; primeira falha de conversação escala (sem backoff de LLM); reserva
não muda de status; zero `solicitacao`

**Scale/Scope**: 0 rotas HTTP novas, 0 operações novas na matriz, 1 método na porta
LLM, 1 método na porta de mensageria, 1 tipo de trabalho, 1 ramo no worker, 1
revisão Alembic. Sem React, sem Alert Center operacional

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas duas
passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Responder dúvida não infere check-in, checkout nem lançamento |
| II — Na dúvida, humano vê | Vazio, não coberta, não fiel e indisponível → aviso + recepção; nunca fato inventado |
| III — Gravar antes de enviar | `mensagem` enviada persiste antes de `enviar_texto_sessao` |
| IV — Fila como verdade | Sinal em `vw_fila_do_dia`; não depende de notificação |
| V — Ausência humana visível | `duvida_nao_coberta` no mesmo booleano que a recepção já lê |
| VI — Confirmação antes de tramitar | Aviso gravado antes do desfecho de chamado; coberta não tramita chamado |
| VII — Não ser intrusivo | Só responde a quem acabou de perguntar; sem mensagem proativa nova |
| VIII — Minimização | Log sem pergunta, resposta, trechos nem conteúdo de item |
| IX — Garantias no banco | UNIQUE do trabalho por mensagem; visão derivada, sem coluna paralela |
| X — Portas trocáveis | `responder_duvida` na porta LLM; catálogo pela porta; `LLMFalso` / `CatalogoFalso` / `MensageriaFalsa` na suíte |
| XI — Complexidade exige problema | Sem `solicitacao`, sem módulo `atendimento`, sem busca, sem lib nova |
| XII — Teste primeiro | Cada FR com teste que falha por ausência; testes F3.2 de passagem completa atualizados de propósito |
| XIII — Parâmetro não é constante | Sem prazo novo; aviso é recado fixo (como o lembrete), não número mágico de comportamento |
| XIV — Multi-tenant | `listar_ativos(id_hotel)` do trabalho; hotel A não responde pelo B |
| XV — Honestidade | Sem React, sem Alert Center operacional, sem ordem entre mensagens, sem detector absoluto de alucinação |

**Ponto de atenção 1 — a passagem completa da F3.2 com `duvida_geral` muda de
significado.** `test_classificacao_valida_nao_liga_sinal_nem_altera_conteudo` roda
`processar_uma_passagem` e hoje espera flag falso e zero enviada. Com catálogo vazio
(estado inicial), esta fatia avisa e liga o sinal. Atualizar esse teste no mesmo
commit; não deixá-lo verde mentindo. Pedido/reclamação/falha de classificar
permanecem como na F3.2.

**Ponto de atenção 2 — classificar idempotente tem de enfileirar.** Se o desfecho já
existe e `responder_duvida` ainda não, o caminho “já classificada” insere o trabalho.
Senão um crash entre eixos e enqueue perde a dúvida.

**Ponto de atenção 3 — não abrir `solicitacao`.** A spec delimita o chamado à
recepção. Criar tipo novo em `solicitacao` puxaria F3.5 para dentro desta fatia.

**Ponto de atenção 4 — não copiar backoff de LLM da ficha.** Conversação falha uma
vez e escala. Reagendar só a mensageria, depois de gravar.

**Ponto de atenção 5 — fidelidade é trecho citado, não NLP.** Trecho órfão recusa o
texto inteiro. Invenção sem trecho correspondente é o residual já aceito no Artefato
5 §10.3.

## Project Structure

### Documentation (this feature)

```text
specs/012-responder-duvida-catalogo/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── llm-e-conversacao.md
│   ├── catalogo-na-resposta.md
│   ├── fila-e-worker.md
│   ├── mensageria-sessao.md
│   ├── api-de-hospedagem.md
│   └── politica-de-autorizacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
alembic/versions/
├── 0011_responder_duvida_catalogo.py
└── sql/
    └── 0011_responder_duvida_catalogo.sql

app/
├── portas/
│   ├── llm.py                 # + ResultadoResposta, FalhaDeConversacao, responder_duvida
│   └── mensageria.py          # + enviar_texto_sessao
├── adaptadores/
│   ├── llm_falso.py           # + responder_duvida / configurar_resposta
│   ├── mensageria_falsa.py    # + enviar_texto_sessao
│   └── mensageria_whatsapp.py # + type text (suíte não instancia)
└── modulos/
    ├── conversa/
    │   ├── service.py         # enfileira ao classificar; processar_trabalho_responder_duvida
    │   ├── repository.py      # UPDATE JSON da recebida; INSERT enviada
    │   ├── fidelidade.py      # função pura trechos × catálogo
    │   └── texto_aviso_duvida.py
    └── hospedagem/            # inalterado no Python (visão cobre o booleano)
app/fila/
├── repository.py              # tipo, unique, allowlist
└── service.py                 # enfileirar_responder_duvida

worker/
└── consumidor.py              # ramo responder_duvida; injeta CatalogoBanco

testes/
├── unitarios/
│   ├── adaptadores/test_llm_falso.py
│   ├── fila/                  # claim passa a consumir responder_duvida
│   └── modulos/conversa/
│       ├── test_fidelidade.py
│       ├── test_responder_duvida.py
│       ├── test_classificar_mensagem.py  # enqueue sem envio
│       └── test_log_sem_conteudo.py
├── integracao/
│   ├── test_responder_duvida.py
│   ├── test_classificar_mensagem.py      # atualiza passagem duvida_geral
│   └── test_fila_do_dia.py               # duvida_nao_coberta liga o sinal
└── ...

docs/
├── 04-schema.sql
├── 04-modelagem-de-dados.md
└── 00-ESTADO-DO-PROJETO.md          # na implementação: F3.3
```

**Structure Decision**: monolito modular existente. Resposta mora em `conversa` +
três portas. Fila só abre o claim. Hospedagem só espelha a visão. Sem módulo
`atendimento`, sem React, sem rota nova.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Pedido de serviço com confirmação | Pedido só tem eixos | F3.4 |
| Chamado de reclamação / Alert Center | Reclamação não vira `solicitacao` | F3.5 |
| Consumo, pulso, pesquisa | Fora | F3.7–F4.1 |
| `GET` HTTP do histórico | Teste lê `mensagem` no banco | Fatia de UI |
| Detector absoluto de alucinação | Trechos citados + prompt; residual aceito | Fora (Artigo XV / ADR) |
| Busca semântica no catálogo | Catálogo inteiro na porta | Gatilho do ADR |
| Adaptador real de IA na suíte | `LLMFalso` | Operação |
| Tela React | Estado via `GET /fila-do-dia` / banco | Fatia de UI |
| Marcar o sinal humano como “visto” | Flag permanece enquanto o desfecho existir | Fora (Artigo XI) |
| Ordem estrita entre mensagens | Cada trabalho é independente | Fora (Artigo XV) |

## Complexity Tracking

> Sem violações a justificar. Tabela omitida.
