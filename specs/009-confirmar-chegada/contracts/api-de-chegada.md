# Contrato — API de chegada e de informações de entrada

Três rotas novas. Todas exigem sessão válida (cookie `omnistay_sessao`) e operam **sempre** no
`id_hotel` da sessão.

---

## `POST /reservas/{id_reserva}/chegada`

Confirma a chegada do hóspede. Operação: `confirmar_fase_da_reserva` (já existente; só
`recepcao`).

**Corpo da requisição:** vazio.

**Resposta `200`:**

```json
{
  "id_reserva": 42,
  "status": "hospedado",
  "checkin_em": "2026-08-17T14:32:07.481Z",
  "boas_vindas": "agendada"
}
```

| Campo | Valores |
| --- | --- |
| `status` | Sempre `hospedado` numa resposta `200` |
| `checkin_em` | Instante da confirmação, com fuso |
| `boas_vindas` | `agendada` \| `nao_enviada_slot_ausente` \| `ja_agendada` |

`boas_vindas` é o desfecho do **registro** da pendência, não da entrega: a entrega é do
worker. `ja_agendada` só aparece na corrida improvável em que outra execução registrou o
trabalho no mesmo instante — o check-in seguiu válido.

**Erros:**

| Código | Quando | Corpo |
| --- | --- | --- |
| `401` | Sessão ausente ou inválida | `{"detail": "Sessao ausente ou invalida."}` |
| `403` | Perfil não é recepção | `{"detail": "Perfil sem permissao para esta operacao."}` |
| `404` | Reserva inexistente **ou** de outro hotel | `{"detail": "Reserva nao encontrada."}` |
| `409` | Estado não admite a chegada (encerrada, cancelada, já hospedada, ainda aguardando cadastro) | `{"detail": "<motivo legível>"}` |

`404` para reserva de outro hotel é deliberado (FR-022): a resposta não distingue "não existe"
de "não é sua".

**Efeitos de uma resposta `200`, na mesma transação:**

1. `reserva.status = 'hospedado'`, `reserva.checkin_em = now()`
2. Se os três slots estão presentes e válidos: `mensagem` (`enviada`/`pendente`) com o texto
   montado **e** `trabalho` (`enviar_boas_vindas`) com `{id_reserva, id_mensagem}`
3. Se algum slot falta ou é inválido: nenhuma mensagem, nenhum trabalho, e a reserva passa a
   constar com `boas_vindas_nao_enviadas` na fila do dia

**Efeitos de `403`, `404` e `409`:** nenhum. Nada é gravado.

---

## `GET /propriedade/boas-vindas`

Lê os três textos de entrada da propriedade da sessão. Operação:
`ler_texto_de_boas_vindas` (`recepcao`, `gestor`).

**Resposta `200`:**

```json
{
  "cafe": "Cafe da manha das 7h as 10h",
  "wifi": "Wi-Fi: rede do hotel, senha na recepcao",
  "checkout": "Checkout ate as 12h"
}
```

Chave ausente na configuração vem como `null`. `403` para perfil operacional.

---

## `PUT /propriedade/boas-vindas`

Grava os três textos de uma vez. Operação: `alterar_texto_de_boas_vindas` (só `recepcao`).

**Corpo:**

```json
{
  "cafe": "Cafe da manha das 7h as 10h30",
  "wifi": "Wi-Fi: rede Hotel-Hospedes, senha 12345678",
  "checkout": "Checkout ate as 12h, bagagem fica na recepcao"
}
```

Os três campos são obrigatórios. **Gravação atômica:** se um valor for recusado, nenhum dos
três muda.

**Resposta `200`:** o mesmo formato do `GET`, com os valores gravados (após `strip`).

**Erros:**

| Código | Quando |
| --- | --- |
| `403` | Perfil diferente de recepção (inclui gestão, que só lê) |
| `422` | Valor vazio, só espaços, com quebra de linha, com tabulação, com 5+ espaços seguidos, ou acima de 255 caracteres |

Mensagem de `422` nomeia o campo recusado e o motivo, em português, sem repetir o valor
enviado.

**Fora do alcance desta permissão:** nenhuma outra chave de `parametro_hotel`. Não existe rota
para `horas_ate_reenvio`, `horas_corte_antes_checkin`, duração de sessão ou periodicidade de
coleta — nem nesta fatia, nem como efeito colateral dela (SC-014a).

---

## `GET /fila-do-dia` — campo novo na resposta

Operação inalterada (`ler_fila_do_dia`, só `recepcao`). Cada item ganha um campo:

```json
{
  "id_reserva": 42,
  "status": "hospedado",
  "chegada_nao_confirmada": false,
  "boas_vindas_nao_enviadas": true
}
```

| Campo | `true` quando |
| --- | --- |
| `chegada_nao_confirmada` | Entrada prevista venceu e a reserva não está hospedada nem cancelada |
| `boas_vindas_nao_enviadas` | A reserva está hospedada e nenhum recado de boas-vindas foi registrado |

Os dois nunca são `true` no mesmo item. Campos anteriores permanecem como estão — nada é
renomeado nem removido.
