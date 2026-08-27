# Contrato: log desta fatia

Composição: [tom-na-composicao.md](./tom-na-composicao.md). API:
[api-de-personalidade.md](./api-de-personalidade.md).

---

## O que o log operacional MAY registrar

- `id_hotel`, `id_mensagem`, `id_trabalho`, `id_reserva`
- Resultado já existente (`automatica`, `nao_fiel`, `aviso`,
  `indisponivel`)
- Código de validação na gravação (`texto_longo`, `controle_invalido`)
  **sem** o texto recusado

## O que o log NUNCA registra

- Descrição de tom (nem prefixo, nem “tom=…”)
- Conteúdo da mensagem do hóspede
- Redação enviada ou recusada
- Prompt (já proibido na F7.1)
- Chave de acesso ao serviço de linguagem

## Testes

1. Gravação bem-sucedida e recusa por tamanho: `caplog` sem o parágrafo
   de tom
2. Dúvida com tom preenchido, fiel e `nao_fiel`: `caplog` sem pergunta,
   sem tom, sem redação
3. Gemini com MockTransport: log de falha continua sem prompt (regressão
   F7.1)
