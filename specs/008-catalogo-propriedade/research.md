# Fase 0 — Pesquisa e decisões técnicas: Catálogo da Propriedade

Cada seção registra a decisão, por que ela foi tomada e o que foi rejeitado. As
divergências documentais encontradas no caminho estão na seção 9.

`/speckit-clarify` começou e o planejamento seguiu sem responder a fila. A spec já
fechava preço por adiamento; o restante (categoria imutável, escrita concorrente) é
decidido aqui, com default alinhado à spec e ao Artigo XI.

---

## 1. Sem migração: a tabela já é o modelo

**Decisão**: esta fatia **não** gera revisão Alembic nem altera `docs/04-schema.sql`.
`catalogo_item` (F0.2 / `0001`) já tem `id_hotel`, `categoria` com `CHECK` das cinco
chaves, `titulo`, `conteudo`, `ativo DEFAULT TRUE` e `atualizado_em`. O índice parcial
`(id_hotel, categoria) WHERE ativo` já cobre a consulta do catálogo ativo.

A aplicação, no `UPDATE`, grava `atualizado_em = now()`. Não há trigger; o caminho
normal passa pelo serviço.

**Rationale**: Artigo XI. Preço estruturado ficou fora da spec; não há coluna nova a
justificar revisão. Inventar migração vazia só para “ter número de fatia” corrompe o
histórico do Alembic.

**Alternativas consideradas**:

- **Tabela de item vendável + preço agora**: rejeitada pela spec (FR-019) e pelo Artigo
  XI — cobrança não tem consumidor até a F3.7.
- **Trigger de `atualizado_em`**: garantia extra para `UPDATE` direto no banco; o MVP só
  escreve pelo serviço. Adiado.

---

## 2. Superfície: API autenticada, sem tela React

**Decisão**: quatro rotas HTTP no módulo `propriedade`. Critério de pronto é
comportamento observável por API e suíte, não o protótipo React.

**Rationale**: mesmo padrão da F1.1–F1.4. A spec já tirou a tela do critério de pronto.

**Alternativas consideradas**:

- **API + tela de manutenção nesta fatia**: dobra o ciclo TDD e compete com o contrato
  que a F2.2 precisa. Rejeitado.
- **Só repositório, sem rota**: deixaria `alterar_catalogo` / `ler_catalogo` sem
  exercício HTTP — o mesmo buraco que a F0.3 pediu para fechar na primeira fatia de
  domínio correspondente.

---

## 3. SQL no módulo `propriedade`; porta só para quem não é dono da tabela

**Decisão**:

| Camada | Papel |
| --- | --- |
| `propriedade.repository` | Único SQL em `catalogo_item` (inserir, atualizar, listar manutenção, listar ativos) |
| `propriedade.service` | Regras: trim, categoria válida, título ≤ 160, categoria imutável, log sem texto do fato |
| `propriedade.router` | HTTP; `id_hotel` só da sessão |
| `portas/catalogo.py` | Protocolo `CatalogoRepository.listar_ativos(id_hotel)` |
| `adaptadores/catalogo_falso.py` | Suíte de quem consome a porta (F2.2 / F3.3) |
| `adaptadores/catalogo_banco.py` | Implementação que recebe a **mesma** `Connection` da transação e delega ao repositório |

A porta **não** abre conexão própria: uma segunda conexão não veria escritas ainda não
commitadas do worker. HTTP de manutenção **não** passa pela porta — o módulo dono usa o
repositório. F2.2 e F3.3 injetam `CatalogoBanco(conexao)` ou `CatalogoFalso`.

Nome do arquivo: `app/portas/catalogo.py`, no padrão de `llm.py` e `mensageria.py`, não
o `catalogo_repository.py` do Artefato 5 (seção 9).

**Rationale**: Artigo X (consulta ativa isolada para o atendimento futuro) + fronteira de
módulo (só `propriedade` toca a tabela) + Artigo III (uma transação, uma conexão).

**Alternativas consideradas**:

- **SQL da consulta ativa no adaptador, separado do repositório**: dois `SELECT` da mesma
  tabela para manter. Rejeitado.
- **Não criar a porta nesta fatia**: a F2.2 inventaria o contrato sob pressão do pacote
  de boas-vindas. FR-010 *é* essa consulta; a porta nasce com o dono do dado.
- **Porta com engine interno**: snapshot errado no worker. Rejeitado.

---

## 4. `ler_catalogo` na matriz; gestão lê e não escreve

**Decisão**: operação nova `ler_catalogo` para `recepcao` e `gestor`. `alterar_catalogo`
permanece só `recepcao`. `staff` recusado nas duas.

GET `/catalogo` e GET `/catalogo/ativo` exigem `ler_catalogo`. POST e PATCH exigem
`alterar_catalogo`. Alvo de outro hotel → `404`, sem confirmar existência.

**Rationale**: a spec (FR-015, FR-016) e a F0.3 (“gestão consulta, não altera”). A matriz
antiga só tinha escrita; leitura sem operação própria faria a gestão cair em 403 no GET
ou forçaria GET a usar `alterar_catalogo` — os dois estão errados.

**Alternativas consideradas**:

- **Reusar `ler_indicadores` para o GET**: indicadores são agregados; catálogo é conteúdo
  da propriedade. Misturaria significados.
- **Gestão também altera**: a política da F0.3 disse revisitável; a spec confirmou que
  não. Mantido.

---

## 5. Categoria imutável; PATCH único para texto e ativo

**Decisão**: depois de criado, o item não muda de categoria. PATCH aceita `titulo`,
`conteudo` e/ou `ativo` (pelo menos um). Enviar `categoria` → `422`. Não existe `DELETE`.

Chaves canônicas (iguais ao `CHECK`): `horario`, `cardapio`, `servico`, `programacao`,
`regra`. A spec fala em português; a API e o banco usam essas chaves.

**Rationale**: FR-005 lista título e conteúdo, não categoria. Recategorizar é criar outro
item e desativar o antigo — dois fatos, não um editado. Um PATCH só (Artigo XI) cobre
editar, desativar e reativar.

**Alternativas consideradas**:

- **Permitir trocar categoria**: a spec não pede; testes e histórico ficam ambíguos
  (“o café era horário ou cardápio?”).
- **POST `/desativar` e `/reativar` separados**: mais rotas para o mesmo bit.
- **DELETE lógico via HTTP DELETE**: a spec proíbe remoção permanente; `405` deixa isso
  explícito.

---

## 6. Consulta ativa agrupada; manutenção plana

**Decisão**:

- **Manutenção** `GET /catalogo`: lista plana, ativos e inativos, com `ativo`, ordenada
  por `categoria`, depois `id_catalogo_item`.
- **Ativo** `GET /catalogo/ativo`: objeto com as **cinco** chaves sempre presentes;
  arrays vazios quando não há item. Só ativos. Dentro de cada categoria, ordem por id.

Catálogo vazio da instalação = cinco arrays vazios, HTTP 200 — não é erro.

**Rationale**: FR-010 pede “completo” e “organizado por categoria”; F2.2 não deve
adivinhar se uma chave ausente significa “sem fatos” ou “esqueci a categoria”. A
manutenção precisa dos inativos para reativar.

**Alternativas consideradas**:

- **Um único GET com query `somente_ativos`**: a spec trata duas consultas; duas rotas
  deixam o contrato da F2.2 estável.
- **Omitir categoria vazia no JSON**: F2.2 teria de lidar com chave faltando.

---

## 7. Título duplicado permitido; último PATCH vence

**Decisão**: sem unicidade de `(id_hotel, categoria, titulo)`. Dois “Café da manhã”
coexistem; a recepção distingue pelo identificador. Dois PATCH simultâneos: o último
`UPDATE ... WHERE id_catalogo_item AND id_hotel` vence. Sem coluna de versão.

**Rationale**: spec (edge case) + Artigo XI. Hotel de uma recepção não justifica lock
otimista nesta fatia.

---

## 8. Validação na borda; `CHECK` continua no banco

**Decisão**: trim em título e conteúdo; vazio após trim → `422`; categoria fora das
cinco → `422` **antes** do banco; título > 160 → `422` (limite já do `VARCHAR`). O
`CHECK` permanece a garantia contra script e SQL direto (Artigo IX). Teste de
repositório pode exercitar o `CHECK`; o caminho HTTP não depende dele para a mensagem
clara.

Log: `id_catalogo_item`, `id_hotel`, `categoria`, ação. Sem `titulo`/`conteudo` como
campo principal (FR-018).

**Rationale**: recusa compreensível na borda; banco não é a UX.

---

## 9. Divergências documentais

| Onde | O que está escrito | O que esta fatia faz |
| --- | --- | --- |
| `docs/00-ESTADO-DO-PROJETO.md` | Fechar desenho catálogo+preços antes da F2.1 | Spec adia preço para F3.7; na implementação, marcar a pendência como adiada — não silenciar |
| Artefato 5 pasta `portas/` | `catalogo_repository.py` | `app/portas/catalogo.py`, alinhado a `llm.py` / `mensageria.py` |
| Artefato 5 | `CatalogoRepository` carrega o catálogo no prompt | Esta fatia entrega a **consulta**. Montar prompt é F3.3; boas-vindas são F2.2 |
| Matriz F0.3 | Só `alterar_catalogo` | Acrescenta `ler_catalogo` para a gestão consultar |
| Clarify | Fila de perguntas aberta | Planejamento seguiu; preço = spec; categoria imutável e PATCH único = esta pesquisa |
