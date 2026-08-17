# Modelo de dados — Responder Dúvida a partir do Catálogo

Complementa o esquema já existente. Referência documental: `docs/04-schema.sql`.
Migração prevista: `0011_responder_duvida_catalogo`.

Nenhuma tabela nova. Nenhuma coluna nova em `mensagem`. O delta é o tipo de trabalho
`responder_duvida`, o índice único correspondente, e o desfecho
`duvida_nao_coberta` projetado em `vw_fila_do_dia`.

---

## Entidades envolvidas

### `mensagem` recebida (já classificada)

A linha da dúvida **não** tem o conteúdo alterado. Os eixos da F3.2 permanecem. Esta
fatia só estende `classificacao_bruta` quando a intenção é `duvida_geral`.

| Campo | Coberto (resposta automática) | Não coberto (aviso + chamado) |
| --- | --- | --- |
| `conteudo` | **intocado** | intocado |
| `intencao` | `duvida_geral` (já gravado) | idem |
| `sentimento` / `urgencia` | intocados | intocados |
| `classificacao_bruta.desfecho` | permanece `classificado` | passa a `duvida_nao_coberta` |
| `classificacao_bruta.resposta` | `automatica` | `aviso` |
| `classificacao_bruta.id_mensagem_resposta` | id da enviada | id da enviada (aviso) |

JSON **não** inclui o texto da pergunta nem o da resposta.

### Formato de `classificacao_bruta` após esta fatia

Coberto:

```json
{
  "tipo": "classificacao_intencao",
  "desfecho": "classificado",
  "intencao": "duvida_geral",
  "sentimento": "neutro",
  "urgencia": "baixa",
  "bruto": {},
  "resposta": "automatica",
  "id_mensagem_resposta": 42
}
```

Não coberto (catálogo vazio, fato ausente, redação não fiel, conversação indisponível):

```json
{
  "tipo": "classificacao_intencao",
  "desfecho": "duvida_nao_coberta",
  "intencao": "duvida_geral",
  "sentimento": "neutro",
  "urgencia": "baixa",
  "bruto": {},
  "resposta": "aviso",
  "id_mensagem_resposta": 43
}
```

`bruto` continua sendo o da **classificação** (F3.2). A conversação não o sobrescreve.

Desfechos da F3.2 que **não** entram nesta fatia (`encaminhado_humano`,
`formato_invalido`, `indisponivel`, e `classificado` de pedido/reclamação) permanecem
como estão.

### `mensagem` enviada (nova linha)

| Campo | Resposta automática | Aviso |
| --- | --- | --- |
| `direcao` | `enviada` | `enviada` |
| `conteudo` | texto fiel ao catálogo | recado padrão (recepção vai atender) |
| `status_envio` | `pendente` → `enviada` (ou `falha` se a mensageria esgotar) | idem |
| classificação | não se preenche | não se preenche |

Gravada **antes** da chamada à porta de envio. O recado padrão não contém fato de
catálogo.

### `trabalho`

| Campo | Uso |
| --- | --- |
| `tipo` | `responder_duvida` (novo no CHECK) |
| `payload` | `{id_reserva, id_mensagem}` — `id_mensagem` é a **recebida** |
| `status` | `pendente` → `processando` → **`concluido`** nos desfechos de redação (coberta, não coberta, não fiel, indisponível, catálogo vazio). Envio pode reagendar se a mensageria falhar **depois** de gravar |
| Unicidade | `uq_trabalho_responder_duvida_mensagem` |

`classificar_mensagem` permanece o da F3.2, com o acréscimo de inserir este tipo quando
a intenção é `duvida_geral`.

### `catalogo_item`

Somente leitura, via porta, `ativo = true` e `id_hotel` do trabalho. Item desativado
não entra. Hotel A não alimenta resposta do hotel B. Sem item ativo ≡ não coberta.

### `reserva`

Status **não** muda. Resolução de hotel: `id_hotel` do trabalho.

### `solicitacao`

Zero linhas criadas nesta fatia.

---

## Projeção: `vw_fila_do_dia`

`precisa_atendimento_humano` passa a ser verdadeiro também quando existe mensagem
recebida com `tipo = classificacao_intencao` e `desfecho = duvida_nao_coberta`.

```sql
AND mh.classificacao_bruta->>'desfecho'
    IN ('encaminhado_humano', 'formato_invalido', 'indisponivel',
        'duvida_nao_coberta')
```

Demais colunas da visão **inalteradas**. `GET /fila-do-dia` já devolve o booleano —
nenhum campo HTTP novo.

Resposta automática (`desfecho = classificado` + `resposta = automatica`) **não** liga
o flag.

---

## Delta SQL (congelar na revisão `0011`)

```sql
ALTER TABLE trabalho DROP CONSTRAINT ck_trabalho_tipo;
ALTER TABLE trabalho ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN ('enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
                    'enviar_boas_vindas', 'classificar_mensagem',
                    'responder_duvida'));

CREATE UNIQUE INDEX uq_trabalho_responder_duvida_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'responder_duvida';

DROP VIEW IF EXISTS vw_fila_do_dia;
CREATE VIEW vw_fila_do_dia AS
SELECT
    -- colunas atuais inalteradas ...
    (r.status = 'hospedado'
     AND EXISTS (
           SELECT 1 FROM mensagem mh
            WHERE mh.id_reserva = r.id_reserva
              AND mh.direcao = 'recebida'
              AND mh.classificacao_bruta->>'tipo' = 'classificacao_intencao'
              AND mh.classificacao_bruta->>'desfecho'
                  IN ('encaminhado_humano', 'formato_invalido', 'indisponivel',
                      'duvida_nao_coberta')
         )) AS precisa_atendimento_humano
  FROM ... -- mesmo FROM/WHERE da visão vigente
;
```

O `CREATE` completo copia a visão vigente após a `0010` e só amplia o `IN`.
`downgrade`: CHECK e visão da `0010`; `DROP INDEX` do único novo.

---

## Regras de validação

- Só `duvida_geral` + `desfecho` inicial `classificado` gera `responder_duvida`.
- Trechos citados: todos presentes no catálogo ativo daquele hotel e no texto
  enviado; senão o texto automático não sai.
- `UPDATE` da recebida não inclui `conteudo` no `SET`.
- `id_hotel` do trabalho em toda leitura de catálogo, mensagem e envio.
- Conteúdo da pergunta, da resposta e dos itens nunca em log.

---

## O que não muda nesta fatia

- Máquina de estados da reserva e `fn_valida_transicao_reserva`.
- CHECK de `intencao` / `sentimento` / `urgencia`.
- Tabela `solicitacao` / `consumo`.
- `estado_cadastro` (ficha).
- Payload de `evento_webhook`.
- Categorias e CRUD de `catalogo_item`.
