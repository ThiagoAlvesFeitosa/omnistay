# Contrato: migração e logs

## Revisão `0027`

Atualiza `hospede.numero_documento` quando `tipo_documento = 'cpf'`.

| Grupo (mesma forma de onze dígitos) | Efeito |
| --- | --- |
| Uma linha | `UPDATE` para onze dígitos |
| Duas ou mais | **nenhuma** linha do grupo muda |

Não apaga cadastro. Não recria nem relaxa `uq_hospede_documento`.
Não revalida dígito verificador em lote.

Linhas que não são CPF: intocadas.

## Log da migração

Quando houver grupo pulado:

```text
cpf_migracao_colisao pares=<n> ids=<id_hospede,...>
```

Nível `warning`. Só identificadores e a contagem. **Nunca** o CPF,
nem pontuado nem em dígitos.

Grupos convertidos: sem necessidade de logar cada id (evita ruído).
O teste da colisão lê o `warning`.

## Log de recusa no PUT / coleta

Identificadores + código (`422` ou consolidação parcial). Sem
número. Sem `str` da exceção que traga o documento.
