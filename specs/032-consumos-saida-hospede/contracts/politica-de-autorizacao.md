# Contrato: política de autorização — F8.5

Esta fatia **não acrescenta operação** à matriz. Recusa de fato
permanece nas rotas já protegidas. A casca já omite `consumos` e
`saida` de staff/gestão e redireciona endereço alheio à casa.

Isolamento por hotel: `id_hotel` da sessão. Alvo alheio → `404`
(não `403`) nas rotas de reserva e solicitação, como F3.7/F4.1.

---

## Operações que estas telas disparam

| Operação existente | `recepcao` | `staff` | `gestor` | Onde |
| --- | :---: | :---: | :---: | --- |
| `ler_solicitacao_atribuida` | ✅ pendentes | ❌ nesta fatia | ❌ nesta fatia (matriz permite; casca não monta) | `GET /consumos/pendentes` |
| `lancar_consumo` | ✅ dois botões | ❌ | ❌ | `POST .../lancamento` e `.../dispensa` |
| `ler_pedidos_feitos_pelo_chat` | ✅ lista da saída | ❌ | ❌ nesta fatia (matriz permite; casca não monta) | `GET .../pedidos-feitos-pelo-chat` |
| `confirmar_fase_da_reserva` | ✅ só em TelaSaida | ❌ | ❌ | `POST .../saida` |
| `ler_dado_cadastral_de_hospede` | ✅ saída com id e Ver ficha | ❌ | ❌ | `GET .../ficha` |
| `ler_fila_do_dia` | ✅ fila + datas na saída | ❌ | ❌ | `GET /fila-do-dia` |

Sessão (`GET/DELETE /sessoes/atual`) continua a da F8.1.

---

## Regras da superfície

- Sem sessão: `/app/consumos` e `/app/saida` não mostram lista —
  tela de entrada.
- Staff e gestão nesses endereços (com ou sem id): a casca não
  renderiza o conteúdo e **não** dispara os GET/POST desta fatia.
- Nome e telefone: só na identidade da saída (ficha) e na fila do
  dia. Zero desses campos em Consumos a lançar.
- Botões de lançar, dispensar e confirmar saída ausentes para
  staff e gestão — não é só o `403` da API.
- **Ver ficha** só na recepção, a partir da lista financeira ou da
  fila.

---

## Não chamar nesta fatia

| Operação | Por que não |
| --- | --- |
| `resolver_solicitacao` | Quarto é Chamados e pedidos (F8.4) |
| `alterar_ficha_de_hospede` | Completar ficha é F8.3 |
| CRUD de item vendável / catálogo | F8.6 |
| `ler_solicitacao_atribuida` via `GET /solicitacoes` | Lista operacional, não financeira |
