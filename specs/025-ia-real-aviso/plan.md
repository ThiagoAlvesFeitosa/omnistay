# Implementation Plan: IA real e aviso de assistente virtual

**Branch**: `025-ia-real-aviso` | **Date**: 2026-08-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/025-ia-real-aviso/spec.md`

## Summary

O worker deixa de instanciar o adaptador controlado no escuro. Escolher
o serviço de linguagem real ou o controlado vira configuração de
plataforma, no molde do canal. Falha, demora ou JSON inválido reusam o
encaminhamento humano já existente. A primeira mensagem da estadia — o
recado de boas-vindas — declara a assistente virtual em texto fixo do
produto.

Decisões em [research.md](./research.md): `LLM_MODO`
(`controlado` \| `real`); fábrica; `LLMGemini` via `httpx` (sem SDK);
timeout 15 s; aviso na montagem do recado; **sem** tabela e **sem**
revisão Alembic. Canal e cérebro continuam independentes.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, `httpx` (já
principal). Porta `LLMProvider` inalterada em métodos. **Nenhuma**
lib nova — sem `google-genai`, Redis, Celery ou fila extra

**Storage**: PostgreSQL 16. **Nenhuma tabela nova.** Reuso de
`mensagem` (corpo do recado e `classificacao` / `bruto` já gravados).
`0001`…`0021` intactos

**Testing**: pytest. Unitários: fábrica (controlado / real-sem-rede /
modo inválido / real sem chave), adaptador com `httpx.MockTransport`
(timeout, 429, JSON inválido, sucesso nos cinco métodos), aviso no
texto de boas-vindas, log sem chave e sem conteúdo. Integração: worker
com fábrica `controlado` não regressa ficha/classificar/dúvida; recusa
de subida não se aplica à suíte que injeta a porta. **Nenhum** teste
chama `generativelanguage.googleapis.com`

**Target Platform**: Servidor Linux; desenvolvimento Windows +
PostgreSQL em contêiner. API HTTP desta fatia **intocada**. Worker
existente

**Project Type**: Serviço web + worker. Sem tela nova

**Performance Goals**: uma chamada HTTP por método da porta, fora do
webhook; timeout 15 s para não prender a passagem. Volume da
demonstração: dezenas de chamadas; estouro de quota degrada a humano

**Constraints**: um modo por processo; domínio sem `if` de provedor;
`id_hotel` intacto; log sem conteúdo e sem chave; testes sem rede;
personalidade e linha de convite fora; template Meta das boas-vindas
não republicado nesta fatia

**Scale/Scope**: 2 chaves obrigatórias de ambiente (`LLM_MODO`,
`GEMINI_API_KEY` no modo real), 1 fábrica, 1 adaptador, 1 constante de
aviso, ajuste do worker e de `.env.example`. 0 rotas, 0 operações na
matriz, 0 migrações

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Cérebro e aviso não inferem chegada/saída nem lançamento |
| II — Na dúvida, humano vê | Timeout, 429, recusa, JSON inválido e fato fora do catálogo reusam os ramos já entregues |
| III — Gravar antes de enviar | Intocado. O aviso entra no `corpo` **antes** do envio, na montagem já existente |
| IV — Fila como verdade | Worker existente; pendência humana continua na fila do dia |
| V — Ausência humana visível | Indisponível do serviço real não some: o desfecho humano já é visível |
| VI — Confirmação antes de tramitar | Intacta. A fábrica não abre chamado |
| VII — Não ser intrusivo | Aviso **dentro** do recado de chegada; sem mensagem proativa nova |
| VIII — Minimização | Log sem texto, sem prompt, sem chave. Foto continua recusada |
| IX — Garantias no banco | Nenhuma tabela nova. UNIQUE e triggers das fatias anteriores intactos |
| X — Portas trocáveis | É a fatia: fábrica + `LLMGemini`. Domínio sem adaptador concreto |
| XI — Complexidade exige problema | Sem SDK Google. `httpx` já sobe o WhatsApp. Sem fila, cache ou módulo novo |
| XII — Teste primeiro | Cada FR com teste que falha por ausência; zero chamada ao serviço real |
| XIII — Parâmetro não é constante | Modo, timeout e modelo são plataforma, não `parametro_hotel` |
| XIV — Multi-tenant | Consultas de domínio intocadas; um cérebro por processo, não por hotel |
| XV — Honestidade | Quota gratuita pode degradar a humano; aviso no WhatsApp real exige republicar o template Meta |

**Ponto de atenção 1 — `LLMFalso` no consumidor.** O default
`llm or LLMFalso()` em `processar_uma_passagem` permanece **só** para a
suíte que chama a função direto e omite a porta (mercado, coleta).
`__main__` e `processar_uma_passagem_na_engine` passam a usar a fábrica.
Isso é o Artigo X cumprido, não regressão: a suíte que precisa de
desfecho armado continua injetando.

**Ponto de atenção 2 — template Meta.** O critério de pronto do aviso é
o `corpo` montado (histórico + simulador). O canal WhatsApp ignora o
corpo. Não se mexe na tupla de quatro variáveis.

**Ponto de atenção 3 — CLI do worker.** Testes que fingem
`obter_configuracao` só com `mensageria_modo` passam a incluir
`llm_modo` (e chave se `real`). Sem isso a subida nova falha alto — o
comportamento pedido.

## Project Structure

### Documentation (this feature)

```text
specs/025-ia-real-aviso/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── modo-e-fabrica-llm.md
│   ├── adaptador-real.md
│   ├── aviso-assistente-virtual.md
│   └── logs-e-segredo.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
app/
├── config.py                            # llm_modo, gemini_api_key,
│                                        # llm_timeout_seconds, llm_modelo
├── adaptadores/
│   ├── llm_falso.py                     # suíte + modo controlado
│   ├── llm_gemini.py                    # novo
│   └── fabrica_llm.py                   # construir_llm
└── modulos/conversa/
    └── texto_boas_vindas.py             # constante de aviso

worker/
├── __main__.py                          # fábrica LLM na subida
└── consumidor.py                        # default da fábrica se llm omitido
                                         # em processar_uma_passagem_na_engine

.env.example                             # LLM_MODO, GEMINI_API_KEY, …

testes/
├── unitarios/
│   ├── adaptadores/test_fabrica_llm.py
│   ├── adaptadores/test_llm_gemini.py   # MockTransport; sem rede
│   ├── adaptadores/test_llm_falso.py    # intacto
│   └── modulos/conversa/test_texto_boas_vindas.py  # estende
└── integracao/
    └── test_ia_real_aviso.py            # subida / aviso no recado gravado
```

**Structure Decision**: monólito existente. Sem módulo novo. Sem
`alembic/versions/0022_*`. Sem rota HTTP. O aviso mora na função pura
que já monta o recado.

## Complexity Tracking

> Sem violações a justificar. Tabela omitida.
