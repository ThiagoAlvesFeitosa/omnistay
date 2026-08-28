# Modelo de dados — linha de convite no recado de boas-vindas

Referência: `docs/04-schema.sql`. Decisões em [research.md](./research.md).
**Nenhuma tabela nova. Nenhuma coluna nova. Nenhuma visão nova.**

---

## Entidade: linha de convite

Não é tabela. É a linha `parametro_hotel` com
`chave = 'boas_vindas_convite'`.

| Campo | Papel |
| --- | --- |
| `id_hotel` | Propriedade dona do convite. Nunca vem do corpo HTTP |
| `chave` | Sempre `boas_vindas_convite` (20 caracteres; cabe em `VARCHAR(60)`) |
| `valor` | Texto **depois** do `strip`. Uma linha. Máximo 255 caracteres Unicode na aplicação (a coluna é `VARCHAR(500)` desde a 0022; esta fatia não afrouxa o teto dos slots) |
| `atualizado_em` | Já existe; o `ON CONFLICT DO UPDATE` o renova |

Uma vigente por propriedade: `UNIQUE (id_hotel, chave)`.

Propriedade recém-instalada **e** hotel já migrado nascem com a linha e
a semente:

```text
Pode perguntar por aqui sobre servicos, cardapio e horarios.
```

Ausência em runtime (DELETE direto, script antigo) trata-se como slot
inválido: o recado **não** sai e a fila do dia acende
`boas_vindas_nao_enviadas`. Não se monta mensagem com linha em branco.

---

## `parametro_hotel` (delta)

| Antes (0022) | Depois (0023) |
| --- | --- |
| COMMENT sem `boas_vindas_convite` | COMMENT inclui a chave, depois de `boas_vindas_checkout` |
| Hotéis sem a linha | `INSERT` da semente por hotel que ainda não a tem |

Sem `ALTER` de tipo. Café, wi-fi, checkout, prazos e
`personalidade_assistente` **não** mudam de chave nem de validação.

Não há `CHECK` extra para o convite: o formato mora no serviço, igual
aos três irmãos. `NOT NULL` já impede `NULL`; vazio `''` no banco é
slot inválido na montagem.

---

## Entidades reusadas (comportamento, esquema intacto)

### Textos de entrada

`boas_vindas_cafe`, `boas_vindas_wifi`, `boas_vindas_checkout` —
inalterados. Passam a ser quatro junto com o convite para o recado
poder sair. A condição de envio é **os quatro** válidos.

### Pacote de boas-vindas (`mensagem`)

`conteudo` da mensagem de chegada passa a terminar com o convite
gravado, depois do aviso de assistente virtual. Colunas intactas.
Unicidade de um recado por reserva intacta (`uq_trabalho_enviar_boas_vindas_reserva`).
Alterar o convite **não** reescreve `conteudo` já enviado.

### Trabalho `enviar_boas_vindas`

Tipo e payload `{id_reserva, id_mensagem}` intactos. Sem campo novo no
JSON: o convite é lido da propriedade na hora de agendar e de enviar,
não copiado no trabalho. Trabalho já concluído não reenvia porque o
convite mudou.

### Fila do dia

Coluna derivada `boas_vindas_nao_enviadas` (hospedado sem trabalho de
boas-vindas) **não muda de SQL**. Convite ausente impede o trabalho de
nascer; a visão já cobre o caso.

### Aviso de assistente virtual

Constante de produto. **Não** é `parametro_hotel`. O PUT de boas-vindas
não o alcança.

---

## Regras de validação (gravação)

A mesma função `validar_texto_de_boas_vindas(campo, valor)` dos três
slots, com `campo="convite"`.

| Regra | Recusa |
| --- | --- |
| `None` | Sim — `Informe o convite.` |
| `\n` ou `\r` | Sim — sem quebra de linha |
| `\t` | Sim — sem tabulação |
| cinco ou mais espaços seguidos (`"     "`) | Sim |
| só espaços após `strip` | Sim — `Informe o convite.` |
| `len(limpo) > 255` | Sim — máximo 255 |
| Perfil ≠ recepção | 403, antes do serviço |
| Hotel da sessão ≠ hotel da linha | Impossível: `id_hotel` só da sessão |

Valor gravado = texto após `strip`. PUT atômico: recusa de um campo
não altera café, wi-fi, checkout nem convite.

---

## Regras de validação (envio)

| Regra | Onde |
| --- | --- |
| Qualquer um dos quatro slots ausente ou inválido → não envia, sinaliza | `agendar_boas_vindas` |
| Os quatro válidos → monta, grava mensagem, enfileira | idem |
| Recuperação na janela de `checkin_em` | Agendador já existente; passa a exigir o quarto slot porque lê a mesma lista de chaves |
| Recado já enviado + convite novo | Nenhum segundo trabalho (índice único) |

---

## Migração `0023_convite_boas_vindas`

1. `INSERT INTO parametro_hotel (id_hotel, chave, valor) SELECT … 'boas_vindas_convite', '<semente>'` para hotel sem a chave
2. `COMMENT ON TABLE parametro_hotel` com a chave na lista
3. `docs/04-schema.sql` no mesmo commit

Downgrade: `DELETE FROM parametro_hotel WHERE chave = 'boas_vindas_convite'`
e COMMENT anterior (o da 0022). Não se reescreve recado já enviado.
