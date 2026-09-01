# Contrato: acréscimo na fila do dia (F8.5)

Delta sobre [superficie-da-recepcao.md](../../029-fila-dia-reserva/contracts/superficie-da-recepcao.md).
Fonte: `TelaFila` em `/app/fila`.

O resumo do turno (três contas) **não muda**.

---

## Caminho de saída

Linha com `status === "hospedado"`: além de **Ver ficha**, um
`<Link>` rotulado **Saída** para `/saida/{id_reserva}`.

Não dispara `POST /reservas/{id}/saida`. Não se rotula **Confirmar
saída**.

Reserva ainda não hospedada: sem esse link. Encerrada que ainda
apareça (leitura humana da pesquisa): sem esse link.

Clique no nome ou no telefone continua sem confirmar chegada e
sem abrir a saída.

---

## Destaque de saída não confirmada

Se `saida_nao_confirmada`: rótulo distinto de “não confirmada”
(chegada vencida), de “recado não enviado” e de “parcial”.

`saida_nao_confirmada` e `chegada_nao_confirmada` não coexistem no
item (contrato F4.1). Saída prevista no dia corrente: flag falso;
o caminho **Saída** mesmo assim existe se estiver hospedada.

Depois do checkout, a reserva deixa de ser hospedada: o destaque
e o link somem no GET seguinte da fila.

---

## Tipo `ItemFila`

Passa a incluir `saida_nao_confirmada: boolean` (já vinha no JSON;
a F8.2 ignorava). `pesquisa_saida_leitura_humana` continua fora
desta superfície.
