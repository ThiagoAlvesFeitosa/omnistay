# Contrato: política de autorização — F8.1

Esta fatia **não acrescenta operação** à matriz. A casca filtra o menu
pelo `perfil` de `GET /sessoes/atual`; a recusa de fato permanece nas
rotas já protegidas.

Isolamento por hotel é ortogonal: `id_hotel` da sessão, alvo alheio →
`404` na API. A casca não pede nem exibe identificador de hotel.

---

## Operações que a casca dispara

| Operação existente | `recepcao` | `staff` | `gestor` | Rota |
| --- | :---: | :---: | :---: | --- |
| *(pública)* autenticar | — | — | — | `POST /sessoes` |
| `ver_sessao_propria` | ✅ | ✅ | ✅ | `GET /sessoes/atual` |
| `encerrar_sessao_propria` | ✅ | ✅ | ✅ | `DELETE /sessoes/atual` |
| `usar_simulador` | ✅ | ❌ | ✅ | `GET/POST /simulador/...` (rota de tela `/app/simulador`) |

Não chamar nesta fatia (existem, mas a casca não oferece):

| Operação | Por que não |
| --- | --- |
| `listar_sessoes` / `revogar_sessao` | Tela de dispositivos fica para fatia posterior |
| `ler_fila_do_dia` | Conteúdo da fila é F8.2 |
| `ler_solicitacao_atribuida` | Lista de chamados é F8.4 |
| `ler_indicadores` | Números do painel são F8.7 |
| `ler_dado_cadastral_de_hospede` | Ficha é F8.3; staff continua sem ela |
| `administrar_usuario` | Usuários são F8.7 |
| `ler_mercado` / `ler_retencao` | Telas nomeadas sem fetch |

---

## Regras da superfície

- Sem sessão: só a tela de entrada. Destino interno não mostra conteúdo.
- Item de menu que o perfil não pode usar **não aparece**.
- Staff não vê simulador; a API continua `403` em `/simulador`.
- Gestão não vê fila do dia nem meus chamados nem revogar dispositivo.
- Recepção não vê meus chamados nem o painel da gestão como casa.
- Dado cadastral de hóspede (nome, telefone, documento) **não** entra
  em nenhum destino desta fatia para `staff`. O simulador, se aberto
  por recepção/gestão, continua com o mínimo da F6.2 (titular/telefone
  da lista) — não é tela nova de ficha.

---

## Recusas visíveis (entrada)

E-mail inexistente, senha errada e usuário desativado: o mesmo texto.
A igualdade de tempo no `POST /sessoes` já é da F0.3; a casca não
acrescenta mensagem distinta por caso.
