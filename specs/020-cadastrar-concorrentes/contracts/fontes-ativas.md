# Contrato: fontes ativas (gancho da F5.2)

A consulta de fontes ativas é o conjunto que a coleta posterior **pode** usar.
Esta fatia entrega a consulta e **não** a executa. Sem porta hexagonal: o
único consumidor futuro é o próprio módulo `mercado`.

Modelo: [data-model.md](../data-model.md). HTTP:
[api-de-concorrentes.md](./api-de-concorrentes.md) (`GET /concorrentes/ativos`).

---

## Função

```text
listar_fontes_ativas(id_hotel) -> sequencia de
  id_concorrente
  nome
  url_fonte
```

Regras:

- Filtra `id_hotel` **e** `ativo = true`. Inativo não retorna.
- Hotel sem ativo: sequência vazia, não é erro.
- Não visita `url_fonte`. Não lê `coleta_mercado`. Não dispara trabalho.
- Ordem estável: `nome`, depois `id_concorrente`.

HTTP de manutenção **não** precisa desta função para listar inativos; usa a
consulta de manutenção. A F5.2 **não** relê a tabela com outro predicado: se
precisar de ativos, chama esta função (ou o `GET` equivalente nos testes).

---

## O que este contrato recusa

| Tentação | Por que não |
| --- | --- |
| Incluir inativo “para histórico” | Fonte desativada não é consultada |
| Abrir a URL para validar | Spec desta fatia; coleta honesta é F5.2 |
| Devolver preço / nota / última coleta | Ainda não existem linhas desta fatia |
| Ignorar `id_hotel` | Artigo XIV |
