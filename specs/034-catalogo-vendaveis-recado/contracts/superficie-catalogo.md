# Contrato: superfície — Catálogo

Fonte: `TelaCatalogo` em `/app/catalogo`.
A casca permanece: menu, sair, recusa de destino alheio.

Recepção e gestão no computador. Sem layout de mão. Gestão:
`somenteLeitura` — vê a lista, não vê criar/editar/desativar/
reativar.

---

## Catálogo (`/app/catalogo`)

Título **Catálogo** (já era o do destino).

**Abas** — Horários, Cardápio, Serviços, Programação, Regras
(chaves `horario`, `cardapio`, `servico`, `programacao`, `regra`).
Uma visível por vez. Trocar aba não dispara GET novo.

**Resumo da aba** — com `200` e lista lida: quantos ativos e
quantos desativados **na aba visível**, derivados do array.

**Lista** — itens da aba, na ordem residual da API. Por linha:

- título
- conteúdo
- situação distinguível (ativo / desativado)
- recepção, linha ativa: **Editar**, **Desativar**
- recepção, linha desativada: **Reativar**

**Não visíveis:** apagar, trocar categoria, identificador como
rótulo de pessoa.

**+ Novo item** (só recepção): título e conteúdo; a categoria é a
da aba. Item novo aparece ativo na mesma aba após o GET.

Clique no texto da linha **não** grava. Só os botões.

Enquanto o POST/PATCH daquele alvo não volta, o botão acionado
não aceita segundo clique.

**Lista vazia da aba** (`200` e filtro vazio): texto de que não há
item nesta categoria. Não é página em branco. Distinto de “a casa
não tem catálogo” se outras abas tiverem item — a pessoa troca a
aba. Casa inteira vazia: vazio em todas as abas, honesto.

**Falha de leitura** (rede, 5xx, corpo ilegível): o painel (menu,
título) permanece. Declara que não carregou. **Tentar de novo**.
**Não** usa o estado de lista vazia. **Não** manda à entrada (isso
é só 401).

**Carregando**: título visível; não mostrar contagem zero como se
a casa não tivesse fatos até chegar o `200`.

---

## O que não aparece

- `GET /catalogo/ativo`
- Personalidade da assistente
- Itens vendáveis (destino à parte)
- Recado de boas-vindas (destino à parte)
- Destino para staff (casca redireciona)
