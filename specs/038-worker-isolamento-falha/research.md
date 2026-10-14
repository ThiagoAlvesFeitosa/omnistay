# Research: O worker não para por causa de um trabalho

## 1. Isolamento na passagem de mensagens

**Decision**: Cada trabalho da passagem corre num **savepoint**
(`begin_nested`). Exceção inesperada faz rollback só desse savepoint,
grava a falha no trabalho via `registrar_falha_de_envio` já existente
(nome da classe da exceção como código) e a passagem segue no
próximo. Não se introduz fila externa, processo extra nem Celery.

**Rationale**: Hoje `processar_uma_passagem` despacha sem `try` e
`processar_uma_passagem_na_engine` usa **uma** transação para todos
os claims. `IntegrityError` (caso 18/09) aborta a transação inteira:
trabalhos já `concluido` na mesma passagem voltam atrás e o laço do
worker morre. Savepoint preserva o concluído (FR-005), esvazia efeito
parcial do que estourou (idempotência do banco na retentativa) e
continua testável com a conexão que os testes de integração já
passam.

**Alternatives considered**: Uma transação por trabalho via
`engine.begin()` — também isola, mas quebra dezenas de testes que
chamam `processar_uma_passagem(conexao)` e duplica o ciclo de
conexão. Deixar a transação única e só logar — viola FR-005 e o
Artigo IX (o banco já abortou).

## 2. Teto e espera crescente

**Decision**: Reusar `tentativas_maximas` (`tentativas_max_envio_mensagem`,
padrão **5**) e `backoff_apos` (`60s * 2^(tentativas-1)`). MUST NOT
criar chave nova de espera. Valor ausente **ou ilegível** devolve 5
(`int` que falha não propaga). Exceção inesperada entra no mesmo
`registrar_falha_de_envio` que a falha de envio já usa.

**Rationale**: FR-008 e a clarificação de 14/10. O teto já é parâmetro
da propriedade (Artigo XIII). A curva de espera já é regra técnica da
fila; parametrizá-la seria peça sem problema presente (Artigo XI).

**Alternatives considered**: Falhar o ciclo se o teto faltar — recusado
na clarificação. Segunda chave de backoff em `parametro_hotel` —
recusado. Constante nova só para isolamento — duplicaria o teto de
envio.

## 3. Registro sem dado pessoal

**Decision**: `erro_ultima_tentativa` e o log recebem **somente**
`type(exc).__name__`. Nunca `str(exc)`, nunca `orig`, nunca
parâmetros da consulta. Os dois `create_engine` (API em
`app/database.py` e o do worker) passam a `hide_parameters=True`.
Worker deixa de abrir engine “nu”: usa `obter_engine()` (já traz
`statement_timeout` no espírito da API, FR-011).

**Rationale**: Auditoria de 18/09 (achado médio: ficha no erro de
banco) e FR-007. `hide_parameters` está explícito no estado do
projeto e ainda não foi feito.

**Alternatives considered**: Sanitizar a mensagem com regex de CPF —
frágil e ainda vaza endereço/SQL. Logger que corta 200 caracteres —
ainda pode trazer documento.

## 4. Isolamento do ciclo (passagem × rotinas × expurgo)

**Decision**: Extrair `executar_ciclo` do `while True` em
`worker/__main__.py`: cada etapa (passagem, cadastros, boas-vindas,
pulso, mercado, retenção) em `try/except` próprio; no except, log com
nome da exceção e segue. Flags `--uma-passagem` e `--verificar-*`
permanecem pontuais (não disparam o ciclo completo). Testes da US3
chamam `executar_ciclo` com funções injetáveis, sem `sleep`.

**Rationale**: Achados 3.2 / 3.3 / 3.12 da Fase 6: expurgo no mesmo
laço. Sem extrair a função, o isolamento não é testável (Artigo XII)
e o `while True` continua sendo o ponto único de falha.

**Alternatives considered**: Processo à parte só para expurgo — recusado
pelo backlog e Artigo XI. APScheduler — recusado desde a F6.1.

## 5. Distintivos na Fila do dia

**Decision**: Ampliar `vw_fila_do_dia` (revisão Alembic **0026** +
`docs/04-schema.sql`) com JSON das falhas definitivas da reserva:
`status = 'falha'`, `payload.id_reserva` presente e igual, `id_hotel`
da linha. Reserva `encerrado` (saída confirmada) devolve lista vazia.
`coletar_mercado` não tem `id_reserva` — não entra. Tentativa ainda
`pendente`/`processando` não entra. O serviço agrega pela **chave de
omissão** do catálogo (não pelo `tipo` cru) e monta o texto; a tela
só pinta.

**Rationale**: Artigo V + regra da 029 (sinal próprio). Sem destino
novo, sem operação `ciente` (FR-012). Agrupar por omissão atende
FR-017 (“2 mensagens do hóspede sem resposta”).

**Alternatives considered**: Tela ou menu novos — recusado. Boolean
único “tem falha” — perde o tipo e a contagem. Agrupar só por
`trabalho.tipo` — dois tipos de inbound gerariam duas frases iguais
em espírito, contra o exemplo da spec.

## 6. Catálogo de omissões (adiado da spec)

**Decision**: Chave estável + frase no singular e no plural. Contagem
1 = frase singular, sem número. Contagem ≥ 2 = `"{n} " + plural`.
Tipos que compartilham a mesma omissão colapsam.

| Chave | Tipos de trabalho | Singular | Plural (`{n}` prefixado) |
| --- | --- | --- | --- |
| `ficha_nao_processada` | `interpretar_ficha` | Ficha não processada | fichas não processadas |
| `mensagem_hospede_sem_resposta` | `classificar_mensagem`, `responder_duvida`, `registrar_pedido_servico`, `abrir_chamado_reclamacao`, `registrar_resposta_pulso`, `interpretar_pesquisa_saida` | Mensagem do hóspede sem resposta | mensagens do hóspede sem resposta |
| `coleta_nao_enviada` | `enviar_coleta` | Coleta não enviada | coletas não enviadas |
| `lembrete_nao_enviado` | `enviar_lembrete` | Lembrete não enviado | lembretes não enviados |
| `recado_boas_vindas_nao_enviado` | `enviar_boas_vindas` | Recado de boas-vindas não saiu | recados de boas-vindas não saíram |
| `confirmacao_resolucao_nao_enviada` | `enviar_confirmacao_resolucao` | Confirmação de resolução não enviada | confirmações de resolução não enviadas |
| `pulso_nao_enviado` | `enviar_pulso` | Pulso não enviado | pulsos não enviados |
| `pesquisa_saida_nao_enviada` | `enviar_pesquisa_saida` | Pesquisa de saída não enviada | pesquisas de saída não enviadas |
| `lista_pedidos_nao_enviada` | `enviar_lista_pedidos_chat` | Lista de pedidos não enviada | listas de pedidos não enviadas |
| `resposta_recepcao_nao_enviada` | `enviar_resposta_recepcao` | Resposta da recepção não enviada | respostas da recepção não enviadas |

`enviar_boas_vindas` em falha **não** reusa o boolean
`boas_vindas_nao_enviadas` (ausência de trabalho). Texto e cor
diferentes. Tipo sem chave (futuro) **não** inventa frase: omite o
rótulo e permanece só no registro do trabalho (Artigo II / XV).

**Rationale**: Spec pediu o catálogo no plano. Frases descrevem o que
deixou de acontecer, sem nome de exceção.

**Alternatives considered**: Um rótulo genérico “falha na fila” —
opaco para a recepção. Texto no frontend — duplicaria e arriscaria
divergeência com o teste de contrato.

## 7. Superfície do painel

**Decision**: Campo novo `omissoes: { chave, texto, contagem }[]` em
`GET /fila-do-dia`. Sem rota nova, sem item de menu, sem clique que
apague o sinal. Cor **sky** (distinta de vermelho / laranja / âmbar /
violeta da 029). Rótulos todos visíveis na mesma célula de situação.

**Rationale**: FR-012–017. Cliente só renderiza `texto` já montado.

**Alternatives considered**: Query string / segundo GET — Artigo XI e
a 029 já carregam a linha num GET.

## 8. Conformidade do esquema

**Decision**: Revisão `0026` recria `vw_fila_do_dia` (padrão das
0023–0025) e atualiza `docs/04-schema.sql`. Sem coluna nova em
`trabalho`. `0001` congelado. Sem tipo novo no CHECK de `trabalho`.

**Rationale**: Artigo IX — status `falha` já existe; a visão só lê.

**Alternatives considered**: Tabela de “ciência” — operação nova,
recusada.
