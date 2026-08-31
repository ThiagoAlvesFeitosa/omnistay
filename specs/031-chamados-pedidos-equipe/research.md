# Fase 0 — Pesquisa e decisões técnicas: chamados e tela da equipe

Cada seção registra a decisão, por que ela foi tomada e o que foi recusado.
Divergências documentais estão na última seção.

---

## 1. Nenhuma rota nova; duas operações já entregues (+ ficha só na recepção)

**Decisão**: as telas consomem só o que já existe:

| Ação na tela | Rota existente | Operação |
| --- | --- | --- |
| Ver pendências abertas | `GET /solicitacoes` | `ler_solicitacao_atribuida` |
| Marcar resolvido | `POST /solicitacoes/{id}/resolucao` | `resolver_solicitacao` |
| Chegar ao nome/ficha (só recepção) | navega para `/app/ficha/{id_reserva}` | `ler_dado_cadastral_de_hospede` (já na F8.3) |

Zero operação nova na matriz. Zero revisão Alembic. Cookie
`omnistay_sessao` continua sendo o transporte (`pedirAutenticado`).
A tela **não** envia `id_hotel`. Proxy Vite já cobre `/solicitacoes`.

`GET /consumos/pendentes` e `POST .../lancamento` **não** entram
(F8.5). `id_reserva` na lista da recepção é só alvo de navegação;
não se exibe como “hóspede #n” na equipe.

**Rationale**: spec reusa F3.4–F3.7 e F8.3. Artigo XI. Clarificações:
lista sem nome; linha da recepção leva à reserva.

**Alternativas consideradas**:

- **Campo `nome` só para recepção no JSON**: duas formas da mesma
  fila, e o payload da equipe ficaria a um bug de filtro. Recusado
  na clarificação.
- **`GET /solicitacoes/{id}`**: a spec não pede detalhe. Rejeitado.
- **WebSocket / recarga periódica**: atualização ao vivo ficou
  deferred no clarify. Sem peça nova. Recarregar, “tentar de novo”
  e o `GET` depois do resolver bastam (Artigo IV).

---

## 2. Duas telas, um módulo puro compartilhado

**Decisão**:

| Destino F8.1 | Componente | Perfil |
| --- | --- | --- |
| `/app/alertas` | `TelaAlertas` | recepção (computador) |
| `/app/chamados` | `TelaChamados` | staff (compacto; casa do papel) |

Funções puras em `frontend/src/painel/solicitacoes.ts`: tipos do
item, rótulo de natureza, tempo decorrido, se o destaque de prazo
vale (só ecoar `destaque_tempo_excedido`). Sem Redux, sem React
Query.

A casca deixa de montar `TelaNomeada` nesses dois `id`. Gestão
continua redirecionada — **zero** `fetch` de `/solicitacoes` na
sessão de gestão nestas rotas.

**Rationale**: superfícies distintas (Ver ficha × um botão; tabela ×
cartão). Artigo XI: dois componentes + helpers, não um terceiro app.

**Alternativas consideradas**:

- **Um componente com `if (perfil)`**: mistura o caminho da ficha no
  mesmo arquivo que a equipe não pode ter. Dois arquivos deixam o
  teste da equipe falhar se alguém colar um `Link` para ficha.
- **App nativo**: cortado no backlog. O painel no celular assume.

---

## 3. Ver ficha rotulado; Resolvido é o botão — a linha não resolve

**Decisão**: na recepção, cada item tem:

1. Controle rotulado **Ver ficha** (`<Link>` para
   `/ficha/{id_reserva}`), o mesmo destino da F8.3. É o caminho da
   clarificação: identificar quem abriu, inclusive sem quarto.
2. `<button>` **Resolvido** — único disparo do `POST .../resolucao`.

Não há `onClick` no cartão/linha que resolva. Clicar descrição,
quarto, natureza ou **Ver ficha** **não** marca resolvido.

Na equipe: **não** existe Ver ficha, nem `Link` com `id_reserva`,
nem texto que convide a “ver o hóspede”. Só **Resolvido**.

Um clique no botão registra; sem “tem certeza?”. Enquanto o `POST`
daquele item não conclui, o botão daquele item fica indisponível
(toque duplo). `409` mostra o motivo da API e refaz o `GET` — a
lista não mente aberto.

**Rationale**: FR-006, FR-009, FR-012. Mesmo critério da chegada
(F8.2): alvo rotulado, não a linha inteira.

**Alternativas consideradas**:

- **Linha inteira como link, botão dentro**: aninha interativos e
  arrisca resolver ao abrir ficha. Rejeitado.
- **Mostrar `id_reserva` na equipe como identificação**: a spec
  recusou identificador que convide a ver o hóspede. Rejeitado.

---

## 4. Ordem = a da API; tempo decorrido na tela

**Decisão**: `GET /solicitacoes` já devolve `ORDER BY aberta_em ASC,
id_solicitacao ASC`. A tela **não** reordena. Destaque de prazo
(`destaque_tempo_excedido`) é classe/rótulo, não `sort`.

Tempo decorrido: função pura `tempoDecorrido(abertaEm, agora)` em
português curto (`há N min` / `há N h` / `há N d`). `agora` entra
como argumento nos testes. Calculado no render de cada `GET`; **não**
há relógio que tique a cada segundo (clarify deferred atualização
ao vivo).

Natureza visível a partir de `tipo`: `reclamacao` → reclamação,
`servico` → serviço, `consumo` → consumo. Rótulos distintos.

**Rationale**: clarificação da ordem. SC-001 (primeiro = mais antigo).
Não expandir o JSON com `tempo_decorrido`.

**Alternativas consideradas**:

- **Reclamações em destaque primeiro**: recusado na clarificação.
- **Campo novo no GET**: o instante já vem. Rejeitado.

---

## 5. Depois de resolver, `GET` da lista — não recarregar a página

**Decisão**: `POST` `200` → `GET /solicitacoes` e substituir `itens`.
O id resolvido **não** volta (já é regra da F3.6). Consumo resolvido
some daqui e **não** dispara lançamento.

Falha de `GET` inicial ou pós-resolução: painel permanece, declara
que a lista não carregou, **Tentar de novo**. **Não** é `itens: []`.
`200` com `itens: []` é lista vazia (turno operacional limpo).

`POST` rede/5xx: o item permanece; aviso; botão volta a aceitar
clique. Zero afirmação de “já avisamos o hóspede”.

**Rationale**: FR-013, FR-020, SC-006, SC-010. Igual à F8.2 depois
da chegada.

**Alternativas consideradas**:

- **Optimistic remove**: se o `POST` falhar, a omissão some da tela
  (Artigo V invertido). Rejeitado.
- **`window.location.reload`**: pede a tela de novo. Rejeitado.

---

## 6. Consumo na equipe; lançar continua fora

**Decisão**: as três naturezas nas duas listas. Valor praticado
visível no consumo. **Resolvido** no consumo = quarto (F3.7). A tela
não chama `/consumos/pendentes` nem lançamento/dispensa.

**Rationale**: clarificação. Entrega no quarto é trabalho da equipe.

**Alternativas consideradas**: ocultar consumo no celular — recusado.

---

## 7. Testes da casca e mock de `GET /solicitacoes`

**Decisão**: `Casca.test.tsx` hoje abre `/app/chamados` e `/app/alertas`
com `TelaNomeada` (só título, zero fetch). Ao nascerem as telas, o
`fetch` falso precisa responder `GET /solicitacoes` com `200` e
`itens: []` no mínimo. Senão a casca “regressa” em estado de falha.

Staff e gestão em `/app/alertas`, recepção em `/app/chamados`: a
casca **não** monta a tela alheia e **não** dispara o GET (já F8.1).
Staff em `/app/ficha/:id`: continua sem GET de ficha (F8.3).

**Rationale**: mesmo ponto da F8.2 com a fila.

---

## 8. Relógio e destaque de prazo

**Decisão**: a tela não lê `parametro_hotel`. `destaque_tempo_excedido`
já vem calculado no GET (F3.5, só reclamação). Serviço e consumo:
nunca destacados por idade nesta superfície, mesmo que `aberta_em`
seja antigo.

**Rationale**: Artigo XIII — o prazo continua no parâmetro; a tela
não inventa “2 horas”.

---

## Divergências documentais

O mapa `docs/wireframes-painel.html` (telas `chamados` e `staff`)
mostra nome do hóspede, coluna de atribuído, canal, abas
abertos/andamento/resolvidos, pergunta fora do catálogo, ação
“Abrir”, e a equipe sem consumo.

Isso **não** foi entregue nas operações e foi recusado nas
clarificações da spec. Corrigir o mapa (lista única de abertas, sem
cadastral, Ver ficha + Resolvido, três naturezas também no celular)
é trabalho documental posterior — não bloqueia implementar. Não
contornar em silêncio: a spec vence o rascunho.

`TelaFicha` hoje diz que a ficha se abre pela fila do dia. Esta
fatia acrescenta o caminho a partir de Chamados e pedidos. O menu
`/app/ficha` sem id **continua** apontando à fila (não inventa
segunda lista nominada). Ajustar a frase do vazio para mencionar os
dois caminhos é honesto e cabe nesta fatia.
