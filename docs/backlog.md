# OmniStay — Backlog de fatias verticais

**Método:** cada fatia atravessa da entrada ao banco e entrega comportamento observável.
**Uso:** o texto em *Descrição para o `/specify`* é o que você cola no comando. Ele descreve
**o que**, nunca **como** — o "como" é trabalho do `/plan`.

---

## Como ler uma fatia

| Campo | Função |
| --- | --- |
| **Objetivo** | O comportamento que passa a existir |
| **Descrição para o `/specify`** | Texto pronto para colar no comando |
| **Critérios de aceite** | Cada linha vira ao menos um teste |
| **Depende de** | Fatias que precisam estar prontas antes |
| **Referência** | Onde a decisão foi tomada, para consulta em caso de dúvida |

**Regra de pronto**, válida para todas as fatias: testes escritos antes do código, todos
verdes, sem número mágico, sem conteúdo pessoal em log, e commit único e descritivo.

---

# Fase 0 — Fundação

Nada nesta fase entrega valor ao usuário. Toda ela existe para que o resto seja possível.

## F0.1 — Esqueleto caminhante

**Objetivo:** provar que a engrenagem inteira funciona, ponta a ponta, com uma funcionalidade
trivial.

**Descrição para o `/specify`:**
> Um endpoint de verificação de saúde que informa se a aplicação está no ar e se o banco de
> dados responde. Deve retornar sucesso quando ambos estão disponíveis e indicar falha
> quando o banco não responde, sem derrubar a aplicação.

**Critérios de aceite:**

- Com banco disponível, o endpoint responde sucesso
- Com banco indisponível, responde falha explícita e a aplicação continua no ar
- Existe um teste automatizado para cada um dos dois casos

**Depende de:** nada. **É a primeira.**
**Referência:** Artefato 5 §6.3 (estrutura de pastas).

> **Por que começar assim:** você descobre problema de configuração numa funcionalidade sem
> consequência, em vez de descobrir no meio do fluxo de webhook. Se o ciclo do Spec Kit
> travar, que trave aqui.

## F0.2 — Esquema e migrações

**Objetivo:** o banco existe, versionado, e o esquema do Artefato 4 está aplicado.

**Descrição para o `/specify`:**
> O esquema de dados do sistema precisa ser criado de forma versionada e reproduzível, de
> modo que qualquer ambiente possa ser levantado do zero até o estado atual, e que mudanças
> futuras sejam aplicadas em ordem. O esquema de referência está documentado em
> `04-schema.sql`.

**Critérios de aceite:**

- Migração aplica o esquema completo em banco vazio
- As restrições de domínio rejeitam valores inválidos
- A trigger de transição de estado rejeita uma transição inválida de reserva
- A restrição de unicidade de `evento_webhook` rejeita a segunda inserção do mesmo identificador
- Existe teste para cada uma das três garantias acima

**Depende de:** F0.1.
**Referência:** Artefato 4 completo, `04-schema.sql`.

**Status: concluída.** O esquema foi aplicado num PostgreSQL 16 real pela migração
`0001_esquema_inicial`, que executa uma cópia congelada do `04-schema.sql`. Duas divergências
apareceram na execução e foram corrigidas no documento: o `BEGIN`/`COMMIT` interno, que fecharia
a transação da migração antes do registro de versão, e a versão declarada do SGBD. Um teste de
conformidade compara, a cada execução da suíte, o banco migrado com o documento — inclusive o
corpo da função de transição — para que nenhuma migração futura possa fazê-los divergir.

> **Atenção:** esta é a primeira execução real do DDL. A verificação feita na documentação
> foi estrutural. **Erros aqui são esperados e são informação** — corrija o `04-schema.sql`
> junto, para documento e banco não divergirem.

## F0.3 — Autenticação e perfis

**Objetivo:** o painel tem acesso controlado, com os três perfis.

**Descrição para o `/specify`:**
> Funcionários do hotel acessam o painel com credenciais próprias e enxergam apenas o que o
> seu papel permite. A recepção vê reservas, fichas e confirmações de fase. A equipe
> operacional vê somente os chamados atribuídos, sem acesso a dados cadastrais de hóspedes.
> A gestão vê painéis de consulta, sem poder alterar dados. A equipe operacional acessa pelo
> celular e não deve precisar autenticar a cada chamado.

**Critérios de aceite:**

- Usuário sem credencial válida não acessa nenhum recurso protegido
- Perfil operacional recebe recusa ao tentar ler dados cadastrais de hóspede
- Perfil de gestão recebe recusa ao tentar alterar qualquer **dado de domínio** — reserva,
  hóspede, solicitação, consumo e avaliação
- Sessão do perfil operacional permanece válida por período longo no mesmo dispositivo
- Sessão pode ser revogada pela recepção
- Senha nunca é armazenada em texto legível
- Um comando de bootstrap cria a propriedade inicial, o usuário inicial de gestão e os
  `parametro_hotel` com valores padrão

**Depende de:** F0.2.
**Referência:** Artefato 4 §6.2, Artefato 5 §11.2.

> **Correção (11/08/2026).** O critério da gestão dizia "alterar qualquer dado", o que tornava
> impossível administrar usuários e deixava a fatia sem caminho para criar os perfis de recepção e
> de operação. Administrar usuário não é dado de domínio: **criar e desativar usuário é da gestão**
> — autoridade — e **revogar sessão de dispositivo é da recepção** — urgência, que não pode
> depender do gerente de madrugada. O bootstrap entrou como critério porque, sem ele, o painel
> exige login, o usuário exige hotel e nada cria o primeiro hotel.

**Status: concluída.** Sessão opaca em cookie, tabela `sessao` (revisão `0002`), matriz de
autorização, bootstrap e varredura de rotas protegidas.
---

# Fase 1 — Pré-chegada (P1)

## F1.1 — Cadastrar reserva

**Objetivo:** a recepção registra uma reserva e ela aparece na fila do dia.

**Descrição para o `/specify`:**
> A recepção registra uma nova reserva informando apenas nome, telefone de contato e as datas
> previstas de entrada e saída. O telefone é validado no momento da digitação, porque um
> dígito errado faz a comunicação inteira falhar ou chegar a um terceiro. A reserva nasce
> aguardando o cadastro do hóspede e passa a constar na fila do dia da recepção.

**Critérios de aceite:**

- Reserva criada com os três campos aparece na fila do dia
- Telefone em formato inválido é recusado com mensagem clara
- Data de saída anterior ou igual à de entrada é recusada
- Reserva nasce com status de aguardando cadastro
- Reserva de um hotel não aparece na fila de outro

**Depende de:** F0.3.
**Referência:** Artefato 2 R2, Artefato 4 §6.3.

**Status: concluída.** Módulo `hospedagem`, titular provisório na criação, telefone canônico,
fila nominada só para recepção, contagem de chegadas via `ler_indicadores`, revisão
`0003_fila_do_dia`. Sem tela React e sem envio WhatsApp (F1.2).

## F1.2 — Disparar a coleta de dados

**Objetivo:** o hóspede recebe o pedido de cadastro pelo WhatsApp.

**Descrição para o `/specify`:**
> Ao registrar a reserva, o sistema envia ao hóspede uma mensagem única solicitando os dados
> cadastrais em lista numerada, informando que o preenchimento antecipado é opcional e serve
> para evitar espera na chegada. A mensagem declara a finalidade da coleta e o contato do
> responsável pelos dados. O envio e a gravação da reserva são independentes: falha no envio
> não pode desfazer a reserva.

**Critérios de aceite:**

- Reserva registrada dispara exatamente uma mensagem de coleta
- Falha no envio mantém a reserva gravada e a marca para nova tentativa
- Mensagem enviada fica registrada no histórico da conversa
- Estado de entrega da mensagem é visível na fila do dia
- Nenhum dado pessoal do hóspede além do primeiro nome aparece na mensagem

**Depende de:** F1.1.
**Referência:** Artefato 1 §3, Artefato 2 F1, Artefato 5 §8.

**Status: concluída.** Tabela `trabalho`, módulo `conversa`, porta `MensageriaGateway` + falsa,
worker (`python -m worker --uma-passagem`), revisão `0005_trabalho_e_coleta`,
`status_envio_coleta` na fila do dia. Sem interpretação da resposta (F1.3) e sem lembrete
(F1.4).

> O último critério existe porque o telefone pode estar errado. A mensagem não pode revelar
> dados de um hóspede a um desconhecido.

## F1.3 — Receber e interpretar a ficha

**Objetivo:** a resposta do hóspede vira ficha consolidada no painel.

**Descrição para o `/specify`:**
> O hóspede responde em texto livre, em uma única mensagem, seguindo a lista numerada. O
> sistema extrai os campos, monta a ficha e a disponibiliza para a recepção. Quando apenas
> parte dos campos é reconhecida, a ficha é consolidada com o que veio e sinalizada como
> incompleta, sem que o sistema peça o restante por mensagem — o que falta é completado no
> balcão. Quando nada é reconhecido, o texto original é preservado e sinalizado para leitura
> humana.

**Critérios de aceite:**

- Resposta completa gera ficha completa e muda o status da reserva
- Resposta parcial gera ficha sinalizada como incompleta, sem nova mensagem ao hóspede
- Resposta irreconhecível preserva o texto original e sinaliza para leitura humana
- A ficha nunca é descartada por falha de interpretação
- A idade não é gravada em nenhum momento
- Ficha aparece na fila do dia com indicação do estado

**Depende de:** F1.2.
**Referência:** Artefato 2 F1, Artefato 3 §5.1, Artefato 4 §6.3.

**Status: concluída.** Webhook idempotente, `LLMProvider` + falsa, trabalho
`interpretar_ficha`, consolidação do titular, `estado_cadastro` na fila, revisão
`0006_interpretar_ficha`. Parcial sem nova mensagem; irreconhecível → leitura humana.

## F1.4 — Controlar o silêncio

**Objetivo:** quem não responde recebe um único lembrete, e depois é deixado em paz.

**Descrição para o `/specify`:**
> Passado o intervalo configurado para a propriedade sem resposta do hóspede, o sistema envia
> um único lembrete, explicando que o cadastro antecipado é opcional e que sem ele o
> preenchimento será feito na recepção. Persistindo o silêncio, o sistema para de insistir e
> sinaliza na fila do dia que aquela reserva chegará sem cadastro prévio. Os prazos são
> configuráveis por propriedade, não fixos.

**Critérios de aceite:**

- O lembrete é enviado uma única vez, nunca duas
- Após o segundo prazo sem resposta, a reserva é marcada como chegará sem cadastro
- Reserva marcada assim ainda permite check-in normalmente
- Resposta recebida entre os prazos cancela o lembrete pendente
- Prazos vêm da configuração da propriedade, não do código

**Depende de:** F1.3.
**Referência:** Artefato 1 §3.2, Artefato 5 §9.

**Status: concluída.** `worker/agendador.py` (`verificar_cadastros_pendentes`), trabalho
`enviar_lembrete` com unicidade por reserva, `reenvio_realizado`, status
`sem_cadastro_previo` na fila, prazos semeados (24 h / 12 h), revisão
`0007_controlar_silencio`. Sem APScheduler; sem tela de parâmetros; sem clique de check-in
(F2.2).

---

# Fase 2 — Chegada (P2)

## F2.1 — Catálogo da propriedade

**Objetivo:** o hotel cadastra os fatos que o sistema pode afirmar.

**Descrição para o `/specify`:**
> O hotel cadastra e mantém os fatos da propriedade organizados por categoria: horários,
> cardápio, serviços, programação e regras. Esse conteúdo é a única fonte a partir da qual o
> atendimento automatizado pode responder ao hóspede. Itens podem ser desativados sem serem
> apagados.

**Critérios de aceite:**

- Itens podem ser criados, editados e desativados por categoria
- Item desativado não é considerado pelo atendimento automatizado
- Catálogo de um hotel não é visível para outro
- Existe consulta que devolve o catálogo ativo completo de uma propriedade

**Depende de:** F0.3.
**Referência:** Artefato 3 §4.1, Artefato 4 §6.2.

> Esta fatia vem antes do check-in porque a conversa aberta na chegada depende dela: sem
> catálogo publicado, não há o que responder quando o hóspede pergunta.

## F2.2 — Confirmar chegada e dar boas-vindas

**Objetivo:** o clique da recepção dispara o recado de boas-vindas e abre a conversa.

**Descrição para o `/specify`:**
> A recepção confirma a chegada do hóspede no painel. Isso registra o momento real da entrada
> e dispara um recado curto de boas-vindas com as informações de entrada da propriedade,
> convidando o hóspede a perguntar o que quiser pelo mesmo canal. A confirmação só é possível
> para reservas que ainda não foram encerradas ou canceladas. Reservas cuja data prevista de
> entrada já passou sem confirmação são destacadas na fila do dia.

**Critérios de aceite:**

- Confirmação registra o momento real e muda o status para hospedado
- Recado curto de boas-vindas é enviado com as informações de entrada configuradas pela
  propriedade e termina convidando o hóspede a perguntar
- Confirmação em reserva encerrada ou cancelada é recusada
- Reserva com entrada prevista vencida e sem confirmação aparece destacada
- Mensagem de boas-vindas não contém oferta comercial

**Depende de:** F1.1, F2.1.
**Referência:** Artefato 2 F2 e R4, Artefato 5 §12.

> O último critério é econômico, não estético: oferta dentro do pacote faz a Meta
> reclassificar o template como marketing, multiplicando o custo por cerca de sete.

> **Correção (17/08/2026).** O critério dizia "pacote de boas-vindas é enviado usando o
> catálogo da propriedade", o que na execução não é enviável: variável de template da Cloud
> API recusa quebra de linha, tabulação e mais de quatro espaços seguidos, então o catálogo
> inteiro não cabe numa variável. O recado de chegada passa a ser **curto** — confirmação,
> três informações de entrada configuradas pela propriedade (café, wi-fi, checkout) e um
> convite a perguntar. **O catálogo continua sendo a única fonte de afirmação**, consumido
> sob demanda na janela de 24h pela F3.3. A F2.1 segue sendo pré-requisito: sem fatos
> publicados, a conversa aberta pelo recado não tem o que responder depois.

---

# Fase 3 — Estadia (P3)

A fase mais densa. São oito fatias, e a ordem entre elas importa.

## F3.1 — Receber mensagem com segurança e sem duplicar

**Objetivo:** o webhook recebe, valida, grava e responde rápido.

**Descrição para o `/specify`:**
> O sistema recebe as mensagens dos hóspedes por notificação do provedor de mensageria. Antes
> de qualquer processamento, verifica que a notificação é autêntica e veio de fato do
> provedor. Notificações repetidas do mesmo evento são descartadas sem efeito. A resposta ao
> provedor é imediata; todo o processamento acontece depois, a partir de uma fila durável que
> sobrevive a reinicialização da aplicação.

**Critérios de aceite:**

- Notificação com assinatura inválida é recusada sem processamento
- Notificação sem assinatura é recusada
- Mesma notificação recebida duas vezes é processada uma única vez
- A resposta ao provedor não espera classificação nem envio de mensagem
- Mensagem gravada permanece na fila se a aplicação for reiniciada antes do processamento
- Conteúdo da mensagem não aparece em nenhum log

**Depende de:** F0.2.
**Referência:** Artefato 5 §7, §8 e §11.1.

> A verificação de assinatura é o item de segurança mais esquecido em webhooks, e o mais
> provável de virar pergunta em banca.

## F3.2 — Classificar a intenção

**Objetivo:** cada mensagem recebida ganha intenção, sentimento e urgência.

**Descrição para o `/specify`:**
> Cada mensagem recebida é classificada quanto à intenção, ao sentimento e à urgência, para
> que o sistema decida entre responder automaticamente e envolver uma pessoa. Quando a
> classificação não é possível — por indisponibilidade do serviço de classificação ou por
> resposta inválida — a mensagem é preservada e encaminhada para atendimento humano.

**Critérios de aceite:**

- Mensagem classificada registra intenção, sentimento e urgência
- A resposta completa do classificador é preservada para auditoria posterior
- Serviço indisponível encaminha para humano, sem perder a mensagem
- Resposta em formato inválido encaminha para humano
- O teste roda sem depender de serviço externo

**Depende de:** F3.1.
**Referência:** Artefato 1 §5.1, Artefato 5 §10.1, Artefato 5 §13.2.

## F3.3 — Responder dúvida a partir do catálogo

**Objetivo:** perguntas simples são respondidas sem envolver ninguém.

**Descrição para o `/specify`:**
> Perguntas classificadas como dúvida geral são respondidas automaticamente, usando
> exclusivamente os fatos cadastrados no catálogo da propriedade. Quando a resposta não está
> no catálogo, o sistema não responde por conhecimento próprio: informa o hóspede que a
> recepção vai atender e abre um chamado.

**Critérios de aceite:**

- Pergunta coberta pelo catálogo recebe resposta automática
- Pergunta não coberta gera chamado e aviso ao hóspede, sem resposta inventada
- A resposta automática não cita informação ausente do catálogo
- Catálogo de outra propriedade nunca é usado

**Depende de:** F2.1, F3.2.
**Referência:** Artefato 3 §5.2, Artefato 5 §10.2 e §10.3.

## F3.4 — Registrar pedido de serviço

**Objetivo:** pedidos operacionais viram tarefa, com confirmação imediata.

**Descrição para o `/specify`:**
> Pedidos de serviço sem cobrança — toalha, travesseiro, cobertor — são registrados como
> tarefa operacional e confirmados ao hóspede imediatamente. A confirmação acontece antes de
> qualquer outro processamento.

**Critérios de aceite:**

- Pedido gera solicitação do tipo serviço, com quarto e descrição
- Confirmação ao hóspede é enviada antes do encaminhamento à equipe
- Solicitação aparece na fila da equipe operacional
- Pedido de serviço não gera valor a cobrar

**Depende de:** F3.2.
**Referência:** Artefato 3 §4.2, Artefato 4 §3.

## F3.5 — Abrir chamado de reclamação

**Objetivo:** reclamação técnica vira chamado com contexto, e o hóspede sabe disso na hora.

**Descrição para o `/specify`:**
> Reclamações técnicas com sentimento negativo geram chamado para a equipe operacional. Antes
> de qualquer tramitação, o hóspede recebe confirmação de que a mensagem foi recebida e de
> que a manutenção está sendo acionada, e é perguntado sobre o horário de sua preferência
> para o atendimento. O chamado registra quarto, tipo, urgência e a janela informada.

**Critérios de aceite:**

- Confirmação ao hóspede ocorre antes da criação do chamado
- Chamado registra quarto, tipo, urgência e janela de preferência
- Chamado aparece no Alert Center da equipe operacional
- A mensagem que originou o chamado fica vinculada a ele
- Chamado aberto há tempo excessivo é destacado

**Depende de:** F3.2.
**Referência:** Artefato 1 §5.1, Artefato 2 F3b, Artefato 4 §6.5.

## F3.6 — Resolver chamado e confirmar

**Objetivo:** o ciclo do chamado fecha e o hóspede é avisado.

**Descrição para o `/specify`:**
> A equipe operacional marca o chamado como resolvido pelo celular, e o hóspede recebe
> confirmação da resolução. Chamados não resolvidos permanecem visíveis na passagem de turno.

**Critérios de aceite:**

- Marcar como resolvido registra quem resolveu e quando
- Hóspede recebe confirmação após a resolução
- Chamado não pode ser resolvido duas vezes
- Chamados abertos aparecem na tela de passagem de turno

**Depende de:** F3.5.
**Referência:** Artefato 1 §5, Artefato 2 R5 e R7.

## F3.7 — Consumo faturável e fila de lançamento

**Objetivo:** o que gera cobrança não se perde entre o chat e o PMS.

**Descrição para o `/specify`:**
> Pedidos que geram cobrança — consumo do bar, impressão, lavanderia — são registrados com o
> valor praticado no momento do pedido e nascem pendentes de lançamento no sistema de gestão
> do hotel. Permanecem em fila destacada no painel até que um funcionário confirme o
> lançamento. A fila de pendências aparece também na passagem de turno.

**Critérios de aceite:**

- Consumo registra descrição e valor praticado no momento
- Consumo nasce pendente de lançamento
- Marcar como lançado exige identificar quem lançou e quando
- Consumos pendentes aparecem em fila destacada e na passagem de turno
- Valor não referencia tabela de preços: reajuste posterior não altera o histórico
- Pedido de serviço sem cobrança não entra nesta fila

**Depende de:** F3.4.
**Referência:** Artefato 3 §4.2 e §7, Artefato 4 §3, Artefato 6 §5.4.

> Esta é a fatia com consequência financeira. Se o lançamento falha, o hotel presta o serviço
> e não cobra, e ninguém percebe — o hóspede não reclama de um item que não foi cobrado.

## F3.8 — Pulso do segundo dia

**Objetivo:** detectar insatisfação enquanto ainda dá tempo de corrigir.

**Descrição para o `/specify`:**
> No segundo dia de estadia, o sistema envia uma única pergunta sobre a experiência do
> hóspede. O envio é suprimido quando há chamado em aberto para aquela estadia ou quando
> restam menos de vinte e quatro horas de hospedagem, porque nesses casos ele deixa de servir
> ao propósito de permitir correção. Resposta negativa gera chamado para a equipe.

**Critérios de aceite:**

- Envio ocorre uma única vez por estadia
- Envio é suprimido com chamado em aberto
- Envio é suprimido com menos de 24 horas restantes
- Resposta negativa gera chamado
- O prazo mínimo vem da configuração da propriedade

**Depende de:** F3.5, F2.2.
**Referência:** Artefato 1 §5.2, Artefato 2 F3c, Artefato 5 §9.

---

# Fase 4 — Checkout (P4)

## F4.1 — Confirmar saída e enviar pesquisa

**Objetivo:** o checkout dispara a avaliação e a coleta de consentimento.

**Descrição para o `/specify`:**
> A recepção confirma a saída do hóspede no painel, o que encerra a estadia e envia a pesquisa
> de avaliação. A pesquisa é curta — nota, comentário opcional e uma pergunta final sobre
> aceitar receber comunicações futuras. A resposta a essa última pergunta é registrada como
> consentimento, com data e hora, e pode ser revogada depois. Reservas com saída prevista
> vencida e ainda não confirmadas são destacadas na fila.

**Critérios de aceite:**

- Confirmação só é possível para reserva com entrada já confirmada
- Pesquisa é enviada após a confirmação
- Consentimento é registrado com data, hora e origem
- Revogação cria novo registro, sem apagar o anterior
- Consulta de consentimento devolve o estado vigente em qualquer data passada
- Reserva com saída prevista vencida e sem confirmação aparece destacada

**Depende de:** F2.2.
**Referência:** Artefato 1 §6, Artefato 4 §6.3, Artefato 6 §1.

## F4.2 — Lista de pedidos feitos pelo chat

**Objetivo:** o hóspede vê o que foi solicitado e será cobrado.

**Descrição para o `/specify`:**
> No encerramento da estadia, o hóspede pode consultar a lista dos consumos que solicitou pelo
> chat, com valores. A lista inclui somente o que gera cobrança — pedidos de serviço sem custo
> não aparecem. Em nenhum ponto da interface ou das mensagens essa lista é chamada de extrato
> ou de conta.

**Critérios de aceite:**

- Somente consumos faturáveis aparecem na lista
- Pedidos de serviço sem cobrança não aparecem
- O termo "extrato" e o termo "conta" não aparecem em nenhum texto da funcionalidade
- Valores exibidos são os praticados no momento de cada pedido

**Depende de:** F3.7, F4.1.
**Referência:** Artefato 1 §6.1, Artefato 3 §4.2.

---

# Fase 5 — Inteligência de mercado (P5)

## F5.1 — Cadastro de concorrentes

**Objetivo:** o hotel define quais propriedades quer acompanhar.

**Descrição para o `/specify`:**
> O hotel cadastra os concorrentes que deseja acompanhar, informando nome e endereço da fonte
> pública de consulta. Fontes podem ser desativadas sem serem apagadas.

**Critérios de aceite:**

- Concorrentes podem ser criados, editados e desativados
- Concorrente de um hotel não é visível para outro
- Fonte desativada não é consultada

**Depende de:** F0.3.
**Referência:** Artefato 4 §6.6.

## F5.2 — Coleta agendada

**Objetivo:** os preços dos concorrentes entram na base sozinhos, com data e sem violar
termos de uso.

**Descrição para o `/specify`:**
> Na periodicidade configurada para a propriedade, o sistema consulta as fontes públicas dos
> concorrentes ativos e registra preço e avaliação encontrados, sempre com a data da coleta.
> Coletas que falham são registradas como falha, e não confundidas com ausência de valor. O
> coletor respeita as diretivas de acesso da fonte, identifica-se honestamente e não coleta
> dado pessoal de avaliadores.

**Critérios de aceite:**

- Cada coleta insere novo registro, sem sobrescrever o anterior
- Toda coleta registra a data e se teve sucesso
- Falha de coleta não apaga nem substitui o dado anterior
- O coletor respeita as diretivas de acesso publicadas pela fonte
- Nenhum dado pessoal de avaliador é armazenado
- A periodicidade vem da configuração da propriedade

**Depende de:** F5.1.
**Referência:** Artefato 4 §6.6, Artefato 5 §15.1, Artefato 6 §10.3.

## F5.3 — Painel de mercado

**Objetivo:** a gestão compara tarifas sem sair do sistema, e sabe de quando é cada número.

**Descrição para o `/specify`:**
> A gestão consulta os preços e avaliações coletados, com a data de cada coleta sempre
> visível, e acompanha a variação ao longo do tempo. Dado antigo é exibido com indicação
> explícita de quando foi coletado.

**Critérios de aceite:**

- Cada valor exibido mostra a data da coleta
- Histórico permite observar variação ao longo do tempo
- Dado desatualizado é sinalizado como tal
- Perfil de gestão não consegue alterar nenhum registro

**Depende de:** F5.2.
**Referência:** Artefato 3 §4.1.

---

# Fase 6 — Transversais

Podem ser feitas em paralelo às fases anteriores, mas nenhuma delas deve ser adiada até o fim.

## F6.1 — Expurgo por retenção

**Objetivo:** o prazo declarado na documentação passa a ser cumprido de fato, e comprovável.

**Descrição para o `/specify`:**
> O sistema aplica automaticamente a política de retenção de dados pessoais. Conteúdo de
> conversas e comentários de avaliação é anonimizado doze meses após a saída do hóspede,
> preservando as estatísticas de volume. Fichas cadastrais são apagadas cinco anos após a
> última estadia. Toda execução registra o que foi tratado, para que o cumprimento possa ser
> demonstrado.

**Critérios de aceite:**

- Conteúdo de conversa é anonimizado no prazo, e a linha permanece
- Estatística de volume de atendimento continua correta após a anonimização
- Ficha cadastral é apagada no prazo
- Cada execução registra quantidade e tipo do que foi tratado
- Dados dentro do prazo não são tocados

**Depende de:** F0.2.
**Referência:** Artefato 4 §6.1, Artefato 5 §9.1.

> **Não deixe esta para o fim.** A documentação declara os prazos publicamente. Prazo
> declarado e não cumprido é pior do que prazo não declarado.

## F6.2 — Simulador de conversa

**Objetivo:** demonstrar o sistema inteiro à banca sem depender de rede, de número de
telefone ou da disponibilidade da Meta no dia.

**Descrição para o `/specify`:**
> Existe um modo de demonstração em que as mensagens trocadas com o hóspede aparecem em uma
> tela de simulação em vez de serem enviadas pelo provedor real, permitindo demonstrar o
> sistema completo sem depender de rede externa nem de número de telefone. O comportamento do
> sistema é idêntico nos dois modos.

**Critérios de aceite:**

- Alternar entre modo real e simulado é configuração, não mudança de código
- O fluxo demonstrado no simulador é o mesmo do modo real
- Nenhuma regra de negócio se comporta de forma diferente entre os modos

**Depende de:** F3.1.
**Referência:** Artefato 5 §5.1 e §12.1.

**Status: concluída.** Canal de demonstração por configuração `MENSAGERIA_MODO`, fábrica no worker (`MensageriaSimulada` em demo; WhatsApp só em `real`), tela React em `frontend/` com estáticos em `/demo/` se houver build. GET/POST `/simulador/conversas` reusam `receber_evento_entrada` e a tabela `mensagem`; operação única `usar_simulador`. Sem túnel, sem painel operacional React, sem migração, sem instância de WhatsApp na suíte.

> **Esta é a fatia que garante a apresentação à banca.** Vale tratá-la como prioridade alta
> assim que a Fase 3 estiver caminhando.

---

## Ordem recomendada

```
F0.1 → F0.2 → F0.3
        ↓
F1.1 → F1.2 → F1.3 → F1.4
        ↓
F2.1 → F2.2
        ↓
F3.1 → F3.2 → F3.3
              ↓
            F3.4 → F3.7
              ↓
            F3.5 → F3.6
              ↓
            F3.8
        ↓
F4.1 → F4.2
        ↓
F5.1 → F5.2 → F5.3

Em paralelo, a partir de F3.1:  F6.2 (simulador)
Em paralelo, a partir de F0.2:  F6.1 (expurgo)
```

**Se o prazo apertar**, o corte defensável é a Fase 5 reduzida — coleta manual em vez de
agendada, com o painel funcionando. O que **não** pode ser cortado: F3.1 (segurança do
webhook), F6.1 (expurgo declarado) e F6.2 (simulador da apresentação).

---

---

# Plano de uma semana — decidido em 26/08/2026

**Prazo real: sete dias.** As Fases 7 e 8 somam doze fatias e não cabem. Este plano registra o
que entra, o que sai e **por quê** — para que o corte seja escopo declarado, e não lacuna
descoberta pela banca.

## O que entra

| Dia | Entrega | Por quê |
| --- | --- | --- |
| 1 | **F7.1** adaptador real de IA **+ aviso de assistente virtual** | Sem isso a demonstração mostra um sistema que responde "a recepção vai atender" a qualquer pergunta. É a fatia com maior efeito por hora gasta |
| 2 | **F8.1** casca do painel: Tailwind + shadcn/ui, login, rota por perfil | Toda tela depende dela. Inclui montar o ferramental de interface, que só se paga uma vez |
| 3 | **F8.2** fila do dia, nova reserva, confirmar chegada | É a tela que decide a adoção. Se só uma tela existisse, seria esta |
| 4 | **F8.4** chamados, pedidos e a tela da equipe no celular | O Alert Center é o que substituiu o app da equipe. Sem ele o corte fica visível |
| 5 | **F8.6** catálogo, itens vendáveis e recado de boas-vindas — com a **F7.3** (linha de convite) junto | São as telas que alimentam a IA. Sem elas, configurar a demonstração vira digitar JSON no `/docs` |
| 6 | **F8.3** ficha do hóspede + **F8.5** consumos e saída | Fecham o ciclo completo de uma estadia, do cadastro ao checkout |
| 7 | **Documento acadêmico, slides, vídeo e ensaio da demonstração** | É o que é avaliado. Não é dia de sobra: é dia de entrega |

## O que sai — escopo declarado

| Fatia | Motivo do corte | O que dizer à banca |
| --- | --- | --- |
| **F7.4** módulos por propriedade | Coerência com o Canvas, mas nenhum efeito na demonstração | "Os três planos estão desenhados e a estrutura (`parametro_hotel`) já existe; ligar e desligar é fatia mapeada" |
| **F7.5** canal de e-mail | Maior fatia da fase. Exige caixa IMAP monitorada e uma segunda identidade de hóspede | "O miolo já é agnóstico de canal — tudo entra pela mesma porta. O e-mail é porta nova, não sistema novo, e está especificado" |
| **F8.7** painel da gestão, mercado, usuários e retenção | Todas são telas de leitura. O `/docs` demonstra os mesmos dados | "As funcionalidades existem e são demonstráveis pela API; a interface delas é a próxima entrega" |
| **Personalidade configurável** | Só o **aviso de IA** entra (uma linha, custo zero). O campo de tom fica para depois | "A porta está pronta; o campo de tom entra sem tocar no resto" |

## Como acelerar sem perder o método

O ciclo completo do Spec Kit — `specify` → `clarify` → `plan` → `tasks` → `analyze` →
`implement` — custa caro. Nas fatias de tela, **os wireframes já são a especificação**: layout,
campos, perfis e endpoints estão em `docs/wireframes-painel.html`.

Recomendação para os dias 2 a 6: `specify` → `plan` → `tasks` → `implement`, sem `clarify` nem
`analyze`. A F7.1 mantém o ciclo completo, porque toca o comportamento do sistema e não só a
apresentação dele.

**O que não se corta:** TDD. O Artigo XII não é cerimônia — é o que permitiu mexer no esquema
onze vezes sem quebrar nada. Numa semana apertada, é justamente ele que evita o dia perdido
caçando regressão.

## Decisões de frontend fechadas em 26/08/2026

| Tema | Decisão |
| --- | --- |
| Onde mora | **Estende o `frontend/` que já existe** (Vite + React + TypeScript), com rotas. Não é aplicação nova: o simulador vira uma rota entre as outras |
| Visual | **Tailwind + shadcn/ui.** Componentes copiados para dentro do projeto, sem dependência de runtime. É o mesmo ferramental do protótipo do Replit, então o visual dele pode ser aproveitado sem o código |
| Celular | **Só a tela da equipe.** Recepção e gestão usam computador, no balcão e na sala. Responsividade completa custa em dezesseis telas e resolve um problema que não existe |
| Sessão | Cookie `HttpOnly` já entregue pela API. A tela nunca toca o token, e não há estado de autenticação para guardar no navegador |
| Estado | Sem biblioteca de estado global. Cada tela busca o que precisa; a fila do dia recarrega ao concluir uma ação |

---

# Fase 7 — Assistente, personalização e canais

**Por que esta fase existe.** As 24 fatias originais entregaram o comportamento do sistema, mas
com três lacunas que só apareceram quando o produto foi visto rodando:

1. A camada de IA não tem implementação real — o worker de produção usa o adaptador falso, e toda
   pergunta cai no ramo humano.
2. Não há como o hotel ajustar o tom da assistente, nem como o hóspede saber que fala com uma IA.
3. Todo hotel recebe tudo, enquanto o Canvas promete três planos com escopos diferentes.

**Ela vem antes da Fase 8 (painel) de propósito.** Se a modularização chegar depois das telas, as
telas nascem sem saber esconder módulo desligado e precisam ser refeitas.

## Decisões que governam a fase

| Tema | Decisão | Motivo |
| --- | --- | --- |
| Personalidade da assistente | Texto livre em `parametro_hotel`, entra no prompt **antes** das regras fixas | O hotel muda o tom; nunca o limite do que a IA pode afirmar |
| Regra do catálogo | Continua no código, e é sempre a última instrução do prompt | Ordem importa: o que vem por último pesa mais, e o hotel não alcança essa parte |
| Aviso de IA | Frase fixa na primeira mensagem de cada estadia | Não é escolha do hotel — é postura do produto |
| Módulos | Linhas em `parametro_hotel`, não tabela nova | Mesmo padrão dos prazos e dos textos de boas-vindas |
| Núcleo | Reserva, ficha, chamados e catálogo **nunca** desligam | Sem eles não existe produto |
| Canal proativo | Sempre WhatsApp | Templates, janela e custo já foram desenhados em cima dele |
| Canal reativo | O mesmo em que o hóspede escreveu | Regra única, sem tabela de preferência e sem escolha a errar |

---

## F7.1 — Adaptador real de IA

**Objetivo:** o sistema passa a pensar de verdade.

**Descrição para o `/specify`:**
> O sistema conversa com um serviço de modelo de linguagem real para classificar mensagens e
> redigir respostas, no lugar da implementação falsa que hoje o worker utiliza. Escolher entre o
> serviço real e o falso é configuração, não mudança de código. Falha, demora excessiva ou
> resposta em formato inválido do serviço não perdem a mensagem: ela segue para atendimento
> humano, como já acontece hoje.

**Critérios de aceite:**

- Alternar entre serviço real e falso é configuração
- Chave de acesso vem do ambiente e nunca aparece em arquivo versionado nem em log
- Chamada que ultrapassa o tempo limite encaminha para humano, sem travar o worker
- Resposta em formato inválido encaminha para humano
- Nenhum teste depende de rede ou consome chamada do serviço real
- Conteúdo de mensagem de hóspede continua fora do log

**Depende de:** F3.2, F3.3, F6.2.

> É a menor fatia da fase e a que mais muda a demonstração. Sem ela, o painel da Fase 8 exibe um
> sistema que responde "a recepção vai atender" a qualquer pergunta.

---

## F7.2 — Personalidade da assistente e aviso de IA

**Objetivo:** a assistente soa como a casa, e o hóspede sabe com quem fala.

**Descrição para o `/specify`:**
> A propriedade descreve, em texto livre, o tom que a assistente deve ter ao conversar com o
> hóspede. Esse tom afeta a forma das respostas automáticas, nunca o conteúdo: a assistente
> continua limitada aos fatos do catálogo, e nenhuma instrução da propriedade é capaz de remover
> esse limite. A primeira mensagem de cada estadia informa ao hóspede que o atendimento inicial é
> feito por uma assistente virtual e que uma pessoa assume quando necessário.

**Critérios de aceite:**

- Descrição de tom vazia mantém a assistente funcionando, com voz padrão
- Tom configurado altera a redação das respostas automáticas
- Texto que instrua a assistente a ignorar o catálogo não surte efeito: a resposta continua fiel
- A primeira mensagem de cada estadia informa que o atendimento é por assistente virtual
- Hóspede que pede para falar com uma pessoa é encaminhado, sem insistência
- Descrição de tom tem tamanho máximo e é recusada acima dele

**Depende de:** F7.1.

> O terceiro critério é de segurança, não de qualidade. Campo de texto livre que entra num prompt
> é superfície de ataque: a mitigação é a regra do catálogo ser sempre a última instrução, fora do
> alcance de quem edita o campo.

---

## F7.3 — Linha de convite no recado de boas-vindas

**Objetivo:** o hotel escreve o convite com as próprias palavras.

**Descrição para o `/specify`:**
> Além das três informações de entrada, o recado de boas-vindas passa a ter uma linha de convite
> mantida pela propriedade, que diz ao hóspede o que ele pode perguntar por ali — serviços,
> cardápio, horários. A linha segue as mesmas restrições de formato dos outros campos e nunca fica
> vazia.

**Critérios de aceite:**

- A linha de convite aparece no recado enviado
- Valor com quebra de linha, tabulação ou espaços múltiplos é recusado ao salvar
- Propriedade recém-instalada já tem um convite padrão preenchido
- Convite vazio impede o envio e sinaliza na fila do dia, como os outros três campos
- Recepção edita; gestão lê; perfil operacional recebe recusa

**Depende de:** F2.2.

> Estrutura de template já aprovada não muda: é uma variável a mais com rótulo fixo, no mesmo
> molde dos outros três.

---

## F7.4 — Módulos por propriedade

**Objetivo:** o escopo do sistema acompanha o plano contratado.

**Descrição para o `/specify`:**
> Cada propriedade tem um conjunto de funcionalidades opcionais que podem estar ligadas ou
> desligadas: inteligência de mercado, pulso do segundo dia, consumo faturável e pesquisa de
> saída. Funcionalidade desligada não é executada pelo sistema nem oferecida na interface. O
> núcleo da operação — reserva, ficha, chamados e catálogo — não é desligável.

**Critérios de aceite:**

- Funcionalidade desligada não dispara mensagem nem tarefa agendada
- Recurso de funcionalidade desligada responde como inexistente, sem revelar que existe
- Ligar uma funcionalidade passa a valer sem reiniciar o sistema
- Desligar não apaga dado já gravado
- Só a gestão altera o estado dos módulos
- Núcleo não aparece na lista do que pode ser desligado

**Depende de:** F5.3, F3.8, F3.7, F4.1.

> Isto é a expressão técnica dos três planos do Business Model Canvas. Sem ela, o Canvas promete
> escopos que o sistema não sabe entregar.

---

## F7.5 — E-mail como segundo canal

**Objetivo:** o hub conversacional deixa de ser só WhatsApp.

**Descrição para o `/specify`:**
> O hóspede pode ter um endereço de e-mail registrado, e pode conversar com a propriedade por
> esse endereço. Mensagem recebida por e-mail entra pelo mesmo caminho de uma mensagem de
> WhatsApp e recebe o mesmo tratamento: classificação, resposta automática pelo catálogo,
> abertura de chamado. A resposta sai pelo mesmo canal em que o hóspede escreveu. Mensagens que o
> sistema inicia continuam saindo por WhatsApp.

**Critérios de aceite:**

- Mensagem recebida por e-mail é classificada e respondida como a de WhatsApp
- A resposta sai pelo canal de origem da mensagem
- Cada mensagem registra por qual canal entrou ou saiu
- Remetente desconhecido não é tratado como hóspede e não recebe dado de ninguém
- Mensagem repetida não gera atendimento duplicado
- Falha do canal de e-mail não afeta o WhatsApp, e vice-versa
- E-mail é opcional: reserva sem e-mail funciona como hoje

**Depende de:** F3.1, F3.2, F3.3, F7.4.

> **É a maior fatia da fase, e o corte defensável se o prazo apertar.** A promessa de hub
> conversacional se sustenta com WhatsApp; o e-mail a amplia. Se cortar, registrar como escopo
> declarado e não como esquecimento.

---

## F7.6 — A recepção responde ao hóspede

**Objetivo:** fechar o ciclo do atendimento. Hoje ele não fecha.

**O buraco que ela tapa.** Quando o atendimento automático não cobre a pergunta, o sistema avisa
o hóspede que a recepção vai atender, abre o chamado e permite marcá-lo como resolvido. Mas
**não existe forma de a recepção escrever a resposta**. O hóspede pergunta se tem berço, ouve que
a recepção vai atender, e depois recebe "seu chamado foi resolvido" — sem nunca ter recebido a
resposta. É falha de lógica do produto, não de acabamento.

**Descrição para o `/specify`:**
> A recepção responde ao hóspede pelo painel, com texto livre, quando o atendimento automático
> encaminha uma pergunta ou quando ela precisa dizer algo sobre um chamado. A resposta chega ao
> hóspede pelo mesmo canal em que ele escreveu e fica registrada no histórico da conversa, junto
> das mensagens automáticas.

**Critérios de aceite:**

- A recepção escreve e o hóspede recebe pelo canal de origem da mensagem
- A resposta fica no histórico da conversa, junto das automáticas
- Só o perfil de recepção responde: a equipe operacional resolve chamado mas não escreve ao
  hóspede, e a gestão não escreve
- O envio passa pela fila e pelo worker, como todas as outras mensagens
- Falha no envio não perde o texto escrito: fica marcada para nova tentativa e visível no painel
- Responder **não** resolve o chamado automaticamente — são ações distintas
- Conteúdo de mensagem continua fora do log

**Depende de:** F3.1, F3.3, F8.4.

> Não precisa de template aprovado: o hóspede escreveu há pouco, então a janela de 24 horas está
> aberta e a resposta é texto livre. Custo zero até 01/10/2026.

---

## Ordem recomendada da Fase 7

```
F7.1 → F7.2 → F7.3 → F7.6 → F7.4 → F7.5
```

F7.1 primeiro porque muda a demonstração inteira. F7.4 antes da Fase 8 porque as telas precisam
nascer sabendo esconder módulo desligado.

## Perguntas a resolver com teste, não no papel

Estas ficam abertas de propósito. São coisas que só o uso responde, e cada uma deve virar ajuste
depois da primeira rodada com gente de verdade:

- **O tom configurado muda mesmo a percepção do hóspede**, ou o efeito some depois de duas frases?
- **Onde o aviso de IA incomoda menos** — na primeira mensagem, na assinatura de cada resposta, ou
  só quando o hóspede pergunta?
- **Quantos hóspedes respondem por e-mail** quando têm as duas opções. Se for perto de zero, o
  canal vira custo de manutenção sem retorno.
- **Qual das linhas do recado de boas-vindas o hóspede usa** — se ninguém pergunta sobre cardápio
  depois do convite, o convite está mal escrito ou mal posicionado.
- **Se desligar um módulo confunde o recepcionista** que já se acostumou com ele.

---

# Fase 8 — Painel de operação (React)

**Por que esta fase existe.** As 24 fatias entregaram o backend inteiro — 27 operações
autorizadas, 21 revisões de esquema, worker, fila e webhook. Mas **nenhuma delas construiu o
painel**: todas diziam "sem tela React". A única interface que existe é o simulador da F6.2,
feito para demonstrar a conversa do hóspede, não para operar o hotel.

Hoje o sistema só é operável pelo `/docs` do FastAPI. Isso não é entregável.

## A decisão: construir do zero, não adaptar o protótipo

| | Construir fatias novas (**escolhido**) | Ligar o protótipo do Replit |
| --- | --- | --- |
| Cobertura | As 27 operações, por desenho | 5 telas: painel, mercado, simulador, alertas, conversas |
| O que falta | Nada — o backend está pronto | Fila do dia, reserva, ficha, catálogo, itens vendáveis, consumos, saída, boas-vindas, usuários, sessões, retenção |
| Alinhamento com a API | Contratos reais desde a primeira linha | Protótipo desenhado antes da API; nomes e formatos divergem |
| Perfis | Recusa por perfil testada, como no backend | Não previstos |
| Esforço | Maior | Menor no início, maior no acerto |
| Risco | Baixo — repete um método já validado 24 vezes | Alto — retrabalho invisível até aparecer |

**Motivo da escolha:** o protótipo cobre a parte gerencial e deixa de fora justamente o núcleo
operacional, que é onde mora o risco de adoção do projeto. Ele serve como **referência visual**,
não como base de código.

**Referência de layout:** `docs/wireframes-painel.html` — 15 telas, com o endpoint de cada uma.

## Regras da fase

- Nenhuma fatia da Fase 7 altera o backend. Se uma tela precisar de algo que a API não oferece,
  isso é achado a registrar, não licença para mudar contrato no meio do caminho.
- Cada fatia entrega tela **funcionando contra a API real**, não maquete.
- Toda tela respeita a matriz de perfis: o que a API recusa, a tela não oferece.
- Dado pessoal não trafega para quem não pode vê-lo. Filtro na origem, nunca na tela.

---

## F8.1 — Casca do painel e login

**Objetivo:** entrar no sistema e chegar à tela certa do seu perfil.

**Descrição para o `/specify`:**
> O funcionário entra com e-mail e senha e é levado à tela inicial correspondente ao seu papel:
> a recepção à fila do dia, a equipe operacional aos seus chamados, a gestão ao painel de
> indicadores. A sessão permanece válida entre visitas no mesmo dispositivo, e sair encerra a
> sessão no servidor. Enquanto a sessão for válida, o funcionário não precisa autenticar de novo.

**Critérios de aceite:**

- Credencial inválida recusa sem revelar se o e-mail existe
- Cada perfil chega à sua tela inicial após entrar
- Recarregar a página mantém a sessão
- Sair encerra a sessão no servidor, não apenas no navegador
- Item de menu que o perfil não pode usar não aparece
- Sessão expirada devolve à tela de entrada sem erro de tela branca

**Depende de:** F0.3.

---

## F8.2 — Fila do dia e cadastro de reserva

**Objetivo:** o turno inteiro da recepção numa tela só.

**Descrição para o `/specify`:**
> A recepção vê, na tela inicial, quem chega hoje, quem já está hospedado e quem deveria ter
> chegado e não foi confirmado. Da mesma tela ela cadastra uma reserva nova com nome, telefone e
> datas, e confirma a chegada de quem apareceu no balcão. Reservas com pendência — ficha
> incompleta, recado de boas-vindas não enviado, chegada vencida — são destacadas.

**Critérios de aceite:**

- A fila mostra chegadas do dia, hospedados e chegadas vencidas, e não reservas futuras
- Cadastro de reserva pede apenas nome, telefone e datas, com telefone validado na digitação
- Confirmar chegada muda a situação na própria lista, sem recarregar a página
- Sinalização de chegada vencida e de recado não enviado aparecem distintas
- Perfil de gestão e perfil operacional recebem recusa nesta tela

**Depende de:** F8.1, F1.1, F2.2.

> É a tela que decide a adoção. Se o Cléber precisar navegar para fazer o trabalho do turno,
> ele volta para o caderno.

---

## F8.3 — Ficha do hóspede e transcrição para o PMS

**Objetivo:** transportar a ficha para o sistema do hotel sem redigitar.

**Descrição para o `/specify`:**
> A recepção abre a ficha de um hóspede, completa no balcão o que faltou, e copia os dados para
> o sistema de gestão do hotel. Fichas parciais são identificadas com os campos ausentes. O
> consentimento para contato futuro é visível e revogável.

**Critérios de aceite:**

- Ficha completa e ficha parcial são distinguíveis, com os campos ausentes nomeados
- Campos editáveis no balcão gravam sem nova rodada de mensagens
- Existe forma de copiar a ficha para colagem externa
- Consentimento aparece com data e pode ser revogado
- Perfil operacional recebe recusa

**Depende de:** F8.2, F1.3.

> Testar a colagem no PMS real continua pendente. A fatia entrega uma variação; qual formato
> funciona é achado de campo.

---

## F8.4 — Chamados, pedidos e a tela da equipe

**Objetivo:** o Alert Center funcionando, e a equipe resolvendo pelo celular.

**Descrição para o `/specify`:**
> A recepção acompanha chamados e pedidos abertos, com o tempo decorrido visível, e distingue
> reclamação, serviço operacional e consumo. A equipe operacional acessa pelo celular uma lista
> apenas dos chamados atribuídos a ela, com um único botão para marcar como resolvido, sem
> qualquer dado cadastral do hóspede na tela.

**Critérios de aceite:**

- Chamados abertos aparecem com tempo decorrido e natureza distinta
- Resolver confirma ao hóspede automaticamente
- A tela da equipe não exibe nome, telefone nem documento de hóspede
- A tela da equipe é utilizável em tela de celular, sem autenticar a cada chamado
- Perfil operacional recebe recusa ao tentar abrir ficha por qualquer caminho

**Depende de:** F8.1, F3.5, F3.6.

---

## F8.5 — Consumos a lançar e saída do hóspede

**Objetivo:** a fila com consequência financeira, e o checkout.

**Descrição para o `/specify`:**
> Os consumos faturáveis pendentes de lançamento aparecem em fila destacada, com o valor
> praticado e há quanto tempo esperam. A recepção marca cada um como lançado ou dispensado. Na
> saída, ela confirma o checkout e vê a lista de pedidos feitos pelo chat daquela estadia,
> avisada se ainda houver consumo pendente.

**Critérios de aceite:**

- A fila de pendentes mostra valor e tempo de espera, e o total pendente
- Marcar como lançado registra quem lançou e quando
- Consumo pendente da estadia é avisado antes da confirmação da saída
- A lista nunca é chamada de "extrato" nem de "conta", em nenhum ponto da interface
- Pedido de serviço sem cobrança não aparece na lista da saída

**Depende de:** F8.2, F3.7, F4.1, F4.2.

---

## F8.6 — Catálogo, itens vendáveis e recado de boas-vindas

**Objetivo:** o hotel mantém sozinho o que o sistema pode afirmar e cobrar.

**Descrição para o `/specify`:**
> A recepção mantém o catálogo por categoria, cadastra e ajusta os itens vendáveis com seus
> preços, e edita os três textos de entrada do recado de boas-vindas. Itens são desativados em
> vez de apagados. Valor recusado pela regra de formato é avisado no momento de salvar.

**Critérios de aceite:**

- Itens do catálogo são criados, editados e desativados por categoria
- Item vendável tem preço editável em campo próprio, sem reescrever texto
- Item desativado deixa de ser considerado pelo atendimento automático
- Texto de boas-vindas com quebra de linha ou espaços múltiplos é recusado ao salvar, com aviso claro
- Gestão lê e não altera; perfil operacional recebe recusa

**Depende de:** F8.1, F2.1, F2.2.

---

## F8.7 — Painel da gestão, mercado e administração

**Objetivo:** a visão de quem responde pelo hotel, sem ver dado pessoal.

**Descrição para o `/specify`:**
> A gestão vê indicadores agregados da operação, o comparativo de mercado com os concorrentes
> cadastrados, a relação de usuários com criação e desativação, e o registro das execuções de
> expurgo por retenção. Nenhum dado cadastral de hóspede aparece em nenhuma dessas telas.

**Critérios de aceite:**

- Os indicadores são números agregados; nenhuma lista nominal é servida à gestão
- Criar usuário exige perfil e senha com o mínimo exigido, e desativar não apaga
- Concorrente com coleta falhada aparece marcado, e não como dado atual
- O registro de expurgo mostra data, tipo e quantidade de registros
- Revogar sessão não aparece para a gestão — é da recepção

**Depende de:** F8.1, F5.3, F6.1.

---

## Ordem recomendada da Fase 8

```
F8.1 → F8.2 → F8.3 → F8.4 → F8.5 → F8.6 → F8.7
```

**Se o prazo apertar**, o mínimo apresentável é **F8.1 + F8.2 + F8.4**: entrar, operar o turno e
resolver chamado. As demais telas continuam acessíveis pelo `/docs` durante a demonstração.
