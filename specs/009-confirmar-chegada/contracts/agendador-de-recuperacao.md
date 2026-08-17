# Contrato — recuperação das boas-vindas do dia

Continuação da varredura criada na F1.4. **Nenhum agendador novo**: uma função na mesma
`worker/agendador.py` e uma flag no mesmo `python -m worker`.

---

## Assinatura

`worker/agendador.py`

```python
CHAVE_VALIDADE_BOAS_VINDAS = "horas_validade_boas_vindas"


def verificar_boas_vindas_pendentes(
    conexao,
    *,
    agora=None,
    repositorio_propriedade=...,
    agendar=...,
) -> int: ...
```

Devolve quantas reservas receberam pendência de recado nesta passagem. `agora` aceita instante
ou callable, como em `verificar_cadastros_pendentes`, e é o que permite testar a virada de dia
sem esperar a meia-noite.

## Elegibilidade

Uma reserva entra na passagem quando **todas** as condições valem:

| Condição | Onde é avaliada |
| --- | --- |
| `status = 'hospedado'` | SQL |
| `checkin_em IS NOT NULL` | SQL |
| Não existe trabalho `enviar_boas_vindas` para ela | SQL (`NOT EXISTS`) |
| `checkin_em >= agora - horas_validade_boas_vindas` | Python, com o prazo daquele hotel |

A consulta vive em `hospedagem/repository.py`
(`listar_hospedados_sem_boas_vindas`), porque lê `reserva`. Retorna `id_reserva`,
`id_hotel`, `checkin_em`, `nome_completo`.

**A janela conta do instante do check-in, nunca de data de calendário.** Chegada às 23h30 com
slot vazio, slots preenchidos às 23h40 e passagem às 00h05 continuam elegíveis — com
`CURRENT_DATE`, a reserva sairia da lista à meia-noite e o pacote nunca sairia, sem erro nenhum.
`data_checkin_prevista` não participa da decisão.

## Sequência

1. Lista as reservas candidatas (todas as propriedades; a varredura não tem sessão).
2. Para cada `id_hotel` novo, lê `horas_validade_boas_vindas` (cache por hotel, como
   `_prazos_do_hotel`). Valor ausente ou não inteiro positivo → log `prazo_ausente` e as
   reservas daquele hotel são puladas. **Nenhum prazo é suposto.**
3. Descarta a reserva cujo `checkin_em` é anterior a `agora - prazo`.
4. Para as restantes, chama `conversa_service.agendar_boas_vindas` com o `id_hotel` da reserva.
5. Slots ainda inválidos → devolve `nao_enviada_slot_ausente`, nada é gravado, e a reserva
   continua candidata na passagem seguinte (até sair pela janela).
6. Slots válidos → nasce a pendência, e a reserva sai da lista porque o trabalho passa a
   existir. Log `boas_vindas_recuperadas id_reserva id_hotel`.

O envio em si continua sendo do consumidor, no ciclo normal da fila.

## Limites que o contrato garante

| Garantia | Como |
| --- | --- |
| Chegada antiga não recebe envio automático | Comparação com a janela do hotel |
| Virada do dia civil não retira ninguém da fila de recuperação | O eixo é `checkin_em`, não `CURRENT_DATE` |
| Chegada antecipada é alcançada | Também decorre do eixo ser `checkin_em` |
| `hospedado` sem instante de check-in não recebe envio | `checkin_em IS NOT NULL` no SQL |
| Reserva encerrada não recebe envio | Já excluída pelo `status = 'hospedado'` |
| Prazo não é constante de código | `horas_validade_boas_vindas` em `parametro_hotel` |
| Nenhuma reserva recebe dois recados | Índice único; o `NOT EXISTS` só evita trabalho inútil, não é a garantia |
| Passagens repetidas são inócuas | Depois da primeira, a reserva não aparece mais na consulta |
| Duas execuções simultâneas | A segunda tem a inserção recusada pelo índice; `agendar_boas_vindas` devolve `ja_agendada` |

## Acionamento

`worker/__main__.py` ganha `--verificar-boas-vindas` (uma passagem e encerra), no molde de
`--verificar-cadastros`. No modo contínuo, a recuperação roda no mesmo ciclo horário da
verificação de cadastros — sem intervalo novo e sem parâmetro de periodicidade novo.

Atraso de um ciclo adia o recado; não o duplica e não o perde. Só a passagem da janela retira a
reserva da elegibilidade, e aí ela mantém a sinalização na fila — que é a regra de validade
curta decidida na spec, agora medida no eixo certo.

## O que esta função não faz

- Não envia mensagem (só registra a pendência).
- Não alcança reserva fora da janela de validade, nem por flag.
- Não usa data de calendário para decidir elegibilidade.
- Não supõe prazo quando a propriedade não tem o valor configurado.
- Não altera status de reserva.
- Não valida slot com regra própria — reusa a função pura da propriedade.
