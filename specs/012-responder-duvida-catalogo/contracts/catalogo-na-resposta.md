# Contrato: catálogo na resposta à dúvida

Porta já entregue na F2.1: [catalogo-repository.md da F2.1](../../008-catalogo-propriedade/contracts/catalogo-repository.md).
Esta fatia **consome** `listar_ativos`; não altera CRUD HTTP.

---

## Uso em `responder_duvida`

```text
itens = catalogo.listar_ativos(id_hotel)
```

`id_hotel` é o do trabalho / da reserva. Nunca o de outra propriedade.

| Situação | Efeito |
| --- | --- |
| Tupla com itens | esses itens (e só eles) vão para `responder_duvida` |
| Tupla vazia | não coberta; porta de LLM **não** é chamada |
| Item inativo | a porta já omite; não é fato afirmável |
| Hotel B lista | zero itens do hotel A |

Não há busca por palavra-chave, ranking nem embedding. O conjunto ativo completo é a
fonte — ADR do Artefato 5 §10.2.

Título e conteúdo **não** vão para log.

---

## Implementações (inalteradas)

| Classe | Uso nesta fatia |
| --- | --- |
| `CatalogoBanco(conexao)` | Padrão do worker na transação corrente |
| `CatalogoFalso` | Unitários; `configurar(id_hotel, itens)` |

HTTP `GET /catalogo` e `GET /catalogo/ativo` **não** mudam. Semeadura nos testes de
integração pode usar essas rotas (recepção) ou o falso injetado no worker.

---

## Fora desta fatia

- Criar, editar, desativar item
- Preço estruturado (F3.7)
- Trocar a porta por busca semântica
