# Fase 0 — Pesquisa e decisões técnicas: Simulador de Conversa

Cada seção registra a decisão, por que ela foi tomada e o que foi recusado.
Divergências documentais estão na seção 9.

---

## 1. Modo de canal é configuração de plataforma, não da propriedade

**Decisão**: chave de ambiente `MENSAGERIA_MODO` com exatamente dois
valores: `demonstracao` | `real`. Um por processo. Lida em
`app/config.py` (padrão das demais chaves de plataforma). **Não** entra
em `parametro_hotel`.

Valor inválido ou vazio: o processo **falha alto** na fábrica, sem
supor um dos dois. `.env.example` documenta as duas chaves sem valor.
A suíte define o modo explicitamente no teste.

**Rationale**: o modo escolhe *qual adaptador* fala com o hóspede, não
*como o hotel se comporta*. Artigo XIII cobre prazo e cadência da casa;
o canal é da plataforma (como `WHATSAPP_APP_SECRET`). Colocar na
propriedade faria um hotel em demonstração e outro em real no mesmo
worker — a spec pede um modo por ambiente.

**Alternativas consideradas**:

- **Chave em `parametro_hotel`**: misturaria canal com café/Wi-Fi e
  permitiria dois modos no mesmo processo. Rejeitado.
- **Botão na tela para hot-swap**: a spec pede configuração, não atalho
  por mensagem. Rejeitado.
- **Default silencioso `demonstracao`**: o worker hoje já engole envio
  com `MensageriaFalsa`, então “parecer que funciona” esconderia modo
  real mal configurado. Falhar alto é o padrão do `DATABASE_URL`.
- **Terceiro valor `teste`**: a suíte injeta a porta; não precisa de
  modo. Rejeitado.

---

## 2. Fábrica escolhe o adaptador; o domínio não ramifica

**Decisão**: `construir_mensageria(config)` devolve
`MensageriaSimulada` ou `MensageriaWhatsapp`. Worker e qualquer
consumidor de processo usam a fábrica quando o teste **não** injeta a
porta. `processar_uma_passagem(..., gateway=)` continua a receber a
porta; a suíte segue injetando `MensageriaFalsa`.

`MensageriaSimulada` implementa o mesmo Protocol, **sempre sucede** e
devolve `id_externo` `sim-{id_mensagem}`. Não chama rede. Não tem os
ganchos de falha da falsa (esses são da suíte).

O serviço de conversa **não** importa adaptador concreto (Artigo X).

**Rationale**: a arquitetura §5.1 e o ADR-006 já nomearam o adaptador
de demonstração. O worker hoje instancia `MensageriaFalsa` no
`__main__` — isso é a lacuna que esta fatia fecha, não um terceiro
caminho de regras.

**Alternativas consideradas**:

- **Reusar `MensageriaFalsa` em produção de demo**: a spec separa duplo
  invisível de tela. A falsa tem `falhar_sempre` / `falhas_restantes`,
  que não podem existir no palco. Rejeitado como adaptador de runtime.
- **`if modo == demonstracao` dentro de cada `enviar_*` do serviço**:
  espalha o canal no domínio. Rejeitado (Artigo X).
- **Instanciar WhatsApp na suíte para “provar o modo real”**: gasta
  rede e foge da regra de teste. O modo real se prova recusando a tela
  e escolhendo a classe WhatsApp na fábrica (sem chamar a Graph API).

---

## 3. A tela lê `mensagem`; entrada reusa `receber_evento_entrada`

**Decisão**: **nenhuma tabela nova.** O histórico da tela é `SELECT` em
`mensagem` da reserva, ordem `(enviada_em, id_mensagem)`. Inclui
`pendente` / `enviada` / `falha` — a pendência visível é o Artigo V, não
um estado extra.

O turno do hóspede **não** passa por `POST /webhook` (sem HMAC do
provedor). A rota autenticada monta `EventoEntrada` com o telefone da
reserva escolhida e chama `receber_evento_entrada` — o mesmo serviço do
webhook. Idempotência continua sendo `evento_webhook.id_externo`
UNIQUE. O cliente envia `id_externo`; reapresentação devolve o
desfecho já conhecido, sem segunda linha.

Identidade da conversa: a reserva escolhida na tela **autoriza** o
telefone que entra no resolver. O resolver (ficha × estadia × pesquisa)
permanece o do canal real. Não há atalho `id_reserva` que fure a ordem
de prioridade do webhook.

**Rationale**: gravar antes de enviar já deixou o texto no banco. Uma
tabela `conversa_simulada` seria cópia. Um caminho especial de
classificação seria o produto paralelo que a spec proíbe.

**Alternativas consideradas**:

- **Tabela de buffer da tela**: desvia do histórico real. Rejeitado.
- **POST /webhook sem HMAC em modo demo**: reabre o endereço público.
  A tela é sessão + modo; o webhook continua HMAC falha-fechada (F3.1).
- **Forçar `id_reserva` no INSERT**: duas reservas do mesmo telefone
  se comportariam diferente da Meta. Rejeitado.
- **WebSocket / SSE para “ao vivo”**: peça nova. A tela **consulta de
  novo** o GET (intervalo curto, da ordem de um segundo). Artigo XI.

---

## 4. `POST /webhook` não muda de comportamento com o modo

**Decisão**: o webhook da F3.1 permanece HMAC falha-fechada, nos dois
modos. Em demonstração local **não há túnel**; a Meta não entrega. Se
alguém ligar túnel e demonstração ao mesmo tempo, uma mensagem real
pode entrar — limitação honesta, não silêncio. A suíte de webhook **não
é reescrita**.

O isolamento pedido pela spec é: a **tela** recusa injeção em modo
`real`; o **adaptador** em `demonstracao` não chama o provedor.

**Rationale**: recusar o webhook em `demonstracao` quebraria dezenas de
testes da F3.1 e misturaria canal de palco com prova de autenticidade.
O problema presente é a banca sem Meta, não um hotel que rode os dois
canais de propósito.

**Alternativas consideradas**:

- **Webhook 409 em demonstração**: coerente com “um canal”, caro em
  regressão e inútil sem túnel. Rejeitado nesta fatia.
- **HMAC opcional em demo**: furo da F3.1. Rejeitado.

---

## 5. Uma operação na matriz; rotas no módulo `conversa`

**Decisão**: operação nova `usar_simulador` — `recepcao` e `gestor`.
`staff` recusado. Sem sessão → `401`. Perfil sem permissão → `403`.
Reserva de outro hotel ou id inexistente → `404` (mesma resposta).

Modo `real` em qualquer rota da tela → `409` com código `modo_real`.

Rotas (cookie `omnistay_sessao`, hotel = sessão, sem `id_hotel` no
JSON):

| Método | Caminho | Papel |
| --- | --- | --- |
| `GET` | `/simulador/conversas` | Lista reservas da casa para escolher |
| `GET` | `/simulador/conversas/{id_reserva}` | Fio da conversa |
| `POST` | `/simulador/conversas/{id_reserva}/mensagens` | Turno do hóspede |

Módulo `conversa` governa `mensagem` e `evento_webhook`. Não nasce
módulo `simulador`. Gestão vê na lista o mínimo para escolher (nome
do titular, telefone de contato, status da reserva) — exceção
declarada à recusa genérica de cadastro da F0.3, porque a spec entrega
a tela também à gestão.

**Rationale**: reusar `ler_dado_cadastral_de_hospede` fecharia a gestão
e misturaria ficha completa com palco. Reusar `ler_fila_do_dia` fecha
a gestão e só mostra o turno do dia.

**Alternativas consideradas**:

- **Duas operações** (`ler_simulador` / `enviar_simulador`): a spec é
  uma superfície só. Rejeitado.
- **Staff na tela**: a spec recusa. Alert Center não é o palco.
- **Tela anônima**: injeção sem sessão. Rejeitado.

---

## 6. Tela React mínima; mesmo origin que o cookie

**Decisão**: pasta `frontend/` (já desenhada no Artefato 5, ainda
ausente). Vite + React + TypeScript. **Uma** tela. Sem roteador, sem
kit visual, sem estado global, sem app da equipe.

Cookie F0.3 permanece `HttpOnly` / `Secure` / `SameSite=Strict`. A
página e a API precisam parecer o **mesmo origin** no navegador, senão
o cookie não viaja:

- Desenvolvimento: Vite faz proxy das rotas da API (incluindo
  `/sessoes` e `/simulador`) para o uvicorn.
- Demonstração à banca: `npm run build`; FastAPI serve `frontend/dist`
  em `/demo/` (estáticos). API continua em `/simulador/...` — sem
  colisão.

A suíte pytest **não** abre navegador. O critério automatizado é o
contrato HTTP. A tela no browser é o quickstart.

**Rationale**: a spec exige superfície visível; a stack já escolheu
React. Servir HTML avulso no FastAPI evitaria Node, mas mentiria a
stack e a pasta `frontend/` do Artefato 5. WebSocket para live update
é peça sem problema: um GET periódico basta numa defesa.

**Alternativas consideradas**:

- **Só API, sem pasta `frontend/`**: a spec diz tela. Rejeitado.
- **Painel operacional completo em React**: fora da spec (FR-018).
- **Relaxar `SameSite` ou `Secure`**: reabre F0.3. Rejeitado.
- **Playwright na suíte**: navegador na CI sem problema presente.
  Rejeitado (Artigo XI).

---

## 7. `httpx` vira dependência principal

**Decisão**: `httpx` sai das extras de teste e entra em
`project.dependencies`. O adaptador WhatsApp **já o importa**. Sem isso,
`MENSAGERIA_MODO=real` nem sobe o worker.

Nenhum teste instancia `MensageriaWhatsapp` nem chama a Graph API.

**Rationale**: não é biblioteca nova; é promover o que já está no
adaptador concreto do modo real. Deixar em `dev` faria o modo real
ser mentira.

**Alternativas consideradas**:

- **Importar WhatsApp só se o modo for real, e exigir httpx na hora**:
  falha no primeiro envio, não na subida. Pior. Rejeitado.
- **Reescrever o adaptador com `urllib`**: trabalho sem problema; o
  arquivo já existe. Rejeitado.

---

## 8. Sem migração Alembic

**Decisão**: revisão **não** nasce. `0001` e `0021` intactos.
`docs/04-schema.sql` intacto. Garantias usadas: UNIQUE de
`evento_webhook.id_externo`; `mensagem.direcao` / `status_envio`.

**Rationale**: não há entidade nova. Inventar `origem = simulada` na
mensagem criaria um segundo tipo de conversa.

---

## 9. Divergências documentais

1. **Worker instancia `MensageriaFalsa` no `__main__`.** O Artefato 5
   §6.3 prevê `mensageria_simulada.py` escolhido por configuração. Esta
   fatia fecha o furo: fábrica + adaptador de demonstração. A falsa
   permanece só na suíte. Não há correção de artefato além de anotar
   aqui — o desenho original estava certo; a implementação das fatias
   de envio adiou a escolha.

2. **Pasta `frontend/` inexistente.** O Artefato 5 e o estado do
   projeto falam em React já existente no protótipo. No repositório não
   há. Esta fatia **cria** o mínimo (uma tela), em vez de fingir que o
   protótipo está no git. Fatias anteriores adiaram a UI com honestidade;
   aqui a UI é o critério.

3. **“APScheduler no worker” no estado do projeto.** Já recusado desde
   a F1.4 (Artigo XI). Esta fatia não o reabre. A tela consulta; o
   worker já existente processa a fila.

4. **Cookie `Secure` em HTTP local.** Decisão da F0.3, fora desta
   fatia. Chromium trata `localhost` como contexto seguro. A banca
   usa o mesmo origin (proxy ou `/demo/`). Não se altera o cookie para
   fazer a tela “funcionar no file://”.
