# Modelo de dados — Expurgo por Retenção

Referência: `docs/04-schema.sql`. Decisões em [research.md](./research.md).
Esta fatia cria **uma** tabela de domínio (`execucao_retencao`) e duas
chaves em `parametro_hotel`. As demais entidades já existem; aqui só se
define o que a passagem lê e escreve nelas.

---

## Entidades novas

### `execucao_retencao`

Comprovante de uma passagem efetiva (uma por hotel por dia civil UTC).
Não guarda texto tratado.

| Campo | Tipo | Restrições | Papel |
| --- | --- | --- | --- |
| `id_execucao` | `BIGSERIAL` | PK | Identificador |
| `id_hotel` | `BIGINT` | FK `hotel`, NOT NULL | Fronteira multi-tenant da consulta |
| `executado_em` | `TIMESTAMPTZ` | NOT NULL, default `now()` | Instante da passagem |
| `mensagens_anonimizadas` | `INTEGER` | NOT NULL, `>= 0`, default 0 | Linhas de `mensagem` cuja marca entrou agora |
| `comentarios_anonimizados` | `INTEGER` | NOT NULL, `>= 0`, default 0 | Comentários de `avaliacao` |
| `payloads_anonimizados` | `INTEGER` | NOT NULL, `>= 0`, default 0 | `evento_webhook.payload` |
| `descricoes_anonimizadas` | `INTEGER` | NOT NULL, `>= 0`, default 0 | `solicitacao.descricao` |
| `fichas_apagadas` | `INTEGER` | NOT NULL, `>= 0`, default 0 | `hospede` excluídos |
| `prazo_conteudo_ausente` | `BOOLEAN` | NOT NULL, default `false` | Chave de meses inválida/ausente nesta passagem |
| `prazo_ficha_ausente` | `BOOLEAN` | NOT NULL, default `false` | Chave de anos inválida/ausente nesta passagem |

Índice único:

```text
uq_execucao_retencao_hotel_dia
  ON (id_hotel, ((executado_em AT TIME ZONE 'UTC')::date))
```

Segunda inserção no mesmo dia UTC no mesmo hotel é rejeitada pelo banco
(Artigo IX). A aplicação trata colisão como “já executada hoje”.

Consultas da gestão: `WHERE id_hotel = :sessao ORDER BY executado_em DESC`.

---

## Entidades reusadas — o que muda

### `parametro_hotel`

| Chave | Valor semeado | Papel |
| --- | --- | --- |
| `meses_retencao_conteudo_livre` | `12` | Intervalo civil até anonimizar DPC da reserva |
| `anos_retencao_ficha` | `5` | Intervalo civil até apagar a ficha |

Inteiro ≥ 1. Ausência ou inválido: aquele tipo não roda (sem default).

### `reserva`

Eixo do relógio: só `checkout_em`. `data_checkout_prevista` não entra.
Após exclusão da última ficha vinculada, `telefone_contato` vira a marca
`anonimizado`. Demais colunas intactas.

### `mensagem`

`conteudo` → `[anonimizado]` quando a reserva venceu o prazo de conteúdo
livre e o valor ainda não é a marca. **Ambas as direções.** `classificacao_bruta` → `NULL`.
`intencao`, `sentimento`, `urgencia`, `direcao`, `enviada_em` intactos.

### `evento_webhook`

`payload` → `{"anonimizado": true}` quando `id_externo` casa com mensagem
da reserva elegível e o payload ainda não é a marca. `id_externo`
intacto.

### `solicitacao`

`descricao` → `[anonimizado]` no mesmo prazo, **somente se havia texto**
(`btrim <> ''`). Tipo, status, urgência, consumo filho, `numero_quarto` e
`janela_preferencia` intactos. Linha **não** é apagada nem muda de status.

### `avaliacao`

`comentario` com texto → `[anonimizado]`. `NULL` ou só espaços: não toca.
`nota`, `origem`, `respondida_em` intactos.

### `hospede` / `consentimento` / `reserva_hospede`

No prazo de ficha: consentimento some, vínculo some, ficha some. Sem
soft-delete.

---

## Relacionamentos

```text
hotel 1 ─── * execucao_retencao
hotel 1 ─── * reserva
reserva 1 ─── * mensagem
mensagem.id_externo ─── evento_webhook.id_externo   (vínculo lógico, sem FK)
reserva 1 ─── * solicitacao
reserva 1 ─── * avaliacao
reserva * ─── * hospede          (via reserva_hospede)
hospede 1 ─── * consentimento
```

---

## Ciclo de vida de uma passagem (por hotel)

```text
já existe execucao_retencao neste dia UTC?
        ↓ sim
  log retencao_ja_executada_hoje; 0 tratamentos
        ↓ não
  ler meses / anos (cada um pode faltar)
        ↓
  se meses válido: UPDATE DPC das reservas com checkout_em vencido
  se anos válido: DELETE fichas cuja última saída (todas as reservas) venceu
        ↓
  INSERT execucao_retencao (quantidades + flags de prazo)
  colisão UNIQUE → já executada hoje
```

---

## Regras de validação

| Regra | Onde |
| --- | --- |
| Quantidade de tipo tratado ≥ 0 | CHECK na tabela |
| Uma execução por hotel por dia UTC | UNIQUE expressão |
| `checkout_em` nulo ⇒ fora | Predicado SQL, não CHECK de tabela |
| Marca distinguível de vazio | Constante de domínio + `WHERE` |
| Hotel da sessão na leitura | `WHERE id_hotel = :sessao` |

---

## Estado / transições

Não há máquina de estados nova. `solicitacao.status` e `reserva.status`
**não** mudam por retenção. Anonimizar não é “cancelar chamado”.
Apagar ficha não é “cancelar reserva”.

---

## Fora do modelo desta fatia

- Coluna `anonimizado_em` nas tabelas operacionais
- `id_reserva` em `evento_webhook` (dívida; JOIN por `id_externo`)
- `id_hotel` em `hospede` (dívida da F1.1; isolamento via reserva)
- `solicitacao.janela_preferencia` e `numero_quarto` (não estão na lista DPC da spec)
- Pedido avulso de exclusão
- Auditoria genérica de UPDATE
