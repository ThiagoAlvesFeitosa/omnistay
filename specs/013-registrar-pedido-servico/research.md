# Pesquisa — F3.4 Registrar Pedido de Serviço

Decisões técnicas tomadas antes de escrever teste. Cada uma traz o que foi escolhido, por
quê, e o que foi recusado. Nada aqui é preferência estética: tudo tem consequência em teste
ou em risco operacional.

---

## 1. Tipo `registrar_pedido_servico`; allowlist e ramo no mesmo passo

**Decisão:** a classificação **não** confirma e **não** abre solicitação. Quando
`classificar_mensagem` grava `pedido_de_servico` + `desfecho = classificado`,
enfileira `registrar_pedido_servico` na mesma transação (payload
`{id_reserva, id_mensagem}` — a mensagem **recebida**). O worker ganha o tipo no
`ck_trabalho_tipo`, no índice único, na allowlist de `reclamar_proximo` **e** no ramo
`processar_trabalho_registrar_pedido` no mesmo commit.

Dúvida geral continua enfileirando só `responder_duvida`. Reclamação técnica **não**
gera este trabalho (F3.5).

Inventário conhecido que esta fatia mexe:

| Teste atual | Destino nesta fatia |
| --- | --- |
| `test_pedido_e_reclamacao_nao_enfileiram_responder` | Permanece: pedido **não** gera `responder_duvida`. Passa a ter teste irmão: pedido enfileira `registrar_pedido_servico` sem envio e sem `solicitacao`. |
| `test_reclamacao_nao_abre_chamado` | Inalterado. |
| Unitários de classificar com `duvida_geral` | Inalterados (continuam enfileirando só resposta). |
| Passagem completa com `pedido_de_servico` (hoje inexistente ou implícita “zero enviada”) | Nova: confirmação + uma `solicitacao` tipo `servico`. |
| Indisponível / inválido / upsell / checkout / fora de escopo / dúvida | **Inalterados** — não enfileiram `registrar_pedido_servico`. |

Caminho idempotente de classificar (já havia desfecho): se a intenção é
`pedido_de_servico` e ainda não existe `registrar_pedido_servico` para aquela
mensagem, **enfileira antes de só concluir**. Mesmo gancho da F3.3 para dúvida.

**Rationale:** a F3.2 prometeu “decidir, não executar”. Confirmar e gravar
`solicitacao` no classificador quebraria esses testes por acoplamento. O padrão já
existe: classificar enfileira o ramo. Artigo III: o webhook continua sem este
trabalho.

**Alternativas recusadas:** abrir solicitação dentro de
`processar_trabalho_classificar_mensagem` — mistura F3.2 e F3.4 e força mensageria no
ramo que a spec da F3.2 proibiu; agendador varrendo `pedido_de_servico` sem
solicitação — atraso e peça nova (Artigo XI); allowlist sem ramo (ou o inverso) —
`tipo_desconhecido` queima o gancho.

---

## 2. Módulo `atendimento` nasce; worker injeta `abrir_servico`

**Decisão:** esta fatia é a primeira a escrever `solicitacao`. O módulo `atendimento`
previsto na arquitetura (dona de `solicitacao` e, depois, `consumo`) passa a existir
mínimo: `abrir_servico` e `listar_abertas`. `conversa` continua dona de `mensagem` e
do envio.

O processador vive em `conversa` e recebe o colaborador por injeção, no padrão da
ficha (`consolidar=hospedagem.consolidar_ficha_titular`):

```text
conversa.processar_trabalho_registrar_pedido(
  conexao, trabalho, gateway,
  abrir_servico=atendimento.abrir_servico,
)
```

`conversa` **não** importa `atendimento` e **não** escreve SQL em `solicitacao`.
`atendimento` **não** importa `conversa` e **não** envia mensagem. O worker
orquestra. Sem ciclo.

Ordem na mesma transação, **antes** do envio:

1. Inserir `mensagem` `enviada` com o recado padrão de confirmação (função pura).
2. `abrir_servico` — INSERT `solicitacao` tipo `servico`.
3. Atualizar o JSON da **recebida**: `resposta = confirmacao_pedido`,
   `id_mensagem_resposta`, `id_solicitacao`. `desfecho` permanece `classificado`.
4. `enviar_texto_sessao`.

Passo 1 acontece antes do passo 2 na transação: nunca existe `solicitacao` desta
origem sem a confirmação já gravada (Artigo VI). Os dois commitam juntos; o envio é
depois (Artigo III). Falha ao gravar desfaz os dois. Falha ao enviar preserva os
dois e reagenda só a mensageria.

**Rationale:** fronteira de módulo (AGENTS.md); Artigo VI e III; FR-001, FR-005,
FR-006. Teste unitário de `conversa` injeta um `abrir_servico` falso e verifica a
ordem (confirmação gravada, depois a chamada). Teste de `atendimento` não conhece
HTTP nem mensageria.

**Alternativas recusadas:** `conversa` INSERT em `solicitacao` — fura a fronteira no
primeiro uso da tabela; `atendimento` enviar a confirmação — módulo de chamado
passaria a conhecer WhatsApp; criar `solicitacao` só depois do envio ok — contradiz
FR-013 (pedido some se a mensageria falhar); módulo novo além de `atendimento`
(fila operacional paralela) — Artigo XI.

---

## 3. Sem LLM novo; descrição = conteúdo; quarto por função pura

**Decisão:** nenhum método novo em `LLMProvider`. A descrição da solicitação é o
`conteudo` da mensagem recebida (o que o hóspede pediu). O quarto é extraído por
função pura em `atendimento` (`extrair_numero_quarto`): padrões explícitos
(`quarto`, `apto`, `apartamento`, `uh` + número), casefold, primeiro match, no
máximo 10 caracteres. Sem match → `numero_quarto` nulo. **Nunca** completa a partir
de inventário, de outra reserva ou de outro hotel.

Não há busca no catálogo. Pedido de toalha não passa por `responder_duvida`.

**Rationale:** FR-001, FR-002, FR-017 da spec de verificação sem rede; Artigo I e
XI. Um segundo passo de extração por IA só para o quarto pagaria rede e falso extra
por um campo que o modelo de dados já admite nulo. “Estou no 402” sem a palavra
quarto cai na User Story 4 (pendência visível sem quarto) — limitação honesta
(Artigo XV).

**Alternativas recusadas:** `LLMProvider.extrair_pedido` — peça nova sem problema
que regex + quarto opcional não cubra; gravar o quarto na reserva no check-in —
escopo da F2.2, já fechada sem esse campo; recusar o pedido sem quarto — silêncio
ao hóspede, viola Artigo VI.

---

## 4. Confirmação padrão; `enviar_texto_sessao` reutilizado

**Decisão:** recado padrão (função pura em `conversa`, espírito de
`texto_aviso_duvida`): prenome + “recebemos seu pedido; a equipe vai atender”. Sem
prazo, sem fato de catálogo, sem pergunta de janela de preferência. Sai pela porta
já existente `enviar_texto_sessao` (janela de sessão aberta). Nenhum método novo na
porta de mensageria.

**Rationale:** FR-004; Artigo VII (não inicia conversa proativa); F3.3 já pagou o
método de sessão. Artigo XIII não pede copy em `parametro_hotel` — é recado
operacional fixo, como o lembrete.

**Alternativas recusadas:** template Utility — o hóspede acabou de escrever; novo
método na porta só para mudar o nome — Artigo XI.

---

## 5. `solicitacao` tipo `servico`; zero `consumo`; fila HTTP, não visão do dia

**Decisão:** INSERT em `solicitacao` com `tipo = 'servico'`, `status = 'aberta'`,
`urgencia` copiada da mensagem (eixo da F3.2; se ausente, `media`),
`janela_preferencia` nula, `id_usuario_responsavel` nulo, `id_mensagem_origem` = a
recebida, `id_reserva` do trabalho. **Zero** linha em `consumo`.

A fila da equipe **não** entra em `vw_fila_do_dia` e **não** liga
`precisa_atendimento_humano`. Toalha não é “recepção precisa falar com o hóspede”;
é tarefa da equipe operacional. A recepção recupera o mesmo item em
`GET /solicitacoes`.

Unicidade no banco:

```sql
CREATE UNIQUE INDEX uq_solicitacao_mensagem_origem
  ON solicitacao (id_mensagem_origem)
  WHERE id_mensagem_origem IS NOT NULL;
```

Mais o índice do trabalho (seção 6). Reprocessar a mesma mensagem não cria segunda
solicitação (IntegrityError no INSERT; o processador trata como já registrado).

Hotel: `abrir_servico` e `listar_abertas` filtram por `reserva.id_hotel` do
trabalho/sessão. `solicitacao` continua sem coluna `id_hotel` (esquema da F0.2:
entidades sob a reserva herdam o hotel por join, como `mensagem`). Não se
reabre essa denormalização aqui.

**Rationale:** FR-003, FR-007, FR-010, FR-011, FR-015; Artigo IV (fila própria,
não notificação); Artigo IX (UNIQUE da origem). Sinal humano da recepção ficou
para falha de classificação e dúvida não coberta — misturar toalha ali treinaria
a recepção a ignorar o flag (risco do Artefato 2 R5).

**Alternativas recusadas:** desfecho novo na visão do dia — Alert Center da
recepção para tarefa de governança; criar `consumo` com valor 0 — inventa
faturamento e polui a lista do checkout; coluna `id_hotel` em `solicitacao` nesta
fatia — migração em tabela ainda virgem só para evitar um JOIN que `mensagem` já
faz.

---

## 6. Idempotência do trabalho e guarda no JSON

**Decisão:** índice único parcial

```sql
CREATE UNIQUE INDEX uq_trabalho_registrar_pedido_servico_mensagem
  ON trabalho ( ((payload->>'id_mensagem')::bigint) )
  WHERE tipo = 'registrar_pedido_servico';
```

No processador: se o JSON da recebida já tem `resposta = confirmacao_pedido` e
`id_solicitacao`, **não** insere segunda enviada, **não** chama `abrir_servico`.
Se a enviada ainda está `pendente`, tenta o envio; senão conclui o trabalho.

**Rationale:** FR-011. O índice impede dois trabalhos; o guard impede dois textos
e duas solicitações se o claim voltar após gravar.

**Alternativa recusada:** unicidade por reserva — uma estadia tem vários pedidos.

---

## 7. `GET /solicitacoes` liga `ler_solicitacao_atribuida`; sem ficha

**Decisão:** primeira rota do módulo `atendimento`. Lista solicitações `aberta` e
`em_andamento` da propriedade da sessão, qualquer `tipo` (esta fatia só cria
`servico`; reclamação passará a aparecer na F3.5 sem mudar o contrato).

Corpo do item: `id_solicitacao`, `id_reserva`, `tipo`, `descricao`,
`numero_quarto`, `urgencia`, `status`, `aberta_em`. **Ausentes:** nome, telefone,
documento, endereço, conteúdo extra da ficha. O mesmo JSON para recepção, staff e
gestão — a proteção cadastral não depende de o roteador ramificar por perfil.

`id_reserva` não é ficha: staff **não** tem `ler_ficha_de_hospede` /
`ler_dado_cadastral_de_hospede`; `GET /reservas/{id}/ficha` continua 403.

Coleção de outro hotel: a consulta filtra `id_hotel` da sessão, devolve lista
vazia — não 404 em coleção. Sem cookie: 401. Operação já está na matriz desde a
F0.3; esta fatia só liga a rota. Nenhuma operação nova.

Sem `GET /solicitacoes/{id}` e sem POST de atribuição/resolução (F3.6).

**Rationale:** FR-007, FR-008, FR-009; sessão longa do staff só é aceitável se o
dispositivo não alcança ficha (F0.3). Critério de pronto da spec: fila observável;
tela React fora.

**Alternativas recusadas:** reusar `GET /fila-do-dia` — carrega nome e telefone, e
staff é recusado nessa operação de propósito; payload diferente por perfil — dois
contratos para o mesmo recurso, e um vazamento no “ramo recepção” contaminaria o
teste do staff; React nesta fatia.

---

## 8. Migração `0012_registrar_pedido_servico`

**Decisão:** SQL congelado em `alembic/versions/sql/0012_registrar_pedido_servico.sql`:

1. `ck_trabalho_tipo` passa a incluir `registrar_pedido_servico`.
2. Índice único `uq_trabalho_registrar_pedido_servico_mensagem`.
3. Índice único `uq_solicitacao_mensagem_origem`.

Tabela `solicitacao` **já existe** (revisão `0001`). Nenhuma coluna nova.
`vw_fila_do_dia` **não** muda. `downgrade` restaura o CHECK da `0011` e remove os
dois índices. Atualizar `docs/04-schema.sql` no mesmo passo. Teste de conformidade
nos dois sentidos + teste da unicidade da origem.

**Rationale:** Artigo IX. Trigger “`consumo` só se `tipo = consumo`” fica para a
F3.7, quando a tabela filha passa a ser escrita — nesta fatia o teste já exige
zero `consumo`.

**Alternativa recusada:** CREATE da tabela nesta revisão — ela já está no esquema
inicial.

---

## 9. Log: resultado e identificadores; nunca pedido nem confirmação

**Decisão:** eventos `pedido_registrado`, `pedido_ja_registrado`,
`pedido_envio_falhou`. Campos: `id_trabalho`, `id_mensagem`, `id_reserva`,
`id_hotel`, `id_solicitacao`, `resultado`
(`registrado` / `ja_registrado` / `envio_falhou`). Ausentes: `conteudo` da
recebida, texto da confirmação, descrição, telefone, quarto como se fosse dado
pessoal de ficha (o quarto na solicitação é operacional; **também não** vai para
log — identificadores bastam).

**Rationale:** FR-014, Artigo VIII.

---

## 10. O que esta pesquisa não reabre

- Taxonomia e desfechos da F3.2.
- Conversação / catálogo / `duvida_nao_coberta` (F3.3).
- Assinatura HMAC do webhook (F3.1).
- Chamado de reclamação, janela de preferência, Alert Center de manutenção (F3.5).
- Marcar resolvido e avisar conclusão (F3.6).
- Consumo, valor, fila de lançamento, preço no catálogo (F3.7).
- Quarto na reserva / inventário (Artigo I).
- Adaptador real de IA ou de WhatsApp na suíte.
- Tela React e `GET` de histórico da conversa.
- Ordem estrita entre mensagens (Artigo XV).
- Texto da confirmação como `parametro_hotel`.
