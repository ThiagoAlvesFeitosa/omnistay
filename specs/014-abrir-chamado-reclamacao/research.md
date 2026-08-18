# Pesquisa — F3.5 Abrir Chamado de Reclamação

Decisões técnicas tomadas antes de escrever teste. Cada uma traz o que foi escolhido, por
quê, e o que foi recusado. Nada aqui é preferência estética: tudo tem consequência em teste
ou em risco operacional.

---

## 1. Tipo `abrir_chamado_reclamacao`; allowlist e ramo no mesmo passo

**Decisão:** a classificação **não** confirma e **não** abre `solicitacao`. Quando
`classificar_mensagem` grava `reclamacao_tecnica` + `desfecho = classificado`,
enfileira `abrir_chamado_reclamacao` na mesma transação (payload
`{id_reserva, id_mensagem}` — a mensagem **recebida**). O worker ganha o tipo no
`ck_trabalho_tipo`, no índice único, na allowlist de `reclamar_proximo` **e** no ramo
`processar_trabalho_abrir_chamado` no mesmo commit.

Vale para sentimento negativo, neutro ou positivo. Pedido de serviço continua
enfileirando só `registrar_pedido_servico`. Dúvida geral continua só
`responder_duvida`.

Inventário conhecido que esta fatia mexe:

| Teste atual | Destino nesta fatia |
| --- | --- |
| `test_reclamacao_nao_abre_chamado` | **Inverte o enqueue, não a fronteira.** Passa a chamar-se (ou a ter irmão) que verifica: classificar **enfileira** `abrir_chamado_reclamacao`, **não** insere `solicitacao`, **não** envia. O INSERT continua no ramo do worker. |
| `test_pedido_e_reclamacao_nao_enfileiram_responder` | Permanece: reclamação **não** gera `responder_duvida` nem `registrar_pedido_servico`. |
| Unitários de classificar com `duvida_geral` / `pedido_de_servico` | Inalterados no enqueue que já tinham. |
| Indisponível / inválido / upsell / checkout / fora de escopo | **Inalterados** — não enfileiram `abrir_chamado_reclamacao`, salvo o atalho da janela (seção 4). |

Caminho idempotente de classificar (já havia desfecho): se a intenção é
`reclamacao_tecnica` e ainda não existe `abrir_chamado_reclamacao` para aquela
mensagem, **enfileira antes de só concluir**. Mesmo gancho da F3.3 e da F3.4.

**Rationale:** a F3.2 prometeu “decidir, não executar”. Abrir chamado no
classificador quebraria a ordem da confirmação (Artigo VI) e os testes que
proíbem `solicitacao` naquele processador. O padrão já existe duas vezes.

**Alternativas recusadas:** INSERT de `reclamacao` dentro de
`processar_trabalho_classificar_mensagem` — mistura F3.2 e F3.5 e força
mensageria no ramo que a spec da F3.2 proibiu; agendador varrendo reclamação
sem chamado — atraso e peça nova (Artigo XI); allowlist sem ramo (ou o
inverso) — `tipo_desconhecido` queima o gancho.

---

## 2. `abrir_reclamacao` no módulo `atendimento`; worker injeta

**Decisão:** `atendimento` já existe (F3.4) e já é dono de `solicitacao`. Esta
fatia acrescenta `abrir_reclamacao` (e a lista passa a projetar janela +
destaque). `conversa` continua dona de `mensagem` e do envio.

O processador vive em `conversa` e recebe o colaborador por injeção, no padrão
do pedido:

```text
conversa.processar_trabalho_abrir_chamado(
  conexao, trabalho, gateway,
  abrir_reclamacao=atendimento.abrir_reclamacao,
)
```

`conversa` **não** importa `atendimento` e **não** escreve SQL em `solicitacao`.
`atendimento` **não** importa `conversa` e **não** envia mensagem. O worker
orquestra. Sem ciclo.

Ordem na mesma transação, **antes** do envio:

1. Inserir `mensagem` `enviada` com o recado padrão (confirmação + pergunta de
   horário só se a janela ainda for desconhecida).
2. `abrir_reclamacao` — INSERT `solicitacao` tipo `reclamacao`.
3. Atualizar o JSON da **recebida**: `resposta = confirmacao_reclamacao`,
   `id_mensagem_resposta`, `id_solicitacao`. `desfecho` permanece `classificado`.
4. `enviar_texto_sessao`.

Passo 1 acontece antes do passo 2 na transação: nunca existe `solicitacao` desta
origem sem a confirmação já gravada (Artigo VI). Os dois commitam juntos; o envio
é depois (Artigo III). Falha ao gravar desfaz os dois. Falha ao enviar preserva
os dois e reagenda só a mensageria.

`abrir_servico` **não** muda de contrato. Repositório ganha `inserir_reclamacao`
(com `janela_preferencia`); não se generaliza `inserir_servico` só para evitar
duas linhas de INSERT (Artigo XI).

**Rationale:** fronteira de módulo; Artigo VI e III; FR-001, FR-005, FR-006.
Teste unitário de `conversa` injeta um `abrir_reclamacao` falso e verifica a
ordem. Teste de `atendimento` não conhece HTTP nem mensageria.

**Alternativas recusadas:** reusar `abrir_servico` com `tipo` na API pública —
muda o contrato da F3.4 sem ganho de teste; `conversa` INSERT em `solicitacao`
— fura a fronteira; criar o chamado só depois do envio ok — contradiz FR-017;
módulo novo além de `atendimento` — Artigo XI.

---

## 3. Sem LLM novo; descrição = conteúdo; quarto reutilizado; janela por função pura

**Decisão:** nenhum método novo em `LLMProvider`. A descrição é o `conteudo` da
recebida. O quarto reutiliza `extrair_numero_quarto` da F3.4. A janela é
`extrair_janela_preferencia` (função pura em `atendimento`, arquivo próprio):
padrões explícitos de horário e período, casefold, primeiro match, no máximo 60
caracteres (teto do campo já existente). Sem match → `janela_preferencia` nula.
**Nunca** completa a partir de agenda da manutenção, de outra reserva ou de
outro hotel.

Não há busca no catálogo. Reclamação não passa por `responder_duvida`.

**Rationale:** FR-001, FR-002, FR-007, FR-021; Artigo I e XI. Um passo de IA só
para o horário pagaria rede por um campo que o modelo já admite nulo. Limitação
honesta (Artigo XV): “pode ser no fim da tarde, depois do almoço” sem padrão
cai na User Story 4 (chamado visível sem janela).

**Alternativas recusadas:** `LLMProvider.extrair_janela` — peça nova sem problema
que regex + janela opcional não cubra; recusar o chamado sem quarto ou sem
janela — silêncio ao hóspede, viola Artigo VI.

---

## 4. Resposta de horário não espera para abrir e não vira segundo chamado

**Decisão:** o chamado **abre na confirmação**, com ou sem janela. Esperar a
resposta para tramitar deixaria o recado invisível se o hóspede não respondesse
(Artigos V e VI).

A resposta posterior de horário **não** é um tipo de trabalho novo. Entra no
processador de `classificar_mensagem`, **antes** de chamar o LLM, por injeção:

```text
conversa.processar_trabalho_classificar_mensagem(
  ...,
  enfileirar_chamado=fila.enfileirar_abrir_chamado_reclamacao,
  completar_janela=atendimento.completar_janela_se_resposta,
)
```

Regra, nesta ordem:

1. Se a reserva tem reclamação `aberta`/`em_andamento` **sem** janela **e** o
   texto `parece_resposta_de_horario` → `completar_janela` naquela solicitação
   (a mais antiga sem janela da reserva), grava na **nova** recebida
   `desfecho = janela_registrada` + `id_solicitacao`, **não** chama o LLM,
   **não** envia recado, **não** abre segundo chamado, conclui o trabalho de
   classificar.
2. Senão, classifica como hoje. `reclamacao_tecnica` enfileira
   `abrir_chamado_reclamacao` (chamado próprio, mesmo que já exista outro
   aberto). Demais intenções inalteradas.

`parece_resposta_de_horario` é função pura: a mensagem **inteira** parece só um
horário ou período (ex.: `14h`, `depois das 16h`, `de manha`). Texto que mistura
problema novo (`o chuveiro tambem vazou`) **não** casa — vai ao classificador e
pode abrir chamado próprio.

Completar janela **não** reenvia a confirmação de acionamento (Artigo VII).

**Rationale:** FR-007, FR-008, FR-009. Sem estado conversacional novo além da
própria `solicitacao` (janela nula = ainda esperando). Sem tipo de trabalho
extra (Artigo XI). Sem LLM numa resposta de três caracteres.

**Alternativas recusadas:** esperar a janela para INSERT da `solicitacao` —
hóspede no silêncio e chamado invisível se ninguém responder; tipo
`registrar_janela_preferencia` na fila — terceira peça para um UPDATE; classificar
`14h` como `fora_de_escopo` e ligar `precisa_atendimento_humano` — treina a
recepção a tratar a resposta que **nós** pedimos como chamado humano; ack
“anotamos seu horário” — segunda mensagem sem necessidade (parcial da ficha já
ensinou a não responder de novo).

---

## 5. Recado padrão com pergunta condicional; `enviar_texto_sessao` reutilizado

**Decisão:** função pura `montar_confirmacao_reclamacao(*, nome_completo,
perguntar_horario: bool)`. Prenome + “recebemos; a manutenção está sendo
acionada”. Se `perguntar_horario` (janela extraída nula), acrescenta a pergunta
pelo horário de preferência **no mesmo recado**. Se a origem já tinha janela,
não pergunta de novo. Sai por `enviar_texto_sessao`. Nenhum método novo na porta.

Não vai para `parametro_hotel`: é recado operacional fixo, como a confirmação
do pedido e o aviso de dúvida.

**Rationale:** FR-004, FR-007; Artigo VII (um recado, não dois; não inicia
conversa proativa). F3.3 já pagou o método de sessão.

**Alternativas recusadas:** duas mensagens (confirmação, depois pergunta) —
intrusivo e dois envios para falhar; template Utility — o hóspede acabou de
escrever; copy em `parametro_hotel` — Artigo XIII pede prazo, não frase de
balcão neste caso (precedente F3.3/F3.4).

---

## 6. `solicitacao` tipo `reclamacao`; Alert Center é o `GET /solicitacoes` da F3.4

**Decisão:** INSERT com `tipo = 'reclamacao'`, `status = 'aberta'`, `urgencia`
copiada da mensagem (se ausente, `media`), `janela_preferencia` extraída ou
nula, `id_usuario_responsavel` nulo, `id_mensagem_origem` = a recebida. **Zero**
linha em `consumo`.

A fila **não** entra em `vw_fila_do_dia` e **não** liga
`precisa_atendimento_humano`. Manutenção lê `GET /solicitacoes`. A recepção
recupera o mesmo item ali. Dúvida não coberta (F3.3) continua sendo o flag da
fila do dia — os dois sinais não se misturam.

Unicidade: `uq_solicitacao_mensagem_origem` **já existe** (F3.4). Reprocessar a
mesma origem não cria segundo chamado. Hotel por `reserva.id_hotel`. Sem coluna
`id_hotel` em `solicitacao`.

`GET /solicitacoes` **não** ganha rota nova. O item ganha dois campos:

| Campo | Origem |
| --- | --- |
| `janela_preferencia` | coluna já existente (nula em serviço da F3.4) |
| `destaque_tempo_excedido` | calculado na listagem; **não** é coluna |

Mesmo JSON para recepção, staff e gestão. Sem ficha.

**Rationale:** FR-003, FR-010–FR-012, FR-014, FR-022; Artigo IV. Sinal humano da
recepção ficou para falha de classificação e dúvida não coberta.

**Alternativas recusadas:** desfecho novo na visão do dia — Alert Center da
recepção para tarefa de manutenção; `consumo` com valor 0; coluna
`destaque_tempo_excedido` persistida — envelhece errado se o prazo da
propriedade mudar.

---

## 7. Destaque por tempo: `horas_destaque_chamado_aberto`

**Decisão:** chave nova em `parametro_hotel`, semeada `2` no bootstrap e na
migração (hotéis já instalados). Só `tipo = 'reclamacao'` recebe o destaque.
Pedido de serviço desta fatia **não** destaca (o critério da spec é o chamado
de manutenção).

`listar_abertas` lê o prazo via serviço de `propriedade` (não SQL direto na
tabela alheia). Compara `aberta_em` com `relogio.agora()` (injetável). Se
`agora - aberta_em` ≥ o prazo **e** o tipo é `reclamacao` →
`destaque_tempo_excedido = true`. Pedido de serviço e reclamação dentro do
prazo → `false`.

Ausência da chave, valor vazio ou não numérico: **nenhum** destaque por limite
inventado; log `prazo_ausente` com `id_hotel` (sem texto da conversa). Não se
usa default no código.

A recepção **não** edita essa chave (parâmetro de comportamento, como
`horas_ate_reenvio`). Sem tela nesta fatia.

**Rationale:** FR-013, Artigo XIII. Dois horas é semente operacional de
manutenção (ar-condicionado parado não espera o dia seguinte); o hotel muda o
valor sem deploy. Teste avança o relógio; não dorme duas horas.

**Alternativas recusadas:** constante `2` no serviço — viola Artigo XIII;
destacar também `servico` — fora da spec; agendador marcando coluna — peça
nova para um booleano derivado.

---

## 8. Idempotência do trabalho e guarda no JSON

**Decisão:** índice único parcial

```sql
CREATE UNIQUE INDEX uq_trabalho_abrir_chamado_reclamacao_mensagem
  ON trabalho ( ((payload->>'id_mensagem')::bigint) )
  WHERE tipo = 'abrir_chamado_reclamacao';
```

No processador: se o JSON da recebida já tem `resposta = confirmacao_reclamacao`
e `id_solicitacao`, **não** insere segunda enviada, **não** chama
`abrir_reclamacao`. Se a enviada ainda está `pendente`, tenta o envio; senão
conclui o trabalho.

Completar janela duas vezes na mesma solicitação: o segundo `completar_janela`
não sobrescreve janela já preenchida (no-op observável).

**Rationale:** FR-015. O índice impede dois trabalhos; o guard impede dois
textos e dois chamados se o claim voltar após gravar.

**Alternativa recusada:** unicidade por reserva — uma estadia pode ter várias
reclamações (User Story 4, último edge: outro problema = outro chamado).

---

## 9. Migração `0013_abrir_chamado_reclamacao`

**Decisão:** SQL congelado em `alembic/versions/sql/0013_abrir_chamado_reclamacao.sql`:

1. `ck_trabalho_tipo` passa a incluir `abrir_chamado_reclamacao`.
2. Índice único `uq_trabalho_abrir_chamado_reclamacao_mensagem`.
3. `INSERT` de `horas_destaque_chamado_aberto = 2` por hotel que ainda não tem
   a chave (mesmo padrão da `0007` / `0008`).
4. Atualizar o `COMMENT ON TABLE parametro_hotel`.

Nenhuma tabela nova. Nenhuma coluna nova em `solicitacao` (`janela_preferencia`
já existe). `vw_fila_do_dia` **não** muda. `downgrade` restaura o CHECK da
`0012`, remove o índice e **não** apaga o parâmetro já semeado (precedente:
downgrade da `0008` não desfaz slots). Atualizar `docs/04-schema.sql` no mesmo
passo.

**Rationale:** Artigo IX. Trigger de `consumo` continua na F3.7.

**Alternativa recusada:** CREATE de coluna de destaque — derivado.

---

## 10. Log: resultado e identificadores; nunca reclamação, confirmação nem janela

**Decisão:** eventos `chamado_aberto`, `chamado_ja_aberto`,
`chamado_envio_falhou`, `janela_registrada`, `prazo_ausente`. Campos:
`id_trabalho`, `id_mensagem`, `id_reserva`, `id_hotel`, `id_solicitacao`,
`resultado` (`aberto` / `ja_aberto` / `envio_falhou` / `janela_registrada` /
`prazo_ausente`). Ausentes: `conteudo`, texto da confirmação, descrição,
telefone, quarto, janela em texto livre.

**Rationale:** FR-018, Artigo VIII.

---

## 11. O que esta pesquisa não reabre

- Taxonomia e desfechos da F3.2 (exceto o enqueue novo e o atalho de janela).
- Conversação / catálogo / `duvida_nao_coberta` (F3.3).
- Pedido de serviço / `abrir_servico` (F3.4) — contrato público permanece.
- Assinatura HMAC do webhook (F3.1).
- Marcar resolvido e avisar conclusão (F3.6).
- Consumo, valor, fila de lançamento (F3.7).
- Pulso e supressão por chamado aberto (F3.8) — esta fatia só garante que o
  chamado exista.
- Quarto na reserva / inventário (Artigo I).
- Adaptador real de IA ou de WhatsApp na suíte.
- Tela React e `GET` de histórico da conversa.
- Ordem estrita entre mensagens (Artigo XV).
- Texto da confirmação como `parametro_hotel`.
- Extração de janela por IA.
