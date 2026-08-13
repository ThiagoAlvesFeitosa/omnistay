# Modelo de dados — Disparar Coleta de Dados

Esta fatia **cria** a tabela `trabalho`, **usa** `mensagem` pela primeira vez no código,
amplia `vw_fila_do_dia` e acrescenta parâmetros de hotel. Detalhe das decisões em
[research.md](./research.md).

---

## Entidades envolvidas

### `trabalho` (nova)

Fila durável de trabalho assíncrono. Nesta fatia o único `tipo` em uso é `enviar_coleta`.

| Campo | Tipo / regra | Papel |
| --- | --- | --- |
| `id_trabalho` | `BIGSERIAL` PK | Identificador |
| `id_hotel` | `BIGINT NOT NULL` FK → `hotel` | Multi-tenant |
| `tipo` | `VARCHAR` + `CHECK` | `enviar_coleta` (outros tipos em fatias futuras) |
| `payload` | `JSONB NOT NULL` | Pelo menos `id_reserva`, `id_mensagem` (inteiros) |
| `status` | `CHECK` | `pendente` · `processando` · `concluido` · `falha` |
| `tentativas` | `INT NOT NULL DEFAULT 0` | Tentativas de envio já feitas |
| `proxima_tentativa_em` | `TIMESTAMPTZ NULL` | `NULL` = elegível; senão, wait até o instante |
| `erro_ultima_tentativa` | `TEXT NULL` | Código/resumo **sem** PII nem corpo de mensagem |
| `processando_desde` | `TIMESTAMPTZ NULL` | Início do claim; base do reclaim |
| `criado_em` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | |
| `atualizado_em` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | |

**Garantias de banco**:

- `CHECK` de `status` e de `tipo`.
- Índice único parcial: no máximo um `enviar_coleta` por `id_reserva` no payload.
- Índice de claim: `(status, proxima_tentativa_em)` (ou equivalente) para o worker listar
  elegíveis com `FOR UPDATE SKIP LOCKED`.

**Payload mínimo (`enviar_coleta`)**:

```json
{
  "id_reserva": 42,
  "id_mensagem": 7
}
```

Sem telefone, sem nome, sem texto — o worker lê destinatário e conteúdo a partir de
`reserva` / `mensagem` (e o conteúdo já gravado não precisa viajar no payload).

### `mensagem` (primeiro uso na aplicação)

| Campo | Valor nesta fatia |
| --- | --- |
| `id_reserva` | Reserva recém-criada |
| `direcao` | `enviada` |
| `conteudo` | Texto completo da coleta (lista numerada, opcionalidade, finalidade, contato) |
| `status_envio` | Nasce `pendente`; worker → `enviada` ou `falha` |
| `id_externo` | Preenchido no sucesso com id do provedor, se houver |
| `intencao` / sentimento / urgência | `NULL` (mensagem de saída proativa, não classificada) |
| `enviada_em` | Default `now()` na criação da pendência (instante do registro) |

**Validações já no banco**: `direcao = enviada` exige `status_envio NOT NULL`; domínio
`pendente|enviada|entregue|falha`.

**Regra de aplicação**: uma mensagem de coleta por reserva neste fluxo — criada junto com o
trabalho; nunca re-inserida no retry.

### `reserva` / `hospede` / `reserva_hospede`

Sem mudança de colunas. Ciclo de vida da reserva **não** muda (`aguardando_cadastro`).
`reenvio_realizado` continua intocado (F1.4).

O primeiro nome na mensagem é derivado de `hospede.nome_completo` do titular (primeiro
token após trim).

### `parametro_hotel` (novas chaves)

| Chave | Default no bootstrap | Uso |
| --- | --- | --- |
| `contato_responsavel_dados` | Telefone do hotel criado no bootstrap | Embutido no texto da coleta |
| `tentativas_max_envio_mensagem` | `5` | Teto de tentativas do worker antes de `falha` |

Durações de sessão da F0.3 permanecem.

### `vw_fila_do_dia` (ampliada de novo)

| Coluna nova | Origem |
| --- | --- |
| `status_envio_coleta` | `mensagem.status_envio` da mensagem de saída de coleta da reserva |

Join: subtabela / `LEFT JOIN LATERAL` da mensagem enviada da reserva (nesta fatia há no
máximo uma). Reservas antigas pré-F1.2 podem ter `NULL`; novas sempre têm valor após o
commit de criação.

A migração usa `DROP VIEW` + `CREATE VIEW` (mesmo motivo das revisões `0003`/`0004`).

---

## Fluxo de escrita no cadastro (atômico)

```text
1. Validar entrada (já F1.1)
2. Normalizar telefone
3. BEGIN
4.   INSERT hospede / reserva / reserva_hospede
5.   Montar texto da coleta (puro; lê contato em parametro_hotel)
6.   INSERT mensagem (direcao=enviada, status_envio=pendente, conteudo=…)
7.   INSERT trabalho (tipo=enviar_coleta, status=pendente, payload={id_reserva,id_mensagem})
8. COMMIT
9. Resposta 201 — sem chamada à mensageria
```

Falha em qualquer passo 4–7 aborta tudo — inclusive a reserva (FR-016 inverso: sucesso
parcial impossível).

---

## Fluxo do worker (após o commit)

```text
1. Claim: SELECT … FOR UPDATE SKIP LOCKED
     WHERE status = pendente
       AND (proxima_tentativa_em IS NULL OR proxima_tentativa_em <= now())
   → status = processando, processando_desde = now()
2. Reclaim prévio: processando com bloqueio expirado volta a pendente
3. Ler mensagem + telefone da reserva (+ id_hotel)
4. MensageriaGateway.enviar_coleta(…)
5a. Sucesso → mensagem.status_envio = enviada (+ id_externo);
              trabalho.status = concluido
5b. Falha  → tentativas += 1; erro_ultima_tentativa = código;
              se tentativas < max → pendente + proxima_tentativa_em (backoff);
              senão → trabalho = falha; mensagem.status_envio = falha
```

A reserva **nunca** é atualizada neste fluxo.

---

## Transições de `mensagem.status_envio` (coleta)

```text
pendente → enviada     (sucesso do gateway)
pendente → pendente    (falha com retry restante — permanece pendente até novo claim;
                        opcionalmente a UI já mostra pendente)
pendente → falha       (tentativas esgotadas)
enviada  → (entregue)  — FORA DE ESCOPO (webhook de status)
```

Na prática do painel: enquanto o trabalho reprocessa, a recepção vê `pendente`; após esgotar,
vê `falha`; após sucesso, `enviada`.

---

## O que não muda no modelo

- Máquina de estados de `reserva`
- `evento_webhook` (entrada)
- Consentimento, solicitação, consumo
- Particionamento de `hospede` por hotel (dívida da F1.1)
