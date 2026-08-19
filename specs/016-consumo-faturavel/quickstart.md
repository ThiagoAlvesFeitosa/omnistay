# Quickstart — validar a entrega de Consumo Faturável

Roteiro manual além da suíte. Contratos em [contracts/](./contracts/).

Comandos em PowerShell, na raiz do repositório. Use `curl.exe`.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. API no ar. Worker com `LLMFalso` (padrão de
`python -m worker --uma-passagem`). **Não** aponte a suíte nem este roteiro a
provedor de IA ou WhatsApp de verdade.

Hotel + usuários dos três perfis. Reserva **hospedada**. Item vendável ativo
(cenários cobrados) ou nenhum (cenário toalha).

---

## Cenário 0 — Esquema

```powershell
alembic current
```

Tabela `item_vendavel`. Triggers de especialização e de lançamento. CHECK de
autor no terminal. `vw_fila_do_dia` inclui `item_ambiguo` e
`identificacao_indisponivel`. `ck_trabalho_tipo` **igual** à `0014` (sem tipo
novo).

---

## Cenário 1 — Manutenção do item vendável

Login recepção:

```text
POST /itens-vendaveis
{"nome": "Cerveja", "preco_atual": "12.00"}
```

**Esperado:** `201`, `ativo = true`. Gestão `GET /itens-vendaveis` vê o item;
`POST` da gestão é `403`. Staff `GET` é `403`. Hotel B não vê o item de A.

---

## Cenário 2 — Pedido cobrado (identificação única)

Configure o falso: `unico` no id da Cerveja, quantidade 1. Classificação
`pedido_de_servico`. Webhook: `duas cervejas no quarto 402` (a quantidade
efetiva é a do falso, não um parse solto).

```powershell
python -m worker --uma-passagem
```

**Esperado:**

- `registrar_pedido_servico` `concluido`
- recebida: `resposta = confirmacao_consumo`, `desfecho = classificado`,
  `id_solicitacao` preenchido
- enviada com `R$ 12,00`, sem “extrato” nem “conta”, sem afirmar lançamento
- `solicitacao.tipo = consumo` + `consumo.valor_praticado = 12.00`,
  `status_lancamento = pendente`
- `GET /fila-do-dia`: `precisa_atendimento_humano = false`
- `GET /solicitacoes` (staff): item com valor, **sem** nome/telefone
- `GET /consumos/pendentes`: o mesmo consumo

---

## Cenário 3 — Toalha continua sem cobrança

Propriedade **sem** item ativo (ou falso em `nenhum`). Webhook: `toalha extra`.

**Esperado:** `tipo = servico`, zero linha em `consumo`, confirmação sem preço,
ausente de `GET /consumos/pendentes`, presente em `GET /solicitacoes`.

---

## Cenário 4 — Identificação ambígua ou IA caída

Falso em `ambiguo` ou `FalhaDeIdentificacao`. Webhook de pedido.

**Esperado:** zero `consumo`, zero valor na enviada, `desfecho` humano,
`precisa_atendimento_humano = true`, trabalho `concluido`.

---

## Cenário 5 — Resolver o quarto não lança

Com o consumo do cenário 2 ainda `pendente`, login staff:

```text
POST /solicitacoes/{id}/resolucao
```

**Esperado:** `200`, some de `GET /solicitacoes`, **permanece** em
`GET /consumos/pendentes`. Recado de conclusão sem valor e sem “lançado”.

---

## Cenário 6 — Lançar (só recepção)

Login recepção:

```text
POST /solicitacoes/{id}/lancamento
```

**Esperado:** `200` com autor e instante; some da fila destacada; valor
inalterado. Segundo POST: `409`. Staff e gestão no mesmo POST: `403`. Hotel B:
`404`.

PATCH do item para `preco_atual = 20`: o consumo lançado **continua 12.00**.
Novo pedido depois do reajuste nasce com 20.00.

---

## Cenário 7 — Dispensar

Outro consumo `pendente`. Recepção:

```text
POST /solicitacoes/{id}/dispensa
```

**Esperado:** sai da fila; `status_lancamento = dispensado`; **não** é
`lancado`. Gestão `403`.

---

## Cenário 8 — Log

Nos desfechos acima, o log tem ids e resultado. **Não** tem o texto do hóspede
nem o da confirmação.

---

## O que este roteiro não cobre

Lista ao hóspede no checkout (F4.2), tela React, débito real no PMS, provedor
de IA verdadeiro.
