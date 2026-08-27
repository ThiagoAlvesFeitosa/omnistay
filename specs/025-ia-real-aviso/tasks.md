---
description: "Task list for feature implementation"
---

# Tasks: IA real e aviso de assistente virtual

**Input**: Design documents from `/specs/025-ia-real-aviso/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Obrigatórios. Artigo XII e a regra TDD do projeto: nenhuma linha de
produção sem teste que falhe antes pelo motivo certo. Nenhum teste chama
`generativelanguage.googleapis.com`.

**Organization**: Tarefas agrupadas por história (US1–US5). Configuração
(`LLM_MODO`) entra na Foundational. Fábrica e worker são a US2 (bloqueia a
US1 e a US3). O adaptador real que classifica/redige/extrai é a US1 (MVP
da demonstração). Mapeamento de timeout/429/JSON inválido é a US3. Aviso
no recado de boas-vindas é a US4 (pode seguir em paralelo com a US2). Log
e segredo são a US5. Sem migração. Sem rota HTTP nova. Sem SDK Google.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependência pendente)
- **[Story]**: A qual história a tarefa pertence (US1 a US5)

## Como ver os testes falharem nesta fatia

**Fábrica.** Sem `LLM_MODO` (ou valor lixo) `construir_llm` deve falhar
alto. O unitário falha com `ImportError` até existir o módulo; depois
falha por não levantar até a validação existir. `real` sem chave deve
levantar a **mesma** família de erro, sem devolver `LLMFalso`.

**Worker.** `testes/unitarios/worker/test_cli_worker.py`: mocks de
`obter_configuracao` só com `mensageria_modo` quebram quando `__main__`
passar a chamar `construir_llm`. O caso novo captura `llm=` (ou a
construção na subida) e exige falha alto sem `llm_modo`. Com
`llm_modo="controlado"`, `--uma-passagem` não instancia o controlado
por omissão em `processar_uma_passagem_na_engine`.

**Adaptador.** Unitários com `httpx.MockTransport` falham com
`AttributeError` até `LLMGemini` existir. Depois de existir vazio, falham
por não parsear o JSON do candidato. Assertiva: o transportador **não**
foi o host real — a suíte nunca resolve DNS de Google.

**Aviso.** `test_texto_confirma_chegada_traz_tres_fatos_e_um_convite`
hoje passa **sem** a frase. O caso novo exige as duas ideias e uma só
`?` na última linha — fica vermelho até a constante entrar em
`texto_boas_vindas.py`. Coleta **não** deve ganhar a frase (regressão
em `test_texto_coleta` se alguém errar o arquivo).

**Log.** `caplog` em classificação com texto de hóspede: se o adaptador
logar o prompt, o teste novo falha pelo motivo certo (texto no log).

---

## Phase 1: Setup

**Purpose**: chaves documentadas e helper de teste. O monólito já existe;
não criar pacote Python novo. Sem `google-genai`.

- [X] T001 [P] Documentar em `.env.example`, sem valor, as chaves
      `LLM_MODO=` (`controlado` \| `real` no comentário),
      `GEMINI_API_KEY=`, `LLM_TIMEOUT_SECONDS=` e `LLM_MODELO=`, no
      padrão de `MENSAGERIA_MODO`. Sem segredo
      ([contracts/modo-e-fabrica-llm.md](./contracts/modo-e-fabrica-llm.md))
- [X] T002 [P] Criar `testes/suporte/llm.py` com: `cfg_llm(modo, chave="",
      timeout=15.0, modelo="gemini-2.0-flash")` devolvendo objeto simples
      para a fábrica; `cliente_gemini_falso(handler)` montando
      `httpx.Client` + `MockTransport` que **nunca** abre rede. Docstring:
      uso só em teste

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: campos de plataforma na config. Sem fábrica ainda, sem
adaptador, sem aviso.

**⚠️ CRÍTICO**: US2 e US1 leem esses campos. US4 (aviso) não depende
deles e pode começar em paralelo depois deste checkpoint.

- [X] T003 Acrescentar em `app/config.py`: `llm_modo: str = ""`,
      `gemini_api_key: str = ""`, `llm_timeout_seconds: float = 15.0`,
      `llm_modelo: str = "gemini-2.0-flash"`. Não falhar no Settings —
      a fábrica é quem recusa modo vazio. Sem importar adaptador

**Checkpoint**: config lê as chaves. Histórias US2 e US4 podem começar.

---

## Phase 3: User Story 2 - Alternar o cérebro é configuração (Priority: P1)

**Goal**: `construir_llm` escolhe controlado ou real sem mudar código;
modo inválido ou real sem chave impede a subida; canal e cérebro não se
forçam. Worker de processo deixa de cair em `LLMFalso()` por omissão.

**Independent Test**: `construir_llm(cfg_llm("controlado"))` é
`LLMFalso`; `construir_llm(cfg_llm("real", chave="x"))` é `LLMGemini`
sem POST; `""` / `"gemini"` / `real`+chave vazia levantam
`ConfiguracaoDeInteligenciaInvalida`. `--uma-passagem` com
`llm_modo="controlado"` passa `llm=` da fábrica, não o default oculto.
Fábrica ignora `mensageria_modo`.

### Tests for User Story 2

- [X] T004 [US2] Unitários em
      `testes/unitarios/adaptadores/test_fabrica_llm.py`: modo
      `controlado` devolve `LLMFalso`; `real` com chave devolve
      `LLMGemini` **sem** chamar rede; ausente/vazio/`teste`/`DEMO`
      levantam `ConfiguracaoDeInteligenciaInvalida`; `real` com chave
      vazia levanta o mesmo tipo (não devolve controlado). Rodar e
      **ver falhar** ([contracts/modo-e-fabrica-llm.md](./contracts/modo-e-fabrica-llm.md),
      FR-001, FR-003, FR-016)
- [X] T005 [US2] Unitário em
      `testes/unitarios/adaptadores/test_fabrica_llm.py`: dois `cfg_llm`
      idênticos
      em `llm_modo` com `mensageria_modo` `demonstracao` vs `real`
      devolvem a **mesma** classe de LLM (FR-002, SC-009). Rodar e
      **ver falhar**
- [X] T006 [P] [US2] Estender
      `testes/unitarios/worker/test_cli_worker.py`: (a) todos os
      `obter_configuracao` falsos ganham `llm_modo="controlado"` para
      não quebrar a subida; (b) caso novo: sem `llm_modo`,
      `--uma-passagem` levanta `ConfiguracaoDeInteligenciaInvalida` e
      **não** chama `processar_uma_passagem_na_engine`. Rodar e **ver
      falhar** (FR-003)

### Implementation for User Story 2

- [X] T007 [US2] Criar `app/adaptadores/llm_gemini.py` com classe
      `LLMGemini`: `__init__` guarda chave, timeout, modelo e
      `httpx.Client` injetável; os cinco métodos da porta existem e
      levantam a `Falha*` do método com codigo `nao_implementado` até
      a US1. Sem POST ainda. Sem logar a chave
- [X] T008 [US2] Criar `app/adaptadores/fabrica_llm.py` com
      `ConfiguracaoDeInteligenciaInvalida` e `construir_llm(config)` até
      T004 e T005 verdes. **Não** importar a fábrica em
      `app/modulos/conversa/service.py`
- [X] T009 [US2] Em `worker/consumidor.py`,
      `processar_uma_passagem_na_engine`: `llm` omitido =
      `construir_llm(obter_configuracao())` (não `LLMFalso()`).
      `processar_uma_passagem(..., llm=)` continua aceitando injeção.
      Em `worker/__main__.py`, construir LLM na subida junto com
      mensageria; passar `llm=` à passagem. T006 verde. Exceção de
      config **não** interpola a chave

**Checkpoint**: worker sobe só com modo explícito; suíte que injeta
`llm=` permanece. US1 e US3 podem começar.

---

## Phase 4: User Story 1 - A conversa pensa de verdade (Priority: P1) 🎯 MVP

**Goal**: Com modo real, os cinco métodos da porta devolvem `Resultado*`
a partir de JSON do serviço (cliente injetado). Classificar, redigir e
extrair ficha levam o prompt cuidado. Item vendável e pesquisa de saída
passam pelo mesmo adaptador, prompt mais simples. Domínio e regras de
catálogo **não** mudam.

**Independent Test**: `LLMGemini` + `MockTransport` com candidato JSON
válido: `classificar` preenche eixos; `responder_duvida` devolve
`coberta`/`texto`/`trechos_citados`; `extrair_ficha` devolve desfecho e
campos sem idade; identificar e pesquisa devolvem o dataclass. Zero
chamada ao host real. `conversa.service` continua sem importar
`llm_gemini`.

### Tests for User Story 1

- [X] T010 [US1] Em `testes/unitarios/adaptadores/test_llm_gemini.py`:
      `classificar` com JSON de taxonomia válida devolve
      `ResultadoClassificacao` e `bruto` parseado; o request usa
      `x-goog-api-key` (não query), modelo de `cfg`, URL
      `generateContent`. Rodar e **ver falhar**
      ([contracts/adaptador-real.md](./contracts/adaptador-real.md))
- [X] T011 [US1] Em `testes/unitarios/adaptadores/test_llm_gemini.py`:
      `extrair_ficha` com JSON
      `desfecho`+`campos` (sem `idade`); `responder_duvida` inclui os
      `itens_ativos` no corpo do POST e devolve `ResultadoResposta`.
      Rodar e **ver falhar**
- [X] T012 [US1] Em `testes/unitarios/adaptadores/test_llm_gemini.py`:
      `identificar_item_vendavel` e
      `interpretar_pesquisa_saida` parseiam o JSON do contrato (prompt
      pode ser curto). Rodar e **ver falhar**

### Implementation for User Story 1

- [X] T013 [US1] Implementar POST `generateContent` compartilhado em
      `app/adaptadores/llm_gemini.py` (timeout do client, chave no
      header). Sem retry. Sem SDK. T010 começa a falar HTTP no mock
- [X] T014 [US1] Implementar `classificar` e o prompt de taxonomia F3.2
      até T010 verde. JSON parseável com valor fora da taxonomia
      **devolve** `ResultadoClassificacao` (domínio valida); não levanta
      `FalhaDeClassificacao`
- [X] T015 [US1] Implementar `extrair_ficha` e `responder_duvida` até
      T011 verde. `responder_duvida` não filtra fidelidade (isso é o
      serviço). Não chamar a porta se a tupla de itens vier vazia — quem
      não chama já é o domínio
- [X] T016 [US1] Implementar `identificar_item_vendavel` e
      `interpretar_pesquisa_saida` até T012 verde. Prompt simples
      aceitável. Falha de transporte continua a `Falha*` do método

**Checkpoint**: os cinco usos passam pelo adaptador real com cliente
falso. Regras de negócio intactas (US2 cenário de mesmo desfecho com o
mesmo `Resultado*`).

---

## Phase 5: User Story 3 - Falha, demora ou lixo não perdem a mensagem (Priority: P1)

**Goal**: Timeout, 429, 401/403, rede/5xx e corpo não-JSON viram a
`Falha*` já tratada pelo domínio, com códigos estáveis, sem prender o
worker. Primeira falha escala; sem retry contra o serviço.

**Independent Test**: `MockTransport` que levanta `httpx.TimeoutException`
→ `FalhaDeClassificacao.codigo == "llm_tempo_esgotado"` (e análogos nos
outros métodos). 429 → `llm_quota`. Corpo `"<<<"` →
`llm_formato_invalido`. Testes de domínio já existentes com
`LLMFalso.falhar_classificacao` continuam verdes (não reescrever o
encaminhamento humano).

### Tests for User Story 3

- [X] T017 [US3] Em `testes/unitarios/adaptadores/test_llm_gemini.py`:
      timeout → `llm_tempo_esgotado`; 429 → `llm_quota`; 401/403 →
      `llm_recusa`; 5xx/rede → `llm_indisponivel`; corpo não-JSON ou
      sem candidato → `llm_formato_invalido`. Códigos sem eco do texto.
      Rodar e **ver falhar** (FR-006, FR-008)
- [X] T018 [P] [US3] Integração em
      `testes/integracao/test_ia_real_aviso.py` (ou estender
      `test_classificar_mensagem.py`): worker com `LLMFalso` armado para
      `FalhaDeClassificacao` continua gravando desfecho humano e
      `concluido` — regressão, não ramo novo. Rodar; se já verde, manter
      como âncora. Não chamar Gemini

### Implementation for User Story 3

- [X] T019 [US3] Mapear exceções HTTP em `app/adaptadores/llm_gemini.py`
      até T017 verde, nos cinco métodos. Sem `time.sleep` de retry. Sem
      logar corpo

**Checkpoint**: demora e lixo não prendem a passagem; domínio reusa o
humano.

---

## Phase 6: User Story 4 - O hóspede sabe com quem fala (Priority: P1)

**Goal**: Recado de boas-vindas inclui o aviso fixo do produto (assistente
virtual + pessoa da recepção), uma vez, antes do convite. Coleta e
respostas seguintes não repetem. Sem slot novo.

**Independent Test**: `montar_texto_boas_vindas(...)` contém as duas
ideias, os três fatos, uma `?` só na última linha, sem `Silva`. Assinatura
da função inalterada. Integração: check-in + worker grava `mensagem`
com o aviso; mensagem de coleta da mesma reserva não o traz.

Pode começar em paralelo com a US2 (só `texto_boas_vindas.py`).

### Tests for User Story 4

- [X] T020 [US4] Estender
      `testes/unitarios/modulos/conversa/test_texto_boas_vindas.py`:
      o texto contém assistente virtual e pessoa da recepção; `count("?")
      == 1` e a última linha tem a interrogação; três rótulos intactos;
      `inspect.signature` sem parâmetro de aviso. Rodar e **ver falhar**
      ([contracts/aviso-assistente-virtual.md](./contracts/aviso-assistente-virtual.md),
      FR-010–FR-012)
- [X] T021 [P] [US4] Integração em
      `testes/integracao/test_ia_real_aviso.py`: após confirmar chegada
      e `--uma-passagem` (ou `processar_uma_passagem` com gateway falso),
      `mensagem.conteudo` de boas-vindas tem o aviso; a coleta da mesma
      reserva não tem. Rodar e **ver falhar** (FR-012, FR-013)

### Implementation for User Story 4

- [X] T022 [US4] Constante de produto e linha antes do convite em
      `app/modulos/conversa/texto_boas_vindas.py` até T020 verde. ASCII
      no registro do recado atual. Não tocar
      `app/modulos/conversa/texto_coleta.py`. Não acrescentar chave em
      `parametro_hotel`
- [X] T023 [US4] T021 verde sem mudar a tupla de quatro variáveis do
      WhatsApp nem `enviar_boas_vindas` da porta de mensageria

**Checkpoint**: histórico e simulador mostram o aviso na primeira
mensagem da estadia.

---

## Phase 7: User Story 5 - Chave e conversa fora do log (Priority: P2)

**Goal**: Log operacional não contém chave, prompt, texto de hóspede nem
corpo da resposta. Arquivos versionados não têm valor de chave. Exceção
de config não interpola o segredo.

**Independent Test**: `caplog` em `classificar` com texto marcado e chave
`"secret-test-key"`: o log tem codigo/ids, não tem o texto nem a chave.
`ConfiguracaoDeInteligenciaInvalida` com modo lixo menciona o modo, não
uma chave. `.env.example` tem `GEMINI_API_KEY=` vazio.

### Tests for User Story 5

- [X] T024 [US5] Em `testes/unitarios/adaptadores/test_llm_gemini.py` (ou
      arquivo `test_log_llm.py`): sucesso e falha 429 com `caplog` —
      ausência da chave, do texto do hóspede e do JSON de resposta.
      Rodar e **ver falhar** se hoje logar demais
      ([contracts/logs-e-segredo.md](./contracts/logs-e-segredo.md),
      FR-015, FR-017)
- [X] T025 [P] [US5] Unitário em
      `testes/unitarios/adaptadores/test_fabrica_llm.py`: mensagem de
      `ConfiguracaoDeInteligenciaInvalida` para `real` sem chave não
      contém o valor da chave (código `chave_ausente` ou equivalente).
      Rodar e **ver falhar**

### Implementation for User Story 5

- [X] T026 [US5] Ajustar logs em `app/adaptadores/llm_gemini.py` e
      `app/adaptadores/fabrica_llm.py` até T024 e T025 verdes: só modo,
      classe, ids, codigo. Nunca `extra` com prompt

**Checkpoint**: US5 observável sem rede.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: regressão da suíte, quickstart, honestidade no estado do
projeto. Sem tela nova. Sem migração.

- [X] T027 [P] Confirmar que
      `testes/unitarios/modulos/conversa/test_texto_coleta.py` (e demais
      recados) **não** ganharam o aviso. Corrigir só se alguma tarefa
      tiver espalhado a constante
- [X] T028 [P] Varredura em `testes/unitarios/adaptadores/test_fabrica_llm.py`
      ou teste de árvore: `.env.example` lista nomes sem valor; nenhum
      arquivo versionado (exceto docs de contrato que citam o **nome**)
      contém chave Gemini típica
- [X] T029 Rodar `pytest testes/unitarios -q` e a integração
      `-k "ia_real_aviso or classificar or responder_duvida or interpretar_ficha or boas_vindas or cli_worker"`;
      corrigir mocks de config que ainda omitam `llm_modo` em
      `testes/unitarios/worker/test_cli_worker.py`
- [X] T030 Percorrer [quickstart.md](./quickstart.md) (fábrica, recusa de
      subida, aviso no recado, caplog). Atualizar
      `docs/00-ESTADO-DO-PROJETO.md`: F7.1 + aviso feitos; worker usa
      fábrica; suíte sem rede. Sem commit nesta tarefa

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: imediata
- **Foundational (Phase 2)**: depende do Setup — só `config.py`
- **US2 (Phase 3)**: depende da Foundational — bloqueia US1 e US3
- **US4 (Phase 6)**: depende da Foundational — **não** da US2; pode
  paralelo com a US2
- **US1 (Phase 4)**: depende da US2 (`LLMGemini` + fábrica)
- **US3 (Phase 5)**: depende da US1 (POST compartilhado)
- **US5 (Phase 7)**: depende da US2; melhor depois da US1/US3 (há POST
  para `caplog`)
- **Polish (Phase 8)**: depois das histórias desejadas

### User Story Dependencies

- **US2**: depois da Foundational
- **US4**: depois da Foundational; paralela à US2
- **US1**: depois da US2
- **US3**: depois da US1
- **US5**: depois da US2; caplog completo depois da US3

### Within Each User Story

- Testes primeiro; **ver falhar** pelo motivo certo
- Esqueleto da classe antes do POST
- Transporte antes dos prompts
- Códigos de falha depois do caminho feliz
- Sem `conversa.service` importar adaptador

### Parallel Opportunities

- T001 e T002
- T005 e T006 (arquivos distintos) depois de T004 escrito
- T010–T012 e T014–T016 são sequenciais no mesmo
  `test_llm_gemini.py` / `llm_gemini.py`
- US4 (T020–T023) em paralelo com US2
- T027 e T028 no polish

---

## Parallel Example: depois da Foundational

```text
# Agente A — US2
Task: T004 testes da fábrica em testes/unitarios/adaptadores/test_fabrica_llm.py
Task: T007 esqueleto em app/adaptadores/llm_gemini.py
Task: T008 fábrica em app/adaptadores/fabrica_llm.py
Task: T009 worker/consumidor.py e worker/__main__.py

# Agente B — US4 (aviso)
Task: T020 testes em testes/unitarios/modulos/conversa/test_texto_boas_vindas.py
Task: T022 constante em app/modulos/conversa/texto_boas_vindas.py
```

---

## Implementation Strategy

### MVP First (US2 + US1)

1. Setup + Foundational (`config.py`)
2. US2: fábrica e worker deixam o controlado oculto
3. US1: três prompts da demonstração (classificar, responder, ficha) +
   os dois restantes no mesmo adaptador
4. **STOP and VALIDATE**: `pytest testes/unitarios/adaptadores -q`
5. US4 (aviso) pode ter saído em paralelo no passo 2

### Incremental Delivery

1. Foundational + US2 → ambiente não sobe no escuro
2. US1 → a demonstração deixa de cair sempre em humano (com
   `LLM_MODO=real` no `.env` local, fora da suíte)
3. US3 → timeout/quota não prendem o worker
4. US4 → hóspede lê o aviso no simulador
5. US5 → caplog limpo

### Prioridade se o dia apertar

Classificar, responder e extrair ficha (T010–T015) primeiro.
Identificar item e pesquisa (T012/T016) em seguida, prompt simples.
Não deixar esses dois no `LLMFalso` com `LLM_MODO=real`.

---

## Notes

- `[P]` só quando os arquivos não colidem. Vários testes no mesmo
  `test_llm_gemini.py` são sequenciais para um agente
- Porta `LLMProvider` **não** ganha método
- `processar_uma_passagem(..., llm=)` na suíte continua injetando
  `LLMFalso` armado — não passar pela recusa de subida
- Template Meta `boas_vindas` não se republica nesta fatia (Artigo XV)
- Commit só se o usuário pedir
