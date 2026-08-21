# Contrato: registro de coleta

Uma linha de `coleta_mercado` por tentativa devida. Nunca UPDATE da anterior.
Modelo: [data-model.md](../data-model.md). Porta: [fonte-publica.md](./fonte-publica.md).

---

## INSERT

| Situação | `sucesso` | `preco` | `nota_media` | `coletado_em` |
| --- | :---: | --- | --- | --- |
| Porta devolveu preço e/ou nota 0–5 | `true` | valor ou nulo | valor ou nulo | agora |
| Preço público **zero** | `true` | `0` | como veio | agora |
| Diretiva `recusa` ou `ausente` | `false` | nulo | nulo | agora |
| `sem_dado` / `indisponivel` / `exige_autenticacao` | `false` | nulo | nulo | agora |
| Fonte inativa no claim | — | **não insere** | | |

Sucesso sem preço **e** sem nota é recusado pelo CHECK
`ck_coleta_sucesso_tem_dado`.

---

## O que a linha não guarda

- Motivo fino da falha (vai ao log)
- Texto da página
- Nome, identificador, foto ou comentário de avaliador
- URL da fonte (já está no concorrente)
- `id_hotel` (JOIN em `concorrente`)

---

## Janela devida

Seja `P` a periodicidade em horas da propriedade e `U` o `coletado_em` da
última linha daquela fonte (sucesso ou falha):

- Sem linha → devido.
- `agora >= U + P horas` → devido.
- Caso contrário → não enfileira.

Inativo não entra na conta (nem visita, nem linha nova).

---

## Isolamento

Toda consulta de série faz JOIN/`WHERE` em `concorrente.id_hotel`. Coleta do
hotel A não é lida nem gravada no ciclo do hotel B. Dois hotéis com a mesma
URL têm séries independentes (FKs de fichas distintas).

---

## Garantias no banco (testes de integração)

- Segundo INSERT de sucesso **não** altera o primeiro (comparar `id_coleta` e
  valores).
- INSERT de falha depois de sucesso deixa o sucesso intacto.
- `sucesso = true` sem preço nem nota → rejeitado pelo CHECK.
- `preco < 0` ou `nota_media` fora de 0–5 → rejeitado.

Não há UNIQUE de “uma coleta por dia”: a unicidade do ciclo aberto mora na
fila, não na série.
