# Pesquisa — F4.1 Confirmar Saída e Pesquisa

Decisões técnicas tomadas antes de escrever teste. Cada uma traz o que foi
escolhido, por quê, e o que foi recusado.

---

## 1. Clique espelha a chegada: `POST /reservas/{id}/saida`

**Decisão:** rota irmã de `POST /reservas/{id}/chegada`. Corpo vazio. Operação
já existente `confirmar_fase_da_reserva` (só recepção) — nenhuma operação nova
para o clique. `UPDATE … WHERE status = 'hospedado'` com `RETURNING`;
`rowcount = 0` vira `404` (outra propriedade / inexistente) ou `409` (estado
não admite). Trigger `fn_valida_transicao_reserva` já permite
`hospedado → encerrado` desde a `0001`. Grava `checkout_em = now()` na mesma
sentença. Na mesma transação, `conversa.agendar_pesquisa_saida` insere
mensagem pendente + trabalho `enviar_pesquisa_saida`.

**Rationale:** Artigo I (clique, não PMS) e o padrão que a F2.2 já ensinou ao
balcão. A spec nomeia a mesma permissão da chegada. A trigger é a garantia;
o `WHERE` é o caminho feliz.

**Alternativas recusadas:** operação nova `confirmar_saida` — duplicata da
matriz; transição só na aplicação — a trigger já existe e o teste de garantia
já cobre `hospedado → encerrado`; enviar a pesquisa no mesmo request síncrono
— viola Artigo III e o contrato da chegada.

---

## 2. Tipo `enviar_pesquisa_saida` com unicidade por reserva

**Decisão:** trabalho `enviar_pesquisa_saida`, índice único parcial por
`(payload->>'id_reserva')` — o mesmo desenho de `enviar_boas_vindas` e
`enviar_pulso`. “Pesquisa gravada” = existe essa linha, mesmo que o envio
ainda falhe. Worker retoma **o mesmo** trabalho. Chamado aberto e consumo
pendente **não** reavaliam elegibilidade no envio: a spec manda disparar
mesmo assim. Só a reserva deixar de estar `encerrado` (não acontece por este
fluxo) impediria o envio.

**Rationale:** Artigo III + IX. Duas confirmações simultâneas não podem criar
duas pesquisas. Não há janela de “já não vale a pena perguntar” depois do
clique — o hóspede acabou de sair do balcão.

**Alternativas recusadas:** unicidade só depois do envio — duas passagens
criam duas pesquisas; coluna `pesquisa_enviada` em `reserva` — o trabalho já
é o fato; suprimir por reclamação aberta — copia o pulso e contradiz a spec.

---

## 3. Tipo `interpretar_pesquisa_saida` por mensagem, não por classificar

**Decisão:** a resposta **não** passa por `classificar_mensagem`. Depois do
checkout não há toalha, catálogo nem chamado operacional (spec). O webhook,
se a reserva ativa não existir, resolve uma `encerrado` com pesquisa
incompleta e enfileira `interpretar_pesquisa_saida` (único por
`id_mensagem`). O worker aplica a janela.

Ordem de resolução no webhook (FR-027):

1. `aguardando_cadastro` no telefone → ficha (F1.3)
2. `hospedado` → classificação de estadia (F3.1)
3. `encerrado` com `enviar_pesquisa_saida` existente e pesquisa incompleta
   (falta nota ou falta aceite) → `interpretar_pesquisa_saida`. O **worker**
   aplica a janela e o prazo: dentro, interpreta; prazo ausente, humano +
   `prazo_ausente`; janela vencida, conclui sem gravar e sem humano
4. senão, se houver `encerrado` recente no telefone: grava a mensagem nela
   **sem** trabalho (histórico; sem nota, sem consentimento, sem humano)
5. senão: `sem_reserva` como hoje

**Rationale:** classificar depois do checkout reabriria F3.3–F3.5 para quem já
saiu. A spec manda não engolir ficha nem estadia em curso. Trabalho próprio
permite retry de interpretação sem misturar taxonomia de estadia.

**Alternativas recusadas:** reusar `classificar_mensagem` + intenção nova —
polui a taxonomia e os testes da F3.2; interpretar no próprio webhook —
LLM na API; interceptar pulso (`registrar_resposta_pulso`) — origem
diferente e o pulso já pode ter fechado.

---

## 4. Porta `interpretar_pesquisa_saida` no `LLMProvider`

**Decisão:** método novo na porta, não `classificar` nem `extrair_ficha`.
Retorno estruturado: `nota` (1–5 ou nulo), `comentario` (texto ou nulo),
`aceite` (`true` / `false` / nulo = não respondeu), `desfecho`
(`completo` | `parcial` | `irreconhecivel`). O domínio valida a nota; valor
fora de 1–5 descarta a nota e, se nada mais for aproveitável, cai em
irreconhecível. `LLMFalso` devolve fixtures. Falha da porta =
`FalhaDeExtracao` (já existe); trabalho `concluido`; sinal humano; **sem**
backoff estilo ficha.

**Rationale:** a ficha extrai nove campos cadastrais; a classificação devolve
eixos de estadia. Nenhum dos dois é nota+aceite. Artigo X: o domínio não
conhece o adaptador. Artigo II: primeira falha vai a humano, não insiste.

**Alternativas recusadas:** parser só de lista numerada no domínio — quebra na
primeira resposta em prosa (“cinco estrelas, pode mandar promo”); reusar
`classificar.sentimento` como nota — sentimento não é 1–5 e não captura
opt-in; backoff de `interpretar_ficha` — a pessoa já saiu, insistir não
completa cadastro nenhum.

---

## 5. `feedback` grava a avaliação de checkout; `hospedagem` grava o consentimento

**Decisão:** `avaliacao` com `origem = 'checkout'` continua no módulo
`feedback` (já dono da tabela). `consentimento` é 1:N de `hospede` — módulo
`hospedagem`, que já governa hóspede e reserva. O worker de interpretação
orquestra: chama `feedback` quando há nota válida; chama `hospedagem` quando
`aceite` é booleano. Nenhum dos dois importa `conversa`. Completar comentário
depois da nota é `UPDATE` da **mesma** linha de checkout (comentário opcional);
nota já gravada não muda depois de a pesquisa estar completa. Consentimento
é **sempre INSERT**.

Unicidade `(id_reserva, origem)` já existe. Pulso e checkout convivem.

**Rationale:** fronteira de módulo da constituição. Misturar SQL de
`consentimento` em `feedback` ou de `avaliacao` em `conversa` reabre o ciclo
que a F0.3 recusou.

**Alternativas recusadas:** módulo novo só para consentimento — terceira peça
para uma tabela que já pertence a hospedagem; campo booleano em `hospede` —
a spec e o Artefato 4 recusam (não responde “aceitava em março?”).

---

## 6. Pesquisa de ida é recado iniciado pelo hotel

**Decisão:** método novo `enviar_pesquisa_saida` na `MensageriaGateway`, no
espírito de `enviar_boas_vindas` / `enviar_pulso` (utilidade). Sem recado de
agradecimento depois da resposta: a spec não pede e Artigo VII não admite
mensagem proativa extra. Sem `enviar_texto_sessao` na ida — a janela de 24 h
pode estar fechada (hóspede silencioso o resto da estadia).

Texto: lista numerada de três itens (nota 1–5, comentário opcional, aceite
sim/não), prenome, sem “extrato”, sem “conta”, sem oferta, sem lista de
pedidos. Teste de conteúdo recusa essas palavras.

**Rationale:** as mensagens iniciadas pelo hotel no MVP são Utility. A pessoa
acabou de estar no balcão, não necessariamente no chat. Agradecimento seria
o quarto recado da fatia sem critério de aceite.

**Alternativas recusadas:** sessão na ida — falha silenciosa se a janela
fechou, e o checkout não se desfaz (a pesquisa some sem sinal novo); incluir
a lista de pedidos no mesmo recado — é F4.2 e reintroduz o atrito de
nomenclatura.

---

## 7. Destaque na fila + exceção estreita para `encerrado`

**Decisão:** coluna derivada `saida_nao_confirmada` =
`status = hospedado AND data_checkout_prevista < CURRENT_DATE`. Distinta de
`chegada_nao_confirmada` e de `boas_vindas_nao_enviadas`. Encerrada some
desse destaque porque deixou de estar hospedada.

**Exceção à F1.1:** a visão hoje faz `status NOT IN ('encerrado', 'cancelada')`.
Isso esconderia interpretação irreconhecível da pesquisa (Artigo II/IV/V: o
humano precisa ver no painel). A visão passa a **manter** `encerrado` só
quando `pesquisa_saida_leitura_humana` é verdadeiro — mensagem recebida da
pesquisa com desfecho `irreconhecivel` / `indisponivel` / `formato_invalido`
/ `prazo_ausente`. Cancelada continua fora. Encerrada “limpa” continua fora.

Isso é correção do documento vivo `docs/04-schema.sql` (comentário da visão)
e da F1.1 como fato histórico: na F1.1 não havia trabalho depois do
checkout. Não reabre a F1.1.

**Rationale:** omissão da pesquisa não gera reclamação (jornada R6). O
destaque de vencida cobre o clique esquecido. O flag humano cobre a resposta
que o sistema não entendeu. Sem o segundo, a mensagem existe no histórico e
some da tela do turno.

**Alternativas recusadas:** manter todo `encerrado` na fila — enche o turno
com quem já saiu; não sinalizar humano — viola Artigo II; coluna na
`reserva` — a mensagem já carrega o desfecho, como `precisa_atendimento_humano`.

---

## 8. Prazo `horas_atribuicao_pesquisa_saida`, relógio do checkout

**Decisão:** chave em `parametro_hotel`, semeada `24`, contada de
`checkout_em` (instante real, não a data prevista). Worker e webhook
releem o prazo. Ausência ou valor inválido: **não** atribui a resposta à
pesquisa; log `prazo_ausente`; sinal humano; nenhum `24` embutido. Sem
varredura nova no agendador — o clique agenda o envio; o webhook agenda a
interpretação. `--uma-passagem` não ganha flag.

**Rationale:** Artigo XIII. Eixo no instante real (lição da F2.2: calendário
mente na virada do dia). Sem APScheduler (Artigo XI).

**Alternativas recusadas:** prazo constante 24 no código; janela até a
pesquisa “completar para sempre” — mensagem meses depois vira nota; varredura
horária de “pesquisas não enviadas” — o clique já gravou o trabalho.

---

## 9. Consentimento: duas rotas, duas operações, append-only

**Decisão:**

| Rota | Operação | Quem |
| --- | --- | --- |
| `GET /hospedes/{id}/consentimento?em=` | `ler_consentimento` | recepção, gestão |
| `POST /hospedes/{id}/consentimento` | `registrar_consentimento` | recepção, gestão |

`em` omisso = agora. Estado vigente = linha mais recente da finalidade
`comunicacao_marketing` com `momento <= em`; zero linhas → `concedido:
false` sem inventar registro. POST insere (`origem` só `painel` ou
`solicitacao_titular` por esta rota). Origem `pesquisa_checkout` só o
worker grava. Isolamento: hóspede alcançável só via reserva do `id_hotel`
da sessão; outro hotel → `404` uniforme. Staff → `403`.

**Rationale:** a spec exige consulta em data passada e revogação sem apagar.
Gestão precisa da prova LGPD; recepção registra o pedido no balcão. Staff
não opera dado cadastral.

**Alternativas recusadas:** uma operação só — leitura e escrita têm risco
diferente; reusar `ler_dado_cadastral_de_hospede` — gestão ficaria de fora;
UPDATE in-place — o Artefato 4 e o `CHECK` de origem já recusam.

---

## 10. Completude da pesquisa e silêncio

**Decisão:** pesquisa **completa** = nota 1–5 gravada **e** aceite
booleano gravado. Comentário é opcional e pode chegar depois, na mesma
avaliação. Silêncio total: zero avaliação de checkout, zero consentimento,
zero lembrete. Nota sem aceite: avalia, não consente. Aceite sem nota:
consente se o booleano veio claro; a avaliação só nasce com nota — se só
veio o sim/não, grava consentimento e espera a nota até a janela fechar.

**Rationale:** FR-023 (silêncio ≠ recusa) e FR-012 (nota alta ≠ opt-in).
Aceite reconhecível não deve ser jogado fora só porque a nota veio numa
segunda bolha.

**Alternativas recusadas:** recusa implícita no silêncio; exigir os três
campos na mesma mensagem; lembrete único estilo ficha — Artigo VII e a
jornada (“disponibilidade curta”, sem insistir depois da estadia).
