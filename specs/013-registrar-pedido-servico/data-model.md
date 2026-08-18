# Modelo de dados — Registrar Pedido de Serviço

Complementa o esquema já existente. Referência documental: `docs/04-schema.sql`.
Migração prevista: `0012_registrar_pedido_servico`.

Nenhuma tabela nova. Nenhuma coluna nova. O delta é o tipo de trabalho
`registrar_pedido_servico`, o índice único correspondente, e a unicidade de
`solicitacao.id_mensagem_origem`. A tabela `solicitacao` já existe desde a revisão
`0001` e passa a receber a primeira linha (tipo `servico`).

---

## Entidades envolvidas

### `mensagem` recebida (já classificada como pedido de serviço)

A linha do pedido **não** tem o conteúdo alterado. Os eixos da F3.2 permanecem.
Esta fatia só estende `classificacao_bruta` quando a intenção é `pedido_de_servico`.

| Campo | Depois do registro |
| --- | --- |
| `conteudo` | **intocado** |
| `intencao` | `pedido_de_servico` (já gravado) |
| `sentimento` / `urgencia` | intocados |
| `classificacao_bruta.desfecho` | permanece `classificado` |
| `classificacao_bruta.resposta` | `confirmacao_pedido` |
| `classificacao_bruta.id_mensagem_resposta` | id da enviada (confirmação) |
| `classificacao_bruta.id_solicitacao` | id da solicitação tipo serviço |

JSON **não** inclui o texto do pedido nem o da confirmação. `desfecho` **não**
passa a um valor que ligue `precisa_atendimento_humano`.

### Formato de `classificacao_bruta` após o registro

```json
{
  "tipo": "classificacao_intencao",
  "desfecho": "classificado",
  "intencao": "pedido_de_servico",
  "sentimento": "neutro",
  "urgencia": "baixa",
  "bruto": {},
  "resposta": "confirmacao_pedido",
  "id_mensagem_resposta": 50,
  "id_solicitacao": 7
}
```

`bruto` continua sendo o da **classificação** (F3.2).

Desfechos da F3.2 / F3.3 que **não** entram nesta fatia permanecem como estão.

### `mensagem` enviada (nova linha — confirmação)

| Campo | Valor |
| --- | --- |
| `direcao` | `enviada` |
| `conteudo` | recado padrão (pedido recebido; equipe vai atender) |
| `status_envio` | `pendente` → `enviada` (ou `falha` se a mensageria esgotar) |
| classificação | não se preenche |

Gravada **antes** da chamada à porta de envio **e** antes (na transação) do INSERT
em `solicitacao`. O recado não contém fato de catálogo, prazo nem janela de
preferência.

### `solicitacao`

Primeira escrita. Tipo operacional sem cobrança.

| Campo | Valor nesta fatia |
| --- | --- |
| `id_reserva` | do trabalho |
| `id_mensagem_origem` | a **recebida** |
| `tipo` | `servico` |
| `descricao` | `conteudo` da recebida |
| `numero_quarto` | extraído da recebida, ou `NULL` |
| `urgencia` | eixo da mensagem; se nulo, `media` |
| `janela_preferencia` | `NULL` |
| `status` | `aberta` |
| `id_usuario_responsavel` | `NULL` |
| `aberta_em` | agora |
| `resolvida_em` | `NULL` |

Zero linha em `consumo`. Hotel da linha: o de `reserva.id_hotel` (join). Unicidade:
`uq_solicitacao_mensagem_origem`.

### `trabalho`

| Campo | Uso |
| --- | --- |
| `tipo` | `registrar_pedido_servico` (novo no CHECK) |
| `payload` | `{id_reserva, id_mensagem}` — `id_mensagem` é a **recebida** |
| `status` | `pendente` → `processando` → **`concluido`** após gravar confirmação + solicitação e envio ok. Envio pode reagendar se a mensageria falhar **depois** de gravar |
| Unicidade | `uq_trabalho_registrar_pedido_servico_mensagem` |

`classificar_mensagem` permanece o da F3.2/F3.3, com o acréscimo de inserir este
tipo quando a intenção é `pedido_de_servico`.

### `reserva`

Status **não** muda. Resolução de hotel: `id_hotel` do trabalho / da sessão.

### `consumo`

Zero linhas criadas nesta fatia.

### `catalogo_item`

Não é lido. Pedido de serviço não consulta o catálogo.

---

## Extração de quarto (não é coluna nova)

Função pura. Entrada: texto da recebida. Saída: string até 10 caracteres ou nulo.

Padrões (casefold), primeiro match:

- `quarto` + número opcionalmente prefixado por `n` / `nº` / `n.°`
- `apto` / `apartamento` + número
- `uh` + número

Número: dígitos com letra opcional (`402`, `12A`). Sem palavra-chave → nulo. Não
consulta reserva nem outro hotel.

---

## Projeção HTTP: `GET /solicitacoes`

Não é visão SQL. Consulta: `solicitacao` JOIN `reserva` WHERE `reserva.id_hotel` da
sessão AND `status IN ('aberta', 'em_andamento')`. Ordenação: `aberta_em` crescente
(mais antigo primeiro — a equipe vê o que espera há mais tempo).

Item **sem** dado cadastral. Ver [contracts/api-de-atendimento.md](./contracts/api-de-atendimento.md).

`vw_fila_do_dia` **inalterada**. Pedido de serviço **não** liga
`precisa_atendimento_humano`.

---

## Delta SQL (congelar na revisão `0012`)

```sql
ALTER TABLE trabalho DROP CONSTRAINT ck_trabalho_tipo;
ALTER TABLE trabalho ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN ('enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
                    'enviar_boas_vindas', 'classificar_mensagem',
                    'responder_duvida', 'registrar_pedido_servico'));

CREATE UNIQUE INDEX uq_trabalho_registrar_pedido_servico_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'registrar_pedido_servico';

CREATE UNIQUE INDEX uq_solicitacao_mensagem_origem
    ON solicitacao (id_mensagem_origem)
    WHERE id_mensagem_origem IS NOT NULL;
```

`downgrade`: CHECK da `0011`; `DROP INDEX` dos dois únicos novos.

---

## Regras de validação

- Só `pedido_de_servico` + `desfecho` inicial `classificado` gera
  `registrar_pedido_servico`.
- Confirmação gravada na transação **antes** do INSERT da solicitação.
- `tipo` da linha desta fatia é sempre `servico`; `consumo` não é inserido.
- `UPDATE` da recebida não inclui `conteudo` no `SET`.
- `id_hotel` do trabalho em toda leitura de reserva/mensagem e no filtro de
  `listar_abertas`.
- Conteúdo do pedido e da confirmação nunca em log.
- Segundo INSERT com o mesmo `id_mensagem_origem` viola
  `uq_solicitacao_mensagem_origem`.
- Segundo INSERT `registrar_pedido_servico` para o mesmo `id_mensagem` viola
  `uq_trabalho_registrar_pedido_servico_mensagem`.

---

## O que não muda nesta fatia

- Máquina de estados da reserva e `fn_valida_transicao_reserva`.
- CHECK de `intencao` / `sentimento` / `urgencia` / `solicitacao.tipo`.
- Tabela `consumo` (sem linhas).
- `vw_fila_do_dia` e `precisa_atendimento_humano`.
- Payload de `evento_webhook`.
- Catálogo.
- Colunas de `solicitacao` (já existentes).
