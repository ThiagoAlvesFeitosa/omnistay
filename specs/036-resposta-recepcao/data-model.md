# Data model: A recepção responde ao hóspede

Nenhuma tabela nova. Revisão `0025` altera CHECK, um índice único
e a visão da fila. Documento vivo: `docs/04-schema.sql` no mesmo
commit.

---

## `mensagem` (intocada na forma)

Colunas usadas:

| Coluna | Uso nesta fatia |
| --- | --- |
| `id_mensagem` | identificador da resposta e payload do trabalho |
| `id_reserva` | conversa da estadia |
| `direcao` | `recebida` (hóspede) / `enviada` (casa) |
| `conteudo` | texto; a API devolve à recepção; **nunca** em log nem no payload |
| `classificacao_bruta` | JSON: resposta humana `{"tipo": "resposta_recepcao"}` |
| `status_envio` | só enviadas: `pendente` → `enviada` / `falha` (retry pode voltar a tentar com o trabalho) |
| `enviada_em` | ordem do histórico; âncora da janela (nas recebidas) |

Janela aberta: existe recebida com `enviada_em >= agora() - 24 hours`.

Origem na API (não persistida como coluna):

- `hospede` — `direcao = recebida`
- `recepcao` — enviada com `tipo = resposta_recepcao`
- `automatico` — demais enviadas

---

## `trabalho` (delta `0025`)

`ck_trabalho_tipo` ganha **`enviar_resposta_recepcao`**.

| Campo | Valor |
| --- | --- |
| `tipo` | `enviar_resposta_recepcao` |
| `payload` | `{id_reserva, id_mensagem}` |
| `status` | `pendente` → `processando` → `concluido` / `falha` |

```sql
CREATE UNIQUE INDEX uq_trabalho_enviar_resposta_recepcao_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'enviar_resposta_recepcao';
```

Uma mensagem, um trabalho. Segunda resposta da recepção = outra
linha em `mensagem` + outro trabalho.

---

## `vw_fila_do_dia` (delta `0025`)

`precisa_atendimento_humano` permanece booleano derivado.

Verdadeiro quando:

1. `reserva.status = hospedado`
2. existe `mensagem` recebida com `tipo = classificacao_intencao` e
   `desfecho` em (`encaminhado_humano`, `formato_invalido`,
   `indisponivel`, `duvida_nao_coberta`, `item_ambiguo`,
   `identificacao_indisponivel`)
3. `enviada_em` dessa recebida é **posterior** a
   `MAX(enviada_em)` das enviadas com `tipo = resposta_recepcao`
   nesta reserva (se não houver nenhuma, a condição 3 vale)

O `GET /fila-do-dia` já devolve o campo; a tela passa a usá-lo.

---

## `solicitacao`

Intocada. POST de resposta **não** altera `status`, responsável
nem instante de resolução.

---

## Validação (serviço)

| Regra | Efeito |
| --- | --- |
| Texto vazio / só espaços | `422` — nada gravado |
| Texto > 4096 caracteres | `422` — nada gravado |
| Janela fechada | `409` `janela_fechada` — nada gravado |
| Texto idêntico ao da última `resposta_recepcao` da reserva com `enviada_em` há menos de 5 s | `409` `texto_repetido` — nada gravado |
| Reserva de outro hotel / inexistente | `404` |
| Perfil ≠ recepção | `403` |
| Reserva da casa, janela aberta, texto válido | INSERT enviada `pendente` + JSON + trabalho; HTTP sem esperar envio |

Relógio: `app.comum.relogio.agora`. Constantes no módulo `conversa`:
`JANELA_SESSAO_CANAL_HORAS = 24`, `TAMANHO_MAXIMO_TEXTO_CANAL = 4096`,
`SEGUNDOS_ANTI_DUPLO = 5`.

---

## Transição de entrega da resposta

```text
pendente  →  enviada   (worker, canal aceitou)
pendente  →  falha     (esgotou tentativas / telefone ausente)
falha     →  (nova tentativa do trabalho, se a fila ainda retentar)
```

A tela distingue **enviando** / **enviada** / **falhou** (e **nova
tentativa marcada** se a fila ainda retenta). Não afirma entregue
se `entrega` não for `enviada`.

---

## Relacionamentos

```text
reserva 1 ── * mensagem
mensagem 1 ── 0..1 trabalho (tipo enviar_resposta_recepcao, pela id)
reserva 1 ── * solicitacao     (intocada por esta fatia)
```
