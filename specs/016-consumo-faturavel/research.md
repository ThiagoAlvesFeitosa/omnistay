# Pesquisa — F3.7 Consumo Faturável e Fila de Lançamento

Decisões técnicas tomadas antes de escrever teste. Cada uma traz o que foi escolhido, por
quê, e o que foi recusado. Nada aqui é preferência estética: tudo tem consequência em teste
ou em risco operacional.

---

## 1. Sem tipo novo de trabalho; o processador da F3.4 ganha um fork

**Decisão:** `classificar_mensagem` continua enfileirando só
`registrar_pedido_servico` quando a intenção é `pedido_de_servico`. Não nasce
`identificar_item` nem `registrar_consumo_faturavel` na fila. O processador já
existente, **antes** de `abrir_servico`, lista os itens vendáveis ativos do hotel
e identifica. Três saídas:

| Identificação | O que acontece |
| --- | --- |
| `unico` (um `id` ativo daquele hotel) | confirmação com valor → `abrir_consumo` |
| `nenhum` (lista vazia, ou o modelo não casa com nenhum) | caminho F3.4 inalterado (`abrir_servico`, sem valor) |
| `ambiguo` / porta indisponível / formato inválido | aviso **sem** preço, `desfecho` humano, zero `solicitacao` |

Inventário conhecido que esta fatia mexe:

| Teste atual | Destino nesta fatia |
| --- | --- |
| Unitários de `registrar_pedido` que prometem zero LLM | **Invertem**: o ramo passa a identificar quando há item ativo. Caso sem item vendável continua sem chamar a porta |
| `test_registrar_pedido` / integração toalha extra | Permanecem: zero `consumo`, confirmação sem preço |
| Passagem com `pedido_de_servico` + item vendável “Cerveja” | **Nova**: tipo `consumo`, valor praticado, pendente |
| F3.6 `tipo = consumo` → `409` | **Inverte**: resolve o quarto; lançamento segue `pendente` |
| `test_pedido_e_reclamacao_nao_enfileiram_responder` | Inalterado |

Caminho idempotente: se o JSON da recebida já tem `resposta` em
`confirmacao_consumo` / `confirmacao_pedido` / `aviso_identificacao`, não
identifica de novo e não insere segunda enviada. Falha de envio retoma só a
mensageria.

**Rationale:** Artigo XI — tipo novo na fila só se o claim/retry for outro. Aqui
o trabalho continua “registrar o pedido classificado”. A F3.2 prometeu decidir,
não executar: classificar **não** identifica. Lista vazia não chama a porta
(espelho F3.3).

**Alternativas recusadas:** trabalho `identificar_item_vendavel` em cascata —
hop extra e allowlist nova sem problema de retry distinto; enfileirar consumo já
na classificação — a classificação não conhece o catálogo vendável e misturaria
F3.2 com preço; intenção nova `pedido_de_consumo` no classificador — a spec
proíbe; abrir consumo dentro de `classificar_mensagem` — quebra os testes da
F3.2 que proíbem execução.

---

## 2. `LLMProvider.identificar_item_vendavel`; o modelo não emite preço

**Decisão:** a porta ganha um quarto método. Identificação **não** reusa
`classificar` nem `responder_duvida`.

```text
identificar_item_vendavel(texto, itens_ativos) -> ResultadoIdentificacao
  desfecho: unico | nenhum | ambiguo
  id_item_vendavel: int | None
  quantidade: int          # só quando unico; inteiro >= 1
```

`itens_ativos` é uma tupla de `(id_item_vendavel, nome)` **sem preço**. O domínio
valida: `unico` exige `id` pertencente à tupla daquele hotel e `quantidade >= 1`;
qualquer outro formato vira `FalhaDeIdentificacao` (equivalente a indisponível).
Dois ids, id inexistente, id de item inativo ou de outro hotel → não é `unico`.

Indisponível / recusa / tempo esgotado: `FalhaDeIdentificacao(codigo)` — distinta
das três falhas já existentes. Código sem eco do texto.

Lista ativa **vazia:** o serviço **não** chama a porta; desfecho `nenhum` →
serviço operacional. Chamar o modelo sem itens é convite a inventar produto.

**Quantidade.** O valor praticado é `preco_atual * quantidade`. O falso da suíte
devolve quantidade configurável (padrão 1). Quantidade inválida → humano, não
arredonda. Vários **itens distintos** na mesma mensagem → `ambiguo` (limitação
honesta; a spec admite um consumo por mensagem).

**Rationale:** desenho adiado na F2.1 e FR-003 / FR-024. Modelo que não emite
número não erra número. Artigo II para ambíguo e queda. Artigo XV para um item
por mensagem.

**Alternativas recusadas:** extrair o preço do texto corrido de `catalogo_item`
— exatamente o risco financeiro que a F2.1 adiou; pedir ao modelo um `valor` —
hóspede informado de um número e cobrado de outro; `CatalogoRepository` passando
a devolver preço — a porta de fatos afirmáveis não é lista de cobrança; regex de
cardápio — paráfrase (“loura” vs “cerveja”) falha do mesmo modo que a busca de
dúvida.

---

## 3. Tabela `item_vendavel`; não é coluna de `catalogo_item`

**Decisão:** tabela nova, governada por `propriedade`, irmã de `catalogo_item`
e **não** uma categoria nova dele.

| Campo | Papel |
| --- | --- |
| `id_item_vendavel` | o que a porta devolve; entra no prompt como identificador |
| `id_hotel` | multi-tenant |
| `nome` | rótulo no prompt e em `consumo.descricao_item` |
| `preco_atual` | `NUMERIC(10,2) >= 0` — só o preço vigente |
| `ativo` | desativar não apaga |
| `atualizado_em` | manutenção |

Índice único parcial `(id_hotel, lower(nome)) WHERE ativo` — dois “Cerveja”
ativos no mesmo hotel tornariam toda identificação ambígua. Recepção recebe
recusa ao cadastrar nome duplicado ativo.

CRUD HTTP em `/itens-vendaveis`, operações já existentes `alterar_catalogo` /
`ler_catalogo` (mesmas pessoas da F2.1). Staff recusado. Gestão lê e não altera.
Sem `DELETE`. Prompt montado na hora a partir das linhas ativas; nenhuma cópia
intermediária.

`consumo.valor_praticado` **não** referencia `id_item_vendavel`. Reajuste
posterior muda `preco_atual` e não toca linhas de `consumo` (não há FK de
histórico). Opcional gravar `id_item_vendavel` no JSON da recebida para auditoria
da identificação — **não** no valor.

**Rationale:** F2.1 e Artefato 4 §3. Preço em texto corrido obriga o modelo a
ler número. Artigo IX: `CHECK` de não negativo no item e no consumo. Artigo XIV:
`id_hotel` na tabela nova.

**Alternativas recusadas:** `preco` nulável em `catalogo_item` — mistura fato
afirmável com cobrança e fura o CHECK de categoria; reusar `conteudo` com “R$”
— a IA extraíria o número; tabela no módulo `atendimento` — o item é cadastro da
propriedade, o consumo é a especialização da solicitação.

---

## 4. Confirmação com o valor lido; `abrir_consumo` na mesma transação

**Decisão:** ordem, **antes** do envio, na mesma transação:

1. Listar itens ativos; identificar (ou pular a porta se a lista for vazia).
2. Se `unico`: ler `preco_atual` **uma vez**; `valor_praticado = preco * quantidade`.
3. Inserir `mensagem` `enviada` com recado padrão (`montar_confirmacao_consumo`)
   contendo esse valor formatado (`R$ 12,00`). Sem “extrato”, sem “conta”, sem
   afirmar que o lançamento no sistema de gestão já ocorreu.
4. `abrir_consumo` — INSERT `solicitacao` tipo `consumo` **e** INSERT `consumo`
   `status_lancamento = pendente`, `descricao_item` = nome (máx. 160), valor
   praticado, autor/instante de lançamento nulos.
5. Atualizar o JSON da **recebida**: `resposta = confirmacao_consumo`,
   `id_mensagem_resposta`, `id_solicitacao`, `id_item_vendavel`, `quantidade`.
   `desfecho` permanece `classificado`.
6. `enviar_texto_sessao`.

Passo 3 antes do 4: nunca existe consumo desta origem sem a confirmação já
gravada (Artigo VI). Os dois commitam juntos; o envio é depois (Artigo III).

`conversa` **não** importa `atendimento` nem `propriedade` no topo que crie
ciclo: o worker injeta `listar_itens_ativos`, `identificar`, `abrir_consumo`
(padrão da ficha e do pedido). `abrir_consumo` recebe o valor já lido — não
releitura entre confirmação e INSERT (READ COMMITTED poderia ver reajuste no
meio).

Quarto: a mesma `extrair_numero_quarto` da F3.4. Urgência: eixo já gravado.

**Rationale:** FR-002 a FR-008; Artigo III e VI. Teste unitário de `conversa`
injeta identificador e `abrir_consumo` falsos e verifica a ordem.

**Alternativas recusadas:** criar `consumo` só depois do envio ok — some se a
mensageria falhar (FR-020); deixar o modelo redigir a confirmação — pode
inventar prazo ou dizer que já lançou; template Utility — o hóspede acabou de
escrever.

---

## 5. Ambíguo / indisponível: aviso sem preço e flag na fila do dia

**Decisão:** não cair no caminho da toalha (viraria cerveja grátis) e não
inventar valor. Recado padrão (`montar_aviso_identificacao`): prenome +
“recebemos sua mensagem; a recepção vai conferir”. Sem número. Sem “extrato”.

JSON da recebida: `desfecho = item_ambiguo` ou `identificacao_indisponivel`,
`resposta = aviso_identificacao`. Trabalho `concluido`.
`vw_fila_do_dia.precisa_atendimento_humano` inclui esses dois valores no `IN`
já usado por `duvida_nao_coberta`.

Não se cria `solicitacao`. Não se liga o flag no caminho `unico` nem no
`nenhum`.

**Rationale:** FR-006, Artigo II e VI (o hóspede não fica em silêncio). O flag
já é o que a recepção lê; não se inventa coluna persistida.

**Alternativas recusadas:** tratar ambíguo como serviço — prejuízo silencioso;
confirmar “vamos ver o preço” com número chutado; `solicitacao` sem `consumo`
para o humano completar o valor — fura o NOT NULL de `valor_praticado` e a
especialização.

---

## 6. Fila destacada HTTP; `GET /solicitacoes` ganha valor opcional

**Decisão:** `GET /consumos/pendentes` lista só `consumo.status_lancamento =
pendente` da propriedade, **independente** de `solicitacao.status`. Consumo já
resolvido no quarto continua na passagem de turno financeira até lançar ou
dispensar.

Operação: `ler_solicitacao_atribuida` (recepção, staff, gestão). Staff vê a
pendência para entregar; **não** consegue POST de lançamento. Mesmo JSON para
os três: `id_solicitacao`, `id_reserva`, `descricao`, `descricao_item`,
`numero_quarto`, `valor_praticado`, `status_lancamento`, `aberta_em`,
`resolvida_em`. **Sem** ficha.

`GET /solicitacoes` (abertas / em andamento) ganha `valor_praticado` e
`status_lancamento` — nulos em reclamação e serviço, preenchidos em consumo.
Testes da F3.4/F3.5 que não esperavam as chaves passam a aceitá-las nulas.

Não entra em `vw_fila_do_dia`. Toalha **não** aparece em `/consumos/pendentes`.

**Rationale:** FR-009, FR-015; Artigo IV e V. Lista misturada com toalha era o
defeito da spec. `id_reserva` continua não sendo ficha.

**Alternativas recusadas:** filtrar `GET /solicitacoes?tipo=consumo` — resolvido
no quarto sairia da passagem de turno financeira; visão SQL nova — a consulta
com JOIN já existente basta (Artigo XI); campo em `GET /fila-do-dia` — mistura
cadastro do dia com prejuízo de lançamento e staff não lê essa rota.

---

## 7. `lancar_consumo` no POST; dispensar reusa a mesma operação

**Decisão:** duas rotas, uma operação:

| Rota | Efeito |
| --- | --- |
| `POST /solicitacoes/{id}/lancamento` | `pendente` → `lancado` + autor + instante |
| `POST /solicitacoes/{id}/dispensa` | `pendente` → `dispensado` + os **mesmos** campos de autor/instante |

`id_usuario_lancamento` e `lancado_em` significam “quem tirou da fila de
pendência e quando”. `status_lancamento` distingue lançado de dispensado.
Gestão e staff: `403`. Hotel B: `404` uniforme. Já terminal: `409`. Não é
consumo / não existe: `404`.

Nenhum recado ao hóspede. Nenhum efeito em `solicitacao.status`. Valor
praticado intocado.

CHECK: estado terminal (`lancado` ou `dispensado`) exige autor e instante.
Trigger: só `pendente` → `lancado` ou `pendente` → `dispensado`. Relógio já
usado na resolução.

**Rationale:** FR-010 a FR-014; matriz F0.3 já reservou `lancar_consumo` à
recepção. Dispensar é disposição financeira, não execução no quarto — mesma
autoridade. Artigo XV: cortesia não mente “lançado”. Artigo IX: transição no
banco.

**Alternativas recusadas:** operação nova `dispensar_consumo` — mesma matriz,
Artigo XI; colunas `id_usuario_dispensa` — duplicata; staff lançar — quebra a
ponte humana da recepção e a sessão longa; gestão lançar — altera domínio.

---

## 8. Resolver tipo `consumo` sem implicar lançamento

**Decisão:** `POST /solicitacoes/{id}/resolucao` passa a aceitar `tipo IN
('reclamacao', 'servico', 'consumo')`. O `409` “deste tipo não pode” **sai**.
Recado de conclusão do consumo reusa o espírito do serviço (“pedido atendido”)
e **não** cita valor, lançamento, “extrato” nem “conta”.

`GET /solicitacoes` perde o item resolvido; `GET /consumos/pendentes` **não**.
Autor da resolução e autor do lançamento são fatos distintos.

**Rationale:** FR-016 / SC-010; a F3.6 deixou consumo de fora porque a linha
ainda não existia. Dois ciclos (quarto vs PMS).

**Alternativas recusadas:** consumo só sair das duas filas no lançamento —
Alert Center eterno depois da entrega; lançar no mesmo POST de resolver —
esconde a quarta travessia.

---

## 9. Especialização no banco; `consumo` deixa de ser tabela morta

**Decisão:** a tabela `consumo` já existe na `0001`. Esta revisão não a recria.
Acrescenta garantias:

1. Trigger `BEFORE INSERT OR UPDATE` em `consumo`: o pai MUST ter `tipo =
   consumo`.
2. Constraint trigger `DEFERRABLE INITIALLY DEFERRED` em `solicitacao`: se
   `tipo = consumo`, MUST existir filho ao commit.
3. CHECK de autor/instante para **qualquer** estado terminal (substitui o CHECK
   só de `lancado`).
4. Trigger de transição de `status_lancamento` (seção 7).
5. `DROP`/`CREATE` de `vw_fila_do_dia` com `item_ambiguo` e
   `identificacao_indisponivel` no `IN` de `precisa_atendimento_humano`.

`uq_solicitacao_mensagem_origem` já impede segundo consumo da mesma mensagem.
Não há tipo novo em `ck_trabalho_tipo`.

`downgrade` remove triggers, CHECK novo, tabela `item_vendavel` e devolve a
visão à `0014`. Teste de conformidade nos dois sentidos + testes das triggers.

**Rationale:** Artigo IX. A F3.4 adiou a trigger “filho só se tipo consumo”
justamente para esta fatia.

**Alternativa recusada:** CREATE da tabela nesta revisão — ela já está no
esquema inicial; recriá-la divergiria do `04-schema.sql` vivo.

---

## 10. Log: resultado e identificadores; nunca pedido, confirmação ou nome do item como texto livre do hóspede

**Decisão:** eventos `consumo_registrado`, `consumo_ja_registrado`,
`consumo_envio_falhou`, `identificacao_humana`, `consumo_lancado`,
`consumo_dispensado`. Campos: ids (`trabalho`, `mensagem`, `reserva`, `hotel`,
`solicitacao`, `item_vendavel`), `resultado`, `status_lancamento` quando
couber. Ausentes: `conteudo`, texto da confirmação, `descricao`, telefone,
valor por extenso no recado. `valor_praticado` **não** vai para log — o
identificador do consumo basta e evita eco de pedido.

**Rationale:** FR-021, Artigo VIII.

---

## 11. O que esta pesquisa não reabre

- Taxonomia e desfechos da F3.2 (além dos dois desfechos humanos novos).
- Conversação / fidelidade ao catálogo de fatos (F3.3).
- Pedido sem cobrança como caminho default na ausência de item (F3.4).
- Reclamação e janela (F3.5).
- Resolver reclamação/serviço e o recado de conclusão deles (F3.6).
- Lista ao hóspede no checkout (F4.2).
- Integração com o PMS (Artigo I).
- Intenção `pedido_de_consumo` no classificador.
- Adaptador real de IA ou de WhatsApp na suíte.
- Tela React e `GET` de histórico da conversa.
- Texto da confirmação como `parametro_hotel`.
- Operação nova na matriz (`lancar_consumo`, `alterar_catalogo` e
  `ler_catalogo` já existem).
