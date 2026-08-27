# Modelo de dados — IA real e aviso de assistente virtual

Referência: `docs/04-schema.sql`. Decisões em [research.md](./research.md).
Esta fatia **não cria tabela**. O modo de inteligência não é linha de
banco. O aviso não é `parametro_hotel`.

---

## Entidades novas (só de configuração / texto de produto)

### Modo de inteligência

Não é tabela. É configuração do processo (`LLM_MODO`).

| Valor | Adaptador | Chave `GEMINI_API_KEY` |
| --- | --- | --- |
| `controlado` | `LLMFalso` | Ignorada (não chama o serviço) |
| `real` | `LLMGemini` | **Obrigatória** — ausência impede a subida |

Um valor por processo. Ausente ou outro texto: a fábrica não devolve
porta; o worker não sobe. Não há coluna em `reserva` nem em `hotel`.
Independente de `MENSAGERIA_MODO`.

Timeout e modelo são do mesmo processo (`LLM_TIMEOUT_SECONDS`,
`LLM_MODELO`), não da propriedade.

### Aviso de assistente virtual

Não é tabela. É constante de produto na montagem do recado de
boas-vindas. Uma frase, uma vez por estadia, no `conteudo` da mensagem
de saída `enviar_boas_vindas`.

A propriedade **não** tem chave para editar, omitir ou substituir.
Não nasce slot ao lado de `boas_vindas_cafe` / `_wifi` / `_checkout`.

---

## Entidades reusadas

### `mensagem`

| Campo | Papel nesta fatia |
| --- | --- |
| `conteudo` | Recado de boas-vindas passa a incluir o aviso (histórico e simulador). **Não** vai para log |
| `classificacao` (JSONB) | Continua guardando `bruto` e desfecho das F3.2/F3.3/F1.3. O adaptador real preenche o mesmo formato; o domínio valida igual |

Nenhuma coluna nova. Nenhuma origem `gemini` na linha.

### `trabalho`

Tipos existentes (`interpretar_ficha`, `classificar_mensagem`,
`responder_duvida`, `registrar_pedido_servico`,
`interpretar_pesquisa_saida`, …) **não** mudam. O worker continua
passando `llm=` para o serviço. Só a **origem** da porta muda.

Falha do serviço real: o serviço já marca `concluido` e encaminha a
humano. Esta fatia não acrescenta tipo nem backoff novo contra o LLM.

### `parametro_hotel`

Intocado. Os três slots de boas-vindas permanecem. O aviso **não** entra
aqui.

### `reserva`

Intocada. O aviso viaja com o recado já único por reserva (índice da
F2.2).

---

## Regras de validação (fora do banco)

| Regra | Onde |
| --- | --- |
| `LLM_MODO` ∈ {`controlado`, `real`} | Fábrica, na subida |
| `real` ⇒ chave não vazia | Fábrica, na subida |
| Timeout > 0 | Configuração de plataforma |
| Aviso presente no corpo montado; exatamente uma `?` na última linha | Função pura de boas-vindas |
| Taxonomia e fidelidade ao catálogo | Domínio já existente, depois da porta |

---

## Transições

Nenhuma máquina de estados nova. `hospedado` continua o clique da
recepção. Classificação `indisponivel` / `formato_invalido` /
`duvida_nao_coberta` permanecem os desfechos já gravados.
