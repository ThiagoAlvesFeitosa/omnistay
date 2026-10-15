# Contrato: conferência do número (CPF)

Função pura usada pela coleta e pelo painel. Sem I/O.

Entrada: `tipo_documento` e `numero_documento` como a pessoa
informou (ou `null`).

| Tipo | Número | Saída do número |
| --- | --- | --- |
| `cpf` | dígitos verificadores ok, com ou sem pontuação | onze dígitos |
| `cpf` | onze iguais (`111.111.111-11` etc.) | ausente (reprovado) |
| `cpf` | dígito verificador não fecha (`123.456.789-00`) | ausente |
| `cpf` | ≠ onze dígitos, letras, vazio | ausente |
| `rg` / `passaporte` | qualquer texto não vazio já aceito hoje | inalterado |
| ausente / outro | — | conferência de CPF **não** corre |

Tipo `cpf` válido continua na saída mesmo se o número cair. O
número cai sozinho.

Nunca logar o número aqui — a função não registra.
