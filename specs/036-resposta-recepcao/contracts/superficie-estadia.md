# Contrato: superfície Estadia

Fonte: `TelaEstadia` em `/app/ficha` e `/app/ficha/:idReserva`.
A casca permanece. Path do destino `ficha` não muda.

Recepção no computador.

---

## Menu sem reserva (`/app/ficha`)

Título **Estadia**. Texto de que se abre pela fila do dia ou por
Chamados e pedidos. **Zero** GET de conversa e de ficha.

---

## Estadia de uma reserva (`/app/ficha/:idReserva`)

Título **Estadia**.

**Ao abrir:** `GET /reservas/{id}/conversa`. **Não** chama
`GET .../ficha`.

**Topo — conversa**, nesta ordem:

- mensagens em ordem, cada uma com origem distinguível
  (hóspede × automático × recepção)
- enviada não entregue: distintivo **enviando**, **enviada** ou
  **falhou** (com **nova tentativa marcada** quando a fila ainda
  vai retentar). Nunca apresentar `pendente`/`falha` como se o
  hóspede já tivesse recebido
- campo de texto livre
- **Enviar** (`<button>`), inerte até o POST voltar

Se `janela.aberta` é falso: o campo **permanece visível**, Enviar
não dispara POST (ou o POST seria `409`; a tela não esconde o
campo). Motivo na tela a partir de `janela.motivo` (`nunca_escreveu`
ou `sem_mensagem_recente`).

Lista vazia com janela fechada: histórico vazio + motivo, não
página em branco.

**Abaixo — dados cadastrais**, inicialmente **recolhidos**.
Controle **ver dados cadastrais** dispara `GET .../ficha` (e
consentimento como hoje). Copiar para o sistema de gestão
permanece **neste** bloco, não na conversa. PUT da ficha intacto.

**Falha de leitura** da conversa: distinta de lista vazia;
**Tentar de novo** (repete o GET). Não manda à entrada (isso é
401). Não usa o vazio da ficha incompleta.

**Enviar** com `201`: a mensagem aparece no histórico como
**enviando**. Chamado aberto, se houver, não some desta tela
(esta tela não lista chamados).

Sem as palavras “extrato” nem “conta”. Sem `console` com o texto.
