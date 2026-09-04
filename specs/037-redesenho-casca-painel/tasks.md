---
description: "Lista de tarefas para implementação da fatia"
---

# Tarefas: F8 Redesenho da casca do painel e apresentação

**Input**: documentos em `specs/037-redesenho-casca-painel/`
**Pré-requisitos**: [plan.md](./plan.md), [spec.md](./spec.md),
[research.md](./research.md), [data-model.md](./data-model.md),
[contracts/](./contracts/), [quickstart.md](./quickstart.md)

**TDD (obrigatório)**: nenhuma linha de produção antes de um teste que
falhe pela ausência dela. Em cada tarefa de teste: escrever, rodar,
**ver falhar pelo motivo certo**. Só então a implementação. Um teste
que passa de primeira é suspeito.

**pytest**: `uv run pytest testes/unitarios -q` no ciclo;
`uv run pytest -k nome` para um só.
**Vitest**: `npm --prefix frontend test -- --run`. Sem Playwright.

**Duas guardas (não negociar):**

1. **`acesso` não lê `hotel`.** `nome_hotel` vem de
   `propriedade.service.ler_nome_hotel`. Sem JOIN no repositório de
   sessão. Sem Alembic. Sem `id_hotel` no JSON da casca. Sem operação
   nova na matriz.
2. **Dois lados de bolha, Enter só no simulador.** Estadia reusa o
   rótulo de origem da F7.6 (sem terceiro estilo). Enter na Estadia
   continua bloqueado. Listas de chamado/consumo: instante **e**
   decorrido (`02/09/2026 14:32 · há 8 min`). Telas **não** prefixam
   `R$` em cima de `formatarMoeda`. Input de preço e `type="date"`
   nativos permanecem como estão.

**Organização**: fases por história (US1–US5). Setup e Foundational
não levam rótulo de história.

## Format: `[ID] [P?] [USx?] Descrição`

- **[P]**: paralelizable (arquivos diferentes, sem dependência incompleta)
- **[USn]**: história correspondente
- Caminho de arquivo em cada tarefa

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: os mocks da casca já carregam `nome_hotel`, para a US1
não quebrar o `fetch` falso quando a sessão passar a tipar o campo.

- [X] T001 [P] Incluir `nome_hotel` (string) no JSON falso de
  `GET /sessoes/atual` e `POST /sessoes` em
  `frontend/src/painel/Casca.test.tsx` (e em
  `frontend/src/painel/TelaEntrada.test.tsx` se o corpo 201 estiver
  literal). **Não** afirmar o nome na tela ainda. Rodar
  `npm --prefix frontend test -- --run src/painel/Casca.test.tsx` e
  ver o teste **passar**.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: nome da casa na sessão, tipos no frontend, regra de
apresentação compartilhada. **Nenhuma história começa antes desta
fase terminar.**

**Checkpoint**: POST/GET de sessão devolvem `nome_hotel` da casa
certa; `apresentacao.ts` formata moeda, calendário, instante, bolha
e instante+decorrido; Vitest da regra verde.

- [X] T002 [P] Escrever
  `testes/unitarios/modulos/propriedade/test_ler_nome_hotel.py`:
  repositório falso; `ler_nome_hotel(conexao, id_hotel)` devolve o
  `nome` daquele hotel; hotel inexistente devolve `""`; **não**
  devolve telefone. Rodar
  `uv run pytest testes/unitarios/modulos/propriedade/test_ler_nome_hotel.py -q`
  e **ver falhar**.

- [X] T003 Implementar `ler_nome_hotel` em
  `app/modulos/propriedade/repository.py` e
  `app/modulos/propriedade/service.py` (serviço chama o repositório;
  `id_hotel` na consulta). Rodar T002 até ficar **verde**.

- [X] T004 [P] Estender `testes/integracao/test_autenticacao.py`:
  `POST /sessoes` 201 e `GET /sessoes/atual` 200 incluem
  `nome_hotel` igual ao nome da propriedade A; **não** incluem
  `id_hotel`; login na propriedade B não devolve o nome da A; 401
  de credencial **não** traz o campo. Rodar e **ver falhar**.

- [X] T005 Acrescentar `nome_hotel` em `SessaoCriada` e
  `SessaoAtualResposta` em `app/modulos/acesso/schema.py`. No
  `app/modulos/acesso/router.py`, POST e GET atual preenchem o
  campo via import local de `propriedade.service.ler_nome_hotel`;
  GET atual passa a receber `Conexao`. **Não** consultar `hotel` no
  repositório de acesso. Rodar T004 até ficar **verde**.

- [X] T006 [P] Estender `frontend/src/painel/sessao.ts` e
  `frontend/src/painel/sessao.test.ts`: tipos `SessaoCriada` e
  `SessaoAtual` com `nome_hotel`; os JSON falsos dos testes de
  sessão incluem o campo. Rodar
  `npm --prefix frontend test -- --run src/painel/sessao.test.ts`
  até ficar **verde**.

- [X] T007 [P] Escrever `frontend/src/painel/apresentacao.test.ts`:
  `formatarMoeda(9)` → `R$ 9,00`; zero → `R$ 0,00`; milhar;
  `formatarDataCalendario("2026-09-02")` → `02/09/2026`; ilegível
  não inventa dia; `formatarInstante` → `02/09/2026 14:32` (sem
  segundos) com `agora`/instante de parede conhecido (sem depender
  do fuso da máquina: documentar o instante no teste);
  `formatarInstanteComDecorrido` no espírito
  `02/09/2026 14:32 · há 8 min` reusando `tempoDecorrido`;
  `formatarHorarioBolha` no mesmo dia de calendário → só `14:32`;
  noutro dia → data e hora; bolha **sem** “há”. Rodar
  `npm --prefix frontend test -- --run src/painel/apresentacao.test.ts`
  e **ver falhar**.

- [X] T008 Implementar `frontend/src/painel/apresentacao.ts`.
  Reusar `tempoDecorrido` de `frontend/src/painel/solicitacoes.ts`.
  Sem pacote novo (`Intl` nativo). Rodar T007 até ficar **verde**.

**Checkpoint**: backend e regra de grafia prontos; a casca ainda é
a faixa superior.

---

## Phase 3: User Story 1 - A casca identifica a casa e a pessoa (Priority: P1) 🎯 MVP

**Goal**: navegação permanente em tela larga com nome da casa,
OmniStay discreto, e no rodapé nome + rótulo do perfil (Recepção /
Gestão / Equipe) + Sair. Sessão já traz o nome (Foundational).

**Independent Test**: autenticar cada perfil; conferir nome da casa
no topo da navegação, marca OmniStay abaixo, rodapé com pessoa,
rótulo e Sair; POST e GET já testados no Foundational.

### Tests (escrever e ver falhar)

- [X] T009 [US1] Estender `frontend/src/painel/Casca.test.tsx`:
  recepção vê o `nome_hotel` do mock em destaque, o texto
  **OmniStay**, o nome da pessoa, o rótulo **Recepção** e **Sair**;
  gestão vê **Gestão**; staff vê **Equipe** (não `staff`);
  `id_hotel` não aparece. Menu ainda pode ser a lista plana. Rodar
  e **ver falhar**.

### Implementation

- [X] T010 [US1] Redesenhar o chrome autenticado em
  `frontend/src/painel/Casca.tsx`: coluna ~240 px, fundo escuro,
  altura inteira em tela larga; topo = nome da casa; abaixo =
  OmniStay discreto; rodapé = nome + rótulo + Sair. Rótulos em
  `frontend/src/painel/destinos.ts` (`recepcao`→Recepção,
  `gestor`→Gestão, `staff`→Equipe). Tirar o nome solto da faixa
  superior. Lista de destinos ainda pode ser plana (`itensMenu`).
  Rodar T009 até ficar **verde**.

**Checkpoint**: os três papéis identificam casa, produto, pessoa e
perfil. Menu ainda não está agrupado.

---

## Phase 4: User Story 2 - Navegar por área, sem ação no menu (Priority: P1)

**Goal**: destinos agrupados (Operação, Propriedade, Gestão);
Simulador no fim sem rótulo de grupo; **Nova reserva** fora do
menu; botão na fila intacto; grupo vazio some.

**Independent Test**: recepção sem Nova reserva no menu e com o
botão na fila; gestão sem Operação; equipe só Operação / meus
chamados.

### Tests (escrever e ver falhar)

- [X] T011 [P] [US2] Estender `frontend/src/painel/destinos.test.ts`:
  `itensMenu("recepcao")` **não** inclui `reserva`; destino
  `reserva` permanece no mapa (rota); grupos da recepção =
  Operação (fila, Estadia, alertas, consumos, saída) e Propriedade
  (catálogo, vendáveis, recado) + simulador no fim; gestão sem
  grupo Operação; equipe só Operação / chamados; grupo sem item
  não entra na árvore. Rodar e **ver falhar**.

- [X] T012 [P] [US2] Estender `frontend/src/painel/Casca.test.tsx`:
  recepção vê rótulos **Operação** e **Propriedade**, vê Simulador,
  **não** vê link **Nova reserva** no `nav`; gestão vê Propriedade
  e Gestão, não vê Fila; equipe não vê Simulador. Rodar e **ver
  falhar**.

### Implementation

- [X] T013 [US2] Acrescentar `grupo` e `noMenu` em
  `frontend/src/painel/destinos.ts`; `itensMenu` ignora `reserva`;
  função de agrupamento que omite grupo vazio. Path `/app/reserva`
  intacto. Rodar T011 até ficar **verde**.

- [X] T014 [US2] Renderizar grupos e Simulador no fim em
  `frontend/src/painel/Casca.tsx`. Rodar T012 até ficar **verde**.
  Confirmar `frontend/src/painel/TelaFila.test.tsx` ainda acha o
  botão/link **Nova reserva** na fila.

**Checkpoint**: menu por área; cadastrar reserva só pela fila.

---

## Phase 5: User Story 3 - A equipe usa o painel no celular (Priority: P1)

**Goal**: abaixo de 768 px a navegação é overlay: abre por botão;
fecha pelo mesmo botão, pelo fundo, por destino ou Sair. Some o
`compacto` que escondia o menu da equipe.

**Independent Test**: sessão staff em viewport estreito (matchMedia
falso); trabalho visível; overlay abre e fecha sem mudar a rota.

### Tests (escrever e ver falhar)

- [X] T015 [US3] Estender `frontend/src/painel/Casca.test.tsx`:
  mock de `matchMedia('(min-width: 768px)')` com `matches: false`;
  equipe em `/app/chamados` vê o heading da lista **sem** coluna
  permanente; controle abre o overlay com casa, OmniStay, Equipe,
  Sair e Meus chamados; segundo clique no controle fecha e a rota
  permanece; toque no fundo (área de trabalho / backdrop) fecha sem
  navegar; Sair fecha e vai à entrada. Com `matches: true`,
  recepção **não** precisa do botão. Rodar e **ver falhar**.

### Implementation

- [X] T016 [US3] Overlay em `frontend/src/painel/Casca.tsx` (estado
  `menuAberto`); classes Tailwind `md:` para coluna permanente.
  Remover o ramo `compacto` que omitia `<nav>` do staff. Fechar no
  botão, no fundo, em `NavLink` e em Sair. Rodar T015 até ficar
  **verde**.

**Checkpoint**: SC-002 — um gesto fecha o menu no telefone.

---

## Phase 6: User Story 4 - O simulador parece conversa e envia com Enter (Priority: P1)

**Goal**: simulador com tipografia da casca, cartões, dois lados de
bolha, horário (hoje / outro dia), Enter envia e Shift+Enter quebra
linha. Estadia: os mesmos dois lados + rótulo de origem; Enter
**não** envia.

**Independent Test**: Vitest do simulador (Enter, balões, hora) e
da Estadia (dois lados, rótulos, data noutro dia, Enter inerte).

### Tests (escrever e ver falhar)

- [X] T017 [P] [US4] Criar `frontend/src/TelaSimulacao.test.tsx`
  (ou `frontend/src/painel/` se o arquivo da tela for movido):
  tipografia **não** é Georgia/serif exclusiva; lista em cartão;
  mensagem `recebida` e `enviada` em lados distintos; `enviada_em`
  de hoje → só hora; de outro dia → data e hora; Enter no campo
  dispara o mesmo envio do botão; Shift+Enter não envia; campo
  vazio + Enter não inventa POST. Rodar e **ver falhar**.

- [X] T018 [P] [US4] Estender `frontend/src/painel/TelaEstadia.test.tsx`:
  hóspede num lado; automático e recepção no lado do hotel; rótulos
  Hóspede / Automático / Recepção visíveis; `em` de outro dia mostra
  data e hora; Enter no textarea **não** chama POST (já existe
  `impedirEnter` — o teste novo trava regressão). Rodar e **ver
  falhar**.

### Implementation

- [X] T019 [US4] Criar `frontend/src/painel/BolhaConversa.tsx` (dois
  lados + `formatarHorarioBolha`). Rodar T017/T018 ainda podem
  falhar na tela.

- [X] T020 [US4] Reescrever `frontend/src/TelaSimulacao.tsx`: Tailwind
  da casca, sem `Georgia`; cartões; `BolhaConversa`; onKeyDown Enter /
  Shift+Enter. Rodar T017 até ficar **verde**.

- [X] T021 [US4] Usar `BolhaConversa` em
  `frontend/src/painel/TelaEstadia.tsx` mantendo rótulo de origem e
  entrega da F7.6. **Não** unificar Enter. Rodar T018 até ficar
  **verde**.

**Checkpoint**: vídeo e balcão compartilham o fio; atalhos
permanecem distintos.

---

## Phase 7: User Story 5 - Moeda e data no padrão brasileiro (Priority: P1)

**Goal**: valores lidos em `R$ 0,00`; calendário `02/09/2026`;
instante operacional completo; chamados/consumos com instante ·
decorrido. `type="date"` intacto. Funções já existem no
Foundational — esta fase **aplica** e atualiza expectativas.

**Independent Test**: amostragem das telas listadas +
`apresentacao.test.ts` (já verde).

### Tests (escrever e ver falhar)

- [X] T022 [P] [US5] Estender `frontend/src/painel/vendaveis.test.ts`:
  valor **lido** `formatarPreco(9)` → `R$ 9,00` (delega a
  `formatarMoeda`). Rodar e **ver falhar**.

- [X] T023 [P] [US5] Estender
  `frontend/src/painel/TelaAlertas.test.tsx`,
  `frontend/src/painel/TelaChamados.test.tsx` e
  `frontend/src/painel/TelaConsumos.test.tsx`: o texto visível traz
  instante **e** decorrido (usar
  `formatarInstanteComDecorrido(aberta_em, agora)` na asserção);
  “há 3 h” sozinho não basta; consumo lido usa `formatarMoeda`
  (não `R$ 32.00`). Rodar e **ver falhar**.

- [X] T024 [P] [US5] Estender `frontend/src/painel/TelaFila.test.tsx`
  (`2026-08-31` lido → `31/08/2026`);
  `frontend/src/painel/TelaMercado.test.tsx` e
  `frontend/src/painel/TelaRetencao.test.tsx` (sem `2026-09-01` cru;
  instante completo); `frontend/src/painel/TelaPainel.test.tsx`
  (`132.00` / `0.00` → `R$ 132,00` / `R$ 0,00`). Rodar e **ver
  falhar**.

- [X] T025 [P] [US5] Estender
  `frontend/src/painel/TelaNovaReserva.test.tsx`: os campos Entrada
  e Saída continuam `type="date"` (não quebrar o valor interno).
  Rodar — este pode **passar** de primeira se já for nativo;
  nesse caso não mudar produção.

### Implementation

- [X] T026 [US5] `formatarPreco` em `frontend/src/painel/vendaveis.ts`
  delega a `formatarMoeda` **só na leitura** (tabela/cartão). Input
  de edição em `frontend/src/painel/TelaVendaveis.tsx` **não** recebe
  `R$` — continua o número digitável. Rodar T022 e o teste da tela
  de vendáveis até ficarem **verdes**.

- [X] T027 [US5] Aplicar
  `formatarInstanteComDecorrido` e `formatarMoeda` em
  `frontend/src/painel/TelaAlertas.tsx`,
  `frontend/src/painel/TelaChamados.tsx` e
  `frontend/src/painel/TelaConsumos.tsx` (remover prefixo `R$`
  manual). Rodar T023 até ficar **verde**.

- [X] T028 [US5] Aplicar `formatarDataCalendario` /
  `formatarInstante` / `formatarMoeda` em
  `frontend/src/painel/TelaFila.tsx`,
  `frontend/src/painel/TelaMercado.tsx` (apagar `dataVisivel` ISO),
  `frontend/src/painel/TelaRetencao.tsx`,
  `frontend/src/painel/TelaPainel.tsx` e
  `frontend/src/painel/ficha.ts` (`formatarDataVisivel` delega).
  Rodar T024 até ficar **verde**. Confirmar T025 ainda verde.

**Checkpoint**: SC-006 — nenhuma leitura em `0.00` ou `2026-09-02`.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T029 Verificar que nenhum `console.log` em
  `frontend/src/TelaSimulacao.tsx` e
  `frontend/src/painel/TelaEstadia.tsx` imprime `conteudo`/texto.
  Logs de sessão em `app/modulos/acesso/` continuam sem senha e sem
  `nome_hotel` como evento novo.

- [X] T030 [P] Conferir que `app/modulos/acesso/politica.py` e
  `alembic/versions/` **não** ganharam revisão nem operação nesta
  fatia. Worker intocado.

- [X] T031 Rodar `uv run pytest testes/unitarios/modulos/acesso
  testes/unitarios/modulos/propriedade/test_ler_nome_hotel.py
  testes/integracao/test_autenticacao.py -q` e
  `npm --prefix frontend test -- --run`. Corrigir regressão de
  mock em `Casca.test.tsx` (toda tela autenticada ainda precisa
  dos GETs já falsos).

- [X] T032 Percorrer [quickstart.md](./quickstart.md) (JSON da
  sessão, casca larga/estreita, simulador, grafia) e anotar
  divergência na spec se o código tiver revelado erro de
  documentação — não contornar em silêncio.

**Checkpoint**: suíte do painel verde; contratos da 037 cumpridos.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: começa já
- **Foundational (Phase 2)**: depende do Setup; **bloqueia** US1–US5
- **US1 → US2 → US3**: mesma `Casca.tsx` — **sequenciais** (não
  paralelizar entre pessoas sem conflito)
- **US4**: depois do Foundational (`apresentacao.ts`); pode seguir
  US1 se a casca já autenticar; não depende de grupos
- **US5**: depois do Foundational; pode em paralelo com US2–US4
  (arquivos de tela diferentes da casca, salvo conflitos pontuais)
- **Polish**: depois das histórias desejadas

### User Story Dependencies

- **US1**: Foundational (nome na sessão)
- **US2**: US1 (chrome já é lateral)
- **US3**: US1 (overlay reusa a mesma identidade); melhor depois
  da US2 para o overlay já mostrar grupos
- **US4**: Foundational (horário da bolha)
- **US5**: Foundational (funções); independente da casca

### Within Each User Story

- Teste → ver falhar → implementação mínima → verde
- Não unificar Enter no “refatorar a conversa”

### Parallel Opportunities

```text
T002 || T007          (depois T001)
T004 depois T003
T011 || T012          (US2 testes)
T017 || T018          (US4 testes)
T022 || T023 || T024 || T025   (US5 testes)
T029 || T030
```

US4 e US5 em paralelo **depois** do Foundational, se US1–US3
estiverem com a casca estável.

---

## Parallel Example: User Story 5

```bash
# Testes de grafia juntos (arquivos diferentes):
Task: vendaveis.test.ts
Task: TelaAlertas.test.tsx + TelaChamados.test.tsx + TelaConsumos.test.tsx
Task: TelaFila.test.tsx + TelaMercado.test.tsx + TelaRetencao.test.tsx + TelaPainel.test.tsx
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Setup T001
2. Foundational T002–T008 (nome da casa + `apresentacao.ts`)
3. US1 T009–T010
4. **STOP**: três perfis identificam casa e papel na lateral

A grafia e o simulador ainda denunciam protótipo — o vídeo da
casca já mostra identidade.

### Incremental Delivery

1. Foundational → sessão e regra de data/moeda
2. US1 → identidade (MVP visual)
3. US2 → menu por área
4. US3 → celular da equipe
5. US4 → simulador + Estadia
6. US5 → grafia em todas as telas
7. Polish → suíte completa

### Parallel Team Strategy

Um desenvolvedor: ordem US1→US2→US3, com US5 intercalada nas
telas depois de T008. Dois: um na casca (US1–US3), outro em
US4+US5 após o Foundational.

---

## Notes

- [P] = arquivos diferentes, sem esperar tarefa incompleta no
  mesmo arquivo
- Casca.tsx é o ponto de conflito US1/US2/US3 — não marcar [P]
  entre essas implementações
- Input `type="date"` e campo de preço digitável não usam a grafia
  de **leitura**
- Relógio dos testes de instante: `agora` fixo +
  `formatarInstante*` na asserção, para não flakar no fuso
- Commit ao fim de cada história (quando o usuário pedir)
