# Contrato: logs — chamados e tela da equipe

Artigo VIII. A tela não cria logger de frontend obrigatório.

---

## Nunca registrar

- Nome, telefone, documento, endereço
- Senha, cookie, cabeçalho `Cookie`
- Conteúdo de mensagem
- `descricao` da solicitação
- Corpo (vazio) do POST não precisa ir ao `console`; a descrição
  do item tampouco

## Pode registrar (servidor, como hoje)

- `id_solicitacao`, `id_reserva`, `id_usuario`, `id_hotel`
- `perfil`, `tipo`
- Código de recusa (`409` com motivo de estado, `404` uniforme)

A API de atendimento **já** não loga descrição nem dado cadastral.
Esta fatia não afrouxa isso.

## Frontend

Nenhum `console.log` de `itens`, de `descricao` ou de ficha.
Telemetria de produto fica fora.
