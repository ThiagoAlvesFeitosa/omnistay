# Contrato: logs — catálogo, vendáveis e recado

Artigo VIII. A tela não cria logger de frontend obrigatório.

---

## Nunca registrar

- Senha, cookie, cabeçalho `Cookie`
- Conteúdo de mensagem de hóspede
- Título e conteúdo do fato de catálogo como texto livre em log
- Nome do item vendável e `preco_atual` como texto livre em log
- Valores de `cafe`, `wifi`, `checkout`, `convite` (nem prefixo)
- Corpo do POST/PATCH/PUT no `console`

## Pode registrar (servidor, como hoje)

- `id_catalogo_item`, `id_item_vendavel`, `id_usuario`, `id_hotel`
- `categoria` (chave), `perfil`, ação (criar, editar, desativar,
  reativar)
- Código de recusa (`422` com motivo de formato **sem** o valor,
  `409`, `404` uniforme)

As APIs de propriedade **já** não logam o texto do fato nem o
valor do recado. Esta fatia não afrouxa isso.

## Frontend

Nenhum `console.log` de `itens`, de preço, de recado ou de corpo
recusado. Telemetria de produto fica fora.
