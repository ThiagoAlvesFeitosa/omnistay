# Contrato: tela de simulação

Superfície visível da F6.2. Contrato HTTP:
[api-do-simulador.md](./api-do-simulador.md).

A suíte pytest **não** renderiza esta tela. O quickstart é quem prova
o navegador.

---

## O que a tela é

Uma página, autenticada com o mesmo cookie do painel. Em modo
`demonstracao`, o apresentador:

1. Vê a lista de reservas da casa e escolhe uma
2. Vê o fio em ordem cronológica, hotel e hóspede distinguíveis
3. Digita o turno do hóspede e envia
4. **Consulta de novo** o fio até aparecer o recado do hotel (worker)

Não é o WhatsApp. Não precisa copiar bolha verde. Precisa ser óbvio
quem falou.

---

## O que a tela não é

- Fila do dia, Alert Center, catálogo, mercado, retenção
- Cadastro de reserva, clique de chegada/saída, resolução de chamado
  (continuam as operações autenticadas já entregues; a banca as usa
  noutro cliente HTTP ou no mesmo origin, fora desta página)
- Seletor de modo (o modo é configuração do ambiente)
- Chat anônimo

---

## Comportamento visível

| Estado | O que a pessoa vê |
| --- | --- |
| Sem sessão | Não opera; o login é o já existente (`POST /sessoes`) |
| Modo `real` | A tela **não** envia turno e **não** substitui o provedor. Recusa visível (`modo_real`) |
| Lista vazia | Estado vazio, não erro |
| Envio sem conversa escolhida | Não dispara POST |
| Texto vazio | Não dispara POST |
| `status_envio = pendente` | Turno do hotel visível como ainda não entregue |
| `status_envio = falha` | Turno visível como falha; reserva intacta |
| Depois do worker | Recado do hotel no fio, direção hotel → hóspede |

Retry de envio reusa o mesmo `id_externo` gerado no cliente.

---

## Origem no navegador

Mesmo origin que a API (proxy Vite em desenvolvimento; SPA em `/app`
quando o uvicorn serve `frontend/dist`). Atalho `GET /demo` redireciona
para `/app/simulador`. Sem isso o cookie `SameSite=Strict` não viaja.
Sem `file://`. Sem segundo formulário de login na tela — a casca
(F8.1) autentica.

---

## Atualização do fio

GET periódico (cerca de 1 s enquanto a página está aberta). Sem
WebSocket. Sem fila de push.

---

## Logs no browser

Nenhum requisito de telemetria. A API já não loga conteúdo.
