# OmniStay — Artefato 1: Mapa de Processos

**Projeto:** OmniStay — Hub Conversacional para Hotelaria
**Aluno:** Thiago Alves Feitosa — Sistemas de Informação (FIAP)
**Versão:** 1.1 — 06/08/2026
**Status:** validado

> **Histórico de alterações — v1.1 (06/08/2026).** Três correções decorrentes da elaboração
> do Artefato 2: o passo 4.4 deixa de enviar oferta de retorno e passa a coletar
> consentimento; o "extrato de gastos" é renomeado para "pedidos feitos pelo chat" (§6.1);
> e a retirada da oferta de retorno é registrada com justificativa de custo e de base legal
> (§6.2).

---

## 1. Premissa arquitetural

O OmniStay **não se integra ao PMS do hotel**. Ele opera como sistema paralelo, e o
recepcionista é a ponte humana entre os dois. Essa é a decisão de projeto que governa
todo o restante da documentação.

A consequência direta: **a transição entre fases do processo não é disparada por
integração, e sim por uma ação manual registrada no painel**. Isso é uma limitação
assumida conscientemente, e ela tem contrapartida comercial — o hotel adota o OmniStay
sem trocar nem reconfigurar o sistema que já usa, o que reduz o atrito de venda a
praticamente zero.

## 2. Atores

| Ator | Papel no processo |
| --- | --- |
| **Hóspede** | Interage exclusivamente por WhatsApp. Nunca acessa o painel. |
| **Recepção** | Opera o painel web. Dispara os eventos de fase e transcreve dados para o PMS. |
| **Staff operacional** | Recebe chamados pelo Alert Center (painel web, acessível pelo navegador do celular). |
| **OmniStay** | Sistema. Executa disparos automáticos, classificação por IA e coleta de inteligência de mercado. |

> **Decisão de escopo (06/08/2026):** o "App da Equipe" previsto no Business Model Canvas
> original foi **cortado**. O Alert Center do painel web assume a função. Justificativa:
> um aplicativo nativo é um segundo produto, e o painel responsivo entrega o mesmo valor
> operacional dentro do escopo do MVP.

## 3. Processo P1 — Pré-chegada

**Objetivo:** eliminar a ficha de papel e a espera no balcão, antecipando o cadastro do
hóspede no PMS antes da chegada física.

| # | Ator | Ação | Saída |
| --- | --- | --- | --- |
| 1.1 | Recepção | Recebe a reserva (WhatsApp, Booking ou e-mail) e cadastra hóspede + telefone + datas no OmniStay | Evento `reserva_cadastrada` |
| 1.2 | OmniStay | Dispara template de coleta de dados | Mensagem *utility* enviada |
| 1.3 | Hóspede | Responde com os dados cadastrais | Ficha preenchida, status `aguardando_transcricao` |
| 1.4 | OmniStay | Valida formato e consolida a ficha no painel | Ficha disponível para a recepção |
| 1.5 | Recepção | Transcreve os dados no PMS | Status `cadastro_concluido` |

### 3.1 Campos da ficha de cadastro

Nome completo · Profissão · Data de nascimento · Tipo de documento · Número do documento ·
Endereço · CEP · Cidade · Telefone

**Decisões sobre esses campos (06/08/2026):**

- **Idade não é persistida.** É valor derivado de `data_nascimento` e sua materialização em
  banco introduziria inconsistência já no dia seguinte ao aniversário. Calculada em exibição.
- **Somente campos digitados. Foto do documento não é aceita.** Justificativas: minimização
  de dados prevista na LGPD, uma vez que a imagem de um documento carrega mais informação do
  que a finalidade exige; o recepcionista transcreve para o PMS de qualquer forma, e ler uma
  imagem é mais lento que copiar texto; a conferência física do documento já ocorre no balcão
  durante o check-in; e evita-se um pipeline de download, cifragem e expurgo de mídia no MVP.
- **O documento é modelado em dois campos** — `tipo_documento` e `numero_documento` — de modo
  que RG, CPF e passaporte caibam no mesmo modelo sem quebrar o cadastro de estrangeiros.
- **Coleta em mensagem única com lista numerada.** O formulário nativo (WhatsApp Flows) fica
  para a Fase 4, justificado pela mudança de cobrança de 01/10/2026, que passa a tarifar cada
  resposta dentro da janela e torna a redução de mensagens por conversa economicamente
  relevante. Para a apresentação, a interface do formulário é simulada na tela Simulator.
- Este conjunto de campos é compatível com o que a legislação brasileira de turismo exige
  do meio de hospedagem (Ficha Nacional de Registro de Hóspedes). Vale confirmar a lista
  oficial vigente antes de fechar a modelagem.

### 3.2 Fluxo de exceção — hóspede não responde

O cadastro é **obrigatório antes do check-in**. Se o hóspede não responder, o processo
degrada com segurança para o fluxo tradicional: ficha preenchida no balcão, na chegada.

Regra de reenvio, calibrada para **não ser intrusiva**:

1. Se não houver resposta, o sistema envia **um único reenvio**, explicando que o cadastro
   antecipado é opcional e que, sem ele, o preenchimento será feito na recepção.
2. Se ainda assim não houver resposta, o sistema **para de insistir** e sinaliza no painel
   que aquela reserva chegará sem cadastro prévio.
3. A recepção vê essa sinalização e se prepara para o atendimento tradicional.

**Parâmetros a definir com o hotel:** intervalo até o reenvio e janela de corte antes do
check-in. Devem ser configuráveis por propriedade, não fixos no código.

## 4. Processo P2 — Chegada

| # | Ator | Ação | Saída |
| --- | --- | --- | --- |
| 2.1 | Hóspede | Chega ao hotel | — |
| 2.2 | Recepção | Confirma o check-in no painel | Evento `checkin_confirmado` |
| 2.3 | OmniStay | Dispara o recado curto de boas-vindas: chegada, informações de entrada da propriedade (café, wi-fi, checkout) e convite a perguntar | Mensagem enviada |

A partir de 2.3 a conversa entra em regime ativo: qualquer mensagem do hóspede abre a
janela de atendimento, dentro da qual as respostas do sistema não têm custo de API.

> **Correção (17/08/2026), na execução da F2.2.** O passo 2.3 dizia "programação, cardápio,
> serviços, horários" no próprio recado. Variável de template não aceita quebra de linha,
> tabulação nem mais de quatro espaços seguidos, então despejar o catálogo ali não é
> enviável. O recado ficou curto e **termina convidando o hóspede a perguntar** — é ele que
> abre a janela de 24h, e é dentro dela que o catálogo responde em texto livre e sem custo
> (P3.3a). O conteúdo não foi perdido: mudou de momento.

## 5. Processo P3 — Estadia

| # | Ator | Ação | Saída |
| --- | --- | --- | --- |
| 3.1 | Hóspede | Envia mensagem | Mensagem recebida via webhook |
| 3.2 | OmniStay | Classifica intenção, sentimento e urgência | Registro classificado |
| 3.3a | OmniStay | **Ramo automático** — responde dúvidas e registra pedidos | Resposta enviada |
| 3.3b | OmniStay | **Ramo humano** — abre chamado e notifica o Alert Center | Chamado criado |
| 3.4 | Staff | Resolve o chamado e marca como resolvido | Evento `chamado_resolvido` |
| 3.5 | OmniStay | Confirma a resolução ao hóspede | Mensagem enviada |

### 5.1 Taxonomia de intenções (versão inicial)

`duvida_geral` · `pedido_de_servico` · `reclamacao_tecnica` · `upsell` ·
`solicitacao_de_checkout` · `fora_de_escopo`

A classificação `reclamacao_tecnica` com sentimento negativo é o gatilho de escalonamento
para o Alert Center. No caso específico de falha em equipamento, o fluxo pergunta ao
hóspede o **horário de preferência para o reparo** antes de fechar o chamado.

### 5.2 Gatilho temporal — micro-pesquisa de pulso

No segundo dia de estadia, o sistema envia **uma única pergunta** sobre a experiência.
O objetivo é detectar insatisfação enquanto ainda há tempo de corrigir, em vez de
descobrir no checkout. Resposta negativa alimenta o Alert Center.

## 6. Processo P4 — Checkout

| # | Ator | Ação | Saída |
| --- | --- | --- | --- |
| 4.1 | Recepção | Confirma o checkout no painel | Evento `checkout_realizado` |
| 4.2 | OmniStay | Envia pesquisa de avaliação | Mensagem enviada |
| 4.3 | Hóspede | Responde a avaliação | Nota e comentário registrados |
| 4.4 | OmniStay | Registra nota e comentário; a última pergunta da pesquisa coleta o aceite para receber comunicações futuras | Avaliação registrada · consentimento datado, ou recusa |

### 6.1 Pedidos feitos pelo chat — escopo reduzido

> **Decisão de escopo (06/08/2026):** a tela e a mensagem mostram **apenas o que foi
> transacionado dentro do OmniStay** (upsells e pedidos feitos pelo chat). Consumo lançado
> diretamente no PMS — frigobar, restaurante, lavanderia — está fora do alcance do sistema.
> A consolidação completa fica registrada como evolução futura, condicionada à integração
> com o PMS.

> **Decisão de nomenclatura (06/08/2026):** essa lista **não é chamada de "extrato" nem de
> "conta"**, em nenhum ponto da interface ou das mensagens. O rótulo adotado é **"pedidos
> feitos pelo chat"**. Justificativa: "extrato" induz o hóspede a compará-lo com a fatura
> do PMS, que inclui consumos que o OmniStay não enxerga, e a divergência vira contestação
> no balcão. É correção de uma palavra que elimina uma classe inteira de atrito.

### 6.2 Oferta de retorno — retirada do MVP

> **Decisão de escopo (06/08/2026):** a **oferta de retorno pós-estadia sai do MVP**. Em
> seu lugar, a pesquisa de avaliação encerra com uma pergunta de aceite para comunicações
> futuras, cuja resposta afirmativa é registrada como consentimento com data e hora.
>
> Justificativas, nas duas dimensões:
>
> - **Custo.** Uma mensagem enviada semanas após o checkout não se refere a nenhuma
>   transação em curso, e portanto é classificada pela Meta como categoria **Marketing** —
>   a mais cara das quatro. A projeção de custo deste projeto (R$ 100 a R$ 150/mês) foi
>   calculada considerando apenas mensagens *utility*, e não comportava esse item.
> - **Base legal (LGPD).** A execução do contrato de hospedagem, que ampara as mensagens
>   das fases P1 a P4, **encerra-se no checkout**. Comunicação promocional posterior exige
>   consentimento específico e revogável, nos termos do art. 7º, I.
>
> A funcionalidade permanece no roadmap. Com o consentimento coletado desde o MVP, a base
> de opt-in já estará formada quando ela for implementada.

**Alerta correlato:** se o pacote de boas-vindas do P2 incluir oferta comercial — desconto
de spa, promoção de restaurante —, a Meta pode reclassificar aquele template como Marketing
por conta própria, alterando o custo sem aviso. **Boas-vindas e venda devem ser templates
separados.**

## 7. Processo P5 — Inteligência de mercado

Roda por agendamento, **em paralelo e sem tocar o fluxo do hóspede**.

| # | Ator | Ação |
| --- | --- | --- |
| 5.1 | OmniStay | Agendador dispara a coleta periódica |
| 5.2 | OmniStay | Coleta preços e avaliações dos concorrentes cadastrados |
| 5.3 | OmniStay | Consolida e apresenta no painel Market Intel |

**Pendência:** definir a lista de concorrentes por propriedade e a periodicidade da coleta.
Registrar também os limites éticos e de termos de uso das fontes consultadas — ponto que
costuma ser cobrado em banca.

## 8. Catálogo de eventos

| Evento | Origem | Tipo | Dispara |
| --- | --- | --- | --- |
| `reserva_cadastrada` | Recepção | Manual | Template de coleta de dados |
| `cadastro_recebido` | Hóspede | Reativo | Consolidação da ficha no painel |
| `cadastro_nao_respondido` | Sistema | Temporal | Reenvio único, depois sinalização no painel |
| `checkin_confirmado` | Recepção | Manual | Pacote de boas-vindas |
| `mensagem_recebida` | Hóspede | Reativo | Classificação por IA |
| `chamado_aberto` | Sistema | Reativo | Notificação no Alert Center |
| `chamado_resolvido` | Staff | Manual | Confirmação ao hóspede |
| `pulso_segundo_dia` | Sistema | Temporal | Micro-pesquisa de satisfação |
| `checkout_realizado` | Recepção | Manual | Pesquisa de avaliação |
| `coleta_mercado` | Sistema | Agendado | Atualização do Market Intel |

## 9. Decisões técnicas registradas

| Decisão | Escolha | Justificativa resumida |
| --- | --- | --- |
| Canal | WhatsApp Cloud API oficial (número de teste no MVP) | Sem taxa de licença; número de teste cobre até 5 destinatários, suficiente para validação acadêmica |
| Backend | Python + FastAPI | Web scraping e IA são os módulos mais pesados; stack única reduz custo de manutenção para um desenvolvedor solo |
| Frontend | React + TypeScript | Já existente no protótipo |
| Banco | PostgreSQL | Domínio fortemente relacional; `JSONB` absorve payloads de webhook e saídas de NLP sem migração |
| IA | Camada gratuita da classe Flash, atrás de interface `LLMProvider` | Custo zero no MVP; provedor trocável por configuração |

**Alerta de custo a registrar no BMC:** mensagens de serviço e mensagens *utility* dentro
da janela de atendimento passam a ser cobradas a partir de 01/10/2026, o que incide sobre
a Fase 4 do cronograma.

## 10. Pendências abertas

- [x] ~~Aceitar foto do documento de identidade?~~ Resolvido: somente campos digitados
- [x] ~~Oferta de retorno no MVP?~~ Resolvido: retirada, substituída por opt-in na pesquisa
- [ ] Intervalo do reenvio e janela de corte na pré-chegada
- [ ] Política de retenção e exclusão dos dados cadastrais (LGPD)
- [ ] Lista de concorrentes e periodicidade da coleta do Market Intel
- [ ] Material do MVP de usuário, ainda a ser enviado

---

## Próximos artefatos

| # | Artefato | Depende de |
| --- | --- | --- |
| 2 | Jornada do usuário (hóspede e recepcionista) | Este documento |
| 3 | Fluxo de dados (DFD) e catálogo de eventos detalhado | Artefatos 1 e 2 |
| 4 | Modelagem de dados (DER + dicionário) | Artefato 3 + decisão sobre o documento de identidade |
| 5 | Arquitetura e stack | Artefato 4 |
| 6 | Business Model Canvas atualizado | Todos os anteriores |
