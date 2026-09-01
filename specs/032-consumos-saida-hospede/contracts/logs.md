# Contrato: logs — consumos a lançar e saída

Artigo VIII. A tela não cria logger de frontend obrigatório.

---

## Nunca registrar

- Nome, telefone, documento, endereço
- Senha, cookie, cabeçalho `Cookie`
- Conteúdo de mensagem
- `descricao` da solicitação e `descricao_item` como texto livre
  em log
- Valor praticado como texto livre em log
- Corpo (vazio) do POST no `console`

## Pode registrar (servidor, como hoje)

- `id_solicitacao`, `id_reserva`, `id_usuario`, `id_hotel`
- `perfil`, `status_lancamento` resultante
- Código de recusa (`409` com motivo de estado, `404` uniforme)

As APIs de atendimento e hospedagem **já** não logam descrição nem
dado cadastral. Esta fatia não afrouxa isso.

## Frontend

Nenhum `console.log` de `itens`, de valores, de ficha ou de lista
cobrável. Telemetria de produto fica fora.
