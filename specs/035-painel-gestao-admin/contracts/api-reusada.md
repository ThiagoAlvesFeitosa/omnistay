# Contrato: APIs reusadas (mercado e retenção)

Detalhe original: F5.3 (`specs/022-painel-mercado/contracts/`) e
F6.1 (`specs/023-expurgo-retencao/contracts/`). Esta fatia é
cliente. Cookie `omnistay_sessao`. Sem `id_hotel` no JSON.

---

## `GET /mercado`

Operação `ler_mercado` (só gestão). Visão atual: nome, `situacao`,
`ultimo_sucesso` (preço/nota/`coletado_em`), `ultima_falha`.
Inativos entram. Sem URL de fonte. Sem tarifa da casa.

`concorrentes: []` é vazio honesto.

A tela **não** dispara `POST`/`PATCH` `/concorrentes` nem escrita
em `/mercado` (`405` se alguém tentar).

---

## `GET /mercado/concorrentes/{id_concorrente}`

Mesma operação. Série completa em ordem de tempo. Falha: `sucesso:
false`, preço/nota `null` — nunca zero inventado. Alheio ou
inexistente: `404` (mesma resposta).

A tela só dispara no clique de um concorrente da visão atual.

---

## `GET /retencao`

Operação `ler_retencao` (só gestão). Lista `execucoes` como na
F6.1 (data, quantidades por espécie, flags de prazo ausente).

**Delta desta fatia** no mesmo `200`:

| Campo | Tipo |
| --- | --- |
| `meses_retencao_conteudo_livre` | inteiro ≥ 1 ou `null` |
| `anos_retencao_ficha` | inteiro ≥ 1 ou `null` |

`null` quando a chave falta ou o valor não é inteiro ≥ 1. A tela
**não** substitui por 12 ou 5.

`execucoes: []`: hotel ainda sem passagem — não é erro.

Sem rota de disparo. `POST`/`PUT`/`PATCH`/`DELETE` em `/retencao`
→ `405`.

---

## `GET /indicadores/chegadas-do-dia`

**Não** usado pela tela Painel. Permanece para quem já consome
(F1.1). O Painel usa `GET /indicadores`.
