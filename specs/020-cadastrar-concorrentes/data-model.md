# Modelo de dados — Cadastro de Concorrentes

Esta fatia **não cria tabela**. Usa `concorrente` já existente e acrescenta
restrição, índice único e índice parcial. Referência: `docs/04-schema.sql`.
Decisões em [research.md](./research.md).

---

## Entidade

### `concorrente`

| Campo | Papel nesta fatia |
| --- | --- |
| `id_concorrente` | Identificador estável; distingue nomes repetidos |
| `id_hotel` | Sempre o hotel da sessão; toda leitura e escrita filtram por aqui |
| `nome` | Obrigatório; trim; 1–120 caracteres visíveis. Duplicata **permitida** |
| `url_fonte` | Endereço da fonte pública; trim; 1–400; `http` ou `https` com anfitrião, sem espaço, sem credencial |
| `ativo` | Nasce `true`; `false` = fora da lista de fontes ativas; reativável |
| `criado_em` | Default no insert; **não** há `atualizado_em` nesta fatia |

Não há preço, nota, data de coleta, usuário/senha da fonte nem embedding.
`coleta_mercado` **não** é escrita.

### Relacionamentos

```text
hotel 1 ─── * concorrente
concorrente 1 ─── * coleta_mercado     (existe; esta fatia não insere)
```

`id_hotel` em `concorrente` é a fronteira multi-tenant (Artigo XIV). A coleta
futura alcança o hotel pelo concorrente, não por coluna própria.

---

## Ciclo de vida

```text
(criar) → ativo = true
         ↓
    PATCH nome/url_fonte     (permanece ativo ou inativo, conforme estava)
         ↓
    PATCH ativo=false        → some das fontes ativas; permanece na manutenção
         ↓
    PATCH ativo=true         → volta às fontes ativas com nome e URL atuais
```

Não há estado “apagado”. Não há `DELETE`. Concorrente de outro hotel é
indistinguível de inexistente (`404`).

Fonte desativada **continua a ocupar** o endereço na propriedade: criar outra
ficha com a mesma URL (ignorando maiúsculas e espaços nas pontas) é recusado.

---

## Consultas

| Consulta | Filtro | Forma |
| --- | --- | --- |
| Manutenção | `id_hotel` da sessão; ativos **e** inativos | Lista plana, ordem `nome`, `id_concorrente` |
| Fontes ativas | `id_hotel`; **somente** `ativo = true` | Lista plana com id, nome, `url_fonte`; ordem igual |

A consulta de fontes ativas é o contrato da F5.2
([fontes-ativas.md](./contracts/fontes-ativas.md)). Índice:
`ix_concorrente_hotel_ativo` em `(id_hotel) WHERE ativo`.

---

## Validações

| Regra | Onde |
| --- | --- |
| Nome e URL não vazios após trim | Aplicação |
| Nome ≤ 120, URL ≤ 400 | Aplicação (espelha `VARCHAR`) |
| URL é `http(s)://` + anfitrião, sem espaço, sem usuário/senha | Aplicação (`urlparse`) + `ck_concorrente_url_fonte` |
| Mesma fonte no mesmo hotel (lower + trim), inclusive inativo | Aplicação (`409`) + `uq_concorrente_hotel_fonte` |
| `id_hotel` da sessão, nunca do corpo | Aplicação |
| Nome duplicado | Permitido; sem índice único de nome |
| Remoção permanente | Não existe operação |

Dois hotéis podem cadastrar a mesma URL: o índice inclui `id_hotel`.

---

## Migração `0019_cadastrar_concorrentes`

SQL congelado em `alembic/versions/sql/0019_cadastrar_concorrentes.sql`.
Documento vivo `docs/04-schema.sql` recebe o mesmo delta. `0001` **não** muda.

```sql
ALTER TABLE concorrente
    ADD CONSTRAINT ck_concorrente_url_fonte
        CHECK (url_fonte ~* '^https?://[^[:space:]]+$');

CREATE UNIQUE INDEX uq_concorrente_hotel_fonte
    ON concorrente (id_hotel, lower(btrim(url_fonte)));

CREATE INDEX ix_concorrente_hotel_ativo
    ON concorrente (id_hotel) WHERE ativo;
```

`downgrade` remove os três. Não há backfill: a tabela está vazia em
instalação nova; ambiente com lixo pré-restrição é fora do MVP.

---

## O que esta fatia não toca

- `coleta_mercado` (leitura ou escrita)
- `parametro_hotel` (`periodicidade_coleta_mercado` já existe; F5.2 lê)
- `catalogo_item`, `item_vendavel`, reserva, hóspede, mensagem
- Bootstrap / semeadura de concorrente de exemplo
- Fila `trabalho`, worker, agendador
