# Contrato: logs — casca do painel

Artigo VIII. A casca não cria logger de frontend obrigatório. O que
vale é o que a API já registra ao autenticar e encerrar sessão.

---

## Nunca registrar

- Senha (nem em claro, nem em hash, nem tamanho)
- Valor do cookie `omnistay_sessao`
- Cabeçalho `Cookie`
- Conteúdo de mensagem de hóspede (a casca desta fatia nem o lê,
  salvo o simulador já existente, que continua sem logar texto)

## Pode registrar (servidor, como hoje)

- `id_usuario`
- `id_sessao` interno (não o token)
- `perfil`
- Resultado da entrada (sucesso / recusa)
- Código de recusa (`credenciais_invalidas`, `sessao_invalida`)
- Path de tela **não** é obrigatório no log

## Frontend

Nenhum `console.log` de senha, de cookie ou de corpo de
`POST /sessoes`. Telemetria de produto fica fora desta fatia.
