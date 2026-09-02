# Contrato: superfície da fila do dia (delta)

`TelaFila` em `/app/fila`. Cadastro, chegada e saída **intactos**.

---

## Distintivo de atendimento humano

Quando `precisa_atendimento_humano` é verdadeiro, a linha mostra
rótulo distinto das pendências já existentes (ficha parcial,
recado não enviado, chegada/saída não confirmada). Não substitui
esses rótulos.

O atalho da linha para a reserva passa a chamar-se **Estadia**
(mesmo destino `/ficha/{id}`).

---

## Chamados e pedidos / Consumos

O atalho que hoje se chama **Ver ficha** passa a **Estadia**,
mesmo `to`. **Resolvido** / lançar **não** mudam.
