# Quickstart — validar consumos a lançar e saída do hóspede

Roteiro depois de `/speckit-implement`. Contratos:
[api-reusada.md](./contracts/api-reusada.md),
[superficie-consumos.md](./contracts/superficie-consumos.md),
[superficie-saida.md](./contracts/superficie-saida.md),
[acrescimo-na-fila.md](./contracts/acrescimo-na-fila.md),
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
como no quickstart da F0.3 / F8.1. Precisa de reserva hospedada com
consumo pendente para o caminho feliz — a suíte Vitest não depende
disso.

```powershell
pytest testes/unitarios -q
pytest testes/integracao -q -k "consumo or lancamento or dispensa or saida or pedidos or fila or sessao"
cd frontend
npm test
```

A suíte Python continua verde **sem** teste novo de regra de
lançamento ou de checkout. `npm test` é o portão desta fatia.

---

## 1. Consumos a lançar deixa de ser só título

Uvicorn na API. No `frontend/`:

```powershell
npm run dev
```

Abrir `http://127.0.0.1:5173/app/entrar`. Entrar como recepção.
Menu **Consumos a lançar**.

A lista mostra item, valor, tempo, total no topo — ou o estado
vazio. Não é só o `<h1>`. Sem nome na linha. **Ver ficha** abre
`/app/ficha/{id}`.

Staff e gestão no mesmo endereço `/app/consumos`: não vêem a
lista; caem na casa do papel.

---

## 2. Lançar e dispensar somem da fila

**Marcar lançado** num pendente: some sem recarregar o navegador;
totais baixam. Segundo clique: recusa visível.

**Dispensar** noutro: some da fila; na saída daquela estadia o
item **não** entra em pedidos feitos pelo chat.

Clicar descrição ou **Ver ficha**: o item **não** lança.

---

## 3. Fila do dia abre a saída; não encerra

Hospedado: link **Saída** (não **Confirmar saída**). Abre
`/app/saida/{id}` com a lista **Pedidos feitos pelo chat**. A
reserva continua hospedada até **Confirmar saída** nessa tela.

Hospedado com saída prevista já passada: destaque de saída não
confirmada, distinto da chegada vencida.

---

## 4. Aviso não trava; nomenclatura

Com consumo pendente na estadia: aviso **antes** do botão. O aviso
leva a Consumos a lançar da **casa** (não só daquela reserva).
Confirmar saída mesmo assim encerra; o pendente permanece na fila
financeira.

Zero “extrato” e zero “conta” na interface. Serviço sem cobrança
fora da lista.

`/app/saida` sem id: aponta à fila, sem botão órfão.

---

## 5. Falha de leitura

Desligar a API com Consumos a lançar aberto e **Tentar de novo**:
o painel permanece e **não** mostra o estado de lista vazia.

---

## Fora deste roteiro

Catálogo, itens vendáveis, recado de boas-vindas, indicadores da
gestão, status de lançamento por item na lista da saída (depois da
semana).
