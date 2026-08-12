# Fase 0 — Pesquisa e decisões técnicas: Cadastrar Reserva

Cada seção registra a decisão, por que ela foi tomada e o que foi rejeitado. As divergências
documentais encontradas no caminho estão consolidadas na seção 8.

---

## 1. Onde mora o nome digitado na criação

**Decisão**: na criação da reserva, o sistema cria **ao mesmo tempo** um hóspede titular
provisório (só `nome_completo` e `telefone`) e o vínculo em `reserva_hospede` com `titular =
true` e `ficha_completa = false`. O nome que a fila exibe é o `nome_completo` desse titular —
exatamente o que `vw_fila_do_dia` já espera.

**Rationale**: o backlog e a jornada pedem nome + telefone + datas; a fila precisa de um nome
antes da ficha completa; o modelo já declara que **toda reserva tem ao menos um hóspede** e a
visão da fila faz `LEFT JOIN` no titular. Criar o titular mínimo na mesma transação fecha a
lacuna **sem coluna nova** e sem inventar um segundo conceito de "nome de contato".

A F1.3 (interpretar a ficha) passa a **atualizar** esse hóspede titular, não a criar outro. É
consequência desejável: o telefone de correlação já está no lugar certo desde o primeiro clique.

**Alternativas consideradas**:

- **Coluna `nome_contato` em `reserva`**: exigiria migração, duplicaria o nome quando a ficha
  chegasse, e obrigaria a visão a um `COALESCE`. Resolve o sintoma criando um segundo lugar para
  o mesmo dado — Artigo XI recusa.
- **Guardar o nome só em memória/API até a F1.3**: a fila ficaria sem nome até o hóspede
  responder, o que viola FR-012 e esvazia o valor da fila no primeiro dia de uso.
- **Não criar `reserva_hospede` agora**: contradiz a cardinalidade 1:N obrigatória do modelo e
  deixa a visão da fila sem nome por construção.

**Consequência**: o cadastro é uma transação atômica de três escritas (`hospede`, `reserva`,
`reserva_hospede`). Falha em qualquer uma desfaz as outras — nenhum registro parcial (cenário de
aceite da US2).

---

## 2. Superfície desta fatia: API autenticada, sem tela React

**Decisão**: a fatia entrega **duas rotas HTTP** protegidas pela sessão já existente — criar
reserva e listar a fila do dia. **Não** liga o protótipo React nem entrega tela de login.

**Rationale**: a spec fixou que o critério de aceite é o comportamento observável, não a
tecnologia da superfície. O padrão das fatias de fundação (F0.1–F0.3) foi API + testes; o painel
React sem conteúdo útil atrás seria casco vazio outra vez — o mesmo argumento que adiou a tela de
login na F0.3. Com um desenvolvedor e prazo fixo (Artigo XI), a primeira gravação de domínio
precisa nascer testável ponta a ponta antes de competir com CSS.

**Alternativas consideradas**:

- **API + telas de cadastro e fila nesta mesma fatia**: honraria a previsão da F0.3 ("tela na
  F1.1"), mas dobraria o escopo e misturaria dois ciclos de TDD (backend e frontend) numa fatia
  que já carrega a primeira escrita de domínio e a conciliação do nome. Rejeitado.
- **Só repositório/serviço sem rota**: deixaria a autorização por perfil sem exercício real em
  HTTP — exatamente o buraco que a F0.3 registrou e pediu que a F1.1 fechasse.

**Consequência honesta (Artigo XV)**: a previsão da F0.3 de que a tela de login viria "junto da
primeira tela com conteúdo na F1.1" **escorrega**. A primeira tela com conteúdo fica para quando
o painel for ligado de propósito (fatia de UI ou início da F1.2). O comportamento de domínio
desta fatia continua exercitável por API, curl e suíte.

---

## 3. Forma canônica do telefone

**Decisão**: na borda, a aplicação:

1. Extrai só os dígitos do que a recepção digitou (ignora espaços, `()`, `-`, `+`).
2. Aceita 10 ou 11 dígitos nacionais (DDD + fixo/celular) **ou** 12/13 dígitos começando com
   `55`.
3. Grava sempre em forma canônica: dígitos com prefixo `55` (sem `+`), ex.: `5511987654321`.
4. Recusa qualquer outra coisa com mensagem clara, sem gravar.

O mesmo valor canônico vai para `reserva.telefone_contato` e para `hospede.telefone` do titular
provisório.

**Rationale**: a spec exige uma forma canônica única para o mesmo número (máscara visual não
pode criar dois registros "diferentes"). Prefixo `55` alinha com o que a mensageria WhatsApp
espera na F1.2, sem conversão surpresa depois. A validação mora na aplicação porque a mensagem
ao usuário precisa ser compreensível; o banco continua com `VARCHAR(20) NOT NULL`, sem `CHECK`
de formato — formato de telefone nacional muda e `CHECK` rígido vira migração recorrente.

**Alternativas consideradas**:

- **Biblioteca `phonenumbers`**: correta e completa, mas é dependência nova para um problema que
  o MVP delimita a Brasil. Artigo XI.
- **Gravar como digitado**: a mesma pessoa digitando `(11) 98765-4321` e `11987654321` geraria
  dois canônicos distintos e quebraria correlação futura com o webhook.
- **Só DDD nacional sem `55`**: adia a normalização para a F1.2 e cria risco de esquecer.

---

## 4. Datas: aplicação na borda, banco como rede de proteção

**Decisão**: o serviço recusa `data_checkout_prevista <= data_checkin_prevista` com mensagem
clara **antes** de escrever. O `CHECK ck_reserva_datas` no banco permanece como garantia contra
script e acesso direto (Artigo IX). Check-in no passado é permitido.

**Rationale**: a FR-004 pede recusa compreensível; restrição de banco sozinha vira erro 500 ou
mensagem de SQL. As duas camadas não se substituem.

---

## 5. Fila do dia: visão ampliada, consulta sempre com `id_hotel`

**Decisão**:

- A listagem usa a visão `vw_fila_do_dia` (ou consulta equivalente) **filtrada por
  `id_hotel` da sessão** e ordenada por `data_checkin_prevista` ascendente.
- A visão ganha duas colunas que o painel precisa e hoje não tem: `telefone_contato` e
  `data_checkout_prevista`. Isso exige revisão de migração e atualização do `04-schema.sql` na
  mesma entrega.
- `chegada_nao_confirmada` já existe na visão e cobre FR-008.

**Rationale**: a visão foi criada exatamente para "alimentar a tela inicial do turno". Entregar
a fila por SQL ad hoc no repositório e deixar a visão obsoleta criaria duas fontes. Ampliar a
visão é a correção mínima do documento à realidade da FR-006.

**Isolamento**: o filtro `id_hotel` é obrigatório na consulta da aplicação mesmo que a visão
exponha a coluna — Artigo XIV. Nunca se confia só no JOIN implícito.

---

## 6. Autorização: fila nominada versus contagem agregada

**Decisão**: duas superfícies distintas, duas operações distintas.

| Operação | Quem | Uso nesta fatia |
| --- | --- | --- |
| `alterar_reserva` | só `recepcao` | `POST` de criação (já na matriz da F0.3) |
| `ler_fila_do_dia` | só `recepcao` | `GET` da fila com nome e telefone — **nova** na matriz |
| `ler_indicadores` | `recepcao` e `gestor` | `GET` da **contagem** de chegadas do dia — já existia na matriz |

A gestão precisa saber **quantas** pessoas chegam para dimensionar equipe; não precisa saber
**quem** são. O endpoint de contagem devolve **somente um número**. A lista nominada nunca é
entregue ao perfil de gestão — nem “filtrada no frontend”: o dado cadastral não pode trafegar
até o cliente da gestão.

**Rationale**: misturar lista e indicador na mesma rota forçaria a gestão a receber (ou a UI a
esconder) nome e telefone — minimização de dados (Artigo VIII) e a decisão da F0.3 de que gestão
não lê ficha. Reusar `ler_indicadores` evita inventar permissão paralela para o primeiro
agregado do painel.

**Alternativas consideradas**:

- **Uma rota só, gestão vê lista sem nome**: ainda vaza telefone e padrão de chegada individual;
  rejeitado.
- **Gestão chama a fila e o frontend conta**: o payload completo trafega; rejeitado de propósito.
- **Operação nova `ler_contagem_chegadas`**: redundante com `ler_indicadores`, que já cobre
  recepção e gestão.

---

## 7. Módulo `hospedagem` e fronteiras

**Decisão**: nasce `app/modulos/hospedagem/` com `router`, `service`, `repository`, `schema`.
Governa `reserva`, `hospede` e `reserva_hospede` nesta fatia (consentimento continua intocado).
O módulo `acesso` só empresta sessão atual e `exigir_operacao` — hospedagem **não** importa
SQL de usuário/sessão.

`id_hotel` da reserva vem **sempre** de `SessaoAtual.id_hotel`, nunca do corpo da requisição.

**Rationale**: `AGENTS.md` já nomeia o módulo. Colocar reserva dentro de `acesso` ou
`propriedade` misturaria fronteiras na primeira fatia de domínio.

---

## 8. Divergências documentais encontradas

| Onde | O que está escrito | O que esta fatia faz | Correção |
| --- | --- | --- | --- |
| Spec F1.1 / backlog vs `04-schema.sql` | Cadastro pede nome; tabela `reserva` não tem nome | Nome vive no titular provisório | Documentar o fluxo em `04-modelagem-de-dados.md` (criação cria titular mínimo); sem coluna nova |
| `vw_fila_do_dia` | Sem telefone nem checkout | Ampliar a visão | Migração `0003` + `04-schema.sql` |
| DER mermaid em `04-modelagem` | Sugere `id_hotel` em `hospede` | Esquema real **não** tem; isolamento via `reserva.id_hotel` | Registrar no modelo que `hospede` ainda é global ao sistema no MVP; não expandir escopo para particionar hóspede agora |
| Plano F0.3 "O que não entrega" | Tela de login viria na F1.1 | F1.1 também sem tela | Atualizar essa linha no estado do projeto / nota na F0.3 quando conveniente; esta fatia declara a ausência honestamente |
| Artefato 2 R2 | Cadastro "dispara o template de coleta" | F1.1 **não** envia mensagem | Correto: disparo é F1.2; R2 descreve o processo completo, não o recorte da fatia |

---

## 9. Telefone repetido sempre cria hóspede novo

**Decisão**: cada `POST /reservas` faz `INSERT` de um `hospede` novo, mesmo quando já existe
linha com o mesmo telefone canônico. **Não há busca nem reaproveitamento** de cadastro pelo
número.

**Rationale**: um número pode ser de duas pessoas (casal que compartilha o celular, telefone de
empresa, secretária). Reusar pelo telefone misturaria fichas e consentimentos de gente diferente
sem o sistema ter como saber.

**Consequência registrada**: o mesmo indivíduo físico pode existir repetido em `hospede` ao longo
do tempo. Se um dia houver histórico “por pessoa”, será preciso um passo explícito de
**consolidação** — fora do escopo desta fatia e de qualquer deduplicação automática silenciosa.

**Alternativas consideradas**:

- **Reusar hóspede pelo telefone**: rejeitado pelos casos casal/empresa.
- **Perguntar à recepção se é a mesma pessoa**: atrito na entrada (R2) e UI que esta fatia não
  entrega; adiado indefinidamente até haver consolidação de verdade.

---

## 10. O que fica propositalmente de fora

Confirmado aqui para não voltar como "esquecimento" no meio da implementação:

- Envio WhatsApp / `reserva_cadastrada` como disparo de mensageria (F1.2)
- Interpretação da ficha e `ficha_completa = true` (F1.3)
- Cancelamento e edição de reserva
- Tela React / login no painel
- Consolidação de hóspedes duplicados / histórico por pessoa
- `id_hotel` na tabela `hospede`
