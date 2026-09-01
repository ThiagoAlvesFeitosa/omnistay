# Contrato: superfície — Saída do hóspede

Fonte: `TelaSaida` em `/app/saida` e `/app/saida/:idReserva`.
A casca (F8.1) permanece.

Recepção no computador. Sem layout de mão nesta tela.

---

## Sem reserva (`/app/saida`)

Título **Saída do hóspede**.

Texto honesto: a saída se abre pela fila do dia. Sem botão
**Confirmar saída**. **Zero** GET de ficha, pedidos, pendentes ou
fila.

---

## Com reserva (`/app/saida/:idReserva`)

Título **Saída do hóspede**.

**Identidade** — nome do titular (ficha); datas previstas se a
reserva ainda estiver na fila do dia; quarto quando um pendente
daquela estadia o trouxer.

**Lista** — título **Pedidos feitos pelo chat**. Cada linha:
descrição do item e valor praticado. Total do envelope. Sem coluna
de status de lançamento. Sem “extrato”. Sem “conta”.

Pedido de serviço sem cobrança e consumo dispensado **não** vêm
neste GET — a tela não os inventa.

**Lista vazia** (`itens: []`): estado honesto, sem aviso de
pendência de lançamento. Confirmar saída continua se estiver
hospedada.

**Aviso de pendência** — se `GET /consumos/pendentes` tiver ao
menos um item com o `id_reserva` desta tela: texto explícito de
que há consumo pendente da estadia, **antes** do botão de
confirmar. O aviso é caminho para `/consumos` (fila da casa, sem
filtro). A tela **não** oferece lançar nem dispensar.

**Confirmar saída** — `<button>` só se `status_reserva ===
hospedado`. Um clique, sem diálogo. Clicar nome, lista ou aviso
**não** confirma.

Depois de `200`: o botão some. A lista cobrável permanece visível.
O aviso permanece se o GET de pendentes ainda mostrar item desta
estadia (lançar depois do checkout é válido).

**Falha ao carregar** ficha, pedidos ou pendentes: painel
permanece; declara que não carregou; **Tentar de novo**. Não é
lista vazia nem checkout concluído.

**404**: recado genérico; sem nome; sem botão de confirmar.

---

## O que não aparece

- Status pendente/lançado por linha da lista cobrável
- Lançar ou dispensar nesta tela
- Pesquisa de avaliação para a recepção redigir
- Destino `saida` para staff ou gestão (casca já redireciona,
  inclusive `/saida/:id`)
