# Contrato — autorização (delta F4.2)

## Clique de saída

Nenhuma operação nova no POST. Continua `confirmar_fase_da_reserva`
(`recepcao`). O campo `lista` na resposta não muda quem pode clicar.

| Quem | `POST /reservas/{id}/saida` |
| --- | --- |
| Recepção do hotel da reserva | `200` ou `409` |
| Gestão / staff | `403` |
| Outro hotel | `404` uniforme |

## Consulta da lista — uma operação nova

| Operação | Perfis | Rota |
| --- | --- | --- |
| `ler_pedidos_feitos_pelo_chat` | `recepcao`, `gestor` | `GET /reservas/{id}/pedidos-feitos-pelo-chat` |

Staff: `403`. Não reusar `ler_solicitacao_atribuida` (staff veria a
lista de checkout). Não reusar `lancar_consumo` (gestão ficaria de fora).
Não reusar `ler_dado_cadastral_de_hospede` (gestão ficaria de fora).

Outro hotel: `404` uniforme, sem revelar que a reserva existe.

Gestão consulta; **não** confirma saída (já recusado na F4.1).
