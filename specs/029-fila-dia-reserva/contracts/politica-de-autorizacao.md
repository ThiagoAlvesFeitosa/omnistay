# Contrato: política de autorização — F8.2

Esta fatia **não acrescenta operação** à matriz. Recusa de fato
permanece nas rotas já protegidas. A casca já omite `fila` e `reserva`
do menu de staff e gestão e redireciona endereço alheio à casa.

Isolamento por hotel: `id_hotel` da sessão. Chegada em reserva alheia
→ `404` (não `403`), como a F2.2.

---

## Operações que estas telas disparam

| Operação existente | `recepcao` | `staff` | `gestor` | Rota |
| --- | :---: | :---: | :---: | --- |
| `ler_fila_do_dia` | ✅ | ❌ | ❌ | `GET /fila-do-dia` |
| `alterar_reserva` | ✅ | ❌ | ❌ | `POST /reservas` |
| `confirmar_fase_da_reserva` | ✅ | ❌ | ❌ | `POST /reservas/{id}/chegada` |

A casca continua com sessão (`GET/DELETE /sessoes/atual`) como na F8.1.

---

## Não chamar nesta fatia

| Operação | Por que não |
| --- | --- |
| `confirmar_fase_da_reserva` na saída | Checkout é F8.5 (`POST .../saida`) |
| `ler_dado_cadastral_de_hospede` | Ficha é F8.3 |
| `alterar_texto_de_boas_vindas` | Recado é F8.6 |
| `ler_indicadores` | Não é o resumo da fila; números da gestão são F8.7 |
| `ler_solicitacao_atribuida` | F8.4 |

---

## Regras da superfície

- Sem sessão: `/app/fila` e `/app/reserva` não mostram lista nem
  formulário — tela de entrada (F8.1).
- Staff e gestão no endereço da fila ou do cadastro: a casca não
  renderiza o conteúdo e **não** dispara `GET /fila-do-dia`.
- Nome e telefone só na sessão de recepção, só nestas duas telas
  (e no simulador já existente, inalterado).
- Botão de chegada ausente quando o `status` não admite — não é só
  o `409` que protege o clique à toa.
