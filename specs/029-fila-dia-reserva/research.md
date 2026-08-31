# Fase 0 — Pesquisa e decisões técnicas: fila do dia e cadastro

Cada seção registra a decisão, por que ela foi tomada e o que foi recusado.
Divergências documentais estão na última seção.

---

## 1. Nenhuma rota nova; três operações já entregues

**Decisão**: a tela consome só o que a recepção já pode:

| Ação na tela | Rota existente | Operação |
| --- | --- | --- |
| Ver o turno | `GET /fila-do-dia` | `ler_fila_do_dia` |
| Cadastrar | `POST /reservas` | `alterar_reserva` |
| Confirmar chegada | `POST /reservas/{id}/chegada` | `confirmar_fase_da_reserva` |

Zero operação nova na matriz. Zero revisão Alembic. Cookie
`omnistay_sessao` continua sendo o transporte (`pedirAutenticado`).

**Rationale**: a spec reusa F1.1 e F2.2. Artigo XI.

**Alternativas consideradas**:

- **`GET` com totais no JSON**: duplicaria a partição no backend só
  para o topo da tela. A lista já é a fonte (Artigo IV). Rejeitado.
- **`GET /indicadores/chegadas-do-dia` no resumo**: conta outro recorte
  (entrada *hoje*, inclusive hospedado; sem isolado de vencida).
  Quebraria FR-005. Rejeitado.
- **WebSocket / recarga periódica**: dois atendentes dessincronizados
  é limitação honesta da spec. Sem peça nova.

---

## 2. Resumo do turno = partição das linhas na tela

**Decisão**: três contas, cada linha em uma só, soma = `itens.length`.

| Conta | Predicado sobre o item |
| --- | --- |
| Hoje ainda não confirmadas | `status !== "hospedado"` **e** `chegada_nao_confirmada === false` |
| Já hospedados | `status === "hospedado"` |
| Entrada vencida sem confirmação | `chegada_nao_confirmada === true` |

Função pura em `frontend/src/painel/fila.ts`, testada sem DOM.

`hospedado` nunca vem com `chegada_nao_confirmada` (já F2.2). Encerrada
e futura não entram em `itens`.

**Rationale**: clarificação da spec (sessão 2026-08-31). Sinal de
vencida não se mistura com o movimento do dia (Artigo V).

**Alternativas consideradas**:

- **Contar vencida também em “chegadas”**: o recepcionista perde o
  atraso no número grande. Recusado na clarificação.
- **Três `COUNT` no SQL**: terceira descrição da mesma visão. Rejeitado.

---

## 3. Botão rotulado; elegibilidade pelo `status`

**Decisão**: oferecer **Confirmar chegada** somente quando

```text
status ∈ { ficha_recebida, ficha_parcial, sem_cadastro_previo }
```

Ausente em `aguardando_cadastro`, `hospedado`, e nos que a lista já
omite. O controle é um `<button>` com o rótulo, **dentro** da linha.
Clique em nome, telefone, datas ou situação **não** dispara `POST`.

Um clique registra; sem diálogo. `409` (corrida) mostra o motivo e
refaz o `GET` — a lista não mente hospedado.

**Rationale**: FR-016/018 e a máquina de estados da F2.2. A tela não
convida o clique que o banco recusaria (Artigo IX, Artigo XV).

**Alternativas consideradas**:

- **Linha inteira clicável**: a clarificação recusou — ler o telefone
  confirmaria por engano.
- **Segundo “tem certeza?”**: atrito no balcão; a spec escolheu um
  clique no botão.
- **Oferecer o botão sempre e tratar `409`**: ensina o clique inútil.
  Rejeitado.

---

## 4. Sinais distintos vêm de campos já na fila

**Decisão**: a tela não inventa flag.

| Pendência da spec | Campo existente | Rótulo visível |
| --- | --- | --- |
| Chegada vencida | `chegada_nao_confirmada` | distinto (ex.: “não confirmada”) |
| Recado não enviado | `boas_vindas_nao_enviadas` | distinto (ex.: “recado não enviado”) |
| Ficha parcial | `estado_cadastro === "parcial"` | distinto (ex.: “parcial”) |

Os dois booleanos de chegada/recado já são mutuamente exclusivos no
backend. Ficha completa / aguardando / sem cadastro prévio /
leitura humana aparecem como estado, sem o destaque vermelho das
três pendências.

`status_envio_coleta`, `precisa_atendimento_humano` e
`saida_nao_confirmada` **não** entram nesta fatia (não são critério
F8.2; checkout é F8.5).

**Rationale**: FR-004. Não expandir o JSON.

**Alternativas consideradas**:

- **Mostrar status de envio da coleta**: a spec deixou opcional; o
  backlog da F8.2 não pede. Fica para se o balcão reclamar.

---

## 5. Depois de gravar, `GET` da fila — não recarregar a página

**Decisão**: `POST` aceito → `GET /fila-do-dia` e substituir `itens`.
Cadastro com entrada futura: o `id_reserva` **não** virá nos itens;
aí sim a mensagem “registrada; entra na fila no dia da entrada”.
Cadastro de hoje/passado: o id aparece; sem fingir falha.

Falha de `GET` inicial ou de `GET` pós-gravação: painel permanece,
declara que a lista não carregou, oferece tentar de novo. **Não** é
`itens: []`. `200` com `itens: []` é o turno vazio (contas em zero).

**Rationale**: spec (FR-007a, FR-012, FR-013). “Hoje” é
`CURRENT_DATE` do banco; a tela não compara calendário local.

**Alternativas consideradas**:

- **Optimistic update só com o `201`**: perde `boas_vindas_nao_enviadas`
  e o resumo. Rejeitado.
- **`window.location.reload`**: viola “sem pedir a tela de novo” na
  prática do balcão e mata o estado da casca. Rejeitado.

---

## 6. Cadastro no destino `/app/reserva` que já existe

**Decisão**: `TelaNovaReserva` no path que a F8.1 já mapeou. A fila
tem ação “Nova reserva” que navega para lá. Cancelar e sucesso
voltam a `/app/fila`. Três campos: nome, telefone, datas. Sem e-mail.

Validação de telefone **na digitação**: função TypeScript com a mesma
regra de `app/comum/telefone.py` (dígitos; 10/11 nacionais ou 12/13
com `55`). A garantia continua no `POST` (`422`). Datas: saída
estritamente depois da entrada; `input type="date"`.

Dois cadastros com o mesmo telefone: a tela **não** busca hóspede;
o `POST` já cria outro titular.

**Rationale**: FR-008, FR-009, FR-026. Destino já no menu; não nascer
modal que o mapa não tem.

**Alternativas consideradas**:

- **Formulário embutido na fila**: “da mesma tela” do backlog. O mapa
  da F8.1 já tem o destino; dois lugares para o mesmo POST. Rejeitado
  nesta fatia (um formulário, dois caminhos de entrada: fila e menu).
- **Campo e-mail do wireframe**: F7.5 cortada; a spec proíbe.

---

## 7. Teste: Vitest na tela; pytest só na regressão HTTP

**Decisão**:

- **Vitest**: partição do resumo; botão presente/ausente por `status`;
  clique fora do botão não chama `POST`; `GET` 500 ≠ vazio; cadastro
  `422` na digitação e no submit; `201` + `GET` atualiza a lista;
  futuro → mensagem e linha ausente. `fetch` falso.
- **pytest**: não reabre regra de hospedagem. A suíte já verde de
  F1.1/F2.2 continua o portão. Nenhum teste novo de backend **salvo**
  se alguém tocar o schema HTTP (esta fatia não toca).

**Rationale**: Artigo XII na superfície nova; Artigo XI contra
Playwright (já recusado na F8.1).

**Alternativas consideradas**:

- **Playwright contra uvicorn**: lente de seis telas, cara agora.

---

## 8. Casca especializa dois destinos; o resto permanece título

**Decisão**: em `Casca.tsx`, `destino.id === "fila"` renderiza
`TelaFila`; `"reserva"` renderiza `TelaNovaReserva`; `"simulador"`
continua o que é; demais → `TelaNomeada`.

Staff/gestão que colam `/app/fila`: a casca já manda à casa **antes**
de montar a tela. A API seguiria `403`. Sem fetch de fila nesses
perfis.

**Rationale**: FR-021. O mapa não muda.

---

## Divergências documentais

1. **Wireframe com e-mail e “Confirmar saída”.** A spec desta fatia
   corta os dois (F7.5 declarada; checkout é F8.5). O plano segue a
   spec, não a linha extra do HTML de referência.
2. **Wireframe com telefone mascarado.** A spec pede o telefone de
   contato que a recepção gravou. Sem máscara nova — seria regra de
   minimização que a F1.1 não aplicou à recepção.
3. **Wireframe com “Ver ficha” na linha.** F8.3. Nesta fatia a linha
   hospedada sem botão de chegada pode não ter ação — o menu já tem
   o destino nomeado.
4. **F8.1: casas só com título.** Esta fatia **substitui** o título
   vazio de `fila` e `reserva`. Não é regressão da casca: é o trabalho
   que a F8.1 adiou de propósito (research §9 da 028).
