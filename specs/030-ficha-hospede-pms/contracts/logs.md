# Contrato: logs — ficha do hóspede

Artigo VIII. A tela não cria logger de frontend obrigatório.

---

## Nunca registrar

- Nome do hóspede
- Telefone (nem canônico, nem mascarado, nem tamanho)
- Número ou tipo de documento
- Endereço, CEP, cidade, profissão, data de nascimento
- Idade derivada
- Senha, cookie, cabeçalho `Cookie`
- Conteúdo de mensagem
- Corpo de `PUT /reservas/{id}/ficha` no `console`
- Texto montado para copiar

## Pode registrar (servidor)

- `id_reserva`, `id_hospede`, `id_usuario`, `id_hotel`
- `perfil`
- `ficha_completa` / `status` novo (códigos, não valores de campo)
- Quantidade de campos gravados (inteiro), não quais
- Código de recusa (`422` / `409` / `404` sem repetir o documento)

O GET da ficha **já** não loga campos. O `PUT` deve seguir o padrão
de `ficha_consolidada` (identificadores + status + contagem).
Consentimento no painel **já** loga `id_hospede` + origem +
`concedido` (booleano), sem texto livre — não afrouxar.

## Frontend

Nenhum `console.log` da ficha, do texto de cópia, do consentimento
ou do corpo do `PUT`. Telemetria de produto fica fora.
