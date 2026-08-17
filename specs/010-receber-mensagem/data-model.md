# Modelo de dados — Receber Mensagem com Segurança

Complementa o esquema já existente. Referência documental: `docs/04-schema.sql`.
Migração prevista: `0009_receber_mensagem`.

Nenhuma tabela nova. Nenhuma coluna nova.

---

## Entidades envolvidas

### `evento_webhook` (reuso)

| Campo | Uso nesta fatia |
| --- | --- |
| `id_externo` | Idempotência do reenvio (`UNIQUE`) |
| `payload` | Flags e identificadores — **sem** texto da mensagem |
| `recebido_em` | Auditoria de chegada |

**Regra:** segunda inserção com o mesmo `id_externo` falha no banco; a API traduz em `200`
sem novo efeito (mensagem, trabalho e reserva intactos).

Notificação recusada por autenticidade **não** insere linha.

### `mensagem` (entrada da estadia)

| Campo | Valor nesta fatia |
| --- | --- |
| `direcao` | `recebida` |
| `conteudo` | Texto do hóspede (só se houver reserva elegível) |
| `id_externo` | Id da mensagem no canal, quando houver |
| `status_envio` | `NULL` |
| `intencao` / `sentimento` / `urgencia` | Permanecem `NULL` (F3.2) |
| `classificacao_bruta` | Permanece `NULL` (F3.2) |
| `enviada_em` | Timestamp de origem do envelope, se vier; senão `now()` |

Mídia sem texto utilizável: **não** cria linha de `mensagem` de estadia (só o evento).

### `reserva` (somente leitura para correlação)

| Status | Efeito desta fatia |
| --- | --- |
| `aguardando_cadastro` | Caminho F1.3: mensagem + `interpretar_ficha` |
| `hospedado` | Mensagem + `classificar_mensagem` |
| Qualquer outro (`ficha_recebida`, `ficha_parcial`, `sem_cadastro_previo`, `encerrada`, `cancelada`, …) | Só evento; status **não** muda |

Consulta sempre com `id_hotel`. Em `hospedado`, desempate: `ORDER BY id_reserva DESC LIMIT 1`.

### `trabalho` (ampliação)

| Campo | Uso |
| --- | --- |
| `tipo` | Passa a admitir `classificar_mensagem` |
| `payload` | `{ "id_reserva", "id_mensagem", "id_evento" }` — só IDs |
| `status` | `pendente` ao nascer; **permanece** `pendente` nesta fatia |
| tentativas / backoff | Intocados |

**CHECK novo:**

```sql
tipo IN ('enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
         'enviar_boas_vindas', 'classificar_mensagem')
```

**Unicidade:**

```sql
CREATE UNIQUE INDEX uq_trabalho_classificar_mensagem_mensagem
  ON trabalho ( ((payload->>'id_mensagem')::bigint) )
  WHERE tipo = 'classificar_mensagem';
```

**Claim:** `reclamar_proximo` **não** inclui `classificar_mensagem` na allowlist de tipos
despacháveis. O índice `ix_trabalho_claim` não muda.

---

## Delta SQL (congelar na revisão)

```sql
ALTER TABLE trabalho DROP CONSTRAINT ck_trabalho_tipo;
ALTER TABLE trabalho
    ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN ('enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
                    'enviar_boas_vindas', 'classificar_mensagem'));

CREATE UNIQUE INDEX uq_trabalho_classificar_mensagem_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'classificar_mensagem';
```

`downgrade`: `DROP INDEX` do único; restaura o CHECK da revisão `0008` (sem
`classificar_mensagem`).

---

## Regras de validação

- Autenticidade é da borda HTTP: recusa **antes** de qualquer INSERT.
- Telefone de origem passa pelo canônico já existente (`app/comum/telefone.py`); inválido →
  só evento, sem mensagem.
- `id_hotel` do canal em toda resolução.
- Foto / mídia sem texto: sem trabalho de estadia, sem texto inventado.
- Conteúdo de `mensagem` e telefone em claro nunca em log.

---

## O que não muda nesta fatia

- Máquina de estados da reserva e a trigger `fn_valida_transicao_reserva`.
- `vw_fila_do_dia`.
- Colunas de classificação em `mensagem` (domínio já existe; preenchimento é F3.2).
- Tipos de trabalho anteriores e seus índices únicos.
- Tabela `solicitacao`.
