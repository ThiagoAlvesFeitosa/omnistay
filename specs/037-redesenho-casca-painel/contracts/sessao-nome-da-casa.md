# Contrato: nome da casa na sessão

Paths e cookie **inalterados**. Só o JSON de sucesso ganha
`nome_hotel`. Matriz de operações intacta.

---

## `POST /sessoes` — 201

Campos atuais mais:

```json
{
  "id_usuario": 3,
  "nome": "Cleber Rocha",
  "perfil": "staff",
  "expira_em": "2026-09-10T14:22:31Z",
  "nome_hotel": "Pousada Exemplo"
}
```

`id_hotel` **não** entra no corpo. Token continua só no cookie.

---

## `GET /sessoes/atual` — 200

Campos atuais mais o mesmo `nome_hotel`.

O roteador resolve o nome com a conexão da requisição e o `id_hotel`
já presente na sessão: `propriedade.service.ler_nome_hotel`. Não há
segunda ida HTTP.

---

## Isolamento

Funcionário da propriedade A nunca recebe o `nome` da propriedade B,
nem no POST nem no GET.

Nome ausente ou em branco no cadastro: `""`. A casca mostra a área
do nome vazia.

---

## Recusas

401 / 422 / 204 de sessão **não mudam**. Não se acrescenta `nome_hotel`
em erro.

`GET /sessoes` (lista da recepção) e `DELETE /sessoes/{id}` **não**
ganham o campo — não alimentam o cabeçalho da casca.

---

## Casca

Tipos `SessaoCriada` e `SessaoAtual` em `sessao.ts` incluem
`nome_hotel`. Entrar e recarregar usam o valor do JSON; a casca **não**
chama um GET de propriedade só para o título.
