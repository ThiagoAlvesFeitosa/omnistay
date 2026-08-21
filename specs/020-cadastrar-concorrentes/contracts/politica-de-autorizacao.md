# Contrato: política de autorização — F5.1

Estende a matriz vigente. Acrescenta **duas** operações novas e as liga às
rotas de concorrentes.

A política continua decisão pura: perfil × operação, sem HTTP e sem banco.
Isolamento por hotel é ortogonal (`id_hotel` da sessão; alvo alheio → `404`).

---

## Operações desta fatia

| Operação | `recepcao` | `staff` | `gestor` | Rotas |
| --- | :---: | :---: | :---: | --- |
| `alterar_concorrentes` | ❌ | ❌ | ✅ | `POST /concorrentes`, `PATCH /concorrentes/{id}` |
| `ler_concorrentes` | ❌ | ❌ | ✅ | `GET /concorrentes`, `GET /concorrentes/ativos` |

Nenhuma das duas existia na matriz da F0.3. Não reutilizar
`alterar_catalogo` / `ler_catalogo` (recepção escreve fatos da casa;
concorrente é mercado). Não reutilizar `ler_indicadores` (a recepção lê
contagem; aqui ela é recusada). Não reutilizar `administrar_usuario`.

---

## Regras

- Só a gestão da **própria** propriedade cria, edita, desativa, reativa e
  consulta concorrentes.
- Recepção: `403` em leitura e escrita. Lista de fontes não é fila do dia.
- Perfil operacional: `403` em leitura e escrita. Concorrente não é chamado
  atribuído.
- Gestão escreve só no hotel da sessão. Id de outro hotel → `404`.
- Worker da F5.2 não autentica perfil para ler fontes ativas; opera com
  `id_hotel` da propriedade. Fora desta fatia.

---

## Recusa visível

| Situação | Resposta |
| --- | --- |
| Sem sessão válida | `401` |
| Sessão válida, perfil sem permissão | `403` |
| Sessão válida, concorrente de outro hotel ou id inexistente | `404` |

---

## Relação com “gestão somente leitura”

A FR-019 da F0.3 recusa a gestão em reserva, hóspede, solicitação, consumo e
avaliação. Concorrente não está nessa lista. O “somente leitura” dos painéis
de mercado (Artefato 5 §11.2) aplica-se a **preço e avaliação coletados**
(F5.3): esta fatia não permite inventar número, só cadastrar quem acompanhar.

---

## Fora desta fatia

- Tela React de manutenção
- Recepção lendo a lista “por curiosidade”
- Gestão alterando linha de `coleta_mercado` (F5.3 recusa)
- `ler_mercado` genérico — nasce na F5.3 se o painel precisar de operação
  distinta da lista de fichas
