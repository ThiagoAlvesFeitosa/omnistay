# Contrato — mensageria do pulso

Fila: [fila-e-worker.md](./fila-e-worker.md).

---

## Porta — método novo `enviar_pulso`

Pergunta **iniciada pelo hotel** (template de utilidade). Não reutiliza
`enviar_boas_vindas` nem `enviar_coleta` (textos e variáveis diferentes).

```text
enviar_pulso(
  telefone_destino,
  primeiro_nome,
  corpo,
  id_mensagem,
  id_reserva,
) -> ResultadoEnvio
```

`corpo` já gravado em `mensagem.conteudo` antes da chamada. `FalhaDeEnvio(codigo)`
sem eco do texto.

`MensageriaFalsa` registra `tipo=pulso` + variáveis/corpo, para a suíte
inspecionar sem rede.

---

## Porta — `enviar_texto_sessao` (já existe)

Reconhecimento e confirmação negativa. Mesmo contrato da F3.3/F3.6.

---

## Textos (funções puras)

### Pergunta — `montar_pergunta_pulso(*, nome_completo: str) -> str`

Uma pergunta sobre a experiência; convite a resposta curta. Único dado pessoal:
primeiro nome. Proibições: oferta comercial, consentimento, “extrato”, “conta”,
nota 1–5 obrigatória, quebra de linha / tabulação / >4 espaços seguidos / vazio.

### Reconhecimento — `montar_reconhecimento_pulso() -> str`

**O mesmo** para positivo e neutro. Agradece a resposta e deixa o canal aberto.
**Não** afirma satisfação (“que bom que está gostando” é recusado pelo teste).
Só sai no dono do turno.

### Confirmação negativa — `montar_confirmacao_pulso_negativo() -> str`

Diz o que acontece: recepção avisada, alguém vai falar com o hóspede. **Não**
pergunta horário de visita. **Não** promete prazo de conserto. **Não** usa
“extrato”/“conta”. Só sai no dono do turno.
