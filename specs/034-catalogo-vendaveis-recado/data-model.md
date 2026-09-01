# Modelo de dados — Catálogo, itens vendáveis e recado

Referência: `docs/04-schema.sql`. Decisões em [research.md](./research.md).
Esta fatia **não cria tabela**. `catalogo_item`, `item_vendavel` e
`parametro_hotel` são os da F2.1, F3.7 e F7.3. O que nasce é
modelo de superfície no frontend.

---

## Entidades novas (só de superfície)

### Item de catálogo na manutenção

Projeção de um item de `GET /catalogo`. Não é persistida. A aba
filtra por `categoria`; a tela **não** reordena o array da API
além desse filtro.

| Campo (API) | Uso na tela |
| --- | --- |
| `id_catalogo_item` | Identidade do PATCH |
| `categoria` | Aba (`horario` · `cardapio` · `servico` · `programacao` · `regra`) |
| `titulo` | Coluna título; campo da edição |
| `conteudo` | Coluna conteúdo; campo da edição |
| `ativo` | Situação; `false` → **Reativar**; `true` → **Editar** + **Desativar** |

A tela **não** envia `categoria` no PATCH. Criação envia a chave da
aba visível.

### Contagem da aba

Derivado do array filtrado: quantos `ativo === true` e quantos
`false`. Sem coluna no banco.

### Item vendável na manutenção

Projeção de `GET /itens-vendaveis`.

| Campo (API) | Uso na tela |
| --- | --- |
| `id_item_vendavel` | Identidade do PATCH |
| `nome` | Coluna e campo próprio |
| `preco_atual` | Coluna e campo próprio (número, separado do nome) |
| `ativo` | Situação; mesma lógica de desativar/reativar |
| `atualizado_em` | Não exibir |

**Não existe** campo de descrição. A tela não o inventa.

### Recado na tela

Projeção de `GET /propriedade/boas-vindas`.

| Campo (API) | Rótulo na tela |
| --- | --- |
| `cafe` | Café da manhã |
| `wifi` | Wi-fi |
| `checkout` | Horário de saída |
| `convite` | Convite |

Quatro campos, um salvamento. `null` no GET trata-se como vazio no
input (a gravação continua recusando vazio).

---

## Entidades reusadas

### `catalogo_item` (banco)

| `ativo` | Na manutenção? | No atendimento (`GET /catalogo/ativo`)? |
| --- | :---: | :---: |
| `true` | sim | sim |
| `false` | sim | não |

A tela não chama o catálogo ativo. Desativar é `PATCH` com
`ativo: false` — o mesmo que o atendimento já omite.

Categoria: cinco chaves fechadas. Sem apagamento (`DELETE` → `405`).

### `item_vendavel` (banco)

| `ativo` | Na manutenção? | Na identificação de pedido cobrado? |
| --- | :---: | :---: |
| `true` | sim | sim |
| `false` | sim | não |

`preco_atual` ≥ 0. Unique de nome entre ativos do hotel. Reajuste
**não** altera `consumo.valor_praticado`. A tela não lê consumo.

### `parametro_hotel` (quatro chaves de recado)

`boas_vindas_cafe`, `boas_vindas_wifi`, `boas_vindas_checkout`,
`boas_vindas_convite`. PUT atômico: um inválido, nenhum muda.
Salvar na tela **não** cria `trabalho` de envio.

### `usuario` / `sessao`

Casca da F8.1, com delta: `recepcao` e `gestor` montam estas telas.
`staff` não monta.

---

## O que não nasce

- Tabela, coluna, visão ou revisão Alembic
- Operação nova em `politica.py`
- Campo `descricao` no JSON de item vendável
- `DELETE` de catálogo ou de item vendável
- Rota de prévia do recado
- Notificação empurrada
- GET de catálogo ativo nesta fatia

---

## Regras de validação (superfície)

| Situação | Efeito |
| --- | --- |
| `GET /catalogo` 200, `itens: []` | Lista vazia explícita na aba; contagem zero |
| Aba sem itens, outras com itens | Vazio só na aba visível |
| `GET` 401 | Casca devolve à entrada |
| `GET` 5xx / rede / corpo ilegível | Falha de leitura; não vazio; tentar de novo |
| Título/conteúdo em branco no POST | Não afirma criado; aviso (API `422`) |
| **Editar** (catálogo ativo) | PATCH título/conteúdo; GET de novo |
| **Desativar** / **Reativar** | PATCH `ativo`; GET de novo |
| Clique fora do botão | Zero POST/PATCH/PUT |
| POST vendável 201 | GET de novo; item ativo na lista |
| PATCH preço sem nome | Só `preco_atual` no corpo |
| POST/PATCH vendável 409 | Motivo visível; estado anterior permanece |
| Preço negativo | API `422`; aviso ao salvar |
| PUT recado 200 | Quatro valores do corpo; zero mensagem ao hóspede |
| PUT recado 422 | `detail` visível; valores anteriores intactos |
| Gestão | GET sim; zero controle de escrita |
| Staff | Casca redireciona; zero fetch |

---

## Relacionamentos

```text
sessao recepção ──> GET /catalogo ──> TelaCatalogo
                         │                 ├─ Novo → POST /catalogo (categoria da aba)
                         │                 ├─ Editar → PATCH titulo/conteudo
                         │                 └─ Desativar/Reativar → PATCH ativo
                   GET /itens-vendaveis ──> TelaVendaveis
                         │                 ├─ Novo → POST nome + preco_atual
                         │                 ├─ Editar → PATCH nome e/ou preco_atual
                         │                 └─ Desativar/Reativar → PATCH ativo
                   GET /propriedade/boas-vindas ──> TelaBoasVindas
                                           └─ Salvar → PUT cafe, wifi, checkout, convite
sessao gestão ──> os três GET; zero POST/PATCH/PUT; sem botões
sessao staff ──> casca redireciona; zero fetch destas telas
```
