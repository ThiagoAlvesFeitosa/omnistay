# Pesquisa — F2.2 Confirmar Chegada e Boas-vindas

Decisões técnicas tomadas antes de escrever teste. Cada uma traz o que foi escolhido, por
quê, e o que foi recusado. Nada aqui é preferência estética: tudo tem consequência em teste
ou em risco operacional.

---

## 1. A operação de autorização do check-in já existe

**Decisão:** a confirmação de chegada usa `confirmar_fase_da_reserva`, que já está na matriz
de `app/modulos/acesso/politica.py` reservada a `recepcao`. **Nenhuma operação nova** para o
clique de chegada.

**Rationale:** a F0.3 previu a operação e ninguém a consumiu ainda. Ela existe exatamente
para isto. FR-021 (só recepção confirma) fica satisfeito pela matriz vigente.

**Alternativas recusadas:** criar `confirmar_chegada` — deixaria a operação da F0.3 órfã e
duplicaria significado; reusar `alterar_reserva` — confundiria "editar dado da reserva" com
"transicionar fase", e a matriz já separa os dois.

## 2. Duas operações novas, restritas às três chaves

**Decisão:** `alterar_texto_de_boas_vindas` (`recepcao`) e `ler_texto_de_boas_vindas`
(`recepcao`, `gestor`).

**Rationale:** a clarificação exige permissão por **grupo de chaves**. O par
escrita/leitura segue o padrão já existente `alterar_catalogo` / `ler_catalogo`.

**Alternativas recusadas:** `alterar_parametro_hotel` genérico — daria à recepção o poder de
mudar `horas_ate_reenvio`, `horas_corte_antes_checkin` e duração de sessão, isto é, como o
sistema se comporta com o hóspede; reusar `ler_catalogo` para ler os slots — os slots não são
catálogo, e amarrar as duas leituras faria uma mudança futura de perfil vazar para a outra.

## 3. Rota de confirmação: `POST /reservas/{id_reserva}/chegada`

**Decisão:** sub-recurso de fase, com `POST`. Corpo vazio. Resposta `200` com o status novo,
o instante gravado e o desfecho das boas-vindas.

| Situação | Código | Por quê |
| --- | --- | --- |
| Confirmação aceita | `200` | Recurso já existia; não nasce entidade nova para o cliente |
| Estado não admite (encerrada, cancelada, hospedada, aguardando cadastro) | `409` | Conflito de estado, não erro de formato |
| Reserva de outro hotel ou inexistente | `404` | FR-022: não confirma existência alheia |
| Perfil sem permissão | `403` | Matriz |

**Alternativas recusadas:** `PATCH /reservas/{id}` com `status` no corpo — deixaria o cliente
escolher o estado destino e transformaria a máquina de estados em campo editável; `422` para
estado inválido — o dado enviado está correto, o estado é que não permite.

## 4. Recusa por estado: aplicação decide, banco protege

**Decisão:** `UPDATE reserva SET status='hospedado', checkin_em=now() WHERE id_reserva=:id
AND id_hotel=:id_hotel AND status IN ('ficha_recebida','ficha_parcial','sem_cadastro_previo')`.
O `rowcount` distingue aceito de recusado.

**Rationale:** o `WHERE` com os estados de origem faz três coisas de uma vez — aplica a regra,
resolve concorrência (duas confirmações simultâneas: só a primeira atualiza) e nunca tenta uma
transição que a trigger `tg_valida_transicao_reserva` recusaria. A trigger continua sendo a
garantia real (Artigo IX): se um script direto tentar `aguardando_cadastro → hospedado`, o
banco recusa mesmo sem passar por aqui.

**Alternativas recusadas:** `SELECT` do status e depois `UPDATE` sem guarda — janela de corrida
entre a leitura e a escrita; confiar só na trigger e tratar a exceção — a mensagem de erro do
banco não é resposta de usuário, e o `rowcount` já basta para distinguir os casos.

## 5. Instante da chegada vem do banco

**Decisão:** `checkin_em = now()` no próprio `UPDATE`. Coluna já existe na `reserva`.

**Rationale:** mesmo critério de `criado_em`. Evita divergência de fuso entre processo e banco,
e o teste verifica o que a spec pede — que o instante seja o da confirmação, não a data
prevista (`checkin_em::date` pode até coincidir; o que se afirma é que é um `TIMESTAMPTZ`
gravado no ato).

**Alternativa recusada:** `relogio.agora()` injetável no caminho da confirmação — o instante
gravado não precisa ser controlado pelo teste, e injetar relógio ali seria mecanismo sem
problema correspondente (Artigo XI).

**Onde o relógio *é* injetável:** na varredura de recuperação (§11), que compara `checkin_em`
com uma janela e por isso precisa que o teste posicione o instante — inclusive do outro lado da
meia-noite. Mesmo parâmetro `agora` de `verificar_cadastros_pendentes`.

## 6. Três slots em `parametro_hotel`, sem tabela nova

**Decisão:** chaves `boas_vindas_cafe`, `boas_vindas_wifi`, `boas_vindas_checkout`.
`VARCHAR(255)` da coluna `valor` já força brevidade. Escrita por
`upsert_parametro` (`INSERT ... ON CONFLICT (id_hotel, chave) DO UPDATE`), aproveitando a
restrição `uq_parametro_hotel_chave` existente.

**Rationale:** é configuração operacional por propriedade — a definição da tabela. Tabela nova
seria terceira descrição do mesmo conceito.

**Alternativas recusadas:** marcar itens do catálogo como "informação de entrada" — o texto
fixo do template congela na aprovação da Meta, então slot móvel exigiria template novo, e
`catalogo_item.conteudo` é `TEXT` livre com quebra de linha, justamente o que a variável
recusa; colunas em `hotel` — engessaria a evolução e fugiria do padrão de configuração.

## 7. Validação na gravação, com a regra do canal

**Decisão:** função pura recusa valor que seja vazio depois de `strip`, ou contenha `\n`,
`\r`, `\t`, ou quatro espaços seguidos ou mais, ou passe de 255 caracteres. Aplicada no
`service` de propriedade, no caminho da gravação.

**Rationale:** a Cloud API recusa parâmetro de template com quebra de linha, tabulação, mais
de quatro espaços consecutivos ou vazio. Validar só no envio faria a falha coincidir com a
chegada do hóspede, quando ninguém está olhando a configuração — é a falha silenciosa que o
projeto combate.

**Detalhe da regra:** "mais de 4 espaços consecutivos" é proibido, logo o limite aceitável é
4. A verificação recusa a partir de 5 (`"     "`).

**Alternativa recusada:** validar nos dois pontos com regra duplicada — a montagem **verifica
presença e validade** antes de enviar (defesa contra valor entrado por SQL direto ou semeadura
malfeita), mas reusa a mesma função pura; não há segunda regra.

## 8. `PUT` dos três juntos, não `PATCH` de um

**Decisão:** `PUT /propriedade/boas-vindas` exige os três campos. `GET` devolve os três.

**Rationale:** os três são obrigatórios para a mensagem sair. Aceitar gravação de um só
permitiria estado parcial válido na API e inválido para o envio — a recepção "salvou com
sucesso" e a mensagem continua não saindo.

**Alternativa recusada:** `PATCH` por chave — mais chamadas, mais estados intermediários, e o
ganho (editar um campo) não paga o risco.

## 9. Tipo de trabalho novo e unicidade por índice

**Decisão:** tipo `enviar_boas_vindas` no `ck_trabalho_tipo` e
`uq_trabalho_enviar_boas_vindas_reserva` — índice único parcial em
`((payload->>'id_reserva')::bigint) WHERE tipo = 'enviar_boas_vindas'`.

**Rationale:** é literalmente o padrão já usado por `enviar_coleta` e `enviar_lembrete`, e é a
garantia exigida pela clarificação: duas execuções concorrentes do worker (ou dois cliques
simultâneos) não produzem dois pacotes, porque a segunda inserção viola o índice. Verificação
prévia em código não resolveria — as duas passariam pela checagem antes de qualquer uma
inserir.

**Tratamento da violação:** a inserção do trabalho acontece dentro de `begin_nested()`
(savepoint). `IntegrityError` é capturada, o savepoint volta, registra-se log de
`boas_vindas_ja_agendadas` e o fluxo segue — a confirmação **não** falha por causa disso.
Sem o savepoint, a exceção abortaria a transação inteira e desfaria o check-in.

## 10. Quem dispara a recuperação: o agendador

**Decisão:** função `verificar_boas_vindas_pendentes` em `worker/agendador.py`, com opção
`--verificar-boas-vindas`, no molde de `verificar_cadastros_pendentes` da F1.4. Ela seleciona
reservas `hospedado` com `checkin_em` preenchido e **sem** trabalho `enviar_boas_vindas`,
descarta as que estão fora da janela de validade do hotel (§11) e, para cada hotel restante, lê
os três slots e agenda se estiverem válidos.

**Rationale:** a passagem é idempotente (o índice único garante), roda independentemente de
como os slots foram preenchidos (rota, semeadura ou SQL direto) e mantém o `PUT` rápido. A
janela precisa ser reavaliada a cada passagem — é uma comparação com o instante atual, não um
efeito colateral de uma gravação.

**Alternativa recusada:** enfileirar dentro do `PUT` dos slots — colocaria uma varredura de
reservas dentro de uma requisição de configuração, não cobriria slot preenchido por outro
caminho, e faria o significado de "completar a configuração" incluir "disparar mensagens", que
é surpresa para quem clicou em salvar.

**Sem APScheduler**, como na F1.4: a cadência é externa (execução do comando), e o atraso de um
ciclo não gera segundo pacote nem mensagem perdida — só adia.

## 11. A janela de validade conta do `checkin_em`, não do calendário

**Decisão:** a recuperação automática alcança a reserva `hospedado` cujo
`checkin_em >= agora - horas_validade_boas_vindas`, com o prazo lido de `parametro_hotel`
(padrão `12`). Reserva com check-in anterior à janela, ou sem `checkin_em`, mantém a
sinalização na fila e **não** recebe envio.

**Rationale:** o limite de validade existe porque recado de chegada tardio é pior do que
nenhum, e porque completar a configuração depois de dias de uso dispararia rajada de template
pago para quem já fez checkout. Mas medir isso por data de calendário abre um furo silencioso:
hóspede chega às 23h30 com slot vazio, a recepção preenche às 23h40, a varredura roda às 00h05
— `CURRENT_DATE` já virou, a reserva sai da elegibilidade e o pacote **nunca sai, sem erro
nenhum**. É exatamente a falha invisível que esta fatia existe para eliminar. Contado do
instante do check-in, o mesmo caso tem 35 minutos de distância e continua elegível.

**Ganho colateral:** o critério antigo também excluía a chegada antecipada. A spec permite
confirmar chegada antes da data prevista, e nesse caso `data_checkin_prevista <> CURRENT_DATE`
— a reserva jamais receberia a recuperação. O eixo novo cobre os dois casos com uma regra.

**Por que o prazo vem de `parametro_hotel`:** Artigo XIII — prazo, intervalo e periodicidade
não são constante de código. `horas_ate_reenvio` e `horas_corte_antes_checkin`, prazos da mesma
natureza, já vivem lá desde a F1.4, e a varredura já sabe lê-los com cache por hotel. Chave
`horas_validade_boas_vindas`, semeada em `12`. Propriedade sem o valor não recebe prazo suposto:
a varredura registra `prazo_ausente` e segue, no comportamento já existente de
`_prazos_do_hotel`.

**Onde o filtro é aplicado:** a consulta em `hospedagem/repository.py` lista `hospedado` com
`checkin_em IS NOT NULL` e sem trabalho de boas-vindas; a janela é comparada em Python, por
hotel, com o prazo daquele hotel. Isso repete o desenho de `verificar_cadastros_pendentes` —
prazo por propriedade não cabe num literal no `WHERE`.

**Alternativas recusadas:** `INTERVAL '12 hours'` no SQL — resolve o furo do calendário, mas
crava o prazo no código e impede que uma propriedade com operação diferente o ajuste;
`data_checkin_prevista >= CURRENT_DATE - 1` — amplia a janela sem corrigir o eixo, e ainda
manda recado de 30 horas atrás; janela relativa ao instante em que os slots foram preenchidos
— dependeria de rastrear a gravação da configuração, e não é a chegada do hóspede que ela
mediria.

**Consequência aceita:** não há rota de envio manual para a reserva fora da janela. A
sinalização permanece visível; a decisão é humana e fica sem automação — registrado na seção
de honestidade do plano. Para chegada antecipada, a sinalização só aparece quando a data
prevista alcança o dia corrente, porque é a cláusula da visão.

## 12. Sinalização na fila: coluna derivada nova na visão

**Decisão:** `vw_fila_do_dia` ganha `boas_vindas_nao_enviadas`:

```sql
(r.status = 'hospedado'
 AND NOT EXISTS (
       SELECT 1 FROM trabalho t
        WHERE t.tipo = 'enviar_boas_vindas'
          AND (t.payload->>'id_reserva')::bigint = r.id_reserva
     )) AS boas_vindas_nao_enviadas
```

**Rationale:** FR-030 exige indicação **distinta** de `chegada_nao_confirmada`. As duas são
mutuamente exclusivas por construção: uma exige `status <> 'hospedado'`, a outra exige
`status = 'hospedado'`. O `NOT EXISTS` usa o índice único parcial criado na mesma revisão.

**Alternativas recusadas:** coluna booleana na `reserva` — estado derivável não se
materializa, e ficaria a manter em sincronia; reusar `status_envio_coleta` — é a mensagem de
coleta, outro assunto, e sobrecarregar o campo apagaria a distinção que a recepção precisa ver.

## 13. Onde vive cada pedaço

| Trabalho | Módulo | Por quê |
| --- | --- | --- |
| Transição e `checkin_em` | `hospedagem` | Governa `reserva` |
| Texto e registro da mensagem | `conversa` | Governa `mensagem` |
| Leitura/gravação dos slots | `propriedade` | Governa `parametro_hotel` |
| Enfileiramento | `app/fila` | Já é o dono da tabela `trabalho` |
| Recuperação periódica | `worker/agendador.py` | Já é o dono da varredura |

`hospedagem.confirmar_chegada` chama `conversa_service.agendar_boas_vindas` por parâmetro
injetável, exatamente como `criar_reserva` chama `agendar_coleta_apos_reserva`. A direção
`hospedagem → conversa` já existe; **nenhum import novo em sentido contrário**, nenhum ciclo.

## 14. Porta de mensageria: método próprio com quatro variáveis

**Decisão:** `MensageriaGateway.enviar_boas_vindas(*, telefone_destino, variaveis, corpo,
id_mensagem, id_reserva)`, onde `variaveis` é a tupla ordenada `(prenome, cafe, wifi,
checkout)`. Implementado em `MensageriaFalsa` e no adaptador WhatsApp (template
`boas_vindas`, quatro parâmetros de corpo).

**Rationale:** o template tem quatro variáveis com rótulo fixo; os outros dois métodos têm
uma. Forçar a assinatura de uma variável obrigaria o adaptador a fatiar o texto montado para
recuperar os valores — frágil e sem motivo.

**Alternativa recusada:** guardar os três textos no `payload` do trabalho — criaria segunda
fonte de verdade para um dado que já está em `parametro_hotel`.

**Risco conhecido e aceito:** o `mensagem.conteudo` é montado na confirmação; as `variaveis`
são lidas no envio. Se a recepção editar um slot entre o clique e o envio (janela de segundos
a minutos), o histórico guarda o valor antigo e o hóspede recebe o novo. O hóspede sempre
recebe informação vigente, que é o que importa; duplicar o texto na fila para fechar essa
janela custaria mais do que o defeito.

## 15. Semeadura dos três slots

**Decisão:** `PARAMETROS_BOAS_VINDAS_PADRAO` no bootstrap **e** semeadura idempotente na
revisão `0008` para hotéis já existentes — o mesmo par que a `0007` fez com os prazos.

Valores de semente são placeholders válidos para o canal, em uma linha, para o hotel
substituir pelo texto real:

| Chave | Semente |
| --- | --- |
| `boas_vindas_cafe` | `Cafe da manha das 7h as 10h` |
| `boas_vindas_wifi` | `Wi-Fi: rede do hotel, senha na recepcao` |
| `boas_vindas_checkout` | `Checkout ate as 12h` |
| `horas_validade_boas_vindas` | `12` |

A quarta chave não é slot de texto e não passa pela validação do canal: é prazo, validado como
inteiro positivo, no mesmo formato de `horas_ate_reenvio`. Ela **não** entra na rota de
boas-vindas — é parâmetro de comportamento, e a permissão da recepção não a alcança (§2).

**Rationale:** FR-029 — a primeira confirmação não pode depender de alguém ter lembrado de
cadastrar. Sem acento nos valores semeados, no mesmo padrão do restante do código do projeto.

## 16. Log

`chegada_confirmada`, `boas_vindas_agendadas`, `boas_vindas_bloqueadas` (com `chave` do slot
faltante), `boas_vindas_ja_agendadas`, `boas_vindas_recuperadas`. Todos com
`id_reserva`/`id_hotel` e nunca com conteúdo de mensagem nem valor de slot — nome de chave é
identificador de configuração, não texto ao hóspede.

## 17. Divergências de documentação — já corrigidas antes deste plano

O backlog, o mapa de processos, a jornada e o fluxo de dados descreviam o pacote de chegada
como o próprio catálogo. Isso não é enviável por template. Os quatro artefatos foram
corrigidos com nota datada, e `docs/00-ESTADO-DO-PROJETO.md` registrou o limite técnico da
variável de template como restrição geral das quatro mensagens proativas. **Nada foi
contornado em silêncio.**

Consequência para esta fatia: a dependência de F2.1 passou a ser de **sequência**, não
funcional — o envio não lê `catalogo_item`.
