# Contrato: verificação estrutural do Artigo XIV

Olha o **catálogo** do banco, não as linhas.

Uma tabela em `public` passa se:

- tem coluna `id_hotel`, ou
- tem chave estrangeira **obrigatória** (NOT NULL) para uma
  tabela que já passou (recursivo, só filho→pai).

Ser referenciada por outra tabela **não** conta.

## Exceções (nomeadas no teste, com motivo)

| Tabela | Motivo |
| --- | --- |
| `alembic_version` | Versionamento, não domínio |
| `evento_webhook` | Idempotência do canal; hotel entra no processamento |

## Comportamento

- Esquema sem `hospede.id_hotel`: a lista de reprovadas **inclui**
  `hospede`.
- `head` desta fatia: `hospede` **não** está na lista.
- Tabela de domínio nova sem dono e sem pai com dono: falha.
- Consentimento e mensagem passam por serem filhos, sem coluna
  própria.
