# Fase 0 — Pesquisa e decisões técnicas: linha de convite no recado

Cada seção registra a decisão, por que ela foi tomada e o que foi recusado.
Divergências documentais estão na seção 8.

---

## 1. Convite é a quarta chave de slot, não tabela nem constante

**Decisão**: chave `boas_vindas_convite` em `parametro_hotel`. Mesmo
`UNIQUE (id_hotel, chave)`, mesmo `validar_texto_de_boas_vindas` (vazio,
quebra de linha, tabulação, cinco espaços seguidos, teto 255). Entra em
`CHAVES_SLOTS_BOAS_VINDAS` ao lado de café, wi-fi e checkout.

Semente (bootstrap **e** migração, em todo hotel já instalado):

```text
Pode perguntar por aqui sobre servicos, cardapio e horarios.
```

**Rationale**: backlog F7.3 e Artigo XIII. Os três slots já são o molde.
Tabela nova (Artigo XI) e constante de produto (a casa não escreveria)
foram recusados na spec.

**Alternativas consideradas**:

- **Constante em `texto_boas_vindas.py`**: é o que existe hoje. A fatia
  existe para acabar com isso.
- **Chave `personalidade_assistente` reusada**: naturezas diferentes
  (tom no prompt vs. linha no recado; gestão vs. recepção). Rejeitado.
- **Teto 500**: os três slots recusam em 255; o canal de template também.
  Igualar a 255. O `VARCHAR(500)` da F7.2 não afrouxa esta validação.

---

## 2. A mesma operação, o mesmo par GET/PUT, quatro campos

**Decisão**: `GET`/`PUT /propriedade/boas-vindas` passam a exigir e
devolver `convite` junto com `cafe`, `wifi` e `checkout`. Operações
intocadas: `ler_texto_de_boas_vindas` e `alterar_texto_de_boas_vindas`.
Gravação continua atômica: um campo recusado não altera nenhum dos
quatro. Sem tela. Sem operação nova na matriz. Nenhuma operação ganha a
substring `parametro`.

**Rationale**: a spec manda a recepção usar a operação já existente.
Permissão nova seria ruído. PUT de três campos deixa de ser válido —
cliente antigo toma `422`; é o ponto da fatia, não um acidente.

**Alternativas consideradas**:

- **Rota `/propriedade/boas-vindas/convite`**: segunda superfície para o
  mesmo recado. Rejeitado (Artigo XI).
- **Campo opcional no PUT**: “nunca fica vazia” viraria omissão
  silenciosa. Rejeitado.

---

## 3. A frase fixa sai; o aviso fica; a última linha é o valor

**Decisão**: `montar_texto_boas_vindas` ganha parâmetro `convite`.
Estrutura:

```text
Ola, {prenome}! Sua chegada esta confirmada, seja bem-vindo.
Cafe da manha: {cafe}
Wi-Fi: {wifi}
Checkout: {checkout}
{AVISO_ASSISTENTE_VIRTUAL}
{convite}
```

A frase `Quer saber mais alguma coisa da sua estadia? Pode perguntar por
aqui.` **some**. Sem rótulo `Convite:` — a última linha é só o texto da
casa. A constante de aviso **não** ganha parâmetro nem chave. Assinatura
continua sem `aviso`, `tom`, `personalidade`, `catalogo`.

A regra “exatamente uma `?` na última linha” **morre**. Os testes
`test_texto_confirma_chegada_traz_tres_fatos_e_um_convite` e
`test_texto_traz_aviso_de_assistente_virtual` deixam de exigir `?` e
passam a exigir: última linha = `convite`; aviso imediatamente antes;
frase antiga ausente.

**Rationale**: spec FR-008, FR-009 e a assumption do rótulo. Um segundo
convite do produto ao lado do da casa mentiria para o hóspede.

**Alternativas consideradas**:

- **Prefixo `Pergunte:` + valor**: a spec manda a última linha ser o
  convite gravado. Rejeitado.
- **Aviso virar variável**: F7.1 fixou texto de produto. Rejeitado.

---

## 4. A tupla da porta passa a cinco valores

**Decisão**: `MensageriaGateway.enviar_boas_vindas` muda
`variaveis: tuple[str, str, str, str]` para
`tuple[str, str, str, str, str]` =

`(prenome, cafe, wifi, checkout, convite)`.

Os três adaptadores (`MensageriaFalsa`, `MensageriaSimulada`,
`MensageriaWhatsapp`) e o worker em
`processar_trabalho_enviar_boas_vindas` acompanham. A falsa registra
`convite` no dict do envio. Asserções `len(envio["variaveis"]) == 4`
viram `== 5`.

`agendar_boas_vindas` e o processamento leem as **quatro** chaves. Falta
ou inválido de qualquer uma (incluindo `boas_vindas_convite`) →
`nao_enviada_slot_ausente` / `slot_invalido`, sem montar recado, sem
trabalho. A visão `vw_fila_do_dia` **não muda**: já marca hospedado sem
trabalho de boas-vindas.

**Rationale**: o adaptador WhatsApp já itera a tupla. Crescer a tupla é
o que faz o canal real receber a linha da casa (FR-015). Quatro valores
com o convite só no `corpo` repetem a mentira da F7.1 (o WhatsApp
descarta o `corpo`).

**Alternativas consideradas**:

- **Convite só no `corpo`**: simulador e histórico ok; WhatsApp não.
  Contradiz FR-015. Rejeitado.
- **`tuple[str, ...]`**: enfraquece o contrato. Rejeitado.

---

## 5. Template Meta `boas_vindas` republicado com cinco variáveis

**Decisão**: o adaptador continua a chamar o template de nome
`boas_vindas`, agora com **cinco** parâmetros de corpo, nesta ordem.
O operador precisa ter aprovado na Meta o corpo abaixo (texto congelado
+ variáveis). Até republicar, o Graph recusa a chamada (contagem de
parâmetros) — `FalhaDeEnvio`, recado não chega errado.

Corpo a submeter:

```text
Ola, {{1}}! Sua chegada esta confirmada, seja bem-vindo.
Cafe da manha: {{2}}
Wi-Fi: {{3}}
Checkout: {{4}}
O atendimento inicial e feito por uma assistente virtual. Uma pessoa da recepcao assume quando necessario.
{{5}}
```

O aviso entra como texto **congelado** do produto (não é variável, não é
editável). {{5}} é a última linha, o convite da casa. A suíte **não**
chama a Graph: um unitário com `MockTransport` prova que o POST leva
cinco parâmetros na ordem. O texto congelado não viaja no JSON — vive
na Meta; o contrato o documenta.

**Rationale**: FR-015 + Artigo XV. A F7.1 deixou o aviso de fora do
WhatsApp de propósito, porque não republicou. Esta fatia **precisa**
republicar por causa da quinta variável; aproveitar a mesma submissão
para o aviso congelado fecha o buraco sem chave nova e sem segunda
chamada.

**Alternativas consideradas**:

- **Nome `boas_vindas_v2` + env**: config a mais sem problema presente
  no código. Rejeitado (Artigo XI). Se a Meta exigir outro nome, isso é
  achado operacional, não desenho desta fatia.
- **Mensagem `type=text` em vez de template**: quebra a janela de
  utilidade do recado de chegada. Rejeitado.
- **Não republicar, só o simulador**: a spec recusou explicitamente.

---

## 6. Revisão `0023`, sem tabela, sem visão nova

**Decisão**: `0023_convite_boas_vindas`. `INSERT` da chave com a semente
em todo `hotel` que ainda não a tem. `COMMENT ON TABLE parametro_hotel`
passa a listar `boas_vindas_convite`. Cópia em `docs/04-schema.sql` no
mesmo commit. `0001`…`0022` intactos. Sem `ALTER` de coluna (o teto 255
já cabe em `VARCHAR(500)`). Sem mudança em `vw_fila_do_dia`.

**Rationale**: propriedade já instalada não pode ficar sem a chave —
o recado pararia em massa (FR-007). Comentário e documento divergentes
quebram `test_conformidade_do_esquema` de propósito.

**Alternativas consideradas**:

- **Só o bootstrap**: hotel migrado ficaria sem chave. Rejeitado.
- **`UPDATE` da frase antiga em `mensagem` já enviada**: unicidade e
  histórico. Rejeitado (FR-014).

---

## 7. Sem módulo novo, sem React, sem tipo de trabalho novo

**Decisão**: toca `propriedade` (semente, validação, schema HTTP),
`conversa` (montagem, agendar, processar), porta e três adaptadores,
matriz já existente, fixtures de teste que semeiam três slots.
`horas_validade_boas_vindas` e o agendador `--verificar-boas-vindas`
continuam como estão — passam a exigir o quarto slot porque leem a
mesma tupla de chaves.

**Rationale**: Artigo XI. A recuperação já existe; o convite vazio é
mais um `slot_invalido`.

---

## 8. Divergências documentais

Nenhuma correção de artefato nesta fatia além do `COMMENT` e da lista
de chaves em `04-schema.sql`, que é o delta da revisão.

O contrato F2.2 (`specs/009-confirmar-chegada/contracts/boas-vindas-fila-e-porta.md`)
descreve três slots e uma `?` na última linha. **Não se reedita** aquele
arquivo: a verdade vigente passa a ser os contratos desta pasta. O
estado do projeto (`docs/00-ESTADO-DO-PROJETO.md`) atualiza-se na
implementação, não aqui.
