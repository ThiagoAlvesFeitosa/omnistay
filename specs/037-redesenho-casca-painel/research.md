# Research: Redesenho da casca do painel e apresentação

## 1. Nome da casa na sessão, sem tabela nova

**Decisão**: `POST /sessoes` e `GET /sessoes/atual` passam a incluir
`nome_hotel`. O valor vem de `hotel.nome` da propriedade ligada ao
`id_hotel` da sessão. `acesso` **não** lê a tabela `hotel`: chama
`propriedade.service.ler_nome_hotel(conexao, id_hotel)`. Sem coluna
nova, sem Alembic, sem `id_hotel` no JSON da casca.

**Rationale**: a lista de ajustes e a FR-007 pedem o nome no
cabeçalho sem consulta extra inventada. O nome já existe no cadastro
(F0). Artigo XIV: o hotel é o da sessão. Artigo XI: GET de
propriedade só para o nome duplicaria ida e exigiria operação nova.

O `GET /sessoes/atual` ganha `Conexao` no roteador (hoje só recebe a
sessão já resolvida). O `POST` já tem conexão. Import local de
`propriedade.service` — o mesmo padrão de
`duracao_da_sessao_em_horas`, para não ciclar com o bootstrap.

**Alternativas recusadas**:

- **JOIN em `acesso.repository`**: o módulo de acesso leria tabela
  que não governa. Recusado.
- **Segundo fetch no browser** (`GET /propriedade`): a spec exige o
  nome já na entrada e na sessão corrente.
- **Coluna `nome_hotel` em `sessao`**: desnormaliza e envelhece se o
  cadastro mudar. Recusado.
- **Devolver `id_hotel` à casca**: a casca não escolhe hotel e não
  precisa do identificador.

---

## 2. Menu por viewport, não por perfil “compacto”

**Decisão**: some o atalho atual em que `staff` **não vê navegação**.
Largo (≥ 768 px, Tailwind `md`): coluna permanente ~240 px, fundo
escuro, altura inteira. Estreito: botão abre overlay; fecha pelo
mesmo botão, pelo fundo, por destino ou Sair (FR-002a). Equipe,
recepção e gestão usam o mesmo chrome; o que muda é o mapa de
destinos.

**Rationale**: a US3 pede menu no celular da equipe, não a ausência
de menu. O `compacto` de hoje resolveu telefone escondendo os
destinos — com um item só isso quebrava menos, mas a identidade
(casa, marca, Equipe, Sair) precisa caber no overlay. 768 px é o
corte “telefone ou janela equivalente” da spec; pixel exato ficou
fora do clarify e não vai para `parametro_hotel` (não é prazo
operacional — Artigo XIII).

**Alternativas recusadas**:

- **Manter compacto = sem menu para staff**: contradiz US3.
- **Corte `lg` (1024)**: o critério de sucesso é celular, não
  tablet. Janela de recepção redimensionada já é o caso de borda da
  spec (mesmo overlay).
- **Biblioteca de drawer**: Artigo XI. Overlay com estado
  `menuAberto` e classes Tailwind basta.

---

## 3. Grupos no mapa de destinos; Nova reserva fora do menu

**Decisão**: cada destino ganha `grupo` (`operacao` | `propriedade` |
`gestao`) ou fica fora de grupo (Simulador, no fim). `reserva`
permanece no mapa **só para a rota** `/app/reserva`; `itensMenu` não
o devolve. O botão na fila do dia continua o caminho de cadastrar.
Grupo sem item visível ao perfil não renderiza o rótulo.

Composição (já na spec):

| Grupo | Recepção | Gestão | Equipe |
| --- | --- | --- | --- |
| Operação | fila, Estadia, chamados e pedidos, consumos, saída | — | meus chamados |
| Propriedade | catálogo, vendáveis, recado | os três | — |
| Gestão | — | painel, mercado, usuários, retenção | — |
| (fim) | Simulador | Simulador | — |

Rótulos de perfil na casca: **Recepção**, **Gestão**, **Equipe**
(valores de `usuario.perfil` intactos: `recepcao` · `gestor` ·
`staff`).

**Rationale**: a lista de ajustes e a clarificação “só Nova reserva
é ação”. Estadia e Saída sem `id` na rota já têm estado vazio (F7.6 /
F8.5). Artigo XI: não persistir menu no banco.

**Alternativas recusadas**:

- **Tirar Estadia/Saída do menu**: recusado na specify.
- **Terceiro grupo “Simulador” com rótulo**: a spec manda separado
  no fim, sem ser um dos três.

---

## 4. Uma regra de apresentação, `Intl` nativo

**Decisão**: módulo `frontend/src/painel/apresentacao.ts` (teste de
unidade próprio). Sem pacote novo.

| Função | Exemplo |
| --- | --- |
| `formatarMoeda` | `R$ 9,00` |
| `formatarDataCalendario` | `02/09/2026` (ISO `YYYY-MM-DD` sem fuso) |
| `formatarInstante` | `02/09/2026 14:32` (hora:minuto, fuso local da tela) |
| `formatarInstanteComDecorrido` | `02/09/2026 14:32 · há 8 min` |
| `formatarHorarioBolha` | `14:32` no mesmo dia de calendário local; senão instante completo |

`tempoDecorrido` permanece; as listas de chamado e consumo passam a
combiná-lo com o instante. `formatarPreco` de vendáveis **delega** a
`formatarMoeda` (os testes que esperam `9.00` mudam). Telas que hoje
fazem `R$ {valor}` cru param de prefixar à mão.

Data de calendário incompleta: devolve vazio utilizável, não inventa
dia. Instante sem relógio parseável: cai na data de calendário, não
em `00:00`. Campo `type="date"` nativo intocado.

**Rationale**: a spec pede uma regra compartilhada. `Intl` já está no
runtime. Fuso = o que o painel já usa (`Date` local), como na
assumption do clarify.

**Alternativas recusadas**:

- **date-fns / dayjs / luxon**: Artigo XI.
- **Formatar no backend**: cada JSON mudaria; a leitura é da tela.
- **Relativo no lugar do instante** nas listas: recusado no clarify.

---

## 5. Bolhas compartilhadas; Enter só no simulador

**Decisão**: componente `BolhaConversa` (dois lados: hóspede × hotel).
Simulador: `direcao === "recebida"` = hóspede. Estadia: `origem ===
"hospede"` = hóspede; `recepcao` e `automatico` = hotel, com o rótulo
de origem já da F7.6. Horário via `formatarHorarioBolha` no campo
`enviada_em` (simulador) ou `em` (Estadia). Sem relativo na bolha.

Simulador perde a serifa `Georgia` e o CSS inline da página; passa a
Tailwind da casca. Lista de conversas em cartão. Enter envia;
Shift+Enter quebra linha. Estadia **não** unifica o atalho (F7.6).

**Rationale**: clarify Q2+Q3. Dois visuais de fio quebram o balcão.
Terceiro estilo de balão repetiria o rótulo. Componente único evita
duas regras de horário.

**Alternativas recusadas**:

- **Só o simulador ganha balão**: recusado no clarify.
- **Três cores de origem**: recusado no clarify.
- **Enter na Estadia**: já recusado na F7.6.

---

## 6. Teste primeiro, sem Playwright

**Decisão**: pytest no JSON da sessão (nome da casa certa, nunca da
outra propriedade; regressão das rotas de sessão). Vitest na casca
(grupos, ausência de Nova reserva no menu, rótulos, overlay), em
`apresentacao.ts`, no simulador (Enter, balões, horário) e na Estadia
(dois lados + rótulo). Telas que já assertam `9.00` / `2026-09-01` /
só `há 3 h` passam a esperar a grafia nova **no mesmo cenário**.

`matchMedia` (ou classe/estado `estreita`) no teste do overlay —
jsdom não é viewport real. Relógio da bolha e do decorrido:
`agora` injetável, como a F2.2.

**Rationale**: Artigo XII. Playwright foi recusado na F8.1 e continua
fora (Artigo XI).

**Alternativas recusadas**:

- **Screenshot / Cypress**: fora da stack.
- **Teste que chama a API de verdade no Vitest**: a casca já usa
  `fetch` falso.
