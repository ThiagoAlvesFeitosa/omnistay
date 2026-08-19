# Modelo de dados — Consumo Faturável e Fila de Lançamento

Complementa o esquema já existente. Referência documental: `docs/04-schema.sql`.
Migração prevista: `0015_consumo_faturavel`.

Tabela nova: `item_vendavel`. Tabela `consumo` **já existe** desde a `0001` e
passa a ser escrita. Delta também: triggers de especialização e de lançamento,
CHECK de autor no estado terminal, dois desfechos na `vw_fila_do_dia`.
Nenhuma coluna nova em `solicitacao`. Nenhum tipo novo em `trabalho`.

---

## Máquina de estados de `consumo.status_lancamento`

```text
pendente ──► lancado      (terminal)
         └──► dispensado  (terminal)
```

| De | Para | Quem dispara | Recusado |
| --- | --- | --- | --- |
| *(insert)* | `pendente` | `abrir_consumo` | nascer `lancado` ou `dispensado` |
| `pendente` | `lancado` | `POST .../lancamento` | — |
| `pendente` | `dispensado` | `POST .../dispensa` | — |
| `lancado` | qualquer | — | sim (aplicação `409` + trigger) |
| `dispensado` | qualquer | — | sim |

`solicitacao.status` é **ortogonal**: `aberta` → `resolvida` (F3.6 estendida)
não altera `status_lancamento`.

---

## Entidades

### `item_vendavel` (nova)

Cadastro da propriedade. Governada por `propriedade`. Fonte do preço **atual**.

| Campo | Restrições | Papel |
| --- | --- | --- |
| `id_item_vendavel` | PK | identificador no prompt e no resultado da porta |
| `id_hotel` | FK, NOT NULL | Artigo XIV |
| `nome` | VARCHAR(160), NOT NULL | rótulo; `consumo.descricao_item` no instante |
| `preco_atual` | NUMERIC(10,2), NOT NULL, CHECK >= 0 | vigente; **não** é o histórico |
| `ativo` | BOOLEAN, NOT NULL, default TRUE | desativar não apaga |
| `atualizado_em` | TIMESTAMPTZ, NOT NULL, default now() | manutenção |

Índices:

- `ix_item_vendavel_hotel_ativo` em `(id_hotel) WHERE ativo`
- `uq_item_vendavel_hotel_nome_ativo` em `(id_hotel, lower(nome)) WHERE ativo`

Hotel B não lê linha de A. Item inativo sai da identificação e permanece na
manutenção.

Não há FK de `consumo` para esta tabela: o valor praticado é retrato, não
referência.

### `solicitacao` (INSERT tipo `consumo`; UPDATE de resolução)

Nesta fatia nasce com `tipo = 'consumo'`, `status = 'aberta'`, `urgencia`
copiada da mensagem, `janela_preferencia` nula, `id_usuario_responsavel` nulo,
`id_mensagem_origem` = a recebida. Quarto: texto extraído ou nulo.

Resolução operacional (recepção ou staff): mesmo `UPDATE` da F3.6, agora
também para este tipo. `status = resolvida` **não** exige `consumo` lançado.

`GET /solicitacoes` continua `status IN ('aberta', 'em_andamento')` — resolvida
sai da fila operacional.

### `consumo` (INSERT + UPDATE de lançamento)

Especialização 1:1. PK = `id_solicitacao`.

| Campo | No INSERT | No lançar | No dispensar |
| --- | --- | --- | --- |
| `descricao_item` | nome do item (máx. 160) | intocado | intocado |
| `valor_praticado` | `preco_atual * quantidade` naquele instante | **intocado** | **intocado** |
| `status_lancamento` | `pendente` | `lancado` | `dispensado` |
| `id_usuario_lancamento` | NULL | usuário da sessão | o mesmo campo |
| `lancado_em` | NULL | `relogio.agora()` | o mesmo campo |

CHECK: `valor_praticado >= 0` (já existe). CHECK novo: se o status não é
`pendente`, autor e instante NOT NULL.

Índice parcial `ix_consumo_pendente_lancamento` já existe. A fila HTTP faz
JOIN `reserva` para filtrar `id_hotel`.

### `mensagem` enviada

| Caminho | `classificacao_bruta.tipo` | Conteúdo |
| --- | --- | --- |
| `unico` | `confirmacao_consumo` | recado com valor praticado |
| `nenhum` | `confirmacao_pedido` (F3.4) | recado sem preço |
| humano | `aviso_identificacao` | recado sem preço |

JSON da **recebida** (além dos eixos da F3.2):

| Caminho | `resposta` | `desfecho` |
| --- | --- | --- |
| `unico` | `confirmacao_consumo` | `classificado` |
| `nenhum` | `confirmacao_pedido` | `classificado` |
| ambíguo | `aviso_identificacao` | `item_ambiguo` |
| indisponível / inválido | `aviso_identificacao` | `identificacao_indisponivel` |

`unico` também guarda `id_item_vendavel` e `quantidade` no JSON — auditoria da
identificação, não fonte do valor (o valor está em `consumo`).

JSON **não** inclui o texto do recado nem o conteúdo do hóspede.

### `trabalho`

Intocado. Continua `registrar_pedido_servico` com payload
`{id_reserva, id_mensagem}` e unique parcial por `id_mensagem`. Lançar e
dispensar **não** geram trabalho.

### `vw_fila_do_dia`

`DROP` + `CREATE`. O `IN` de `precisa_atendimento_humano` ganha
`item_ambiguo` e `identificacao_indisponivel`. Sem coluna nova. Sem incluir
consumo pendente nesse booleano.

### `reserva`, `usuario`, `parametro_hotel`, `catalogo_item`

Intocados. Status da reserva não entra em lançar/dispensar/resolver.

---

## Validação

| Regra | Onde mora |
| --- | --- |
| `consumo` só se o pai é tipo `consumo` | trigger BEFORE INSERT/UPDATE em `consumo` |
| tipo `consumo` tem filho ao commit | constraint trigger DEFERRABLE em `solicitacao` |
| valor não negativo | CHECK já em `consumo` + CHECK em `item_vendavel` |
| terminal tem autor e instante | CHECK |
| transição de lançamento | trigger |
| um consumo por mensagem | `uq_solicitacao_mensagem_origem` (já existe) |
| nome ativo único no hotel | unique parcial em `item_vendavel` |
| hotel da sessão | JOIN `reserva` / `item_vendavel.id_hotel` |
| payload da fila sem dado pessoal | só IDs (inalterado) |

---

## Relacionamentos

```text
hotel 1 ─── * item_vendavel
reserva 1 ─── * solicitacao
solicitacao 1 ─── 0..1 consumo     (obrigatório quando tipo = consumo)
usuario 1 ─── * consumo            (id_usuario_lancamento, no terminal)
mensagem 1 ─── 0..1 solicitacao    (id_mensagem_origem, unique)
```

Não há aresta `consumo → item_vendavel`.

---

## Inventário de esquema (delta da `0015`)

| Objeto | Ação |
| --- | --- |
| `item_vendavel` | CREATE TABLE + índices |
| `ck_consumo_terminal_tem_autor` | ADD (substitui o CHECK só de `lancado`) |
| `fn_consumo_pai_tipo_consumo` + trigger | CREATE |
| `fn_solicitacao_consumo_tem_filho` + constraint trigger DEFERRABLE | CREATE |
| `fn_valida_transicao_lancamento` + trigger | CREATE |
| `vw_fila_do_dia` | DROP/CREATE com dois desfechos a mais |
| `docs/04-schema.sql` | o mesmo delta, documento vivo |
| `ck_trabalho_tipo` | intocado |
| colunas de `solicitacao` / `consumo` | nenhuma nova |
