# Contrato: logs

Artigo VIII. Conteúdo de mensagem, senha e token **nunca** no log.

## Nunca registrar

- Senha, cookie, `Cookie`
- Corpo de mensagem (simulador, Estadia, webhook)
- `nome_hotel` e nome da pessoa como se fossem evento novo obrigatório
  (a API de sessão já loga ids / recusas como hoje)

## Pode registrar

- `id_usuario`, `id_sessao`, `id_hotel`, `perfil`
- Recusa de credencial / sessão (códigos já existentes)

## Frontend

Nenhum `console.log` de senha, cookie, corpo de POST de sessão ou
texto de mensagem. Telemetria de produto continua fora.
