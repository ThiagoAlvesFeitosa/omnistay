# Quickstart — validar o Simulador de Conversa

Roteiro depois de `/speckit-implement`. Contratos:
[modo-e-fabrica.md](./contracts/modo-e-fabrica.md),
[api-do-simulador.md](./contracts/api-do-simulador.md),
[entrada-simulada.md](./contracts/entrada-simulada.md),
[politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md),
[tela-de-simulacao.md](./contracts/tela-de-simulacao.md).
Modelo: [data-model.md](./data-model.md).

Comandos na raiz do repositório. Sem WhatsApp real, sem PMS, sem túnel.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. Hotel + gestor (ou recepção) como no
quickstart da F0.3.

```powershell
$env:MENSAGERIA_MODO = "demonstracao"
pytest testes/unitarios -q
pytest testes/integracao -q -k simulador
```

---

## 1. Fábrica e modo

Sem `MENSAGERIA_MODO` (ou valor lixo), construir a porta **falha alto**.
Com `demonstracao`, a classe é a simulada. Com `real`, é a do WhatsApp
— a suíte **não** chama a Graph API.

Worker (`python -m worker`) **não** instancia mais a falsa de teste.

---

## 2. Recado do hotel aparece no GET, não no provedor

Sessão de recepção, modo `demonstracao`. Cadastrar reserva (dispara
coleta). Consumir a fila:

```powershell
python -m worker --uma-passagem
```

`GET /simulador/conversas/{id}` mostra a coleta com `direcao=enviada`
e `status_envio=enviada`. Nenhuma chamada à Graph API.

---

## 3. Turno do hóspede usa as mesmas regras

Na reserva **hospedada**, `POST /simulador/conversas/{id}/mensagens`
com texto de dúvida coberta pelo catálogo e um `id_externo` novo.

**Esperado:** `201`, linha `recebida` no histórico, trabalho na fila.
`--uma-passagem`: resposta fiel ao catálogo **no GET**, não no corpo do
POST. Pedido de serviço: confirmação visível no fio **antes** de existir
`solicitacao`.

O mesmo `id_externo` de novo: `200`, uma só mensagem.

---

## 4. Modo real recusa a tela

```powershell
$env:MENSAGERIA_MODO = "real"
```

Reiniciar a API. `GET` e `POST` `/simulador/...` → `409` `modo_real`.
Zero linha nova. Staff em demonstração → `403`. Outro hotel → `404`.
Sem cookie → `401`.

---

## 5. Tela no navegador (critério visual)

Com a API em `demonstracao` e o worker em loop:

```powershell
cd frontend
npm install
npm run dev
```

Proxy Vite para o uvicorn. Entrar pelo painel em `/app/entrar`
(`POST /sessoes` já existente, mesmo origin via proxy). Com sessão de
recepção ou gestão, abrir `/app/simulador`, escolher a reserva, ver o
fio, digitar como hóspede, esperar o recado do hotel aparecer **sem**
telefone e **sem** Meta. Staff não vê essa rota.

Build de banca (opcional): `npm run build`; uvicorn serve a SPA em
`/app`. `GET /demo` redireciona para `/app/simulador`.

---

## Fora deste roteiro

- Painel da fila / mercado / retenção em React
- Instância de `MensageriaWhatsapp` na suíte
- Túnel + demonstração ao mesmo tempo (pode misturar entrada — pesquisa §4)
