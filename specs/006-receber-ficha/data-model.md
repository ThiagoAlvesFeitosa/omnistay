# Modelo de dados — Receber e Interpretar a Ficha

Complementa o esquema já existente. Referência documental: `docs/04-schema.sql`.
Migração prevista: `0006_interpretar_ficha` (número efetivo = próximo livre no Alembic).

---

## Entidades envolvidas

### `evento_webhook` (reuso)

| Campo | Uso nesta fatia |
| --- | --- |
| `id_externo` | Idempotência do reenvio do canal (`UNIQUE`) |
| `payload` | Corpo bruto (DPC); não vai para log |
| `recebido_em` | Auditoria de chegada |

**Regra**: segunda inserção com o mesmo `id_externo` falha no banco; a API traduz em
`200` sem novo efeito.

### `mensagem` (entrada)

| Campo | Valor nesta fatia |
| --- | --- |
| `direcao` | `recebida` |
| `conteudo` | Texto livre do hóspede (ou marcador de mídia sem texto, se necessário para trilha) |
| `id_externo` | Id da mensagem no canal, quando houver |
| `classificacao_bruta` | Resultado da extração (preenchido pelo worker) |
| `status_envio` | `NULL` (só saída exige status) |
| `intencao` / `sentimento` / `urgencia` | Permanecem `NULL` nesta fatia |

#### Formato de `classificacao_bruta` (extração de ficha)

```json
{
  "tipo": "extracao_ficha",
  "desfecho": "completa | parcial | irreconhecivel | falha_extrator",
  "campos_reconhecidos": ["nome_completo", "profissao"]
}
```

Sem idade. Sem eco do texto completo além do já armazenado em `conteudo`.

### `trabalho` (ampliação)

| Campo | Uso |
| --- | --- |
| `tipo` | Passa a admitir `interpretar_ficha` |
| `payload` | `{ "id_reserva", "id_mensagem", "id_evento" }` — só IDs |
| `status` / tentativas / backoff | Mesmo vocabulário da F1.2 |

**CHECK novo**:

```sql
tipo IN ('enviar_coleta', 'interpretar_ficha')
```

**Unicidade**:

```sql
CREATE UNIQUE INDEX uq_trabalho_interpretar_ficha_mensagem
  ON trabalho ( ((payload->>'id_mensagem')::bigint) )
  WHERE tipo = 'interpretar_ficha';
```

### `hospede` (atualização do titular)

Campos atualizáveis pela consolidação (somente quando reconhecidos e válidos):

| Campo | Notas |
| --- | --- |
| `nome_completo` | |
| `profissao` | |
| `data_nascimento` | Date; **nunca idade** |
| `tipo_documento` | `rg` \| `cpf` \| `passaporte` |
| `numero_documento` | |
| `endereco` | |
| `cep` | |
| `cidade` | |
| `telefone` | Pode atualizar se reconhecido; correlação inicial usa `reserva.telefone_contato` |

### `reserva_hospede`

| Campo | Completa | Parcial / irreconhecível |
| --- | --- | --- |
| `ficha_completa` | `true` | permanece `false` |

Atualiza o vínculo **titular** existente (F1.1); não cria segundo titular.

### `reserva`

| De | Para | Quando |
| --- | --- | --- |
| `aguardando_cadastro` | `ficha_recebida` | Extração completa utilizável |
| `aguardando_cadastro` | `ficha_parcial` | Extração parcial utilizável |
| `aguardando_cadastro` | *(inalterado)* | Irreconhecível ou falha do extrator |

Transições inválidas continuam rejeitadas pela trigger `fn_valida_transicao_reserva`.

---

## Projeção: `vw_fila_do_dia`

Acrescentar **`estado_cadastro`** (texto), derivado:

| Valor | Condição |
| --- | --- |
| `completa` | `r.status = 'ficha_recebida'` |
| `parcial` | `r.status = 'ficha_parcial'` |
| `leitura_humana` | `r.status = 'aguardando_cadastro'` e existe mensagem `recebida` da reserva com `classificacao_bruta->>'desfecho'` ∈ (`irreconhecivel`, `falha_extrator`) |
| `aguardando` | `r.status = 'aguardando_cadastro'` e não há o sinal acima |
| *(outros status)* | Mapear de forma estável se a reserva ainda aparece na visão (ex. hospedado) — fora do foco desta fatia; pode espelhar `r.status` ou omitir semântica de cadastro |

Manter colunas já existentes (`status`, `ficha_completa`, `status_envio_coleta`, etc.).

---

## Campos da ficha (alvo da extração)

Alinhados a `CAMPOS_FICHA` / coleta:

1. nome completo  
2. profissão  
3. data de nascimento  
4. tipo de documento  
5. número do documento  
6. endereço  
7. CEP  
8. cidade  
9. telefone  

**Completa** = os nove reconhecidos e válidos. **Parcial** = pelo menos um, menos que nove.
**Irreconhecível** = zero utilizáveis.

---

## Regras de validação (aplicação + domínio de banco)

- Data de nascimento: data calendário real; rejeitar impossíveis.
- Tipo de documento: só valores do `CHECK` de `hospede`.
- Idade: inexistente no modelo — testes falham se aparecer em INSERT/UPDATE.
- Foto/mídia sem texto: não preenche campos; desfecho irreconhecível.
- `id_hotel` em toda leitura/atualização de reserva e hóspede.

---

## O que não muda nesta fatia

- Máquina de estados além das transições já previstas a partir de `aguardando_cadastro`.
- Tabela `consentimento` (opt-in é F4).
- Lembrete / `reenvio_realizado` / `sem_cadastro_previo` (F1.4).
- Classificação F3 (`intencao` de atendimento).
