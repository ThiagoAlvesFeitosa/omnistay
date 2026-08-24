# Contrato: agendador e retenção

A passagem aplica a política no banco e grava o comprovante. Não enfileira
trabalho. Modelo: [data-model.md](../data-model.md). Marcas e predicados:
[anonimizacao-e-exclusao.md](./anonimizacao-e-exclusao.md).

---

## Flag e cadência

```text
python -m worker --verificar-retencao
```

- Relógio injetável (`agora`), padrão o relógio da aplicação.
- `--uma-passagem` **não** dispara esta varredura.
- Modo contínuo: a passagem horária já existente chama
  `verificar_retencao` junto com cadastros, boas-vindas, pulsos e mercado.
- Sem APScheduler. Efetividade diária: no máximo uma `execucao_retencao`
  por hotel por dia civil UTC.

---

## `verificar_retencao(conexao, *, agora=None) -> int`

Para cada hotel:

1. Se já existe comprovante daquele hotel com
   `(executado_em AT TIME ZONE 'UTC')::date` igual ao dia UTC de `agora`:
   log `retencao_ja_executada_hoje`; não trata; segue o próximo hotel.
2. Lê `meses_retencao_conteudo_livre` e `anos_retencao_ficha` (cache por
   hotel). Cada um inválido/ausente → flag correspondente no comprovante
   e log `prazo_conteudo_ausente` / `prazo_ficha_ausente`; **não** usa
   12 nem 5 embutidos.
3. Se meses válido: pede a `conversa`, `atendimento` e `feedback` que
   anonimizem o vencido daquele hotel; soma as quantidades devolvidas.
4. Se anos válido: pede a `hospedagem` que apague fichas vencidas daquele
   hotel; soma `fichas_apagadas`.
5. INSERT em `execucao_retencao` com instante, quantidades e flags.
   Colisão do UNIQUE do dia → trata como já executada (não falha a
   passagem dos outros hotéis).

Devolve quantos hotéis **receberam** comprovante novo nesta chamada
(0 se todos já tinham o dia). Hotel sem reserva vencida: comprovante com
zeros, não é erro.

A varredura **não** envia mensagem ao hóspede. **não** confirma fase.
**não** chama PMS.

---

## Relógio

`agora` é o único “agora”. Testes avançam o relógio; a função não lê
`datetime.now()` direto. Comparações usam `checkout_em` da reserva, nunca
`data_checkout_prevista`.

---

## Transação

A chamada do worker (`engine.begin()`) envolve a passagem inteira, no
padrão das outras verificações. Idempotência do `WHERE` (marca) e do
UNIQUE do dia tornam um retry seguro.

---

## Fora deste contrato

- Tipo novo em `trabalho`
- Consumo no `worker/consumidor.py`
- Disparo via HTTP
