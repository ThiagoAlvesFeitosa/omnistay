# Modelo de dados — Classificar a Intenção

Complementa o esquema já existente. Referência documental: `docs/04-schema.sql`.
Migração prevista: `0010_classificar_intencao`.

Nenhuma tabela nova. Nenhuma coluna nova em `mensagem` (os três eixos e
`classificacao_bruta` já existem desde a `0001`). O delta é a projeção
`precisa_atendimento_humano` em `vw_fila_do_dia`.

---

## Entidades envolvidas

### `mensagem` (preenchimento nesta fatia)

| Campo | Classificação válida (ramo posterior) | Encaminhado humano (intenção sem ramo) | Formato inválido | Serviço indisponível |
| --- | --- | --- | --- | --- |
| `conteudo` | **intocado** | intocado | intocado | intocado |
| `intencao` | um dos três: `duvida_geral`, `pedido_de_servico`, `reclamacao_tecnica` | `upsell`, `solicitacao_de_checkout` ou `fora_de_escopo` | permanece `NULL` | permanece `NULL` |
| `sentimento` | `positivo` / `neutro` / `negativo` | idem | `NULL` | `NULL` |
| `urgencia` | `baixa` / `media` / `alta` | idem | `NULL` | `NULL` |
| `classificacao_bruta` | ver JSON abaixo | ver JSON abaixo | ver JSON abaixo | ver JSON abaixo |

`CHECK` já vigente: intenção, sentimento e urgência só admitem os valores acima ou
`NULL`. A aplicação valida **antes** do `UPDATE`; valor fora cai em `formato_invalido`,
não tenta gravar eixo inválido.

Mensagem de ficha (`tipo` de JSON `extracao_ficha`) **não** é sobrescrita por esta
fatia — o worker só processa `classificar_mensagem`, cujo payload aponta à mensagem da
estadia.

### Formato de `classificacao_bruta` (classificação de intenção)

```json
{
  "tipo": "classificacao_intencao",
  "desfecho": "classificado",
  "intencao": "reclamacao_tecnica",
  "sentimento": "negativo",
  "urgencia": "alta",
  "bruto": { }
}
```

| `desfecho` | `intencao` / `sentimento` / `urgencia` no JSON | `bruto` |
| --- | --- | --- |
| `classificado` | iguais às colunas | resposta completa do classificador |
| `encaminhado_humano` | iguais às colunas | resposta completa |
| `formato_invalido` | omitidos ou nulos | o que veio (mesmo ilegível) |
| `indisponivel` | omitidos | omitido |

`tipo` distingue extração de ficha (`extracao_ficha`, F1.3) desta classificação. A visão
da estadia **só** olha `tipo = classificacao_intencao`.

O JSON **não** inclui o texto da mensagem do hóspede.

### `trabalho` (consumo)

| Campo | Uso |
| --- | --- |
| `tipo` | `classificar_mensagem` (já no CHECK da `0009`) |
| `payload` | `{id_reserva, id_mensagem, id_evento}` — só IDs |
| `status` | `pendente` → `processando` → **`concluido`** em todo desfecho desta fatia (sucesso, humano por intenção, inválido, indisponível) |
| tentativas / backoff | **não** usados para o classificador |

Unicidade `uq_trabalho_classificar_mensagem_mensagem` permanece. Claim passa a incluir o
tipo (ver [contracts/fila-e-worker.md](./contracts/fila-e-worker.md)).

Já classificada (`desfecho` presente com `tipo = classificacao_intencao`): não chama o
LLM; só conclui o trabalho se ainda estiver aberto.

### `reserva` (somente leitura)

Status **não** muda. Resolução de hotel: `id_hotel` do trabalho / da reserva da
mensagem. Isolamento entre propriedades.

### `solicitacao`

Zero linhas criadas nesta fatia.

---

## Projeção: `vw_fila_do_dia`

Acrescentar **`precisa_atendimento_humano`** (boolean), derivado:

```sql
(r.status = 'hospedado'
 AND EXISTS (
       SELECT 1
         FROM mensagem mh
        WHERE mh.id_reserva = r.id_reserva
          AND mh.direcao = 'recebida'
          AND mh.classificacao_bruta->>'tipo' = 'classificacao_intencao'
          AND mh.classificacao_bruta->>'desfecho'
              IN ('encaminhado_humano', 'formato_invalido', 'indisponivel')
     )) AS precisa_atendimento_humano
```

Demais colunas da visão **inalteradas** (incluindo `estado_cadastro` e
`boas_vindas_nao_enviadas`).

`GET /fila-do-dia` devolve o booleano no item. Perfil operacional e gestão continuam
sem essa lista.

---

## Delta SQL (congelar na revisão `0010`)

```sql
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
                  IN ('encaminhado_humano', 'formato_invalido', 'indisponivel')
         )) AS precisa_atendimento_humano
  FROM ... -- mesmo FROM/WHERE da visão vigente
;

COMMENT ON VIEW vw_fila_do_dia IS
    '... e precisa_atendimento_humano (hospedado com mensagem de estadia '
    'encaminhada a pessoa: classificador falhou ou intencao sem ramo proprio).';
```

O `CREATE` completo copia a visão vigente (`docs/04-schema.sql` após a `0009`) e só
acrescenta a coluna. `downgrade`: recria a visão sem o booleano.

---

## Regras de validação

- Taxonomia fechada; fora da lista = `formato_invalido`, eixos `NULL`.
- `UPDATE` de eixos e JSON na mesma operação; `conteudo` fora do `SET`.
- `id_hotel` do trabalho conferido com a reserva da mensagem.
- Foto / texto vazio: se um trabalho órfão existir, `formato_invalido` / humano — não
  se inventa texto para mandar ao classificador.
- Conteúdo e `bruto` nunca em log.

---

## O que não muda nesta fatia

- Máquina de estados da reserva e `fn_valida_transicao_reserva`.
- `ck_trabalho_tipo` e o índice único de `classificar_mensagem`.
- `CHECK` de `intencao` / `sentimento` / `urgencia`.
- Tabela `solicitacao` / `consumo`.
- `estado_cadastro` (ficha).
- Payload de `evento_webhook`.
