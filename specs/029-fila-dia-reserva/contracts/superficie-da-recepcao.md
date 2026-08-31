# Contrato: superfície da recepção

Fonte: `TelaFila` em `/app/fila` e `TelaNovaReserva` em `/app/reserva`.
A casca (F8.1) permanece: menu, sair, recusa de destino alheio.

Recepção no computador. Sem layout de mão nesta fatia.

---

## Fila do dia (`/app/fila`)

Título **Fila do dia** (já era o da casa).

**Resumo** — três contas distintas, ver [resumo-do-turno.md](./resumo-do-turno.md).

**Ação** — controle visível **Nova reserva** que navega para
`/app/reserva` (o destino já no menu).

**Lista** — uma linha por item. Colunas: hóspede (nome + telefone),
entrada, saída, situação (`status` em linguagem de negócio), ficha
(`estado_cadastro`), ação.

**Destaques** (rótulos distintos, sem o mesmo texto):

| Condição | Sinal |
| --- | --- |
| `chegada_nao_confirmada` | chegada vencida / não confirmada |
| `boas_vindas_nao_enviadas` | recado não enviado |
| `estado_cadastro === "parcial"` | parcial |

**Confirmar chegada** — `<button>` com esse rótulo **dentro** da
linha, só se o `status` admite. Não há `onClick` na linha, no nome
nem no telefone. Um clique envia o `POST`; sem diálogo.

Hospedado: sem esse botão e **sem** confirmar saída.

**Fila vazia** (`200` + `itens: []`): contas em zero, texto de turno
sem ninguém, Nova reserva alcançável. Não é página em branco.

**Falha de leitura** (rede, 5xx, corpo ilegível): o painel (menu,
título, Nova reserva) permanece. A lista declara que não carregou.
Oferece **Tentar de novo** (repete o `GET`). **Não** usa o estado de
fila vazia. **Não** manda à tela de entrada (isso é só 401).

**Carregando**: título visível; não mostrar contas em zero como se o
turno estivesse vazio até chegar o `200`.

---

## Nova reserva (`/app/reserva`)

Título **Nova reserva**.

Campos, nesta ordem: nome do hóspede, telefone com DDD, entrada, saída.
Sem e-mail, documento, endereço.

Telefone: recusa na digitação se os dígitos não forem brasileiro com
DDD (mesma regra da API). Datas: saída > entrada; recusa antes do
`POST` se não for.

**Cadastrar** — `POST /reservas`. **Cancelar** — volta a `/app/fila`
sem `POST`.

Sucesso: volta a `/app/fila` e dispara o `GET`. Se a reserva não
está nos itens, aviso de que foi gravada e só entra na fila no dia
da entrada.

---

## O que não aparece

- Confirmar saída
- Abrir/editar ficha
- Editar textos de boas-vindas
- Campo e-mail
- Lista de outro hotel
- Destino `fila` / `reserva` para staff ou gestão (casca já redireciona)
