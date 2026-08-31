# Quickstart — validar a casca do painel e o login

Roteiro depois de `/speckit-implement`. Contratos:
[sessao-no-navegador.md](./contracts/sessao-no-navegador.md),
[casca-e-rotas.md](./contracts/casca-e-rotas.md),
[destinos-por-perfil.md](./contracts/destinos-por-perfil.md),
[politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md),
[logs.md](./contracts/logs.md).
Modelo: [data-model.md](./data-model.md).

Comandos na raiz do repositório. Sem PMS, sem WhatsApp.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. Propriedade e usuários dos três perfis
como no quickstart da F0.3 (`python -m app.bootstrap` + usuários de
recepção e staff já existentes no ambiente de teste).

```powershell
pytest testes/unitarios -q
pytest testes/integracao -q -k "sessao or casca or sessoes"
cd frontend
npm test
```

---

## 1. Cookie no canal HTTP

`POST /sessoes` com credencial válida em HTTP: `Set-Cookie` **sem**
`Secure`. O mesmo em HTTPS: **com** `Secure`. `HttpOnly` e
`SameSite=Strict` nos dois. Corpo **sem** o token.

E-mail inexistente e senha errada: o mesmo `401` e o mesmo texto.

---

## 2. Casca no navegador (desenvolvimento)

Uvicorn na API. No `frontend/`:

```powershell
npm run dev
```

Abrir `http://127.0.0.1:5173/app/entrar` (porta do Vite).

| Quem entra | Onde cai | Menu mostra | Menu não mostra |
| --- | --- | --- | --- |
| Recepção | Fila do dia | Fila, simulador | Meus chamados, Painel |
| Staff | Meus chamados | (casa + sair) | Fila, simulador, Painel |
| Gestão | Painel | Painel, simulador | Fila, Meus chamados, Dispositivos |

Credencial inválida: permanece na entrada, sem dizer se o e-mail existe.

Recarregar na casa: continua reconhecido. Sair: volta à entrada;
recarregar de novo pede senha.

Digitar `/app/chamados` autenticado como recepção: não mostra Meus
chamados; volta à fila.

---

## 3. Simulador é rota, não a casa

Com recepção, `/app/simulador` abre o fio da F6.2 **sem** segundo
formulário de login. Staff no mesmo endereço: recusa na casca (e
`403` se chamar a API).

`http://127.0.0.1:8000/demo` redireciona para `/app/simulador` quando
a API serve o `dist`.

---

## 4. Telas nomeadas

Abrir `/app/catalogo` como recepção: título **Catálogo**, lista vazia
de verdade (não hóspedes inventados). Gestão nesse endereço: não vê o
catálogo; cai no Painel.

---

## 5. O que não precisa passar

- Lista da fila do dia, cadastro de reserva, resolver chamado
- Playwright / teste que abre Chrome na CI
- Migração Alembic
- Alterar prazo de sessão em `parametro_hotel`
