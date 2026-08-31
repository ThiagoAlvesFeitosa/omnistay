# Contrato: sessão no navegador

A casca **não** inventa autenticação. Consome o contrato da F0.3,
com um ajuste de cookie documentado em [research.md](../research.md) §5.

Rotas (inalteradas no path e no corpo):

| Ação | Método | Path | Corpo |
| --- | --- | --- | --- |
| Entrar | `POST` | `/sessoes` | `{ "email", "senha" }` (`dispositivo` opcional) |
| Quem sou eu | `GET` | `/sessoes/atual` | — |
| Sair | `DELETE` | `/sessoes/atual` | — |

`credentials: "include"` em todo `fetch`. Sem `Authorization`. Sem
token no JSON de resposta (já era assim: só `Set-Cookie`).

---

## Cookie

| Atributo | Valor |
| --- | --- |
| Nome | `omnistay_sessao` |
| `HttpOnly` | Sim |
| `SameSite` | `Strict` |
| `Path` | `/` |
| `Secure` | Sim se a requisição for HTTPS; não se for HTTP |
| `Max-Age` | Segundos até `expira_em` |

O script da página **não** lê, **não** copia e **não** grava o valor
em `localStorage` nem em `sessionStorage`.

---

## Respostas que a casca trata

| Status | Quando | O que a tela faz |
| --- | --- | --- |
| 201 | `POST /sessoes` ok | Lê `perfil` do corpo **ou** chama `GET /sessoes/atual` e vai à casa |
| 401 | credencial inválida ou sessão inválida | Texto único de recusa na entrada; não diz se o e-mail existe |
| 204 | `DELETE /sessoes/atual` | Vai a `/app/entrar` |
| 422 | corpo malformado | Não ecoa senha; trata como “preencha os campos”, não como e-mail inexistente |

401 de **qualquer** fetch autenticado no painel: a casca volta à
entrada, sem página em branco e sem dado residual na interface.

---

## O que esta fatia não chama

`GET /sessoes` e `DELETE /sessoes/{id}` (revogar dispositivo) existem
e continuam só da recepção. A casca **não** oferece a lista nesta
fatia.

`POST /usuarios` tampouco.
