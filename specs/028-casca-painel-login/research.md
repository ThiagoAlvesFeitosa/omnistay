# Fase 0 — Pesquisa e decisões técnicas: casca do painel e login

Cada seção registra a decisão, por que ela foi tomada e o que foi recusado.
Divergências documentais estão na última seção.

---

## 1. Nenhuma rota nova de autenticação

**Decisão**: a casca consome as três operações já entregues na F0.3:

| Ação na tela | Rota existente |
| --- | --- |
| Entrar | `POST /sessoes` |
| Quem sou eu / recarregar | `GET /sessoes/atual` |
| Sair | `DELETE /sessoes/atual` |

Zero operação nova na matriz. Zero revisão Alembic. Cookie
`omnistay_sessao` (`HttpOnly`, `SameSite=Strict`, `Path=/`) continua
sendo o único transporte. O JavaScript **nunca** lê o token.

**Rationale**: a spec (FR-001, FR-007, FR-019) reusa a autenticação; não
a redesenha. Artigo XI.

**Alternativas consideradas**:

- **JWT no `localStorage`**: a F0.3 rejeitou — não é revogável na
  requisição seguinte e o script alcança o token. Rejeitado de novo.
- **`GET /painel/destinos`**: API só para o menu. O mapa é estático por
  perfil; uma rota nova compete com tempo de tela (Artigo XI).
- **Segundo cookie / “lembrar-me”**: a sessão longa por perfil já existe.

---

## 2. SPA em `/app`, não em `/` nem em `/demo`

**Decisão**: o painel vive sob o prefixo `/app`. Rotas de tela:

| Caminho | Destino |
| --- | --- |
| `/app/entrar` | Tela de entrada |
| `/app/fila` | Casa da recepção |
| `/app/chamados` | Casa da equipe (`staff`) |
| `/app/indicadores` | Casa da gestão |
| `/app/simulador` | Simulador já entregue (F6.2) |
| demais `/app/...` do mapa | Telas nomeadas, sem ação operacional |

A API permanece nas raízes atuais (`/sessoes`, `/fila-do-dia`,
`/simulador/conversas`, …). FastAPI serve `frontend/dist` em `/app`
(arquivo real ou, se o caminho não existir, `index.html`). Vite
`base: "/app/"`. React Router com `basename="/app"`.

**Na implementação:** o plano citava `StaticFiles(html=True)`. Isso
404 em `/app/entrar`. O mount passou a ser fallback explícito para o
`index.html` da raiz do dist. Dist ausente não registra `/app`.

`/demo` e `/demo/` passam a **redirecionar** para `/app/simulador`, para
não quebrar o atalho da F6.2.

**Rationale**: `GET /fila-do-dia` já existe. Uma rota de tela com o
mesmo caminho colide. Prefixo `/app` é um mount, não um gateway.

**Alternativas consideradas**:

- **Tela em `/` com os mesmos paths da API**: o primeiro clique na fila
  acerta o JSON, não o HTML. Rejeitado.
- **Hash (`#/fila`)**: evita colisão sem prefixo, mas o endereço da
  spec (FR-014) fica feio e o FastAPI não precisa proteger hash.
- **Manter `/demo` como casa do SPA**: a casca deixa de ser o produto e
  continua “a tela da banca”. Rejeitado pelo backlog da Fase 8.

---

## 3. `react-router` porque o endereço é requisito

**Decisão**: `react-router-dom` no `frontend/` já existente. Destino
alheio digitado na barra é recusado na casca (redireciona à casa do
papel ou à entrada) **e** qualquer fetch à API daquele destino continua
levando `403`/`404` — a omissão no menu não é a única parede.

**Rationale**: FR-014 exige endereço. As fatias F8.2–F8.7 acrescentam
telas no mesmo mapa. Trocar de `useState` a cada fatia é retrabalho.

**Alternativas consideradas**:

- **Um `pathname` manual sem lib**: cabe em três telas; quebra no sexto
  destino. Rejeitado porque o mapa desta fatia já tem mais de três.
- **Aplicação React nova ao lado do simulador**: o backlog fechou
  “estende o `frontend/`”. Rejeitado.

---

## 4. Tailwind + shadcn copiado, sem runtime

**Decisão**: seguir a decisão fechada da Fase 8. Tailwind no Vite.
Componentes shadcn **copiados** para `frontend/src/components/ui/` —
nesta fatia só o que a entrada precisa (campo, botão, rótulo). Sem
dependência de serviço de componentes. Sem biblioteca de estado global.

**Rationale**: visual da demonstração e do protótipo de referência; o
Artigo XI barra kit com runtime, não CSS copiado.

**Alternativas consideradas**:

- **CSS do simulador (objetos `style=`)**: a Fase 8 já escolheu o kit.
  Reabrir competiria com as telas seguintes.
- **shadcn via CLI a cada build**: runtime disfarçado. Rejeitado.

---

## 5. Cookie `Secure` acompanha o esquema da requisição

**Decisão**: `Secure=True` quando o pedido é HTTPS; `Secure=False`
quando é HTTP. `HttpOnly` e `SameSite=Strict` não mudam. Teste
automatizado cobre os dois esquemas.

**Rationale**: o contrato da F0.3 marcou `Secure` sempre. Em
`http://127.0.0.1` o navegador **não grava** cookie `Secure`. A casca
não funciona na máquina de desenvolvimento nem na demonstração local
sem isso. Não é segundo mecanismo de sessão: é o cookie existente
passar a viajar no canal em que a tela roda.

**Alternativas consideradas**:

- **HTTPS local (mkcert)**: peça a mais sem problema de produto
  (Artigo XI).
- **Deixar `Secure=True` e documentar “só funciona em HTTPS”**: a
  demonstração da semana é local e HTTP. A tela mentiria o login.
- **`SameSite=Lax` para cross-port**: o proxy Vite e o mount `/app` no
  uvicorn mantêm mesma origem. Lax enfraqueceria sem ganho.

---

## 6. Mapa de destinos no frontend, matriz de permissão intacta

**Decisão**: tabela `perfil → destinos` em módulo TypeScript
(`frontend/src/painel/destinos.ts`). A matriz `politica.py` **não ganha**
operação `ver_painel`. Recusa de fato continua 401/403/404 da API.

Casa por perfil (valores já gravados em `usuario.perfil`):

| Perfil | Tela inicial |
| --- | --- |
| `recepcao` | `/app/fila` |
| `staff` | `/app/chamados` |
| `gestor` | `/app/indicadores` |

Visitante (`GET /sessoes/atual` → 401) só vê `/app/entrar`.

**Rationale**: o menu é apresentação; a autorização já existe. Duplicar
a matriz no backend só para o menu seria terceira descrição.

**Alternativas consideradas**:

- **Esconder só no CSS**: o endereço alheio ainda renderizaria. Viola
  FR-014.
- **Uma operação nova por destino**: explode a matriz sem mudar o que a
  API já recusa. Rejeitado.

---

## 7. Teste da casca: pytest no que é HTTP; Vitest no que é tela

**Decisão**:

- **pytest** (como sempre): cookie conforme o esquema; mount `/app`
  quando `frontend/dist` existe; redirecionamento `/demo` →
  `/app/simulador`; regressão de `POST/GET/DELETE /sessoes` (já verde,
  não reabrir regra). **Nenhum** teste abre navegador.
- **Vitest + Testing Library** no `frontend/`: destino inicial por
  perfil, itens de menu (o que aparece e o que some), entrar chama
  `POST /sessoes` com `credentials: "include"` e **não** guarda token,
  401 devolve à entrada, sair chama `DELETE /sessoes/atual`. `fetch`
  falso. Sem Playwright.

**Rationale**: Artigo XII exige teste que falhe sem a tela. pytest não
renderiza React. Playwright é processo de browser — complexidade sem
problema presente (F6.2 já recusou). Vitest é o menor runner que vê a
casca.

A suíte `pytest` continua o portão do backend. `npm test` no `frontend/`
é o portão da casca. O quickstart roda os dois.

**Alternativas consideradas**:

- **Só pytest + quickstart no browser** (molde F6.2): a F6.2 era uma
  página; esta fatia **é** a tela. Rejeitado pelo Artigo XII.
- **Playwright ponta a ponta**: lente certa daqui a seis telas, cara
  agora. Rejeitado nesta fatia.

---

## 8. O simulador perde o login embutido

**Decisão**: `TelaSimulacao` deixa de pedir e-mail e senha. A casca
autentica; o simulador é uma rota de recepção e gestão. 401 em
`/simulador/conversas` sobe para a casca (volta a `/app/entrar`). Staff
não vê o item e, se digitar o endereço, a casca recusa **e** a API
continua `403`.

**Rationale**: um login por produto. Dois formulários divergiriam na
recusa indistinguível.

**Alternativas consideradas**:

- **Manter login só no simulador**: a casca nasceria vazia. Rejeitado.
- **Iframe do `/demo` antigo**: duas origens, cookie `Strict` não
  atravessa. Rejeitado.

---

## 9. Telas nomeadas sem dado inventado

**Decisão**: destino cujo trabalho é F8.2–F8.7 renderiza o **título**
acordado e nada mais — zero hóspede, zero chamado, zero indicador
falso. Sem botão que chame API operacional.

**Rationale**: FR-017 e FR-018. Maquete com lista inventada ensinaria o
turno errado na banca.

**Alternativas consideradas**:

- **Já listar `GET /fila-do-dia` na casa da recepção**: é a F8.2.
  Antecipar mistura aceite desta fatia com a seguinte.
- **Omitir do menu o que ainda não opera**: o filtro por perfil deixa
  de ser observável (só três casas). A spec pede o mapa.

---

## 10. Celular só na equipe

**Decisão**: layout compacto (título, sair, área da casa) apenas em
`/app/chamados` e em `/app/entrar` quando o perfil for `staff`. Recepção
e gestão: menu lateral no computador. Não há meta de responsividade nas
dezesseis telas.

**Rationale**: decisão fechada da Fase 8.

---

## Divergências documentais

1. **`Secure` sempre-ligado (contrato F0.3).** A F0.3 escreveu `Secure`
   incondicional pensando no painel em canal seguro. A casca precisa
   rodar em HTTP local. Esta fatia ajusta o atributo ao esquema e
   registra o teste. O contrato vivo da sessão nesta pasta prevalece
   para o navegador; HTTPS de instalação real continua com `Secure`.
2. **`/demo/` como casa do SPA (F6.2).** A F6.2 montou o estático em
   `/demo`. A Fase 8 promove o mesmo `frontend/` a painel. `/demo`
   redireciona; o fio do simulador não muda (`/simulador/conversas`).
3. **Login embutido em `TelaSimulacao`.** Era o único jeito de autenticar
   na página da banca. Sai nesta fatia. Não é regressão do canal: é o
   login passando a ser da casca.
4. **F7.4 não esconde destino.** O backlog da semana cortou módulos por
   propriedade. O menu filtra só por perfil, como a spec.
