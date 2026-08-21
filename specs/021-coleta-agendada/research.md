# Fase 0 — Pesquisa e decisões técnicas: Coleta Agendada

Cada seção registra a decisão, por que ela foi tomada e o que foi recusado.
Divergências documentais estão na seção 10.

---

## 1. Varredura no agendador existente; sem APScheduler

**Decisão**: `verificar_coletas_mercado` em `worker/agendador.py`, relógio
injetável (`agora`), flag `--verificar-mercado`. No modo contínuo, a passagem
horária que já chama cadastros, boas-vindas e pulsos passa a chamar o mercado
também. `--uma-passagem` **não** dispara a varredura (igual às anteriores).

A varredura **só enfileira**. Não abre a fonte. Rede fica no consumidor, como
envio de mensagem.

**Rationale**: F1.4, F2.2 e F3.8 já recusaram APScheduler (Artigo XI). O
Artefato 5 nomeia a lib; o Artigo XI vence. Periodicidade de 24 h não pede
relógio novo: a cadência horária já percorre o que está devido e no-opa o
resto. Misturar HTTP na varredura deixaria `--verificar-mercado` lento e
acoplado à rede.

**Alternativas consideradas**:

- **APScheduler só para mercado**: quarta peça móvel sem problema que a flag
  não resolva. Rejeitado.
- **Coletar na própria varredura**: simples, mas a passagem bloqueia em rede
  e quebra o padrão “gravar intenção antes da I/O” (Artigo III). Rejeitado.
- **Disparar mercado dentro de `--uma-passagem`**: mistura fila com calendário
  e quebra o contrato das fatias anteriores.

---

## 2. Tipo `coletar_mercado` com unicidade do pendente, não da história

**Decisão**: trabalho `coletar_mercado`, payload só `{"id_concorrente": N}`.
`id_hotel` vai na coluna da fila, nunca no corpo. A URL **não** entra no
payload: o processador relê a ficha ativa no momento da visita.

Índice único **parcial**:

```text
uq_trabalho_coletar_mercado_concorrente_aberto
  ON ((payload->>'id_concorrente')::bigint)
  WHERE tipo = 'coletar_mercado'
    AND status IN ('pendente', 'processando')
```

Muitos trabalhos `concluido` do mesmo concorrente são o produto (um por
ciclo). Dois abertos do mesmo concorrente são o defeito que a spec chama de
“par contemporâneo”.

O processador **reavalia** antes de visitar: se a ficha não está mais ativa,
ou não é daquele hotel, conclui **sem** inserir coleta. Se já existe coleta
com `coletado_em >= criado_em` deste trabalho (reclaim), conclui sem segunda
visita. Falha de rede ou diretiva **não** usa backoff da fila: grava coleta
`sucesso = false` e marca o trabalho `concluido`. Martelar a fonte não é
recuperação.

**Rationale**: Artigo III (intenção durável antes da rede) + Artigo IX (duas
varreduras simultâneas não criam dois ciclos). Unicidade eterna como no pulso
impediria o segundo ciclo. Retry de `falha` na fila violaria frequência
moderada (Artefato 5 §15.1).

**Alternativas consideradas**:

- **Unicidade eterna por concorrente**: um único trabalho na vida; a série
  temporal morre no primeiro ciclo. Rejeitado.
- **Sem fila, INSERT direto na varredura**: duas passagens coincidentes
  inserem duas coletas; conferência em código não fecha (Artigo IX).
- **Backoff / status `falha`**: a spec trata falha como desfecho do ciclo,
  não como “tente de novo em 30 s”. O próximo ciclo, pela periodicidade, é
  quem tenta outra vez.
- **URL no payload**: evita um SELECT, mas desatualiza se a gestão editar, e
  convida logar o endereço. Rejeitado.

---

## 3. Quarta porta: `FontePublica`; domínio sem HTTP

**Decisão**: protocolo `FontePublica` em `app/portas/fonte_publica.py`. O
módulo `mercado` depende só da interface. Falso em
`app/adaptadores/fonte_falsa.py` (mapa url → diretiva + resultado). Adaptador
real em `app/adaptadores/fonte_http.py` com biblioteca padrão
(`urllib.request`, `urllib.robotparser`, `json`, `html.parser`). **Nenhuma
dependência nova** (`httpx`, BeautifulSoup, Scrapy: não).

O worker injeta a porta como já injeta mensageria e LLM. A suíte **não**
instancia o adaptador HTTP contra site alheio; o HTTP real tem teste de
unidade com página-fixture. O `__main__` do worker hoje usa
`MensageriaFalsa`; a fonte falsa segue o mesmo padrão na suíte. O adaptador
HTTP existe para produção e para o teste de fixture — não para CI falar com
OTA.

Dois métodos, porque a spec exige ler a diretiva **antes** do conteúdo:

| Método | Desfecho |
| --- | --- |
| `consultar_diretiva(url)` | `permite` · `recusa` · `ausente` |
| `coletar_publico(url)` | preço e/ou nota, ou falha tipada (`sem_dado`, `indisponivel`, `exige_autenticacao`) |

`ausente` (404, timeout, texto ilegível) **não** é permissão. O domínio não
chama `coletar_publico` se a diretiva não for `permite`.

Identidade honesta é propriedade do adaptador (cabeçalho reconhecível
`OmniStay-Coletor/1.0`, sem imitar navegador). O falso expõe o último
identificador usado para o teste da FR-010.

**Rationale**: Artigo X (domínio não conhece implementação) + FR-020 (sem
site real). As três portas da constituição nasceram com o produto; visita a
fonte pública é o mesmo tipo de I/O externo que a mensageria, e não existia
na F0. Sem porta, `urllib` cairia no serviço. Artigo XI: protocolo novo sim;
biblioteca nova não.

**Alternativas consideradas**:

- **LLM para “ler” a página**: a spec recusa. Número alucinado não é coleta.
- **Protocolo dentro de `mercado/` sem `app/portas/`**: esconderia o I/O
  externo do mapa que a constituição usa. Rejeitado.
- **Um método só `visitar`**: misturaria diretiva e conteúdo; o teste de
  “proíbe → não recolhe” ficaria opaco.
- **`can_fetch` do `robotparser` no 404**: o padrão trata arquivo ausente
  como “pode tudo”. A spec inverte. O adaptador só devolve `permite` depois
  de ler um corpo compreensível que autorize aquele endereço.

---

## 4. Extração: dado estruturado público, sem chute

**Decisão**: o adaptador HTTP procura preço e nota agregada em dado
estruturado público da página (JSON-LD / schema.org `Offer` +
`AggregateRating`). Escala da nota: 0–5; valor fora disso descarta a nota
(campo vazio). Sem dado estruturado extraível → `sem_dado` → coleta falha se
não houver o outro campo.

O falso **não parseia HTML**: o teste do domínio configura preço/nota/falha
direto. Parser tem teste próprio com fixture, nunca com URL viva.

**Rationale**: spec (preço em destaque para anônimo; nota agregada; sem IA).
JSON-LD é o que a fonte publica para máquinas sem disfarce. Regex solta em
HTML inteiro inventa número com aparência de fundamento — o defeito que o
Artefato 3 §6.10 descreve.

**Alternativas consideradas**:

- **BeautifulSoup + heurística visual**: lib nova + frágil. Rejeitado.
- **Classificar a página no `LLMProvider`**: viola a spec e o Artigo II
  (conhecimento geral do modelo não fala em nome do hotel; aqui falaria em
  nome do concorrente com o mesmo vício).
- **Um preço por categoria de quarto**: fora do recorte da spec.

---

## 5. Periodicidade: chave já prevista; semear 24; ausência falha alto

**Decisão**: ler `periodicidade_coleta_mercado` (horas, inteiro ≥ 1).
Bootstrap e revisão `0020` semeiam `"24"`. Ausência, vazio, zero, negativo
ou não numérico: aquela propriedade não coleta; log `periodicidade_ausente`;
nenhum default no verificador.

Janela **por concorrente**: devido se não há coleta ou se
`agora >= ultima.coletado_em + horas` (última tentativa, sucesso ou falha).
Fonte nova nunca coletada está devida na primeira verificação com chave
válida. Mudar a chave vale na verificação seguinte; sem replay.

**Rationale**: Artigo XIII + spec FR-002/FR-014/FR-022. Mesmo padrão de
`horas_minimas_para_pulso`. Carimbo único “última execução do hotel”
atrasaria fonte recém-incluída.

**Alternativas consideradas**:

- **Unidade em dias, valor `1`**: o resto das chaves é hora. Rejeitado.
- **Default 24 no código quando a chave falta**: a spec e o pulso recusam.
- **Replay de ciclos perdidos** ao baixar a periodicidade: rajada contra a
  fonte. Rejeitado.

---

## 6. Série temporal na tabela que já existe; hotel pelo concorrente

**Decisão**: INSERT em `coleta_mercado` (já na `0001`). Sem coluna nova, sem
`id_hotel` próprio (o hotel chega pelo `concorrente`, decisão da F5.1). Sem
`motivo_falha` na tabela: o desfecho fino vai ao log (`diretiva_recusada`,
`diretiva_ausente`, `fonte_indisponivel`, `exige_autenticacao`, `sem_dado`).

Regras já no banco, só exercitadas:

| Restrição | Papel nesta fatia |
| --- | --- |
| `sucesso` NOT NULL | falha não se omite |
| `coletado_em` NOT NULL | toda coleta tem data |
| `ck_coleta_sucesso_tem_dado` | sucesso exige preço ou nota |
| `ck_coleta_preco_nao_negativo` | preço zero é válido |
| `ck_coleta_nota_media` | nota 0–5 |
| `ix_coleta_concorrente_data` | última coleta para a janela |

Toda leitura/escrita filtra `concorrente.id_hotel`. Lista de alvos = 
`listar_fontes_ativas` (por hotel) ou equivalente interno que **devolve**
`id_hotel` (não omite o filtro: cada linha traz o hotel).

**Rationale**: Artigo IX (CHECKs já existem) + Artigo XI (sem coluna de
motivo que a spec não pede) + Artigo XIV.

**Alternativas consideradas**:

- **`id_hotel` em `coleta_mercado`**: desnormaliza; a F5.1 já fechou o
  contrário.
- **UPDATE do último registro**: destrói a série (spec FR-004).
- **Coluna `motivo`**: o painel (F5.3) mostra data e sucesso; o código fino
  é operacional, não dado de gestão.

---

## 7. Sem rota HTTP, sem operação nova na matriz, sem React

**Decisão**: zero rota nova. A superfície é a flag do worker + o consumidor.
Gestão não dispara “coletar agora”. F5.3 nasce a consulta do painel e, se
precisar, `ler_mercado`. Esta fatia **não** dá à gestão escrita em
`coleta_mercado` (não inventa número).

O worker não autentica perfil: opera com `id_hotel` da ficha, como a F5.1 já
previu no contrato de fontes ativas.

**Rationale**: FR-017/FR-018. Endpoint de disparo seria o botão que a spec
recusa. Reusar `alterar_concorrentes` para gravar preço seria deixar a
gestão inventar número.

**Alternativas consideradas**:

- **POST `/concorrentes/{id}/coleta`**: disparo manual. Rejeitado.
- **GET da série nesta fatia**: é o painel da F5.3. Testes leem pelo
  repositório.

---

## 8. Log só com identificadores e desfecho

**Decisão**: `logger.info` com `id_concorrente`, `id_hotel`, desfecho
(`sucesso`, `falha`, `diretiva_recusada`, `diretiva_ausente`,
`fonte_indisponivel`, `exige_autenticacao`, `sem_dado`,
`fonte_inativa_omitida`, `periodicidade_ausente`). Sem URL, sem HTML, sem
preço, sem nota, sem nome de avaliador, sem texto de hóspede.

**Rationale**: FR-019 e Artigo VIII.

---

## 9. Orquestração no agendador; SQL de coleta só em `mercado`

**Decisão**: `worker/agendador.py` lê o parâmetro (via
`propriedade.repository`, padrão já usado) e chama
`mercado.service.agendar_coletas_devidas`. O serviço decide quem está
devido e pede à fila o INSERT do trabalho. O consumidor chama
`mercado.service.processar_trabalho_coletar_mercado` com a porta. Nenhum
outro módulo escreve `coleta_mercado`. `conversa` não entra.

**Rationale**: fronteira de módulo + evitar ciclo mercado ↔ propriedade: o
agendador já é o lugar da orquestração (lição da F0.3).

**Alternativas consideradas**:

- **`mercado` ler `parametro_hotel` direto**: SQL de outro dono.
- **Fila conhecer URL da fonte**: payload com dado que o log não pode ecoar.

---

## 10. Divergências documentais

| Onde | O que está escrito | O que esta fatia faz |
| --- | --- | --- |
| Artefato 5 §9 | `APScheduler` no worker | Sem a lib; flag + passagem horária. Já divergido desde a F1.4; registrar de novo no estado se o texto do artefato ainda citar coleta |
| Artefato 5 §15.1 | Respeitar `robots.txt` (o padrão trata ausência como permissão) | Lê a diretiva publicada; **ausência/ilegível = não visita**. A spec vence o default da RFC. Na implementação, registrar em `docs/00-ESTADO-DO-PROJETO.md` |
| Constituição Artigo X | Três portas nomeadas | Quarta porta `FontePublica`, mesmo princípio, I/O que não existia na F0. Não é Redis/Celery. Registrar no estado |
| Artefato 5 §10.3 | IA só afirma o catálogo | Coleta **não** usa LLM. Extração estruturada ou falha |
| Comentário de `parametro_hotel` | Cita `periodicidade_coleta_mercado` | Chave nunca semeada. `0020` + bootstrap fecham |
| Pendência “verificar termos de uso” nos artefatos 4 e 5 | Um item só com o cadastro | Cadastro foi F5.1 (humano). Esta fatia recusa o que a diretiva publicada já proíbe; contrato jurídico em linguagem natural continua humano |
| `__main__` do worker | `MensageriaFalsa` no processo | Coletor falso na suíte; HTTP real não é chamado em teste. Limitação honesta igual à mensageria |

Clarify não rodou. Planejamento usou a spec (24 h, diretiva ausente = falha,
preço em destaque via dado estruturado, sem painel, sem disparo manual).
