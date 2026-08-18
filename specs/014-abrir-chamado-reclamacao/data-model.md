# Modelo de dados — Abrir Chamado de Reclamação

Complementa o esquema já existente. Referência documental: `docs/04-schema.sql`.
Migração prevista: `0013_abrir_chamado_reclamacao`.

Nenhuma tabela nova. Nenhuma coluna nova em `solicitacao`. O delta é o tipo de
trabalho `abrir_chamado_reclamacao`, o índice único correspondente, e a chave
`horas_destaque_chamado_aberto` em `parametro_hotel`. A coluna
`janela_preferencia` já existe desde a revisão `0001` e passa a ser escrita.

---

## Entidades envolvidas

### `mensagem` recebida (já classificada como reclamação técnica)

A linha da reclamação **não** tem o conteúdo alterado. Os eixos da F3.2
permanecem. Esta fatia só estende `classificacao_bruta` quando a intenção é
`reclamacao_tecnica` (após o worker do chamado) ou quando o atalho de janela
grava `janela_registrada` numa recebida posterior.

| Campo | Depois da abertura do chamado |
| --- | --- |
| `conteudo` | **intocado** |
| `intencao` | `reclamacao_tecnica` (já gravado) |
| `sentimento` / `urgencia` | intocados |
| `classificacao_bruta.desfecho` | permanece `classificado` |
| `classificacao_bruta.resposta` | `confirmacao_reclamacao` |
| `classificacao_bruta.id_mensagem_resposta` | id da enviada (confirmação) |
| `classificacao_bruta.id_solicitacao` | id da solicitação tipo reclamação |

JSON **não** inclui o texto da reclamação, o da confirmação nem a janela.
`desfecho` **não** passa a um valor que ligue `precisa_atendimento_humano`.

### Formato de `classificacao_bruta` após a abertura

```json
{
  "tipo": "classificacao_intencao",
  "desfecho": "classificado",
  "intencao": "reclamacao_tecnica",
  "sentimento": "negativo",
  "urgencia": "alta",
  "bruto": {},
  "resposta": "confirmacao_reclamacao",
  "id_mensagem_resposta": 50,
  "id_solicitacao": 7
}
```

`bruto` continua sendo o da **classificação** (F3.2). Sentimento pode ser
`negativo`, `neutro` ou `positivo` — os três abrem chamado.

### `mensagem` recebida posterior (só horário)

Quando o atalho de janela dispara **antes** do LLM:

| Campo | Valor |
| --- | --- |
| `conteudo` | **intocado** |
| eixos estruturados | permanecem vazios |
| `classificacao_bruta.tipo` | `classificacao_intencao` |
| `classificacao_bruta.desfecho` | `janela_registrada` |
| `classificacao_bruta.id_solicitacao` | o chamado já aberto que recebeu a janela |

Não há enviada nova. Não há segunda `solicitacao`.

### `mensagem` enviada (nova linha — confirmação)

| Campo | Valor |
| --- | --- |
| `direcao` | `enviada` |
| `conteudo` | recado padrão (manutenção acionada; pergunta de horário se a janela era desconhecida) |
| `status_envio` | `pendente` → `enviada` (ou `falha` se a mensageria esgotar) |
| classificação | não se preenche |

Gravada **antes** da chamada à porta de envio **e** antes (na transação) do
INSERT em `solicitacao`. O recado não contém fato de catálogo nem prazo de
conserto.

### `solicitacao`

Escrita do tipo `reclamacao`. Pedidos `servico` da F3.4 continuam como estão.

| Campo | Valor nesta fatia |
| --- | --- |
| `id_reserva` | do trabalho |
| `id_mensagem_origem` | a **recebida** da reclamação (não a do horário posterior) |
| `tipo` | `reclamacao` |
| `descricao` | `conteudo` da recebida de origem |
| `numero_quarto` | extraído da origem, ou `NULL` |
| `urgencia` | eixo da mensagem; se nulo, `media` |
| `janela_preferencia` | extraída da origem, ou `NULL`; preenchida depois pelo atalho |
| `status` | `aberta` |
| `id_usuario_responsavel` | `NULL` |
| `aberta_em` | agora |
| `resolvida_em` | `NULL` |

Zero linha em `consumo`. Hotel da linha: o de `reserva.id_hotel` (join).
Unicidade da origem: `uq_solicitacao_mensagem_origem` (já na `0012`).

Completar janela: `UPDATE solicitacao SET janela_preferencia = :janela`
somente se `tipo = 'reclamacao'` AND `status IN ('aberta', 'em_andamento')`
AND `janela_preferencia IS NULL` AND `reserva.id_hotel` do trabalho. A mais
antiga sem janela da reserva. Se já houver janela, no-op.

### `trabalho`

| Campo | Uso |
| --- | --- |
| `tipo` | `abrir_chamado_reclamacao` (novo no CHECK) |
| `payload` | `{id_reserva, id_mensagem}` — `id_mensagem` é a **recebida** da reclamação |
| `status` | `pendente` → `processando` → **`concluido`** após gravar confirmação + solicitação e envio ok. Envio pode reagendar se a mensageria falhar **depois** de gravar |
| Unicidade | `uq_trabalho_abrir_chamado_reclamacao_mensagem` |

`classificar_mensagem` permanece o da F3.2–F3.4, com o acréscimo de inserir
este tipo quando a intenção é `reclamacao_tecnica`, e o atalho de janela
(sem tipo novo).

### `parametro_hotel`

| Chave | Valor semeado | Uso |
| --- | --- | --- |
| `horas_destaque_chamado_aberto` | `2` | horas desde `aberta_em` para destacar reclamação no Alert Center |

Ausência: nenhum destaque; log `prazo_ausente`. Não é editável pela recepção
nesta fatia.

### `reserva`

Status **não** muda. Resolução de hotel: `id_hotel` do trabalho / da sessão.

### `consumo`

Zero linhas criadas nesta fatia.

### `catalogo_item`

Não é lido.

---

## Extração de quarto (reuso)

Função pura já entregue na F3.4. Entrada: texto da recebida de **origem**.
Sem palavra-chave → nulo. Não consulta reserva nem outro hotel.

## Extração de janela (não é coluna nova)

Função pura. Entrada: texto. Saída: string até 60 caracteres ou nulo.

Padrões (casefold), primeiro match, para uso **dentro** de um relato:

- `depois das 16h` / `depois das 16 horas` / `a partir das 14:00`
- `antes das 10h`
- `as 14h` / `às 14h` / `14h` / `14:30`
- `de manha` / `de manhã` / `de tarde` / `a noite` / `à noite`
- `agora` / `o quanto antes` / `imediatamente`

`parece_resposta_de_horario(texto) -> bool`: verdadeiro só quando a mensagem
**inteira**, depois de strip, casa com esses padrões (opcionalmente com
pontuação final). Relato misturado (`o chuveiro tambem vazou, 14h`) → falso.

---

## Projeção HTTP: `GET /solicitacoes`

Consulta inalterada no filtro (hotel da sessão, `status IN ('aberta',
'em_andamento')`, `aberta_em` crescente). SELECT passa a trazer
`janela_preferencia`. `destaque_tempo_excedido` é derivado em
`listar_abertas`:

```text
tipo == reclamacao
AND prazo configurado (inteiro > 0)
AND agora - aberta_em >= prazo
```

Pedido `servico` → `destaque_tempo_excedido = false` sempre nesta fatia.
`vw_fila_do_dia` **inalterada**. Reclamação **não** liga
`precisa_atendimento_humano`.

---

## Delta SQL (congelar na revisão `0013`)

```sql
ALTER TABLE trabalho DROP CONSTRAINT ck_trabalho_tipo;
ALTER TABLE trabalho ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN ('enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
                    'enviar_boas_vindas', 'classificar_mensagem',
                    'responder_duvida', 'registrar_pedido_servico',
                    'abrir_chamado_reclamacao'));

CREATE UNIQUE INDEX uq_trabalho_abrir_chamado_reclamacao_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'abrir_chamado_reclamacao';

INSERT INTO parametro_hotel (id_hotel, chave, valor)
SELECT h.id_hotel, 'horas_destaque_chamado_aberto', '2'
  FROM hotel h
 WHERE NOT EXISTS (
       SELECT 1 FROM parametro_hotel p
        WHERE p.id_hotel = h.id_hotel
          AND p.chave = 'horas_destaque_chamado_aberto'
 );
```

Atualizar o `COMMENT ON TABLE parametro_hotel` com a chave nova.

`downgrade`: CHECK da `0012`; `DROP INDEX` do único novo. Não apaga o parâmetro.

---

## Regras de validação

- Só `reclamacao_tecnica` + `desfecho` inicial `classificado` gera
  `abrir_chamado_reclamacao`.
- Confirmação gravada na transação **antes** do INSERT da solicitação.
- `tipo` da linha desta fatia é sempre `reclamacao`; `consumo` não é inserido.
- `UPDATE` da recebida não inclui `conteudo` no `SET`.
- `id_hotel` do trabalho em toda leitura de reserva/mensagem e no filtro de
  `listar_abertas` / `completar_janela`.
- Conteúdo da reclamação, da confirmação e da janela nunca em log.
- Segundo INSERT `abrir_chamado_reclamacao` para o mesmo `id_mensagem` viola
  o único novo. Segundo INSERT de `solicitacao` com a mesma origem viola o
  único da `0012`.
- Destaque sem prazo configurado: sempre `false`, sem número mágico.

---

## O que não muda nesta fatia

- Máquina de estados da reserva e `fn_valida_transicao_reserva`.
- CHECK de `intencao` / `sentimento` / `urgencia` / `solicitacao.tipo`.
- Colunas de `solicitacao` (já existentes).
- Tabela `consumo` (sem linhas).
- `vw_fila_do_dia` e `precisa_atendimento_humano`.
- Payload de `evento_webhook`.
- Catálogo.
- Contrato público de `abrir_servico`.
