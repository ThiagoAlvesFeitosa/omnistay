# Quickstart — validar a linha de convite no recado

Roteiro depois de `/speckit-implement`. Contratos:
[api-de-boas-vindas.md](./contracts/api-de-boas-vindas.md),
[politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md),
[montagem-e-porta.md](./contracts/montagem-e-porta.md),
[logs.md](./contracts/logs.md).
Modelo: [data-model.md](./data-model.md).

Comandos na raiz do repositório. **Sem** Graph/WhatsApp de verdade,
**sem** PMS, **sem** tela React.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. Hotel + gestor + recepção como no
quickstart da F0.3.

```powershell
$env:MENSAGERIA_MODO = "demonstracao"
$env:LLM_MODO = "controlado"
pytest testes/unitarios -q
pytest testes/integracao -q
```

Nenhum teste desta fatia exige token da Meta nem chave de linguagem.

---

## 1. Chave semeada

Depois de `alembic upgrade head`, a propriedade do bootstrap tem
`boas_vindas_convite` com a semente de serviços / cardápio / horários.
Hotel que já existia também. O teste de conformidade compara documento
e banco (comentário da tabela).

---

## 2. Recepção grava os quatro; gestão lê; staff recusado

Cookie de **recepção**:

```text
GET /propriedade/boas-vindas
PUT /propriedade/boas-vindas
    {"cafe":"…","wifi":"…","checkout":"…","convite":"Pode perguntar sobre o spa."}
```

GET seguinte devolve o convite já com `strip`. Corpo sem `convite`:
`422`. Convite com quebra de linha ou 256 caracteres: `422`, GET
devolve o valor **anterior**.

Cookie de **gestão**: GET `200`; PUT `403`. Cookie de **staff**: GET e
PUT `403`.

---

## 3. Recado termina com a linha da casa

Confirmar chegada com os quatro válidos. No histórico (e no simulador,
se o canal estiver em demonstração):

- três fatos com rótulo
- aviso de assistente virtual
- última linha = convite gravado
- frase `Quer saber mais alguma coisa da sua estadia?` **ausente**

A porta falsa registra `len(variaveis) == 5` e `convite` igual ao
gravado.

---

## 4. Convite ausente: check-in ocorre, recado não sai

Apagar `boas_vindas_convite` (ou os três de entrada válidos e o convite
vazio via SQL). Confirmar chegada: reserva `hospedado`, zero trabalho,
`boas_vindas_nao_enviadas` na fila.

Completar o convite e rodar `--verificar-boas-vindas`: recado único na
janela; nada fora da janela. Segundo `--verificar-boas-vindas`: nenhum
segundo recado.

---

## 5. WhatsApp (só MockTransport)

Unitário do adaptador: POST com cinco parâmetros na ordem
`(prenome, cafe, wifi, checkout, convite)`. Sem rede.

O template aprovado na Meta com esse corpo é passo **humano**, fora da
suíte. Até existir, o canal real recusa o envio — não entrega a frase
antiga.
