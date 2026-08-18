# Quickstart — validar a entrega de Abrir Chamado de Reclamação

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
classificar como `reclamacao_tecnica` (o padrão continua `duvida_geral`).

Confira a semente:

```powershell
docker compose exec db psql -U postgres -d omnistay -c "SELECT chave, valor FROM parametro_hotel WHERE chave = 'horas_destaque_chamado_aberto';"
```

Esperado: `2`.

---

## Cenário 0 — Esquema

```powershell
alembic current
```

`trabalho.tipo` admite `abrir_chamado_reclamacao`. Índice
`uq_trabalho_abrir_chamado_reclamacao_mensagem`. `vw_fila_do_dia` **igual** à
`0012` (reclamação não entra no flag humano).

---

## Cenário 1 — Reclamação com quarto, sem horário

Configure classificação `reclamacao_tecnica`. Webhook:
`o ar do quarto 402 nao esta gelando`. Uma passagem do worker (classifica **e**
abre o chamado, dois claims se o limite permitir):

```powershell
python -m worker --uma-passagem
```

**Esperado:**

- `classificar_mensagem` e `abrir_chamado_reclamacao` `concluido`
- recebida: `intencao = reclamacao_tecnica`, `desfecho = classificado`,
  `resposta = confirmacao_reclamacao`, `id_mensagem_resposta` e `id_solicitacao`
  preenchidos, `conteudo` intocado
- uma `mensagem` `enviada` com recado de manutenção acionada **e** pergunta de
  horário (sem prazo de conserto, sem catálogo)
- uma `solicitacao` `tipo = reclamacao`, `descricao` igual ao texto do hóspede,
  `numero_quarto = 402`, `janela_preferencia` nula, `status = aberta`, sem
  `consumo`
- `GET /fila-do-dia`: `precisa_atendimento_humano = false`
- `reserva.status` continua `hospedado`

Login staff:

```text
GET /solicitacoes
```

**Esperado:** item com quarto 402, tipo `reclamacao`, janela nula,
`destaque_tempo_excedido = false`; **sem** nome e **sem** telefone. Recepção e
gestão da mesma propriedade também 200, mesmo formato. Staff em
`GET /reservas/{id}/ficha` continua 403.

---

## Cenário 2 — Horário já na origem

Nova reserva hospedada. Webhook:
`o chuveiro vazou, pode ser depois das 16h`. Passagem.

**Esperado:** chamado com `janela_preferencia` contendo `depois das 16h`; recado
**sem** pergunta de horário; item visível no `GET /solicitacoes` com a janela.

---

## Cenário 3 — Horário informado depois

Sobre o chamado do cenário 1 (ainda sem janela). Webhook: `depois das 14h`.
Passagem (só `classificar_mensagem`).

**Esperado:**

- `desfecho = janela_registrada` nessa recebida; eixos estruturados vazios
- a **mesma** `solicitacao` agora tem a janela; zero segunda linha
- zero segunda enviada de “manutenção acionada”
- LLM **não** foi necessário para esse texto (o falso não registra chamada, se
  o roteiro usar um falso instrumentado)
- `GET /solicitacoes` mostra a janela no item original

---

## Cenário 4 — Sem quarto

Nova reserva. Webhook: `o ar nao esta gelando`. Passagem.

**Esperado:** confirmação com pergunta de horário; `numero_quarto` nulo;
pendência visível; zero quarto inventado.

---

## Cenário 5 — Tempo excessivo

Com um chamado de reclamação aberto, avance o relógio na suíte (não no
roteiro HTTP: o teste unitário/integração injeta `agora`). Ou, no banco de
teste, ajuste `aberta_em` para mais de 2 horas no passado e chame
`GET /solicitacoes`.

**Esperado:** `destaque_tempo_excedido = true` só no item `reclamacao`. Um
pedido `servico` igualmente antigo permanece `false`.

Sem a chave no `parametro_hotel` daquele hotel: todos `false`; log
`prazo_ausente` sem texto da conversa.

---

## Cenário 6 — Isolamento e o que não acontece

Hotel B autenticado: 200 sem o chamado de A. Reprocessar o mesmo webhook: uma
confirmação, um chamado. Dúvida geral e pedido de toalha **não** criam
`reclamacao`. Sentimento neutro na classificação **ainda** abre chamado.

---

## Fora deste roteiro

Resolver o chamado, consumo faturável, pulso, tela React, WhatsApp real, provedor
de IA real.
