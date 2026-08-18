# Modelo de dados — Resolver Chamado e Confirmar

Complementa o esquema já existente. Referência documental: `docs/04-schema.sql`.
Migração prevista: `0014_resolver_chamado`.

Nenhuma tabela nova. Nenhuma coluna nova. O delta é o tipo de trabalho
`enviar_confirmacao_resolucao`, o índice único correspondente, o trigger de
transição de `solicitacao.status`, e o CHECK de autor na resolução. As colunas
`status`, `id_usuario_responsavel` e `resolvida_em` já existem desde a revisão
`0001` e passam a ser escritas neste recorte.

---

## Máquina de estados de `solicitacao` (esta fatia)

```text
aberta ──────────────┐
                     ├──► resolvida   (terminal nesta fatia)
em_andamento ────────┘
```

| De | Para | Quem dispara | Recusado |
| --- | --- | --- | --- |
| `aberta` | `resolvida` | `POST .../resolucao` | — |
| `em_andamento` | `resolvida` | o mesmo POST | — |
| `resolvida` | qualquer | — | sim (aplicação `409` + trigger) |
| qualquer | `cancelada` | — | sim nesta fatia |
| `aberta` | `em_andamento` | — | sim nesta fatia (sem clique de atribuir) |

`tipo = consumo` não transita por esta operação (recusa `409`), mesmo que o
status seja `aberta`.

O CHECK já existente `status <> 'resolvida' OR resolvida_em IS NOT NULL`
permanece. Acrescenta-se o irmão do autor:

```text
status <> 'resolvida' OR id_usuario_responsavel IS NOT NULL
```

---

## Entidades envolvidas

### `solicitacao` (UPDATE)

Somente linhas do hotel da sessão, `tipo IN ('reclamacao', 'servico')`,
`status IN ('aberta', 'em_andamento')`.

| Campo | Depois da resolução |
| --- | --- |
| `status` | `resolvida` |
| `resolvida_em` | instante do clique (`relogio.agora()`) |
| `id_usuario_responsavel` | `id_usuario` da sessão que clicou |
| `descricao`, quarto, janela, urgência, origem | **intocados** |
| `tipo` | intocado |

Zero linha em `consumo`. Hotel da linha: join com `reserva.id_hotel` (não há
`id_hotel` em `solicitacao`).

`GET /solicitacoes` continua filtrando `status IN ('aberta', 'em_andamento')`:
a linha resolvida **sai da passagem de turno** sem mudança de consulta.

Completar janela (F3.5) já restringe a `aberta` / `em_andamento`: chamado
resolvido **não** ganha janela depois.

### `mensagem` enviada (nova linha — confirmação de resolução)

Inserida **na mesma transação do UPDATE**, antes do commit do POST, **antes**
da chamada à porta de envio (que é do worker).

| Campo | Valor |
| --- | --- |
| `direcao` | `enviada` |
| `conteudo` | recado padrão (`montar_confirmacao_resolucao`) |
| `status_envio` | `pendente` → `enviada` (ou `falha` se a mensageria esgotar) |
| `classificacao_bruta.tipo` | `confirmacao_resolucao` |
| `classificacao_bruta.id_solicitacao` | a solicitação recém-resolvida |

JSON **não** inclui o texto do recado nem a descrição do chamado. Eixos de
intenção **não** se preenchem (não é classificação de entrada).

### `trabalho`

| Campo | Uso |
| --- | --- |
| `tipo` | `enviar_confirmacao_resolucao` (novo no CHECK) |
| `payload` | `{id_reserva, id_solicitacao, id_mensagem}` — só IDs |
| `status` | `pendente` → `processando` → **`concluido`** após envio ok. Envio pode reagendar se a mensageria falhar **depois** de gravar |
| Unicidade | `uq_trabalho_enviar_confirmacao_resolucao_solicitacao` |

Não existe tipo `resolver_solicitacao` na fila: o clique já resolveu.

### `reserva` e `usuario`

Intocados. Status da reserva (hospedado ou encerrado) **não** entra no
`UPDATE`. `id_usuario_responsavel` referencia `usuario` já existente; o
usuário é o da sessão, do mesmo hotel (a sessão já é da propriedade).

### `parametro_hotel`

Intocado. O prazo de destaque continua valendo só para o que ainda está
aberto na listagem.

---

## Validação

| Regra | Onde mora |
| --- | --- |
| Só `reclamacao` e `servico` fecham aqui | `UPDATE` condicional + `409` se outro tipo no hotel |
| Hotel da sessão | `JOIN reserva` no `UPDATE` / no `SELECT` de recusa; outro hotel → 0 linhas → `404` |
| Autor e instante obrigatórios em `resolvida` | CHECK (instante já existia; autor nesta revisão) + preenchimento no `UPDATE` |
| Não reabrir / não cancelar por este caminho | trigger de transição |
| Um aviso por solicitação | unique parcial do trabalho + processador não reinsere mensagem |
| Payload da fila sem dado pessoal | só IDs |

---

## Relacionamentos

```text
usuario 1 ─── * solicitacao (id_usuario_responsavel, preenchido na resolução)
reserva 1 ─── * solicitacao
solicitacao 1 ─── 0..1 trabalho (enviar_confirmacao_resolucao, unique)
solicitacao 1 ─── 0..1 mensagem enviada (confirmacao_resolucao no JSON)
```

A mensagem de **origem** (`id_mensagem_origem`) permanece a da abertura
(F3.4/F3.5). A confirmação de resolução é outra linha, enviada.

---

## Inventário de esquema (delta da `0014`)

| Objeto | Ação |
| --- | --- |
| `ck_trabalho_tipo` | inclui `enviar_confirmacao_resolucao` |
| `uq_trabalho_enviar_confirmacao_resolucao_solicitacao` | CREATE UNIQUE INDEX parcial |
| `fn_valida_transicao_solicitacao` + `tg_valida_transicao_solicitacao` | CREATE |
| `ck_solicitacao_resolvida_tem_responsavel` | ADD CHECK |
| `docs/04-schema.sql` | o mesmo delta, documento vivo |
| tabelas / colunas | nenhuma |
