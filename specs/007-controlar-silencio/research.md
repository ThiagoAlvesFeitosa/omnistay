# Fase 0 — Pesquisa e decisões técnicas: Controlar o Silêncio

Cada seção registra a decisão, por que ela foi tomada e o que foi rejeitado. As divergências
documentais encontradas no caminho estão consolidadas na seção 9.

---

## 1. Agendador é uma função no worker; sem APScheduler nesta fatia

**Decisão**: o evento temporal `cadastro_nao_respondido` vira a função
`verificar_cadastros_pendentes` em `worker/agendador.py`, invocável:

| Modo | Quando roda |
| --- | --- |
| Suíte / operação pontual | Chamada direta, ou `python -m worker --verificar-cadastros` |
| Worker contínuo | Após passagens da fila, quando o intervalo desde a última verificação venceu |
| `python -m worker --uma-passagem` | **Não** dispara a verificação — só consome `trabalho` (não quebra a suíte F1.2/F1.3) |

A cadência do contínuo é a já registrada no Artefato 5 para esta tarefa (~1 hora). Não é
parâmetro de hotel: o que o hotel configura são `horas_ate_reenvio` e
`horas_corte_antes_checkin`. Testes não esperam uma hora — injetam `relogio.agora` (ou o
argumento `agora`) e chamam a função.

**Rationale**: a F1.2 adiou o APScheduler para “F1.4+”. O problema periódico agora existe,
mas o Artigo XI veta biblioteca nova sem problema que a justifique. Uma função pura +
relógio injetável resolve lembrete, marcação e cancelamento por resposta. Quatro tarefas
com calendários distintos (pulso, mercado, expurgo) é que tornariam um framework de
agendamento correspondente ao problema.

**Alternativas consideradas**:

- **APScheduler no worker**, como o Artefato 5 §9 nomeia: resolve, mas acrescenta
  dependência e um modelo de job que a suíte teria de desligar. Adiado com divergência
  registrada (seção 9).
- **Trabalho recorrente `verificar_cadastros` com `proxima_tentativa_em`**: reusa a fila,
  mistura “varrer o mundo” com “enviar uma mensagem” e complica unicidade/`id_hotel`.
- **Verificar em toda `--uma-passagem`**: acoplaria a suíte antiga a efeitos de silêncio.

---

## 2. Worker orquestra; `hospedagem` não lê `mensagem`

**Decisão**:

| Camada | Responsabilidade |
| --- | --- |
| `hospedagem` | Listar reservas `aguardando_cadastro` (sempre com `id_hotel`); gravar `reenvio_realizado`; transicionar para `sem_cadastro_previo` |
| `conversa` | Dizer se há mensagem recebida; instante da coleta **enviada**; montar texto; gravar mensagem de lembrete + enfileirar `enviar_lembrete`; enviar via porta |
| `propriedade` | Ler os dois prazos; bootstrap semeia as chaves |
| `worker/agendador` | Para cada reserva candidata: aplicar as regras da spec **sem** import cruzado novo `conversa` ↔ `hospedagem` além do já existente (`hospedagem` → `conversa` só no agendamento da coleta na criação) |

O agendador chama os dois serviços. Não se cria ciclo: `conversa` continua sem importar
`hospedagem`.

**Rationale**: um módulo só toca as tabelas que governa. Silêncio depende de `reserva` e de
`mensagem`; a orquestração no worker é o mesmo padrão da F1.3.

**Alternativas consideradas**:

- **Tudo em `hospedagem` consultando `mensagem`**: viola fronteira.
- **Tudo em `conversa` mudando `reserva.status`**: viola fronteira (e a trigger de
  transição é de hospedagem).
- **Estender `hospedagem → conversa`** para o agendador viver no serviço de reserva: o
  serviço de reserva passaria a conhecer prazos, corte e fila — mistura criação de reserva
  com varredura temporal.

---

## 3. Dois prazos da propriedade; ausência não assume número mágico

**Decisão**:

| Chave | Default no bootstrap (e backfill da migração) | Papel |
| --- | --- | --- |
| `horas_ate_reenvio` | `24` | Horas desde a coleta **enviada** até o lembrete |
| `horas_corte_antes_checkin` | `12` | Horas antes das 00:00 UTC da `data_checkin_prevista` |

A migração `0007` insere as chaves em todo hotel que ainda não as tenha (instalação já
bootstrapped). Propriedade nova recebe no bootstrap.

Se a chave faltar ou o valor não for inteiro positivo: **não** usar 24/12 em código. Logar
identificador do hotel + código de erro, pular aquele hotel. Teste cobre o “não lembra por
default embutido”.

**Rationale**: Artigo XIII e FR-003. Os números 24 e 12 são da spec (assumptions), não
constantes de regra espalhadas no verificador.

**Alternativas consideradas**:

- **Default no `ler_parametro` se None**: esconde hotel mal instalado.
- **Tela no painel para editar**: lacuna já aceita no estado do projeto; fora desta fatia.

---

## 4. Relógio do primeiro prazo = `enviada_em` no sucesso da coleta

**Decisão**: ao marcar `mensagem.status_envio = 'enviada'`, gravar também
`enviada_em = agora()`. O verificador usa o `enviada_em` da **primeira** mensagem de saída
da reserva com status `enviada` (a coleta — o `LATERAL` da fila do dia já a identifica pela
ordem crescente).

Coleta ainda `pendente` ou `falha`: não há t0; **não** envia lembrete. A janela de corte
ainda pode marcar `sem_cadastro_previo` (recepção se prepara).

**Rationale**: FR-004. Hoje `enviada_em` nasce no INSERT da pendência; um retry longo
adiantaria o lembrete. Corrigir no sucesso do envio alinha o relógio ao fato observável
“o hóspede teve a mensagem”.

**Alternativas consideradas**:

- **Usar `reserva.criado_em`**: conta tempo antes do hóspede receber qualquer coisa.
- **Coluna nova `coleta_enviada_em` em `reserva`**: denormaliza sem necessidade.

---

## 5. Ordem das regras na verificação

**Decisão** (por reserva `aguardando_cadastro`, com `id_hotel`):

```text
1. Se existe mensagem recebida na reserva → não lembra, não marca (F1.3 já tratou)
2. Se agora >= instante_corte OU a data prevista de entrada já passou
     → transicionar para sem_cadastro_previo; não enviar lembrete
3. Se reenvio_realizado → parar
4. Se coleta ainda não está enviada → parar (sem lembrete)
5. Se agora >= enviada_em da coleta + horas_ate_reenvio
     → na mesma TX: inserir mensagem de lembrete + trabalho enviar_lembrete
        + reenvio_realizado = true
```

`instante_corte` = 00:00 **UTC** de `data_checkin_prevista` menos `horas_corte_antes_checkin`.

**Rationale**: a spec prioriza não ser intrusivo na janela de corte (pula o lembrete) e
tornar a omissão visível. Resposta (qualquer entrada) cancela o ciclo. A flag e o trabalho
nascem juntos — retry de envio não cria segundo lembrete.

**Alternativas consideradas**:

- **Lembrar mesmo dentro da janela de corte**: contradiz FR-005.
- **Marcar `reenvio_realizado` só após envio bem-sucedido**: uma verificação concorrente
  enfileiraria o segundo; o índice único ajudaria, mas a flag de domínio ficaria atrasada.

---

## 6. Trabalho `enviar_lembrete` + porta `enviar_lembrete`

**Decisão**: novo `tipo` de `trabalho`, índice único parcial por `id_reserva`, payload só
com IDs (`id_reserva`, `id_mensagem`). Worker reusa backoff/`tentativas_max_envio_mensagem`.

Na porta `MensageriaGateway`, método novo `enviar_lembrete` com a mesma forma de
`enviar_coleta` (telefone, primeiro nome, corpo, ids). `MensageriaFalsa` registra o envio
de forma distinguível (campo `tipo = lembrete`). A suíte não instancia o adaptador WhatsApp.

O corpo **não** repete a lista numerada da coleta: saudação com primeiro nome + opcionalidade
+ preenchimento na recepção. Mais curto, alinhado a “não ser intrusivo”.

**Rationale**: Artigo IX (unicidade no banco) + Artigo III (gravar antes de enviar) +
Artigo X (porta). Segundo método em vez de genérico `enviar(tipo=…)`: o terceiro e o quarto
envio proativo (boas-vindas, pulso) ainda não existem; Artigo XI.

**Alternativas consideradas**:

- **Reusar `enviar_coleta` para o lembrete**: nome mentiroso; o adaptador real pode
  precisar de outro template Utility.
- **Reusar o tipo `enviar_coleta`**: o índice único por reserva já está ocupado pela
  primeira coleta.

---

## 7. Fila do dia: `estado_cadastro = sem_cadastro_previo`

**Decisão**: na `vw_fila_do_dia`, ramo explícito

```sql
WHEN r.status = 'sem_cadastro_previo' THEN 'sem_cadastro_previo'
```

`GET /fila-do-dia` já devolve `status` e `estado_cadastro`; o contrato só amplia o
vocabulário. Sem endpoint novo. Sem React.

A transição `sem_cadastro_previo → hospedado` **já é válida** na trigger; esta fatia não
implementa o clique de check-in (F2.2). Um teste de integração confirma que a marcação não
impede o `UPDATE` de status permitido.

**Rationale**: FR-010 / FR-013. Não inventar quinto status paralelo: o ciclo de vida já
tem `sem_cadastro_previo`.

---

## 8. Relógio injetável; log sem conteúdo

**Decisão**: `verificar_cadastros_pendentes(..., agora=relogio.agora)`. Logs: `id_hotel`,
`id_reserva`, `id_trabalho`, códigos (`lembrete_agendado`, `marcado_sem_cadastro`,
`prazo_ausente`). Nunca corpo, telefone, nome.

**Rationale**: o módulo `acesso` já usa `app.comum.relogio` para não esperar 30 dias.
Artigo VIII.

---

## 9. Divergências documentais encontradas

| Onde | O que está escrito | O que esta fatia faz | Correção |
| --- | --- | --- | --- |
| Artefato 5 §9 | Tarefas periódicas via **APScheduler** | Função em `worker/agendador.py`; lib adiada | Registrar no estado do projeto na implementação: o *comportamento* entra agora; o *framework* quando houver várias tarefas de calendário |
| Artefato 5 §9 | A tarefa lê só `horas_ate_reenvio` | Lê também `horas_corte_antes_checkin` | A spec F1.4 e o Artefato 1 §3.2 já pediam os dois prazos |
| Artefato 3 §6.3 | Status `chegara_sem_cadastro` | Status modelado `sem_cadastro_previo` | Vocabulário do schema (já alinhado na spec) |
| `enviada_em` | Default no INSERT da pendência | Atualizado no sucesso do envio | Documentar no `04-schema.sql` / comentário se o significado operacional mudar |
| Estado do projeto | F1.4 lê prazos que ninguém semeia | Bootstrap + backfill na `0007` | Fecha a lacuna para estas duas chaves; ainda sem tela de edição |
| Artefato 5 estrutura | `worker/agendador.py` previsto, arquivo inexistente | O arquivo nasce nesta fatia | Alinha pasta à arquitetura, sem a lib |

---

## 10. O que fica propositalmente de fora

- Clique de check-in / pacote de boas-vindas (F2.2)
- Tela para editar `parametro_hotel`
- APScheduler / pulso / expurgo / coleta de mercado
- React
- Adaptador WhatsApp real na suíte
- Segundo lembrete, lista numerada no lembrete, confirmação de “recebemos seu silêncio”
