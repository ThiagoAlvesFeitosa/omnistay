# Contrato: superfície — Consumos a lançar

Fonte: `TelaConsumos` em `/app/consumos`.
A casca (F8.1) permanece: menu, sair, recusa de destino alheio.

Recepção no computador. Sem layout de mão nesta tela.

---

## Consumos a lançar (`/app/consumos`)

Título **Consumos a lançar** (já era o do destino).

**Resumo** — com `200` e lista lida: quantidade de pendentes, total
pendente (soma dos `valor_praticado`), tempo de espera do mais
antigo (`tempoDecorrido` do primeiro item).

**Lista** — uma linha por item, na ordem do GET (mais antigos
primeiro). Por linha, visíveis:

- descrição do item (`descricao_item`)
- quarto quando conhecido; ausência perceptível
- valor praticado
- tempo de espera
- **Ver ficha** — link para `/ficha/{id_reserva}`
- **Marcar lançado** — `<button>`
- **Dispensar** — `<button>` distinto

**Não visíveis na linha:** nome, telefone, documento, endereço,
`descricao` livre da solicitação, “extrato”, “conta”.

Clique em descrição, quarto, valor ou **Ver ficha** **não** lança
nem dispensa. Os dois botões não disparam um ao outro.

Enquanto o POST daquele item não volta, o botão acionado daquela
linha não aceita segundo clique.

**Lista vazia** (`200` + `itens: []`): texto de que não há consumo
a lançar; total zero. Não é página em branco. Sem botão órfão.

**Falha de leitura** (rede, 5xx, corpo ilegível): o painel (menu,
título) permanece. A lista declara que não carregou. Oferece
**Tentar de novo**. **Não** usa o estado de lista vazia. **Não**
manda à tela de entrada (isso é só 401).

**Carregando**: título visível; não mostrar total zero como se o
turno financeiro estivesse limpo até chegar o `200`.

---

## O que não aparece

- Resolver o quarto
- Confirmar saída
- Recorte por reserva
- Status “lançado” / “dispensado” de item que já saiu (eles não
  estão nesta lista)
- Destino `consumos` para staff ou gestão (casca já redireciona)
