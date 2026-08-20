# Pesquisa — F3.8 Pulso do Segundo Dia

Decisões técnicas tomadas antes de escrever teste. Cada uma traz o que foi
escolhido, por quê, e o que foi recusado.

---

## 1. Varredura no agendador já existente; sem APScheduler

**Decisão:** `verificar_pulsos_pendentes` em `worker/agendador.py`, relógio
injetável (`agora`), flag `--verificar-pulsos`. No modo contínuo, a passagem
horária que já chama cadastros e boas-vindas passa a chamar o pulso também.
`--uma-passagem` **não** dispara a varredura (igual às duas anteriores).

**Rationale:** F1.4 e F2.2 já recusaram APScheduler (Artigo XI). O Artefato 5
nomeia a lib para “quando houver várias tarefas de calendário”; o comportamento
exigido é “no segundo dia, uma vez”, não um relógio novo. A cadência horária já
roda.

**Alternativas recusadas:** APScheduler só para o pulso — terceira peça móvel
sem problema que as flags não resolvam; varredura dentro de `--uma-passagem` —
mistura fila com calendário e quebra o contrato das fatias anteriores.

---

## 2. Tipo `enviar_pulso` com unicidade por reserva

**Decisão:** trabalho `enviar_pulso`, índice único parcial por
`(payload->>'id_reserva')` — o mesmo desenho de `enviar_boas_vindas`. A
varredura grava mensagem pendente + trabalho na mesma transação **antes** do
envio. “Pulso gravado” = existe essa linha, mesmo que o envio ainda falhe.

O processador **reavalia a elegibilidade** a cada tentativa. Se a janela já
fechou (reclamação aberta, horas restantes abaixo do mínimo, reserva
encerrada), conclui **sem enviar**. Perda tolerável; o índice impede um segundo
pulso distinto.

**Rationale:** Artigo III + IX. Conferência em código não segura duas
varreduras simultâneas. O catálogo de eventos admite perder o pulso; não admite
duas perguntas.

**Alternativas recusadas:** unicidade só depois do envio bem-sucedido — duas
passagens criam duas perguntas; flag na `reserva` — coluna nova sem necessidade
(o trabalho já é o fato); recriar trabalho se o primeiro nunca saiu — viola o
teto de um recado e a perda tolerável.

---

## 3. Tipo `registrar_resposta_pulso` só quando o pulso é dono do turno

**Decisão:** depois de `classificar_mensagem`, se a reserva tem pulso **enviado**
e ainda sem avaliação:

| Intenção | O que enfileira |
| --- | --- |
| `duvida_geral` / `pedido_de_servico` / `reclamacao_tecnica` | o trabalho já existente (F3.3–F3.5) |
| qualquer outra intenção classificada | `registrar_resposta_pulso` |
| classificação falha / formato inválido / indisponível | **não** enfileira resposta de pulso; encerra a micro-pesquisa e sinaliza humano |

Os três processadores operacionais, **no fim** do caminho que já produziu
recado (ou chamado), chamam `feedback.encerrar_pulso_em_silencio`. Não mandam
“obrigado”. Se o sentimento é `negativo` e esta mensagem **ainda não** abriu
reclamação, `abrir_reclamacao` sem segundo recado.

`registrar_resposta_pulso` é único por `id_mensagem`. Caminho dono do turno:
positivo/neutro → reconhecimento único; negativo → confirmação (o que acontece
em seguida, sem horário) **antes** de `abrir_reclamacao`.

**Rationale:** a spec exige no máximo um recado por mensagem. Os fluxos
operacionais já são trabalhos separados; o gancho no fim evita hop extra e
evita o classificador “engolir” toalha. O tipo novo só existe porque o retry
do recado de pulso é outro (sessão, não catálogo).

**Alternativas recusadas:** interceptar a primeira mensagem e **não** rodar
F3.3–F3.5 — rejeitado no clarify; fechar o pulso ainda em `classificar_mensagem`
com envio síncrono — mistura classificação com mensageria e quebra os testes da
F3.2 que proíbem execução; um trabalho só `fechar_pulso` depois dos três — hop
e corrida (“obrigado” vs confirmação de toalha”).

---

## 4. Módulo `feedback` nasce como dono de `avaliacao`

**Decisão:** `app/modulos/feedback/` (service + repository). Primeira escrita em
`avaliacao`. `conversa` orquestra e chama o serviço; **não** faz SQL nessa
tabela. Sem rota HTTP nesta fatia.

Encerrar o pulso = `INSERT` com `origem = pulso_segundo_dia`. Unicidade
`(id_reserva, origem)` fecha a janela. Caminho humano também insere (nota nula,
comentário preservado) — senão a próxima mensagem continuaria “aguardando
resposta”. Polaridade **não** é coluna de `avaliacao`; vive em
`mensagem.sentimento`.

**Rationale:** a constituição de pastas e o Artefato 5 já nomeiam o módulo.
Metade de `avaliacao` na conversa seria a F4.1 herdando fronteira errada.

**Alternativas recusadas:** gravar `avaliacao` em `conversa` — viola “módulo só
grava tabela que governa”; coluna `pulso_respondido` em `reserva` — dado de
feedback fora do depósito D6; não inserir no caminho humano — a interceptação
nunca fecha (FR-015).

---

## 5. Pulso de ida é recado iniciado pelo hotel; respostas são sessão

**Decisão:** a pergunta usa método novo na porta, `enviar_pulso` (template de
utilidade, no espírito de `enviar_boas_vindas`). Reconhecimento e confirmação
negativa usam `enviar_texto_sessao` — o hóspede acabou de escrever.

Variáveis da pergunta: prenome + texto curto da micro-pesquisa. Mesmas
restrições descobertas na F2.2: sem quebra de linha, tabulação, mais de quatro
espaços seguidos nem vazio.

**Rationale:** as quatro mensagens proativas do MVP são Utility. Recado de
resposta na janela de 24h é sessão, como F3.3–F3.6.

**Alternativas recusadas:** pergunta por `enviar_texto_sessao` — a janela pode
estar fechada no segundo dia (hóspede silencioso desde as boas-vindas);
reconhecimento por template — recado extra pago e desnecessário dentro da
sessão recém-aberta.

---

## 6. Dia civil e horas restantes no relógio UTC do agendador

**Decisão:** “segundo dia” = a data UTC de `agora` é **estritamente posterior**
à data UTC de `checkin_em`. Horas restantes =
`24 * (data_checkout_prevista - data UTC de hoje)` em dias inteiros. Prazo
`horas_minimas_para_pulso` (inteiro ≥ 1). Ausência ou valor inválido →
`prazo_ausente` no log, zero envios naquele hotel, nenhum 24 embutido.

Eixo do segundo dia: **`checkin_em`**, nunca `data_checkin_prevista`.

**Rationale:** spec + F1.4 (data civil UTC) + correção da F2.2 (instante real).
Não inventar horário de checkout.

**Alternativas recusadas:** 12h como checkout padrão — número mágico; fuso da
propriedade — campo inexistente; “24h após o check-in” no lugar do segundo dia
— uma estadia seg–qua perderia o pulso de terça de manhã.

---

## 7. Reclamação aberta só via `atendimento`; gancho sem segundo recado

**Decisão:** a varredura pergunta a `atendimento` se existe solicitação
`tipo = reclamacao` com `status` em (`aberta`, `em_andamento`) naquela reserva.
Não lê `solicitacao` de `hospedagem` nem do worker.

`abrir_reclamacao` permanece o INSERT. O processador de pulso (dono do turno)
grava a enviada **antes** de chamar. O gancho silencioso chama o INSERT sem
montar recado novo. Sem parâmetro `confirmar=` espalhado: quem manda recado é
sempre `conversa`; `atendimento` não envia (já é a fronteira da F3.5).

Janela de preferência no chamado de recuperação do pulso: **nula**. Sem
pergunta de horário. Sem ramo que detecte defeito de quarto.

**Rationale:** Artigo VI no caminho dono do turno; clarify C; fronteira de
módulo já vigente.

**Alternativas recusadas:** worker com SQL direto em `solicitacao`; copiar
`montar_confirmacao_reclamacao` (pergunta horário); flag `confirmar` em
`abrir_reclamacao` que escondesse envio dentro de atendimento.

---

## 8. Sem coluna nova na fila do dia e sem operação nova na matriz

**Decisão:** não há sinal “pulso enviado” na `vw_fila_do_dia`. Irreconhecível
reusa `precisa_atendimento_humano`. O chamado de recuperação aparece em
`GET /solicitacoes`. Nenhuma operação nova: o sistema dispara; a recepção já
lê chamado.

**Rationale:** a spec não pede painel de pulso. Artigo XI.

**Alternativas recusadas:** coluna `pulso_pendente` — UI sem critério de
aceite; permissão `disparar_pulso` — não há clique.

---

## 9. Inventário de testes que esta fatia mexe

| Teste atual | Destino |
| --- | --- |
| F3.2: classificar não executa dúvida/pedido/reclamação | **Permanece** para quem **não** tem pulso aguardando. Com pulso, o enqueue operacional continua sendo o das fatias 3.3–3.5, não a execução |
| F3.3–F3.5 caminhos felizes | Permanecem; ganham asserção extra só nos casos com pulso aberto: avaliação gravada e zero “obrigado” empilhado |
| CLI `--uma-passagem` não chama cadastros/boas-vindas | Estende: também não chama pulsos |
| Bootstrap conta parâmetros | Ganha `horas_minimas_para_pulso=24` |
| `ck_trabalho_tipo` / unicidades | Ganha os dois tipos novos |

Nenhum teste da F3.4/F3.5 **inverte** o recado operacional. O que nasce é o
gancho de encerrar pulso, inerte quando não há pulso aguardando.
