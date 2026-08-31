# Contrato: política de autorização — F8.4

Esta fatia **não acrescenta operação** à matriz. Recusa de fato
permanece nas rotas já protegidas. A casca já omite `alertas` do
staff/gestão e `chamados` da recepção/gestão, e redireciona
endereço alheio à casa.

Isolamento por hotel: `id_hotel` da sessão. Resolução em item
alheio → `404` (não `403`), como a F3.6.

---

## Operações que estas telas disparam

| Operação existente | `recepcao` | `staff` | `gestor` | Rota / destino |
| --- | :---: | :---: | :---: | --- |
| `ler_solicitacao_atribuida` | ✅ lista | ✅ lista | ❌ nesta fatia (casa é indicadores; casca não monta) | `GET /solicitacoes` |
| `resolver_solicitacao` | ✅ botão | ✅ botão | ❌ | `POST /solicitacoes/{id}/resolucao` |
| `ler_dado_cadastral_de_hospede` | ✅ só após **Ver ficha** | ❌ | ❌ | `GET /reservas/{id}/ficha` (TelaFicha) |

A casca continua com sessão (`GET/DELETE /sessoes/atual`) como na F8.1.

Gestão **pode** a operação `ler_solicitacao_atribuida` na matriz, mas
**não** vê Chamados e pedidos nem Meus chamados. Indicadores são F8.7.
Esta fatia não dispara o GET na sessão de gestão.

---

## Não chamar nesta fatia

| Operação | Por que não |
| --- | --- |
| `lancar_consumo` / dispensa | F8.5 |
| `ler_fila_do_dia` | A lista operacional não é a fila nominada |
| `alterar_ficha_de_hospede` | Completar ficha é F8.3; daqui só se navega |
| `confirmar_fase_da_reserva` | Chegada/saída não são esta tela |

---

## Regras da superfície

- Sem sessão: `/app/alertas` e `/app/chamados` não mostram lista —
  tela de entrada (F8.1).
- Staff e gestão no endereço de Chamados e pedidos: a casca não
  renderiza o conteúdo e **não** dispara `GET /solicitacoes`.
- Recepção e gestão no endereço de Meus chamados: o mesmo.
- Staff em `/app/ficha` ou `/app/ficha/:id`: casca redireciona; **não**
  dispara GET de ficha (já F8.3; esta fatia não abre atalho).
- Nome, telefone e documento: só depois que a recepção abre a ficha.
  Zero desses campos nas duas listas.
- Botão Resolvido ausente para gestão — não é só o `403` da API.
