# Contrato: migração e logs

## Revisão `0028`

1. `hospede.id_hotel` (FK `hotel`), preenchido, depois NOT NULL.
2. UNIQUE parcial `(id_hotel, tipo_documento, numero_documento)`.
3. UNIQUE antigo `(tipo_documento, numero_documento)` some.
4. `0001` congelado. `04-schema.sql` alinhado.

Planejamento puro (testável sem banco):

| Situação | Efeito |
| --- | --- |
| Reservas de um hotel | atribui esse hotel |
| Reservas de vários | original no menor `id_hotel`; cópia da ficha nos outros; vínculos das reservas copiadas; consentimento não copia |
| Sem reserva, 1 hotel | atribui esse |
| Sem reserva, ≥2 hotéis | `orfaos`; não atribui; revisão aborta depois do log |

## Logs

```text
hospede_migracao_orfao n=<n> ids=<id_hospede,...>
```

Nível `warning`. Só identificadores e a contagem. **Nunca**
documento, nome ou telefone.

Recusa no PUT: `ficha_alterada_recusada … codigo=409` com
`id_reserva` / `id_hospede` da tentativa — sem nome na linha de
log se isso ecoar dado pessoal além do id; ids bastam. Sem
número de documento.
