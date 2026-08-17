# Implementation Plan: Classificar a Intenção

**Branch**: `011-classificar-intencao` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/011-classificar-intencao/spec.md`

## Summary

O worker passa a consumir `classificar_mensagem`: chama `LLMProvider.classificar`, o
domínio valida a taxonomia e grava intenção, sentimento, urgência e a resposta completa
em `mensagem.classificacao_bruta`. Falha do classificador (indisponível ou formato
inválido) e intenções sem ramo posterior (`upsell`, checkout, fora de escopo) viram
pendência visível na fila do dia (`precisa_atendimento_humano`). Dúvida, pedido e
reclamação ficam só classificados — sem envio, sem chamado, sem catálogo. O trabalho
termina `concluido` em todo desfecho; não há retentativa contra o LLM.

Decisões em [research.md](./research.md): allowlist+ramo juntos e inversão dos testes
da F3.1; validação no domínio; escala na primeira falha; desfecho no JSON já existente;
coluna só na visão; `LLMFalso` sem quebrar a ficha.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary (já no
projeto). Porta `LLMProvider` existente. **Nenhuma dependência nova.** Sem Redis,
Celery, fila externa ou provedor de IA na suíte

**Storage**: PostgreSQL 16. Reuso de `mensagem` (eixos + `JSONB`), `trabalho`,
`vw_fila_do_dia`. Revisão `0010_classificar_intencao`: `DROP`/`CREATE` da visão com
`precisa_atendimento_humano`. **Nenhuma tabela e nenhuma coluna nova em tabela-base**

**Testing**: pytest. Unitários sem rede: taxonomia (válida / inválida), desfechos
(`classificado` vs `encaminhado_humano` vs `indisponivel` vs `formato_invalido`),
conteúdo intocado, zero envio / zero `solicitacao`, log sem texto nem bruto, idempotência
se já classificada, `LLMFalso` não quebra `extrair_ficha`. Integração com PostgreSQL
real: worker consome o tipo; fila do dia liga o sinal; F1.3 intacta; isolamento entre
hotéis; testes da F3.1 que proibiam o claim são invertidos

**Target Platform**: Servidor Linux; desenvolvimento Windows + PostgreSQL em contêiner.
API intocada neste fluxo; worker existente. Sem frontend

**Project Type**: Serviço web + worker. Sem React

**Performance Goals**: classificação no worker, fora do webhook (já responde em
milissegundos). Volume do MVP: dezenas de mensagens de estadia por minuto

**Constraints**: HTTP do webhook **nunca** chama LLM; `id_hotel` em toda leitura/gravação;
conteúdo e `bruto` nunca em log; testes sem provedor real; primeira falha do classificador
escala (sem backoff de LLM); reserva não muda de status; catálogo e mensageria de saída
fora deste tipo de trabalho

**Scale/Scope**: 0 rotas HTTP novas (estende `GET /fila-do-dia`), 0 operações novas na
matriz, 1 método na porta, 1 ramo no worker, 1 revisão Alembic (visão). Sem React, sem
chamado, sem resposta ao hóspede

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas duas
passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Classificar não infere check-in, checkout nem lançamento |
| II — Na dúvida, humano vê | Indisponível, inválido e intenção sem ramo → recepção; nunca resposta inventada |
| III — Gravar antes de processar | Mensagem já gravada na F3.1; esta fatia só preenche classificação depois |
| IV — Fila como verdade | Sinal em `vw_fila_do_dia`; não depende de notificação |
| V — Ausência humana visível | `precisa_atendimento_humano` na fila que a recepção já lê |
| VI — Confirmação antes de tramitar | Não tramita solicitação/reclamação; não envia confirmação |
| VII — Não ser intrusivo | Zero mensagem de saída |
| VIII — Minimização | Log sem conteúdo e sem bruto; foto não entra aqui |
| IX — Garantias no banco | CHECK dos eixos já existe; visão derivada, sem coluna paralela que possa divergir |
| X — Portas trocáveis | `classificar` na porta; `LLMFalso` na suíte; domínio sem adaptador concreto |
| XI — Complexidade exige problema | Sem fila nova, sem módulo `atendimento`, sem lib nova |
| XII — Teste primeiro | Cada FR com teste que falha por ausência; testes F3.1 invertidos de propósito |
| XIII — Parâmetro não é constante | Sem prazo novo; não se inventa timeout mágico no código de domínio |
| XIV — Multi-tenant | Gravação e fila sempre com `id_hotel` do trabalho/reserva |
| XV — Honestidade | Sem resposta automática, sem chamado, sem React, sem ordem entre mensagens |

**Ponto de atenção 1 — os testes da F3.1 afirmam o contrário desta fatia.**
`reclamar_proximo` e o worker **não** consomem `classificar_mensagem` hoje. Esta entrega
inverte allowlist, ramo e aqueles testes no mesmo passo. Deixar os testes antigos verdes
seria suíte mentirosa.

**Ponto de atenção 2 — não copiar a retentativa da ficha.** `interpretar_ficha` ainda
reagenda o LLM. Aqui a spec manda escalar na primeira falha e concluir o trabalho.
Reagendar seria FR-012 vermelho.

**Ponto de atenção 3 — não sobrecarregar `estado_cadastro`.** `leitura_humana` é da
ficha em `aguardando_cadastro`. O sinal da estadia é coluna nova na visão, booleana.

**Ponto de atenção 4 — `conversa` grava; `hospedagem` só projeta.** Mesmo padrão da
F1.3. O ramo do worker **não** importa `hospedagem` (evita ciclo e não muda reserva).

## Project Structure

### Documentation (this feature)

```text
specs/011-classificar-intencao/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── llm-e-classificacao.md
│   ├── fila-e-worker.md
│   ├── api-de-hospedagem.md
│   └── politica-de-autorizacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
alembic/versions/
├── 0010_classificar_intencao.py
└── sql/
    └── 0010_classificar_intencao.sql

app/
├── portas/llm.py                    # + ResultadoClassificacao, FalhaDeClassificacao, classificar
├── adaptadores/llm_falso.py         # + classificar / configurar_classificacao
├── fila/repository.py               # allowlist inclui classificar_mensagem
└── modulos/
    ├── conversa/
    │   ├── service.py               # processar_trabalho_classificar_mensagem; validar taxonomia
    │   └── repository.py            # UPDATE eixos + JSON; não toca conteudo
    └── hospedagem/
        ├── schema.py                # ItemFilaDoDia.precisa_atendimento_humano
        ├── repository.py            # SELECT da coluna nova
        └── service.py               # mapeia o booleano

worker/
└── consumidor.py                    # ramo classificar_mensagem

testes/
├── unitarios/
│   ├── fila/
│   │   └── test_claim_nao_consome_classificar.py   # invertido: passa a consumir
│   ├── adaptadores/
│   │   └── test_llm_falso.py                       # + classificar sem quebrar ficha
│   └── modulos/conversa/
│       ├── test_classificar_mensagem.py            # desfechos, taxonomia, sem envio
│       └── test_log_sem_conteudo.py                # estende: classificação
├── integracao/
│   ├── test_webhook_estadia.py      # inverte test_worker_nao_consome_...
│   ├── test_classificar_mensagem.py # worker + eixos + sinal na fila
│   ├── test_fila_do_dia.py          # precisa_atendimento_humano
│   └── test_rotas_protegidas.py     # GET fila inalterado na matriz
└── ...

docs/
├── 04-schema.sql                    # visão + COMMENT
├── 04-modelagem-de-dados.md         # desfechos de classificacao_intencao / coluna da visão
└── 00-ESTADO-DO-PROJETO.md          # na implementação: F3.2
```

**Structure Decision**: monolito modular existente. Classificação mora em `conversa` +
porta LLM. Fila só abre o claim. Hospedagem só espelha a visão. Sem módulo
`atendimento`, sem React, sem rota nova.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Resposta automática a partir do catálogo | Dúvida classificada fica quieta | F3.3 |
| Pedido de serviço com confirmação | Pedido só tem eixos | F3.4 |
| Chamado de reclamação / Alert Center | Reclamação negativa não vira `solicitacao` | F3.5 |
| Consumo, pulso, pesquisa | Fora | F3.7–F4.1 |
| `GET` HTTP do histórico | Teste lê `mensagem` no banco | Fatia de UI |
| Marcar o sinal humano como “visto” | Flag permanece enquanto o desfecho existir | Fora (Artigo XI) |
| Retentativa de LLM | Escala na primeira falha | Decisão desta fatia |
| Adaptador real de IA na suíte | `LLMFalso` | Operação |
| Tela React | Estado via `GET /fila-do-dia` / banco | Fatia de UI |
| Ordem estrita entre mensagens | Cada trabalho é independente | Fora (Artigo XV) |

## Complexity Tracking

> Sem violações a justificar. Tabela omitida.
