# Quickstart — validar a entrega de Resolver Chamado e Confirmar

Roteiro manual além da suíte. Contratos em [contracts/](./contracts/).

Comandos em PowerShell, na raiz do repositório. Use `curl.exe`.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. API no ar. Worker com `MensageriaFalsa` (padrão de
`python -m worker --uma-passagem`). **Não** aponte a suíte nem este roteiro a
WhatsApp de verdade.

Hotel + usuários dos três perfis. Reserva **hospedada** com uma solicitação
`aberta` tipo `reclamacao` ou `servico` (fluxo F3.4 / F3.5, ou semente de
teste). Confira o esquema:

```powershell
alembic current
```

Esperado: revisão `0014_resolver_chamado`. `trabalho.tipo` admite
`enviar_confirmacao_resolucao`. Índice
`uq_trabalho_enviar_confirmacao_resolucao_solicitacao`. Trigger de transição
em `solicitacao`.

---

## Cenário 1 — Staff resolve reclamação aberta

Login staff. `GET /solicitacoes` anota `id_solicitacao` de uma reclamação
aberta.

```text
POST /solicitacoes/{id}/resolucao
```

**Esperado:** `200` com `status = resolvida`, `id_usuario_responsavel` do
staff, `confirmacao = agendada`. Sem nome e sem telefone no JSON.

`GET /solicitacoes`: aquele id **não** aparece. Outras abertas, se houver,
permanecem.

```powershell
python -m worker --uma-passagem
```

**Esperado:**

- `enviar_confirmacao_resolucao` `concluido`
- uma `mensagem` `enviada` com recado de problema atendido (sem “extrato”,
  sem pergunta de horário, sem catálogo)
- `solicitacao.status` continua `resolvida` (não reabre)
- `reserva.status` intocado

---

## Cenário 2 — Recepção resolve pedido de serviço

Login recepção. POST na solicitação tipo `servico` ainda aberta.

**Esperado:** `200`. Recado do worker fala de pedido atendido (não de
manutenção). Item some da lista.

---

## Cenário 3 — Segundo clique recusa

O mesmo id do cenário 1, de novo:

**Esperado:** `409` `Esta solicitacao ja foi resolvida.` Autor e instante da
primeira resolução inalterados. Zero segunda enviada. `GET /solicitacoes`
continua sem o item.

---

## Cenário 4 — Gestão e hotel B

Login gestão, mesmo id aberto de outra reserva (ou o cenário 1 antes de
resolver):

**Esperado:** `403`. Item permanece na lista.

Login staff do hotel B no id do hotel A:

**Esperado:** `404` `Solicitacao nao encontrada.` Item de A inalterado.

---

## Cenário 5 — Falha de envio não reabre

Com a falsa configurada para falhar o envio, POST `200` e uma passagem:

**Esperado:** `solicitacao` `resolvida`; enviada gravada; trabalho pendente de
retry; `GET /solicitacoes` sem o item. Segunda passagem com envio ok conclui
**sem** segunda mensagem.

---

## Fora deste roteiro

Consumo faturável, atribuir, cancelar, tela React, template Utility, pulso.
