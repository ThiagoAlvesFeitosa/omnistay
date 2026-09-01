# Contrato: destinos e perfis — F8.6

Esta fatia **não acrescenta operação** à matriz. Recusa de fato
permanece nas rotas já protegidas (`alterar_catalogo`,
`ler_catalogo`, `alterar_texto_de_boas_vindas`,
`ler_texto_de_boas_vindas`).

O mapa da casca **muda**: `catalogo`, `vendaveis` e `boas-vindas`
passam a incluir `gestor` em `perfis`. Staff continua de fora.

Isolamento por hotel: `id_hotel` da sessão. Alvo alheio → `404`
nas rotas com id, como F2.1/F3.7.

---

## Operações que estas telas disparam

| Operação existente | `recepcao` | `staff` | `gestor` | Onde |
| --- | :---: | :---: | :---: | --- |
| `ler_catalogo` | ✅ dois GET | ❌ zero fetch | ✅ dois GET | `GET /catalogo`, `GET /itens-vendaveis` |
| `alterar_catalogo` | ✅ POST/PATCH | ❌ | ❌ sem botão | criar, editar, desativar, reativar |
| `ler_texto_de_boas_vindas` | ✅ | ❌ | ✅ | `GET /propriedade/boas-vindas` |
| `alterar_texto_de_boas_vindas` | ✅ PUT | ❌ | ❌ sem botão | **Salvar** |

Sessão (`GET/DELETE /sessoes/atual`) continua a da F8.1.

---

## Menu (delta em relação à F8.1)

| Destino | Título | `recepcao` | `staff` | `gestor` |
| --- | --- | :---: | :---: | :---: |
| `catalogo` | Catálogo | ✅ | ❌ | ✅ leitura |
| `vendaveis` | Itens vendáveis | ✅ | ❌ | ✅ leitura |
| `boas-vindas` | Recado de boas-vindas | ✅ | ❌ | ✅ leitura |

Casa dos três perfis **não** muda (fila, meus chamados, painel).

---

## Regras da superfície

- Sem sessão: os três paths não mostram manutenção — tela de
  entrada.
- Staff nesses endereços: a casca não renderiza o conteúdo e
  **não** dispara GET/POST/PATCH/PUT destas rotas.
- Gestão: monta a tela, dispara o GET, **não** oferece criar,
  editar, desativar, reativar nem salvar.
- Recepção: GET e controles de escrita.
- Compacto da equipe: estas telas **não** usam `compacto`.

---

## Não chamar nesta fatia

| Operação | Por que não |
| --- | --- |
| `GET /catalogo/ativo` | Fonte do atendimento, não da manutenção |
| `confirmar_fase_da_reserva` | Chegada/saída já têm tela |
| `alterar_personalidade` | Fora desta fatia |
| CRUD de usuário / mercado / retenção | F8.7 |
