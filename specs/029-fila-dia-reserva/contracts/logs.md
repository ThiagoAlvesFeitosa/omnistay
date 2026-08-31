# Contrato: logs — fila do dia e cadastro

Artigo VIII. A tela não cria logger de frontend obrigatório.

---

## Nunca registrar

- Nome do hóspede
- Telefone (nem canônico, nem mascarado, nem tamanho)
- Senha, cookie, cabeçalho `Cookie`
- Conteúdo de mensagem
- Corpo de `POST /reservas` no `console`

## Pode registrar (servidor, como hoje)

- `id_reserva`, `id_usuario`, `id_hotel`
- `perfil`
- Código de recusa (`422` de telefone/datas sem repetir o valor,
  `409` de chegada com motivo de estado, `404` uniforme)

A API de hospedagem **já** não loga nome nem telefone. Esta fatia não
afrouxa isso.

## Frontend

Nenhum `console.log` de `itens`, de telefone ou de corpo de cadastro.
Telemetria de produto fica fora.
