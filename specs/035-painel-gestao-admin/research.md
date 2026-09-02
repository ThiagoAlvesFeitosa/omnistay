# Fase 0 — Pesquisa e decisões técnicas: painel da gestão

Cada seção registra a decisão, por que ela foi tomada e o que foi recusado.
Divergências documentais estão na última seção. Clarificações da spec
(2026-09-02) vencem o rascunho de telas.

---

## 1. Um GET de números puros; chegadas-do-dia intacto

**Decisão**: nascer `GET /indicadores` (operação já existente
`ler_indicadores`) com **quatro números** e **zero lista**:

| Campo JSON | Recorte |
| --- | --- |
| `chegadas_hoje` | A mesma contagem de `GET /indicadores/chegadas-do-dia` (reuso da função já entregue) |
| `hospedados` | `COUNT` de `reserva` com `status = 'hospedado'` no hotel da sessão |
| `chamados_abertos` | `COUNT` de `solicitacao` tipo `reclamacao` ou `servico` com status `aberta` ou `em_andamento` (via serviço de atendimento) |
| `consumo_a_lancar` | `SUM(valor_praticado)` de `consumo` com `status_lancamento = 'pendente'` no hotel; zero se não houver linha |

`GET /indicadores/chegadas-do-dia` **não muda** (FR-028). A tela
Painel **não** chama essa rota nem `GET /fila-do-dia`,
`GET /solicitacoes` ou `GET /consumos/pendentes`.

Rota no módulo `hospedagem` (já abriga `/indicadores/...`). Para
chamados e consumo, o serviço de hospedagem **chama o serviço de
atendimento** — não importa o repositório alheio.

**Rationale**: spec clarificada (quatro números; tickets sem
consumo; consumo em dinheiro). Artigo XI: um envelope, não três
rotas irmãs. Artigo VIII: a gestão não recebe lista para filtrar.

**Alternatives consideradas**:

- **Estender `GET /indicadores/chegadas-do-dia`**: mistura o
  contrato da F1.1 com três recortes novos. Recusado.
- **Reusar `GET /solicitacoes` / `GET /consumos/pendentes` na
  tela e contar no cliente**: serviria lista nominada à gestão.
  Recusado (FR-002, SC-002).
- **Operação nova `ler_painel_gestao`**: `ler_indicadores` já é
  “número, não pessoa” e já inclui gestão. Recusado.
- **Gráfico de 30 dias, fichas antecipadas, nota média**: fora
  na clarificação. Recusado.

---

## 2. Relação de usuários: GET novo; POST e DELETE reusados

**Decisão**:

| Ação na tela | Rota | Operação |
| --- | --- | --- |
| Listar (ativos e desativados) | `GET /usuarios` **(nova)** | `administrar_usuario` (já só gestão) |
| Criar | `POST /usuarios` | `administrar_usuario` |
| Desativar | `DELETE /usuarios/{id}` | `administrar_usuario` |

Lista: `id_usuario`, `nome`, `email`, `perfil`, `ativo`. **Sem**
`senha_hash`. Ordem: nome, depois id.

**Sem** `PATCH` de `ativo: true`. **Sem** controle de reativar.
E-mail de desativado continua único — criar de novo com o mesmo
endereço segue `409`.

A tela **não** chama `GET /sessoes` nem `DELETE /sessoes/{id}`.

Depois de POST 201 ou DELETE 204: `GET /usuarios` de novo, como
F8.2–F8.6. A linha da sessão autenticada não oferece Desativar
(FR-018); se o DELETE forçado voltar `409`, aviso e lista intacta.

**Rationale**: clarificação Q4. POST/DELETE já existem (F0.3). A
lista é o buraco presente. Artigo XI: não inventar reativação.

**Alternatives consideradas**:

- **Só POST/DELETE, lista montada no cliente a partir de criações
  da sessão**: some quem já existia. Recusado.
- **Reativar (`PATCH ativo`)** : fora na clarificação. Recusado.
- **Operação `ler_usuarios`**: a lista é administração, não
  consulta pública. Recusado.

---

## 3. Mercado: só o comparativo já entregue

**Decisão**: a tela consome:

| Ação | Rota | Operação |
| --- | --- | --- |
| Visão atual | `GET /mercado` | `ler_mercado` |
| Histórico de um concorrente | `GET /mercado/concorrentes/{id}` | `ler_mercado` |

Marca de falha / não-atual deriva de `situacao` e `ultima_falha`
já definidas na F5.3 (`so_falha`, `desatualizado` com
`ultima_falha`, `sem_coleta`, `cadencia_ausente`). A tela **não**
calcula variação percentual nem desenha a tarifa da casa.

**Zero** `POST|PATCH /concorrentes`. **Zero** disparo de coleta.

Clique na linha (não em “coletar”) dispara o GET de histórico;
falha no histórico ≠ apagar a visão atual.

**Rationale**: clarificação Q3. F5.3 já cobre FR-006–FR-011.

**Alternatives consideradas**:

- **Aba Concorrentes do rascunho (CRUD)**: fora. Recusado.
- **Linha “você” / % 7 dias**: contradiz Artigo I e F5.3.
  Recusado.

---

## 4. Retenção: GET existente + prazos no envelope

**Decisão**: `GET /retencao` (`ler_retencao`) continua a lista
`execucoes`. Esta fatia **acrescenta** no mesmo `200` os prazos
vigentes lidos de `parametro_hotel`:

- `meses_retencao_conteudo_livre`: inteiro ≥ 1 ou `null`
- `anos_retencao_ficha`: inteiro ≥ 1 ou `null`

Não inventar 12 nem 5 no cliente quando a chave falta (Artigo
XIII). Sem botão de disparo. Sem `POST /retencao/executar`.

Cada linha da tabela mostra data, espécies já gravadas
(mensagens, comentários, payloads, descrições, fichas) e
quantidades — inclusive zero. A tela **não** inventa tipo
“conversas” que some campos se isso esconder uma espécie.

**Rationale**: FR-020–FR-022. Um GET a menos do que uma rota só
de prazo. Campos novos são aditivos.

**Alternatives consideradas**:

- **GET novo só de prazo**: peça a mais. Recusado.
- **Números 12 e 5 fixos no React**: constante de produto no
  cliente. Recusado.
- **Botão expurgar agora**: F6.1 e spec proíbem. Recusado.

---

## 5. Quatro telas; recepção e staff nem montam

**Decisão**: destinos F8.1 já são só `gestor` para Painel,
Mercado, Usuários e Retenção. Esta fatia **não** mexe em
`perfis`. A casca deixa de montar `TelaNomeada` nesses quatro e
monta `TelaPainel`, `TelaMercado`, `TelaUsuarios`,
`TelaRetencao`. Sem `compacto`. Sem `somenteLeitura` de recepção
— estes destinos não são da recepção.

Recepção ou staff em `/app/indicadores` (etc.): `Navigate` à
casa; **zero** fetch destas rotas (mesmo padrão F8.2–F8.6).

Funções puras: `indicadores.ts` (tipos do envelope), `mercado.ts`
(rótulo de `situacao`, se a linha está marcada como falha / não
atual), `usuarios.ts` (rótulo de perfil), `retencao.ts` (se um
prazo é número válido). Sem Redux, sem React Query.

Proxy Vite **já** encaminha `/indicadores`, `/mercado`,
`/retencao`, `/usuarios`. Sem linha nova.

**Rationale**: FR-023–FR-026. Artigo XI: o problema presente é
título sozinho.

**Alternatives consideradas**:

- **Playwright**: a suíte do projeto não abre navegador. Recusado.
- **Um componente só para os quatro destinos**: mistura número,
  série, funcionário e comprovante. Recusado.

---

## 6. Depois de gravar, GET — não recarregar a página

**Decisão**: igual F8.2–F8.6.

| Escrita 2xx | Em seguida |
| --- | --- |
| POST usuário | `GET /usuarios` |
| DELETE usuário | `GET /usuarios` |

GET inicial com falha (rede/5xx/corpo ilegível): estado de falha,
**Tentar de novo**, distinto de zeros / lista vazia.

`409` (e-mail duplicado, auto-desativação), `422` (senha curta,
perfil inválido): motivo visível; estado anterior permanece.

Enquanto a escrita daquele alvo não conclui, o botão daquele
alvo fica indisponível.

Mercado e Painel e Retenção são só leitura nesta fatia.

**Rationale**: FR-003, FR-015, FR-018.

---

## 7. Testes: pytest nos números e na lista; Vitest nas telas

**Decisão**:

- **pytest** (TDD): `contar_hospedados`, `contar_chamados_abertos`
  (sem consumo), `somar_consumo_pendente` (soma, não COUNT);
  `GET /indicadores` sem campos nominados; staff `403`;
  `GET /usuarios` só gestão, sem hash; DELETE não apaga a linha;
  GET `/retencao` devolve prazos sem inventar default. Recepção
  no `GET /indicadores` continua permitida pela matriz (como em
  chegadas-do-dia); a **tela** não dispara. Isolamento por hotel.
- **Vitest**: quatro telas + casca (gestão faz os GET certos;
  recepção/staff zero fetch nestes paths). `fetch` falso.
  Asserção “Painel é só o título” **quebra de propósito**.

Nenhum teste chama WhatsApp, IA, fonte pública ou PMS.
Nenhuma revisão Alembic.

**Rationale**: Artigo XII. Backend nasce; não é F8.6.

**Alternatives consideradas**:

- **Só Vitest, pytest só regressão**: os três COUNT/SUM não têm
  teste hoje. Recusado.

---

## Divergências documentais

O mapa `docs/wireframes-painel.html` (telas `gestao`, `mercado`,
`usuarios`, `retencao`) mostra seis KPIs, gráfico de 30 dias,
linha “você” com tarifa da casa, variação em 7 dias, aba
Concorrentes (CRUD) e **Reativar** usuário.

A spec clarificada **vence** o rascunho: quatro números; sem
gráfico; sem tarifa própria; sem %; sem CRUD de concorrente; sem
reativar. Corrigir o HTML é trabalho documental posterior — não
bloqueia implementar. Não contornar em silêncio.

`Casca.test.tsx` trata Painel como `TelaNomeada` (só o heading).
Esta fatia substitui essa asserção: passam a existir os quatro
números (ou zeros honestos).

`GET /retencao` hoje devolve só `execucoes`. O envelope ganha
prazos; testes que congelam o JSON exato precisam aceitar os
dois campos novos (ou `null`).
