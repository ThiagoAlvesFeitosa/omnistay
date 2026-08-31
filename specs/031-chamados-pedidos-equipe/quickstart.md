# Quickstart — validar chamados, pedidos e a tela da equipe

Roteiro depois de `/speckit-implement`. Contratos:
[api-reusada.md](./contracts/api-reusada.md),
[superficie-da-recepcao.md](./contracts/superficie-da-recepcao.md),
[superficie-da-equipe.md](./contracts/superficie-da-equipe.md),
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
como no quickstart da F0.3 / F8.1. Precisa de ao menos uma reserva
hospedada com solicitação aberta (reclamação, serviço e consumo)
para exercitar o caminho feliz — a suíte Vitest não depende disso.

```powershell
pytest testes/unitarios -q
pytest testes/integracao -q -k "solicitacao or resolver or sessao or casca"
cd frontend
npm test
```

A suíte Python continua verde **sem** teste novo de regra de
atendimento. `npm test` é o portão desta fatia.

---

## 1. Recepção: Chamados e pedidos deixa de ser só título

Uvicorn na API. No `frontend/`:

```powershell
npm run dev
```

Abrir `http://127.0.0.1:5173/app/entrar`. Entrar como recepção.
Menu **Chamados e pedidos**.

A lista mostra naturezas distintas, tempo decorrido, mais antigos
primeiro — ou o estado vazio, se não houver pendência. Não é só o
`<h1>`. Sem nome na linha. **Ver ficha** abre `/app/ficha/{id}`.

Staff e gestão no mesmo endereço `/app/alertas`: não vêem a lista;
caem na casa do papel.

---

## 2. Equipe: Meus chamados no compacto

Sair. Entrar como perfil operacional.

Casa **Meus chamados**: as três naturezas (incluindo consumo), um
botão **Resolvido** por cartão, sem nome/telefone/documento, sem
Ver ficha. Recarregar: continua reconhecido, sem nova senha.

Em `/app/ficha/1` e `/app/alertas`: recusa sem dado cadastral.

---

## 3. Resolver some da lista e não pede recado

Como recepção ou equipe, **Resolvido** num item aberto: some da
lista sem recarregar o navegador. Segundo clique: recusa visível,
sem segunda confirmação ao hóspede (conferir conversa / histórico
se o worker estiver no ar; a suíte já cobre o servidor).

Consumo resolvido some daqui; **não** há lançar nesta tela.

Clicar descrição ou **Ver ficha**: o item **não** resolve.

---

## 4. Sem quarto e falha de leitura

Pendência sem `numero_quarto`: continua na lista; na recepção,
**Ver ficha** ainda identifica o titular.

Desligar a API com a lista já aberta e **Tentar de novo**: o painel
permanece e **não** mostra o estado de lista vazia.

---

## Fora deste roteiro

Lançar consumo, confirmar saída, catálogo, indicadores da gestão.
Continuam título no menu, como a F8.1.
