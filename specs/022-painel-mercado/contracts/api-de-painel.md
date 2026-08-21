# Contrato: API do painel de mercado (F5.3)

Dois GETs. Cookie de sessão `omnistay_sessao`. O hotel é **sempre** o da
sessão — corpo e query **não** carregam `id_hotel`.

Autorização: [politica-de-autorizacao.md](./politica-de-autorizacao.md).
Situação: [situacao-do-dado.md](./situacao-do-dado.md).
Modelo: [data-model.md](../data-model.md).

Esta fatia **não** visita fonte, **não** enfileira `coletar_mercado` e
**não** altera `coleta_mercado`.

---

## Convenções

| Tema | Regra |
| --- | --- |
| Autenticação | Cookie; ausência → `401` |
| Autorização | Perfil sem `ler_mercado` → `403` |
| Outro hotel / id inexistente | `404` (mesma resposta; não revela existência) |
| Escrita de coleta | Método inexistente → `405` |
| Logs | `id_hotel`, `id_concorrente` (quando houver), ação `painel` ou `historico` — sem preço, sem nota, sem URL |
| `id_hotel` no JSON | Ausente |

`preco` e `nota_media` no JSON são números (`Decimal`). Campo não obtido é
`null`, nunca `0`. Zero encontrado é `0`.

Datas em ISO-8601 com fuso (`TIMESTAMPTZ`).

---

## `GET /mercado`

**Operação**: `ler_mercado`

Visão atual de todos os concorrentes da propriedade (ativos e inativos).
Uma consulta, sem etapa obrigatória de histórico.

### Saída `200`

```json
{
  "periodicidade_horas": 24,
  "concorrentes": [
    {
      "id_concorrente": 4,
      "nome": "Hotel Praia Norte",
      "ativo": true,
      "situacao": "atual",
      "ultimo_sucesso": {
        "preco": 150.0,
        "nota_media": 4.5,
        "coletado_em": "2026-08-21T10:00:00+00:00"
      },
      "ultima_falha": null
    }
  ]
}
```

| Campo | Regra |
| --- | --- |
| `periodicidade_horas` | Inteiro ≥ 1 da chave da propriedade, ou `null` se ausente/inválido |
| `concorrentes` | Todos os da sessão; ordem `nome`, depois `id_concorrente` |
| `situacao` | Um de `atual`, `desatualizado`, `cadencia_ausente`, `sem_coleta`, `so_falha` |
| `ultimo_sucesso` | Objeto ou `null` (sem sucesso na série) |
| `ultima_falha` | `{ "coletado_em": ... }` ou `null` |

Hotel sem concorrente: `"concorrentes": []` — não é erro.

Concorrente nunca coletado: `situacao = sem_coleta`, os dois blocos `null`.

Só falhas: `situacao = so_falha`, `ultimo_sucesso = null`, `ultima_falha`
com a data da falha mais recente.

Inativo: `ativo = false`; série e situação iguais às regras gerais.

Sem `url_fonte`. Sem tarifa da própria casa. Sem lista de pontos da série.

### Erros

| Situação | Status |
| --- | --- |
| Sessão ausente/inválida | `401` |
| Perfil não é gestão | `403` |

---

## `GET /mercado/concorrentes/{id_concorrente}`

**Operação**: `ler_mercado`

Histórico completo da série daquele concorrente, se for da propriedade da
sessão.

### Saída `200`

```json
{
  "id_concorrente": 4,
  "nome": "Hotel Praia Norte",
  "ativo": true,
  "coletas": [
    {
      "id_coleta": 1,
      "sucesso": true,
      "preco": 140.0,
      "nota_media": 4.4,
      "coletado_em": "2026-08-19T10:00:00+00:00"
    },
    {
      "id_coleta": 2,
      "sucesso": false,
      "preco": null,
      "nota_media": null,
      "coletado_em": "2026-08-20T10:00:00+00:00"
    },
    {
      "id_coleta": 3,
      "sucesso": true,
      "preco": 150.0,
      "nota_media": 4.5,
      "coletado_em": "2026-08-21T10:00:00+00:00"
    }
  ]
}
```

Ordem de `coletas`: `coletado_em` crescente, depois `id_coleta` crescente.
Falha intercalada permanece na lista, com `preco` e `nota_media` nulos —
nunca `0`. Série vazia (cadastrado, nunca coletado): `"coletas": []`.

Não inclui `situacao` (é da visão atual). Não inclui `url_fonte`.

### Erros

| Situação | Status |
| --- | --- |
| Sessão ausente/inválida | `401` |
| Perfil não é gestão | `403` |
| Id inexistente **ou** de outro hotel | `404` |

---

## Métodos que não existem

| Tentativa | Status |
| --- | --- |
| `POST /mercado` | `405` |
| `PATCH` / `PUT` / `DELETE` em `/mercado` ou `/mercado/concorrentes/{id}` | `405` |
| `POST /mercado/concorrentes/{id}` (inventa ponto) | `405` |

O cadastro de concorrente (`POST`/`PATCH /concorrentes`) permanece a F5.1
e **não** grava `coleta_mercado`.

---

## Recusas por perfil (resumo)

| Rota | recepção | gestão | operação |
| --- | :---: | :---: | :---: |
| `GET /mercado` | `403` | sim | `403` |
| `GET /mercado/concorrentes/{id}` | `403` | sim | `403` |
