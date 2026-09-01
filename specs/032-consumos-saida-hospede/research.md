# Fase 0 — Pesquisa e decisões técnicas: consumos a lançar e saída

Cada seção registra a decisão, por que ela foi tomada e o que foi recusado.
Divergências documentais estão na última seção.

---

## 1. Nenhuma rota nova; seis operações já entregues

**Decisão**: as telas consomem só o que já existe:

| Ação na tela | Rota existente | Operação |
| --- | --- | --- |
| Ver pendentes de lançamento | `GET /consumos/pendentes` | `ler_solicitacao_atribuida` |
| Marcar lançado | `POST /solicitacoes/{id}/lancamento` | `lancar_consumo` |
| Dispensar | `POST /solicitacoes/{id}/dispensa` | `lancar_consumo` |
| Pedidos feitos pelo chat | `GET /reservas/{id}/pedidos-feitos-pelo-chat` | `ler_pedidos_feitos_pelo_chat` |
| Confirmar saída | `POST /reservas/{id}/saida` | `confirmar_fase_da_reserva` |
| Nome e status da estadia | `GET /reservas/{id}/ficha` | `ler_dado_cadastral_de_hospede` |
| Datas + destaque vencida | `GET /fila-do-dia` | `ler_fila_do_dia` |
| Chegar à ficha (lista financeira) | navega para `/app/ficha/{id}` | já F8.3 |

Zero operação nova na matriz. Zero revisão Alembic. Cookie
`omnistay_sessao` via `pedirAutenticado`. A tela **não** envia
`id_hotel`. Proxy Vite já cobre `/consumos` e `/reservas`.

**Rationale**: spec reusa F3.7, F4.1, F4.2, F8.2 e F8.3. Artigo XI.
Clarificações: lista sem nome; sem status por item (a consulta
cobrável não o traz); esta fase não altera backend.

**Alternativas consideradas**:

- **Campo `nome` em `GET /consumos/pendentes`**: a consulta é a
  mesma que equipe e gestão leem (`ler_solicitacao_atribuida`).
  Recusado na clarificação.
- **`status_lancamento` em pedidos-feitos-pelo-chat**: útil na
  recepção, mas é extensão da consulta. Recusado nesta fase;
  fica para depois da semana.
- **`GET /reservas/{id}` resumo**: rota nova. Recusado. Nome vem
  da ficha; datas, da fila quando a reserva ainda está nela.
- **WebSocket / recarga periódica**: sem peça nova. Recarregar,
  “tentar de novo” e o GET depois do POST bastam (Artigo IV).

---

## 2. Duas telas novas; acréscimo na fila do dia

**Decisão**:

| Destino F8.1 | Componente | Perfil |
| --- | --- | --- |
| `/app/consumos` | `TelaConsumos` | recepção |
| `/app/saida/:idReserva?` | `TelaSaida` | recepção |
| `/app/fila` | `TelaFila` (acréscimo) | recepção |

Funções puras em `frontend/src/painel/consumos.ts`: tipo do item
pendente, `totalPendente`, tempo do mais antigo, `pendentesDaEstadia`
(só para o **aviso** na saída — **não** para filtrar a tela
Consumos a lançar). Tempo decorrido **reusa** `tempoDecorrido` de
`solicitacoes.ts`. Sem Redux, sem React Query.

`destinoPorCaminho` trata `/app/saida` e `/app/saida/12` como o
destino `saida`, no mesmo padrão da ficha.

Gestão e staff continuam redirecionados — **zero** fetch destas
rotas.

**Rationale**: superfícies distintas (fila da casa × checkout de
uma reserva). Clarificação: o aviso abre a fila da casa, não um
recorte.

**Alternativas consideradas**:

- **Um componente só**: mistura lançar com confirmar saída.
  Rejeitado.
- **Filtrar Consumos a lançar pela estadia** ao vir do aviso:
  recusado na clarificação. A tela do menu e a do aviso são a
  mesma fila da casa.
- **Checkout na própria fila** (um clique): recusado na
  clarificação.

---

## 3. Ver ficha e Saída são links; lançar, dispensar e confirmar são botões

**Decisão**:

Em Consumos a lançar, cada item tem:

1. **Ver ficha** — `<Link>` para `/ficha/{id_reserva}`.
2. **Marcar lançado** — único disparo do `POST .../lancamento`.
3. **Dispensar** — único disparo do `POST .../dispensa`.

Não há `onClick` na linha. Clicar descrição, quarto, valor ou
**Ver ficha** **não** lança nem dispensa.

Na fila do dia, hospedado ganha **Saída** — `<Link>` para
`/saida/{id_reserva}`. **Não** se chama **Confirmar saída**. Não
dispara `POST /saida`.

Em Saída do hóspede, **Confirmar saída** é o único `<button>` que
posta. Clicar nome, lista ou aviso **não** encerra. O aviso é
`<Link>` para `/consumos` (fila da casa).

Um clique no botão registra; sem “tem certeza?”. Enquanto o POST
daquele alvo não conclui, o botão daquele alvo fica indisponível.
`409` mostra o motivo da API e refaz o GET.

**Rationale**: FR-008, FR-018, FR-023. Mesmo critério da chegada e
do Resolvido.

**Alternativas consideradas**:

- **Rótulo Confirmar saída na fila**: sugere encerramento no
  gesto. Recusado.
- **Dois controles na linha** (abrir + encerrar): recusado na
  clarificação.

---

## 4. Ordem = a da API; totais e tempo no cliente

**Decisão**: `GET /consumos/pendentes` já devolve `ORDER BY
aberta_em ASC`. A tela **não** reordena.

Tempo de espera: `tempoDecorrido(aberta_em, agora)` já existente.
`agora` entra como argumento nos testes. Calculado no render;
**não** há relógio que tique.

Total pendente e quantidade: soma/`length` do array recebido.
Tempo do mais antigo: o do primeiro item (já ordenado).

Na saída, o total cobrável é o `total` do envelope de
pedidos-feitos-pelo-chat — a tela **não** some de novo.

Aviso de pendência: `pendentesDaEstadia(itensPendentes, idReserva)`
com o GET da **casa** inteira; se o recorte da estadia for
não-vazio, avisa. Não filtra a tela Consumos a lançar.

**Rationale**: clarificações 3 e 4. SC-001, SC-003. Não expandir
JSON.

**Alternativas consideradas**:

- **Campo `tempo_decorrido` / `total` no GET de pendentes**: o
  instante e os valores já vêm. Rejeitado.
- **Coluna pendente/lançado na lista da saída**: a consulta não
  traz o status. Recusado nesta fase.

---

## 5. Depois de lançar, dispensar ou confirmar, `GET` — não recarregar a página

**Decisão**:

| POST 200 | Em seguida |
| --- | --- |
| lançamento ou dispensa | `GET /consumos/pendentes` e substituir `itens` |
| saída | estado local `encerrado`; botão some; **não** afirma que o lançamento acabou |

Falha de GET inicial: painel permanece, declara que não carregou,
**Tentar de novo**. **Não** é `itens: []`. `200` com `itens: []` é
lista vazia (turno financeiro limpo).

POST rede/5xx: o item ou a reserva permanece; aviso; botão volta a
aceitar clique. Zero recado novo ao hóspede afirmado pela tela.

**Rationale**: FR-006, FR-027, SC-004, SC-010. Igual à F8.2/F8.4.

**Alternativas consideradas**:

- **Optimistic remove**: se o POST falhar, a omissão some da tela
  (Artigo V invertido). Rejeitado.
- **`window.location.reload`**: pede a tela de novo. Rejeitado.

---

## 6. Identidade na saída: ficha + fila; aviso: pendentes da casa

**Decisão**: com `idReserva` na URL, `TelaSaida` dispara:

1. `GET /reservas/{id}/ficha` — nome e `status_reserva` (confirmar
   só se `hospedado`).
2. `GET /reservas/{id}/pedidos-feitos-pelo-chat` — lista e total.
3. `GET /consumos/pendentes` — aviso se existir item daquela
   reserva; quarto “quando conhecido” a partir desses itens.
4. `GET /fila-do-dia` — datas previstas se a reserva ainda estiver
   na fila.

Sem id: estado honesto, aponta à fila, **zero** fetch (como
`TelaFicha`).

`404` de ficha ou de pedidos: recado genérico da API; não afirmar
que a reserva existe; sem botão de confirmar.

**Rationale**: spec pede nome, quarto quando conhecido e datas.
Nenhum GET novo. Quarto não está na consulta cobrável; vem do
pendente quando houver.

**Alternativas consideradas**:

- **Só os dados passados pelo `Link` da fila**: some no recarregar.
  Rejeitado.
- **Buscar quarto em `GET /solicitacoes`**: mistura a lista
  operacional na saída. Rejeitado.

---

## 7. Destaque de saída vencida; resumo do turno intacto

**Decisão**: `ItemFila` passa a ler `saida_nao_confirmada` (já no
JSON desde F4.1; a F8.2 ignorou). Rótulo distinto de chegada
vencida, recado não enviado e ficha parcial.

`resumirTurno` **não** ganha quarta conta (spec: as três da F8.2
permanecem).

Caminho **Saída** só se `status === "hospedado"`.

**Rationale**: FR-024, FR-025. Artigo V no checkout.

**Alternativas consideradas**: conta “saídas vencidas” no topo —
recusado pela spec.

---

## 8. Testes da casca e mock de pendentes

**Decisão**: ao nascer `TelaConsumos`, o `fetch` falso da casca
precisa responder `GET /consumos/pendentes` com `200` e `itens: []`
no mínimo quando a recepção abrir esse destino. Staff e gestão em
`/app/consumos` e `/app/saida` / `/app/saida/:id`: a casca **não**
monta a tela e **não** dispara GET de pendentes, ficha, pedidos
nem POST de saída.

**Rationale**: mesmo ponto da F8.2/F8.4.

---

## Divergências documentais

O mapa `docs/wireframes-painel.html` (telas `consumos` e `saida`)
mostra nome do hóspede na fila financeira, coluna de lançamento no
sistema de gestão por item, e **Confirmar saída** encerrando na
própria fila.

Isso **não** foi entregue nas operações e foi recusado nas
clarificações da spec. Corrigir o mapa (lista financeira sem
cadastral, Ver ficha + lançar/dispensar, aviso de estadia sem
status por linha, **Saída** na fila que só navega) é trabalho
documental posterior — não bloqueia implementar. Não contornar em
silêncio: a spec vence o rascunho.

`TelaFila` hoje documenta “sem confirmar saída”. Esta fatia
acrescenta o caminho **Saída** e o destaque vencida; o POST
continua só em `TelaSaida`.
