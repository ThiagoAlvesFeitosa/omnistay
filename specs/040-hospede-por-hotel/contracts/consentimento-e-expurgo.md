# Contrato: consentimento e expurgo (alcance)

Sem rota nova. Operações `ler_consentimento` /
`registrar_consentimento` inalteradas na matriz.

## Consentimento

`GET`/`POST /hospedes/{id_hospede}/consentimento` com sessão do
hotel A e cadastro do hotel B: `404` genérico (já era
`HospedeNaoEncontrado`). A prova passa a ser `hospede.id_hotel`,
não só o JOIN com reserva.

Revogar no A não insere nem altera linha do B.

## Expurgo da ficha

`apagar_fichas_vencidas(id_hotel=A)` só apaga cadastros com
`hospede.id_hotel = A` cujo relógio de retenção venceu. Não
apaga o B. Comprovante `execucao_retencao` continua uma linha
por hotel por dia.

Prazos (5 anos após checkout) não mudam.
