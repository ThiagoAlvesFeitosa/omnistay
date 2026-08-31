# Modelo de dados — Ficha do hóspede e transcrição

Referência: `docs/04-schema.sql`. Decisões em [research.md](./research.md).
Esta fatia **não cria tabela**. Hóspede, vínculo titular e
consentimento são os da F1.1–F4.1. O que nasce é a escrita no balcão,
uma transição a mais no gatilho, e o modelo de superfície no frontend.

---

## Entidades novas (só de superfície)

### Ficha visível

Projeção de `GET/PUT /reservas/{id}/ficha` para a tela. Não é
persistida além das colunas já existentes em `hospede` /
`reserva_hospede`.

| Campo (API) | Uso na tela |
| --- | --- |
| `id_reserva` | Identidade; volta à fila |
| `id_hospede` | Alvo do GET/POST de consentimento |
| `ficha_completa` | Distintivo completa / parcial |
| `status_reserva` | Contexto; **não** é editável nesta tela |
| `estado_cadastro` | Leitura humana vs aguardando vs parcial vs completa |
| Nove campos do titular | Exibição, edição, cópia |

Sem `idade`, sem `email`.

### Campo ausente

Derivado na tela (e conferido no `PUT`): um dos nove de
`CAMPOS_FICHA_CHAVE` sem valor utilizável. Nomeado por rótulo de
negócio, nunca só por contagem.

### Texto de cópia

Nove linhas `Rótulo: valor`, na ordem da coleta. Não é coluna. Não
é arquivo. Não vai ao PMS sozinho.

### Consentimento vigente (reuso)

Projeção de `GET /hospedes/{id}/consentimento`. Ver contrato F4.1:
ausência (`momento` nulo) ≠ recusa gravada.

---

## Entidades reusadas

### `hospede`

| Coluna | Nesta fatia |
| --- | --- |
| `nome_completo` | Obrigatório; editável |
| `telefone` | Obrigatório; cadastral (não é o canal da reserva) |
| `profissao`, `data_nascimento`, `tipo_documento`, `numero_documento`, `endereco`, `cep`, `cidade` | Opcionais; vazios no formulário → NULL |
| *(idade)* | **Não existe** |

`CHECK` de tipo (`rg`, `cpf`, `passaporte`) e nascimento passado
permanecem. `uq_hospede_documento` recusa colisão.

### `reserva_hospede`

| Coluna | Nesta fatia |
| --- | --- |
| `titular` | Só o titular; acompanhante fora |
| `ficha_completa` | `true` sse os nove campos estão utilizáveis após o `PUT` |

### `reserva` (`status`)

| Status atual | `PUT` completo (9 campos) | `PUT` incompleto |
| --- | --- | --- |
| `aguardando_cadastro` | → `ficha_recebida` | → `ficha_parcial` |
| `ficha_parcial` | → `ficha_recebida` | permanece |
| `ficha_recebida` | permanece | → `ficha_parcial` |
| `sem_cadastro_previo` | permanece; só flag | permanece; só flag |
| `hospedado` / `encerrado` / `cancelada` | permanece; só flag | permanece; só flag |

**Não** admite, por esta gravação: qualquer ida a `hospedado` ou
`encerrado`; volta a `aguardando_cadastro`; toque em `cancelada` como
ciclo.

### Gatilho `fn_valida_transicao_reserva`

Acrescentar ao conjunto já existente:

```text
(OLD.status = 'ficha_parcial'  AND NEW.status = 'ficha_recebida')
(OLD.status = 'ficha_recebida' AND NEW.status = 'ficha_parcial')
```

Demais transições inalteradas. Revisão `0024` + `04-schema.sql`.

### `consentimento`

Append-only como F4.1. Origem nesta tela: só `painel`. Finalidade:
`comunicacao_marketing`.

### `usuario` / `sessao`

Casca da F8.1. Só `recepcao` monta esta tela.

---

## Os nove campos (ordem da coleta)

1. Nome completo
2. Profissão
3. Data de nascimento
4. Tipo de documento
5. Número do documento
6. Endereço
7. CEP
8. Cidade
9. Telefone

Completa ⇔ os nove utilizáveis. Parcial ⇔ pelo menos um ausente
(com nome e telefone mínimos do cadastro da reserva, os ausentes
são em geral os outros sete).

---

## O que não nasce

- Tabela, coluna de e-mail, coluna de idade
- Operação nova em `politica.py`
- Entidade de acompanhante na tela
- Integração / fila / trabalho de “enviar ao PMS”
- Confirmação de chegada ou saída nesta tela

---

## Regras de validação

| Situação | Efeito |
| --- | --- |
| `GET .../ficha` 200 | Monta a tela com os nove + distintivo + ausentes nomeados |
| `GET` 404 | Recusa genérica; não afirmar que a reserva existe |
| `GET` 5xx / rede | Falha de leitura; painel permanece; tentar de novo ou voltar à fila |
| Menu `/app/ficha` sem id | Estado vazio; zero GET de ficha |
| `PUT` 200, nove campos | Distintivo completa; se estava `ficha_parcial`, status vira `ficha_recebida` |
| `PUT` 200, ainda falta campo | Permanece parcial; ausentes atualizados; o que era válido permanece |
| `PUT` 422 | Campo inválido nomeado; nada daquele valor persistido |
| Documento duplicado | Recusa; fichas não se fundem |
| `PUT` em `hospedado` | Flag e campos; status permanece `hospedado` |
| Cancelar edição | Descarta o formulário; último GET permanece |
| Consentimento sem `momento` | Nunca registrado |
| `POST` consentimento `201` | Vigente novo; linhas antigas intactas |

---

## Relacionamentos

```text
fila (F8.2) ──Ver ficha──> GET /reservas/{id}/ficha
                              │
                              ├── PUT /reservas/{id}/ficha
                              │     └── hospede + reserva_hospede.ficha_completa
                              │           └── reserva.status (só par parcial ↔ recebida
                              │               ou a partir de aguardando_cadastro)
                              │
                              └── GET/POST /hospedes/{id_hospede}/consentimento
```
