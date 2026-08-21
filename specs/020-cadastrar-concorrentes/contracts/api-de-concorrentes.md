# Contrato: API de concorrentes (F5.1)

Quatro rotas. Cookie de sessão `omnistay_sessao`. O hotel é **sempre** o da
sessão — corpo e query **não** carregam `id_hotel`.

Autorização: [politica-de-autorizacao.md](./politica-de-autorizacao.md).
Modelo: [data-model.md](../data-model.md).
Contrato da coleta futura: [fontes-ativas.md](./fontes-ativas.md).

---

## Convenções

| Tema | Regra |
| --- | --- |
| Autenticação | Cookie; ausência → `401` |
| Autorização | Perfil sem permissão → `403` |
| Outro hotel / id inexistente | `404` (mesma resposta; não revela existência) |
| Validação de formato | `422` com mensagem por campo / regra |
| Fonte já cadastrada no hotel | `409` |
| Logs | `id_concorrente`, `id_hotel`, ação — sem `nome` e sem `url_fonte` |

---

## Item (resposta de manutenção)

```text
id_concorrente
nome
url_fonte
ativo
```

Sem `id_hotel` no JSON. Sem `criado_em` nesta fatia (a spec não pede).

---

## `POST /concorrentes`

**Operação**: `alterar_concorrentes`

Cria concorrente ativo na propriedade da sessão.

### Entrada

```json
{
  "nome": "Hotel Praia Norte",
  "url_fonte": "https://www.exemplo.com/hotel-praia-norte"
}
```

| Campo | Obrigatório | Regra |
| --- | --- | --- |
| `nome` | sim | Trim; 1 a 120 caracteres visíveis |
| `url_fonte` | sim | Trim; 1 a 400; `http` ou `https` com anfitrião; sem espaço; sem usuário/senha na URL |

Não aceita `ativo` na criação (nasce ativo). Não aceita `id_hotel`.

### Saída `201`

```json
{
  "id_concorrente": 4,
  "nome": "Hotel Praia Norte",
  "url_fonte": "https://www.exemplo.com/hotel-praia-norte",
  "ativo": true
}
```

### Erros

| Situação | Status |
| --- | --- |
| Sessão ausente/inválida | `401` |
| Perfil não é gestão | `403` |
| Campo ausente, só espaços, URL inválida, nome > 120, URL > 400 | `422` |
| Mesma fonte já existe no hotel (ativo ou inativo; diferença só de maiúsculas ou espaços nas pontas) | `409` |

---

## `GET /concorrentes`

**Operação**: `ler_concorrentes`

Lista de manutenção: ativos e inativos do hotel da sessão.

### Saída `200`

```json
{
  "concorrentes": [
    {
      "id_concorrente": 4,
      "nome": "Hotel Praia Norte",
      "url_fonte": "https://www.exemplo.com/hotel-praia-norte",
      "ativo": true
    }
  ]
}
```

Ordem: `nome`, depois `id_concorrente`. Hotel sem fichas: `"concorrentes": []`.

---

## `GET /concorrentes/ativos`

**Operação**: `ler_concorrentes`

Fontes ativas da propriedade. Item inativo não aparece. Sem campo `ativo`.

### Saída `200`

```json
{
  "fontes": [
    {
      "id_concorrente": 4,
      "nome": "Hotel Praia Norte",
      "url_fonte": "https://www.exemplo.com/hotel-praia-norte"
    }
  ]
}
```

Ordem: `nome`, depois `id_concorrente`. Propriedade sem ativo: `"fontes": []`,
não é erro. Esta rota **não** visita as URLs.

---

## `PATCH /concorrentes/{id_concorrente}`

**Operação**: `alterar_concorrentes`

Altera nome, endereço e/ou `ativo` de um concorrente do hotel da sessão.

### Entrada

Pelo menos um campo:

```json
{
  "nome": "Hotel Praia Norte",
  "url_fonte": "https://www.exemplo.com/outra-pagina",
  "ativo": false
}
```

| Campo | Obrigatório | Regra |
| --- | --- | --- |
| `nome` | não | Se presente: trim; 1 a 120 |
| `url_fonte` | não | Se presente: mesmas regras do POST |
| `ativo` | não | `true` reativa; `false` desativa |

### Saída `200`

Mesmo formato do `201` de criação, com os valores atuais.

### Erros

| Situação | Status |
| --- | --- |
| Sessão ausente/inválida | `401` |
| Perfil não é gestão | `403` |
| Id inexistente **ou** de outro hotel | `404` |
| Corpo vazio, só espaços, URL inválida | `422` |
| URL colide com outra ficha do mesmo hotel | `409` |

---

## `DELETE /concorrentes/{id_concorrente}`

Não existe. Resposta `405`. O caminho suportado é `PATCH` com `"ativo": false`.

---

## Recusas por perfil (resumo)

| Rota | recepção | gestão | operação |
| --- | --- | --- | --- |
| `POST` / `PATCH` | `403` | sim | `403` |
| `GET /concorrentes` e `GET /concorrentes/ativos` | `403` | sim | `403` |
