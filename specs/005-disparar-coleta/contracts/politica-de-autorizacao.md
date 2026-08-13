# Contrato: política de autorização (F1.2)

Sem operação nova na matriz. Reutiliza a F1.1 / F0.3.

| Operação | `recepcao` | `staff` | `gestor` |
| --- | --- | --- | --- |
| `alterar_reserva` (`POST /reservas`) | sim | não | não |
| `ler_fila_do_dia` (`GET /fila-do-dia`, agora com `status_envio_coleta`) | sim | não | não |
| `ler_indicadores` | sim | não | sim |

O worker **não** é HTTP autenticado: processo interno com credencial de banco. Não amplia
privilégios de `staff`/`gestor` sobre mensagem ou telefone.

Referência histórica: [politica F1.1](../../004-cadastrar-reserva/contracts/politica-de-autorizacao.md).
