# Quickstart — validar a ficha do hóspede no painel

Roteiro depois de `/speckit-implement`. Contratos:
[api-reusada.md](./contracts/api-reusada.md),
[api-alterar-ficha.md](./contracts/api-alterar-ficha.md),
[superficie-da-recepcao.md](./contracts/superficie-da-recepcao.md),
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

A revisão `0024` precisa estar aplicada (gatilho). `DATABASE_URL` no
ambiente. Propriedade e usuários dos três perfis como no quickstart
da F0.3 / F8.1. Pelo menos uma reserva do turno com ficha parcial
(campos reconhecidos só em parte) e outra completa.

```powershell
pytest testes/unitarios -q
pytest testes/integracao -q -k "ficha or consentimento or transicao or inventario or conformidade or sessao"
cd frontend
npm test
```

`npm test` é o portão da superfície. A suíte Python é o portão do
`PUT` e do gatilho.

---

## 1. Abrir a ficha pela fila

Uvicorn na API. No `frontend/`:

```powershell
npm run dev
```

Abrir `http://127.0.0.1:5173/app/entrar`. Entrar como recepção.

Na **Fila do dia**, **Ver ficha** na linha parcial: distintivo
parcial e cada campo ausente **nomeado**. Completa: distintivo
completa, lista de ausentes vazia. Sem e-mail. Idade, se houver
nascimento, só como texto ao lado.

Menu **Ficha do hóspede** sem escolher reserva: nenhum nome, nenhum
documento; indica abrir pela fila.

Staff e gestão em `/app/ficha` ou `/app/ficha/1`: não vêem a ficha;
caem na casa do papel.

---

## 2. Completar no balcão

Na parcial, preencher os ausentes com valores válidos e **Gravar**.
A tela vira completa. Nenhuma mensagem nova no simulador / histórico
daquela reserva.

Voltar à fila: aquela linha **não** traz mais o sinal de parcial
(status `ficha_recebida` / estado `completa`).

Telefone `123` ou CEP curto: recusa, sem persistir o inválido.
Cancelar: volta ao que estava.

---

## 3. Copiar tudo

**Copiar tudo** numa ficha completa: o texto tem os nove rótulos e
os valores visíveis, sem linha de idade e sem e-mail. Colar num
bloco de notas (não é preciso colar no PMS neste roteiro).

Se o navegador recusar a cópia automática, o mesmo texto permanece
selecionável na tela.

---

## 4. Consentimento

Bloco na ficha: nunca registrado, ou concedido/recusado **com data**.
**Revogar** um aceite: vigente passa a recusado com data de agora;
consultar de novo não apaga o histórico (GET com `em` anterior ainda
mostra o aceite antigo — pela API, se quiser conferir).

---

## Fora deste roteiro

Checkout, consumos, chamados, catálogo, recado de boas-vindas.
Colagem no PMS real da propriedade (achado de campo). Continua
título no menu o que a F8.4+ ainda não preencheu.
