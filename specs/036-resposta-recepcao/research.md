# Research: A recepção responde ao hóspede

## 1. Duas rotas novas em `/reservas/{id}`, não um envelope na ficha

**Decisão**: `GET /reservas/{id_reserva}/conversa` lista o histórico
e a janela. `POST /reservas/{id_reserva}/respostas` grava e
enfileira. `GET /reservas/{id}/ficha` **não muda** o JSON (F8.3).
A Estadia chama a conversa ao abrir; a ficha só ao expandir
**ver dados cadastrais**.

**Rationale**: quem chega de um chamado veio responder (FR-019).
Misturar nove campos no mesmo GET atrasaria a conversa e
convidaria a tela a renderizar cadastral no topo. Artigo XI: não
inventar recurso “estadia completa”.

**Alternativas recusadas**:

- **Um GET só com ficha+conversa**: a tela puxaria documento
  sempre. Recusado (clarificação).
- **POST no webhook / simulador**: a recepção não é o hóspede.
  Recusado.
- **Enviar do browser ao WhatsApp**: viola gravar-antes-de-enviar
  e a porta. Recusado.

---

## 2. Tipo `enviar_resposta_recepcao` na fila

**Decisão**: novo valor em `ck_trabalho_tipo`. Payload
`{id_reserva, id_mensagem}` — só IDs. UNIQUE
`uq_trabalho_enviar_resposta_recepcao_mensagem` em
`(payload->>'id_mensagem')` onde `tipo` é esse. Allowlist e
`elif` no consumidor **juntos**. Processador lê o `conteudo` já
gravado e chama o mesmo `enviar_texto_sessao` das outras
enviadas. HTTP **não** espera o worker.

**Rationale**: todas as saídas já nascem `mensagem.pendente` +
`trabalho`. Reusar o helper de envio (F3.6) evita segunda porta.
UNIQUE por mensagem impede segundo trabalho do mesmo texto
gravado, não impede segunda resposta distinta (outro INSERT de
mensagem). **Proibido** índice único por `id_reserva` (padrão das
boas-vindas): várias respostas por estadia são legítimas.

Clique duplo: (1) o botão **Enviar** fica inerte enquanto o POST
não volta; (2) o serviço recusa texto **idêntico** ao da última
`resposta_recepcao` daquela reserva se `enviada_em` da anterior
está dentro de `SEGUNDOS_ANTI_DUPLO = 5` (`409` `texto_repetido`).
Não é UNIQUE no banco.

**Alternativas recusadas**:

- **Reusar `enviar_confirmacao_resolucao`**: recado padrão, unique
  por solicitação, dispararia conclusão. Recusado (FR-007).
- **Worker intocado**: o CHECK recusaria o INSERT. Recusado.
- **Celery/Redis**: Artigo XI e stack fixa.

---

## 3. Origem da mensagem: `classificacao_bruta.tipo`, sem coluna

**Decisão**: enviada da recepção nasce com
`classificacao_bruta = {"tipo": "resposta_recepcao"}` (sem o
texto). O GET deriva:

| `direcao` | `tipo` no JSON | `origem` na API |
| --- | --- | --- |
| `recebida` | qualquer | `hospede` |
| `enviada` | `resposta_recepcao` | `recepcao` |
| `enviada` | outro ou ausente | `automatico` |

`ck_mensagem_direcao` permanece `recebida` / `enviada`.

**Rationale**: as enviadas automáticas já marcam `tipo` no JSON
(`confirmacao_resolucao`, aviso de dúvida, etc.). Terceira
direção exigiria CHECK e migrar o histórico. Artigo IX: domínio
de valor no CHECK que já existe; o `tipo` no JSON é o mesmo
padrão da F3.6.

**Alternativas recusadas**:

- **Coluna `origem`**: migração extra sem ganho observável.
- **Inferir “sem JSON = recepção”**: coletadas e boas-vindas
  antigas quebrariam.

---

## 4. Janela de 24 horas: constante do canal + relógio

**Decisão**: `JANELA_SESSAO_CANAL_HORAS = 24` em `conversa`.
Aberta se existe `mensagem` `recebida` desta reserva com
`enviada_em >= agora() - 24h`. Nunca escreveu → fechada,
`motivo=nunca_escreveu`. Escreveu há mais de 24 h →
`sem_mensagem_recente`. O serviço usa `app.comum.relogio.agora`.
A tela **só lê** `janela.aberta` e `janela.motivo`. Não entra em
`parametro_hotel`.

**Rationale**: clarificação — é o comportamento do canal, não
permissão de negócio. Hotel configurando 48 h faria o OmniStay
afirmar entrega que o canal recusa (Artigo XV). Artigo XIII pede
parâmetro para prazo **da propriedade** (pulso, reenvio); esta
janela não é da propriedade.

**Alternativas recusadas**:

- **Só tentar enviar e deixar o canal falhar**: a spec exige
  motivo visível **antes** (FR-018).
- **Chave em `parametro_hotel`**: contradiz a spec.
- **Calcular 24 h no cliente**: relógio do browser e fuso.

POST com janela fechada: `409` com código `janela_fechada`. Texto
vazio: `422`. Texto acima de 4096 caracteres (limite do canal):
`422`. Constante `TAMANHO_MAXIMO_TEXTO_CANAL = 4096` no mesmo
módulo.

---

## 5. `precisa_atendimento_humano` depois da resposta humana

**Decisão**: a `0025` recria `vw_fila_do_dia`. O booleano
permanece `hospedado` + recebida com desfecho humano **e**
`enviada_em` **posterior** à última enviada com
`tipo=resposta_recepcao` (ou nenhuma resposta humana ainda).
Desfechos da lista atual permanecem
(`encaminhado_humano`, `formato_invalido`, `indisponivel`,
`duvida_nao_coberta`, `item_ambiguo`,
`identificacao_indisponivel`).

**Rationale**: FR-010. Flag persistida em `reserva` foi recusada
na F3.2. Uma resposta atende as encaminhadas **já ocorridas**;
mensagem nova depois da resposta reacende.

**Alternativas recusadas**:

- **Apagar ou reescrever o desfecho da recebida**: destrói
  auditoria da classificação.
- **Sinal some só no cliente**: a API da fila mentiria.

---

## 6. Fronteira de módulo e autorização

**Decisão**: serviço e repositório em `conversa`. Rotas no
roteador de `conversa` (prefixo `/reservas/{id_reserva}/…`).
Operações novas, só `recepcao`:

- `ler_conversa_da_estadia`
- `enviar_resposta_recepcao`

`ler_ficha_de_hospede` intacta. Staff/gestão: `403` nas duas
novas; casca não monta Estadia para eles (já não monta ficha).

**Rationale**: `conversa` já governa `mensagem`. Hospedagem não
escreve SQL nela. Reserva alheia: JOIN `reserva.id_hotel` →
`404` genérico (padrão ficha).

---

## 7. Superfície: Estadia no destino `ficha`

**Decisão**: `destinos.ts` — `id` e `caminho` `/app/ficha`
intactos; `titulo` **Estadia**. Componente `TelaEstadia` (substitui
`TelaFicha` nesse destino). Com id: conversa no topo (GET
conversa); cadastral recolhido; **ver dados cadastrais** dispara
GET ficha + consentimento como hoje. Sem id: título Estadia;
texto de que se abre pela fila / Chamados e pedidos; zero GET.
Atalhos **Ver ficha** na fila, alertas e consumos passam a
**Estadia** (mesmo `to={/ficha/:id}`).

**Rationale**: clarificação. Path estável evita quebrar a casca e
os testes de navegação. Nome no menu descreve o que a tela é.

**Alternativas recusadas**:

- **Destino novo `/app/estadia`**: spec FR-014.
- **Campo só na linha do chamado**: sem histórico (US2).

---

## 8. Log: identificadores e resultado, nunca corpo

**Decisão**: `resposta_recepcao_enfileirada` /
`resposta_recepcao_enviada` / `resposta_recepcao_envio_falhou` com
`id_trabalho`, `id_mensagem`, `id_reserva`, `id_hotel`, código.
Sem `conteudo`, sem nome, sem telefone. `console` da tela sem o
texto.

**Rationale**: Artigo VIII e FR-015. O GET devolve o corpo à
recepção autenticada; log operacional não.

---

## 9. Simulador e testes sem rede

**Decisão**: o worker de demonstração já usa
`MensageriaSimulada`. A resposta humana aparece no fio do
simulador como as outras enviadas. Suíte: `MensageriaFalsa` +
relógio. Vitest: `fetch` falso. Sem Playwright.

**Rationale**: Artigo X. Quickstart manual com worker no ar é
opcional para ver o simulador; os testes não dependem disso.
