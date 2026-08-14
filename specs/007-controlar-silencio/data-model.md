# Modelo de dados — Controlar o Silêncio

Complementa o esquema já existente. Referência documental: `docs/04-schema.sql`.
Migração prevista: `0007_controlar_silencio` (número efetivo = próximo livre no Alembic).
Decisões em [research.md](./research.md).

---

## Entidades envolvidas

### `parametro_hotel` (chaves que passam a existir de fato)

| Chave | Default (bootstrap + backfill) | Semântica |
| --- | --- | --- |
| `horas_ate_reenvio` | `24` | Horas entre coleta **enviada** e o único lembrete |
| `horas_corte_antes_checkin` | `12` | Horas antes das 00:00 UTC de `data_checkin_prevista` |

`UNIQUE (id_hotel, chave)` já existe. A migração faz `INSERT` só onde a chave falta
(hotel já instalado). Valor inválido ou ausente na verificação: pular o hotel, sem default
em código.

### `reserva`

| Campo | Uso nesta fatia |
| --- | --- |
| `status` | De `aguardando_cadastro` → `sem_cadastro_previo` no segundo prazo |
| `reenvio_realizado` | `false` → `true` na mesma transação que enfileira o lembrete; **nunca** volta a `false` |
| `data_checkin_prevista` | Base da janela de corte |
| `id_hotel` | Toda listagem e toda transição |

Nenhuma coluna nova. A trigger `fn_valida_transicao_reserva` **já permite**:

```text
aguardando_cadastro → sem_cadastro_previo
sem_cadastro_previo → hospedado | cancelada
```

Esta fatia dispara a primeira transição. Não dispara check-in.

### `mensagem`

| Papel | Valor |
| --- | --- |
| Coleta (já existe) | Primeira saída; `status_envio = enviada` define o t0 |
| Lembrete (novo) | Segunda saída; `status_envio` nasce `pendente`; worker → `enviada` ou `falha` |
| Resposta do hóspede | Qualquer `direcao = recebida` cancela lembrete e marcação |

**Ajuste operacional de `enviada_em`**: no sucesso do envio (coleta **e** lembrete),
atualizar `enviada_em` para o instante do relógio. O default no INSERT continua válido
para pendências e para mensagens recebidas.

O `LATERAL` atual da fila do dia (primeira saída por `enviada_em ASC`) **permanece a
coleta**; o lembrete não substitui `status_envio_coleta`.

### `trabalho` (ampliação)

| Campo | Uso |
| --- | --- |
| `tipo` | Passa a admitir `enviar_lembrete` |
| `payload` | `{ "id_reserva", "id_mensagem" }` — só IDs |
| `status` / tentativas / backoff | Igual à coleta (teto `tentativas_max_envio_mensagem`) |

**CHECK novo**:

```sql
tipo IN ('enviar_coleta', 'interpretar_ficha', 'enviar_lembrete')
```

**Unicidade** (Artigo IX / FR-007):

```sql
CREATE UNIQUE INDEX uq_trabalho_enviar_lembrete_reserva
  ON trabalho ( ((payload->>'id_reserva')::bigint) )
  WHERE tipo = 'enviar_lembrete';
```

No máximo um lembrete enfileirado por reserva. Retry reusa a mesma linha.

---

## Projeção: `vw_fila_do_dia`

Acrescentar ramo explícito em `estado_cadastro`:

| Valor | Condição |
| --- | --- |
| `completa` | `r.status = 'ficha_recebida'` (já existe) |
| `parcial` | `r.status = 'ficha_parcial'` (já existe) |
| `leitura_humana` | `aguardando_cadastro` + desfecho irreconhecível/falha (já existe) |
| `aguardando` | `aguardando_cadastro` sem o sinal acima (já existe) |
| **`sem_cadastro_previo`** | **`r.status = 'sem_cadastro_previo'`** |

Manter `status`, `ficha_completa`, `status_envio_coleta`, `chegada_nao_confirmada`.
Migração: `DROP VIEW` + `CREATE VIEW` (padrão `0003`–`0006`).

---

## Regras de validação

- `horas_ate_reenvio` e `horas_corte_antes_checkin`: inteiros positivos; ausência ou lixo
  não disparam efeito e não caem para 24/12 no verificador.
- `reenvio_realizado = true` é irreversível nesta fatia.
- Transição só a partir de `aguardando_cadastro`; a trigger rejeita o resto.
- `id_hotel` em listagem, leitura de parâmetro e `UPDATE` de reserva.
- Conteúdo de mensagem nunca em log.

---

## Fluxo da verificação (atômico por reserva afetada)

```text
verificar_cadastros_pendentes(agora):
  para cada reserva aguardando_cadastro (com id_hotel):
    ler prazos do hotel; se faltarem → log + próxima
    se há mensagem recebida → próxima
    se agora >= corte ou data de entrada já passou:
      UPDATE status = sem_cadastro_previo
      próxima
    se reenvio_realizado → próxima
    se coleta não enviada → próxima
    se agora >= enviada_em_coleta + horas_ate_reenvio:
      BEGIN (mesma conexão/TX da passagem)
        INSERT mensagem lembrete (pendente)
        INSERT trabalho enviar_lembrete
        UPDATE reenvio_realizado = true
```

Falha no INSERT do trabalho por unicidade: não envia segundo lembrete; a flag já verdadeira
ou o índice aborta o duplicado.

---

## Fluxo do worker após o commit do lembrete

Igual à coleta (F1.2), com `tipo = enviar_lembrete` e `gateway.enviar_lembrete(...)`.
A reserva **não** muda neste fluxo — só `mensagem.status_envio` e o status do trabalho.

---

## O que não muda no modelo

- Máquina de estados além de **usar** a transição já prevista
- Colunas de `hospede` / `reserva_hospede`
- `evento_webhook`
- Consentimento, solicitação, consumo
- Check-in (`hospedado`) — F2.2
