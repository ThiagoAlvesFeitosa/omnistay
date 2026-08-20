# Modelo de dados — F4.1 Confirmar Saída e Pesquisa

Nenhuma tabela nova. `reserva.checkout_em`, `avaliacao` (origem `checkout`),
`consentimento` e a trigger `hospedado → encerrado` já existem na `0001`.
Revisão `0017_confirmar_saida`.

---

## Entidades

### Reserva (delta)

| Campo | Uso nesta fatia |
| --- | --- |
| `status` | `hospedado` → `encerrado` no clique |
| `checkout_em` | instante da confirmação (`now()`), não a data prevista |
| `data_checkout_prevista` | só o destaque de vencida (`< CURRENT_DATE`) |

`UPDATE` guardado: `WHERE status = 'hospedado' AND id_hotel = :hotel`.
Trigger recusa qualquer outro salto para `encerrado`. Chamado aberto e
consumo pendente **não** entram no `WHERE`.

### Avaliação de checkout (`avaliacao`)

| Campo | Uso nesta fatia |
| --- | --- |
| `id_reserva` | estadia encerrada |
| `origem` | sempre `checkout` (pulso permanece `pulso_segundo_dia`) |
| `nota` | 1–5; a linha **só nasce** com nota válida |
| `comentario` | opcional; pode ser preenchido depois na mesma linha |
| `respondida_em` | instante da **primeira** gravação da nota |

`uq_avaliacao_reserva_origem` = no máximo uma avaliação de checkout por
reserva. Pulso e checkout convivem. CHECK novo:
`origem <> 'checkout' OR nota IS NOT NULL` — pulso continua com nota nula.

Hotel chega por junção com `reserva`.

### Consentimento (`consentimento`)

Já modelado na `0001`. Esta fatia é o primeiro escritor.

| Campo | Uso |
| --- | --- |
| `id_hospede` | titular da reserva (pesquisa) ou hóspede da rota |
| `finalidade` | `comunicacao_marketing` |
| `concedido` | `true` aceite / `false` recusa ou revogação |
| `momento` | `now()` na inserção |
| `origem` | `pesquisa_checkout` (worker) · `painel` · `solicitacao_titular` |

**Nunca UPDATE.** Estado vigente em `em` = `ORDER BY momento DESC` com
`momento <= em`, limite 1. Zero linhas = não concedido (resposta, não
INSERT).

Titular da pesquisa: `reserva_hospede.titular = true`.

### Trabalho `enviar_pesquisa_saida`

| Campo | Valor |
| --- | --- |
| `tipo` | `enviar_pesquisa_saida` |
| `payload` | `{id_reserva, id_mensagem}` |
| Unicidade | parcial por reserva |

Pendente → worker envia; `concluido` no sucesso; falha de mensageria
reagenda o **mesmo** id. Índice
`uq_trabalho_enviar_pesquisa_saida_reserva`.

### Trabalho `interpretar_pesquisa_saida`

| Campo | Valor |
| --- | --- |
| `tipo` | `interpretar_pesquisa_saida` |
| `payload` | `{id_reserva, id_mensagem}` |
| Unicidade | parcial por `id_mensagem` |

`concluido` após gravar o que deu, ou após desvio a humano, ou após recusar
atribuição (prazo ausente / janela fechada). Sem backoff de extração.

### Parâmetro `horas_atribuicao_pesquisa_saida`

| | |
| --- | --- |
| Chave | `horas_atribuicao_pesquisa_saida` |
| Valor semeado | `24` (inteiro ≥ 1) |
| Eixo | `checkout_em` |
| Ausência / inválido | não atribui resposta; log `prazo_ausente`; sinal humano |

Bootstrap e revisão `0017` (idempotente, padrão `0007`/`0016`).

### Mensagem da pesquisa

Saída: corpo da lista numerada, gravada **antes** do envio; `enviada_em` no
sucesso. Entrada da resposta: `classificacao_bruta` com
`tipo = pesquisa_saida` e `desfecho` em
`completo` | `parcial` | `irreconhecivel` | `indisponivel` |
`formato_invalido` | `prazo_ausente` | `fora_da_janela`. Conteúdo nunca em
log.

---

## `vw_fila_do_dia` (delta)

Nova coluna:

```sql
(r.status = 'hospedado'
 AND r.data_checkout_prevista < CURRENT_DATE) AS saida_nao_confirmada
```

Nova coluna de leitura humana da pesquisa (desfecho da mensagem recebida):
`pesquisa_saida_leitura_humana`.

Filtro da visão:

```sql
WHERE r.status <> 'cancelada'
  AND r.data_checkin_prevista <= CURRENT_DATE
  AND (
        r.status <> 'encerrado'
        OR <pesquisa_saida_leitura_humana>
      )
```

Encerrada limpa continua fora. Encerrada com resposta irreconhecível
permanece no turno. `docs/04-schema.sql` (comentário da visão) acompanha —
é a correção da F1.1, que excluía todo `encerrado` porque ainda não havia
trabalho depois do checkout.

`ItemFilaDoDia` ganha `saida_nao_confirmada: bool` e
`pesquisa_saida_leitura_humana: bool` (default falso).

---

## Transição

```text
hospedado --[POST /reservas/{id}/saida]--> encerrado
```

Recusado (aplicação + trigger): qualquer origem que não seja `hospedado`.
Segundo clique: `409`, `checkout_em` intacto, 0 trabalhos novos (índice).

---

## Completude (domínio, não coluna)

| Tem nota checkout | Tem consentimento desta pesquisa | Estado |
| --- | --- | --- |
| não | não | incompleta; silêncio ok |
| sim | não | incompleta; próxima mensagem na janela pode completar o aceite |
| não | sim | incompleta; próxima mensagem na janela pode completar a nota |
| sim | sim | completa; mensagem posterior não altera |

“Tem consentimento desta pesquisa” = existe linha do titular com
`origem = pesquisa_checkout` ligada a esta estadia (via titular da reserva)
**depois** de `checkout_em`. Revogação posterior no painel não reabre a
pesquisa.
