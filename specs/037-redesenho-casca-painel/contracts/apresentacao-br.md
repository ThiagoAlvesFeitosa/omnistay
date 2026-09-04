# Contrato: moeda, data, instante e decorrido

Módulo: `frontend/src/painel/apresentacao.ts`. Uma regra; as telas
só chamam. Teste de unidade com exemplos fixos **antes** de mudar
produção (Artigo XII).

Fuso de instante e de “hoje”: relógio local da tela (`Date`), o mesmo
já usado no decorrido. Data **só calendário** (`YYYY-MM-DD`) não
atravessa fuso — parte-se a string.

---

## Moeda (valor lido)

`formatarMoeda(9)` → **`R$ 9,00`**.

- Símbolo `R$`, dois decimais, vírgula decimal, ponto de milhar
  acima de 999.
- Zero: **`R$ 0,00`**.
- Campo de digitação de preço: o valor **lido** (tabela, cartão,
  total) usa esta função; o input pode continuar aceitando o número
  que a pessoa já digita.
- Telas **não** prefixam `R$` na mão em cima de número cru.

`formatarPreco` de vendáveis passa a ser esta grafia (delega).

---

## Data de calendário

`formatarDataCalendario("2026-09-02")` → **`02/09/2026`**.

Usar em: fila (entrada/saída previstas), ficha (nascimento e aceite
quando for só dia), qualquer leitura `YYYY-MM-DD`.

Ilegível / incompleto: não inventar dia (vazio ou o texto já tratado
pela tela).

`input type="date"`: valor interno do controle intacto.

---

## Instante operacional (fora da bolha)

`formatarInstante(...)` → **`02/09/2026 14:32`** (sem segundos, sem
`2026-09-02T14:32`).

Usar em: coleta de mercado, execução de retenção, abertura de
chamado ou consumo **como relógio absoluto**.

Sem relógio parseável: data de calendário se houver dia; nunca
`00:00` inventado.

---

## Listas de chamados e consumos

`formatarInstanteComDecorrido(abertaEm, agora)` no espírito
**`02/09/2026 14:32 · há 8 min`**.

`tempoDecorrido` permanece. Não substituir um pelo outro.

Sem `aberta_em` utilizável: só o decorrido que a tela já mostrava;
não fabricar o instante.

Onde vale: Chamados e pedidos, Meus chamados, Consumos a lançar
(e o “mais antigo” da lista de consumos, se continuar a mostrar
decorrido).

---

## Bolha (exceção)

Ver [conversa-bolhas.md](./conversa-bolhas.md).
`formatarHorarioBolha(quando, agora)`:

- mesmo dia de calendário local: **`14:32`**
- outro dia: **`02/09/2026 14:32`**
- nunca “há 8 min”

---

## Telas que precisam deixar o inglês de máquina

Fila, Estadia/ficha (datas lidas), chamados, consumos, vendáveis,
painel da gestão, mercado, retenção, simulador (horário da bolha).
Testes de tela existentes: **mesmo cenário**, expectativa de grafia
atualizada.
