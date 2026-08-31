# Contrato: política de autorização — F8.3

Esta fatia **não acrescenta operação** à matriz. `alterar_ficha_de_hospede`
já existe e passa a ter rota.

A casca já omite `ficha` do menu de staff e gestão. Precisa tratar
`/app/ficha/:id` como o mesmo destino (prefixo), senão o parâmetro
furaria o redirecionamento.

Isolamento por hotel: `id_hotel` da sessão. Ficha de reserva alheia
→ `404` (não `403`), como o GET da F1.3.

---

## Operações que estas telas disparam

| Operação existente | `recepcao` | `staff` | `gestor` | Rota |
| --- | :---: | :---: | :---: | --- |
| `ler_ficha_de_hospede` | ✅ | ❌ | ❌ | `GET /reservas/{id}/ficha` |
| `alterar_ficha_de_hospede` | ✅ | ❌ | ❌ | `PUT /reservas/{id}/ficha` |
| `ler_consentimento` | ✅ | ❌ | ✅ | `GET /hospedes/{id}/consentimento` |
| `registrar_consentimento` | ✅ | ❌ | ✅ | `POST /hospedes/{id}/consentimento` |

Nesta superfície, só `recepcao` dispara as quatro. Gestão **não**
monta a tela (veria o cadastral). A API de consentimento da gestão
permanece para outros usos; não é caminho desta fatia.

A casca continua com sessão (`GET/DELETE /sessoes/atual`) como na F8.1.

---

## Não chamar nesta fatia

| Operação | Por que não |
| --- | --- |
| `ler_fila_do_dia` | Só ao voltar à fila (tela da F8.2) |
| `confirmar_fase_da_reserva` | Chegada continua na fila; saída é F8.5 |
| `alterar_reserva` | Cadastro mínimo é F8.2 |
| `ler_solicitacao_atribuida` | F8.4 |

---

## Regras da superfície

- Sem sessão: `/app/ficha` não mostra campos — tela de entrada (F8.1).
- Staff e gestão no endereço da ficha (com ou sem id): a casca **não**
  renderiza o conteúdo e **não** dispara GET/PUT de ficha nem
  consentimento.
- Nome, documento, telefone e endereço só na sessão de recepção, só
  nesta tela (e no que a F8.2 já mostra na fila: nome e telefone).
- Menu `/app/ficha` sem id: zero fetch de ficha.
