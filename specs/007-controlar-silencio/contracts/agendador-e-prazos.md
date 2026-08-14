# Contrato: agendador e prazos da propriedade

Modelo: [data-model.md](../data-model.md). Envio: [mensageria-e-fila.md](./mensageria-e-fila.md).

Não é rota HTTP. A verificação é função de domínio/worker com relógio injetável.

---

## Entrada

| Parâmetro | Semântica |
| --- | --- |
| `agora` | Instante UTC (`app.comum.relogio`); testes substituem |
| Conexão | Transação da passagem |

Lê, por `id_hotel`: `horas_ate_reenvio`, `horas_corte_antes_checkin`.

---

## Instante de corte

```text
início_do_dia_utc(data_checkin_prevista) - horas_corte_antes_checkin
```

Data prevista de entrada já no passado (calendário UTC de `agora` > data) equivale a
“corte atingido”.

---

## Efeitos observáveis (por reserva `aguardando_cadastro`)

| Condição | Lembrete | Status |
| --- | --- | --- |
| Há mensagem `recebida` | não | inalterado (F1.3 manda) |
| Corte atingido ou data de entrada vencida, sem resposta | não | `sem_cadastro_previo` |
| `reenvio_realizado` | não | inalterado nesta etapa |
| Coleta ainda não `enviada` | não | inalterado (corte ainda pode marcar depois) |
| Silêncio ≥ `horas_ate_reenvio` desde coleta enviada, fora do corte | exatamente um | inalterado; `reenvio_realizado = true` |
| Segunda invocação após lembrete agendado | zero extras | inalterado até o corte |

Hotel sem prazo configurado: nenhum efeito nas reservas daquele hotel; log com
`id_hotel` + código (`prazo_ausente` / `prazo_invalido`), sem número mágico.

---

## Idempotência

Rodar a verificação duas vezes no mesmo instante não cria segundo lembrete nem segunda
transição (flag + índice único + `UPDATE` de status só a partir de `aguardando_cadastro`).

---

## Como acionar

| Superfície | Comportamento |
| --- | --- |
| `verificar_cadastros_pendentes` | Caminho da suíte |
| `python -m worker --verificar-cadastros` | Uma verificação e encerra (não consome a fila, ou consome depois — o plano de tasks fixa; o efeito de silêncio não depende do consumo) |
| Worker contínuo | Verifica quando a cadência (~1 h) vence; memória do último run pode ser do processo |
| `--uma-passagem` | Não verifica |

---

## Proibições

- Enviar lembrete de coleta que o hóspede não recebeu (`status_envio` ≠ `enviada`)
- Enviar lembrete dentro da janela de corte ou com data de entrada vencida
- Marcar `sem_cadastro_previo` se já houve resposta
- Usar prazo de um hotel em reserva de outro
- Logar corpo, telefone ou nome
