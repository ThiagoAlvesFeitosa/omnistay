# Quickstart — validar IA real e aviso de assistente virtual

Roteiro depois de `/speckit-implement`. Contratos:
[modo-e-fabrica-llm.md](./contracts/modo-e-fabrica-llm.md),
[adaptador-real.md](./contracts/adaptador-real.md),
[aviso-assistente-virtual.md](./contracts/aviso-assistente-virtual.md),
[logs-e-segredo.md](./contracts/logs-e-segredo.md).
Modelo: [data-model.md](./data-model.md).

Comandos na raiz do repositório. **Sem** chamada ao serviço de
linguagem, **sem** PMS, **sem** Graph API.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. Hotel + recepção como no quickstart da F0.3.

```powershell
$env:MENSAGERIA_MODO = "demonstracao"
$env:LLM_MODO = "controlado"
pytest testes/unitarios -q
pytest testes/integracao -q
```

Nenhum teste desta fatia exige `GEMINI_API_KEY`.

---

## 1. Fábrica e recusa de subida

Sem `LLM_MODO` (ou valor lixo), `construir_llm` **falha alto**.
`controlado` devolve `LLMFalso`. `real` com chave na config de teste
devolve `LLMGemini` **sem** POST à rede (a suíte não dispara método).
`real` sem chave falha alto — não devolve o controlado.

```powershell
python -m worker --uma-passagem
```

sem `LLM_MODO` no ambiente: o processo **não** reclama trabalho.

Worker **não** instancia mais o controlado por omissão no
`processar_uma_passagem_na_engine`.

---

## 2. Canal e cérebro independentes

`MENSAGERIA_MODO=demonstracao` + `LLM_MODO=controlado` sobe.
A combinação inversa na fábrica (mensageria `real`, LLM `controlado`)
também constrói — a suíte **não** chama WhatsApp nem Gemini.

---

## 3. Aviso na primeira mensagem da estadia

Confirmar chegada com os três slots válidos. Consumir a fila.

O `conteudo` da mensagem de boas-vindas (histórico / GET do simulador)
contém as duas ideias (assistente virtual e pessoa da recepção) **e**
os três fatos. Coleta da mesma reserva **não** contém o aviso.
Resposta de dúvida seguinte **não** repete o aviso.

Única `?` continua na última linha.

---

## 4. Falha do cérebro não perde a mensagem

Com `LLMFalso` armado para `FalhaDeClassificacao` / timeout simulado no
adaptador real (transportador falso): a mensagem permanece, desfecho
humano visível, trabalho não fica pendente à espera do serviço. Log da
passagem tem `id_mensagem` e código — sem texto e sem chave.

---

## 5. Demonstração à banca (manual, fora da suíte)

No `.env` local (não versionado):

```
MENSAGERIA_MODO=demonstracao
LLM_MODO=real
GEMINI_API_KEY=...
```

Reiniciar API e worker. Pelo simulador: check-in → recado com aviso →
pergunta coberta pelo catálogo → resposta automática. Quota estourada:
“a recepção vai atender”, sem tela de erro.

A suíte pytest **não** usa esse `.env` para chamar o serviço.
