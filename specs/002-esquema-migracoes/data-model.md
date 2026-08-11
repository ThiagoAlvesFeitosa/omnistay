# Modelo de dados — Esquema e Migrações

O detalhamento de campos, tipos e restrições vive em `docs/04-schema.sql`, que é a fonte de onde
sai o SQL da migração. Este documento não o repete: registra o que a fatia precisa saber para
planejar a implementação e os testes — as entidades por domínio, as garantias que o banco impõe
por conta própria e o ciclo de vida que a trigger protege.

## Entidades por domínio

| Domínio | Tabelas | Observação |
| --- | --- | --- |
| Propriedade | `hotel`, `usuario`, `parametro_hotel`, `catalogo_item` | `hotel` é a raiz do particionamento; `parametro_hotel` é onde vivem os prazos operacionais |
| Hospedagem | `hospede`, `reserva`, `reserva_hospede`, `consentimento` | `reserva` nasce antes de existir ficha; `consentimento` é histórico, nunca atualizado |
| Conversa | `mensagem`, `evento_webhook` | `evento_webhook` guarda o payload bruto e é onde mora a idempotência |
| Atendimento | `solicitacao`, `consumo` | `consumo` é especialização de `solicitacao` com chave primária compartilhada |
| Feedback | `avaliacao` | Uma avaliação por reserva e origem |
| Mercado | `concorrente`, `coleta_mercado` | Série temporal: cada coleta insere, nunca atualiza |

Apoio: a visão `vw_fila_do_dia`, que alimenta a tela inicial do turno da recepção e expõe a
coluna derivada `chegada_nao_confirmada`.

Multi-tenant: `id_hotel` está presente em `usuario`, `parametro_hotel`, `catalogo_item`,
`reserva` e `concorrente`. As demais tabelas alcançam a propriedade por referência a essas.

## Garantias que o banco impõe

São a razão de ser da User Story 2. Cada linha é uma proteção que sobrevive a script de correção
e a acesso direto ao banco.

### Domínio de valor (`CHECK`)

| Tabela | Restrição | Valores aceitos |
| --- | --- | --- |
| `usuario` | `ck_usuario_perfil` | `recepcao`, `staff`, `gestor` |
| `catalogo_item` | `ck_catalogo_categoria` | `horario`, `cardapio`, `servico`, `programacao`, `regra` |
| `hospede` | `ck_hospede_tipo_documento` | nulo, `rg`, `cpf`, `passaporte` |
| `reserva` | `ck_reserva_status` | os sete estados do ciclo de vida abaixo |
| `mensagem` | `ck_mensagem_direcao` | `recebida`, `enviada` |
| `mensagem` | `ck_mensagem_intencao` | nulo ou uma das seis intenções catalogadas |
| `mensagem` | `ck_mensagem_sentimento` | nulo, `positivo`, `neutro`, `negativo` |
| `mensagem` | `ck_mensagem_urgencia` | nulo, `baixa`, `media`, `alta` |
| `mensagem` | `ck_mensagem_status_envio` | nulo, `pendente`, `enviada`, `entregue`, `falha` |
| `solicitacao` | `ck_solicitacao_tipo` | `reclamacao`, `servico`, `consumo` |
| `solicitacao` | `ck_solicitacao_urgencia` | `baixa`, `media`, `alta` |
| `solicitacao` | `ck_solicitacao_status` | `aberta`, `em_andamento`, `resolvida`, `cancelada` |
| `consumo` | `ck_consumo_status` | `pendente`, `lancado`, `dispensado` |
| `consentimento` | `ck_consentimento_finalidade`, `ck_consentimento_origem` | finalidade única e três origens |
| `avaliacao` | `ck_avaliacao_origem` | `pulso_segundo_dia`, `checkout` |

### Coerência entre campos (`CHECK`)

| Tabela | Restrição | Regra |
| --- | --- | --- |
| `reserva` | `ck_reserva_datas` | saída posterior à entrada |
| `reserva` | `ck_reserva_checkout_apos_checkin` | não se sai antes de entrar |
| `reserva` | `ck_reserva_encerrada_tem_checkin` | não se encerra quem não chegou |
| `hospede` | `ck_hospede_nascimento_passado` | nascimento no passado |
| `solicitacao` | `ck_solicitacao_resolvida_tem_data` | resolvida exige momento da resolução |
| `consumo` | `ck_consumo_valor_nao_negativo` | valor praticado ≥ 0 |
| `consumo` | `ck_consumo_lancado_tem_autor` | lançamento exige autor e momento |
| `avaliacao` | `ck_avaliacao_nota` | nota entre 1 e 5, ou nula |
| `coleta_mercado` | `ck_coleta_preco_nao_negativo`, `ck_coleta_nota_media`, `ck_coleta_sucesso_tem_dado` | coleta bem-sucedida traz ao menos um dado |

### Unicidade

| Restrição | Protege |
| --- | --- |
| `evento_webhook.id_externo UNIQUE` | **A idempotência do sistema inteiro.** Reenvio do WhatsApp falha na inserção e é descartado |
| `usuario.email UNIQUE` | Identidade de login |
| `uq_parametro_hotel_chave` | Uma configuração por chave e propriedade |
| `uq_hospede_documento` (parcial) | Documento repetido, quando informado |
| `uq_reserva_hospede` | Hóspede repetido na mesma reserva |
| `uq_reserva_um_titular` (parcial) | Mais de um titular por reserva |
| `uq_avaliacao_reserva_origem` | Duas respostas ao mesmo pulso |

## Ciclo de vida da reserva

A trigger `tg_valida_transicao_reserva` roda `BEFORE UPDATE OF status` e recusa qualquer
transição fora deste grafo. Mudança de um estado para ele mesmo é aceita sem verificação.

```text
aguardando_cadastro ──> ficha_recebida ──────┐
                   ├──> ficha_parcial ───────┼──> hospedado ──> encerrado
                   ├──> sem_cadastro_previo ─┘
                   └──> cancelada
ficha_recebida | ficha_parcial | sem_cadastro_previo ──> cancelada
```

Nenhuma outra transição é alcançável. `hospedado` não volta para nenhum estado anterior, e
`encerrado` e `cancelada` são terminais.

Casos que os testes desta fatia exercitam:

| Transição | Resultado esperado |
| --- | --- |
| `aguardando_cadastro` → `ficha_recebida` | Aceita |
| `ficha_recebida` → `hospedado` | Aceita |
| `hospedado` → `encerrado` | Aceita |
| `aguardando_cadastro` → `hospedado` | Recusada pela trigger |
| `encerrado` → `hospedado` | Recusada pela trigger |
| `hospedado` → `cancelada` | Recusada pela trigger |

## Registro de versão do esquema

A tabela `alembic_version` é criada e mantida pela ferramenta de migração, não pelo documento de
referência. Ela é o que atende à FR-008, e é a única tabela do banco que **não** deve aparecer na
comparação de inventários — o lado de referência, aplicado direto do documento, não a tem.
