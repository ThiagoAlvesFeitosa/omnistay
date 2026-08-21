# Modelo de dados — Coleta Agendada

Esta fatia **não cria tabela de domínio nova**. Reusa `coleta_mercado` e
`concorrente` da `0001`, lê `parametro_hotel`, e acrescenta tipo + unicidade
na fila `trabalho`. Referência: `docs/04-schema.sql`. Decisões em
[research.md](./research.md).

---

## Entidades

### `coleta_mercado`

Série temporal. Cada ciclo **insere**; jamais atualiza a linha anterior.

| Campo | Papel nesta fatia |
| --- | --- |
| `id_coleta` | Identificador do registro |
| `id_concorrente` | FK; o hotel chega por JOIN em `concorrente` — **não** há `id_hotel` aqui |
| `preco` | Público encontrado; nulo em falha; **zero é sucesso** |
| `nota_media` | Agregada 0–5; nula se ausente ou escala não confiável |
| `sucesso` | `true` só com preço e/ou nota; `false` = tentativa datada sem valor encontrado |
| `coletado_em` | Instante da tentativa; obrigatório no sucesso **e** na falha |

Não há `motivo_falha`, HTML, nome de avaliador nem texto de página.

### `concorrente`

Somente leitura de alvos. Escrita de cadastro continua a F5.1.

| Campo | Papel nesta fatia |
| --- | --- |
| `id_concorrente` | Alvo do trabalho e da série |
| `id_hotel` | Fronteira multi-tenant de **toda** consulta de coleta |
| `url_fonte` | Lida na hora da visita, não copiada para a fila |
| `ativo` | Só `true` entra no ciclo; inativo não gera linha nova |

### `parametro_hotel`

| Chave | Valor | Papel |
| --- | --- | --- |
| `periodicidade_coleta_mercado` | Horas, inteiro ≥ 1. Semente **24** | Janela até a próxima visita **daquela fonte** |

Ausência ou valor inválido: a propriedade não coleta (não há default no
verificador).

### `trabalho` (tipo novo)

| Campo | Papel |
| --- | --- |
| `tipo` | `coletar_mercado` |
| `id_hotel` | Hotel dono da ficha |
| `payload` | Só `{"id_concorrente": N}` |
| `status` | Enfileira `pendente`; o processador termina em `concluido` mesmo na falha de coleta |

---

## Relacionamentos

```text
hotel 1 ─── * concorrente
concorrente 1 ─── * coleta_mercado
hotel 1 ─── * trabalho (tipo coletar_mercado)
concorrente 1 ─── * trabalho aberto (0 ou 1; índice único parcial)
```

---

## Ciclo de vida de uma coleta

```text
fonte ativa + periodicidade válida + janela vencida (ou nunca coletada)
        ↓
  INSERT trabalho coletar_mercado (pendente)
        ↓
  worker reclama
        ↓
  ficha ainda ativa? diretiva permite? ──não──► INSERT coleta sucesso=false
        ↓ sim                                    trabalho concluido
  coletar_publico
        ↓
  tem preço ou nota? ──sim──► INSERT sucesso=true
        ↓ não
  INSERT sucesso=false
        ↓
  trabalho concluido
```

Reclaim do mesmo trabalho: se já existe coleta com `coletado_em >= criado_em`
do trabalho, conclui sem segundo INSERT.

Inativa entre o enqueue e o claim: conclui **sem** INSERT (FR-003).

---

## Validações

| Regra | Onde |
| --- | --- |
| Sucesso exige preço ou nota | `ck_coleta_sucesso_tem_dado` + aplicação |
| Preço nulo ou ≥ 0 | `ck_coleta_preco_nao_negativo` |
| Nota nula ou 0–5 | `ck_coleta_nota_media` |
| Falha não apaga a anterior | só INSERT; sem UPDATE/DELETE |
| Um trabalho aberto por concorrente | `uq_trabalho_coletar_mercado_concorrente_aberto` |
| Tipo conhecido | `ck_trabalho_tipo` (acrescenta `coletar_mercado`) |
| Só ativo é visitado | aplicação relê `ativo` + `id_hotel` no claim |
| Periodicidade inteiro ≥ 1 | aplicação; ausência = não coleta |
| `id_hotel` em toda leitura/escrita | JOIN/`WHERE` no concorrente da sessão/ficha |

Preço público zero: INSERT `sucesso=true`, `preco=0`. Distinto de falha.

---

## Consultas desta fatia

| Consulta | Filtro | Uso |
| --- | --- | --- |
| Fontes ativas | `id_hotel` + `ativo` | Contrato F5.1; varredura por hotel |
| Última coleta | `id_concorrente`, `coletado_em DESC LIMIT 1` | Janela devida |
| Inserir coleta | FK concorrente | Processador |
| Trabalhos abertos | índice único parcial | Não duplicar ciclo |

Não há GET HTTP da série. Testes leem pelo repositório. Painel = F5.3.

---

## Migração `0020_coleta_agendada`

SQL congelado em `alembic/versions/sql/0020_coleta_agendada.sql`. Documento
vivo `docs/04-schema.sql` recebe o mesmo delta. `0001` **não** muda.
`coleta_mercado` **não** é recriada.

```sql
ALTER TABLE trabalho DROP CONSTRAINT ck_trabalho_tipo;
ALTER TABLE trabalho ADD CONSTRAINT ck_trabalho_tipo CHECK (tipo IN (
    -- tipos já vigentes +
    'coletar_mercado'
));

CREATE UNIQUE INDEX uq_trabalho_coletar_mercado_concorrente_aberto
    ON trabalho (( (payload->>'id_concorrente')::bigint ))
    WHERE tipo = 'coletar_mercado'
      AND status IN ('pendente', 'processando');

INSERT INTO parametro_hotel (id_hotel, chave, valor)
SELECT h.id_hotel, 'periodicidade_coleta_mercado', '24'
  FROM hotel h
 WHERE NOT EXISTS (
       SELECT 1 FROM parametro_hotel p
        WHERE p.id_hotel = h.id_hotel
          AND p.chave = 'periodicidade_coleta_mercado'
 );
```

`downgrade` remove o índice, restaura o CHECK anterior (lista da `0019` /
`0018`) e **não** apaga a chave já semeada (mesmo critério da `0016` com o
pulso).

---

## O que esta fatia não toca

- Colunas de `concorrente` (cadastro permanece F5.1)
- Painel / GET de histórico (F5.3)
- `catalogo_item`, `item_vendavel`, reserva, hóspede, mensagem
- Tarifa da casa e o outro sistema do hotel
- Tela React
