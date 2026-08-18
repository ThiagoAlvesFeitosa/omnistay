# Pesquisa — F3.6 Resolver Chamado e Confirmar

Decisões técnicas tomadas antes de escrever teste. Cada uma traz o que foi escolhido, por
quê, e o que foi recusado. Nada aqui é preferência estética: tudo tem consequência em teste
ou em risco operacional.

---

## 1. Clique HTTP resolve; o worker só envia — padrão da chegada (F2.2)

**Decisão:** `POST /solicitacoes/{id}/resolucao` (corpo vazio) na mesma transação:

1. `UPDATE` da `solicitacao` para `resolvida`, com `id_usuario_responsavel` = quem
   autenticou e `resolvida_em` = agora.
2. `conversa.agendar_confirmacao_resolucao` insere a `mensagem` enviada
   (`status_envio = pendente`) e o trabalho `enviar_confirmacao_resolucao`.

O worker **não** marca resolvido. Só envia o recado já gravado, via
`enviar_texto_sessao` (nenhum método novo na porta). Falha de envio reagenda a
mensageria; **não** reabre a solicitação.

A API **não** chama a porta de mensageria (AGENTS.md: HTTP nunca faz trabalho
demorado). O hóspede é avisado depois da resolução gravada (FR-006, FR-007).

**Rationale:** é o mesmo desenho de `POST /reservas/{id}/chegada` +
`enviar_boas_vindas`. Abrir chamado (F3.4/F3.5) é o inverso — o fato nasce no
worker porque veio do WhatsApp. Aqui o fato nasce no clique humano. Confirmar
antes de gravar avisaria um fechamento inexistente (Artigos III e XV).

**Alternativas recusadas:** resolver e enviar no mesmo request — HTTP espera
rede; worker insere a mensagem **e** resolve — o clique não deixaria prova se o
worker atrasasse, e a passagem de turno continuaria mostrando o item; gravar
só o UPDATE e deixar o worker redigir depois — entre o clique e o claim o
histórico não tem o recado, e um crash antes do INSERT perde o aviso sem
sinalizar (o item já saiu da fila aberta).

---

## 2. `resolver` em `atendimento`; `agendar` em `conversa`; worker orquestra o envio

**Decisão:** `atendimento` é dono do `UPDATE` em `solicitacao`. `conversa` é dona
da mensagem e do enqueue de envio. Fronteira igual à F2.2 (`hospedagem` →
`conversa.agendar_boas_vindas`).

```text
atendimento.resolver(
  conexao, id_hotel, id_solicitacao, id_usuario,
  agendar_confirmacao=conversa.agendar_confirmacao_resolucao,
)

conversa.agendar_confirmacao_resolucao(
  conexao, id_hotel, id_reserva, id_solicitacao, tipo,
)
# lê o prenome do titular (como os outros recados);
# recado padrão segundo o tipo; INSERT enviada; enqueue
```

`conversa` **não** importa `atendimento` e **não** escreve SQL em `solicitacao`.
`atendimento` **não** envia mensagem. O worker chama
`conversa.processar_trabalho_enviar_confirmacao_resolucao` — só porta de envio,
como `enviar_boas_vindas`. Sem ciclo.

Teste unitário de `atendimento` injeta `agendar_confirmacao` falso: verifica que
só é chamado depois do UPDATE bem-sucedido, e **não** é chamado na recusa.
Teste de `conversa.agendar` não conhece HTTP. Teste do processador não conhece
`UPDATE` de status.

**Rationale:** FR-001, FR-006, FR-007; fronteira de módulo. Orquestração no
serviço, não no roteador.

**Alternativas recusadas:** roteador chamando os dois serviços — regra no HTTP;
`atendimento` INSERT em `mensagem` — fura a fronteira; `conversa` UPDATE em
`solicitacao` — o inverso; módulo novo — Artigo XI.

---

## 3. Uma rota; operação já existente; serviço **e** reclamação

**Decisão:** liga `resolver_solicitacao` (matriz F0.3: recepção e staff; gestão
**não**). Nenhuma operação nova.

Fecha `tipo IN ('reclamacao', 'servico')` com `status IN ('aberta',
'em_andamento')`. Pedido de toalha não tem fatia posterior para fechar.
`consumo` — ainda inexistente nesta linha — é recusado com `409` se aparecer.

Não há passo `em_andamento`, não há atribuir, não há cancelar. Quem clicou é
quem resolveu (`id_usuario_responsavel` no instante do UPDATE). A coluna já
existe; não se cria `id_usuario_resolvedor`.

`GET /solicitacoes` **não muda o contrato**: já lista só `aberta` /
`em_andamento`. O teste novo é: depois do POST, o item **some** da lista.
Nenhum `GET /solicitacoes/{id}` (Artigo XI). O fato histórico é a linha no
banco e o corpo `200` do POST.

**Rationale:** FR-001, FR-003, FR-004, FR-016, FR-017; spec (assumptions).
`em_andamento` entra no UPDATE porque já é pendência visível na lista; se no
futuro alguém assumir, este clique ainda fecha.

**Alternativas recusadas:** só reclamação — serviço fica aberto para sempre;
`PATCH` genérico de status — gestão ou script mandaria `cancelada`; rota de
atribuir nesta fatia — sem critério de aceite no backlog; `GET` por id —
superfície sem consumidor nesta entrega.

---

## 4. Recusa: `404` esconde o outro hotel; `409` recusa o segundo clique

**Decisão:** o `UPDATE` é condicional (hotel da sessão + tipos desta fatia +
status aberto). Zero linhas:

1. `SELECT` da solicitação **no hotel da sessão**.
2. Se não existe (ou é de outro hotel): `SolicitacaoNaoEncontrada` → **404**
   `"Solicitacao nao encontrada."` — não distingue ausência de alheio.
3. Se existe: `ResolucaoNaoPermitida` → **409** com motivo legível
   (`ja_resolvida`, `tipo_consumo`, `cancelada`, …). Não altera autor nem
   instante. Não agenda recado.

Corrida de dois cliques: `SELECT FOR UPDATE` implícito no `UPDATE` da linha.
O segundo vê status `resolvida` e cai no `409`. Unique do trabalho é rede de
segurança, não o mecanismo principal.

Gestão: `403` pela matriz, **antes** de qualquer `UPDATE`. Sem sessão: `401`.

**Rationale:** FR-008, FR-009, FR-010; contrato de autorização F0.3 (alvo de
outra propriedade é 404). Artigo IX: a aplicação recusa o caminho feliz; o
banco recusa transição inválida.

**Alternativas recusadas:** `200` idempotente no segundo clique — mandaria
segunda confirmação ou mentiria que “agora” resolveu; `404` para já resolvida
no próprio hotel — o profissional que acabou de clicar acharia que o item
sumiu.

---

## 5. Garantias no banco: trigger de transição + CHECK de autor + unique do trabalho

**Decisão:** revisão `0014_resolver_chamado`. Nenhuma tabela nova. Nenhuma
coluna nova.

1. `ck_trabalho_tipo` passa a incluir `enviar_confirmacao_resolucao`.
2. Índice único parcial

   ```sql
   CREATE UNIQUE INDEX uq_trabalho_enviar_confirmacao_resolucao_solicitacao
     ON trabalho ( ((payload->>'id_solicitacao')::bigint) )
     WHERE tipo = 'enviar_confirmacao_resolucao';
   ```

3. Trigger `tg_valida_transicao_solicitacao` (espelho da reserva):
   - mesmo status → no-op
   - `aberta` | `em_andamento` → `resolvida` → ok
   - qualquer outra (inclui `resolvida` → `aberta`, `cancelada`, etc.) →
     rejeita
4. `CHECK (status <> 'resolvida' OR id_usuario_responsavel IS NOT NULL)`
   — já existe o CHECK de `resolvida_em`; falta o autor (FR-002).

`downgrade` restaura o CHECK de tipo da `0013`, remove o índice e o trigger,
**não** afrouxa o CHECK de autor se a coluna já tiver dados (o CHECK novo é
compatível com linhas ainda abertas: responsável nulo só é proibido em
`resolvida`). Atualizar `docs/04-schema.sql` no mesmo passo.

**Rationale:** Artigo IX; FR-002, FR-008. Unique por solicitação, não por
reserva: uma estadia tem vários chamados.

**Alternativas recusadas:** só `UPDATE` na aplicação — script de correção
reabriria; unique por reserva — segundo chamado da mesma estadia não avisaria;
coluna nova de resolvedor — a existente já é o responsável operacional.

---

## 6. Recado padrão por tipo; `enviar_texto_sessao`; janela de 24h é limitação honesta

**Decisão:** função pura `montar_confirmacao_resolucao(*, nome_completo, tipo)`.
Prenome + recado de conclusão. Reclamação: problema atendido / manutenção
concluiu. Serviço: pedido atendido. Proibições testáveis: sem “extrato”, sem
“conta”, sem fato de catálogo, sem prazo de garantia, sem pergunta de horário,
sem inventar o que foi feito no quarto.

Não vai para `parametro_hotel` (precedente F3.3–F3.5: prazo é parâmetro; frase
de balcão desta operação é fixa).

Envio: `enviar_texto_sessao`. **Nenhum template Utility nesta fatia.** O recado
é transacional (ligado a um atendimento existente), não marketing. Se a janela
de sessão já fechou, o envio falha, o chamado **permanece resolvido**, e o
envio é retomado — o mesmo desfecho de qualquer falha de mensageria (FR-013).
Um template Utility dedicado é fatia futura se a demo com atraso de horas
provar o fechamento da janela; não se constrói agora (Artigo XI / XV).

**Rationale:** FR-005, FR-018; Artigo VII (não é reengajamento comercial).

**Alternativas recusadas:** método novo na porta “enviar template” — peça sem
problema presente na suíte (tudo é `MensageriaFalsa`); copy em
`parametro_hotel`; um recado único genérico que não distingue toalha de
ar-condicionado — a spec pede adequação ao tipo.

---

## 7. Idempotência do aviso, não da marcação

**Decisão:** o segundo POST é `409` (seção 4) — **não** há “resolver de novo
em paz”. O retrabalho é só o **envio**:

- Unique impede segundo `trabalho` da mesma solicitação.
- Processador: se a enviada já está `enviada`, conclui; se `pendente` ou
  `falha`, tenta de novo. **Não** insere segunda mensagem.
- `agendar_confirmacao_resolucao` no `IntegrityError` do unique devolve
  `ja_agendada` (espelho das boas-vindas) — só é alcançável em corrida após
  o UPDATE, não no segundo clique do usuário.

A enviada guarda no JSON (sem texto do recado) `tipo = confirmacao_resolucao`
e `id_solicitacao`, para o processador achar a linha pelo payload.

**Rationale:** FR-008, FR-013, User Story 7.

**Alternativa recusada:** POST idempotente que reenvia no segundo clique —
o hóspede receberia dois “já foi atendido”.

---

## 8. Log: resultado e identificadores; nunca descrição nem recado

**Decisão:** eventos `chamado_resolvido`, `resolucao_recusada`,
`resolucao_ja_agendada`, `resolucao_envio_falhou`. Campos: `id_solicitacao`,
`id_reserva`, `id_hotel`, `id_usuario`, `id_trabalho`, `id_mensagem`,
`resultado`. Ausentes: descrição, texto da confirmação, telefone, quarto,
janela, nome.

**Rationale:** FR-014, Artigo VIII.

---

## 9. O que esta pesquisa não reabre

- Classificar / catálogo / pedido / abertura de reclamação (F3.2–F3.5).
- Assinatura HMAC do webhook (F3.1).
- Atribuir responsável em passo separado, `em_andamento` como clique, cancelar.
- Consumo, valor, fila de lançamento (F3.7).
- Pulso e supressão por chamado aberto (F3.8) — resolver **tira** o insumo;
  esta fatia não lê pulso.
- Template Utility de resolução; adaptador real de WhatsApp na suíte.
- Tela React, `GET` de histórico, `GET /solicitacoes/{id}`.
- Tela agregada de passagem de turno (ficha parcial + dia seguinte). A
  passagem de turno **desta** fatia é o `GET /solicitacoes` que já existe.
- Reabrir chamado resolvido.
- Inferência de que o quarto foi atendido sem o clique (Artigo V).
