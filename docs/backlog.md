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
