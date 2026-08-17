# Modelo de dados — Catálogo da Propriedade

Esta fatia **não cria tabela nem coluna**. Usa `catalogo_item` já existente.
Referência: `docs/04-schema.sql`. Decisões em [research.md](./research.md).

---

## Entidade

### `catalogo_item`

| Campo | Papel nesta fatia |
| --- | --- |
| `id_catalogo_item` | Identificador estável; a recepção distingue duplicatas de título por ele |
| `id_hotel` | Sempre o hotel da sessão; toda leitura e escrita filtram por aqui |
| `categoria` | Uma das cinco chaves do `CHECK`; **imutável** depois da criação |
| `titulo` | Obrigatório; trim; 1–160 caracteres visíveis |
| `conteudo` | O fato em texto; obrigatório após trim; `TEXT` sem teto extra nesta fatia |
| `ativo` | Nasce `true`; `false` = desativado (fora do catálogo ativo); reativável |
| `atualizado_em` | Default no insert; o `UPDATE` do serviço grava `now()` |

Não há preço, código vendável, embedding nem ordem manual.

### Categorias canônicas

| Chave (API e banco) | Nome na spec |
| --- | --- |
| `horario` | horários |
| `cardapio` | cardápio |
| `servico` | serviços |
| `programacao` | programação |
| `regra` | regras |

Qualquer outro valor é recusado na aplicação (`422`) e, se chegar ao banco, pelo
`ck_catalogo_categoria`.

---

## Ciclo de vida

```text
(criar) → ativo = true
         ↓
    PATCH titulo/conteudo   (permanece ativo ou inativo, conforme estava)
         ↓
    PATCH ativo=false       → some do catálogo ativo; permanece na manutenção
         ↓
    PATCH ativo=true        → volta ao catálogo ativo com o conteúdo atual
```

Não há estado “apagado”. Não há `DELETE`. Item de outro hotel é indistinguível de
inexistente (`404`).

---

## Consultas

| Consulta | Filtro | Forma |
| --- | --- | --- |
| Manutenção | `id_hotel` da sessão; ativos **e** inativos | Lista plana, ordem `categoria`, `id_catalogo_item` |
| Catálogo ativo | `id_hotel`; **somente** `ativo = true` | Cinco chaves sempre presentes; itens por id crescente |

A consulta ativa é o contrato da porta `CatalogoRepository` (lista plana de ativos;
agrupamento é apresentação HTTP). Índice já existente:
`ix_catalogo_hotel_categoria` em `(id_hotel, categoria) WHERE ativo`.

---

## Validações

| Regra | Onde |
| --- | --- |
| Categoria ∈ cinco chaves | Aplicação + `CHECK` |
| Título e conteúdo não vazios após trim | Aplicação |
| Título ≤ 160 | Aplicação (espelha `VARCHAR(160)`) |
| `id_hotel` da sessão, nunca do corpo | Aplicação |
| Categoria não muda no PATCH | Aplicação (`422` se o campo vier) |
| Duplicata de título | Permitida; sem índice único |
| Remoção permanente | Não existe operação |

---

## O que esta fatia não toca

- `parametro_hotel`, `hotel` (além do FK já existente)
- `consumo`, preço, `valor_praticado`
- Mensagem ao hóspede, fila `trabalho`, prompt de IA
- Semeadura de itens no bootstrap (catálogo nasce vazio)
