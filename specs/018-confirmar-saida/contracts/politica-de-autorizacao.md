# Contrato — autorização (delta F4.1)

## Clique de saída

Nenhuma operação nova. Reusa `confirmar_fase_da_reserva` (`recepcao`), a
mesma da chegada.

| Quem | `POST /reservas/{id}/saida` |
| --- | --- |
| Recepção do hotel da reserva | `200` ou `409` |
| Gestão / staff | `403` |
| Outro hotel | `404` uniforme |

## Consentimento — duas operações novas

| Operação | Perfis | Rotas |
| --- | --- | --- |
| `ler_consentimento` | `recepcao`, `gestor` | `GET /hospedes/{id}/consentimento` |
| `registrar_consentimento` | `recepcao`, `gestor` | `POST /hospedes/{id}/consentimento` |

Staff: `403` nas duas. Não reusar `ler_dado_cadastral_de_hospede` (gestão
ficaria de fora) nem `alterar_ficha_de_hospede` (não é ficha).

Não criar `confirmar_saida`, `enviar_pesquisa` nem `ler_avaliacao` nesta
fatia. Avaliação de checkout não tem rota — o hotel lê o dado pelos testes
e, no produto, pela fatia futura de indicadores se houver.

## Fila

`ler_fila_do_dia` inalterada na matriz. O JSON ganha campos; a operação
não muda. Gestão continua sem a fila nominada.
