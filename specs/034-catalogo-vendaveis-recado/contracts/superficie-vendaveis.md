# Contrato: superfície — Itens vendáveis

Fonte: `TelaVendaveis` em `/app/vendaveis`.
Gestão: leitura. Recepção: cadastro, preço próprio, desativar.
Staff: casca redireciona.

Recepção e gestão no computador. Sem layout de mão.

---

## Itens vendáveis (`/app/vendaveis`)

Título **Itens vendáveis**.

**Lista** — uma linha por item do GET (ativos e desativados). Por
linha, visíveis:

- nome
- preço atual em campo/coluna **própria** (não embutido no nome)
- situação distinguível
- recepção, linha ativa: **Editar**, **Desativar**
- recepção, linha desativada: **Reativar**

**Não visíveis:** descrição (o recurso não tem), apagar,
`atualizado_em` como coluna obrigatória, “extrato”, “conta”.

**+ Novo item** (só recepção): nome e preço, dois campos. Preço
zero é válido.

**Editar** (só recepção, linha ativa): nome e preço separados.
Salvar só o preço **não** exige reescrever o nome.

Clique no texto da linha **não** grava.

`409` (nome ativo duplicado, inclusive ao reativar): aviso na
tela; estado anterior permanece.

**Lista vazia** (`200` + `itens: []`): texto de que não há item
vendável. Sem botão órfão de editar.

**Falha de leitura**: igual ao Catálogo — painel permanece, não é
vazio, **Tentar de novo**.

**Carregando**: título visível; não fingir lista vazia até o `200`.

---

## O que não aparece

- Catálogo de fatos (destino à parte)
- Lançar / dispensar consumo (F8.5)
- Campo descrição do rascunho de telas
- Destino para staff
