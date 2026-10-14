# Contrato: distintivos na Fila do dia

Nenhuma rota nova. Operação continua `ler_fila_do_dia` (só recepção).
Sem item de menu, sem “ciente”.

## `GET /fila-do-dia`

Cada item ganha:

```json
"omissoes": [
  { "chave": "ficha_nao_processada", "texto": "Ficha não processada", "contagem": 1 },
  { "chave": "mensagem_hospede_sem_resposta", "texto": "2 mensagens do hóspede sem resposta", "contagem": 2 }
]
```

- Lista vazia quando não há trabalho `falha` ligado à reserva, quando
  a reserva está `encerrado`, ou quando a falha é só mercado.
- Várias chaves: **todas** na mesma linha, ordem estável = ordem da
  tabela do catálogo (research §6), não ordem de `id_trabalho`.
- `texto` já vem pronto (singular / plural). O cliente não concatena.
- `chave` é estável para teste; a recepção lê `texto`.

Campos booleanos atuais **não** mudam de significado
(`chegada_nao_confirmada`, `boas_vindas_nao_enviadas`,
`saida_nao_confirmada`, `precisa_atendimento_humano`).

Hotel só o da sessão. Sem `id_hotel` no cliente.

## Superfície (`TelaFila`)

Na célula de situação, **depois** dos quatro sinais já existentes,
um `<span>` por omissão.

- Visual próprio: fundo sky (`bg-sky-100` / texto `text-sky-900`),
  distinto de vermelho, laranja, âmbar e violeta.
- Conteúdo = `texto`. MUST NOT mostrar `chave`, nome de exceção,
  CPF, telefone.
- Sem botão, sem clique que silencie.
- Confirmar saída: a reserva some da condição de distintivo
  (`encerrado` → `omissoes: []`); se a linha ainda listar, sem
  rótulo sky.

## Autorização

Intocada. `staff` / `gestor` continuam 403. Sem operação nova na
matriz.
