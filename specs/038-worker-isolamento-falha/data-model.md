# Data model: isolamento de falha no worker

Nenhuma tabela nova. Nenhuma coluna nova em `trabalho`. A fatia
**lê** o que a fila já persiste e **amplia a visão** da Fila do dia.

## Trabalho da fila (`trabalho`)

Já existe (`docs/04-schema.sql`). Campos que esta fatia realmente usa:

| Campo | Papel nesta fatia |
| --- | --- |
| `id_trabalho` | Identificador nos logs (nunca payload pessoal) |
| `id_hotel` | Teto de tentativas da **casa do trabalho** |
| `tipo` | Despacho; chave de omissão na Fila do dia |
| `payload` | JSON só com identificadores. Distintivo exige `id_reserva`. `coletar_mercado` traz `id_concorrente` — sem distintivo |
| `status` | `pendente` → `processando` → `concluido` **ou** `pendente` (reagendado) **ou** `falha`. CHECK já admite `falha` |
| `tentativas` | Incremento em toda falha capturada |
| `proxima_tentativa_em` | `backoff_apos(novas)`; `reclamar_proximo` ignora quem ainda não venceu |
| `erro_ultima_tentativa` | **Somente** o nome da classe da exceção (ou código de envio já existente) |
| `processando_desde` | Reclaim de `processando` expirado permanece (5 min já no repositório) |

### Transições nesta fatia

```text
pendente --reclamar--> processando
processando --sucesso--> concluido
processando --exceção, tentativas+1 < teto--> pendente (espera crescente)
processando --exceção, tentativas+1 >= teto--> falha
falha --não é reclamado--> (terminal até intervenção fora de escopo)
concluido --intocado quando outro falha--> concluido
```

Reclamação: `status = 'pendente'` e
`(proxima_tentativa_em IS NULL OR <= agora)`. `falha` e `concluido`
fora. Tipo desconhecido continua indo a `falha` (já existia), agora
pelo mesmo registrador isolado.

Unicidades por tipo de trabalho **não** se relaxam na retentativa.

## Configuração da propriedade (`parametro_hotel`)

| Chave | Uso |
| --- | --- |
| `tentativas_max_envio_mensagem` | Teto. Ausente ou ilegível → **5** (`TENTATIVAS_MAX_PADRAO` já existente) |

Sem chave nova de espera. `backoff_apos` permanece fórmula técnica da
fila.

## Passagem e ciclo (não persistidos)

- **Passagem**: até N claims elegíveis, cada um em savepoint.
- **Ciclo**: passagem + verificar cadastros + boas-vindas + pulsos +
  mercado + retenção. Cada etapa isolada. Cadência horária das
  verificações **não muda**.

## Distintivo de omissão (derivado)

Não é entidade gravada. Derivado na visão + serviço:

| Campo API | Origem |
| --- | --- |
| `chave` | Catálogo (research §6), a partir dos `tipo` em `falha` |
| `contagem` | Soma de trabalhos da mesma chave na reserva |
| `texto` | Singular se 1; `"{n} " + plural` se ≥ 2 |

Filtros: mesmo `id_hotel`, `payload.id_reserva` = linha, `status =
'falha'`, reserva **não** `encerrado`. Sem `id_reserva` → não deriva.

Some só com saída confirmada (`status = encerrado`), não com gesto de
ciência.

## Relacionamentos

```text
hotel 1──* trabalho
reserva 1──* trabalho (via payload.id_reserva, quando houver)
reserva 1──* omissão (derivada, só status falha)
vw_fila_do_dia 1── linha da recepção (omissoes[])
```

## Validação

- `erro_ultima_tentativa` no caminho desta fatia: identificador de
  classe, sem CPF, sem SQL, sem conteúdo de mensagem — imposto por
  teste, não por CHECK (o campo é `TEXT` reusado pela falha de envio).
- `omissoes` vazia é válido (reserva saudável ou só mercado em falha).
