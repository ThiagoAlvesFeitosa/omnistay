# Contrato: casca e rotas

Prefixo da SPA: `/app`. API nas raízes já existentes. Mesma origem
(proxy Vite ou estáticos no uvicorn). Sem isso o cookie `SameSite=Strict`
não viaja.

---

## Rotas de tela

| Path | Quem entra | Conteúdo nesta fatia |
| --- | --- | --- |
| `/app/entrar` | visitante; autenticado é redirecionado à casa | E-mail, senha, Entrar |
| `/app/fila` | `recepcao` | Casa — título **Fila do dia** |
| `/app/chamados` | `staff` | Casa — título **Meus chamados**; layout compacto |
| `/app/indicadores` | `gestor` | Casa — título **Painel** |
| `/app/simulador` | `recepcao`, `gestor` | Tela da F6.2, sem login embutido |
| `/app/reserva`, `/app/ficha`, `/app/alertas`, `/app/consumos`, `/app/saida`, `/app/catalogo`, `/app/vendaveis`, `/app/boas-vindas` | `recepcao` | Tela nomeada (só título) |
| `/app/mercado`, `/app/usuarios`, `/app/retencao` | `gestor` | Tela nomeada (só título) |

Mapa completo: [destinos-por-perfil.md](./destinos-por-perfil.md).

Raiz `/app` e `/app/` com sessão → casa do perfil. Sem sessão →
`/app/entrar`.

---

## Comportamento visível

| Estado | O que a pessoa vê |
| --- | --- |
| Sem sessão em qualquer `/app/...` interno | Tela de entrada, não página vazia |
| Sessão válida em `/app/entrar` | Redirect à casa, sem seletor de papel |
| Recarregar na casa | Permanece; `GET /sessoes/atual` de novo |
| Sair | Entrada; recarregar não restaura |
| Destino de outro perfil pelo endereço | Não mostra o conteúdo; vai à casa |
| 401 no meio do uso | Entrada, aviso de sessão, zero dado residual |
| Tela nomeada | Título acordado; zero lista inventada |

---

## Menu e chrome

Autenticado: nome do funcionário (já vem em `GET /sessoes/atual`),
itens do mapa do perfil, ação **Sair**.

`staff`: sem menu lateral longo — casa + sair, utilizável em telefone.

Visitante: sem menu de destinos internos.

---

## Estáticos e atalho antigo

- `frontend/dist` servido em `/app` por rotas em `criar_aplicacao`:
  arquivo real se existir no dist; senão `index.html` (rotas do
  React Router como `/app/entrar`). **Não** usar
  `StaticFiles(html=True)` — o Starlette devolve 404 nesses caminhos
  em vez de cair no `index.html` da raiz do dist.
- Dist ausente: as rotas `/app` não são registradas; a API sobe.
- `GET /demo` e `GET /demo/` → redirecionamento 307 para
  `/app/simulador`.
- API `/simulador/conversas` **não** muda de path.

---

## Vite (desenvolvimento)

`base: "/app/"`. Proxy de todas as raízes de API para o uvicorn
(` /sessoes`, `/simulador`, `/health`, `/reservas`, `/fila-do-dia`,
e as demais já existentes). O SPA **não** é proxied.

---

## O que a casca não é

- Fila com hóspedes, cadastro, chegada, ficha, resolver chamado,
  lançar consumo, catálogo editável, usuários, mercado, retenção
- Seletor de hotel
- Tela de dispositivos conectados
- Layout compacto para recepção e gestão
