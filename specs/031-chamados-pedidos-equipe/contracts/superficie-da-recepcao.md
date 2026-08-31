# Contrato: superfície da recepção — Chamados e pedidos

Fonte: `TelaAlertas` em `/app/alertas`.
A casca (F8.1) permanece: menu, sair, recusa de destino alheio.

Recepção no computador. Sem layout de mão nesta tela.

---

## Chamados e pedidos (`/app/alertas`)

Título **Chamados e pedidos** (já era o do destino).

**Lista** — uma linha por item, na ordem do `GET` (mais antigos
primeiro). Por linha, visíveis:

- natureza distinguível (reclamação × serviço × consumo)
- tempo decorrido (`tempoDecorrido`)
- descrição
- quarto quando conhecido; ausência perceptível (não inventar número)
- urgência
- janela de preferência, se houver
- valor praticado, se consumo
- destaque de tempo excessivo só quando `destaque_tempo_excedido`
- **Ver ficha** — link para `/ficha/{id_reserva}`
- **Resolvido** — `<button>` na linha

**Não visíveis na linha:** nome, telefone, documento, endereço,
`id_reserva` como rótulo de pessoa, lançar/dispensar, “extrato”,
“conta”.

**Ver ficha** convive com **Resolvido**. Clique em descrição, quarto
ou natureza **não** resolve. **Ver ficha** **não** resolve.

**Resolvido** — um clique envia o `POST`; sem diálogo. Enquanto
aquele `POST` não volta, o botão daquela linha não aceita segundo
clique.

**Lista vazia** (`200` + `itens: []`): texto de que não há pendência
aberta. Não é página em branco. Sem botão órfão.

**Falha de leitura** (rede, 5xx, corpo ilegível): o painel (menu,
título) permanece. A lista declara que não carregou. Oferece
**Tentar de novo** (repete o `GET`). **Não** usa o estado de lista
vazia. **Não** manda à tela de entrada (isso é só 401).

**Carregando**: título visível; não mostrar vazio como se o turno
estivesse limpo até chegar o `200`.

---

## Ficha a partir desta lista

Navega para o destino já existente `/app/ficha/:idReserva`. Sem
GET de ficha enquanto a pessoa está em `/app/alertas`.

Menu `/app/ficha` sem id: continua o vazio da F8.3 (aponta à fila;
zero GET). A frase do vazio pode citar também Chamados e pedidos
como origem quando há id na linha.

---

## O que não aparece

- Abas abertos / em andamento / resolvidos hoje
- Coluna de atribuído ou canal
- Pergunta fora do catálogo
- Lançar ou dispensar consumo
- Confirmar saída, catálogo, nova reserva
- Destino `alertas` para staff ou gestão (casca já redireciona)
