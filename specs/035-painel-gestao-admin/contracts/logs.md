# Contrato: logs — painel da gestão

Artigo VIII. A tela não cria logger de frontend obrigatório.

---

## Nunca registrar

- Senha, `senha_hash`, cookie, cabeçalho `Cookie`
- Identificador de sessão apresentado ao cliente
- Conteúdo de mensagem de hóspede, comentário, documento, telefone,
  nome de hóspede
- Texto de página de fonte, URL de concorrente, preço/nota como
  texto livre em log
- Corpo do POST de usuário (a senha iria junto) no `console`

## Pode registrar (servidor)

- `id_hotel`, `id_usuario` (funcionário), `id_concorrente`, perfil
- Ação (`indicadores`, `painel`, `historico`, `listar`, `criar`,
  `desativar`, `comprovante`)
- Quantidades do comprovante de retenção (não identificam titular)
- Código de recusa (`409`, `422`, `403`, `404` uniforme)

As APIs de mercado e retenção **já** não logam preço nem texto
tratado. Esta fatia não afrouxa isso. `GET /usuarios` não loga
e-mail em texto se o padrão do módulo já evita dado pessoal de
funcionário além do id — preferir `id_usuario`.

## Frontend

Nenhum `console.log` de indicadores, concorrentes, lista de
usuários, senha digitada ou execuções de retenção. Telemetria de
produto fica fora.
