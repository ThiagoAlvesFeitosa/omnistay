# Quickstart — F3.8 Pulso do Segundo Dia

Validação ponta a ponta **depois** de `/speckit-implement`. Contratos:
[agendador-de-pulso.md](./contracts/agendador-de-pulso.md),
[fila-e-worker.md](./contracts/fila-e-worker.md),
[roteamento-resposta.md](./contracts/roteamento-resposta.md).
Modelo: [data-model.md](./data-model.md).

## Pré-requisitos

- PostgreSQL 16 e `DATABASE_URL` (como o restante da suíte)
- Migrações até `0016_pulso_segundo_dia`
- Sem WhatsApp real e sem LLM real — `MensageriaFalsa` e `LLMFalso`

```bash
pytest testes/unitarios -q
pytest testes/integracao -q -k pulso
```

## 1. Semente do prazo

Hotel novo (bootstrap) tem `horas_minimas_para_pulso = 24`. Hotel migrado
recebe a mesma chave na `0016` (idempotente).

```sql
SELECT valor FROM parametro_hotel
 WHERE id_hotel = :id AND chave = 'horas_minimas_para_pulso';
```

**Esperado:** `24`. Apagar a chave e rodar a varredura: 0 trabalhos
`enviar_pulso`; log `prazo_ausente`.

## 2. Estadia elegível agenda exatamente um pulso

Reserva `hospedado`, `checkin_em` no dia UTC anterior, checkout previsto daqui
a ≥ 1 dia civil, sem reclamação aberta:

```bash
python -m worker --verificar-pulsos
```

**Esperado:** 1 `trabalho` `enviar_pulso` + 1 mensagem pendente. Segunda
passagem: 0 extras. Segundo INSERT manual: violação de
`uq_trabalho_enviar_pulso_reserva`.

`--uma-passagem` **não** cria esse trabalho.

## 3. Supressões

| Cenário | `enviar_pulso` |
| --- | --- |
| Ainda no dia do check-in | 0 |
| Reclamação `aberta` | 0 |
| Só toalha / consumo pendente | 1 (se o resto elegível) |
| Sinal humano na fila, sem reclamação | 1 |
| Saída prevista hoje (0 h restantes) | 0 |

## 4. Envio e resposta dona do turno

Com o trabalho pendente, `python -m worker --uma-passagem` (ou o processador
direto) marca a pergunta enviada via falsa (`tipo=pulso`).

Mensagem do hóspede classificada **neutra**, intenção fora de dúvida/pedido/
reclamação:

**Esperado:** 1 `avaliacao` origem `pulso_segundo_dia`; 1 recado de
reconhecimento **sem** afirmar satisfação; 0 chamados. A mesma redação vale
para sentimento positivo.

Mensagem **negativa** no mesmo recorte:

**Esperado:** confirmação diz que a recepção foi avisada e que alguém vai
falar; **não** pergunta horário; 1 `solicitacao` `reclamacao`; ordem: enviada
antes do INSERT.

## 5. Um recado quando o operacional já respondeu

Pulso enviado + pedido de toalha (ou dúvida coberta):

**Esperado:** recado operacional existente; **0** “obrigado por responder”;
avaliação de pulso gravada. Reclamação técnica na janela: 1 chamado, 1
confirmação da F3.5, 0 segundo recado de pulso.

## 6. Isolamento

Hotel A com reclamação aberta não impede o pulso elegível do hotel B no mesmo
telefone.

## 7. Log

Nenhum dos desfechos acima coloca pergunta, resposta, reconhecimento ou
confirmação no log — só ids e códigos.

## Fora deste guia

Telas React, pesquisa de checkout, consentimento, janela noturna de disparo,
edição do prazo no painel.
