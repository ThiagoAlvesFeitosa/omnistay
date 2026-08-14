# Fase 0 — Pesquisa e decisões técnicas: Receber e Interpretar a Ficha

Cada seção registra a decisão, por que ela foi tomada e o que foi rejeitado.

---

## 1. Webhook grava evento + mensagem + trabalho; interpreta depois

**Decisão**: `POST /webhook` (e o desafio `GET` de verificação) pertencem ao módulo
`conversa`. Em **uma transação**:

1. Insere `evento_webhook` com `id_externo` do provedor.
2. Se houver texto utilizável e reserva resolvida em `aguardando_cadastro`, insere
   `mensagem` (`direcao = recebida`) e `trabalho` (`tipo = interpretar_ficha`).
3. `COMMIT` e responde `200` **sem** chamar o LLM.

Se `id_externo` já existir (`UNIQUE`), responde `200` sem novo efeito (idempotência).

**Rationale**: Artigo III e Artefato 5 §7 — o webhook precisa responder rápido; IA é
trabalho demorado. Idempotência no banco (Artigo IX), não só em memória. Mesmo padrão
estrutural da F1.2 (gravar intenção durável + worker).

**Alternativas consideradas**:

- **Interpretar na requisição HTTP**: estoura prazo do provedor e acopla a API à IA.
- **Só gravar `evento_webhook` e deixar outro job varrer**: atrasa a mensagem no histórico e
  complica a correlação; rejeitado em favor de mensagem + trabalho na mesma TX.
- **BackgroundTasks na API**: Artefato 5 já rejeitou — reinício perde trabalho sem rastro.

---

## 2. Porta `LLMProvider` + implementação falsa obrigatória

**Decisão**: criar `app/portas/llm.py` com protocolo mínimo para esta fatia, por exemplo
`extrair_ficha(texto: str) -> ResultadoExtracao`, onde o resultado traz campos opcionais
(sem idade), lista de campos reconhecidos e desfecho
(`completa` | `parcial` | `irreconhecivel`) ou sinal de falha/indisponibilidade.

`LLMFalso` devolve desfechos fixos configuráveis pelo teste. Nenhum teste chama provedor
real. Adaptador real fica fora do critério de pronto da suíte (paridade com
`MensageriaFalsa` na F1.2).

**Rationale**: Artigo X — domínio não conhece implementação. Artigo II — falha do extrator
escala para humano, nunca inventa ficha.

**Alternatives considered**:

- **Parser regex-only sem porta**: quebra com paráfrase e impede trocar o extrator; a porta
  ainda permite um adaptador “heurístico” nos testes se quiser, mas o domínio depende da
  interface.
- **Chamar LLM real nos testes**: proibido pelas regras do projeto.

---

## 3. Worker orquestra; sem ciclo `conversa` ↔ `hospedagem`

**Decisão**:

| Camada | Responsabilidade |
| --- | --- |
| `conversa` | Webhook, `evento_webhook`, mensagem recebida, chamar `LLMProvider`, gravar `classificacao_bruta`, **não** atualizar `hospede`/`reserva.status` |
| `hospedagem` | Atualizar titular (`hospede`), `reserva_hospede.ficha_completa`, `reserva.status` |
| `worker` | Claim `interpretar_ficha` → pede extração a `conversa` → pede consolidação a `hospedagem` → conclui trabalho |

**Rationale**: `hospedagem` já importa `conversa` para agendar coleta. Se `conversa`
importasse `hospedagem`, nasceria o ciclo que a F0.3 proibiu resolver com import local.

**Alternativas consideradas**:

- **Tudo em `conversa`**: viola fronteira de tabelas (`hospede`/`reserva` são de hospedagem).
- **Tudo em `hospedagem`**: webhook e `evento_webhook` são de `conversa` (Artefato 5).
- **Import local para quebrar ciclo**: rejeitado na F0.3.

---

## 4. Desfechos: completo, parcial, irreconhecível, falha do extrator

**Decisão**:

| Desfecho | Campos gravados | `ficha_completa` | `reserva.status` | Mensagem ao hóspede |
| --- | --- | --- | --- | --- |
| Completa | Todos os 9 utilizáveis | `true` | `ficha_recebida` | Nenhuma |
| Parcial | Subconjunto utilizável | `false` | `ficha_parcial` | Nenhuma |
| Irreconhecível | Nenhum inventado | permanece `false` | permanece `aguardando_cadastro` | Nenhuma |
| Falha/indisponibilidade do LLM | Nenhum inventado | permanece `false` | permanece `aguardando_cadastro` | Nenhuma |

Campos com formato inválido (data impossível, tipo de documento fora do domínio) **não**
contam como reconhecidos utilizáveis.

Mídia sem texto / foto de documento: tratada como irreconhecível para fins de ficha (FR-010).

**Rationale**: máquina de estados já admite `ficha_recebida` / `ficha_parcial` a partir de
`aguardando_cadastro`. Irreconhecível não ganha quinto status (assumption da spec); o
sinal operacional é separado (§5).

**Alternativas consideradas**:

- **Irreconhecível → `ficha_parcial` vazia**: polui o status “parcial” (que implica “veio
  algo útil”) e atrapalha a fila.
- **Pedir reenvio automático**: viola FR-006 / Artigo VII.

---

## 5. Sinal “leitura humana” e `estado_cadastro` na fila do dia

**Decisão**: persistir o resultado da tentativa em `mensagem.classificacao_bruta` (JSONB),
por exemplo:

```json
{
  "tipo": "extracao_ficha",
  "desfecho": "irreconhecivel",
  "campos_reconhecidos": []
}
```

Expor na fila do dia o campo derivado **`estado_cadastro`**:

| Valor | Regra |
| --- | --- |
| `completa` | `reserva.status = ficha_recebida` |
| `parcial` | `reserva.status = ficha_parcial` |
| `leitura_humana` | `status = aguardando_cadastro` e existe mensagem recebida com desfecho `irreconhecivel` ou `falha_extrator` |
| `aguardando` | `status = aguardando_cadastro` sem esse sinal |

Implementação preferível: coluna (ou expressão) na `vw_fila_do_dia` + campo em
`ItemFilaDoDia`, para a recepção distinguir os quatro desfechos sem JOIN ad hoc no router.

Não reutilizar `mensagem.intencao` para isso: o `CHECK` atual é de intenções de atendimento
(F3), não de extração de ficha.

**Rationale**: FR-011 / SC-007; Artigo IV/V — pendência humana visível na fila.

**Alternativas consideradas**:

- **Novo status `aguardando_leitura`**: migração de máquina de estados + trigger; a spec
  pediu evitar quinto status.
- **Só `ficha_completa` booleano**: não distingue aguardando vs leitura humana.

---

## 6. Tipo de trabalho `interpretar_ficha` e unicidade

**Decisão**: ampliar `ck_trabalho_tipo` para `('enviar_coleta', 'interpretar_ficha')`.
Payload mínimo: `{ "id_reserva", "id_mensagem", "id_evento" }` — só identificadores.

Índice único parcial:

```sql
UNIQUE ( ((payload->>'id_mensagem')::bigint) )
  WHERE tipo = 'interpretar_ficha'
```

Garante no máximo um trabalho de interpretação por mensagem de entrada. Retries do worker
reatualizam o mesmo trabalho; reenvio do webhook nem chega a criar segundo (UNIQUE do
evento).

**Rationale**: Artigo IX; simetria com `uq_trabalho_enviar_coleta_reserva`.

---

## 7. Resolução da reserva pelo telefone

**Decisão**: normalizar o número de origem com `app.comum.telefone.normalizar` e buscar
reserva do hotel em `aguardando_cadastro` com `telefone_contato` igual. No MVP, o número de
negócio do WhatsApp mapeia para **um** `id_hotel` (configuração / único hotel bootstrap).

Sem reserva elegível: grava só `evento_webhook` (quando o insert for novo), **não** cria
mensagem/trabalho de ficha, responde `200`. Não inventa vínculo.

Se a reserva já não está em `aguardando_cadastro` (ficha já consolidada etc.): grava evento
(idempotente) e **não** sobrescreve ficha nem cria interpretação (edge da spec).

**Rationale**: FR-001 / edge cases; Artigo XIV.

**Alternatives considered**:

- **Sempre criar mensagem órfã sem reserva**: polui histórico sem dono; adiado.
- **Reabrir coleta após `ficha_parcial`**: fora desta fatia.

---

## 8. Validação de campos e proibição de idade

**Decisão**: após o LLM (ou falsa), uma camada pura valida/normaliza: data de nascimento
como data calendário; `tipo_documento` ∈ {`rg`,`cpf`,`passaporte`}; CEP/telefone canônicos
quando presentes. **Nunca** há campo `idade` no resultado persistido nem no schema de
atualização de `hospede`.

**Rationale**: Artigo VIII / FR-009; coluna inexistente no DDL.

---

## 9. Segurança do webhook

**Decisão**: `GET /webhook` responde ao desafio de verificação com o token configurado.
`POST /webhook` valida assinatura do provedor (segredo de app). Falha de assinatura → `401`
(ou `403`), sem gravar. Testes usam o mesmo segredo de ambiente de teste para assinar
payloads sintéticos.

**Rationale**: Artefato 5 §11.1 — endpoint público.

**Recorte honesto**: payload completo da Meta pode ser normalizado por um adaptador fino no
router; o domínio trabalha com um evento interno (id externo, telefone, texto, tipo de
mídia). A suíte pode postar o formato interno autenticado **ou** o envelope Meta assinado —
o contrato fixa o comportamento observável, não a fidelidade byte-a-byte do JSON da Meta.

---

## 10. Leitura da ficha pela recepção

**Decisão**: além do `estado_cadastro` na fila, expor `GET /reservas/{id_reserva}/ficha`
para o perfil recepção do hotel, devolvendo os campos do titular (sem idade). Operacional e
gestão continuam bloqueados para dado cadastral (política já existente /
`alterar_ficha_de_hospede` / leitura restrita).

**Rationale**: “disponibiliza para a recepção” na spec; fila resume estado, não substitui a
ficha legível para o balcão.

---

## 11. Divergências / alinhamentos documentais

| Tema | Situação | Ação nesta fatia |
| --- | --- | --- |
| Vocabulário jornada `aguardando_transcricao` | Modelo usa `ficha_recebida` | Manter modelo; painel/API usam `estado_cadastro` / status do DDL |
| `trabalho.tipo` só `enviar_coleta` | Bloqueia interpretação assíncrona | Migração + `04-schema.sql` |
| `LLMProvider` documentado, código ausente | Lacuna desde Artefato 5 | Introduzir porta + falsa |
| Webhook / `evento_webhook` sem writer | Tabela e teste de UNIQUE já existem | Writer na F1.3 |
| `intencao` de mensagem | CHECK de F3 | Usar `classificacao_bruta` para extração |

Nenhuma divergência exige emenda constitucional.
