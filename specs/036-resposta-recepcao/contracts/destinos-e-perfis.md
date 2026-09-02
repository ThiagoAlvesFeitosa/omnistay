# Contrato: destinos e perfis (delta)

Fonte: `frontend/src/painel/destinos.ts`.

| Campo | Antes | Depois |
| --- | --- | --- |
| `id` | `ficha` | `ficha` |
| `caminho` | `/app/ficha` | `/app/ficha` |
| `titulo` | Ficha do hóspede | **Estadia** |
| `perfis` | `recepcao` | `recepcao` |

Staff e gestão: casca continua sem montar este destino. Zero
GET de conversa.

Testes de casca que afirmam o heading **Ficha do hóspede** passam
a **Estadia** de propósito.
