# Contrato: modo de inteligência e fábrica

Configuração e escolha do adaptador. Adaptador HTTP:
[adaptador-real.md](./adaptador-real.md). Aviso:
[aviso-assistente-virtual.md](./aviso-assistente-virtual.md). Log:
[logs-e-segredo.md](./logs-e-segredo.md).

---

## Configuração

| Chave | Valores | Onde |
| --- | --- | --- |
| `LLM_MODO` | `controlado` \| `real` | Ambiente / `.env`. Sem valor versionado |
| `GEMINI_API_KEY` | segredo | Ambiente. Obrigatória se `real`. Nunca versionada |
| `LLM_TIMEOUT_SECONDS` | número > 0 | Ambiente. Padrão `15` se omitida |
| `LLM_MODELO` | id do modelo | Ambiente. Padrão `gemini-2.0-flash` se omitida |

Não é `parametro_hotel`. Um modo por processo. Independente de
`MENSAGERIA_MODO` — as quatro combinações são válidas.

Ausente, vazio ou outro texto em `LLM_MODO`: `construir_llm` **falha
alto**. `LLM_MODO=real` com chave vazia: o **mesmo** (não chama o
serviço, não devolve `LLMFalso`).

`.env.example` lista as chaves **sem valor**.

---

## Fábrica

```text
construir_llm(config) → LLMProvider
```

| Modo | Classe | Rede |
| --- | --- | --- |
| `controlado` | `LLMFalso` | Nenhuma |
| `real` | `LLMGemini` | generateContent (suíte **não** aponta para o host real) |

Exceção: `ConfiguracaoDeInteligenciaInvalida` (modo inválido **ou**
real sem chave). A mensagem da exceção **não** contém a chave.

`python -m worker` usa a fábrica na subida, junto com
`construir_mensageria`. `processar_uma_passagem_na_engine` usa a fábrica
quando `llm` é omitido. `processar_uma_passagem(..., llm=)` continua
aceitando a porta — a suíte injeta `LLMFalso` armado.

O módulo `conversa.service` **não** importa classe de adaptador.

---

## `LLMFalso` (modo `controlado` e suíte)

Implementa o Protocol completo. Em `controlado` no worker, sobe **sem**
`falhar_sempre` / `proximo_*` armados — o mesmo default de hoje
(`irreconhecivel` / dúvida genérica / `nenhum` item) até alguém
configurar. Na suíte, os ganchos de falha permanecem.

Não é um segundo conjunto de regras: o domínio trata o resultado como
sempre tratou.

---

## Isolamento canal × cérebro

| | `LLM_MODO=controlado` | `LLM_MODO=real` |
| --- | --- | --- |
| `MENSAGERIA_MODO=demonstracao` | Tela + cérebro determinístico | Tela + serviço de linguagem |
| `MENSAGERIA_MODO=real` | WhatsApp + cérebro determinístico | WhatsApp + serviço de linguagem |

A fábrica de LLM **não** lê `mensageria_modo`. A de mensageria **não**
lê `llm_modo`.

---

## Recusa de subida

Qualquer comando `python -m worker …` constrói as duas fábricas **antes**
de processar fila ou agendador. Modo inválido ou real sem chave: o
processo termina com falha; 0 trabalhos reclamados.
