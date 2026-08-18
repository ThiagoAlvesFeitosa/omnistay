# Quickstart — validar a entrega de Registrar Pedido de Serviço

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

Hotel + usuários dos três perfis. Reserva **hospedada**. Mensagem de estadia:
`POST /webhook` assinado com o telefone da reserva (F3.1). Configure o falso para
classificar como `pedido_de_servico` (o padrão continua `duvida_geral`).

---

## Cenário 0 — Esquema

```powershell
alembic current
```

`trabalho.tipo` admite `registrar_pedido_servico`. Índices
`uq_trabalho_registrar_pedido_servico_mensagem` e
`uq_solicitacao_mensagem_origem`. `vw_fila_do_dia` **igual** à `0011` (toalha não
entra no flag humano).

---

## Cenário 1 — Pedido com quarto

Configure classificação `pedido_de_servico`. Webhook: `toalha extra no quarto 402`.
Uma passagem do worker (classifica **e** registra, dois claims se o limite
permitir):

```powershell
python -m worker --uma-passagem
```

**Esperado:**

- `classificar_mensagem` e `registrar_pedido_servico` `concluido`
- recebida: `intencao = pedido_de_servico`, `desfecho = classificado`,
  `resposta = confirmacao_pedido`, `id_mensagem_resposta` e `id_solicitacao`
  preenchidos, `conteudo` intocado
- uma `mensagem` `enviada` com recado padrão (sem prazo, sem catálogo)
- uma `solicitacao` `tipo = servico`, `descricao` igual ao texto do hóspede,
  `numero_quarto = 402`, `status = aberta`, sem `consumo`
- `GET /fila-do-dia`: `precisa_atendimento_humano = false`
- `reserva.status` continua `hospedado`

Login staff:

```text
GET /solicitacoes
```

**Esperado:** item com quarto 402 e descrição do pedido; **sem** nome e **sem**
telefone. Recepção e gestão da mesma propriedade também 200, mesmo formato.
Staff em `GET /reservas/{id}/ficha` continua 403.

---

## Cenário 2 — Pedido sem quarto

Nova reserva hospedada. Webhook: `pode mandar um travesseiro extra`. Passagem.

**Esperado:** confirmação enviada; `solicitacao` com `numero_quarto` nulo; item
visível em `GET /solicitacoes`; zero quarto inventado.

---

## Cenário 3 — Isolamento entre hotéis

Pedido no hotel A. Login staff (ou recepção) do hotel B:

```text
GET /solicitacoes
```

**Esperado:** lista sem o item de A. Fila do dia de A inalterada por esse GET.

---

## Cenário 4 — Idempotência

Com o pedido do cenário 1 já registrado, segunda passagem do worker.

**Esperado:** zero segunda `enviada`; zero segunda `solicitacao`; trabalho já
`concluido` não reabre registro.

Segundo `INSERT` `registrar_pedido_servico` para o mesmo `id_mensagem` viola
`uq_trabalho_registrar_pedido_servico_mensagem`. Segundo INSERT em `solicitacao`
com o mesmo `id_mensagem_origem` viola `uq_solicitacao_mensagem_origem`.

---

## Cenário 5 — Dúvida e reclamação não abrem serviço

Padrão do falso (`duvida_geral`) ou classificação `reclamacao_tecnica`. Passagem.

**Esperado:** **não** existe `registrar_pedido_servico` para essa mensagem; zero
nova `solicitacao` tipo `servico` dessa origem. Dúvida segue a F3.3; reclamação
só tem eixos.

---

## Cenário 6 — Classificar ainda não confirma

Inspecione o banco **após** só o claim de `classificar_mensagem` (antes do
`registrar_pedido_servico`), ou rode o unitário correspondente.

**Esperado:** eixos gravados; trabalho `registrar_pedido_servico` `pendente`; zero
enviada de confirmação; zero `solicitacao`.

---

## Log

Dispare os desfechos acima e inspecione o log. Deve haver `pedido_registrado` (e
códigos) com identificadores. **Não** deve aparecer o texto do pedido nem o da
confirmação.

---

## Suíte

```powershell
pytest testes/unitarios -q
pytest testes/integracao -q
```
