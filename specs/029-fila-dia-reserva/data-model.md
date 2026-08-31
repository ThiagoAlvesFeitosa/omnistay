# Modelo de dados — Fila do dia e cadastro de reserva

Referência: `docs/04-schema.sql`. Decisões em [research.md](./research.md).
Esta fatia **não cria tabela**. Reserva, titular e a visão
`vw_fila_do_dia` são os da F1.1–F2.2. O que nasce é modelo de
superfície no frontend.

---

## Entidades novas (só de superfície)

### Linha da fila

Projeção de um item de `GET /fila-do-dia` para a tela. Não é persistida.

| Campo (API) | Uso na tela |
| --- | --- |
| `id_reserva` | Identidade da linha e alvo do `POST .../chegada` |
| `nome` | Coluna hóspede |
| `telefone_contato` | Coluna hóspede (canônico `55…`; exibir à recepção) |
| `data_checkin_prevista` | Coluna entrada |
| `data_checkout_prevista` | Coluna saída |
| `status` | Situação + elegibilidade do botão |
| `estado_cadastro` | Coluna ficha |
| `chegada_nao_confirmada` | Destaque de entrada vencida + conta do resumo |
| `boas_vindas_nao_enviadas` | Destaque de recado não enviado |

Ignorados nesta fatia: `ficha_completa` (redundante com
`estado_cadastro`), `status_envio_coleta`, `precisa_atendimento_humano`,
`saida_nao_confirmada`, `pesquisa_saida_leitura_humana`.

### Resumo do turno

Três inteiros derivados da lista carregada. Ver
[resumo-do-turno.md](./contracts/resumo-do-turno.md). Não há coluna
no banco.

### Cadastro mínimo

Corpo de `POST /reservas` — não é tabela nova.

| Campo | Regra na tela |
| --- | --- |
| `nome` | Obrigatório após trim |
| `telefone` | Normalizável como brasileiro com DDD (espelho de `telefone.py`) |
| `data_checkin_prevista` | Data; pode ser passada |
| `data_checkout_prevista` | Estritamente posterior à entrada |

Sem e-mail, documento ou endereço.

---

## Entidades reusadas

### `reserva` (banco)

| `status` | Na fila? | Botão confirmar chegada? |
| --- | :---: | :---: |
| `aguardando_cadastro` | sim, se check-in ≤ hoje | não |
| `ficha_recebida` | sim | sim |
| `ficha_parcial` | sim | sim |
| `sem_cadastro_previo` | sim | sim |
| `hospedado` | sim | não |
| `encerrado` / `cancelada` | não | — |

Transição `* → hospedado` continua na F2.2 (clique + trigger). A tela
não envia `status` no corpo.

### `vw_fila_do_dia`

Já restringe: hotel da sessão, `data_checkin_prevista <= CURRENT_DATE`,
fora de encerrado/cancelada. Ordenação: entrada prevista, depois
`id_reserva`. A tela **não** reordena nem refiltra por data.

### `usuario` / `sessao`

Casca da F8.1. Só `recepcao` monta estas telas.

---

## Estados visíveis da ficha (`estado_cadastro`)

| Valor | Rótulo de negócio | Destaque de pendência F8.2? |
| --- | --- | :---: |
| `aguardando` | aguardando cadastro | não (não é as três pendências) |
| `completa` | completa | não |
| `parcial` | parcial | **sim** |
| `leitura_humana` | leitura humana | não (F8.3 completa no balcão) |
| `sem_cadastro_previo` | chegará sem cadastro prévio | não |

---

## O que não nasce

- Tabela, coluna, visão ou revisão Alembic
- Operação nova em `politica.py`
- Entidade de “hóspede de maquete”
- Campo de e-mail na reserva
- Confirmação de saída
- Desfazer chegada

---

## Regras de validação (superfície)

| Situação | Efeito |
| --- | --- |
| `GET /fila-do-dia` 200, `itens: []` | Fila vazia; três contas em 0; cadastrar visível |
| `GET` 401 | Casca já devolve à entrada |
| `GET` 5xx / rede / 403 inesperado | Falha de leitura; não vazio; tentar de novo |
| Telefone ilegível na digitação | Mensagem; não dispara `POST` |
| Checkout ≤ check-in | Mensagem; não dispara `POST` |
| `POST /reservas` 201 e id na lista | Volta à fila; linha visível |
| `POST /reservas` 201 e id ausente | Informa que entra no dia da entrada; volta à fila |
| `POST /reservas` 422 | Declara o campo; nada gravado |
| Clique fora do botão | Zero `POST .../chegada` |
| `POST .../chegada` 200 | `GET` de novo; linha vira hospedado |
| `POST .../chegada` 409 | Motivo visível; `GET` de novo; não afirma hospedado |

---

## Relacionamentos

```text
sessao (F0.3) ──> GET /fila-do-dia ──> itens[] ──> linhas + resumo
                         │
                         └── POST /reservas/{id}/chegada  (se status admite)

POST /reservas ──> 201 ──> GET /fila-do-dia (decide se a linha aparece hoje)
```
