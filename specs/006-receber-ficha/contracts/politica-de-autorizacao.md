# Contrato: política de autorização — F1.3

Estende a matriz já vigente (F0.3 / F1.1 / F1.2).

---

## Operações

| Operação | recepcao | operacional | gestao |
| --- | --- | --- | --- |
| `ler_fila_do_dia` | sim (inclui `estado_cadastro`) | não | não* |
| `ler_ficha_de_hospede` | sim | não | não |
| Webhook (`GET`/`POST /webhook`) | — (canal público com assinatura/token; sem sessão de painel) | — | — |

\*Gestão continua com indicadores agregados (`ler_indicadores`); a fila nominada e a ficha
cadastral não trafegam para gestão/operacional.

---

## Regras

- `GET /reservas/{id}/ficha` exige sessão de **recepção** do mesmo `id_hotel` da reserva.
- Operacional tentando ler ficha ou fila nominada: `403`.
- Gestão tentando ler ficha: `403`.
- Conteúdo de mensagem e campos da ficha nunca em log, qualquer perfil.

---

## Fora desta fatia

- Edição manual da ficha pela recepção
- Revogação de sessão (já existe)
- Criação de usuários (já existe)
