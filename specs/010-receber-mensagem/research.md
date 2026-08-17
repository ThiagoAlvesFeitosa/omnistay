# Pesquisa — F3.1 Receber Mensagem com Segurança

Decisões técnicas tomadas antes de escrever teste. Cada uma traz o que foi escolhido, por
quê, e o que foi recusado. Nada aqui é preferência estética: tudo tem consequência em teste
ou em risco operacional.

---

## 1. O mesmo `/webhook` da F1.3; nenhum endereço novo

**Decisão:** `GET /webhook` e `POST /webhook` continuam no módulo `conversa`. Esta fatia
estende o `POST`: depois de gravar o evento, se não houver reserva em `aguardando_cadastro`,
tenta reserva `hospedado` e enfileira `classificar_mensagem`.

**Rationale:** a spec exige reusar o canal. Um segundo endpoint duplicaria assinatura,
idempotência e o endereço que o provedor já conhece.

**Alternativas recusadas:** `POST /webhook/estadia` — dois contratos de autenticidade para
manter; receber na API e despachar por módulo via fila interna nova — fila paralela
proibida pela spec e pelo Artigo XI.

---

## 2. Falha fechada: sem segredo, recusa

**Decisão:** o `POST` verifica a assinatura **sempre**, **antes** de parsear efeito de
domínio. Três recusas, todas sem INSERT:

| Condição | HTTP | Efeito |
| --- | --- | --- |
| Cabeçalho de assinatura ausente | `401` | Nada gravado |
| Assinatura não confere | `401` | Nada gravado |
| `WHATSAPP_APP_SECRET` vazio ou ausente | `401` | Nada gravado |

Comparação em tempo constante (`hmac.compare_digest`), HMAC-SHA256 do **corpo cru**,
prefixo `sha256=` — o que a F1.3 já faz quando o segredo existe. Cabeçalhos aceitos:
`X-Hub-Signature-256` e, na suíte, `X-Omnistay-Signature` (já usado).

**Rationale:** FR-003, FR-004, FR-005. O endereço é público (Artefato 5 §11.1). Segredo
vazio hoje **aceita qualquer corpo** (`if cfg.whatsapp_app_secret:` no router). Isso
contraria a spec e deixa a suíte verde com o furo aberto. Fecha-se aqui, não na F3.2.

**Alternativas recusadas:** aceitar sem assinatura em “modo teste” via flag — dois caminhos
de segurança; verificar depois de gravar o evento — o forjado já teria rastro; `403` —
`401` já é o contrato da F1.3 para assinatura inválida.

**Divergência a registrar em `docs/00-ESTADO-DO-PROJETO.md` na implementação:** a F1.3
documentou verificação de assinatura; a execução pulava a checagem sem segredo.

---

## 3. Ordem de resolução: ficha primeiro, estadia depois

**Decisão:** com texto utilizável e telefone canônico:

1. `resolver_reserva_aguardando_cadastro` (F1.3, inalterado) → mensagem + `interpretar_ficha`
2. senão `resolver_reserva_hospedada` (`status = 'hospedado'`, mesmo `id_hotel` e telefone,
   `ORDER BY id_reserva DESC LIMIT 1`) → mensagem + `classificar_mensagem`
3. senão só o `evento_webhook` (`sem_reserva`) — não inventa conversa, não confirma chegada

**Rationale:** FR-013 (F1.3 permanece) e FR-006 (estadia). Uma função de resolução com
`status IN (...)` misturaria os tipos de trabalho.

**Choque aceito:** o mesmo telefone com uma reserva `aguardando_cadastro` e outra
`hospedado` manda a mensagem para a ficha. É o caminho que já existia; não se inventa
desempate por “mais recente check-in”.

**Alternativas recusadas:** só `hospedado` (quebraria a F1.3); inferir check-in se a
reserva estiver em `ficha_recebida` (Artigo I); criar conversa órfã sem reserva.

---

## 4. Tipo `classificar_mensagem`, unicidade por mensagem

**Decisão:** ampliar `ck_trabalho_tipo` com `classificar_mensagem`. Payload só com IDs:
`{id_reserva, id_mensagem, id_evento}`. Índice:

```sql
CREATE UNIQUE INDEX uq_trabalho_classificar_mensagem_mensagem
  ON trabalho ( ((payload->>'id_mensagem')::bigint) )
  WHERE tipo = 'classificar_mensagem';
```

O nome antecipa a F3.2 (o trabalho **é** o gancho de classificar). Não se processa aqui.

**Rationale:** FR-018. Unicidade no banco (Artigo IX), no padrão de `interpretar_ficha`.
A idempotência do reenvio do provedor continua em `evento_webhook.id_externo UNIQUE`; o
índice protege script, retry interno e corrida.

**Alternativas recusadas:** tipo `processar_entrada` — F3.2 teria de migrar o nome;
unicidade só em código — duas passagens simultâneas criariam dois trabalhos; reusar
`interpretar_ficha` para estadia — o worker da F1.3 tentaria extrair ficha de “o ar não
gelou”.

---

## 5. O worker não reclama o tipo novo (allowlist)

**Decisão:** `reclamar_proximo` passa a restringir `tipo` aos despacháveis hoje:

`enviar_coleta`, `interpretar_ficha`, `enviar_lembrete`, `enviar_boas_vindas`.

`classificar_mensagem` permanece `pendente`. O `else` `tipo_desconhecido` → `falha`
continua para lixo real, mas o tipo novo **nunca é reclamado**. A F3.2 acrescenta o nome
à allowlist **e** o ramo no consumidor, no mesmo commit.

**Rationale:** FR-009. Sem o filtro, `ORDER BY id_trabalho` pegaria o item novo e o
consumidor o marcaria `falha` na primeira `--uma-passagem` — a “fila durável” viraria
cinza. Recolocar em `pendente` dentro do `else` criaria loop (o mesmo `id_trabalho` é
sempre o próximo).

**Alternativas recusadas:** ramo no-op que marca `concluido` — a F3.2 não teria o que
consumir; `proxima_tentativa_em` no infinito — F3.2 precisaria limpar o campo; processo
worker separado — Artigo XI.

**Teste obrigatório:** depois do webhook de estadia, uma passagem do worker processa
outros tipos se houver, e o `classificar_mensagem` permanece `pendente` com a mesma
`id_mensagem`.

---

## 6. Thread HTTP sem LLM, sem envio, sem mudança de reserva

**Decisão:** `receber_evento_entrada` não ganha parâmetro `llm` nem `gateway`. Não chama
hospedagem para transicionar status. `intencao` / `sentimento` / `urgencia` permanecem
`NULL`.

**Rationale:** FR-007, FR-016, SC-005, SC-007. Igual à F1.3 no “grava e responde”.

**Alternativa recusada:** classificar “já que a mensagem está na mão” — é a F3.2, e
estouraria o prazo do provedor (Artefato 5 §7).

---

## 7. Envelope de status de entrega não é mensagem de hóspede

**Decisão:** se o JSON for notificação de status (entregue/lida) e não de mensagem, o
`POST` responde `200` **sem** criar `mensagem` nem trabalho. Se houver identificador de
evento extraível, grava `evento_webhook` para o reenvio ser inócuo; senão só `200`.

Payload irreconhecível (nem mensagem, nem status) continua `400` — não é o provedor
falando a língua combinada, e gravar lixo não ajuda o reenvio.

**Rationale:** spec, casos de borda. `400` em status faria o provedor reenviar para
sempre um envelope que nunca virará conversa.

**Alternativa recusada:** tratar `statuses[].id` como `id_externo` de mensagem recebida —
contaminaria o histórico.

---

## 8. Instante de origem, se vier; senão o `now()` do banco

**Decisão:** `mensagem.enviada_em` já existe (`DEFAULT now()`). Se o envelope trouxer
timestamp de origem, o INSERT usa esse instante; senão o default. Sem coluna nova.

**Rationale:** a spec pede preservar o instante para exibição futura e admite que o MVP
não ordena o processamento. `EventoEntrada` ganha campo opcional; o router preenche
quando o envelope Meta-like tiver `timestamp`.

**Alternativa recusada:** coluna `recebida_em` distinta — duas colunas para o mesmo fato
na entrada.

---

## 9. Sem rota nova de histórico; sem operação nova na matriz

**Decisão:** US1 cenário 3 (“recepção consulta o histórico”) é verificado na suíte pela
leitura de `mensagem` no banco. Não nasce `GET /reservas/{id}/mensagens` nesta fatia.
Webhook permanece público (assinatura/token; sem sessão).

**Rationale:** as fatias anteriores (F1.2/F1.3) também não expuseram o histórico por HTTP.
Painel React está fora. Artigo XI.

**Alternativa recusada:** criar a rota “já que a recepção precisa ver” — vira fatia de UI
com política `ler_dado_cadastral` / conteúdo de conversa, e não está nos critérios de
aceite do backlog.

---

## 10. Payload de `evento_webhook` continua sem texto

**Decisão:** o INSERT de evento guarda identificadores e flags (`id_externo`,
`tem_texto_utilizavel`, talvez `tipo_envelope`), **nunca** o corpo da mensagem. O texto
mora só em `mensagem.conteudo` quando há reserva elegível.

**Rationale:** Artigo VIII. O schema comenta o payload como DPC; a F1.3 já não ecoa o
texto. Manter.

**Alternativa recusada:** gravar o JSON cru “para auditoria” — duplica o DPC e aumenta o
risco de log acidental.

---

## 11. Migração `0009_receber_mensagem`

**Decisão:** SQL congelado em `alembic/versions/sql/0009_receber_mensagem.sql`: `DROP` +
`ADD` do `ck_trabalho_tipo` incluindo `classificar_mensagem`; `CREATE UNIQUE INDEX`
parcial. `downgrade` explícito: derruba o índice e restaura o CHECK da `0008`. Atualizar
`docs/04-schema.sql` no mesmo passo. Teste de conformidade nos dois sentidos.

**Rationale:** padrão das revisões `0006`–`0008`. Sem tabela nova.

**Alternativa recusada:** adiar o CHECK e inserir o tipo só na aplicação — o banco
rejeitaria o INSERT.

---

## 12. O que esta pesquisa não reabre

- Porta `MensageriaGateway` / `LLMProvider` (não usadas no POST).
- Máquina de estados da reserva.
- `vw_fila_do_dia`.
- Simulador (F6.2).
- Rate limit do Artefato 5 §11.1.
