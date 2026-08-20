# Pesquisa — F4.2 Lista de Pedidos Feitos pelo Chat

Decisões técnicas tomadas antes de escrever teste. Cada uma traz o que foi
escolhido, por quê, e o que foi recusado.

---

## 1. O clique de saída orquestra a lista; não há segundo gesto

**Decisão:** `hospedagem.confirmar_saida` continua sendo o único clique. Depois
de persistir `encerrado` e agendar a pesquisa (F4.1), consulta
`atendimento.listar_pedidos_feitos_pelo_chat`. Se a lista de cobráveis não é
vazia, chama `conversa.agendar_lista_pedidos_chat` na **mesma transação**.
Resposta do POST ganha `lista`: `agendada` | `ausente` | `ja_agendada`.
`ausente` = zero itens cobráveis = zero mensagem, zero trabalho. A pesquisa
não depende desse campo.

**Rationale:** a spec proíbe segundo clique e manda silêncio quando não há o
que conferir (Artigo VII). Orquestrar no dono do checkout evita que `conversa`
importe `atendimento` — esse import já existe no sentido inverso e seria
ciclo (lição da F0.3).

**Alternativas recusadas:** segundo POST “enviar lista” — a omissão humana
voltaria a ser silenciosa; sempre enfileirar e o worker decidir não enviar —
cria trabalho fantasma e mensagem vazia; `conversa` buscar o consumo —
ciclo de import; mandar a lista dentro da pesquisa — reabre F4.1 e o atrito
de nomenclatura.

---

## 2. Tipo `enviar_lista_pedidos_chat` único por reserva

**Decisão:** trabalho `enviar_lista_pedidos_chat`, índice único parcial por
`(payload->>'id_reserva')` — o mesmo desenho de `enviar_pesquisa_saida`.
Payload só com identificadores: `{id_reserva, id_mensagem}`. O texto já está
em `mensagem.conteudo`. Worker retoma **o mesmo** id. CHECK e allowlist
na mesma revisão (`0018`). `--uma-passagem` consome o tipo; nenhuma flag
no agendador.

“Lista gravada” = existe essa linha. Duas confirmações simultâneas não
existem (a segunda é `409` de estado); duas execuções do agendar na mesma
reserva colidem no índice e devolvem `ja_agendada` sem segunda mensagem.

**Rationale:** Artigos III e IX. Conferência em código não impede corrida.

**Alternativas recusadas:** unicidade só depois do envio — duas passagens
criam duas listas; reusar `enviar_pesquisa_saida` — mistura pendências e
quebra os testes da F4.1 que contam uma pesquisa; coluna booleana em
`reserva` — o trabalho já é o fato.

---

## 3. Recorte cobrável: pendente + lançado; fora serviço e dispensado

**Decisão:** `SELECT` em `consumo` ⋈ `solicitacao` ⋈ `reserva` com
`reserva.id_hotel` da sessão, `solicitacao.id_reserva` pedido e
`status_lancamento IN ('pendente', 'lancado')`. Ordem: `solicitacao.aberta_em`,
depois `id_solicitacao`. Campos da linha: `descricao_item`, `valor_praticado`
(e `id_solicitacao` no JSON do painel). **Não** lê `solicitacao.descricao`
(DPC — texto do hóspede). **Não** devolve `status_lancamento` ao hóspede nem
no GET desta lista (o recorte é o da mensagem).

Serviço operacional não tem linha em `consumo`. Dispensado tem, e é
filtrado.

**Rationale:** a spec (e o Artefato 3 §4.2) manda conferir o que será
cobrado. Pendente entra porque o lançamento no outro sistema pode ocorrer
depois da saída (já decidido na F3.7). Dispensado não será cobrado.
Status interno de lançamento no recado induz “já está na fatura da casa”.

**Alternativas recusadas:** só `lancado` — omite o que o hóspede pediu e
ainda não foi clicado no PMS; incluir dispensado com nota “cortesia” —
mensagem extra e confusão; reusar `GET /consumos/pendentes` — mistura fila
financeira com conferência de checkout e inclui staff.

---

## 4. Snapshot na mensagem; GET ao vivo

**Decisão:** `conversa` monta o texto **no enfileiramento** com os itens
recebidos e grava `mensagem` pendente. O worker só envia o corpo já
gravado. O GET do painel **releia** o recorte cobrável agora. Lançar ou
dispensar depois **não** reescreve a mensagem, **não** cria segundo
trabalho, **não** manda correção (Artigo VII / FR-017).

**Rationale:** gravar antes de enviar é o padrão de toda mensagem do
produto. A divergência posterior (item dispensado após o envio) é o caso
de borda que a spec já aceita como correção humana no balcão.

**Alternativas recusadas:** montar o texto no worker — o corpo ainda não
estaria gravado se o processo morrer entre claim e send; UPDATE da
mensagem quando a recepção dispensa — mensagem proativa disfarçada e
mente o histórico do que foi enviado.

---

## 5. Porta `enviar_lista_pedidos_chat` na ida; sem LLM e sem webhook novo

**Decisão:** método novo em `MensageriaGateway`, no espírito de
`enviar_pesquisa_saida` (utilidade, hotel inicia). Assinatura: telefone,
prenome, corpo, ids. `MensageriaFalsa` registra `tipo=lista_pedidos_chat`.
A ida **não** usa `enviar_texto_sessao` — a janela de 24 h pode estar
fechada. Sem método novo no `LLMProvider`. Sem ramo novo no webhook: a
lista não pede resposta; contestação continua no fluxo da F4.1 (pesquisa
incompleta ou leitura humana).

**Rationale:** Artigo X e VII. Intenção nova na classificação reabriria
F3.2–F3.5 para quem já saiu — a F4.1 recusou isso de propósito.

**Alternativas recusadas:** sessão na ida — falha silenciosa se o hóspede
não falou no dia; parser de “faltou a cerveja” — inventa correção; segundo
tipo `interpretar_lista` — complexidade sem critério de aceite.

---

## 6. Texto: rótulo, itens, total dos pedidos do chat, honestidade

**Decisão:** uma mensagem, montagem pura em
`conversa.texto_lista_pedidos_chat`. Prenome. Rótulo **pedidos feitos pelo
chat**. Cada item em linha: descrição + valor no mesmo formato `R$ 0,00` da
confirmação de consumo. Em seguida, `Total dos pedidos feitos pelo chat`
com a soma **somente** desses itens. Uma frase de alcance: a lista cobre
somente o que foi pedido pelo chat. Sem pergunta, sem convite a pagar, sem
oferta. Teste unitário recusa as substrings `extrato` e `conta` (qualquer
capitalização).

**Rationale:** a spec permite a soma se o rótulo não sugerir fatura. O
balcão precisa do total; o hóspede confere o conjunto. A frase de alcance
é o Artigo XV em texto.

**Alternativas recusadas:** omitir o total — o critério de aceite não
exige, mas o balcão conferiria somando à mão; chamar a soma de “total da
estadia” — mente; listar `solicitacao.descricao` — vaza DPC.

---

## 7. GET `/reservas/{id}/pedidos-feitos-pelo-chat` e operação nova

**Decisão:** rota no roteador de `hospedagem` (mesmo recurso da saída),
serviço SQL em `atendimento`. Operação nova
`ler_pedidos_feitos_pelo_chat`: `recepcao` e `gestor`. Staff `403`. Outro
hotel ou reserva inexistente: `404` uniforme (`Reserva nao encontrada.`).
Lista vazia: `200` com `itens: []` e `total: 0`. Consulta permitida em
qualquer status da reserva da casa (a recepção pode olhar antes do
clique). Campos proibidos: nome, telefone, documento, endereço, texto da
solicitação, `status_lancamento`.

Não reutilizar `ler_solicitacao_atribuida` (staff veria) nem
`ler_indicadores` (é contagem, não itens nominados de uma reserva).

**Rationale:** Artigo IV (painel é a verdade) e a matriz da F4.1
(consentimento: recepção + gestão, staff fora). URL sem “extrato” nem
“conta”.

**Alternativas recusadas:** só a mensagem — envio falho apaga a
conferência; PUT na fila do dia — mistura turno com cobrança; gestão sem
acesso — a spec manda consultar.

---

## 8. Fronteira dos módulos e log

**Decisão:**

| Módulo | Faz |
| --- | --- |
| `atendimento` | SQL do recorte cobrável |
| `conversa` | texto, `mensagem`, trabalho, envio |
| `hospedagem` | orquestra no `confirmar_saida`; GET traduz HTTP |
| `acesso` | uma operação nova |
| `fila` / worker | tipo + ramo |

Log: `lista_pedidos_agendada` / `lista_pedidos_ausente` /
`lista_pedidos_enviada` com ids, hotel e **contagem** de itens — nunca
corpo, nunca `descricao_item`, nunca `valor_praticado` por extenso
(padrão F3.7).

**Rationale:** cada módulo nas tabelas que governa. Valor no log seria o
eco da mensagem.

**Alternativas recusadas:** `feedback` dono da lista — não é avaliação;
módulo novo — Artigo XI.

---

## 9. Sem parâmetro novo, sem disparo retroativo

**Decisão:** nenhum `parametro_hotel`. A lista sai no clique, como a
pesquisa. Reservas já `encerrado` antes desta fatia **não** recebem
varredura de catch-up.

**Rationale:** Artigo VII e XIII. Inventar prazo ou backfill seria
mensagem proativa em massa.

**Alternativas recusadas:** agendador `--enviar-listas-pendentes` —
APScheduler de fato, sem problema presente; copiar
`horas_atribuicao_pesquisa_saida` — a lista não espera resposta.
