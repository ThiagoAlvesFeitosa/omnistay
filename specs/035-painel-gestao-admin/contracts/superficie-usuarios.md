# Contrato: superfície — Usuários

Destino `/app/usuarios`. Título **Usuários**. Só gestão.
Computador. Sem `compacto`.

`GET /usuarios` ao montar. POST e DELETE só pelos botões
rotulados.

---

## Lista

Colunas: nome, e-mail, perfil (rótulo recepção / equipe /
gestão), situação (ativo / desativado). Sem senha.

Contagem visível de ativos e desativados derivada do array, sem
inventar.

Linha da sessão atual: legenda **você**; **sem** Desativar.

Linha ativa de outra pessoa: **Desativar**.

Linha desativada: **sem** Reativar, **sem** apagar.

---

## Novo usuário

Campos: nome, e-mail, perfil (os três), senha. Um confirmar.

`201` → GET da lista. `409` / `422` → `detail` visível; lista
anterior intacta.

---

## O que não aparece

Revogar sessão. Listar dispositivos. Trocar senha de existente.
Reativar.

---

## Vazio e falha

Lista vazia (só o próprio bootstrap, se a API devolver um item,
não é vazio) vs GET 5xx. Zeros de indicador não se aplicam aqui.
