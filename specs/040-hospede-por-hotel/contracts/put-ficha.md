# Contrato: `PUT /reservas/{id_reserva}/ficha` (acréscimo)

Rota e operação `alterar_ficha_de_hospede` **já existem** (spec
030). Autorização, hotel, ciclo, `422` de CPF (F9.2): inalterados.

## `200`

Igual ao 030/039. O documento gravado nesta casa não impede o
mesmo par tipo+número em **outro** hotel.

## `409` — documento já de outro hóspede **desta** casa

Nada daquele salvamento. Corpo:

```json
{
  "detail": {
    "codigo": "documento_em_uso",
    "recado": "Documento já cadastrado para Ana.",
    "nome": "Ana",
    "id_reserva": 12
  }
}
```

`id_reserva`: uma estadia titular deste hóspede **neste** hotel
(maior id não cancelada; senão maior id). A tela liga para
`/ficha/{id_reserva}`.

MUST NOT incluir número de documento. MUST NOT nomear hóspede de
outro hotel. `403` de staff/gestão permanece genérico, sem este
objeto.

`401` / `404` / `422`: iguais ao 030/039.
