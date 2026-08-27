# Fase 0 — Pesquisa e decisões técnicas: IA real e aviso de assistente virtual

Cada seção registra a decisão, por que ela foi tomada e o que foi recusado.
Divergências documentais estão na seção 9.

---

## 1. Modo de inteligência é configuração de plataforma

**Decisão**: chave de ambiente `LLM_MODO` com exatamente dois valores:
`controlado` | `real`. Um por processo. Lida em `app/config.py`. **Não**
entra em `parametro_hotel`. Independente de `MENSAGERIA_MODO`.

| Valor | Adaptador |
| --- | --- |
| `controlado` | `LLMFalso` (o mesmo da suíte, sem ganchos de falha armados) |
| `real` | `LLMGemini` (HTTP ao serviço de linguagem) |

Ausente, vazio ou outro texto: a fábrica **falha alto**. Modo `real` sem
`GEMINI_API_KEY`: o mesmo — falha alto, sem fingir o controlado e sem
chamar o serviço. Clarificação da sessão 2026-08-26: a recusa impede
**qualquer** trabalho daquele ambiente (coleta e boas-vindas inclusive).

`.env.example` lista `LLM_MODO` e `GEMINI_API_KEY` **sem valor**.

Timeout: `LLM_TIMEOUT_SECONDS` (plataforma, padrão **15**, o mesmo do
adaptador WhatsApp). Modelo: `LLM_MODELO` (opcional; padrão
`gemini-2.0-flash`). Nem timeout nem modelo são `parametro_hotel`.

**Rationale**: o modo escolhe *qual adaptador* classifica e redige, não
*como o hotel se comporta*. Artigo XIII cobre prazo da casa; o cérebro é
da plataforma, como o canal. Duas propriedades no mesmo worker com
cérebros diferentes violaria “um modo por ambiente”.

**Alternativas consideradas**:

- **Chave em `parametro_hotel`**: permitiria dois cérebros no mesmo
  processo. Rejeitado (spec + Artigo XIV não pedem cérebro por hotel).
- **Default silencioso `controlado`**: é o furo de hoje (`LLMFalso()` no
  consumidor). Esconderia `LLM_MODO=real` sem chave. Rejeitado.
- **Terceiro valor `teste`**: a suíte injeta a porta. Rejeitado.
- **`falso` em vez de `controlado`**: a spec usa controlado; `falso` é o
  nome da classe de teste. Rejeitado como valor de ambiente.

---

## 2. Fábrica no mesmo molde da mensageria

**Decisão**: `construir_llm(config)` em
`app/adaptadores/fabrica_llm.py`. Worker (`python -m worker`) e
`processar_uma_passagem_na_engine` (quando `llm` é omitido) usam a
fábrica. `processar_uma_passagem(..., llm=)` continua aceitando a porta:
a suíte injeta `LLMFalso` configurado.

O domínio (`conversa.service`) **não** importa adaptador concreto
(Artigo X). A porta `LLMProvider` **não muda de métodos**.

`__main__` do worker constrói mensageria **e** LLM na subida — o mesmo
momento em que hoje já exige `MENSAGERIA_MODO`. Comando só de
agendador (`--verificar-retencao` etc.) também exige os dois modos:
é um processo só, a recusa é na subida.

**Rationale**: a spec pede o molde da F6.2. O furo concreto é
`porta_llm = llm or LLMFalso()` no consumidor e a ausência de fábrica
no `__main__`.

**Alternativas consideradas**:

- **Fábrica só no primeiro trabalho que precisa do cérebro**: coleta
  sairia com modo inválido. A clarificação recusou. Rejeitado.
- **`if llm_modo` dentro de cada serviço**: espalha o provedor no
  domínio. Rejeitado (Artigo X).
- **Instanciar Gemini na suíte para “provar o modo real”**: gasta rede
  e foge da regra de teste. O modo real se prova pela classe devolvida
  pela fábrica e por um cliente HTTP falso no adaptador.

---

## 3. Gemini por `httpx`, sem SDK

**Decisão**: `app/adaptadores/llm_gemini.py` implementa os cinco métodos
da porta com `httpx.post`, timeout da configuração. **Nenhuma biblioteca
nova.** `httpx` já é dependência principal (F6.2).

- URL: `https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent`
- Chave no cabeçalho `x-goog-api-key`, **não** na query — URL logada não
  pode vazar o segredo
- `generationConfig.response_mime_type = application/json`
- Um POST por chamada de método; o domínio já valida taxonomia e
  fidelidade ao catálogo **depois** da porta

Mapeamento de falha (código **sem** texto do hóspede):

| Situação | Exceção | Código |
| --- | --- | --- |
| Timeout `httpx` | a `Falha*` do método | `llm_tempo_esgotado` |
| Rede / 5xx | idem | `llm_indisponivel` |
| 401 / 403 | idem | `llm_recusa` |
| 429 | idem | `llm_quota` |
| Corpo não é JSON do método | idem | `llm_formato_invalido` |

JSON parseável com valor fora da taxonomia **não** levanta exceção: a
porta devolve `Resultado*` e o domínio já trata `formato_invalido`.

Cliente injetável (`httpx.Client`) para o teste de timeout/429 **sem
rede**. A suíte **nunca** aponta para `generativelanguage.googleapis.com`.

**Rationale**: Artigo XI — o problema é falar HTTP com um serviço; isso
já está resolvido no WhatsApp. SDK `google-genai` é peça, wheel e
versão a mais, e ainda assim falharia em timeout do mesmo jeito.

**Alternativas consideradas**:

- **Pacote `google-genai` / `google-generativeai`**: lib nova, Artigo XI.
  Rejeitado.
- **`urllib` da stdlib**: retrabalho; `httpx` já sobe o worker. Rejeitado.
- **Um único prompt “faz tudo”**: a porta tem cinco métodos com
  resultados distintos; o domínio chama um por tipo de trabalho.
  Rejeitado.

---

## 4. Cinco métodos, prioridade de refinamento

**Decisão**: o adaptador real implementa a porta **completa**. Clarificação:
classificar, `responder_duvida` e `extrair_ficha` levam o prompt
cuidado (jornada da demonstração). `identificar_item_vendavel` e
`interpretar_pesquisa_saida` passam pelo mesmo serviço; prompt mais
simples é aceitável — falha reusa `FalhaDeIdentificacao` /
`FalhaDeExtracao` já tratadas.

Não há híbrido (ficha no controlado, dúvida no real) no mesmo processo.

**Rationale**: um interruptor. Deixar dois usos no `LLMFalso` com
`LLM_MODO=real` seria o produto paralelo que a spec proíbe.

**Alternativas consideradas**:

- **Só classificar e redigir nesta fatia**: a clarificação escolheu todos
  os usos. Rejeitado.
- **Métodos não refinados levantam sempre `Falha*`**: mentiria “resultado
  útil”. Eles tentam o serviço; o fallback humano é o que já existe.

---

## 5. Aviso de assistente virtual no recado montado

**Decisão**: constante de produto em
`app/modulos/conversa/texto_boas_vindas.py`, linha **antes** do convite,
para a última linha continuar com a única interrogação (contrato F2.2).

Texto (ASCII, no mesmo registro do recado atual):

```text
O atendimento inicial e feito por uma assistente virtual. Uma pessoa da recepcao assume quando necessario.
```

Não é slot de `parametro_hotel`. Não é variável nova do template. A
propriedade não edita.

O `corpo` gravado em `mensagem` (e exibido no simulador) **leva** o
aviso. O adaptador WhatsApp **descarta** o `corpo` e manda o template
`boas_vindas` com as quatro variáveis já existentes (prenome, café,
wi-fi, checkout). Atualizar o texto fixo na Meta é operação fora desta
fatia — limitação honesta: no canal real, o hóspede só vê o aviso depois
que o template for republicado. A demonstração à banca usa o simulador.

**Rationale**: “primeira mensagem da estadia” é o recado de chegada.
Artigo VII: não nasce recado proativo extra. Quinta variável quebraria
o template aprovado das quatro.

**Alternativas consideradas**:

- **Primeira resposta automática da sessão**: hóspede que não pergunta
  nunca lê o aviso. A spec recusou ao fixar as boas-vindas.
- **Recado avulso depois das boas-vindas**: mensagem proativa nova.
  Rejeitado (Artigo VII).
- **Quinta variável no template**: retrabalho de aprovação Meta e
  mudança da tupla `(prenome, cafe, wifi, checkout)`. Rejeitado nesta
  fatia.
- **Aviso só com `LLM_MODO=real`**: é postura de produto, não do
  adaptador. O controlado é desenvolvimento/teste, não hóspede.

---

## 6. Sem migração Alembic

**Decisão**: revisão **não** nasce. `0001`…`0021` intactos.
`docs/04-schema.sql` intacto. Nada de coluna `modo_inteligencia`.

**Rationale**: modo e chave são do processo. O aviso é texto montado.
Inventar tabela para o aviso seria parâmetro da propriedade, que a spec
proíbe.

---

## 7. Log e segredo

**Decisão**: logs registram `modo`, classe escolhida, `id_mensagem` /
`id_trabalho` / `id_hotel`, código de falha. **Nunca** `GEMINI_API_KEY`,
**nunca** conteúdo de mensagem, **nunca** prompt, **nunca** corpo da
resposta do serviço (`bruto` continua só no JSON de auditoria da
mensagem, como nas F3.2/F3.3 — fora do log).

Exceção de configuração **não** interpola a chave. Teste varre arquivos
versionados à procura de padrão de chave Gemini (prefixo conhecido) e
falha se achar valor.

**Rationale**: Artigo VIII + FR-015/FR-017. O `bruto` na coluna já
existente é auditoria de classificação, não log operacional.

---

## 8. Tempo aceitável = timeout do cliente HTTP

**Decisão**: 15 segundos, configurável. `httpx.TimeoutException` vira
`Falha*` na primeira ocorrência. O domínio **já** marca o trabalho
`concluido` e encaminha a humano — sem backoff contra o LLM (F3.2,
F3.3). O worker não fica preso: o timeout é do cliente, não da fila.

**Rationale**: o WhatsApp já usa 15 s. Número de hotel não é; é limite
de plataforma para não travar a passagem. Valor no planejamento, como a
spec pediu.

**Alternativas consideradas**:

- **`parametro_hotel`**: o hotel não calibra o provedor. Rejeitado.
- **Retry único antes de humano**: a F3.2 decidiu primeira falha →
  humano. Não reabrir. Rejeitado.

---

## 9. Divergências documentais

1. **Worker instancia `LLMFalso` no consumidor.** O Artefato 5 §5.1 e o
   estado do projeto (26/08/2026) já previam adaptador real + fábrica.
   Nenhuma fatia das 24 pediu. Esta fecha o furo. A falsa permanece na
   suíte e no valor `controlado`.

2. **Contrato F2.2 da montagem do recado.** Ganha uma linha de produto
   antes do convite. A interrogação única na última linha **permanece**.
   Os três slots não mudam. O contrato histórico em
   `specs/009-confirmar-chegada/contracts/` não se reescreve; a mudança
   vive nesta fatia e no teste de `texto_boas_vindas`.

3. **Template Meta `boas_vindas`.** O canal real ignora o `corpo`
   montado. O aviso no WhatsApp de verdade exige republicar o template
   — fora do critério de pronto desta fatia. A banca vê o aviso no
   simulador. Artigo XV.

4. **`google-genai` não entra.** O estado do projeto fala em Gemini; não
   obriga o SDK oficial. HTTP com `httpx` cumpre o mesmo serviço.
