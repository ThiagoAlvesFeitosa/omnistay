# Contrato — varredura do pulso do segundo dia

Modelo: [data-model.md](../data-model.md). Fila: [fila-e-worker.md](./fila-e-worker.md).

Nenhum agendador novo: uma função em `worker/agendador.py` e uma flag no mesmo
`python -m worker`.

---

## Assinatura

```python
CHAVE_MINIMO_PULSO = "horas_minimas_para_pulso"


def verificar_pulsos_pendentes(
    conexao,
    *,
    agora=None,
    repositorio_propriedade=...,
    tem_reclamacao_aberta=...,
    agendar=...,
) -> int: ...
```

Devolve quantas reservas receberam pendência de pulso nesta passagem. `agora`
aceita instante ou callable (UTC), como em `verificar_cadastros_pendentes`.

---

## Elegibilidade

Ver tabela em [data-model.md](../data-model.md). A listagem SQL vive em
`hospedagem` (`listar_hospedados_sem_pulso`): `hospedado`, `checkin_em` preenchido,
sem trabalho `enviar_pulso`. Devolve `id_reserva`, `id_hotel`, `checkin_em`,
`data_checkout_prevista`, `nome_completo`.

Reclamação aberta: `atendimento.tem_reclamacao_aberta(conexao, id_reserva=...)`
→ verdadeiro se existe `tipo=reclamacao` com status `aberta` ou `em_andamento`.

Horas restantes:

```text
24 * (data_checkout_prevista - data_utc(agora)).days
```

Segundo dia: `data_utc(agora) > data_utc(checkin_em)`.

Prazo ausente ou não inteiro ≥ 1: log `prazo_ausente id_hotel=…`, hotel inteiro
fora da passagem.

---

## Sequência por reserva elegível

Na mesma transação, **antes** de qualquer envio:

1. Montar o texto da pergunta (prenome + micro-pesquisa)
2. INSERT `mensagem` pendente
3. `enfileirar_enviar_pulso` (`id_reserva`, `id_mensagem`)

Colisão no índice único → tratar como já agendado (zero segundo recado), igual
às boas-vindas.

O worker envia depois. A varredura **não** chama a porta de mensageria.

---

## CLI

| Flag | Efeito |
| --- | --- |
| `--verificar-pulsos` | Uma passagem da varredura e encerra |
| `--uma-passagem` | **Não** chama esta função |
| modo contínuo | A cada ~1 h, depois de cadastros e boas-vindas |

Hotel B isolado: prazo, reclamação e trabalho de A não afetam B.
