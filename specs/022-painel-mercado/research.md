# Fase 0 — Pesquisa e decisões técnicas: Painel de Mercado

Cada seção registra a decisão, por que ela foi tomada e o que foi recusado.
Divergências documentais estão na seção 8.

---

## 1. Duas consultas autenticadas; zero escrita; zero migração

**Decisão**: o painel é HTTP de leitura no módulo `mercado` que já existe.

| Rota | Papel |
| --- | --- |
| `GET /mercado` | Visão atual de **todos** os concorrentes da propriedade (ativos e inativos) |
| `GET /mercado/concorrentes/{id_concorrente}` | Histórico completo da série daquele concorrente |

Não há `POST`/`PATCH`/`DELETE` de coleta. Tentativa → `405`. Não há revisão
Alembic: `concorrente`, `coleta_mercado`, `parametro_hotel` e o índice
`ix_coleta_concorrente_data` já existem. Sem view SQL nova.

**Rationale**: a spec é consulta. A série já é o produto da F5.2. Tabela ou
view que “consolida” o último sucesso duplicaria o depósito e convidaria
UPDATE — exatamente o que a série temporal existe para impedir. Índice de
`(id_concorrente, coletado_em DESC)` já cobre histórico e último ponto.

**Alternativas consideradas**:

- **View `vw_painel_mercado`**: a periodicidade mora em `parametro_hotel`
  (chave/valor). Join + limiar no SQL mistura donos de tabela e dificulta
  relógio injetável. Rejeitado.
- **Aninhar histórico em `GET /concorrentes/{id}/coletas`**: mistura cadastro
  (F5.1, `ler_concorrentes`) com número coletado. A F5.1 já previu operação
  distinta. Rejeitado.
- **Uma única rota com histórico embutido na visão atual**: a spec pede a
  comparação em **uma** consulta (visão atual) e o histórico à parte. Trazer
  a série inteira de todos os concorrentes em toda abertura é custo sem
  problema presente (Artigo XI).
- **Migração só de comentário**: o comentário de `coleta_mercado` já fala do
  painel. Mudar `04-schema.sql` sem revisão quebra conformidade. Não tocar.

---

## 2. Operação nova `ler_mercado`; gestão não escreve a série

**Decisão**: uma operação na matriz, só `gestor`:

| Operação | `recepcao` | `staff` | `gestor` | Rotas |
| --- | :---: | :---: | :---: | --- |
| `ler_mercado` | ❌ | ❌ | ✅ | os dois GETs |

Não nasce `alterar_coleta_mercado`. A garantia de “gestão não altera
registro coletado” é **ausência de rota de escrita**, não um `403` em
método que existe. Recepção e staff → `403`. Alvo de outro hotel → `404`.

Não reutilizar `ler_concorrentes`: cadastrar quem acompanhar e ler preço
coletado são recursos diferentes. A F5.1 e a F5.2 já nomearam `ler_mercado`
como o gancho desta fatia.

**Rationale**: Artefato 3 §4 (“o gestor lê e não escreve”) + critério de
aceite da F5.3. Reusar `ler_indicadores` daria o painel à recepção.

**Alternativas consideradas**:

- **Reusar `ler_concorrentes`**: mesma matriz hoje, mas um perfil futuro na
  lista de fichas herdaria preço. A spec trata a série como depósito à parte.
- **Operação de escrita que sempre recusa**: cerimônia. `405` no método
  inexistente é o contrato honesto.

---

## 3. Visão atual lê o último **sucesso**; falha posterior não substitui o número

**Decisão**: para cada concorrente da propriedade:

1. `ultimo_sucesso` = linha de `coleta_mercado` com `sucesso = true` mais
   recente (`coletado_em`, depois `id_coleta`).
2. `ultima_falha` = preenchida **somente** quando a linha mais recente da
   série (qualquer desfecho) tem `sucesso = false`. Traz só `coletado_em`.
3. Preço e nota da visão atual vêm **só** de `ultimo_sucesso`. Falha
   posterior não apaga, não zera e não redata esse sucesso.

`ultima_coleta` da F5.2 (último ponto, sucesso **ou** falha) **não** alimenta
o número exibido. Reusá-la sozinha faria a falha parecer “preço sumiu” ou,
pior, redataria o valor velho com a data da tentativa falha.

**Rationale**: FR-003, FR-007 e Artefato 3 §6.10 (“mantém o dado anterior com
o carimbo antigo visível”).

**Alternativas consideradas**:

- **Exibir a última tentativa, seja ela qual for**: falha vira ausência de
  preço e o gestor acha que o concorrente “está de graça” ou “sem dado de
  hoje”. Rejeitado pela spec.
- **Esconder o sucesso quando há falha depois**: perde o número que ainda é
  a melhor evidência, contra o depósito D8.

---

## 4. `situacao` no serviço, com o mesmo limiar da coleta

**Decisão**: o serviço classifica cada concorrente **depois** de ler as
linhas e a periodicidade. Relógio injetável (`agora`), padrão das varreduras.

| `situacao` | Quando |
| --- | --- |
| `sem_coleta` | Nenhuma linha na série |
| `so_falha` | Só falhas; nenhum sucesso |
| `cadencia_ausente` | Há sucesso, mas a periodicidade da propriedade é ausente/inválida |
| `desatualizado` | Há sucesso **e** (periodicidade válida) **e** (sucesso mais antigo que a janela **ou** existe `ultima_falha`) |
| `atual` | Há sucesso, periodicidade válida, janela ainda não venceu, sem falha posterior |

Janela: seja `P` a periodicidade em horas e `U` o `coletado_em` do último
sucesso. `agora >= U + P horas` → velho. É o **mesmo** `>=` da F5.2 para
“coleta devida”. No instante em que a fonte volta a ficar devida, o número
deixa de ser apresentado como atual.

Periodicidade lida com `propriedade.repository.ler_parametro` (chave
`periodicidade_coleta_mercado`), injetável. `mercado.repository` **não**
consulta `parametro_hotel`. Ausência não inventa `24`.

Não há chave nova de “horas até desatualizado” (Artigo XIII).

**Rationale**: FR-006, FR-007, FR-018. Sinal distinto de `desatualizado` vs
`cadencia_ausente` — a spec pede os dois. Boolean `desatualizado` sozinho
não cobre “cadência não configurada”.

**Alternativas consideradas**:

- **“Velho” = não é de hoje (meia-noite local)**: número mágico de calendário;
  quebra hotel cuja periodicidade é 48 h. Rejeitado.
- **Chave nova `horas_dado_mercado_velho`**: segundo prazo para o mesmo fato.
  Rejeitado.
- **Classificar no SQL / na view**: relógio de teste e parâmetro por hotel
  ficam piores de injetar. Rejeitado.

---

## 5. Histórico é a série crua, em ordem cronológica crescente

**Decisão**: `GET /mercado/concorrentes/{id}` devolve todas as linhas daquele
concorrente, da mais antiga para a mais nova (`coletado_em ASC`, `id_coleta
ASC`). Cada ponto traz `sucesso`, `preco`, `nota_media`, `coletado_em`.
Falha entra com `preco`/`nota_media` nulos — nunca `0`. Sem paginação no
MVP. Sem percentual de variação calculado: ver os pontos sucessivos **é**
acompanhar o movimento (assumption da spec).

Inativo é consultável. Id inexistente ou de outro hotel → `404` idêntico.

**Rationale**: FR-010, FR-011, FR-016. Ordem crescente deixa a variação
legível (subiu / caiu / parou) sem o cliente inverter a lista.

**Alternativas consideradas**:

- **Só sucessos no histórico**: a spec exige a falha intercalada visível,
  senão dois sucessos parecem consecutivos. Rejeitado.
- **Percentual ou “Δ vs anterior” obrigatório**: a spec não pede produto
  derivado. Pode nascer depois, fora desta fatia.
- **Mais recente primeiro**: comum em feed; ruim para “ao longo do tempo”.

---

## 6. Superfície, testes e o que não entra

**Decisão**: critério de pronto = os dois GETs + matriz + classificação de
`situacao`. Sem React. Sem disparo de coleta. Sem visita à fonte. Sem
mensagem ao hóspede. Sem tarifa da casa no payload (o sistema não a tem).

Testes **não** ligam o worker nem a `FontePublica`: inserem
`coleta_mercado` (helper da F5.2 / SQL de suporte) e consultam. Unitários
do serviço usam repositório falso, parâmetro falso e relógio falso.

Logs: `id_hotel`, `id_concorrente`, ação (`painel` / `historico`). Sem
preço, sem nota, sem URL, sem HTML, sem texto de hóspede.

**Rationale**: FR-019–FR-021 e o padrão das fatias de painel já entregues
(fila do dia, consumos pendentes): API observável, protótipo visual depois.

**Alternativas consideradas**:

- **Tela React nesta fatia**: a spec deixou fora do critério de pronto.
  Primeira tela do produto inteiro não cabe no “consultar a série”.
- **Incluir `url_fonte` na visão atual**: a manutenção já a devolve; o
  painel de preço não precisa repetir o endereço (e o log não pode ecoá-lo).

---

## 7. Isolamento: hotel chega pelo concorrente

**Decisão**: `coleta_mercado` continua sem `id_hotel`. Toda leitura faz
`JOIN`/`WHERE` em `concorrente.id_hotel = :id_hotel` da sessão. Lista da
visão atual: `FROM concorrente WHERE id_hotel = …`, com sucessos e falhas
agregados só desses ids. Dois hotéis com a mesma URL de fonte têm séries
e painéis independentes.

**Rationale**: FR-015, Artigo XIV, contrato da F5.2. Não se adiciona coluna
redundante.

---

## 8. Divergências documentais

| Onde | O que está escrito | O que esta fatia faz |
| --- | --- | --- |
| Artefato 1 §5.3 | “Consolida e apresenta no painel Market Intel” | Consolida na leitura (último sucesso + `situacao`); apresenta por API. Sem tela gráfica |
| Artefato 2 §5.2 | Gestor consulta no painel web, desktop | Cookie de gestão nos GETs; React continua fora, no padrão F5.1/F5.2 |
| Artefato 5 §11.2 | Gestor só lê painéis de mercado | `ler_mercado` só gestão; escrita da série inexistente. Cadastro de concorrente permanece F5.1 |
| F5.1 contrato de autorização | “`ler_mercado` nasce na F5.3 se o painel precisar” | Nasce. Não reutiliza `ler_concorrentes` |
| F5.2 | “Sem painel (F5.3)” | Esta fatia é esse painel, só leitura |
| Pendência “lista oficial / termos de uso” | Ainda humana | Painel não visita fonte e não examina ToS |

Clarify não rodou. Planejamento usou a spec (limiar = periodicidade, visão =
último sucesso, variação = série, sem tarifa da casa, inativo visível, sem
protótipo visual).
