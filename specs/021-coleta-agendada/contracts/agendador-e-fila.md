# Contrato: agendador e fila — coleta de mercado

A varredura decide **quem está devido** e grava trabalho. O consumidor visita
a fonte via [fonte-publica.md](./fonte-publica.md) e grava a série em
[registro-de-coleta.md](./registro-de-coleta.md).

---

## Flag e cadência

```text
python -m worker --verificar-mercado
```

- Relógio injetável (`agora`), padrão o relógio da aplicação.
- `--uma-passagem` **não** dispara esta varredura.
- Modo contínuo: a passagem horária já existente chama
  `verificar_coletas_mercado` junto com cadastros, boas-vindas e pulsos.
- Sem APScheduler. Sem intervalo novo no código além da cadência horária
  já usada (ela só pergunta “há alguém devido?”; a periodicidade é por
  propriedade).

---

## `verificar_coletas_mercado(conexao, *, agora=None) -> int`

Para cada fonte **ativa**, com periodicidade válida do hotel:

1. Lê `periodicidade_coleta_mercado` (cache por `id_hotel`).
2. Inválida/ausente → log `periodicidade_ausente`; **não** enfileira nada
   daquele hotel.
3. Última coleta da fonte (qualquer `sucesso`) + horas ≤ agora, **ou**
   nunca coletada → devido.
4. Enfileira `coletar_mercado` com payload `{id_concorrente}`.
5. Colisão do índice único aberto → ignora (já há ciclo em voo).

Devolve quantos trabalhos **novos** nasceram. Hotel sem ativo: 0, sem erro.

A varredura **não** chama a porta. **Não** envia mensagem ao hóspede.

---

## Tipo `coletar_mercado`

| Campo | Valor |
| --- | --- |
| `tipo` | `coletar_mercado` |
| `id_hotel` | Hotel da ficha |
| `payload` | `{"id_concorrente": N}` — só identificador |
| Allowlist do consumidor | **sim**, nesta fatia |

Unicidade: no máximo um trabalho `pendente` ou `processando` por
`id_concorrente`. Histórico `concluido` é ilimitado.

Entra em `ck_trabalho_tipo` e em `TIPOS_CONSUMIVEIS` / `reclamar_proximo`
**no mesmo passo** (lição da F3.1/F3.2: allowlist sem ramo, ou o contrário,
destrói o gancho).

---

## Processador

`mercado.service.processar_trabalho_coletar_mercado(conexao, trabalho, fonte)`

Ordem:

1. Relê concorrente por `id_hotel` + `id_concorrente` + `ativo`.
   Ausente/inativo → `concluido`, log `fonte_inativa_omitida`, **0** INSERT
   em `coleta_mercado`.
2. Se já há coleta com `coletado_em >= criado_em` do trabalho → `concluido`,
   sem segunda visita.
3. `consultar_diretiva(url_fonte)`. Se não `permite` → INSERT falha +
   `concluido`.
4. `coletar_publico(url_fonte)`. Mapeia desfecho → INSERT sucesso ou falha.
5. Trabalho sempre `concluido`. **Não** usa `falha` + backoff.

Visitas do consumidor são **sequenciais** (um claim por vez). Não há pool
paralelo contra o mesmo anfitrião nesta fatia.

---

## O que este contrato recusa

| Tentação | Por que não |
| --- | --- |
| HTTP na varredura | Varredura fica lenta; Artigo III |
| URL no payload | Ficha pode mudar; log |
| Segundo trabalho aberto | Spec FR-016 |
| Retry curto na fila | Frequência moderada; falha já é o desfecho do ciclo |
| Botão/rota de disparo | FR-018 |
