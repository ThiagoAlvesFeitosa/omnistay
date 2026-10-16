# Modelo de dados — Cada hóspede pertence a um hotel

Referência: `docs/04-schema.sql`. Sem tabela nova. `0001` congelado.

## Entidades

### Hóspede (`hospede`)

| Campo | Desta fatia |
| --- | --- |
| `id_hotel` | **Novo.** NOT NULL, FK `hotel`. Dono/controlador |
| `tipo_documento` / `numero_documento` | Únicos **junto com** `id_hotel` quando ambos preenchidos. CPF: F9.2 (onze dígitos) |

Índice: `uq_hospede_documento` em
`(id_hotel, tipo_documento, numero_documento)` WHERE os dois
campos de documento NOT NULL.

### Reserva / vínculo

`reserva.id_hotel` já existe. `reserva_hospede` continua filho
(FK obrigatória para reserva **e** hóspede). Depois da migração,
o hotel da reserva e o do hóspede titular coincidem.

### Consentimento

Sem coluna nova. Filho obrigatório de `hospede`; o dono é o do
pai. Não se copia na partição multi-hotel.

### Hotel

Inalterado. É a raiz (`id_hotel` PK).

## Regras

1. Todo hóspede tem exatamente um hotel.
2. Par tipo+número único por hotel, se preenchido.
3. Mesmo par em outro hotel: outro cadastro, sem conflito.
4. Consentimento e expurgo só no hotel do cadastro.
5. Walker Artigo XIV: tabela tem `id_hotel` ou FK NOT NULL para
   quem já tem (filho→pai). Exceções nomeadas:
   `alembic_version`, `evento_webhook`.

## Transições

Nenhuma transição de status de reserva nova. Colisão no PUT:
nada daquele salvamento; status intacto. Coleta: UNIQUE por hotel;
sem estado novo de pendência (F9.5).

## Migração (dados + forma)

1. Adicionar `id_hotel` anulável.
2. Atribuir pelo hotel das reservas; partir cadastro multi-hotel
   (cópia da ficha; vínculo das reservas do outro hotel; consentimento
   fica no original).
3. Sem reserva + um hotel → esse hotel.
4. Sem reserva + dois ou mais → log de ids, abortar.
5. NOT NULL + UNIQUE novo. Dropar UNIQUE antigo.
