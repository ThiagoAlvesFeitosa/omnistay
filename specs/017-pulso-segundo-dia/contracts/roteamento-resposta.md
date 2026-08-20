# Contrato — roteamento da resposta ao pulso

Fila: [fila-e-worker.md](./fila-e-worker.md). Avaliação:
[avaliacao-e-feedback.md](./avaliacao-e-feedback.md).

Regra fechada no clarify: **no máximo um recado ao hóspede por mensagem de
entrada.**

---

## Pulso aguardando resposta

Verdadeiro só se as três valerem:

1. Existe `trabalho` `enviar_pulso` da reserva
2. A mensagem da pergunta está `enviada`
3. Não existe `avaliacao` com `origem = pulso_segundo_dia` da reserva

Trabalho ainda pendente (pergunta não saiu) **não** intercepta a conversa.

---

## Gancho nos processadores F3.3–F3.5

No **fim** de `responder_duvida`, `registrar_pedido_servico` e
`abrir_chamado_reclamacao`, depois de gravar o recado operacional (ou o aviso
de dúvida não coberta, ou a confirmação de chamado):

```text
feedback.encerrar_pulso_em_silencio(id_reserva, comentario)
se sentimento == negativo
   e esta mensagem ainda não originou reclamação:
       atendimento.abrir_reclamacao(...)   # sem recado novo
```

Se não há pulso aguardando, o gancho é no-op. Testes atuais desses
processadores permanecem; só os cenários **com** pulso aberto asserem
avaliação e a ausência do reconhecimento.

`abrir_chamado_reclamacao` já abriu reclamação: o `se` não dispara segunda.

Pedido/consumo com sentimento negativo: abre reclamação de recuperação **além**
da solicitação operacional, sem segundo recado ao hóspede.

---

## Dono do turno

`registrar_resposta_pulso` (ver fila). Recado de pulso **só** aqui — porque
nada operacional respondeu.

Reconhecimento (positivo = neutro, mesmo texto) e confirmação negativa são
funções puras em `conversa`, arquivos novos, sem reutilizar
`montar_confirmacao_reclamacao` (esse pergunta horário).

---

## Humano

Classificação falha na janela do pulso: `feedback.encerrar_pulso` (nota nula,
comentário preservado) + o mesmo sinal `precisa_atendimento_humano` já usado
na F3.2. Zero recado que afirme ter entendido. Zero chamado automático.
