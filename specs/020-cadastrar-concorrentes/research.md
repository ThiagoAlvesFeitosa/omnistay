# Fase 0 — Pesquisa e decisões técnicas: Cadastro de Concorrentes

Cada seção registra a decisão, por que ela foi tomada e o que foi recusado.
Divergências documentais estão na seção 10.

---

## 1. Tabela já existe; a revisão só garante o que a spec exige e o `0001` não tem

**Decisão**: reusar `concorrente` da revisão `0001` (`id_concorrente`, `id_hotel`,
`nome`, `url_fonte`, `ativo DEFAULT TRUE`, `criado_em`). **Não** criar tabela,
**não** acrescentar `atualizado_em`, **não** tocar `coleta_mercado`.

Revisão `0019_cadastrar_concorrentes` (SQL congelado em
`alembic/versions/sql/`) acrescenta só o que a spec precisa e o esquema inicial
não entrega:

| Artefato | Papel |
| --- | --- |
| `uq_concorrente_hotel_fonte` | `UNIQUE (id_hotel, lower(btrim(url_fonte)))` — **completo**, não parcial. Fonte desativada continua ocupando o endereço |
| `ck_concorrente_url_fonte` | `url_fonte` casa `^https?://[^[:space:]]+$` — recusa texto solto, e-mail e espaço no meio contra SQL direto |
| `ix_concorrente_hotel_ativo` | `(id_hotel) WHERE ativo` — consulta de fontes ativas (FR-011) e gancho da F5.2 |

`docs/04-schema.sql` recebe os três. A cópia congelada `0001` **não** muda.

**Rationale**: Artigo IX (unicidade e domínio no banco, não só na aplicação) +
Artigo XI (sem coluna de auditoria que a spec não pede; `item_vendavel` tem
`atualizado_em` porque o preço vigente muda com frequência; aqui o rastro útil
é a ficha que não se apaga). Índice parcial de ativos é o mesmo padrão de
`item_vendavel`, barato, e evita a F5.2 varrer inativos.

**Alternativas consideradas**:

- **Índice único parcial `WHERE ativo`**: rejeitado pela spec — desativado
  continua a ocupar a fonte; o caminho é reativar, não duplicar ficha.
- **Extensão `citext`**: biblioteca/extensão nova sem problema que
  `lower(btrim(...))` não resolva.
- **Coluna gerada `url_fonte_normalizada`**: índice por expressão basta; coluna
  extra é terceira descrição do mesmo endereço.
- **Migração vazia “para ter número”**: corrompe o Alembic. Sem unicidade no
  banco, duas gestões simultâneas criariam a mesma fonte duas vezes.
- **Não ter `CHECK` de URL**: o domínio “endereço da web” cairia só na
  aplicação; script de correção gravaria `mailto:` e a F5.2 herdaria lixo.

---

## 2. Módulo `mercado` nasce nesta fatia; SQL só nele

**Decisão**: `app/modulos/mercado/` (router, schema, service, repository) governa
`concorrente`. `app/main.py` inclui o roteador. Nenhum outro módulo lê ou
escreve essa tabela.

HTTP de manutenção usa `mercado.repository`. **Não** nasce porta hexagonal:
o único consumidor futuro da lista de fontes ativas é a coleta (F5.2), no
**mesmo** módulo. O contrato interno é `listar_fontes_ativas(id_hotel)` no
serviço/repositório — documentado para a F5.2 não reinventar o filtro.

**Rationale**: Artefato 5 já reserva `mercado` a `concorrente` e
`coleta_mercado`. Fronteira de módulo (só o dono toca a tabela) + Artigo XI
(porta sem segundo módulo consumidor é abstração antecipada). O catálogo teve
porta porque `conversa` não é `propriedade`. Aqui não há esse cruzamento.

**Alternativas consideradas**:

- **CRUD em `propriedade`**: mistura fatos da casa com estratégia de mercado;
  a gestão escreveria numa área que a recepção já opera. Rejeitado.
- **Porta `FontesAtivas` + falso nesta fatia**: zero consumidor fora de
  `mercado`; o falso nasceria sem teste que o exija. Extraída na F5.2 só se
  outro módulo precisar ler.
- **Worker nesta fatia**: a spec proíbe visitar a fonte. Sem coleta, sem
  agendador, sem tipo novo em `trabalho`.

---

## 3. Superfície: API autenticada, sem tela React, sem visita à fonte

**Decisão**: quatro comportamentos HTTP no módulo `mercado`. Critério de pronto
é suíte + API, no padrão F1.1–F4.2. Nenhum cliente HTTP de saída no módulo
(sem `httpx`, sem `urllib.request` para a fonte). `coleta_mercado` permanece
intocada: teste de integração confirma que o cadastro não insere linha lá.

**Rationale**: spec (FR-012, SC-010) e Artigo XI. Tela React compete com o
contrato que a F5.2 precisa.

**Alternativas consideradas**:

- **API + tela de manutenção**: dobra o ciclo TDD. Rejeitado.
- **Só repositório, sem rota**: deixaria as operações novas sem exercício
  HTTP — o buraco que a F0.3 pediu para fechar.
- **HEAD/GET na fonte “para validar” o endereço**: visita a fonte, gasta rede
  e falha por motivo alheio ao cadastro. A spec recusa.

---

## 4. Só a gestão lê e escreve; duas operações novas na matriz

**Decisão**:

| Operação | `recepcao` | `staff` | `gestor` | Rotas |
| --- | :---: | :---: | :---: | --- |
| `alterar_concorrentes` | ❌ | ❌ | ✅ | `POST /concorrentes`, `PATCH /concorrentes/{id}` |
| `ler_concorrentes` | ❌ | ❌ | ✅ | `GET /concorrentes`, `GET /concorrentes/ativos` |

Não reusar `ler_indicadores` (agregado, recepção também lê) nem
`administrar_usuario` (não é concorrente). Não reusar `alterar_catalogo` (é da
recepção e é fato da casa).

Alvo de outro hotel ou id inexistente → `404`, sem confirmar existência.
Perfil sem permissão → `403`. Sem sessão → `401`.

**Rationale**: spec FR-014/FR-015. Inteligência de mercado é processo da gestão
(Artefato 2 §5.2). A FR-019 da F0.3 lista reserva, hóspede, solicitação,
consumo e avaliação — não concorrente. “Somente leitura” do Artefato 5 §11.2
vale para **painel de preços coletados** (F5.3), não para dizer quem
acompanhar. Sem operação de leitura própria, o GET reusaria escrita ou a
recepção cairia num `ler_*` largo demais.

**Alternativas consideradas**:

- **Recepção escreve, gestão lê** (espelho do catálogo): o balcão não define
  estratégia de preço; a spec já fechou gestão como autora.
- **Uma operação só (`manter_concorrentes`)**: funcionaria porque o perfil é
  o mesmo; duas operações deixam a F5.3 recusar escrita de **coleta** sem
  apagar a leitura da lista, e seguem o padrão de todos os recursos.
- **Gestão e recepção leem**: a spec recusa a recepção na leitura. Lista de
  fontes não é fila do dia.

---

## 5. URL válida na aplicação; unicidade no banco; PATCH único

**Decisão**:

Validação de endereço (serviço, após trim): `urllib.parse.urlparse` da
biblioteca padrão. Exige esquema `http` ou `https`, anfitrião não vazio, **sem**
usuário nem senha na URL. Recusa `mailto:`, caminho relativo, texto solto.
Comprimento: nome 1–120, URL 1–400, no espelho do `VARCHAR`. Nome duplicado é
permitido.

Unicidade: mesma propriedade não tem dois `lower(btrim(url_fonte))`. Colisão
na criação ou no PATCH → `409` (mesmo código de nome ativo duplicado em
`item_vendavel`). A aplicação recusa com mensagem clara; o índice único
protege duas escritas simultâneas.

PATCH aceita `nome`, `url_fonte` e/ou `ativo` (pelo menos um). Não existe
`DELETE` (`405`). Desativar = `"ativo": false`; reativar = `"ativo": true`.
Edição de inativo é permitida; ele permanece inativo até reativar.

**Rationale**: FR-003/FR-009 + Artigo IX + um PATCH só (Artigo XI), igual ao
catálogo. Credencial na URL não é fonte pública e vaza segredo no banco.
`409` distingue “já existe” de “formato inválido” (`422`).

**Alternativas consideradas**:

- **Normalizar barra final / `www.` / query**: a spec só iguala maiúsculas e
  espaços nas pontas. Normalizar demais fundiria fontes distintas.
- **POST `/desativar` separado**: mais rota para o mesmo bit.
- **`DELETE` lógico via HTTP DELETE**: a spec proíbe remoção permanente; `405`
  deixa isso explícito.
- **`requests`/`httpx` para “ver se abre”**: visita a fonte. Rejeitado.

---

## 6. Duas consultas: manutenção plana e fontes ativas

**Decisão**:

- **Manutenção** `GET /concorrentes`: lista plana, ativos **e** inativos, com
  `ativo`, ordem `nome`, depois `id_concorrente`.
- **Fontes ativas** `GET /concorrentes/ativos`: só `ativo = true`; cada item
  traz identificador, nome e endereço; **sem** campo `ativo` (todos são
  ativos). Hotel sem ativo: `"fontes": []`, HTTP 200 — não é erro.

A lista de fontes ativas **é** o contrato da F5.2. Esta fatia não dispara
coleta.

**Rationale**: FR-010 e FR-011. Duas rotas deixam o contrato da coleta estável
(espelho `GET /catalogo` vs `/catalogo/ativo`). Um query-param
`somente_ativos` misturaria as duas e a F5.2 teria de adivinhar o default.

**Alternativas consideradas**:

- **Um GET com `?ativos=true`**: a spec trata duas consultas; a coleta não
  pode herdar um default errado.
- **Omitir a rota de ativos e filtrar na F5.2**: a spec exige a consulta nesta
  fatia precisamente para “fonte desativada não é consultada” ser testável
  agora.

---

## 7. Log sem nome e sem endereço da fonte

**Decisão**: `logger.info` com `id_concorrente`, `id_hotel` e ação (`criar`,
`editar`, `desativar`, `reativar`). Se o PATCH só muda `ativo` para falso →
`desativar`; só para verdadeiro → `reativar`; demais escritas de PATCH →
`editar`. Nome e `url_fonte` **não** são campo do log.

**Rationale**: FR-017 e Artigo VIII (conteúdo de mensagem nunca; aqui não há
mensagem de hóspede, mas a spec pede que nome e endereço não sejam o conteúdo
principal). Identificador basta para rastrear manutenção.

**Alternativas consideradas**:

- **Logar a URL**: útil em suporte, mas a spec manda o contrário; F5.2 poderá
  logar identificador da fonte na coleta, nunca o HTML.

---

## 8. Sem semeadura, sem periodicidade, sem ToS automático

**Decisão**: bootstrap **não** cria concorrente de exemplo. Periodicidade da
coleta já vive em `parametro_hotel` e será lida na F5.2. Termos de uso não são
examinados pelo sistema nesta fatia: quem cadastra escolhe fonte pública.

**Rationale**: spec Assumptions + Artigo XV. Prometer verificação automática
de contrato de terceiro nesta fatia seria superpromessa.

---

## 9. Garantia no banco vs recusa na borda

**Decisão**: caminho HTTP valida e devolve `422`/`409` compreensível. Testes
de `test_garantias_do_banco.py` exercitam `uq_concorrente_hotel_fonte` (segundo
insert com a mesma fonte, inclusive inativa, e com diferença só de maiúscula)
e `ck_concorrente_url_fonte` (texto que não é `http(s)://...`). Dois hotéis
com a mesma URL: os dois inserts passam.

**Rationale**: Artigo IX. Recusa na UX não substitui o índice.

---

## 10. Divergências documentais

| Onde | O que está escrito | O que esta fatia faz |
| --- | --- | --- |
| Artefato 5 §11.2 | Gestor: painéis de mercado, “somente leitura” | Gestão **escreve** a lista de concorrentes (spec). “Somente leitura” permanece para preço/avaliação coletados (F5.3). Na implementação, registrar em `docs/00-ESTADO-DO-PROJETO.md` — não silenciar |
| Artefato 5 pasta `mercado/` | Módulo previsto, pasta ausente no código | Esta fatia cria o módulo |
| `docs/04-schema.sql` / `0001` | `concorrente` sem unicidade de fonte e sem CHECK de URL | Revisão `0019` + documento vivo; `0001` congelado |
| Pendência “cadastrar lista **e** verificar termos de uso” | Um item só nos artefatos 4 e 5 | Cadastro nesta fatia; verificação de termos continua humana / F5.2 |
| Clarify | Não rodou | Planejamento usou a spec (gestão cadastra, duplicata de fonte recusada, sem visita) |
