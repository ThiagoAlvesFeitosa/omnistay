# Pesquisa — F3.3 Responder Dúvida a partir do Catálogo

Decisões técnicas tomadas antes de escrever teste. Cada uma traz o que foi escolhido, por
quê, e o que foi recusado. Nada aqui é preferência estética: tudo tem consequência em teste
ou em risco operacional.

---

## 1. Tipo `responder_duvida`; allowlist e ramo no mesmo passo

**Decisão:** a classificação **não** responde. Quando `classificar_mensagem` grava
`duvida_geral` + `desfecho = classificado`, enfileira `responder_duvida` na mesma
transação (payload `{id_reserva, id_mensagem}` — a mensagem **recebida**). O worker
ganha o tipo no `ck_trabalho_tipo`, no índice único, na allowlist de `reclamar_proximo`
**e** no ramo `processar_trabalho_responder_duvida` no mesmo commit.

Pedido de serviço e reclamação técnica **não** geram este trabalho (F3.4 / F3.5).

Inventário conhecido que esta fatia mexe:

| Teste atual (F3.2) | Destino nesta fatia |
| --- | --- |
| `test_classificacao_valida_nao_liga_sinal_nem_altera_conteudo` | Uma passagem completa com catálogo vazio (padrão da propriedade) passa a avisar o hóspede e ligar `precisa_atendimento_humano`. Conteúdo da **recebida** continua intocado. O caso “flag falso” exige fato no catálogo (novo teste coberto). |
| Unitários de `processar_trabalho_classificar_mensagem` com `duvida_geral` | Continuam sem envio e sem ler catálogo; passam a deixar `responder_duvida` `pendente`. |
| Indisponível / inválido / upsell / checkout / fora de escopo | **Inalterados** — não enfileiram `responder_duvida`. |

**Rationale:** a F3.2 prometeu “decidir, não executar”. Misturar redação no mesmo
processador quebraria esses testes por acoplamento, não por regressão. O padrão já
existe: webhook enfileira classificar; classificar enfileira responder. Artigo III: o
webhook continua sem LLM de conversação.

Caminho idempotente de classificar (já havia desfecho): se a intenção é `duvida_geral` e
ainda não existe `responder_duvida` para aquela mensagem, **enfileira antes de só
concluir**. Sem isso, crash entre gravar eixos e inserir o trabalho perderia o gancho.

**Alternativas recusadas:** responder dentro de `processar_trabalho_classificar_mensagem`
— mistura F3.2 e F3.3 e força catálogo/mensageria no ramo que a spec da F3.2 proibiu;
agendador varrendo `duvida_geral` sem resposta — atraso e peça nova (Artigo XI);
deixar `responder_duvida` na allowlist sem ramo (ou o inverso) — `tipo_desconhecido`
queima o gancho, o mesmo defeito que a F3.1 evitou.

---

## 2. `LLMProvider.responder_duvida`; catálogo inteiro; fidelidade por trechos

**Decisão:** a porta ganha um terceiro método, ao lado de `extrair_ficha` e
`classificar`. Conversação **não** reusa classificação.

```text
responder_duvida(pergunta, itens_ativos) -> ResultadoResposta
  coberta: bool
  texto: str | None
  trechos_citados: tuple[str, ...]
```

O domínio passa **todos** os itens ativos da propriedade da reserva
(`CatalogoRepository.listar_ativos(id_hotel)`). Não há busca por palavra-chave. Isso é
o ADR já fechado (Artefato 5 §10.2): paráfrase (“desjejum” vs “café da manhã”) não pode
virar escala humana.

Indisponível / recusa / tempo esgotado: `FalhaDeConversacao(codigo)` — distinta de
`FalhaDeClassificacao` e de `FalhaDeExtracao`. Código sem eco do texto.

Catálogo ativo **vazio:** o serviço **não** chama a porta; desfecho de não coberta.
Chamar o modelo sem fatos é convite a inventar.

Fidelidade (User Story 3 / FR-008), função pura em `conversa`:

1. `coberta is False` → não coberta (ignora `texto`).
2. `coberta is True` e (`texto` vazio ou `trechos_citados` vazio) → não fiel → não coberta.
3. Cada trecho, normalizado (`strip` + `casefold`), MUST ser substring de
   `titulo + " " + conteudo` de **algum** item ativo daquele hotel **e** MUST aparecer
   no `texto` enviado.
4. Qualquer trecho fora do catálogo → não fiel → não coberta. O texto **não** é
   enviado.

Não há detector aberto de alucinação. O residual (modelo cita trechos verdadeiros e
ainda acrescenta um fato sem trecho) é o risco que o Artefato 5 §10.3 já aceitou; a
mitigação desta fatia é estrutural (coberta + trechos) e testável com o falso.

**Rationale:** Artigo II e X; FR-002, FR-003, FR-008, FR-017. Teste sem rede.

**Alternativas recusadas:** um único método `classificar` que já devolve resposta —
paga conversação em pedido/reclamação; busca full-text / embedding — ADR recusou;
exigir que o `texto` inteiro seja substring do catálogo — quebra paráfrase, que é o
motivo do catálogo inteiro; flag `inventou` só no falso — o domínio não pegaria o caso
no adaptador real.

---

## 3. Primeira falha de conversação escala; trabalho `concluido`

**Decisão:** `FalhaDeConversacao`, catálogo vazio, `coberta is False` e redação não
fiel seguem o **mesmo** desfecho de pergunta não coberta: aviso padrão + sinal na fila
+ trabalho `responder_duvida` **`concluido`**. Sem retentativa contra o LLM. Sem
`status = falha` nesse caminho.

Falha ao **gravar** aviso/desfecho: a transação desfaz; reclaim por expiração devolve
`pendente` (já existe na fila). Falha ao **enviar** depois de gravar: a mensagem
pendente permanece; o trabalho pode reagendar **envio** (backoff da mensageria, como
coleta). Não abre segundo chamado e não chama o LLM de novo.

**Rationale:** FR-004, FR-009, FR-010, FR-018; Artigo II na primeira ocorrência, Artigo
III na ordem gravar → enviar.

**Alternativas recusadas:** copiar o backoff da ficha contra o LLM — o hóspede da
estadia ficaria sem ninguém olhando; tratar envio falho como “não coberta” extra —
duplicaria chamado sem novo fato.

---

## 4. Aviso padrão; chamado = desfecho `duvida_nao_coberta` na fila do dia

**Decisão:** zero linha em `solicitacao`. O “chamado” da spec é a pendência já visível
à recepção: `classificacao_bruta.desfecho = duvida_nao_coberta` na mensagem recebida,
projetado em `precisa_atendimento_humano` (a visão acrescenta esse valor ao `IN`
existente).

Ordem na mesma transação, **antes** do envio:

1. Inserir `mensagem` `enviada` com o recado padrão (função pura, sem catálogo e sem
   LLM).
2. Atualizar o JSON da **recebida**: `desfecho = duvida_nao_coberta`,
   `resposta = aviso`, `id_mensagem_resposta`.
3. Enviar pela porta de sessão.

Eixos (`intencao` / `sentimento` / `urgencia`) **não** são apagados. `conteudo` da
recebida **não** muda.

Recado padrão (único dado pessoal: prenome, no mesmo padrão do lembrete): informa que
a recepção vai atender. Não completa a lacuna com horário, cardápio ou regra.

Coberto: insere `mensagem` `enviada` com o `texto` fiel, JSON da recebida ganha
`resposta = automatica` e `id_mensagem_resposta`, `desfecho` permanece
`classificado`. Flag humano **não** liga.

**Rationale:** spec FR-005, FR-006, FR-007; Artigo IV e V; “a recepção vai atender”.
`solicitacao` é o chamado operacional com quarto/urgência/janela — F3.5.

**Alternativas recusadas:** `tipo` novo em `solicitacao` (`duvida`) — esquema e Alert
Center sem consumidor operacional; reusar `encaminhado_humano` — mistura “classificador
mandou a humano” com “catálogo não cobriu”, e a F3.2 já usa aquele desfecho sem aviso
ao hóspede; módulo `atendimento` — Artigo XI.

---

## 5. Idempotência: uma resposta observável por mensagem recebida

**Decisão:** índice único parcial

```sql
CREATE UNIQUE INDEX uq_trabalho_responder_duvida_mensagem
  ON trabalho ( ((payload->>'id_mensagem')::bigint) )
  WHERE tipo = 'responder_duvida';
```

No processador: se o JSON da recebida já tem `resposta` ∈ (`automatica`, `aviso`) e
`id_mensagem_resposta`, **não** insere segunda enviada, **não** chama o LLM, **não**
muda desfecho. Se a enviada ainda está `pendente`, tenta o envio; senão conclui o
trabalho.

**Rationale:** FR-013. O índice impede dois trabalhos; o guard no JSON impede dois
textos se o trabalho for reclaimed após gravar.

**Alternativa recusada:** unicidade por reserva — uma estadia tem várias dúvidas.

---

## 6. `MensageriaGateway.enviar_texto_sessao`

**Decisão:** método novo na porta já existente. A resposta (automática ou aviso) sai
como texto de sessão — o hóspede acabou de escrever, a janela de 24h está aberta. Não
é template Utility.

```text
enviar_texto_sessao(telefone_destino, corpo, id_mensagem, id_reserva)
  -> ResultadoEnvio
```

`MensageriaFalsa` registra `tipo=sessao` + `corpo` (observável nos testes). O adaptador
WhatsApp ganha o método (`type: text`) para não quebrar o Protocol; a suíte **não** o
instancia.

Não se reutiliza `enviar_coleta` / `enviar_lembrete` / `enviar_boas_vindas`: cada um é
template com variáveis próprias.

**Rationale:** Artigo X; F2.2 já documentou que catálogo não cabe em variável de
template. FR-011: corpo já está em `mensagem.conteudo` antes da chamada.

---

## 7. `LLMFalso` e `CatalogoFalso` sem quebrar ficha nem classificação

**Decisão:** o mesmo `LLMFalso` ganha `responder_duvida` e configuração **separada**
(`configurar_resposta` / `falhar_conversacao`). `extrair_ficha` e `classificar`
permanecem idênticos.

Padrão ausente de configuração de resposta:

- se `itens_ativos` é vazio → `coberta=False` (o serviço nem deveria chamar; se
  chamar, o falso não inventa);
- se há itens → `coberta=True`, `texto` e `trechos_citados` derivados do **primeiro**
  item (caminho feliz mínimo para não falhar uma passagem por acidente).

Testes de não coberta, não fiel e indisponível configuram explicitamente.

Worker: `catalogo or CatalogoBanco(conexao)` — produção lê o catálogo real na mesma
transação. Testes unitários injetam `CatalogoFalso`. Integração pode semear
`catalogo_item` no banco ou injetar o falso.

**Rationale:** FR-017; um segundo falso só para conversação seria duas portas para a
mesma interface.

---

## 8. Migração `0011_responder_duvida_catalogo`

**Decisão:** SQL congelado em `alembic/versions/sql/0011_responder_duvida_catalogo.sql`:

1. `ck_trabalho_tipo` passa a incluir `responder_duvida`.
2. Índice único `uq_trabalho_responder_duvida_mensagem`.
3. `DROP`/`CREATE` de `vw_fila_do_dia`: o `IN` de `precisa_atendimento_humano` ganha
   `'duvida_nao_coberta'`.

Nenhuma tabela nova, nenhuma coluna nova em `mensagem`. `downgrade` restaura o CHECK /
índice / visão da `0010`. Atualizar `docs/04-schema.sql` no mesmo passo. Teste de
conformidade nos dois sentidos.

**Rationale:** o sinal humano já é coluna derivada; o fato novo é mais um desfecho no
JSON. Artigo IX: unicidade do trabalho no banco.

**Alternativa recusada:** coluna `precisa_atendimento_humano` persistida em `reserva`.

---

## 9. Módulo `conversa` responde; `hospedagem` só projeta a fila

**Decisão:** `processar_trabalho_responder_duvida` vive em `conversa` (dona de
`mensagem` e do envio). Lê catálogo **só** pela porta. Worker injeta `llm`, `gateway` e
`catalogo`. **Não** chama `hospedagem` no ramo (reserva não muda). `hospedagem` só
continua a ler `precisa_atendimento_humano` da visão — o contrato HTTP do item não
muda de forma, só a regra SQL por trás do booleano.

Classificar **não** recebe catálogo nem gateway. Continua o processador da F3.2, com o
único acréscimo de enfileirar.

Hotel B: `listar_ativos(id_hotel)` do trabalho; mensagem e sinal gravados com esse
hotel. Catálogo de A não entra no prompt de B.

**Rationale:** fronteira já usada; Artigo XIV; Artigo X.

**Alternativa recusada:** `propriedade.service` chamado de `conversa` para listar
itens — fura a porta que a F2.1 criou exatamente para F3.3.

---

## 10. HTTP: zero rota nova; webhook intocado

**Decisão:** `POST /webhook` permanece o da F3.1. Responder é só worker. A recepção vê
o chamado em `GET /fila-do-dia` (mesmo booleano). Histórico HTTP continua fora; a suíte
lê `mensagem` no banco.

**Rationale:** Artigo XI; critério de pronto da spec.

---

## 11. Log: resultado e identificadores; nunca pergunta, resposta ou catálogo

**Decisão:** eventos `duvida_respondida`, `duvida_nao_coberta`,
`conversacao_indisponivel`, `resposta_nao_fiel`, `duvida_ja_respondida`. Campos:
`id_trabalho`, `id_mensagem`, `id_reserva`, `id_hotel`, `resultado`
(`automatica` / `aviso` / `nao_fiel` / `indisponivel` / `catalogo_vazio`). Ausentes:
`conteudo` da pergunta, texto enviado, título/conteúdo de item, `trechos_citados`,
telefone.

**Rationale:** FR-014, Artigo VIII. “Pergunta coberta ou não” é o que a constituição
autoriza no lugar do texto.

---

## 12. O que esta pesquisa não reabre

- Taxonomia e desfechos da F3.2 (`classificado`, `encaminhado_humano`,
  `formato_invalido`, `indisponivel`).
- Assinatura HMAC / falha fechada do webhook (F3.1).
- `solicitacao` / Alert Center / janela de preferência (F3.5).
- Pedido de serviço com confirmação (F3.4).
- Preço estruturado / consumo (F3.7).
- Busca semântica no catálogo (gatilho do ADR: catálogo que não cabe no prompt).
- Adaptador real de provedor de IA na suíte.
- Tela React e `GET` de histórico.
- Ordem estrita entre mensagens (Artigo XV).
- Texto do aviso como `parametro_hotel` — é recado operacional fixo, como o lembrete;
  Artigo XIII cobre prazo, não copy.
