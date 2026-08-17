# Contrato: `CatalogoRepository` (F2.1)

Porta para módulos que **não** governam `catalogo_item`. O módulo `propriedade` continua
sendo o único a escrever SQL; esta porta é a leitura do catálogo **ativo** que F2.2 e
F3.3 vão injetar.

Arquivo: `app/portas/catalogo.py` (padrão de `llm.py` / `mensageria.py`).

---

## Tipos

```text
ItemCatalogo
  id_catalogo_item: int
  categoria: str          # uma das cinco chaves
  titulo: str
  conteudo: str
```

Sem `ativo`: a porta só devolve o que pode ser afirmado.

---

## Operação

```text
CatalogoRepository
  listar_ativos(id_hotel) -> tuple[ItemCatalogo, ...]
```

- Filtra `id_hotel` **e** `ativo = true`.
- Ordem estável: `categoria`, depois `id_catalogo_item`.
- Hotel sem itens ativos: tupla vazia, não é erro.
- Não agrupa por categoria (agrupamento é apresentação HTTP).
- Não registra `titulo`/`conteudo` em log.

---

## Implementações

| Classe | Onde | Uso |
| --- | --- | --- |
| `CatalogoBanco` | `app/adaptadores/catalogo_banco.py` | Recebe a `Connection` da transação corrente; delega a `propriedade.repository.listar_ativos` |
| `CatalogoFalso` | `app/adaptadores/catalogo_falso.py` | Suíte; devolve o que o teste configurou; nunca abre banco |

Nenhum teste instancia um provedor externo. A HTTP `GET /catalogo/ativo` **não** precisa
da porta: o serviço de `propriedade` lê o repositório com a conexão do pedido. F2.2 /
F3.3 constroem `CatalogoBanco(conexao)` no worker.

---

## Fora desta fatia

- Montar prompt com o catálogo inteiro (F3.3)
- Montar pacote de boas-vindas (F2.2)
- Busca semântica / embedding (gatilho do Artefato 5, quando o catálogo não couber no prompt)
