# Contrato — API de textos de boas-vindas (delta)

As rotas **já existem**. Esta fatia acrescenta o campo `convite`. Sessão
por cookie `omnistay_sessao`. `id_hotel` **só** da sessão.

---

## `GET /propriedade/boas-vindas`

Operação: `ler_texto_de_boas_vindas` (`recepcao`, `gestor`).

**Resposta `200`:**

```json
{
  "cafe": "Cafe da manha das 7h as 10h",
  "wifi": "Wi-Fi: rede do hotel, senha na recepcao",
  "checkout": "Checkout ate as 12h",
  "convite": "Pode perguntar por aqui sobre servicos, cardapio e horarios."
}
```

Chave ausente na configuração vem como `null` (igual aos três). Depois
da 0023, propriedade migrada não devolve `null` no convite.

| Código | Quando |
| --- | --- |
| `401` | Sessão ausente ou inválida |
| `403` | Perfil operacional |

---

## `PUT /propriedade/boas-vindas`

Operação: `alterar_texto_de_boas_vindas` (só `recepcao`).

**Corpo** — os **quatro** campos obrigatórios:

```json
{
  "cafe": "Cafe da manha das 7h as 10h30",
  "wifi": "Wi-Fi: rede Hotel-Hospedes, senha 12345678",
  "checkout": "Checkout ate as 12h",
  "convite": "Pode perguntar sobre o cardapio e o horario do spa."
}
```

`extra=forbid`. Corpo sem `convite` (cliente da F2.2) → `422`.
Gravação atômica: se um valor for recusado, **nenhum** dos quatro muda.

**Resposta `200`:** o mesmo formato do `GET`, valores após `strip`.

| Código | Quando |
| --- | --- |
| `403` | Perfil diferente de recepção (inclui gestão, que só lê) |
| `422` | Vazio, só espaços, quebra de linha, tabulação, 5+ espaços seguidos, ou acima de 255 caracteres |

Mensagem de `422` nomeia o campo e o motivo, em português, **sem** repetir
o valor enviado.

**Fora do alcance:** `horas_validade_boas_vindas`, prazos, durações de
sessão, `personalidade_assistente`, aviso de assistente virtual.

---

## O que não muda de rota

- `POST /reservas/{id}/chegada` — mesmo contrato de status; o desfecho
  `nao_enviada_slot_ausente` passa a incluir convite vazio ou ausente
- `GET /fila-do-dia` — campo `boas_vindas_nao_enviadas` inalterado
