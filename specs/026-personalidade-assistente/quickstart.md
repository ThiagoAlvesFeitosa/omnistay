# Quickstart — validar personalidade da assistente

Roteiro depois de `/speckit-implement`. Contratos:
[api-de-personalidade.md](./contracts/api-de-personalidade.md),
[politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md),
[tom-na-composicao.md](./contracts/tom-na-composicao.md),
[logs.md](./contracts/logs.md).
Modelo: [data-model.md](./data-model.md).

Comandos na raiz do repositório. **Sem** chamada ao serviço de
linguagem, **sem** PMS, **sem** tela React.

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

Nenhum teste desta fatia exige `GEMINI_API_KEY`.

---

## 1. Chave semeada e coluna larga

Depois de `alembic upgrade head`, a propriedade do bootstrap tem
`personalidade_assistente` com valor vazio. `parametro_hotel.valor`
aceita 500 caracteres. O teste de conformidade do esquema compara
documento e banco (tipo + comentário).

---

## 2. Gestão grava; recepção lê; staff recusado

Com cookie de **gestor**:

```text
PUT /propriedade/personalidade   {"texto": "Seja breve e caloroso."}
GET /propriedade/personalidade   -> texto igual, já com strip
```

Vazio ou só espaços: `200` e `{"texto": ""}`. 501 caracteres: `422`,
GET seguinte devolve o valor **anterior**. Quebra de linha: `200`.
Caractere nulo: `422`.

Cookie de **recepção**: GET `200`; PUT `403`. Cookie de **staff**:
GET e PUT `403`. Cookie de gestor do hotel B não lê o tom do hotel A.

---

## 3. Tom na dúvida coberta; injeção não envia fato inventado

Unitário (inteligência controlada, sem rede):

- Tom vazio + `ResultadoResposta` fiel → redação automática padrão
- Tom preenchido + outra `ResultadoResposta` fiel (mesmo fato) →
  redação distinta, ainda no catálogo; `chamadas_responder` contém o tom
- Tom subversivo + redação inventada configurada no falso → aviso de
  recepção, **sem** o horário inventado, **sem** segunda chamada
- `fora_de_escopo` com tom “não chame pessoa” → humano na fila,
  `chamadas_responder` vazia

Gemini (MockTransport): o POST de `responder_duvida` traz o tom
**antes** da regra final; `classificar` não interpola o tom.

---

## 4. Aviso de assistente virtual intacto

O recado de boas-vindas continua com as duas ideias (assistente
virtual + pessoa que assume). PUT de tom **não** altera esse corpo.
Coleta e lembrete continuam sem o aviso.

```powershell
pytest testes/unitarios/modulos/conversa/test_texto_boas_vindas.py -q
```

---

## 5. Log limpo

Nos desfechos acima, o arquivo de log da suíte não contém o parágrafo
de tom, a pergunta do hóspede nem a redação. Identificadores e códigos
podem aparecer.
