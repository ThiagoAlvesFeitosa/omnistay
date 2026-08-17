# Quickstart — validar a entrega de Responder Dúvida a partir do Catálogo

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
provedor de IA de verdade.

Hotel + recepção autenticada. Reserva **hospedada**. Catálogo: use o quickstart da
F2.1 para cadastrar pelo menos um fato (ex.: horário “Cafe da manha” / “7h as 10h”)
quando o cenário pedir cobertura. Propriedade recém-bootstrapada tem catálogo vazio.

Mensagem de estadia: `POST /webhook` assinado com o telefone da reserva (F3.1). O
falso classifica no padrão como `duvida_geral`.

---

## Cenário 0 — Esquema

```powershell
alembic current
```

`trabalho.tipo` admite `responder_duvida`. Índice
`uq_trabalho_responder_duvida_mensagem`. Visão `vw_fila_do_dia`:
`precisa_atendimento_humano` inclui `duvida_nao_coberta`.

---

## Cenário 1 — Pergunta coberta pelo catálogo

Cadastre o horário de café (recepção). Webhook: texto perguntando o café. Uma
passagem do worker (classifica **e** responde, dois claims na mesma passagem se o
limite permitir):

```powershell
python -m worker --uma-passagem
```

**Esperado:**

- `classificar_mensagem` e `responder_duvida` `concluido`
- recebida: `intencao = duvida_geral`, `desfecho = classificado`,
  `resposta = automatica`, `id_mensagem_resposta` preenchido, `conteudo` intocado
- uma `mensagem` `enviada` cujo texto afirma o fato cadastrado (e não um fato de
  outro hotel)
- `GET /fila-do-dia`: `precisa_atendimento_humano = false`
- zero linha em `solicitacao`
- `reserva.status` continua `hospedado`

---

## Cenário 2 — Catálogo vazio (não coberta)

Nova reserva hospedada **sem** itens ativos. Webhook + uma passagem.

**Esperado:** recebida com `desfecho = duvida_nao_coberta` e `resposta = aviso`;
enviada com o recado padrão (recepção vai atender), **sem** horário/cardápio
inventado; `precisa_atendimento_humano = true`; zero `solicitacao`.

Reinicie a API e repita o `GET /fila-do-dia` — o sinal permanece.

---

## Cenário 3 — Fato só no outro hotel

Item ativo no hotel A; pergunta equivalente no hotel B (catálogo de B vazio ou sem
esse fato). Passagem no contexto de B.

**Esperado:** desfecho de não coberta em B; o texto enviado **não** cita o fato de
A; fila do dia de B liga o sinal; fila de A não muda por causa dessa mensagem.

---

## Cenário 4 — Redação não fiel

Configure o falso para `coberta=True` com trecho que **não** está no catálogo ativo
daquela propriedade. Nova mensagem + passagem.

**Esperado:** o texto inventado **não** é enviado; aviso + `duvida_nao_coberta`;
flag verdadeiro.

---

## Cenário 5 — Conversação indisponível

`falhar_conversacao` no falso; catálogo com itens (para não cair no vazio antes da
porta). Nova mensagem + passagem.

**Esperado:** aviso + `duvida_nao_coberta`; trabalho `concluido` (não `falha`, não
`pendente` esperando o LLM); zero afirmação de fato da casa.

---

## Cenário 6 — Idempotência

Com uma dúvida já respondida (cenário 1 ou 2), segunda passagem do worker.

**Esperado:** zero segunda `enviada`; zero segundo aviso; trabalho já `concluido`
não reabre redação.

Segundo `INSERT` `responder_duvida` para o mesmo `id_mensagem` viola
`uq_trabalho_responder_duvida_mensagem`.

---

## Cenário 7 — Outras intenções não disparam resposta

Configure classificação como `pedido_de_servico` ou `reclamacao_tecnica`. Passagem.

**Esperado:** eixos gravados; **não** existe `responder_duvida`; zero enviada nova
desta fatia; flag permanece o da F3.2 (`false` se `classificado`).

---

## Log

Dispare os desfechos acima e inspecione o log da API/worker. Deve haver
`duvida_respondida` ou `duvida_nao_coberta` (e códigos) com identificadores.
**Não** deve aparecer o texto da pergunta, o da resposta, nem o conteúdo do item.

---

## Suíte

```powershell
pytest testes/unitarios -q
pytest testes/integracao -q
```
