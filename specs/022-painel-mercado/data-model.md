# Modelo de dados — Painel de Mercado

Esta fatia **não cria tabela, coluna, índice, view nem tipo de trabalho**.
Reusa `concorrente`, `coleta_mercado` e `parametro_hotel`. Referência:
`docs/04-schema.sql`. Decisões em [research.md](./research.md).

O produto novo é a **leitura consolidada**: visão atual (último sucesso +
situação) e histórico (série crua). Nenhuma linha de `coleta_mercado` é
inserida, atualizada ou apagada aqui.

---

## Entidades

### `concorrente` (somente leitura nesta fatia)

Cadastro da F5.1. A visão atual lista **todos** os da propriedade, ativos e
inativos.

| Campo | Papel nesta fatia |
| --- | --- |
| `id_concorrente` | Identificador no painel e no histórico |
| `id_hotel` | Fronteira multi-tenant de **toda** leitura |
| `nome` | Rótulo na comparação |
| `ativo` | Distingue inativo; inativo **permanece** na consulta |
| `url_fonte` | **Não** entra no payload do painel (já está na manutenção) |

Escrita de cadastro continua nas rotas da F5.1. Esta fatia não as redesenha.

### `coleta_mercado` (somente leitura nesta fatia)

Série temporal da F5.2. Cada linha é um ponto. O painel **não** dá UPDATE.

| Campo | Papel nesta fatia |
| --- | --- |
| `id_coleta` | Identificador do ponto no histórico |
| `id_concorrente` | Dono da série; hotel chega por JOIN |
| `preco` | Valor do sucesso; nulo na falha; **zero é zero** |
| `nota_media` | Nota agregada do sucesso; nula se ausente |
| `sucesso` | Distingue valor encontrado de tentativa sem valor |
| `coletado_em` | Carimbo obrigatório de todo ponto — sucesso e falha |

Índice já existente: `ix_coleta_concorrente_data (id_concorrente, coletado_em DESC)`.

Não há coluna `situacao` persistida. A classificação é derivada na leitura
(ver [situacao-do-dado.md](./contracts/situacao-do-dado.md)).

### `parametro_hotel` (leitura da chave existente)

| Chave | Papel |
| --- | --- |
| `periodicidade_coleta_mercado` | Limiar, em horas, entre `atual` e `desatualizado` |

Ausência ou valor inválido (vazio, não inteiro, menor que 1): nenhum número é
`atual`; concorrente com sucesso fica `cadencia_ausente`. **Não** se lê
default `24` no painel. A semente `24` continua sendo da instalação (F5.2),
não da consulta.

SQL desta chave permanece em `propriedade.repository`. Mercado só pede o
valor.

---

## Relacionamentos

```text
hotel 1 ─── * concorrente
concorrente 1 ─── * coleta_mercado     (append-only; esta fatia só SELECT)
hotel 1 ─── * parametro_hotel          (chave periodicidade_coleta_mercado)
```

Não há FK nova. Não há `id_hotel` em `coleta_mercado`.

---

## Projeções de leitura (não são tabelas)

### Visão atual (por concorrente da propriedade)

Derivada no serviço a partir de: ficha + último sucesso + última linha da
série + periodicidade + relógio.

| Campo derivado | Origem |
| --- | --- |
| `id_concorrente`, `nome`, `ativo` | `concorrente` |
| `ultimo_sucesso` | última linha com `sucesso = true`, ou ausente |
| `ultima_falha` | `coletado_em` da última linha se ela for falha; senão ausente |
| `situacao` | regras do contrato de situação |
| `periodicidade_horas` | parâmetro da propriedade (no envelope da lista; nulo se inválido) |

Preço/nota **nunca** vêm de uma linha com `sucesso = false`.

### Histórico (por concorrente)

A série completa, uma entrada por linha, ordem `coletado_em ASC`,
`id_coleta ASC`. Sem derivar `situacao` por ponto.

---

## Regras de validação (leitura)

- Toda query de coleta inclui `concorrente.id_hotel = :id_hotel` da sessão.
- Concorrente de outro hotel ou id inexistente: o serviço trata como
  **não encontrado** (a API responde `404`, sem distinguir).
- Campo vazio (`NULL`) ≠ zero. Falha ≠ sucesso com zero.
- Inativo não some da visão atual nem do histórico.

## Transições de estado

Nenhuma. Esta fatia não altera `concorrente.ativo`, não insere coleta e não
enfileira `coletar_mercado`.

## Integridade que o banco já garante (reuso)

| Garantia | Onde |
| --- | --- |
| Falha sem preço/nota; sucesso com ao menos um | `ck_coleta_sucesso_tem_dado` |
| Preço ≥ 0 | `ck_coleta_preco_nao_negativo` |
| Nota 0–5 | `ck_coleta_nota_media` |
| Série por concorrente indexada no tempo | `ix_coleta_concorrente_data` |

O painel **confia** nesses CHECKs: não reimplementa “sucesso sem dado” na
exibição além de recusar tratar `NULL` como zero.
