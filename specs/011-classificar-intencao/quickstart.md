# Quickstart — validar a entrega de Classificar a Intenção

Roteiro manual além da suíte. Contratos em [contracts/](./contracts/).

Comandos em PowerShell, na raiz do repositório. Use `curl.exe`.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. API no ar. Worker com `LLMFalso` (padrão do
`python -m worker --uma-passagem` quando não há adaptador real). Não aponte a suíte
nem este roteiro a provedor de IA de verdade.

Hotel + recepção autenticada como nos quickstarts anteriores. Reserva **hospedada**
com mensagem de estadia já gravada (F3.1): `POST /webhook` assinado com o telefone
da reserva → `trabalho` `classificar_mensagem` `pendente`.

---

## Cenário 0 — Esquema

```powershell
alembic current
```

A visão `vw_fila_do_dia` tem `precisa_atendimento_humano`. `mensagem` já tem
`intencao`, `sentimento`, `urgencia`, `classificacao_bruta` — esta fatia não cria
coluna nessas tabelas.

---

## Cenário 1 — Classificação válida (dúvida geral)

Com o item `pendente` de uma mensagem de estadia e o falso no padrão (ou configurado
para `duvida_geral` / `neutro` / `baixa`):

```powershell
python -m worker --uma-passagem
```

**Esperado:**

- `trabalho.status = concluido`
- `mensagem.intencao = duvida_geral` (e os outros dois eixos preenchidos)
- `classificacao_bruta.tipo = classificacao_intencao`
- `classificacao_bruta.desfecho = classificado`
- `conteudo` idêntico ao de antes
- zero `mensagem` `enviada` nova
- zero linha em `solicitacao`
- `GET /fila-do-dia` (cookie de recepção): `precisa_atendimento_humano = false`
- `reserva.status` continua `hospedado`

---

## Cenário 2 — Serviço indisponível

Configure o falso para falhar a classificação. Nova mensagem + trabalho pendente.

```powershell
python -m worker --uma-passagem
```

**Esperado:** conteúdo intacto; eixos `NULL`; `desfecho = indisponivel`; trabalho
`concluido` (não `pendente`, não `falha`); `precisa_atendimento_humano = true` na
fila do dia daquela reserva; zero resposta ao hóspede.

Reinicie a API e repita o `GET /fila-do-dia` — o sinal permanece.

---

## Cenário 3 — Resposta inválida

Configure o falso para devolver intenção fora da taxonomia (ou eixo faltando), com
`bruto` preenchido.

**Esperado:** eixos `NULL`; `desfecho = formato_invalido`; `bruto` recuperável em
`classificacao_bruta`; sinal humano `true`; trabalho `concluido`; zero envio.

---

## Cenário 4 — Intenção sem ramo próprio

Configure `upsell` (ou `fora_de_escopo` / `solicitacao_de_checkout`) com sentimento
e urgência válidos.

**Esperado:** os três eixos gravados; `desfecho = encaminhado_humano`; sinal
`true`; zero texto enviado; zero chamado.

---

## Cenário 5 — Reclamação técnica não abre chamado aqui

Configure `reclamacao_tecnica` / `negativo` / `alta`.

**Esperado:** eixos gravados; `desfecho = classificado`; sinal humano `false`;
`SELECT count(*) FROM solicitacao` inalterado.

Repita o espírito para `pedido_de_servico`.

---

## Cenário 6 — Segunda passagem inócua

Com o trabalho já `concluido` do cenário 1, rode `--uma-passagem` de novo.

**Esperado:** eixos e `desfecho` inalterados; o falso **não** precisa ser chamado de
novo para essa mensagem (ou, se um trabalho residual não existir, zero claim desse
id). Sem segundo sinal, sem segunda linha de classificação.

---

## Cenário 7 — F1.3 intacta

Reserva em `aguardando_cadastro` + webhook de ficha + worker.

**Esperado:** continua `interpretar_ficha`; `estado_cadastro` como antes; **não**
preenche `intencao` de estadia nem liga `precisa_atendimento_humano`.

---

## Cenário 8 — Isolamento e autorização

1. Mensagem classificada no hotel A: fila do hotel B (outra sessão) não mostra essa
   reserva nem o sinal.
2. `GET /fila-do-dia` com sessão operacional ou de gestão: recusa (matriz
   inalterada).

---

## Cenário 9 — Log sem conteúdo

Dispare sucesso, indisponível e inválido.

**Esperado no log:** `id_mensagem`, `id_trabalho`, `id_reserva`, `id_hotel`,
`desfecho`, `intencao` quando houver. **Ausente:** texto da mensagem, telefone,
JSON `bruto` do classificador.
