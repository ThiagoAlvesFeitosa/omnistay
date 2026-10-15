# Contrato: superfície da ficha no painel

Sem rota nova. Sem item de menu novo. Perfis: os que já abrem a
ficha (recepção; staff se a 030 já permitir leitura).

## Leitura

Com tipo CPF e onze dígitos gravados, o valor visível é
`000.000.000-00`. RG e passaporte: como hoje.

## Cópia (“Copiar tudo”)

A linha do número, se tipo é CPF e há onze dígitos, usa a mesma
forma pontuada. Demais campos: contrato 030.

## Edição

O rascunho pode mostrar o CPF formatado. A pessoa pode digitar com
ou sem pontuação.

`422` de CPF: aviso **no campo** número do documento. Os outros
campos do formulário conservam o que foi digitado. Cancelar continua
voltando ao último gravado (030).

Não há validador de dígito no cliente — o servidor é a fonte.

## Log no navegador

Nenhum `console.log` do número, do rascunho ou do corpo do PUT
(já no contrato de logs da 030).
