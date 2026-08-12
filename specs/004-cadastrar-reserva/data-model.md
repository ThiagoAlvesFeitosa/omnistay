# Modelo de dados — Cadastrar Reserva

Esta fatia **não cria tabela nova**. Usa `hospede`, `reserva` e `reserva_hospede` já existentes
e amplia a visão `vw_fila_do_dia`. Detalhe das decisões em [research.md](./research.md).

---

## Entidades envolvidas

### `reserva`

| Campo | Papel nesta fatia |
| --- | --- |
| `id_reserva` | Gerado na criação |
| `id_hotel` | Copiado de `SessaoAtual.id_hotel` — nunca do corpo |
| `telefone_contato` | Forma canônica (`55` + DDD + número) |
| `data_checkin_prevista` | Informada pela recepção |
| `data_checkout_prevista` | Informada; deve ser **estritamente posterior** ao check-in |
| `status` | Sempre `aguardando_cadastro` neste fluxo |
| `reenvio_realizado` | Default `false` (intocado; F1.4) |
| `checkin_em` / `checkout_em` | Nulos |
| `criado_em` | Default do banco |

**Validações de aplicação**: campos obrigatórios; telefone canônico válido; checkout > check-in.

**Garantias de banco já existentes**: `ck_reserva_datas`, domínio de `status`, default
`aguardando_cadastro`, FK de hotel.

### `hospede` (titular provisório)

Criado na mesma transação da reserva. Nesta fatia só preenche:

| Campo | Valor |
| --- | --- |
| `nome_completo` | Nome digitado pela recepção (trim; não vazio) |
| `telefone` | Mesma forma canônica de `reserva.telefone_contato` |
| Demais campos da ficha | `NULL` — preenchidos na F1.3 |

Não há `id_hotel` na tabela (dívida registrada no plano). Isolamento de acesso é pela reserva.

### `reserva_hospede`

| Campo | Valor nesta fatia |
| --- | --- |
| `id_reserva` | A reserva recém-criada |
| `id_hospede` | O titular provisório |
| `titular` | `true` |
| `ficha_completa` | `false` |

O índice único parcial `uq_reserva_um_titular` garante um único titular por reserva.

---

## Fluxo de escrita (atômico)

```text
1. Validar entrada (nome, telefone, datas)
2. Normalizar telefone → canônico
3. BEGIN
4.   INSERT hospede (nome_completo, telefone)
5.   INSERT reserva (id_hotel, telefone_contato, datas, status=aguardando_cadastro)
6.   INSERT reserva_hospede (titular=true, ficha_completa=false)
7. COMMIT
```

Qualquer falha (validação, restrição, erro de I/O) aborta a transação — nenhum dos três
registros permanece.

---

## `vw_fila_do_dia` (ampliada)

A visão atual devolve hotel, reserva, check-in, status, nome do titular, `ficha_completa` e
`chegada_nao_confirmada`. Nesta fatia ela passa a incluir também:

| Coluna nova | Origem |
| --- | --- |
| `telefone_contato` | `reserva.telefone_contato` |
| `data_checkout_prevista` | `reserva.data_checkout_prevista` |

A migração usa `DROP VIEW` + `CREATE VIEW`: no PostgreSQL, `CREATE OR REPLACE VIEW` não permite
inserir colunas no meio da lista existente.

Definição alvo (equivalente ao bloco congelado da migração `0003`):

```sql
CREATE OR REPLACE VIEW vw_fila_do_dia AS
SELECT r.id_hotel,
       r.id_reserva,
       r.data_checkin_prevista,
       r.data_checkout_prevista,
       r.telefone_contato,
       r.status,
       h.nome_completo,
       rh.ficha_completa,
       (r.data_checkin_prevista < CURRENT_DATE
        AND r.status <> 'hospedado'
        AND r.status <> 'cancelada') AS chegada_nao_confirmada
  FROM reserva r
  LEFT JOIN reserva_hospede rh
         ON rh.id_reserva = r.id_reserva AND rh.titular
  LEFT JOIN hospede h
         ON h.id_hospede = rh.id_hospede
 WHERE r.status NOT IN ('encerrado', 'cancelada')
   AND r.data_checkin_prevista <= CURRENT_DATE;
```

**Consulta da aplicação (fila)**: `WHERE id_hotel = :hotel_da_sessao ORDER BY
data_checkin_prevista ASC, id_reserva ASC`.

A visão já restringe a check-in previsto **até hoje** (chegadas do dia, atrasadas e
hospedados). Reserva futura não entra. Correção na revisão `0004_fila_sem_futuro`.

---

## Contagem de chegadas do dia

Agregado, sem dado de hóspede. Conta reservas do hotel da sessão com
`data_checkin_prevista = CURRENT_DATE` e `status NOT IN ('encerrado', 'cancelada')`.

A consulta devolve um inteiro. Não junta `hospede`, não projeta telefone nem nome.

---

## Máquina de estados (recorte)

Nesta fatia só existe a transição implícita de criação:

| De | Para | Evento |
| --- | --- | --- |
| *(inexistente)* | `aguardando_cadastro` | cadastro pela recepção |

Nenhuma outra transição é disparada. A trigger `tg_valida_transicao_reserva` não age em
`INSERT`.

---

## Relacionamentos

```text
hotel 1 ─── N reserva
reserva 1 ─── 1 titular (via reserva_hospede WHERE titular)
hospede 1 ─── N reserva_hospede
```

No MVP e daqui pra frente neste produto: **cada criação gera um hóspede novo**, mesmo com
telefone já existente. Não há reuso por número. Consolidação “por pessoa”, se um dia existir,
é passo explícito futuro — ver [research.md](./research.md) §9.

---

## Impacto em documentação e migração

| Artefato | Mudança |
| --- | --- |
| `alembic/versions/0003_fila_do_dia.py` + SQL congelado | `CREATE OR REPLACE VIEW` ampliada |
| `docs/04-schema.sql` | Mesma definição da visão |
| `docs/04-modelagem-de-dados.md` | Registrar que a criação da reserva cria titular mínimo com nome e telefone; ficha completa vem depois |
| Inventário de conformidade (F0.2) | Continua passando se documento e banco forem atualizados juntos |
