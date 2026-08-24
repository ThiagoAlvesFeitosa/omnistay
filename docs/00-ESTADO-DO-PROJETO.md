# OmniStay — Estado do Projeto

**Atualizado em:** 24/08/2026
**Para que serve:** ponto de retomada. Leia este arquivo antes de continuar o trabalho.

---

## Onde paramos

**Documentação concluída** — seis artefatos. **Implementação em andamento.**

**Progresso:** 23 de 24 fatias concluídas.

| Fatia | Estado |
| --- | --- |
| F0.1 Esqueleto caminhante | ✅ Concluída — `GET /health`, 6 testes verdes, commitada |
| F0.2 Esquema e migrações | ✅ Concluída — revisão `0001` com SQL congelado, teste de inventário nos dois sentidos, commit `c42a6ed` |
| F0.3 Autenticação e perfis | ✅ Concluída — bootstrap, sessão opaca em cookie, matriz de perfis, revisão `0002_sessao` |
| F1.1 Cadastrar reserva | ✅ Concluída — módulo `hospedagem`, titular provisório, fila + contagem, revisão `0003_fila_do_dia` |
| F1.2 Disparar a coleta de dados | ✅ Concluída — tabela `trabalho`, módulo `conversa`, `MensageriaGateway` + falsa, worker, revisão `0005_trabalho_e_coleta` |
| F1.3 Receber e interpretar a ficha | ✅ Concluída — webhook, `LLMProvider` + falsa, `interpretar_ficha`, `estado_cadastro`, revisão `0006_interpretar_ficha` |
| F1.4 Controlar o silêncio | ✅ Concluída — lembrete único, `sem_cadastro_previo`, prazos em `parametro_hotel`, `worker/agendador.py`, revisão `0007_controlar_silencio` |
| F2.1 Catálogo da propriedade | ✅ Concluída — CRUD em `propriedade`, `GET /catalogo/ativo`, porta `CatalogoRepository`, `ler_catalogo` na matriz; sem migração (tabela `0001`) |
| F2.2 Confirmar chegada e dar boas-vindas | ✅ Concluída — clique `POST /reservas/{id}/chegada`, recado curto, slots em `parametro_hotel`, recuperação pela janela de `checkin_em`, revisão `0008_confirmar_chegada` |
| F3.1 Receber mensagem com segurança | ✅ Concluída — `POST /webhook` reutilizado, HMAC falha-fechada, `classificar_mensagem` pendente sem consumo, revisão `0009_receber_mensagem` |
| F3.2 Classificar a intenção | ✅ Concluída — worker consome `classificar_mensagem`, taxonomia validada no domínio, `precisa_atendimento_humano` na fila, revisão `0010_classificar_intencao` |
| F3.3 Responder dúvida a partir do catálogo | ✅ Concluída — worker consome `responder_duvida`, resposta fiel ao catálogo ativo do hotel, aviso + `duvida_nao_coberta` na fila, revisão `0011_responder_duvida_catalogo` |
| F3.4 Registrar pedido de serviço | ✅ Concluída — worker consome `registrar_pedido_servico`, confirmação antes da `solicitacao` tipo `servico` (sem `consumo`), `GET /solicitacoes` sem ficha, revisão `0012_registrar_pedido_servico` |
| F3.5 Abrir chamado de reclamação | ✅ Concluída — worker consome `abrir_chamado_reclamacao`, confirmação antes da `solicitacao` tipo `reclamacao` (sem `consumo`), janela + destaque no `GET /solicitacoes`, revisão `0013_abrir_chamado_reclamacao` |
| F3.6 Resolver chamado e confirmar | ✅ Concluída — `POST /solicitacoes/{id}/resolucao` grava `resolvida` (autor + instante) e agenda `enviar_confirmacao_resolucao`; worker só envia; revisão `0014_resolver_chamado` |
| F3.7 Consumo faturável e fila de lançamento | ✅ Concluída — fork em `registrar_pedido_servico`, tabela `item_vendavel`, `GET /consumos/pendentes`, POST lançamento/dispensa; resolver consumo não lança; revisão `0015_consumo_faturavel` |
| F3.8 Pulso do segundo dia | ✅ Concluída — varredura em `worker/agendador.py` (sem APScheduler), módulo `feedback` escreve `avaliacao`, um recado por mensagem, neutro = positivo, só reclamação não resolvida suprime, `horas_minimas_para_pulso=24`; revisão `0016_pulso_segundo_dia` |
| F4.1 Confirmar saída e pesquisa | ✅ Concluída — clique `POST /reservas/{id}/saida` reusa `confirmar_fase_da_reserva`, pesquisa curta sem classificar, consentimento append-only, visão mantém encerrada só com leitura humana, `horas_atribuicao_pesquisa_saida=24`; revisão `0017_confirmar_saida` |
| F4.2 Lista de pedidos feitos pelo chat | ✅ Concluída — o mesmo clique de saída agenda pesquisa **e** lista (mensagem distinta); recorte cobrável (`pendente`+`lancado`); GET ao vivo `pedidos-feitos-pelo-chat`; snapshot na mensagem; operação `ler_pedidos_feitos_pelo_chat`; revisão `0018_lista_pedidos_chat`. Sem React, sem extrato/conta |
| F5.1 Cadastro de concorrentes | ✅ Concluída — módulo `mercado`, gestão cria/edita/desativa (não apaga); `GET /concorrentes/ativos` omite inativo; UNIQUE da fonte por hotel inclusive inativo; CHECK de URL; recepção e staff `403`; revisão `0019_cadastrar_concorrentes`. Sem visita à fonte, sem React, sem `coleta_mercado` |
| F5.2 Coleta agendada de mercado | ✅ Concluída — `verificar_coletas_mercado` no `worker/agendador.py` (sem APScheduler, sem rota HTTP); tipo `coletar_mercado` com unicidade só do trabalho aberto; porta `FontePublica` + `FonteFalsa` / `FonteHttp` (stdlib, JSON-LD, User-Agent `OmniStay-Coletor/1.0`); diretiva ausente **não** autoriza visita; falha grava `sucesso=false`; `periodicidade_coleta_mercado=24` horas; revisão `0020_coleta_agendada`. Sem painel (F5.3), sem disparo manual, sem mensagem ao hóspede |
| F5.3 Painel de mercado | ✅ Concluída — `GET /mercado` (visão atual) e `GET /mercado/concorrentes/{id}` (histórico); operação `ler_mercado` só gestão; visão atual = último **sucesso** datado; `situacao` (`atual` · `desatualizado` · `cadencia_ausente` · `sem_coleta` · `so_falha`); limiar = periodicidade da casa; escrita da série `405`; sem migração, sem React, sem disparo de coleta |
| F6.1 Expurgo por retenção | ✅ Concluída — `verificar_retencao` no `worker/agendador.py` (sem APScheduler, sem tipo na fila, sem botão “expurgar agora”); conteúdo livre vira marca 12 meses após `checkout_em`; ficha apagada 5 anos após a última saída vinculada; comprovante `execucao_retencao` (1/hotel/dia UTC); `GET /retencao` com `ler_retencao` só gestão; revisão `0021_expurgo_retencao`. Payload órfão fora; sem React; sem pedido avulso de esquecimento |
| Demais 1 fatia | Pendente, na ordem de `docs/backlog.md` — próxima: **F6.2** (simulador da apresentação). Não há F2.3 nem F3.9 no backlog |

**Ambiente montado:** repositório em `omnistay/`, Cursor com Spec Kit inicializado
(`--integration cursor-agent`, scripts PowerShell), constituição carregada em
`.specify/memory/`, regras em `.cursor/rules/`, documentação copiada para `docs/`.

**Método:** spec-driven development com GitHub Spec Kit no Cursor, TDD obrigatório. Ciclo por
fatia: `/speckit.specify` → `/clarify` → `/plan` → `/tasks` → `/implement` → `pytest` →
commit.

> **Regra de higiene de contexto:** uma fatia, uma conversa. Ao commitar, abrir conversa nova.
> O estado mora nos arquivos — spec, plano, tarefas, código e este documento —, nunca no
> histórico da conversa.

**Para a próxima entrega**, além da implementação: a implantação em nuvem, que o ADR-008
deixou deliberadamente adiada para ser decidida contra um sistema funcionando.

## Decisões tomadas durante a implementação

Registradas aqui porque não constam dos seis artefatos originais.

| Tema | Decisão | Origem |
| --- | --- | --- |
| Versão do Python | **3.14** na máquina, com `requires-python = ">=3.11"`. Risco conhecido: bibliotecas podem não ter wheel. Se travar, `uv python install 3.12` e recriar a venv | F0.1 |
| Endpoint de saúde | Falha do banco responde **HTTP 503** com corpo distinguindo aplicação e banco. Não são dois endpoints separados — sem orquestrador, seria complexidade sem problema (Artigo XI) | F0.1 |
| Prazo de resposta na falha | **3 segundos**, não 2. O cliente PostgreSQL eleva qualquer `connect_timeout` menor que 2 para 2 | F0.1 |
| Container do banco | Reutilizado o `omnistay-db` existente, com usuário `postgres`. Verificação da subida limpa (`docker compose down -v` + `up`) virou tarefa da F0.2 | F0.1 |
| Credenciais em arquivo versionado | `testes/conftest.py` trazia URL com senha embutida, herdada da F0.1. Removida na F0.2: sem valor padrão, a suíte exige `DATABASE_URL` do ambiente e falha alto se ausente. `.env.example` registra as chaves **sem valor** | F0.2 |
| Fonte do esquema | ~~A migração executa o próprio `docs/04-schema.sql`~~ **Superada no planejamento da F0.2.** Migração precisa ser imutável: uma revisão que lê um arquivo mutável muda de significado a cada edição e deixa de ser reprodutível. A revisão inicial carrega **cópia congelada** em `alembic/versions/sql/`; `docs/04-schema.sql` segue como documento vivo; a equivalência é garantida por teste, não por disciplina | F0.2 |
| Verificação do esquema | Teste que compara o inventário do banco migrado com as estruturas do documento, **nos dois sentidos** — para detectar migração futura que altere o banco sem atualizar o arquivo | F0.2 |
| Sessão do painel | Token opaco em cookie `HttpOnly`/`Secure`/`SameSite=Strict`; banco guarda só SHA-256. JWT rejeitado porque não é revogável na requisição seguinte | F0.3 |
| Derivação de senha | PBKDF2-HMAC-SHA256 com **600.000 iterações** (recomendação OWASP), da biblioteca padrão. Sem bcrypt/Argon2id: são pacotes compilados e o risco de wheel ausente no Python 3.14 está registrado desde a F0.1. Formato autodescritivo (algoritmo + iterações + sal no valor gravado), então elevar o custo ou trocar de algoritmo **não invalida senhas existentes**. Revisitar antes de produção com hóspede real, ou quando `argon2-cffi` tiver wheel para 3.14 | F0.3 |
| Ataque de tempo no login | E-mail inexistente também paga a derivação, contra hash de referência — resposta com duração igual nos dois casos | F0.3 |
| Ciclo entre módulos | Apareceu ciclo `acesso.service` ↔ `propriedade.service`. **Regra: ciclo se resolve movendo código, nunca com import local.** Orquestração entre módulos pertence a `app/bootstrap.py`, não a um dos módulos. O valor do monolito modular está em as fronteiras serem reais — primeiro ciclo na 3ª fatia de 24 é aviso, não acidente | F0.3 |
| Administração de acesso | Gestão cria/desativa usuários; recepção revoga sessões. Autoridade ≠ urgência | F0.3 |
| Bootstrap | Comando `python -m app.bootstrap` cria hotel, gestor e parâmetros de duração. Sem senha padrão | F0.3 |
| Módulo `acesso` | Acrescentado aos módulos do monólito; governa `usuario` e `sessao`. Camada ORM `model` permanece vazia | F0.3 |
| Tela React na F1.1 | **Não.** A previsão da F0.3 de que a tela de login viria “junto da primeira tela com conteúdo na F1.1” escorregou: F1.1 entregou API autenticada (`POST /reservas`, `GET /fila-do-dia`, `GET /indicadores/chegadas-do-dia`) sem painel. A primeira tela fica para fatia de UI ou início da F1.2 | F1.1 |
| Titular provisório | Nome digitado na criação vira `hospede` mínimo + `reserva_hospede` titular (`ficha_completa = false`) na mesma transação. Sem coluna `nome` em `reserva` | F1.1 |
| Telefone repetido | Sempre cria hóspede novo. Casal/telefone de empresa não podem misturar fichas. Consolidação por pessoa, se existir, é passo futuro explícito | F1.1 |
| Fila vs contagem | Lista nominada (`ler_fila_do_dia`) só recepção; contagem do dia (`ler_indicadores`) só o número, para recepção e gestão — dado cadastral não trafega para a gestão filtrar no frontend | F1.1 |
| Visão `vw_fila_do_dia` | Revisão `0003`: `DROP` + `CREATE` com `telefone_contato` e `data_checkout_prevista`. Revisão `0004`: `data_checkin_prevista <= CURRENT_DATE` — reserva futura sai da fila do turno; contagem de chegadas segue com igualdade ao dia corrente | F1.1 |
| Telefone canônico | Dígitos com prefixo `55`; máscara aceita na entrada. Função pura em `app/comum/telefone.py` | F1.1 |
| Fila `trabalho` | Tabela no PostgreSQL (Artefato 5); lacuna do `04-schema.sql` fechada na `0005`. Unicidade parcial de `enviar_coleta` por reserva | F1.2 |
| Independência estrutural | `POST /reservas` grava mensagem pendente + trabalho na mesma TX; worker envia depois via porta | F1.2 |
| `MensageriaGateway` | Protocolo + `MensageriaFalsa` na suíte; adaptador WhatsApp Cloud existe mas nenhum teste o instancia | F1.2 |
| Módulo `conversa` | Nasce mínimo: texto da coleta, `mensagem`, espelho de `status_envio`. `hospedagem` só agenda | F1.2 |
| Contato LGPD | `parametro_hotel.contato_responsavel_dados` (default = telefone do hotel no bootstrap) | F1.2 |
| Status na fila | `vw_fila_do_dia.status_envio_coleta`; webhook `entregue` fora de escopo | F1.2 |
| Webhook + interpretação | `POST/GET /webhook` grava evento+mensagem+`interpretar_ficha`; LLM só no worker | F1.3 |
| `LLMProvider` | Protocolo + `LLMFalso`; domínio sem adaptador concreto | F1.3 |
| Orquestração | Worker chama `conversa` (extrai) e `hospedagem` (consolida) — sem ciclo de import | F1.3 |
| `estado_cadastro` | `aguardando` · `completa` · `parcial` · `leitura_humana` na fila do dia | F1.3 |
| Irreconhecível | Permanece `aguardando_cadastro`; sinal via `classificacao_bruta` | F1.3 |
| Agendador de silêncio | Função `verificar_cadastros_pendentes` em `worker/agendador.py`; **sem** APScheduler (Artigo XI). `--verificar-cadastros`; `--uma-passagem` não dispara | F1.4 |
| Lembrete único | Trabalho `enviar_lembrete` + `reenvio_realizado` + índice único por reserva | F1.4 |
| t0 do silêncio | `mensagem.enviada_em` atualizado no sucesso do envio | F1.4 |
| Prazos de silêncio | Bootstrap e `0007` semeiam `horas_ate_reenvio=24` e `horas_corte_antes_checkin=12`; ausência não usa default no verificador | F1.4 |
| Catálogo | Fatos em texto por categoria; desativar não apaga; consulta ativa agrupa as cinco chaves | F2.1 |
| Porta `CatalogoRepository` | `listar_ativos` na mesma transação; HTTP de manutenção não passa pela porta | F2.1 |
| `ler_catalogo` | Recepção e gestão leem; só recepção altera; operação recusada | F2.1 |
| Preço estruturado | **Entregue na F3.7.** `item_vendavel` com `preco_atual`; a identificação devolve id, o domínio lê o preço no banco. F2.1 não criou a tabela | F3.7 |
| Recado de boas-vindas | **Mensagem curta, não o catálogo.** Variável de template recusa quebra de linha, tabulação e mais de 4 espaços seguidos: catálogo inteiro numa variável não é enviável. O recado confirma a chegada, leva três informações de entrada e convida a perguntar; o catálogo responde sob demanda na janela de 24h (F3.3) | F2.2 (spec) |
| Informações de entrada | Três chaves em `parametro_hotel` — `boas_vindas_cafe`, `boas_vindas_wifi`, `boas_vindas_checkout`. Obrigatórias, semeadas no bootstrap, validadas **na gravação** (vazio, quebra de linha, tabulação, >4 espaços). Validar só no envio faria a falha coincidir com a chegada | F2.2 (spec) |
| Slot vazio na confirmação | Check-in ocorre, recado **não** sai, reserva sinalizada na fila do dia. Nunca variável em branco | F2.2 (spec) |
| Recuperação do recado | Completar os slots envia para reserva `hospedado` cujo **`checkin_em` está dentro da janela de validade** da propriedade. Reserva com chegada anterior à janela mantém a sinalização e não recebe envio automático — boas-vindas tem validade curta, e sem o limite completar a configuração dispararia rajada de template pago, inclusive para quem já saiu | F2.2 (spec) |
| Eixo da janela de validade | **Instante do check-in, nunca data de calendário.** A clarificação dizia `data_checkin_prevista = CURRENT_DATE`; isso perdia em silêncio a chegada das 23h30 com slots preenchidos às 23h40 e varredura às 00h05 — o dia virava, a reserva saía da elegibilidade e o pacote nunca saía, sem erro nenhum. Corrigido no planejamento. Fecha também a chegada antecipada, que o critério por data excluía | F2.2 (correção no plano) |
| Duração da janela | Chave `horas_validade_boas_vindas` em `parametro_hotel`, semeada em `12`. Artigo XIII: prazo não é constante de código, e `horas_ate_reenvio` e `horas_corte_antes_checkin` já estabeleceram o padrão na F1.4. É parâmetro de comportamento — fora da permissão da recepção e fora da rota de boas-vindas. Sem valor configurado, a propriedade não recebe recuperação e o log registra `prazo_ausente`; nenhum prazo é suposto | F2.2 (plano) |
| Unicidade do recado | Restrição `UNIQUE` por reserva, no padrão da idempotência de webhook. Conferência em código não basta: duas execuções simultâneas do worker enviariam duas vezes | F2.2 (spec) |
| Permissão de configuração | Operação por **grupo de chaves** (`alterar_texto_de_boas_vindas`, só recepção), nunca `alterar_parametro_hotel` genérico. A tabela guarda texto operacional de balcão (recepção) e parâmetro de comportamento (gestão, fatia futura); permissão pela tabela daria à recepção o poder de mudar como o sistema se comporta com o hóspede | F2.2 (spec) |
| Autorização do clique de chegada | Sem operação nova: `confirmar_fase_da_reserva` está na matriz desde a F0.3 e nunca teve consumidor. A F2.2 é a primeira a usá-la | F2.2 (plano) |
| Chegada em `aguardando_cadastro` | Recusada com `409`, porque a trigger só admite `hospedado` a partir de ficha recebida, ficha parcial ou sem cadastro prévio. Atalho para o balcão exigiria spec própria | F2.2 (plano) |
| Recuperação do recado, na prática | Varredura na `worker/agendador.py` da F1.4 (`--verificar-boas-vindas`), não efeito colateral da gravação dos slots — a janela precisa ser reavaliada a cada passagem, e o slot pode ser preenchido por outro caminho. O SQL lista `hospedado` com `checkin_em` e sem trabalho; a janela é comparada em Python, por hotel, porque o prazo é por propriedade | F2.2 (plano) |
| Sinalização de recado não enviado | Coluna derivada `boas_vindas_nao_enviadas` na `vw_fila_do_dia` (hospedado sem trabalho de boas-vindas). Mutuamente exclusiva de `chegada_nao_confirmada`, que exige status diferente de hospedado | F2.2 (plano) |
| Webhook falha-fechada | `WHATSAPP_APP_SECRET` vazio ou ausente recusa o `POST /webhook` com `401` **antes** de qualquer INSERT. A F1.3 pulava a verificação quando o segredo faltava; esse furo fecha aqui | F3.1 |
| Tipo `classificar_mensagem` | Trabalho durável da estadia; o worker desta fatia **não** o consome (`reclamar_proximo` em allowlist). Consumir agora marcaria `tipo_desconhecido` e destruiria o gancho da F3.2 | F3.1 |
| Unicidade da classificação | Índice único parcial por `id_mensagem` no payload, no padrão de `enviar_coleta`. Reenvio do mesmo `id_externo` já para em `evento_webhook` | F3.1 |
| Mesmo telefone, dois estados | `aguardando_cadastro` vence `hospedado` no webhook — a ficha da F1.3 não muda. Mensagem não infere check-in (Artigo I) | F3.1 |
| Consumo de `classificar_mensagem` | Allowlist e ramo no worker no mesmo passo. Os testes da F3.1 que proibiam o claim foram invertidos — isso é a fatia, não regressão | F3.2 |
| Escala na primeira falha | `FalhaDeClassificacao` e formato inválido marcam o trabalho `concluido` e encaminham a humano. Não se copia o backoff de `interpretar_ficha` | F3.2 |
| Sinal na fila do dia | Coluna derivada `precisa_atendimento_humano` (hospedado com desfecho `encaminhado_humano` / `formato_invalido` / `indisponivel`). Não se reusa `estado_cadastro = leitura_humana` | F3.2 |
| Ramo automático não executa | Dúvida, pedido e reclamação só gravam eixos (`desfecho = classificado`). Upsell, checkout e fora de escopo já vão a humano. Zero `solicitacao`, zero envio, zero catálogo | F3.2 |
| Consumo de `responder_duvida` | Allowlist, enqueue na classificação de `duvida_geral` e ramo no worker no mesmo passo. Classificar não lê catálogo nem envia | F3.3 |
| Chamado desta fatia | Desfecho `duvida_nao_coberta` na fila do dia (`precisa_atendimento_humano`). Zero `solicitacao` — chamado operacional é F3.5 | F3.3 |
| Fidelidade ao catálogo | Trechos citados têm de ser substring do catálogo ativo **e** do texto enviado. Mentira estruturada vira o mesmo aviso da não coberta | F3.3 |
| Catálogo vazio ou IA caída | Não chama (ou não retenta) o LLM; aviso + chamado; trabalho `concluido`. Falha de envio reagenda mensageria, não a redação | F3.3 |
| Consumo de `registrar_pedido_servico` | Allowlist, enqueue na classificação de `pedido_de_servico` e ramo no worker no mesmo passo. Classificar não confirma nem insere `solicitacao` | F3.4 |
| Pedido desta fatia | `solicitacao` tipo `servico`, sem `consumo`. Confirmação padrão **antes** de abrir a tarefa. Quarto só do texto do hóspede; ausência não bloqueia | F3.4 |
| Fila operacional | `GET /solicitacoes` com `ler_solicitacao_atribuida` (recepção, staff, gestão). Mesmo JSON, sem nome/telefone/documento. Staff continua recusado na ficha e na fila do dia | F3.4 |
| Flag humano no pedido | `precisa_atendimento_humano` permanece falso. Toalha não é chamado da recepção; a equipe lê `GET /solicitacoes` | F3.4 |
| Consumo de `abrir_chamado_reclamacao` | Allowlist, enqueue na classificação de `reclamacao_tecnica` e ramo no worker no mesmo passo. Classificar não confirma nem insere `solicitacao` | F3.5 |
| Chamado desta fatia | `solicitacao` tipo `reclamacao`, sem `consumo`. Toda reclamação técnica classificada abre chamado, qualquer sentimento. Confirmação padrão **antes** de tramitar; pergunta de horário só se a janela for nula | F3.5 |
| Follow-up de horário | Atalho **antes do LLM** em `classificar_mensagem` se houver reclamação aberta sem janela e o texto `parece_resposta_de_horario`. Sem tipo extra, sem segundo recado | F3.5 |
| Destaque por tempo | `parametro_hotel.horas_destaque_chamado_aberto` semeado `"2"`. Só `tipo=reclamacao`. Sem default no código se a chave faltar; log `prazo_ausente` | F3.5 |
| Flag humano na reclamação | `precisa_atendimento_humano` permanece falso. Alert Center continua sendo `GET /solicitacoes` | F3.5 |
| Resolução no clique | `POST /solicitacoes/{id}/resolucao` (`resolver_solicitacao`: recepção e staff; gestão `403`). UPDATE `resolvida` + autor + instante **antes** do recado. Segundo clique `409`. Outro hotel `404` uniforme | F3.6 |
| Recado de conclusão | Trabalho `enviar_confirmacao_resolucao` (unicidade por `id_solicitacao`). Worker só chama `enviar_texto_sessao`. Falha de envio **não** reabre. Sem template Utility | F3.6 |
| Janela de 24h | O recado de resolução usa sessão, não Utility. Se a janela estiver fechada, o envio falha e é retomado; o chamado permanece resolvido. Limitação honesta desta fatia | F3.6 |
| Fork no mesmo trabalho | Não nasce tipo novo na fila. `registrar_pedido_servico` identifica item ativo; `unico` abre `consumo` pendente; `nenhum` ou lista vazia permanece F3.4 | F3.7 |
| Preço fora do prompt | Porta recebe `(id, nome)`; `valor_praticado = preco_atual * quantidade` lido no banco na mesma TX da confirmação | F3.7 |
| Fila de lançamento | `GET /consumos/pendentes` (`ler_solicitacao_atribuida`). Inclui consumo já resolvido no quarto. Toalha não entra | F3.7 |
| Clique financeiro | `POST .../lancamento` e `.../dispensa` (`lancar_consumo`, só recepção). Sem recado ao hóspede. Resolver o quarto não altera `status_lancamento` | F3.7 |
| Agendador de pulso | Sem APScheduler. `verificar_pulsos_pendentes` no `worker/agendador.py`; `--verificar-pulsos`; o loop horário chama depois de cadastros e boas-vindas. `--uma-passagem` não varre | F3.8 |
| Módulo `feedback` | Primeiro escritor de `avaliacao` (`origem=pulso_segundo_dia`, nota nula). Sem HTTP. Sem import de `conversa` | F3.8 |
| Um recado por mensagem | Dúvida, pedido ou reclamação na janela do pulso correm F3.3–F3.5; o pulso fecha em silêncio. Neutro usa o mesmo reconhecimento do positivo, sem afirmar satisfação | F3.8 |
| Só reclamação suprime | Serviço, consumo e `precisa_atendimento_humano` não bloqueiam o pulso. `horas_minimas_para_pulso=24` no bootstrap e na `0016`; ausência loga `prazo_ausente` | F3.8 |
| Clique de saída | Reusa `confirmar_fase_da_reserva` (só recepção). `hospedado` → `encerrado` com `checkout_em = now()`. Chamado aberto e consumo pendente não bloqueiam. Segundo clique `409` | F4.1 |
| Pesquisa sem classificar | Trabalho `interpretar_pesquisa_saida` (unicidade por mensagem). Encerrada não gera `classificar_mensagem`. Sem recado de agradecimento, sem lista de pedidos | F4.1 |
| Consentimento append-only | Primeiro escritor: worker `origem=pesquisa_checkout`. Painel só `painel` / `solicitacao_titular`. Silêncio e nota alta não consentem. GET vigente em `em` | F4.1 |
| Visão após checkout | Encerrada limpa continua fora (F1.1). Encerrada com `pesquisa_saida_leitura_humana` permanece. `saida_nao_confirmada` = hospedado com checkout previsto anterior a hoje | F4.1 |
| Prazo da resposta | `horas_atribuicao_pesquisa_saida=24` no bootstrap e na `0017`, eixo `checkout_em`. Ausência loga `prazo_ausente` e sinaliza humano; não inventa 24. Janela vencida conclui sem humano | F4.1 |
| Mesmo clique da saída | Não há segundo botão. `confirmar_saida` agenda a pesquisa e, se houver cobrável, a lista. Recorte vazio → `lista=ausente`, zero trabalho extra | F4.2 |
| Recorte cobrável | `consumo` com `status_lancamento` em `pendente` ou `lancado`. Serviço operacional e dispensado ficam de fora. Status de lançamento não vaza no recado nem no GET | F4.2 |
| Snapshot vs consulta | O corpo da mensagem é gravado no enfileiramento. `GET /reservas/{id}/pedidos-feitos-pelo-chat` é consulta ao vivo (recepção e gestão; staff `403`; outro hotel `404` uniforme) | F4.2 |
| Valor histórico | A lista lê `consumo.valor_praticado`, nunca `item_vendavel.preco_atual`. Reajuste depois do pedido não altera o recado nem o GET | F4.2 |
| Nomenclatura | Rótulo **pedidos feitos pelo chat**. Sem “extrato”, sem “conta”, sem “está correto?”, sem convite a pagar. Sem tela React nesta fatia | F4.2 |
| Gestão cadastra concorrentes | Escrever a lista **não** contradiz “somente leitura” do painel de preços (F5.3). A FR-019 da F0.3 recusa gestão em reserva/hóspede/solicitação/consumo/avaliação — não em concorrente. Recepção e staff não leem nem alteram | F5.1 |
| Fonte única por hotel | `uq_concorrente_hotel_fonte` em `(id_hotel, lower(btrim(url_fonte)))` é completa, não parcial: inativo continua a ocupar o endereço. Desativar não apaga. `GET /concorrentes/ativos` é o contrato da F5.2 | F5.1 |
| Sem visita nesta fatia | Cadastro não abre a URL, não grava `coleta_mercado` e não examina termos de uso. Quem cadastra escolhe fonte pública | F5.1 |
| Quarta porta | `FontePublica` entra ao lado de LLM, catálogo e mensageria. O Artigo X da constituição listava três na ratificação; o princípio (domínio depende de I/O, não de cliente HTTP) é o mesmo | F5.2 |
| Diretiva ausente | Arquivo de acesso publicado ausente ou vazio **não** autoriza visita — diverge do default clássico de robots.txt. Recusa e ausência gravam falha datada | F5.2 |
| Sem APScheduler | Varredura em `verificar_coletas_mercado`, flag `--verificar-mercado`, laço horário do worker. O Artigo XI segue; o Artefato 5 ainda nomeia a lib | F5.2 |
| Falha ≠ preço zero | `coleta_mercado` só INSERT. `sucesso=false` com preço/nota nulos. Zero é sucesso. Trabalho sempre `concluido` — sem backoff da fila | F5.2 |
| Periodicidade por hotel | `periodicidade_coleta_mercado` em horas, semente 24. Ausência loga `periodicidade_ausente` e omite o hotel. Isolamento pelo `id_hotel` do concorrente | F5.2 |
| Visão atual = último sucesso | `GET /mercado` não usa `ultima_coleta` (qualquer desfecho) como preço. Falha posterior deixa o sucesso com a data antiga e marca `desatualizado` | F5.3 |
| `ler_mercado` | Operação só gestão, distinta de `ler_concorrentes`. Recepção e staff `403`. Escrita da série inexistente (`405`) | F5.3 |
| Limiar de desatualizado | O mesmo `agora >= U + P` da coleta devida. Sem chave nova. Periodicidade inválida → `cadencia_ausente`, não assume 24 | F5.3 |
| Relógio da retenção | Só `checkout_em` (clique de saída). Data prevista e PMS intocados. Sem `checkout_em`, o prazo não anda | F6.1 |
| Anonimizar ≠ apagar | Mensagem, comentário, descrição e payload viram marca; a linha fica (volume). `classificacao_bruta` vira `NULL`. Comentário **e** descrição vazios não ganham marca | F6.1 |
| Ficha aos 5 anos | DELETE de consentimento, vínculo e hóspede; reserva operacional permanece; telefone da reserva vira marca se ficou sem vínculo. Elegível só se **todas** as reservas vinculadas (qualquer hotel) já venceram | F6.1 |
| Sem APScheduler (retenção) | `verificar_retencao` no laço horário; efetividade 1×/hotel/dia UTC via UNIQUE. `--verificar-retencao`; `--uma-passagem` não dispara. Sem tipo na fila `trabalho` | F6.1 |
| Comprovante ≠ auditoria | Tabela `execucao_retencao` (quantidades e flags, sem texto). `GET /retencao` com `ler_retencao` só gestão. Sem botão de disparo (`405` / rota inexistente) | F6.1 |
| Prazos sem default | `meses_retencao_conteudo_livre=12` e `anos_retencao_ficha=5` semeados. Ausência ou inválido: flag no comprovante e log `prazo_conteudo_ausente` / `prazo_ficha_ausente` — não assume 12 nem 5 | F6.1 |
| Divergência do Artefato 5 §9.1 | `solicitacao.descricao` e `classificacao_bruta` entram no prazo de 12 meses (conteúdo livre). Payload de webhook órfão (sem mensagem) fica **fora** desta fatia | F6.1 |

## Onde ficam os arquivos

**Fonte única dos documentos: `omnistay/docs/`**, dentro do repositório. Nada de cópia
fora dali — foi assim que o `04-schema.sql` divergiu antes.

Na raiz da pasta do projeto sobraram apenas os que não são documentação de engenharia:
os `.docx` de entrega, `diagramas/`, `gerar_bmc_v2.py` e `implementacao/`.

| Arquivo em `omnistay/docs/` | Conteúdo |
| --- | --- |
| `01-mapa-de-processos.md` | Artefato 1 v1.1 — cinco processos, catálogo de dez eventos, fluxos de exceção |
| `02-jornada-do-usuario.md` | Artefato 2 v1.1 — personas, trilhas do hóspede e do recepcionista, as-is/to-be, análise crítica |
| `03-fluxo-de-dados.md` | Artefato 3 v1.1 — DFD em três níveis, oito depósitos, catálogo de dez eventos detalhado |
| `04-modelagem-de-dados.md` | Artefato 4 v1.0 — DER, dicionário com classificação LGPD, máquina de estados |
| `04-schema.sql` | DDL PostgreSQL executável — 15 tabelas, 30 restrições, 17 índices, 1 trigger |
| `05-arquitetura.md` | Artefato 5 v1.0 — monolito modular, C4, fila, segurança, oito ADRs |
| `Business_Model_Canvas_OmniStay_v2.0.docx` | Artefato 6 — revisão completa, com preços, margens e MVP x negócio |
| `gerar_bmc_v2.py` | Script que reproduz o Canvas v2.0 a partir do v1.1, herdando os estilos |
| `diagramas/` | Os oito PNGs para o documento de entrega, e os scripts que os reproduzem |
| `implementacao/` | Kit de preparação da programação — ver abaixo |
| `Business_Model_Canvas_OmniStay_v1.1.docx` | Versão anterior, mantida para histórico |

### Dentro de `implementacao/`

| Arquivo | Para onde vai, no repositório de código |
| --- | --- |
| `00-GUIA-DE-SETUP.md` | Fica aqui. É o passo a passo a seguir |
| `constitution.md` | `.specify/memory/constitution.md` — carregado com `/speckit.constitution` |
| `01-backlog-de-fatias.md` | 24 fatias verticais; o texto de cada uma alimenta o `/speckit.specify` |
| `AGENTS.md` | Raiz do repositório |
| `cursor-rules/*.mdc` | `.cursor/rules/` |
| `Entrega_de_Projeto_OmniStay_v2.docx` | Documento acadêmico principal |
| `Business_Model_Canvas_OmniStay_v1.1.docx` | BMC com revisão pontual e registro de alterações |

## Premissa que governa tudo

O OmniStay **não se integra ao PMS**. É sistema paralelo, e o recepcionista é a ponte
humana. As transições entre fases são disparadas por cliques de funcionários no painel,
não por integração. Isso é decisão deliberada e é o argumento comercial do produto.

**O Artefato 2 detalhou o custo dessa premissa:** três transições dependem de um clique
manual e falham em silêncio se ele não acontecer. As mitigações propostas (detecção de
divergência temporal, inferência por comportamento, confirmação em lote) tornam a falha
visível, mas não a eliminam. Isso é assumido no documento.

## Decisões fechadas — não reabrir

| Tema | Decisão |
| --- | --- |
| Integração com PMS | Não haverá |
| Canal | WhatsApp Cloud API oficial, número de teste da Meta no MVP (até 5 destinatários) |
| Backend | Python + FastAPI, stack única |
| Frontend | React + TypeScript, já existente no protótipo |
| Banco | PostgreSQL com `JSONB` para payloads de webhook e saídas de NLP |
| IA | Modelo classe Flash em camada gratuita, atrás de interface `LLMProvider` trocável |
| App da Equipe | Cortado — Alert Center do painel web assume |
| Pedidos feitos pelo chat | Só transações internas ao OmniStay |
| Documento de identidade | **Somente campos digitados, sem foto** |
| Modelagem do documento | `tipo_documento` + `numero_documento`, para RG, CPF e passaporte |
| Coleta de dados | Mensagem única com lista numerada no MVP; Flows na Fase 4 |
| Campo idade | Não persistir — derivar de `data_nascimento` na exibição |
| Ficha parcial | Consolidar como `parcial` e completar no balcão, sem nova rodada de mensagens |
| Pulso do 2º dia | Só dispara com ≥24h de estadia restante; suprimido se houver chamado aberto |
| Confirmação de reclamação | Recebimento confirmado ao hóspede imediatamente, antes da tramitação |
| Cadastro de reserva | Painel pede apenas nome, telefone e datas |
| Acompanhantes | Ficha por WhatsApp só do titular; modelagem prevê 1 reserva : N hóspedes |
| Nomenclatura do extrato | **Nunca "extrato" nem "conta"** — o rótulo é "pedidos feitos pelo chat" |
| Oferta de retorno | **Fora do MVP.** Consentimento coletado na pesquisa de checkout, com data |
| Templates de boas-vindas | Boas-vindas e oferta comercial em templates **separados** |
| Auxílios de transcrição | Copiar ficha e ordem configurável = evolução futura, após testar colagem no PMS |
| Pedidos pelo chat | Duas naturezas: **serviço operacional** (toalha) e **consumo faturável** (bar, lavanderia). Só o faturável aparece no checkout |
| Chamados e pedidos | Tabela única `solicitacao` com `tipo`; consumo faturável em tabela filha especializada |
| Retenção de dados | Ficha cadastral 5 anos após checkout · conversas 12 meses · expurgo automático |
| Multi-tenant | `id_hotel` presente desde o MVP, para não exigir migração ao vender a segunda propriedade |
| Modelagem dimensional | Fora do escopo — volume de ~6 mil estadias/ano é agregável por consulta direta |
| Estilo arquitetural | **Monolito modular** — um desenvolvedor, prazo fixo, sem problema de escala a resolver |
| Processamento assíncrono | Fila em tabela do PostgreSQL, consumida por worker. Sem Redis, sem Celery |
| Busca no catálogo | **Catálogo inteiro no prompt**, atrás de interface trocável. Evita falha por paráfrase |
| Agendamento | `APScheduler` no worker; frequências lidas de `parametro_hotel` |
| Interfaces trocáveis | `LLMProvider` · `CatalogoRepository` · `MensageriaGateway` |
| Hospedagem | **Local com túnel** por enquanto. Demonstração à banca pelo simulador |
| Acesso do staff | Sessão longa por dispositivo, sem senha por chamado |
| Preços (hipótese) | Essencial R$ 249 · Padrão R$ 449 · Avançado R$ 849, com franquia de mensagens |
| Comissão sobre serviços | Reduzida de 20% para 8% da receita — depende de lançamento manual no PMS |
| Dados como ativo | **Não** se apoia no conteúdo das conversas. O ativo é o catálogo da propriedade |

## Catálogo e preços — fechado na F3.7

**Decisão (14/08/2026, cumprida em 19/08/2026):** F2.1 entregou fato afirmável em texto (`catalogo_item`). F3.7 criou `item_vendavel` com preço em campo próprio, revisão `0015`. A IA identifica o item; o sistema lê o preço no banco.

**Problema resolvido.** `catalogo_item.conteudo` em texto livre não serve para cobrar: reajuste exigiria reescrever o bloco, e a IA teria de extrair o número. `consumo.valor_praticado` é retrato, sem FK para o cadastro vigente. A identificação recebe `(id, nome)` sem preço.

## Categorias de mensagem do WhatsApp — referência rápida

Toda mensagem que o sistema **inicia** exige template aprovado, e a categoria define o preço.

| Categoria | O que é | Custo |
| --- | --- | --- |
| **Utility** | Ligada a transação existente: confirmação, status, lembrete | Barata |
| **Authentication** | Código de verificação | Barata |
| **Marketing** | Promoção, oferta, reengajamento de cliente inativo | **A mais cara** |
| **Service** | Resposta dentro da janela de 24h | Grátis até 01/10/2026 |

As quatro mensagens proativas do MVP — coleta de dados, boas-vindas, pulso e pesquisa de
checkout — são todas **Utility**, e é sobre elas que a projeção de custo foi calculada.
Qualquer mensagem nova precisa ser classificada antes de entrar no escopo.

**Limite técnico da variável de template** (descoberto na F2.2, vale para as quatro): o valor
enviado numa variável não pode conter quebra de linha, tabulação nem mais de quatro espaços
seguidos, e não pode ser vazio. Texto longo estruturado — catálogo, lista formatada — não é
enviável por template. Conteúdo assim pertence à janela de 24h, que é texto livre e gratuita.

## Ficha de cadastro do hóspede

Nome completo · Profissão · Data de nascimento · Tipo de documento · Número do documento ·
Endereço · CEP · Cidade · Telefone

## Regra de reenvio na pré-chegada

Um único reenvio com mensagem explicando que o cadastro antecipado é opcional. Persistindo
o silêncio, o sistema para de insistir e sinaliza no painel que a reserva chegará sem
cadastro prévio. **Não ser intrusivo é requisito explícito do projeto.**

Os parâmetros são linhas em `parametro_hotel`, configuráveis por propriedade:
`horas_ate_reenvio`, `horas_corte_antes_checkin`, `horas_validade_boas_vindas`,
`horas_destaque_chamado_aberto`, e os três
slots de entrada (`boas_vindas_cafe`, `boas_vindas_wifi`, `boas_vindas_checkout`). Os
**valores** dos prazos ainda precisam ser definidos com o hotel, mas a estrutura para
armazená-los já existe. A recepção edita só os três slots, pela operação
`alterar_texto_de_boas_vindas`; `ler_texto_de_boas_vindas` vale para recepção e gestão.

## Personas de referência (Artefato 2)

- **Marina Duarte**, 34, gerente de contas, viaja a trabalho 2x/mês. Não instala app de
  hotel. Resolve tudo por WhatsApp.
- **Cléber Rocha**, 27, recepcionista do turno da tarde, 3 anos de casa. Pico das 14h às
  18h. Cético com sistema novo — o último virou mais uma tela para preencher.

**O Cléber é o risco de adoção, não a Marina.** Hóspede que ignora a mensagem só degrada
para o fluxo tradicional; recepcionista que abandona o painel paralisa o sistema.

## Custo — situação atual

Zero durante todo o desenvolvimento e a apresentação. O número de teste da Meta não gera
cobrança e dispensa cartão. IA, banco e hospedagem em camada gratuita.

Custo só existe em produção com número real. Simulação para hotel de 40 quartos, ~500
hóspedes/mês, 4 mensagens proativas por hóspede na categoria Utility: aproximadamente
R$ 100 a R$ 150/mês. **Ressalva do Artefato 2:** essa projeção só vale se toda mensagem
proativa for Utility. A oferta de retorno é Marketing e ficaria fora da conta.

**Marco a acompanhar:** a partir de 01/10/2026, respostas dentro da janela de 24 horas
também passam a ser cobradas. Não afeta o MVP; muda a projeção do produto comercial.

## Pendências abertas

Resolvidas pelo Artefato 4 — estrutura pronta, faltam apenas os valores:

- [x] ~~Política de retenção e prazo de exclusão dos dados~~ Ficha 5 anos, conversas
      12 meses, classificação campo a campo no dicionário
- [x] ~~Conteúdo e estrutura de D7~~ Tabela `catalogo_item`
- [x] ~~Status válidos de reserva e transições~~ Máquina de estados com trigger de validação
- [x] ~~Intervalo do reenvio e janela de corte~~ Viraram `parametro_hotel`
- [x] ~~Periodicidade da coleta de mercado~~ Mesmo mecanismo
- [x] ~~D5 registra valor monetário?~~ Sim para consumo faturável, com preço praticado

Resolvidas pelo Artefato 5:

- [x] ~~Idempotência dos webhooks~~ Restrição `UNIQUE`, com o fluxo descrito
- [x] ~~Ordem de chegada das mensagens~~ Não garantida no MVP, com justificativa
- [x] ~~Mecanismo de agendamento~~ Artefato 5 nomeou APScheduler; F1.4, F5.2 e F6.1
      entregam o comportamento em `worker/agendador.py` sem a biblioteca (Artigo XI).
      Pulso, mercado, cadastros e retenção varrem nesse laço. A lib permanece rejeitada
- [x] ~~Rotina de expurgo por retenção~~ F6.1: anonimização + exclusão da ficha + comprovante
      `execucao_retencao` consultável pela gestão. Não é auditoria genérica de UPDATE
- [x] ~~Acesso do staff ao Alert Center~~ Sessão longa por dispositivo

Resolvidas pelo Artefato 6:

- [x] ~~Faixa de preço e margem~~ Três planos com custo unitário e margem em dois cenários
- [x] ~~Contradições entre o Canvas e a arquitetura~~ Seis corrigidas, com registro de
      alterações no próprio documento

Lacunas encontradas no backlog (agosto/2026) — nenhuma tem fatia dedicada:

- [x] ~~**Não há como criar o primeiro hotel nem o primeiro usuário.**~~ Resolvido na F0.3 com
      comando de bootstrap que cria hotel, gestor inicial e `parametro_hotel` com valores padrão
- [x] ~~**`parametro_hotel` é lido por três fatias e escrito por nenhuma.**~~ F1.4 semeia
      `horas_ate_reenvio` e `horas_corte_antes_checkin` no bootstrap e na `0007`. Continua
      **sem tela** de edição (SQL no MVP), escolha registrada
- [x] ~~**Fechar o desenho de catálogo e preços**~~ F3.7 entregou `item_vendavel` e o retrato em `consumo.valor_praticado`. Catálogo de fatos (F2.1) permanece texto.
- [ ] **Contenção de tentativa repetida de senha** — fora da F0.3 de propósito (painel ainda não
      publicado). Precisa entrar antes de qualquer exposição contínua; a sessão longa do staff
      amplifica a consequência

Ainda abertas:

- [ ] **Documento de entrega desatualizado.** `Entrega_de_Projeto_OmniStay_v2.docx` é de
      06/08 e os slides de 11/08 — anteriores a toda a implementação. Dezenas de decisões
      mudaram o projeto desde então (recado de boas-vindas encurtado por limite da Meta,
      divisão de poderes gestão x recepção, quatro revisões de esquema). Comparar com o estado
      atual e atualizar antes da entrega final

- [ ] **Sem limite de tentativas no login (F0.3).** Cada tentativa custa ~0,4 s de CPU pelas
      600 mil iterações — bom contra força bruta, barato como negação de serviço. Aceitável hoje
      (painel atrás de túnel, poucos usuários); definir em qual fatia entra
- [ ] **`SameSite=Strict` quebra acesso por link externo.** Se o Alert Center passar a mandar
      link para o celular do staff, o primeiro clique cai em tela deslogada. Trocar para `Lax`
      quando isso acontecer — decisão antecipada, não descoberta

- [x] ~~**Executar o `04-schema.sql` num PostgreSQL real**~~ Feito na F0.2. O documento agora é
      aplicado a cada execução da suíte, num banco descartável, e comparado com o banco migrado
- [ ] **Ruído de fim de linha no repositório** — 18 arquivos aparecem modificados só por CRLF/LF
      (`git diff --ignore-all-space` volta vazio). Resolver com `.gitattributes` contendo
      `* text=auto eol=lf`, senão todo diff futuro vem poluído
- [x] ~~**Duas cópias dos documentos**~~ Resolvido: os sete artefatos viviam na raiz e em
      `omnistay/docs/`, e o `04-schema.sql` da raiz já estava desatualizado (sem as correções da
      F0.2). As cópias da raiz foram apagadas. **`omnistay/docs/` é a fonte única**, versionada
- [ ] **Confirmar junto à Meta a tarifação das mensagens dentro da janela a partir de
      01/10/2026** — as margens do cenário B do Canvas dependem disso
- [ ] Definir os **valores** dos parâmetros com o hotel (horas de reenvio, janela de corte,
      periodicidade da coleta)
- [x] ~~Cadastrar a lista de concorrentes~~ F5.1: API de manutenção + fontes ativas. **Verificar os termos de uso de cada fonte** permanece humano
- [x] ~~Coleta agendada de mercado~~ F5.2: varredura + `coleta_mercado` append-only
- [x] ~~Painel de mercado~~ F5.3: `GET /mercado` + histórico; dado velho sinalizado; série somente leitura
- [x] ~~Expurgo por retenção~~ F6.1: varredura diária efetiva, marcas, ficha aos 5 anos, `GET /retencao`
- [ ] Confirmar a lista oficial vigente de campos exigidos por lei para registro de hóspede
- [ ] Testar colagem no PMS real
- [ ] Confirmar junto à Meta a categoria do template de pulso do segundo dia
- [x] Redigir a pergunta de opt-in da pesquisa de checkout
- [ ] Reconferir as camadas gratuitas, se a hospedagem for retomada
- [ ] Validar as personas com um recepcionista real, se houver acesso durante o projeto
- [ ] Material do MVP de usuário, ainda não enviado

Detalhamento de duas delas, para não perder o contexto:

- **Colagem no PMS** — aceita `Ctrl+V`? Aceita bloco com tabulação entre campos, ou só valor
  por valor? Define se os auxílios de transcrição valem o esforço, e qual variação construir.
- **Acesso do staff** — recomendação: sessão longa por dispositivo, sem senha por chamado.
  Um profissional de manutenção com as mãos ocupadas não digita e-mail e senha no celular.

## Ordem dos artefatos

1. Mapa de processos ✅ v1.1
2. Jornada do usuário — hóspede e recepcionista ✅ v1.1
3. Fluxo de dados (DFD) e catálogo de eventos detalhado ✅ v1.1
4. Modelagem de dados (DER + dicionário) ✅ v1.0
5. Arquitetura e stack ✅ v1.0
6. Business Model Canvas — revisão completa ✅ v2.0

**Documentação concluída.** A partir daqui o trabalho é de implementação.

## Como trabalhar

Planejar e perguntar antes de produzir cada artefato. Trazer recomendação junto com a
pergunta, não apenas opções neutras. Registrar progresso e atualizar a documentação
continuamente, sem precisar ser lembrado.

Postura crítica esperada: apontar contradições entre documentos, campos redundantes na
modelagem, lacunas de LGPD e caminhos de exceção ausentes. É trabalho de banca — o valor
está em achar o que está frágil, não em validar o que já existe.
