# Fase 0 — Pesquisa e decisões técnicas: catálogo, vendáveis e recado

Cada seção registra a decisão, por que ela foi tomada e o que foi recusado.
Divergências documentais estão na última seção.

---

## 1. Nenhuma rota nova; oito operações já entregues

**Decisão**: as telas consomem só o que já existe:

| Ação na tela | Rota existente | Operação |
| --- | --- | --- |
| Listar fatos (ativos e inativos) | `GET /catalogo` | `ler_catalogo` |
| Criar fato | `POST /catalogo` | `alterar_catalogo` |
| Editar / desativar / reativar fato | `PATCH /catalogo/{id}` | `alterar_catalogo` |
| Listar itens vendáveis | `GET /itens-vendaveis` | `ler_catalogo` |
| Criar item vendável | `POST /itens-vendaveis` | `alterar_catalogo` |
| Editar preço/nome / desativar / reativar | `PATCH /itens-vendaveis/{id}` | `alterar_catalogo` |
| Ler recado | `GET /propriedade/boas-vindas` | `ler_texto_de_boas_vindas` |
| Gravar recado (quatro campos) | `PUT /propriedade/boas-vindas` | `alterar_texto_de_boas_vindas` |

Zero operação nova na matriz. Zero revisão Alembic. Cookie
`omnistay_sessao` via `pedirAutenticado`. A tela **não** envia
`id_hotel`. **Não** chama `GET /catalogo/ativo` (é a fonte do
atendimento, não a manutenção). **Não** há `DELETE`.

**Rationale**: spec reusa F2.1, F3.7 e F7.3. Artigo XI. Restrição
de não alterar o comportamento já entregue fora das telas.

**Alternativas consideradas**:

- **`GET /catalogo/ativo` na tela**: omite inativos; a manutenção
  precisa vê-los para reativar. Recusado.
- **Query `?categoria=`**: a API não tem. Filtrar no cliente a
  partir do array. Recusado inventar query.
- **Campo `descricao` em item vendável**: o JSON tem `nome`,
  `preco_atual`, `ativo`, `atualizado_em`. Recusado (Artigo XI).
- **WebSocket / recarga periódica**: sem peça nova. Recarregar,
  “tentar de novo” e o GET depois do POST/PATCH/PUT bastam.

---

## 2. Três telas; gestão lê; staff nem monta

**Decisão**:

| Destino F8.1 | Componente | Perfis |
| --- | --- | --- |
| `/app/catalogo` | `TelaCatalogo` | recepção (edita), gestão (lê) |
| `/app/vendaveis` | `TelaVendaveis` | recepção (edita), gestão (lê) |
| `/app/boas-vindas` | `TelaBoasVindas` | recepção (edita), gestão (lê) |

`destinos.ts`: os três passam a `perfis: ["recepcao", "gestor"]`.
A casca monta o componente e passa `somenteLeitura` quando o
perfil é `gestor`. Staff permanece fora; redireciona à casa;
**zero** fetch destas rotas.

Funções puras em `catalogo.ts` (chaves das cinco categorias,
rótulos, filtro da aba, contagem ativo/desativado) e `vendaveis.ts`
(tipo, formatação visível do preço). Sem Redux, sem React Query.

**Rationale**: FR-019–FR-021. “Gestão apenas lê” só é alcançável se
a gestão vir o destino. Não é F8.7.

**Alternativas consideradas**:

- **Um componente só para os três destinos**: mistura fato, preço e
  recado. Rejeitado.
- **Gestão só pela API /docs**: contradiz o critério da spec.
  Rejeitado.
- **Mostrar botões e deixar o `403` ensinar**: a spec manda não
  oferecer o que a autorização recusa. Rejeitado.

---

## 3. Abas de categoria no cliente; criação herda a aba

**Decisão**: `GET /catalogo` devolve todos os itens, ordem
`categoria` + `id`. A tela mostra cinco abas com rótulos de
negócio:

| Chave da API | Rótulo |
| --- | --- |
| `horario` | Horários |
| `cardapio` | Cardápio |
| `servico` | Serviços |
| `programacao` | Programação |
| `regra` | Regras |

A lista visível é o filtro da aba. Contagem ativo/desativado é da
aba (ou da lista apresentada), derivada do array, sem inventar.

**+ Novo item** envia `categoria` igual à aba visível, mais título
e conteúdo. **Editar** manda só `titulo` e/ou `conteudo` — nunca
`categoria`. **Desativar** / **Reativar** mandam só `ativo`.

Linha ativa: **Editar** e **Desativar**. Linha desativada:
**Reativar**. Sem apagar.

**Rationale**: FR-001–FR-006, wireframe de abas, contrato F2.1
(categoria imutável no PATCH).

**Alternativas consideradas**:

- **Cinco GETs**: a API não recorta. Rejeitado.
- **Trocar categoria na edição**: a API recusa `categoria` no
  PATCH. Rejeitado.

---

## 4. Preço é campo próprio; sem descrição

**Decisão**: Itens vendáveis lista `nome`, `preco_atual` (campo
numérico visível, separado do nome) e situação. Cadastro e edição
têm dois campos: nome e preço. Alterar só o preço manda
`{ "preco_atual": … }` sem reenviar o nome, e vice-versa.

`atualizado_em` não precisa ser coluna visível.

Desativar / reativar: `PATCH` com `ativo`. Nome duplicado entre
ativos: `409` visível ao salvar; o item permanece como estava.

**Rationale**: FR-007–FR-011, SC-006. Recurso existente não tem
descrição.

**Alternativas consideradas**:

- **Preço no mesmo input do nome**: viola o critério. Rejeitado.
- **Coluna descrição do rascunho**: exigiria backend. Recusado.

---

## 5. Recado: um PUT atômico; formato é da API

**Decisão**: a tela mostra quatro campos rotulados — café, wi-fi,
horário de saída, convite — ligados a `cafe`, `wifi`, `checkout`,
`convite`. Um **Salvar** manda os quatro. `200` substitui o estado
pelo corpo (já com `strip`). `422` mostra o `detail` da API (string
em português, sem ecoar o valor) e **não** altera os valores
anteriores já lidos.

A tela **não** reimplementa a regra de quebra de linha, tabulação
ou cinco espaços. Quatro espaços seguidos passam se a API passar.

Salvar **não** dispara chegada, worker nem mensagem. Aviso de
assistente virtual não aparece como campo.

**Rationale**: FR-012–FR-016, contrato F7.3, FR-015.

**Alternativas consideradas**:

- **Validar formato no cliente**: risco de divergir da API
  (FR-015). Rejeitado como fonte da verdade; o `422` basta.
- **Prévia com nome de hóspede**: inventa mensagem. Recusado na
  spec.
- **PUT só do campo sujo**: a API exige os quatro. Rejeitado.

---

## 6. Depois de gravar, `GET` — não recarregar a página

**Decisão**:

| Escrita 2xx | Em seguida |
| --- | --- |
| POST/PATCH catálogo ou vendável | `GET` da lista correspondente e substituir `itens` |
| PUT boas-vindas | usar o corpo `200` (já é o gravado); GET extra não é obrigatório |

Falha de GET inicial: painel permanece, declara que não carregou,
**Tentar de novo**. **Não** é `itens: []`. `200` com `itens: []` é
lista vazia honesta.

POST/PATCH/PUT rede/5xx: o estado anterior permanece; aviso; o
botão volta a aceitar clique. Zero recado ao hóspede afirmado pela
tela.

`409` (nome vendável duplicado) e `422`: motivo visível; sem
afirmar gravado.

Enquanto a escrita daquele alvo não conclui, o botão daquele alvo
fica indisponível.

**Rationale**: FR-017, FR-018. Igual à F8.2–F8.5.

**Alternativas consideradas**:

- **Optimistic insert**: se o POST falhar, o fato “existe” na tela
  (Artigo V invertido). Rejeitado.
- **`window.location.reload`**: pede a tela de novo. Rejeitado.

---

## 7. Proxy Vite para `/itens-vendaveis`

**Decisão**: acrescentar `"/itens-vendaveis": api` em
`frontend/vite.config.ts`, no mesmo molde de `/catalogo`. Sem isso
o `npm run dev` não alcança a API de itens vendáveis.

Não é rota nova no FastAPI. Não muda `base: "/app/"`.

**Rationale**: o proxy atual lista `/catalogo` e `/propriedade`,
não `/itens-vendaveis`. Problema presente só nesta fatia.

**Alternativas consideradas**:

- **Chamar `/propriedade/itens-vendaveis`**: a API é
  `/itens-vendaveis`. Rejeitado.
- **Proxy coringa `/`**: amplo demais. Rejeitado.

---

## 8. Testes da casca e mock das três leituras

**Decisão**: ao nascerem as telas, o `fetch` falso da casca
responde no mínimo:

- `GET /catalogo` → `{ itens: [] }`
- `GET /itens-vendaveis` → `{ itens: [] }`
- `GET /propriedade/boas-vindas` → quatro strings (ou o `200` real
  do hotel de teste)

Staff em `/app/catalogo`, `/app/vendaveis`, `/app/boas-vindas`: a
casca **não** monta a tela e **não** dispara esses GET nem
POST/PATCH/PUT.

Gestão: monta, dispara o GET, **não** oferece criar/editar/
desativar/salvar e **não** dispara escrita.

O teste “recepção em /catalogo vê só o título Catálogo” deixa de
valer: passa a haver lista ou estado vazio honesto.

**Rationale**: mesmo ponto da F8.2–F8.5, invertido para a gestão
(aqui ela lê).

---

## Divergências documentais

O mapa `docs/wireframes-painel.html` (telas `catalogo`, `vendaveis`,
`boasvindas`) mostra coluna **Descrição** no item vendável e uma
prévia do recado com nome de hóspede (“Olá, Marina!”). O contrato
F2.2 em `specs/009-confirmar-chegada/contracts/api-de-chegada.md`
ainda descreve GET/PUT de **três** campos; o vigente é o de F7.3
(`convite` obrigatório).

Isso **não** será entregue: sem `descricao` no JSON; sem prévia com
nome; quatro campos. Corrigir o mapa e o contrato antigo da F2.2 é
trabalho documental posterior — não bloqueia implementar. Não
contornar em silêncio: a spec e o contrato F7.3 vencem o rascunho.

`Casca.test.tsx` documenta catálogo como tela nomeada. Esta fatia
substitui essa asserção.

`destinos-por-perfil.md` da F8.1 lista os três destinos só para
recepção. Esta fatia atualiza o mapa **no código** (`destinos.ts`)
e registra o delta em
[contracts/destinos-e-perfis.md](./contracts/destinos-e-perfis.md);
não reabre a spec da F8.1.
