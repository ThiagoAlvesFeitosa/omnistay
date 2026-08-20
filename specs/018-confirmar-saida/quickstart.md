# Quickstart — F4.1 Confirmar Saída e Pesquisa

Validação ponta a ponta **depois** de `/speckit-implement`. Contratos:
[api-de-saida.md](./contracts/api-de-saida.md),
[api-de-consentimento.md](./contracts/api-de-consentimento.md),
[fila-e-worker.md](./contracts/fila-e-worker.md),
[portas-pesquisa.md](./contracts/portas-pesquisa.md).
Modelo: [data-model.md](./data-model.md).

## Pré-requisitos

- PostgreSQL 16 e `DATABASE_URL`
- Migrações até `0017_confirmar_saida`
- Sem WhatsApp real e sem LLM real — `MensageriaFalsa` e `LLMFalso`

```bash
pytest testes/unitarios -q
pytest testes/integracao -q -k saida
```

## 1. Semente do prazo

Hotel novo (bootstrap) tem `horas_atribuicao_pesquisa_saida = 24`. Hotel
migrado recebe a mesma chave na `0017` (idempotente).

```sql
SELECT valor FROM parametro_hotel
 WHERE id_hotel = :id AND chave = 'horas_atribuicao_pesquisa_saida';
```

**Esperado:** `24`. Apagar a chave: resposta do hóspede **não** vira nota
nem consentimento; log `prazo_ausente`; sinal humano na fila.

## 2. Clique encerra e agenda exatamente uma pesquisa

Reserva `hospedado` da propriedade da sessão, cookie de recepção:

```http
POST /reservas/{id}/saida
```

**Esperado:** `200`, `status=encerrado`, `checkout_em` ≈ agora (≠ data
prevista), `pesquisa=agendada`. Uma linha `trabalho` tipo
`enviar_pesquisa_saida` + uma mensagem pendente. Segundo clique: `409`,
`checkout_em` intacto, 0 trabalhos extras. INSERT manual duplicado: violação
de `uq_trabalho_enviar_pesquisa_saida_reserva`.

Reclamação aberta ou consumo pendente **não** mudam o `200`.

Gestão ou staff: `403`. Hotel B no id do hotel A: `404`.

## 3. Destaque de saída vencida

Hospedada com `data_checkout_prevista` ontem: `GET /fila-do-dia` traz
`saida_nao_confirmada=true`. Saída prevista hoje: flag falso. Depois do
`POST …/saida`: reserva some desse destaque (encerrada limpa sai da fila).

## 4. Envio e resposta completa

Com o trabalho pendente, `python -m worker --uma-passagem` marca a pesquisa
enviada via falsa (`tipo=pesquisa_saida`). Corpo: três partes, sem
“extrato”/“conta”.

Webhook com texto que o falso devolve como nota 5 + aceite sim:

**Esperado:** 1 `avaliacao` origem `checkout` com nota 5; 1 `consentimento`
do titular, `concedido=true`, `origem=pesquisa_checkout`; 0 segunda
pesquisa; 0 lembrete.

Só a nota, sem aceite: avaliação gravada; **0** consentimentos. GET de
consentimento devolve `concedido=false` com `momento=null`.

## 5. Silêncio, irreconhecível e prazo

| Cenário | Avaliação checkout | Consentimento | Humano na fila |
| --- | --- | --- | --- |
| Não responde | 0 | 0 | não |
| Texto irreconhecível / IA caída | 0 (se nada válido) | 0 | sim (`pesquisa_saida_leitura_humana`) |
| Prazo apagado | 0 | 0 | sim |

## 6. Consulta histórica e revogação

Aceite na pesquisa, depois `POST /hospedes/{id}/consentimento` com
`concedido=false`, `origem=painel` (recepção ou gestão):

**Esperado:** `201`, linha nova; linha do aceite intacta. GET com `em` entre
os dois instantes: `concedido=true`. GET agora: `concedido=false` com
`momento` da revogação. Staff: `403`. Hotel B: `404`.

## 7. Roteamento

Mesmo telefone com `aguardando_cadastro` nova **e** encerrada com pesquisa
incompleta: a mensagem vai à ficha, não à pesquisa.

Falha de envio: reserva permanece `encerrado`; o mesmo trabalho é
retomado; 0 pesquisas distintas.
