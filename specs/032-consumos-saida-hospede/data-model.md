# Modelo de dados — Consumos a lançar e saída do hóspede

Referência: `docs/04-schema.sql`. Decisões em [research.md](./research.md).
Esta fatia **não cria tabela**. `consumo`, `solicitacao` e `reserva`
são os da F3.7 e F4.1–F4.2. O que nasce é modelo de superfície no
frontend.

---

## Entidades novas (só de superfície)

### Item da fila financeira

Projeção de um item de `GET /consumos/pendentes`. Não é persistida.
Ordem = ordem do array (já `aberta_em` crescente).

| Campo (API) | Uso na tela |
| --- | --- |
| `id_solicitacao` | Identidade do POST de lançamento/dispensa |
| `id_reserva` | Alvo de **Ver ficha** (`/ficha/{id}`) |
| `descricao_item` | Texto visível do item |
| `descricao` | Não exibir (pode ecoar texto livre) |
| `numero_quarto` | Quarto, ou vazio perceptível |
| `valor_praticado` | Valor da linha e da soma |
| `aberta_em` | Entrada de `tempoDecorrido` |
| `status_lancamento` | Sempre `pendente` nesta lista; não oferece outro status |
| `resolvida_em` | Não é ação nesta tela (quarto ≠ lançamento) |

A tela **não** lê nome, telefone, documento. Esses campos **não**
existem neste JSON (contrato F3.7).

### Resumo financeiro

Derivado do array: quantidade, `totalPendente` (soma dos valores),
tempo de espera do primeiro item. Não há coluna no banco.

### Item cobrável da saída

Projeção de `GET .../pedidos-feitos-pelo-chat`. Sem
`status_lancamento`.

| Campo (API) | Uso na tela |
| --- | --- |
| `descricao_item` | Linha da lista |
| `valor_praticado` | Linha e conferência com o `total` do envelope |
| `id_solicitacao` | Identidade interna; não rótulo de pessoa |

### Aviso de pendência da estadia

Derivado: `pendentesDaEstadia(itensDaCasa, idReserva)`. Se
não-vazio, a saída avisa e aponta para `/consumos`. Não altera a
lista cobrável nem filtra Consumos a lançar.

### Tempo de espera

Derivado: `tempoDecorrido(aberta_em, agora)` já existente. Sem
coluna. Sem tique contínuo.

---

## Entidades reusadas

### `consumo` (banco)

| `status_lancamento` | Em Consumos a lançar? | Em pedidos da saída? |
| --- | :---: | :---: |
| `pendente` | sim | sim |
| `lancado` | não | sim |
| `dispensado` | não | não |

Transição `pendente` → `lancado` / `dispensado` continua na F3.7
(clique + autor + instante, sem recado). A tela não envia corpo no
POST. Resolver o quarto (F8.4) **não** tira o pendente daqui.

### `reserva`

Confirmar saída: `hospedado` → `encerrado` + `checkout_em`, como
F4.1. A tela só dispara o POST já existente. Consumo pendente e
chamado aberto **não** bloqueiam.

### Fila do dia (`vw_fila_do_dia`)

`saida_nao_confirmada` já é coluna da visão (F4.1). Esta fatia
passa a **exibir** o destaque. `resumirTurno` não ganha conta nova.
Caminho **Saída** só para `status = hospedado`.

### `usuario` / `sessao`

Casca da F8.1. Só `recepcao` monta estas telas. `staff` e `gestor`
não montam.

---

## O que não nasce

- Tabela, coluna, visão ou revisão Alembic
- Operação nova em `politica.py`
- Campo de nome no JSON de pendentes
- Campo de `status_lancamento` no JSON de pedidos feitos pelo chat
- Recorte HTTP da fila financeira por reserva
- Notificação empurrada
- GET de resumo de reserva

---

## Regras de validação (superfície)

| Situação | Efeito |
| --- | --- |
| `GET /consumos/pendentes` 200, `itens: []` | Lista vazia explícita; total zero; sem botão órfão |
| `GET` 401 | Casca devolve à entrada |
| `GET` 5xx / rede / corpo ilegível | Falha de leitura; não vazio; tentar de novo |
| Primeiro item do array | Mais antigo; a tela não reordena |
| **Ver ficha** | Navega; zero POST financeiro |
| **Marcar lançado** / **Dispensar** | POST respectivo; botão daquele item indisponível até o retorno |
| POST lançamento/dispensa 200 | GET de novo; id some; totais recalculam |
| POST 409 | Motivo visível; GET de novo; não afirma lançado/dispensado |
| Clique fora do botão | Zero POST |
| `/saida` sem id | Texto honesto; zero fetch |
| `/saida/:id` | GET ficha + pedidos + pendentes + fila |
| Ficha ou pedidos 404 | Recado genérico; sem confirmar existência; sem botão de confirmar |
| Aviso de pendência | Há item daquela reserva em pendentes da casa; link para `/consumos` sem filtro |
| **Confirmar saída** | Só se `status_reserva === hospedado`; POST `/saida`; sem diálogo |
| POST saída 200 | Botão some; estado encerrado; pendentes da casa continuam se ainda houver |
| POST saída 409 | Motivo visível; não afirma encerrado |
| **Saída** na fila | Só hospedado; `<Link>`; zero POST |
| `saida_nao_confirmada` | Destaque distinto da chegada vencida |

---

## Relacionamentos

```text
sessao recepção ──> GET /consumos/pendentes ──> TelaConsumos
                         │                         ├─ Ver ficha → /ficha/{id}
                         │                         ├─ Marcar lançado → POST .../lancamento → GET
                         │                         └─ Dispensar → POST .../dispensa → GET
                   GET /fila-do-dia ──> TelaFila
                         │                 ├─ Saída → /saida/{id}   (Link)
                         │                 └─ saida_nao_confirmada (destaque)
                   /saida/:id ──> TelaSaida
                         ├─ GET ficha
                         ├─ GET pedidos-feitos-pelo-chat
                         ├─ GET /consumos/pendentes  (aviso; link → /consumos)
                         ├─ GET /fila-do-dia         (datas, se ainda na fila)
                         └─ Confirmar saída → POST .../saida
sessao staff/gestão ──> casca redireciona; zero fetch destas telas
```
