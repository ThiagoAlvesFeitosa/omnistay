# Modelo de dados — personalidade da assistente

Referência: `docs/04-schema.sql`. Decisões em [research.md](./research.md).
**Nenhuma tabela nova.** Uma chave nova e o alargamento de `valor`.

---

## Entidade: descrição de tom

Não é tabela. É a linha `parametro_hotel` com
`chave = 'personalidade_assistente'`.

| Campo | Papel |
| --- | --- |
| `id_hotel` | Propriedade dona do tom. Nunca vem do corpo HTTP |
| `chave` | Sempre `personalidade_assistente` (24 caracteres; cabe em `VARCHAR(60)`) |
| `valor` | Texto do tom **depois** do `strip`. `''` = voz padrão. Máximo 500 caracteres Unicode |
| `atualizado_em` | Já existe; o `ON CONFLICT DO UPDATE` o renova |

Uma vigente por propriedade: `UNIQUE (id_hotel, chave)`.

Propriedade recém-instalada e hotel já migrado **nascem com a linha**,
valor `''`. Ausência em runtime (hotel criado por script antigo sem a
chave) trata-se como `''` na composição — não derruba o worker.

---

## `parametro_hotel` (delta)

| Antes (0001…0021) | Depois (0022) |
| --- | --- |
| `valor VARCHAR(255) NOT NULL` | `valor VARCHAR(500) NOT NULL` |
| COMMENT sem `personalidade_assistente` | COMMENT inclui a chave |

Slots de boas-vindas, prazos e durações **não** mudam de chave nem de
validação de aplicação. Só passam a caber, no banco, em coluna mais
larga.

Não há `CHECK` extra: o teto é o tipo. Vazio `''` satisfaz `NOT NULL`.

---

## Entidades reusadas (intocadas)

### `mensagem`

O `conteudo` da resposta automática de dúvida coberta pode soar
diferente com tom preenchido. Colunas e JSON de classificação **não**
ganham campo de tom. O tom **não** vai para log.

### `trabalho`

Tipo `responder_duvida` inalterado. Sem payload novo: o tom é lido da
propriedade na hora de processar, não copiado no JSON do trabalho.
Trabalho já em curso usa o valor vigente na leitura — não se reprocessa
mensagem já respondida porque o tom mudou (FR-013).

### Recado de boas-vindas

Constante de produto. **Não** é `parametro_hotel`. O PUT de tom não a
altera.

---

## Regras de validação (gravação)

| Regra | Onde |
| --- | --- |
| `strip` nas extremidades | Serviço de `propriedade` |
| Só espaços → `''` | Serviço |
| `len(texto) > 500` → recusa, sem recorte | Serviço; banco recusa o excesso via `VARCHAR(500)` |
| `\n`, `\r`, `\t` aceitos | Serviço |
| Outro `Cc` (inclui nulo) → recusa | Serviço |
| Perfil ≠ gestão → 403 | Política, antes do serviço |
| Hotel da sessão ≠ hotel da linha | Impossível: `id_hotel` só da sessão |

## Regras de validação (composição)

| Regra | Onde |
| --- | --- |
| Tom lido do hotel da **reserva** | `processar_trabalho_responder_duvida` |
| Tom não entra em classificar / ficha / item / pesquisa | Chamadas da porta |
| Redação não fiel → `nao_fiel` (aviso + humano) | `resposta_fiel_ao_catalogo` já existente |
| Sem retry, sem “limpar e enviar” | Serviço de conversa |

---

## Migração

Revisão `0022_personalidade_assistente`, depois de `0021_expurgo_retencao`.

1. `ALTER TABLE parametro_hotel ALTER COLUMN valor TYPE VARCHAR(500);`
2. `INSERT` da chave `personalidade_assistente` com `''` para cada
   `hotel` que ainda não a tenha (molde dos `INSERT` da `0008`)
3. `COMMENT ON TABLE parametro_hotel` com a chave na lista
4. Espelho em `docs/04-schema.sql` (tipo, comentário)

Downgrade desta fatia não é necessário para o ciclo: o projeto não
reverte revisões em produção acadêmica. O arquivo `downgrade` pode
encolher a coluna **só se** nenhum valor passar de 255 — fora do
caminho feliz; documentar no SQL e não exercitar na suíte.

---

## Inventário que o teste de conformidade passa a exigir

- Tipo de `parametro_hotel.valor` = `character varying(500)`
- Comentário da tabela cita `personalidade_assistente`
- Hotel do bootstrap tem a chave com valor vazio
