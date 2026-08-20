# Contrato — autorização (delta F3.8)

Nenhuma operação nova na matriz. Nenhuma rota HTTP nova.

| Quem | O que já vale |
| --- | --- |
| Sistema (worker) | Dispara e interpreta o pulso |
| Recepção / staff / gestão | Veem o chamado de recuperação em `GET /solicitacoes` (`ler_solicitacao_atribuida`) |
| Staff | Continua sem ficha cadastral |
| Gestão | Continua sem resolver nem lançar |

Não criar `disparar_pulso` nem `ler_avaliacao` nesta fatia. Tela de indicadores
e pesquisa de checkout são fatias seguintes.
