# Contrato: política de autorização — F5.3

Estende a matriz vigente. Acrescenta **uma** operação nova e a liga aos
GETs do painel. Não acrescenta operação de escrita da série.

A política continua decisão pura: perfil × operação, sem HTTP e sem banco.
Isolamento por hotel é ortogonal (`id_hotel` da sessão; alvo alheio → `404`).

---

## Operações desta fatia

| Operação | `recepcao` | `staff` | `gestor` | Rotas |
| --- | :---: | :---: | :---: | --- |
| `ler_mercado` | ❌ | ❌ | ✅ | `GET /mercado`, `GET /mercado/concorrentes/{id}` |

Não reutilizar:

| Operação existente | Por que não |
| --- | --- |
| `ler_concorrentes` | Lista de fichas (F5.1), não número coletado. A F5.1 já reservou `ler_mercado` para esta fatia |
| `ler_indicadores` | A recepção lê contagem; aqui ela é recusada |
| `ler_catalogo` | Recepção lê fatos da casa; mercado é gestão |

`alterar_concorrentes` / `ler_concorrentes` **não mudam**. Cadastro continua
só gestão; esta fatia não o abre à recepção nem o fecha.

Não nasce `alterar_coleta_mercado`. Escrita da série é método HTTP
inexistente (`405`), não recusa de uma operação da matriz.

---

## Regras

- Só a gestão da **própria** propriedade consulta visão atual e histórico.
- Recepção: `403`. Market Intel não é fila do dia.
- Perfil operacional: `403`. Coleta não é chamado atribuído.
- Gestão lê só o hotel da sessão. Id de concorrente de outro hotel → `404`.
- Gestão **não** cria, corrige, apaga nem redata linha de `coleta_mercado`.
- Worker da F5.2 continua sem cookie; esta fatia não o altera.

---

## Recusa visível

| Situação | Resposta |
| --- | --- |
| Sem sessão válida | `401` |
| Sessão válida, perfil sem permissão | `403` |
| Sessão válida, concorrente de outro hotel ou id inexistente | `404` |
| Qualquer escrita na série | `405` |

---

## Relação com “gestão somente leitura”

A FR-019 da F0.3 recusa a gestão em reserva, hóspede, solicitação, consumo
e avaliação. A F5.1 já registrou: essa recusa **não** cobre o cadastro de
concorrente. Esta fatia fecha o outro lado: preço e nota coletados são
somente leitura. Quem acompanha se cadastra na F5.1; o número só o coletor
grava.

---

## Fora desta fatia

- Tela React
- Recepção lendo o painel “por curiosidade”
- Disparo manual de coleta
- Edição de `periodicidade_coleta_mercado` pelo painel
