# Contrato: `PUT /reservas/{id_reserva}/ficha` (acréscimo)

Rota e operação `alterar_ficha_de_hospede` **já existem** (spec
030). Esta fatia só acrescenta a conferência de CPF.

Autorização, hotel, ciclo de vida, `409` de documento em uso:
inalterados. Ver `specs/030-ficha-hospede-pms/contracts/api-alterar-ficha.md`.

## Corpo

Igual ao 030. `tipo_documento: "cpf"` aceita número com ou sem
pontuação. Persistido: onze dígitos.

## `200`

`numero_documento` canônico (onze dígitos). A tela formata.

Zero item na fila. Zero mensagem ao hóspede.

## `422` — CPF não confere

O salvamento **inteiro** é recusado. Nenhum campo daquele clique
é persistido. O que já estava no banco permanece.

`detail`: texto que deixa claro que o **CPF não confere**. **Não**
repete o número. Sem lista de outros campos.

A tela amarra esse recado ao campo número do documento e **não**
descarta o rascunho.

Demais `422` (nascimento, CEP, telefone, tipo, nome vazio)
continuam como no 030.

## `401` / `403` / `404` / `409`

Iguais ao 030.
