# Modelo de dados — Conferir o CPF

Referência: `docs/04-schema.sql`. Sem tabela nova. Sem índice novo.
`uq_hospede_documento (tipo_documento, numero_documento)` permanece.

## Entidades

### Hóspede (`hospede`)

| Campo | Desta fatia |
| --- | --- |
| `tipo_documento` | `cpf` \| `rg` \| `passaporte`. Inalterado |
| `numero_documento` | Se tipo é `cpf` e o número foi **aceito nesta fatia**: exatamente onze dígitos. Se o cadastro ficou de fora da migração (par que colidiria): escrita original, possivelmente pontuada. RG/passaporte: regras atuais |

Não se revalida dígito em lote. Próximo `PUT` recusa número ruim.

### Ficha (ciclo)

Estados já existentes. CPF recusado na **coleta** conta como
`numero_documento` ausente → `ficha_parcial` (ou permanece
irreconhecível se nada mais veio). No **painel**, recusa **não**
muda status: nada daquele salvamento entra.

### Superfície

O JSON da API carrega onze dígitos quando o valor é canônico. A
tela e o texto de cópia mostram `000.000.000-00`. Não é coluna.

## Regras de validação

Só quando `tipo_documento = cpf` e há número informado:

1. Extrair dígitos (ignorar espaço, ponto, hífen).
2. Reprovar se não forem exatamente onze.
3. Reprovar se os onze forem iguais.
4. Reprovar se os dígitos verificadores da Receita não fecharem.
5. Aceito → persistir os onze dígitos.

RG e passaporte: não passam por 2–5.

## Transições

Nenhuma transição nova. Coleta: o que já faz `refinar_resultado` +
`consolidar_ficha_titular`. Painel: `completar_ficha_titular` já
recusa o lote em `DadosInvalidos`; esta fatia acrescenta CPF à
lista de inválidos.

## Migração (dados, não forma)

Grupos de `hospede` tipo `cpf` com número, pela forma de onze
dígitos:

- tamanho 1 → `UPDATE` para essa forma
- tamanho ≥ 2 → nenhuma linha do grupo muda; log de ids

Cadastros sem tipo CPF não entram.
