<!--
Sync Impact Report
- Version change: template placeholders → 1.0.0
- Modified principles: none (initial ratification)
- Added sections:
  - Artigos I–XV (princípios inegociáveis do OmniStay)
  - Como usar esta constituição
  - Governance
- Removed sections: generic template placeholder principles (5 slots)
- Follow-up TODOs: none
-->

# OmniStay Constitution

Princípios inegociáveis do projeto. São o filtro pelo qual toda especificação, plano e
implementação passa. Quando uma proposta contraria um artigo desta constituição, a proposta
está errada — não o artigo.

Cada artigo deriva de uma decisão registrada nos artefatos de documentação, e traz a
referência. Nenhum artigo foi inventado aqui.

---

## Core Principles

### Artigo I — O sistema não se integra ao PMS

O OmniStay opera em paralelo ao sistema de gestão do hotel. O recepcionista é a ponte humana
entre os dois.

**Consequência que toda implementação deve respeitar:** as transições entre fases do processo
são disparadas por cliques de funcionários no painel, jamais por integração. Se uma
especificação pressupõe que o sistema "sabe" algo que só existe no PMS, essa especificação
está errada.

**Nunca proponha:** leitura de banco do PMS, importação de arquivo do PMS, sincronização de
reservas, débito automático em conta do hóspede.

*Origem: Artefato 1 §1, ADR-001.*

---

### Artigo II — Na dúvida, um humano vê

Falha de classificação, texto não reconhecido, pergunta fora do catálogo cadastrado ou
indisponibilidade do provedor de IA terminam **sempre** em fila humana. Nunca em resposta
automática arriscada, nunca em descarte silencioso.

A resposta automática só é permitida quando a informação está no catálogo da propriedade.
Conhecimento geral do modelo não é fonte válida para falar em nome de um hotel.

*Origem: Artefato 2 F3a, Artefato 3 §6.11, Artefato 5 §8.3 e §10.3.*

---

### Artigo III — Gravar antes de enviar

Nenhuma falha de envio de mensagem pode causar perda de dado. Persistência e comunicação são
operações separadas, nessa ordem.

O webhook grava e responde imediatamente. Todo trabalho que dependa de rede externa ou de IA
acontece depois, a partir da fila.

*Origem: Artefato 3 §6.11, Artefato 5 §7 e §8.*

---

### Artigo IV — A fila é a fonte da verdade; a notificação é conveniência

Todo alerta perdido precisa ser recuperável pela leitura do painel. Nenhuma funcionalidade
pode depender de uma notificação ter chegado.

*Origem: Artefato 3 §6.11.*

---

### Artigo V — A ausência de ação humana precisa ser visível

Quatro travessias de fronteira dependem de uma pessoa: entrada dos dados da reserva,
devolução da ficha ao PMS, registro da chegada e da partida, e lançamento do consumo
faturável. Três falham em silêncio, e uma tem consequência financeira.

Toda funcionalidade que dependa de ação humana precisa expor a pendência em fila visível no
painel. **Não elimina a dependência — torna a omissão perceptível**, que é o máximo
alcançável sem integração.

*Origem: Artefato 2 §9.1, Artefato 3 §7, Artefato 5 §15.*

---

### Artigo VI — O hóspede nunca fica esperando em silêncio

Toda solicitação ou reclamação recebe confirmação de recebimento **antes** de qualquer
tramitação. A confirmação vem primeiro; o processamento vem depois.

*Origem: Artefato 2 F3b, Artefato 3 §5.2.*

---

### Artigo VII — Não ser intrusivo é requisito, não preferência

O sistema envia **um único reenvio** quando o hóspede não responde à coleta de dados. Depois
disso, para de insistir e sinaliza no painel.

O pulso do segundo dia é suprimido quando há chamado em aberto ou quando restam menos de 24
horas de estadia.

Nenhuma mensagem proativa nova entra no produto sem justificativa explícita de necessidade.

*Origem: Artefato 1 §3.2, Artefato 2 F3c.*

---

### Artigo VIII — Minimização de dados pessoais

Somente campos digitados. **Foto de documento não é aceita**, em nenhuma hipótese.

A idade não é persistida — é derivada da data de nascimento em exibição.

Conteúdo de mensagem **nunca** aparece em log. Logs registram identificadores, classificações
e códigos de erro. Nunca o texto.

Prazos de retenção: ficha cadastral por 5 anos após o checkout, conversas por 12 meses com
anonimização, expurgo automático e auditado.

*Origem: Artefato 1 §3.1, Artefato 4 §6.1, Artefato 5 §9.1 e §11.4.*

---

### Artigo IX — Garantias moram no banco quando podem morar no banco

Idempotência é restrição `UNIQUE`, não verificação em código. Transição de estado inválida é
rejeitada por trigger, não apenas pela camada de aplicação. Domínio de valor é `CHECK`.

Regra na aplicação protege o caminho normal; regra no banco protege contra script de
correção, importação e acesso direto — que é quando o histórico costuma ser corrompido.

*Origem: Artefato 4 §4 e §7.1, ADR-004.*

---

### Artigo X — Três interfaces são trocáveis, e o domínio não as conhece

`LLMProvider`, `CatalogoRepository` e `MensageriaGateway` são portas. O domínio depende das
interfaces, nunca das implementações.

Isso não é preferência estética. É o que permite o simulador da apresentação ser um
adaptador em vez de um caminho alternativo no código, e o que torna os testes determinísticos
sem rede.

*Origem: Artefato 5 §5.1, ADR-006.*

---

### Artigo XI — Complexidade exige problema correspondente

Cada peça móvel adicionada ao projeto compete com o tempo de implementar funcionalidade. Um
desenvolvedor, prazo fixo, custo zero.

**Não introduza** serviço novo, biblioteca nova ou camada de abstração sem um problema
concreto e presente que a justifique. Antecipação a problema hipotético é o modo mais comum
de um projeto acadêmico não ser entregue.

*Origem: Artefato 5 §1 e §2, ADR-002, ADR-003, ADR-005.*

---

### Artigo XII — Teste primeiro, sem exceção

Nenhuma linha de código de produção é escrita antes de existir um teste que falhe por sua
ausência.

O ciclo é: escrever o teste, ver falhar pelo motivo certo, implementar o mínimo para passar,
refatorar com o teste verde.

**Um teste que passa na primeira execução é suspeito** — ou ele não testa o que diz testar,
ou a funcionalidade já existia.

*Origem: decisão de método do projeto; casos obrigatórios em Artefato 5 §13.2.*

---

### Artigo XIII — Parâmetro operacional não é constante de código

Intervalo de reenvio, janela de corte, periodicidade de coleta, horas mínimas para o pulso —
todos vivem em `parametro_hotel`, configuráveis por propriedade.

Um número mágico no código é defeito, não atalho.

*Origem: Artefato 4 §6.2, Artefato 5 §9.*

---

### Artigo XIV — Multi-tenant desde a primeira linha

`id_hotel` existe nas tabelas de domínio e é considerado em toda consulta, mesmo com uma
única propriedade cadastrada.

Introduzir particionamento depois é migração que toca toda tabela e toda consulta,
exatamente quando houver cliente em produção.

*Origem: Artefato 4 §2.1, ADR-007.*

---

### Artigo XV — Honestidade sobre o que o sistema não faz

A documentação registra explicitamente o que a arquitetura não entrega: não há alta
disponibilidade, não há garantia de ordem entre mensagens, não há auditoria genérica de
alteração, e a dependência do clique humano permanece.

**Nenhuma especificação, mensagem de interface ou material de apresentação pode prometer o
contrário.** Superprometer é o defeito mais caro em trabalho que será defendido em banca.

*Origem: Artefato 5 §15.2, Artefato 6 §10.3.*

---

## Como usar esta constituição

**No Spec Kit:** carregue com `/speckit.constitution`. Ela passa a ser considerada em todo
`/specify`, `/plan` e `/implement`.

**Quando o agente propuser algo que contraria um artigo:** cite o artigo. Não argumente do
zero — a decisão já foi tomada e justificada, e reabri-la custa coerência com cinco artefatos.

**Para emendar:** só com decisão registrada. Uma constituição que muda por conveniência de
implementação não é constituição, é sugestão.

## Governance

Esta constituição supersede todas as outras práticas de desenvolvimento do OmniStay. Toda
especificação, plano e implementação deve ser verificada contra os artigos acima.

Emendas exigem decisão registrada nos artefatos de documentação (ADR ou seção equivalente),
com atualização de versão e data de emenda neste arquivo. Mudanças por conveniência de
implementação não são válidas.

**Version**: 1.0.0 | **Ratified**: 2026-08-10 | **Last Amended**: 2026-08-10
