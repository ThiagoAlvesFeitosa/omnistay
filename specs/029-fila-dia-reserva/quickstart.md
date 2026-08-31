# Quickstart — validar a fila do dia e o cadastro no painel

Roteiro depois de `/speckit-implement`. Contratos:
[api-reusada.md](./contracts/api-reusada.md),
[superficie-da-recepcao.md](./contracts/superficie-da-recepcao.md),
[resumo-do-turno.md](./contracts/resumo-do-turno.md),
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
como no quickstart da F0.3 / F8.1.

```powershell
pytest testes/unitarios -q
pytest testes/integracao -q -k "reserva or fila or chegada or sessao or casca"
cd frontend
npm test
```

A suíte Python continua verde **sem** teste novo de regra de
hospedagem. `npm test` é o portão desta fatia.

---

## 1. Casa da recepção deixa de ser só título

Uvicorn na API. No `frontend/`:

```powershell
npm run dev
```

Abrir `http://127.0.0.1:5173/app/entrar`. Entrar como recepção.

A casa **Fila do dia** mostra o resumo (três contas) e a lista — ou
o estado vazio, se não houver reserva do turno. Não é só o `<h1>`.

Staff e gestão no mesmo endereço `/app/fila`: não vêem nome nem
telefone; caem na casa do papel.

---

## 2. Cadastro de três campos

Da fila, **Nova reserva** (ou o item do menu). Só nome, telefone e
datas. Sem e-mail.

Telefone `123`: recusa na digitação, sem criar reserva.

Saída = entrada: recusa, sem criar.

Cadastro válido com entrada **hoje**: volta à fila; a linha aparece;
as contas somam o número de linhas.

Cadastro válido com entrada **futura**: aviso de que foi gravada e
não entra hoje; a linha **não** aparece na lista.

Cancelar: volta à fila, zero reserva nova.

---

## 3. Confirmar chegada no botão

Na linha elegível (`ficha_recebida`, `ficha_parcial` ou sem cadastro
prévio), o botão **Confirmar chegada** registra num clique. A linha
passa a hospedada sem recarregar o navegador. Se estava vencida, a
conta de vencida cai e a de hospedados sobe.

Clicar no nome ou no telefone da mesma linha: a situação **não** muda.

Linha ainda `aguardando_cadastro`: o botão **não** aparece.

---

## 4. Pendências distintas e falha de leitura

Uma ficha parcial, um hospedado sem recado e uma entrada vencida:
três sinais com rótulos diferentes.

Desligar a API com a fila já aberta e **Tentar de novo** (ou recarregar
com a API fora): o painel permanece e **não** mostra o estado de fila
vazia.

---

## Fora deste roteiro

Ficha, checkout, textos de boas-vindas, chamados, catálogo. Continua
título no menu, como a F8.1.
