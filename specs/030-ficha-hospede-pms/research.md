# Fase 0 — Pesquisa e decisões técnicas: ficha e transcrição

Cada seção registra a decisão, por que ela foi tomada e o que foi recusado.
Divergências documentais estão na última seção.

---

## 1. Uma rota nova de gravação; o resto já existe

**Decisão**: a tela consome o que já está entregue e **uma** escrita
nova, na operação que a matriz já reserva à recepção:

| Ação na tela | Rota | Operação | Fatia |
| --- | --- | --- | --- |
| Abrir a ficha | `GET /reservas/{id}/ficha` | `ler_ficha_de_hospede` | F1.3 (reuso) |
| Gravar no balcão | `PUT /reservas/{id}/ficha` | `alterar_ficha_de_hospede` | **esta** |
| Ver consentimento | `GET /hospedes/{id}/consentimento` | `ler_consentimento` | F4.1 (reuso) |
| Revogar / registrar aceite | `POST /hospedes/{id}/consentimento` | `registrar_consentimento` | F4.1 (reuso) |

`alterar_ficha_de_hospede` já está na matriz (só `recepcao`) e **não
tem rota**. Esta fatia a liga. Cookie `omnistay_sessao` via
`pedirAutenticado`. Sem operação nova na matriz.

**Rationale**: a spec reusa leitura e consentimento. Completar no
balcão é o buraco: `atualizar_hospede_titular` só é chamado pela
interpretação da mensagem. Artigo XI — uma rota, não um módulo.

**Alternativas consideradas**:

- **`PATCH /hospedes/{id}`**: a completeza mora em `reserva_hospede`
  (`ficha_completa`) e o isolamento é pela reserva do hotel. O GET
  já é por reserva. Rejeitado.
- **Gravar só no cliente (localStorage)**: a fila e a próxima visita
  não veriam o completar. Rejeitado.
- **Reusar `POST` de webhook / interpretação**: dispararia caminho de
  mensagem. A spec proíbe nova rodada ao hóspede.

---

## 2. Completar no balcão atualiza a máquina `ficha_parcial` ↔ `ficha_recebida`

**Decisão**: quando os nove campos ficam utilizáveis e a reserva ainda
está em `ficha_parcial`, o serviço transiciona para `ficha_recebida` e
marca `ficha_completa = true`. O inverso (apagar um campo utilizável)
volta a `ficha_parcial` e `ficha_completa = false`.

Hoje o gatilho **recusa** `ficha_parcial → ficha_recebida`. Sem essa
passagem, a fila continua com `estado_cadastro = parcial` (a visão
deriva isso de `status`), e SC-004 falha. Revisão Alembic `0024` +
`docs/04-schema.sql` (o teste de conformidade compara o corpo da
função).

Estados que **não** mudam por esta gravação:

| Status atual | Efeito da gravação |
| --- | --- |
| `aguardando_cadastro` | Já admite ir a `ficha_recebida` / `ficha_parcial` — reusa |
| `sem_cadastro_previo` | Permanece; só `ficha_completa` |
| `hospedado` / `encerrado` / `cancelada` | Permanece; só `ficha_completa` |

Não confirma chegada nem saída. Não enfileira coleta nem recado.

**Rationale**: Artigo IX (a transição mora no gatilho, não só na
tela) e Artigo V (a pendência some onde já era visível). Situação e
coluna ficha na fila precisam concordar — só virar o booleano deixaria
“ficha parcial” na situação e “completa” na ficha.

**Alternativas consideradas**:

- **Só `ficha_completa`, sem tocar `status`**: a visão não muda o
  rótulo da fila. Rejeitado (SC-004).
- **Mudar `vw_fila_do_dia` para olhar o booleano e deixar o status
  mentir**: duas verdades na mesma linha. Rejeitado.
- **Novo status `transcrita`**: a spec não inventa fase. Rejeitado.

---

## 3. Validação dos nove campos é a da coleta, sem ciclo de import

**Decisão**: `PUT` passa pelos mesmos critérios de
`validar_campos_extraidos` / `classificar_desfecho` (tipo RG/CPF/
passaporte, nascimento passado, CEP com oito dígitos, telefone
brasileiro). Completa = os nove de `CAMPOS_FICHA_CHAVE` utilizáveis.

`conversa.service` já importa `hospedagem`. O PUT **não** importa
`conversa.service`. Funções puras de `conversa.validacao_ficha` podem
ser chamadas se o pacote não puxar o service; se puxar, **mover** o
arquivo puro para `app/modulos/hospedagem/validacao_ficha.py` e
ajustar o import da conversa — um arquivo, dois chamadores. Sem
cópia da regra.

Campo vazio no formulário vira ausência (NULL nos opcionais). Nome
completo e telefone continuam NOT NULL: recusa se vierem em branco.
Idade nunca entra no corpo. E-mail não existe no contrato.

Telefone da ficha atualiza `hospede.telefone`, **não**
`reserva.telefone_contato`.

Documento (tipo + número) que bata no índice único: recusa `409` (ou
`422` se a API já usar isso para dado inválido — o recado é o mesmo:
não funde fichas), sem eco do número no log.

**Rationale**: F1.3 já fechou o formato. Duas escritas, uma regra.

**Alternativas consideradas**:

- **Validar só no frontend**: o PUT direto furaria. Rejeitado.
- **Pedir foto “para conferir”**: Artigo VIII. Rejeitado.

---

## 4. Copiar tudo = texto rotulado no cliente; uma variação

**Decisão**: função pura monta nove linhas `Rótulo: valor` (valor
vazio se o campo estiver ausente). A tela chama
`navigator.clipboard.writeText`. Se a cópia automática falhar, o
mesmo texto fica visível e selecionável (`<pre>` ou equivalente).

Sem ordem configurável, sem copiar um campo por vez, sem POST ao
PMS. Vitest mocka `clipboard`.

**Rationale**: spec FR-015–018. Artigo I e XV: ponte humana, uma
variação. Artigo XI: a API não precisa de rota “exportar”.

**Alternativas consideradas**:

- **Tabulação entre campos / CSV**: achado de campo; a spec entregou
  bloco rotulado. Rejeitado nesta fatia.
- **Rota que devolve `text/plain`**: extra round-trip para o que a
  tela já tem. Rejeitado.

---

## 5. Destino `/app/ficha` e `/app/ficha/:idReserva`

**Decisão**: o mapa da F8.1 permanece `caminho: "/app/ficha"`. A
casca passa a aceitar parâmetro opcional (`/ficha/:idReserva?`).
Menu e visita sem id: estado vazio, **zero** `GET` de ficha.
`Ver ficha` na linha da fila navega para `/app/ficha/{id_reserva}`.

`destinoPorCaminho` trata prefixo `/app/ficha` como o destino ficha,
para staff/gestão colando `/app/ficha/12` continuarem recusados pela
casca **antes** do fetch.

Voltar: atalho visível para `/app/fila`. Depois de gravar, a própria
tela mostra o novo estado; a fila, ao ser aberta de novo, já vem do
`GET /fila-do-dia` (não precisa de cache).

**Rationale**: FR-001, FR-002. Não inventar segunda lista nominada
no item de menu.

**Alternativas consideradas**:

- **Query `?reserva=`**: o path da casca continuaria exato, mas o
  id some do histórico de forma feia. Prefixo no destino é um ajuste
  local. Rejeitado o query como principal.
- **Modal em cima da fila**: o mapa já tem destino próprio. Rejeitado.

---

## 6. Consentimento na ficha = vigente da F4.1

**Decisão**: depois do `GET` da ficha, `GET /hospedes/{id_hospede}/consentimento`
sem `em` (agora). Distinguir na tela:

| JSON | Rótulo |
| --- | --- |
| `concedido: true` + `momento` | concedido em {data} |
| `concedido: false` + `momento` | recusado em {data} |
| `concedido: false` sem `momento` | nunca registrado (sem aceite) |

Revogar: `POST` `{ "concedido": false, "origem": "painel" }`.
Aceite no balcão: `{ "concedido": true, "origem": "painel" }`.
Não enviar `pesquisa_checkout`. Não disparar mensagem.

Gestão **não** monta esta tela (não tem `ler_ficha_de_hospede`). A
consulta de consentimento que a gestão já tem pela API permanece;
esta fatia não cria tela de gestão.

**Rationale**: FR-019–021. Reuso literal do contrato F4.1.

**Alternativas consideradas**:

- **Embutir consentimento no JSON da ficha**: duas operações, dois
  recortes de autorização (gestão lê consentimento e não lê ficha).
  Misturar furaria a matriz. Rejeitado.

---

## 7. Teste: pytest na escrita nova; Vitest na tela

**Decisão**:

- **pytest**: `PUT` aceita/recusa; completa `ficha_parcial` →
  `ficha_recebida` sem mensagem na fila de trabalho; status
  `hospedado` não muda; gatilho passa a admitir o vai-e-vem;
  transição inválida antiga continua recusada; staff/gestão `403`;
  outro hotel `404`; documento duplicado não funde; log sem nome/
  documento/telefone. Consentimento: regressão F4.1, sem reabrir
  regra. `GET` da ficha intocado no contrato.
- **Vitest**: campos ausentes nomeados; distintivo completa/parcial;
  idade derivada e ausente do texto de cópia; copiar chama clipboard
  (falso); fallback selecionável; gravar não dispara fetch de
  mensagem; menu `/ficha` sem id não busca; `Ver ficha` na fila
  navega; staff/gestão não montam a tela. `fetch` falso.
- **Playwright**: não. Como F8.1/F8.2.

**Rationale**: Artigo XII na superfície e na rota novas. Artigo XI
contra lente de seis telas.

---

## 8. Casca especializa `ficha`; a fila ganha um controle

**Decisão**: `destino.id === "ficha"` → `TelaFicha`. Na `TelaFila`,
botão/link rotulado **Ver ficha** em cada linha (além de Confirmar
chegada quando couber). Clique em nome/telefone **continua** sem
confirmar chegada (F8.2). Não precisa ser o mesmo clique da ficha —
o rótulo novo é o caminho.

Mocks da casca: `GET /reservas/:id/ficha` e consentimento só se algum
teste abrir `/ficha/…`. `/ficha` vazio não pode 404 de “TelaNomeada
sumiu” — é estado vazio.

**Rationale**: FR-001. F8.2 adiou “Ver ficha” de propósito
(research § divergências da 029).

---

## Divergências documentais

1. **Wireframe com e-mail opcional.** Spec e F7.5 cortam. O plano
   segue a spec.
2. **`docs/00-ESTADO-DO-PROJETO.md` e a jornada ainda dizem que
   copiar ficha é evolução futura.** A F8.3 do backlog e a spec desta
   fatia puxam **uma** variação. Sinalizar no estado do projeto na
   implementação (não neste plan): a decisão antiga ficou para ordem
   configurável e cópia campo a campo, não para “copiar tudo”.
3. **Wireframe “Editar” como secundário.** A spec trata editar como
   P1 (completar no balcão). Copiar continua o gesto principal
   visual; editar não é opcional.
4. **Idade no rodapé do wireframe.** Só derivada na exibição; nunca
   no JSON nem no texto copiado como campo próprio.
5. **Acompanhantes.** O SQL admite N hóspedes; o MVP e a spec são
   só o titular. Sem tela de acompanhante.
