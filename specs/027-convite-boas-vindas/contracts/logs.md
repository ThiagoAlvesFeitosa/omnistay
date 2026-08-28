# Contrato: log desta fatia

Montagem: [montagem-e-porta.md](./montagem-e-porta.md). API:
[api-de-boas-vindas.md](./api-de-boas-vindas.md).

---

## O que o log operacional MAY registrar

- `id_hotel`, `id_reserva`, `id_mensagem`, `id_trabalho`
- Resultado já existente (`agendada`, `bloqueadas`, `ja_agendada`,
  `enviadas`, `recuperadas`)
- `chave=` da slot inválida (`boas_vindas_convite` inclusive)
- Código de recusa de formato **sem** o texto recusado

## O que o log NUNCA registra

- Valor do convite (nem prefixo, nem recorte)
- Valor de café, wi-fi ou checkout (regressão F2.2)
- Corpo do recado montado
- Conteúdo de mensagem de hóspede

Eventos a reusar, sem campo novo de texto:

- `textos_de_boas_vindas_gravados id_hotel=…`
- `boas_vindas_bloqueadas motivo=slot_invalido chave=boas_vindas_convite …`
- `boas_vindas_agendadas …`
- `boas_vindas_enviadas …`

---

## Testes

1. Gravação aceita e recusa de convite com quebra de linha: `caplog` sem
   o texto tentado
2. Agendamento bloqueado por convite ausente: log traz a **chave**, não
   o valor
3. Agendamento e envio com convite preenchido: log sem a linha da casa e
   sem o corpo
