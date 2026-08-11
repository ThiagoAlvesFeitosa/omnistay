# OmniStay — Artefato 2: Jornada do Usuário

**Projeto:** OmniStay — Hub Conversacional para Hotelaria
**Aluno:** Thiago Alves Feitosa — Sistemas de Informação (FIAP)
**Versão:** 1.1 — 06/08/2026
**Status:** validado

> **Histórico de alterações — v1.1 (06/08/2026).** Retirada da oferta de retorno do MVP,
> com o consentimento passando a ser coletado na pesquisa de checkout (F5 e §9.3a); auxílios
> de transcrição da R4 movidos para evolução futura, condicionados a testar colagem no PMS
> real. Ambas as mudanças foram propagadas para o Artefato 1, que passou à v1.1.

---

## 1. Objetivo e recorte

Este artefato descreve a experiência ponta a ponta dos atores identificados no Artefato 1,
organizada em camadas, e a contrasta com o cenário atual do hotel sem o sistema.

Duas trilhas recebem tratamento completo — **hóspede** e **recepcionista** — porque são as
únicas que atravessam todos os cinco processos. **Staff operacional** e **gestor** recebem
seções reduzidas, suficientes para demonstrar que o Alert Center e o Market Intel têm
consumidor definido.

O recepcionista não é coadjuvante. Como o OmniStay não se integra ao PMS, **é o clique dele
que move o processo de uma fase para a outra**. Se a jornada dele falhar, o sistema inteiro
para — e essa dependência é analisada explicitamente na seção 9.

### 1.1 Como ler as camadas

Cada fase é descrita por seis camadas:

| Camada | O que registra |
| --- | --- |
| **Ação** | O que o ator faz, em termos observáveis |
| **Canal** | Onde a ação acontece (WhatsApp, painel web, presencial, PMS) |
| **O que o OmniStay faz** | Comportamento do sistema, incluindo disparos automáticos |
| **Dado gerado** | Informação que nasce ou muda de estado nesta fase — insumo direto do Artefato 3 |
| **Estado emocional** | Como o ator se sente, e por quê |
| **Risco / oportunidade** | O que pode dar errado e onde há ganho a capturar |

A camada **Dado gerado** existe para que o Fluxo de Dados (Artefato 3) não precise ser
derivado do zero: cada linha dessa camada vira um fluxo ou um depósito no DFD.

## 2. Personas

> **Nota de método:** as personas são instrumentos de projeto, não pesquisa de campo. Foram
> construídas a partir do perfil de propriedade adotado como referência — hotel independente
> de 40 quartos, ~500 hóspedes/mês, mesma base usada na projeção de custo do Artefato 1.

### 2.1 Marina Duarte — a hóspede

34 anos, gerente de contas em São Paulo. Viaja a trabalho duas vezes por mês, quase sempre
sozinha, estadias de duas a três noites. Reserva pela Booking porque é rápido, não porque é
fiel a alguma marca.

Chega de carro no fim da tarde, cansada, e o que ela quer do check-in é que ele acabe.
**Não instala aplicativo de hotel** — usa a propriedade por poucos dias e não vê motivo para
ocupar espaço no celular. Resolve tudo por WhatsApp: trabalho, família, pedido de comida.
Se precisar de algo no quarto, prefere mandar mensagem a ligar para a recepção, porque
ligação exige atenção sincronizada e ela costuma estar em call.

**O que ela valoriza:** não repetir informação que já deu, não esperar em pé, e ter
confirmação de que o pedido foi recebido.
**O que a irrita:** preencher ficha de papel com dados que já estão na reserva, e pedir algo
sem saber se alguém viu.

### 2.2 Cléber Rocha — o recepcionista

27 anos, três anos de casa, turno da tarde. Domina o PMS da propriedade e digita rápido —
o sistema é feio e antigo, mas ele já decorou a ordem de tabulação dos campos.

Seu turno tem um pico claro entre 14h e 18h: check-ins concentrados, telefone tocando,
e-mail da Booking chegando, hóspede pedindo toalha extra no balcão. Nesse intervalo ele faz
três coisas ao mesmo tempo e a fila é visível.

**É cético com sistema novo.** O último que a gerência contratou prometia facilitar e virou
mais uma tela para preencher, com os mesmos dados que ele já digitava no PMS. Ele abandonou
o uso em duas semanas e ninguém cobrou.

**O que ele valoriza:** menos digitação no momento de pico, e saber de manhã o que vai
acontecer à tarde.
**O que o irrita:** sistema que exige atenção constante, e retrabalho de digitar duas vezes.

> **Implicação de projeto:** o Cléber é o risco de adoção do OmniStay, não a Marina. Um
> hóspede que ignora a mensagem apenas degrada para o fluxo tradicional; um recepcionista
> que abandona o painel **paralisa o sistema**, porque as transições de fase dependem dele.
> A trilha B foi desenhada para caber na rotina dele, não para adicionar uma etapa.

---

## 3. Trilha A — Jornada do hóspede

Cobre os processos P1 a P4 do Artefato 1, mais uma fase anterior (F0) que está fora do
sistema mas produz o dado de entrada, e uma posterior (F5) que hoje é uma lacuna.

### F0 — Reserva *(fora do OmniStay)*

| Camada | Conteúdo |
| --- | --- |
| **Ação** | Marina reserva pela Booking, ou por WhatsApp direto com o hotel |
| **Canal** | OTA, e-mail ou WhatsApp do hotel |
| **O que o OmniStay faz** | Nada. O sistema ainda não conhece esta reserva |
| **Dado gerado** | Nome, telefone e datas — existem no PMS ou na caixa de entrada, não no OmniStay |
| **Estado emocional** | Neutro. Decisão comercial já tomada |
| **Risco / oportunidade** | **Risco de origem:** o telefone é digitado por uma pessoa em algum ponto dessa cadeia. Um dígito errado aqui contamina todo o processo — e o erro só aparece quando a mensagem não é entregue, ou pior, quando é entregue a um terceiro |

**Por que F0 está no documento:** é a fronteira do sistema. O OmniStay começa a existir
quando alguém transcreve esse dado para o painel, e não antes. Marcar isso evita que o
Artefato 3 desenhe um fluxo de entrada que não existe.

### F1 — Pré-chegada *(P1)*

| Camada | Conteúdo |
| --- | --- |
| **Ação** | Marina recebe uma mensagem do hotel e responde os dados cadastrais em uma única mensagem, seguindo a lista numerada |
| **Canal** | WhatsApp |
| **O que o OmniStay faz** | Dispara o template *utility* de coleta; recebe a resposta via webhook; interpreta e valida o formato; consolida a ficha no painel com status `aguardando_transcricao` |
| **Dado gerado** | Ficha de cadastro (nome, profissão, data de nascimento, tipo e número do documento, endereço, CEP, cidade, telefone) · status da reserva · registro de consentimento e horário |
| **Estado emocional** | **Surpresa favorável.** É um pedido curto, no aplicativo que ela já usa, e ela entende que serve para não parar na recepção depois. Se a mensagem for longa ou parecer formulário burocrático, a disposição cai |
| **Risco / oportunidade** | **Oportunidade:** é o primeiro contato direto do hotel com a hóspede — define o tom da estadia. **Riscos:** resposta fora do formato esperado; resposta parcial (ela responde 5 dos 9 campos); número errado entregando dados a terceiro; e a percepção de intrusão se o reenvio for insistente |

**Regra de reenvio (herdada do Artefato 1):** um único reenvio, explicando que o cadastro
antecipado é opcional. Persistindo o silêncio, o sistema para de insistir e sinaliza a
reserva no painel. Não ser intrusivo é requisito explícito do projeto.

**Tratamento da resposta parcial** — lacuna que este artefato fecha:

> **Decisão de escopo (06/08/2026):** resposta parcial **não** dispara nova cobrança de
> campos pelo WhatsApp. A ficha é consolidada com o que veio, marcada como `parcial` no
> painel, e os campos faltantes são completados no balcão. Justificativa: cada rodada de
> ida e volta consome mensagens, aumenta a percepção de burocracia e, a partir de
> 01/10/2026, gera custo por resposta. Pedir três campos no balcão é mais rápido para
> ambos do que negociar por chat.

### F2 — Chegada *(P2)*

| Camada | Conteúdo |
| --- | --- |
| **Ação** | Marina chega ao balcão, apresenta o documento físico, confere e assina o que for necessário, recebe a chave |
| **Canal** | Presencial + WhatsApp (logo após) |
| **O que o OmniStay faz** | Ao receber `checkin_confirmado`, dispara o pacote de boas-vindas: programação, cardápio, serviços e horários. A partir daqui a conversa está em regime ativo |
| **Dado gerado** | Timestamp de check-in · abertura da janela de atendimento de 24h · vínculo hóspede↔estadia ativo |
| **Estado emocional** | **Alívio se a ficha já estava pronta** — o balcão vira conferência de documento, não preenchimento. Se ela não respondeu na F1, a experiência é a tradicional, e o sistema não piorou nada |
| **Risco / oportunidade** | **Risco central:** se o Cléber esquecer de confirmar o check-in no painel, nada é disparado e o sistema continua achando que ela não chegou. **Oportunidade:** o pacote de boas-vindas chega quando ela está subindo para o quarto — momento de atenção alta e disposição para ler |

**Tratamento do check-in não confirmado** — ver a mitigação proposta na seção 9.1.

### F3 — Estadia *(P3)*

A estadia não é uma fase homogênea. Ela se divide em três situações com jornadas distintas.

#### F3a — Rotina: dúvida ou pedido simples

| Camada | Conteúdo |
| --- | --- |
| **Ação** | Marina pergunta o horário do café, ou pede uma toalha extra |
| **Canal** | WhatsApp |
| **O que o OmniStay faz** | Classifica como `duvida_geral` ou `pedido_de_servico`; responde direto pela IA ou registra o pedido e confirma o recebimento |
| **Dado gerado** | Mensagem · classificação (intenção, sentimento, urgência) · pedido registrado |
| **Estado emocional** | **Satisfação discreta.** Ela mandou mensagem em vez de descer ou ligar, e teve resposta. É o valor mais frequente do sistema, ainda que o menos vistoso |
| **Risco / oportunidade** | **Risco:** a IA responder com confiança algo errado sobre o hotel — horário de café inventado destrói a confiança de uma vez. **Mitigação:** a resposta automática só cobre fatos vindos da base cadastrada da propriedade; fora disso, cai para o ramo humano |

#### F3b — Atrito: reclamação técnica

| Camada | Conteúdo |
| --- | --- |
| **Ação** | Marina relata que o ar-condicionado não está gelando |
| **Canal** | WhatsApp |
| **O que o OmniStay faz** | Classifica como `reclamacao_tecnica` com sentimento negativo; **confirma imediatamente o recebimento**; pergunta o horário de preferência para o reparo; abre chamado no Alert Center |
| **Dado gerado** | Chamado (quarto, tipo, urgência, janela de preferência) · notificação ao staff |
| **Estado emocional** | **Frustração, e é aqui que o produto se prova ou se desmoraliza.** Um hóspede irritado que manda mensagem e não recebe nada por dez minutos conclui que o robô não serve — e liga para a recepção, que era exatamente o que se queria evitar |
| **Risco / oportunidade** | **A confirmação imediata é obrigatória, não opcional.** É a única coisa que segura a ansiedade enquanto o chamado tramita. **Oportunidade:** perguntar o horário de preferência transforma um incômodo em sensação de controle |

#### F3c — Pulso do segundo dia

| Camada | Conteúdo |
| --- | --- |
| **Ação** | Marina responde (ou ignora) uma pergunta única sobre a experiência |
| **Canal** | WhatsApp |
| **O que o OmniStay faz** | Dispara a micro-pesquisa; resposta negativa alimenta o Alert Center |
| **Dado gerado** | Resposta de pulso · eventual chamado de recuperação |
| **Estado emocional** | **Depende inteiramente do timing.** No momento certo, soa como cuidado. Logo após uma reclamação ainda aberta, soa como deboche |
| **Risco / oportunidade** | **Risco:** disparar o pulso com chamado em aberto, ou perto demais do checkout. Ver a regra de supressão abaixo |

> **Decisão de escopo (06/08/2026):** o pulso do segundo dia só dispara se **restarem ao
> menos 24 horas de estadia prevista** após o envio, e é **suprimido se houver chamado em
> aberto** para aquela estadia. Justificativa: o propósito declarado do pulso é detectar
> insatisfação enquanto ainda há tempo de corrigir. Sem tempo hábil, ele deixa de ser
> instrumento de recuperação e vira pesquisa antecipada — função que o checkout já cumpre.
> E perguntar "como está sendo sua estadia?" a quem está esperando o conserto do ar
> demonstra que o sistema não sabe o que a própria empresa já sabe.

### F4 — Checkout *(P4)*

| Camada | Conteúdo |
| --- | --- |
| **Ação** | Marina faz o checkout no balcão e recebe, em seguida, a pesquisa de avaliação |
| **Canal** | Presencial + WhatsApp |
| **O que o OmniStay faz** | Ao receber `checkout_realizado`, envia a pesquisa; registra nota e comentário; encerra com a pergunta de aceite para comunicações futuras |
| **Dado gerado** | Nota · comentário · lista de pedidos feitos pelo chat · consentimento datado, ou recusa · encerramento da estadia |
| **Estado emocional** | **Disponibilidade curta.** Ela responde se for uma pergunta, no celular, enquanto caminha para o carro. Um formulário de cinco itens não é respondido |
| **Risco / oportunidade** | **Oportunidade:** capturar a insatisfação em canal privado antes que ela vire avaliação pública. **Risco:** a lista de pedidos é parcial por decisão de escopo e não bate com a conta do PMS |

> **Decisão de nomenclatura (06/08/2026), aplicada ao Artefato 1 §6.1:** a lista de
> transações **não é chamada de "extrato" nem de "conta"**, em nenhum ponto da interface ou
> das mensagens. O rótulo é **"pedidos feitos pelo chat"**.
>
> Justificativa: o OmniStay só enxerga o que passou pelo próprio chat, e "extrato" induz o
> hóspede a comparar aquilo com a fatura do PMS, que inclui frigobar, restaurante e
> lavanderia. A divergência vira contestação no balcão — exatamente o atrito que o produto
> existe para remover. É correção de uma palavra que elimina uma classe inteira de problema.

> **Atenção ao desenho da pesquisa.** A camada emocional acima e a coleta de consentimento
> puxam em direções opostas: a pesquisa quer ser curta, e o opt-in acrescenta uma pergunta.
> A redação precisa caber nesse limite — nota, comentário opcional e aceite, nada além.
> Item registrado nas pendências.

### F5 — Pós-estadia

| Camada | Conteúdo |
| --- | --- |
| **Ação** | Marina não recebe nada. Se aceitou o opt-in na F4, entra na base de comunicação futura |
| **Canal** | — |
| **O que o OmniStay faz** | **Nada, no MVP.** Retém a ficha e o consentimento, conforme a política de retenção |
| **Dado gerado** | Histórico do hóspede em base · registro de consentimento (aceito ou recusado) com data |
| **Estado emocional** | **Neutro.** O silêncio pós-estadia é a experiência esperada. Mensagem promocional não solicitada seria, para ela, indistinguível de spam |
| **Risco / oportunidade** | O risco remanescente não é de mensagem, é de **retenção**: dados cadastrais completos guardados por prazo indefinido. Tratado em 9.3b |

> **Decisão de escopo (06/08/2026):** a **oferta de retorno sai do MVP**, e o passo 4.4 do
> Artefato 1 foi corrigido para refletir isso. Em substituição, a pesquisa da F4 encerra com
> uma pergunta de aceite, e a resposta é registrada como consentimento datado.
>
> Justificativa em duas frentes: **custo** — mensagem enviada semanas após o checkout não se
> refere a transação em curso e é classificada pela Meta como categoria *Marketing*, a mais
> cara, fora da projeção de R$ 100 a R$ 150/mês que considerou apenas *utility*; e **base
> legal** — a execução do contrato de hospedagem encerra-se no checkout, e comunicação
> promocional posterior exige consentimento específico e revogável (LGPD, art. 7º, I).
>
> A funcionalidade permanece no roadmap. Coletando o consentimento desde o MVP, a base de
> opt-in já estará formada quando ela for implementada.

**F5 deixa de ser uma fase ativa do sistema.** Permanece no documento porque delimita a
fronteira temporal do tratamento de dados — é aqui que a política de retenção passa a ser a
única regra em vigor.

---

## 4. Trilha B — Jornada do recepcionista

Esta trilha **não é organizada por hóspede, e sim por ritmo de turno**. É assim que o Cléber
experimenta o sistema: ele não acompanha uma reserva do início ao fim, ele atravessa um
turno no qual dezenas de reservas estão em estados diferentes ao mesmo tempo.

Desenhar a jornada dele por hóspede produziria um painel errado — um painel com uma tela por
reserva, quando o que ele precisa é de uma fila única priorizada pelo que é urgente agora.

### R1 — Início do turno

| Camada | Conteúdo |
| --- | --- |
| **Ação** | Cléber abre o painel e olha o dia: quem chega, quais fichas estão prontas, quais reservas chegarão sem cadastro, o que ficou pendente do turno anterior |
| **Canal** | Painel web |
| **O que o OmniStay faz** | Apresenta a fila do dia consolidada, ordenada por horário previsto de chegada, com o status de cadastro de cada reserva |
| **Dado gerado** | Nenhum. É leitura pura |
| **Estado emocional** | **Preparo.** Pela primeira vez ele sabe às 14h o que vai acontecer às 17h. É o momento que constrói a adesão dele ao sistema |
| **Risco / oportunidade** | **Oportunidade decisiva de adoção:** se essa tela entrega valor em cinco segundos de leitura, ele volta a ela. **Risco:** se exigir navegação por abas para montar o quadro, ele para de abrir |

**Requisito derivado:** uma tela inicial única, sem navegação, respondendo a três perguntas —
quem chega hoje, o que precisa de mim agora, e o que está pendente há tempo demais.

### R2 — Entrada de reserva

| Camada | Conteúdo |
| --- | --- |
| **Ação** | Chega uma reserva pela Booking, e-mail ou WhatsApp. Cléber lança no PMS, como sempre fez, e **cadastra nome, telefone e datas no OmniStay** |
| **Canal** | PMS + painel web |
| **O que o OmniStay faz** | Registra a reserva, emite `reserva_cadastrada` e dispara o template de coleta |
| **Dado gerado** | Reserva (nome, telefone, datas) · evento de disparo |
| **Estado emocional** | **É aqui que mora a objeção dele.** Esta etapa é digitação adicional, e ele vai sentir. Não adianta esconder |
| **Risco / oportunidade** | **Risco de abandono.** Se o cadastro no OmniStay for tão trabalhoso quanto o do PMS, o sistema morre por atrito na entrada, antes de provar qualquer valor |

**Mitigação de atrito, em três medidas concretas:**

1. **Três campos, não nove.** O cadastro de reserva no painel pede exclusivamente nome,
   telefone e datas. Todo o resto vem do hóspede.
2. **Validação do telefone na digitação** — formato e DDD conferidos no momento em que ele
   digita, não depois. Erro de telefone é a falha de origem identificada na F0.
3. **Status de entrega visível.** Se o WhatsApp retornar falha de entrega, a reserva é
   marcada no painel. Sem isso, o número errado só aparece quando o hóspede chega sem ficha.

### R3 — Acompanhamento das fichas

| Camada | Conteúdo |
| --- | --- |
| **Ação** | Ao longo do turno, Cléber vê fichas chegando. Ele não faz nada — apenas percebe que o trabalho está sendo feito sem ele |
| **Canal** | Painel web |
| **O que o OmniStay faz** | Consolida cada resposta de hóspede e atualiza o status para `aguardando_transcricao` ou `parcial` |
| **Dado gerado** | Fichas consolidadas · mudanças de status |
| **Estado emocional** | **Confiança crescente.** É o único momento da jornada em que o sistema trabalha e ele assiste. Vale desenhar para ser percebido |
| **Risco / oportunidade** | **Oportunidade:** é o argumento de venda interno do produto — o gerente vê a fila de fichas prontas antes do pico |

### R4 — Check-in e transcrição

Esta é a fase mais importante da trilha B e a mais frágil da proposta de valor.

| Camada | Conteúdo |
| --- | --- |
| **Ação** | Marina chega. Cléber confere o documento físico, **confirma o check-in no painel**, e transcreve a ficha para o PMS |
| **Canal** | Presencial + painel web + PMS |
| **O que o OmniStay faz** | Emite `checkin_confirmado` e dispara o pacote de boas-vindas |
| **Dado gerado** | Timestamp de check-in · status `cadastro_concluido` após a transcrição |
| **Estado emocional** | **Ambivalente.** O atendimento no balcão ficou mais rápido, mas a digitação não desapareceu — apenas mudou de lugar |
| **Risco / oportunidade** | Dois riscos: **esquecer de clicar** (o processo trava silenciosamente) e **a percepção de digitação dupla** (o sistema perde o defensor interno) |

> **Ponto de honestidade — a transcrição não é eliminada.** O OmniStay elimina a ficha de
> papel, não a digitação no PMS. Sustentar em banca que ele acaba com o retrabalho seria
> falso, e é o tipo de afirmação que não sobrevive à primeira pergunta.
>
> **O ganho real, que é defensável:** a digitação sai do momento crítico — hóspede em pé,
> esperando, fila atrás — e vai para um momento de baixa demanda, com **dados já validados,
> legíveis e copiáveis**, em vez de letra manuscrita em ficha de papel.

**O que o MVP entrega nesta fase:** a ficha aparece no painel em texto limpo, validado e
organizado, e o recepcionista digita no PMS a partir dela. A transcrição continua manual.

> **Decisão de escopo (06/08/2026):** os auxílios de transcrição — botão "copiar ficha" em
> bloco, ordem de campos configurável por propriedade para coincidir com a tabulação do PMS,
> e cópia campo a campo — ficam registrados como **evolução futura, fora do MVP**.
>
> Justificativa: o ganho depende inteiramente de o PMS da propriedade aceitar colagem nos
> campos de cadastro, o que **ainda não foi verificado**. Sistemas hoteleiros antigos com
> interface em terminal frequentemente bloqueiam colagem, ou a aceitam em um campo mas não
> no formulário inteiro. Construir a funcionalidade antes dessa verificação é assumir o
> risco de entregar um botão inútil.
>
> **Verificação necessária antes de reabrir:** testar, no PMS real da propriedade, se o
> campo aceita `Ctrl+V`, e se aceita colagem em bloco com tabulação entre campos ou apenas
> valor por valor. O resultado desse teste é o que define se a evolução vale o esforço — e
> qual das três variações implementar.

Vale notar que o ganho principal da R4 **não depende dessa evolução**: ele vem de a ficha
estar digitada, legível e validada em vez de manuscrita, e de a digitação acontecer fora do
momento em que há alguém esperando no balcão.

### R5 — Durante a estadia: triagem do Alert Center

| Camada | Conteúdo |
| --- | --- |
| **Ação** | Cléber vê um chamado aberto, avalia e encaminha para a manutenção ou resolve ele mesmo |
| **Canal** | Painel web (Alert Center) |
| **O que o OmniStay faz** | Notifica o chamado classificado, com quarto, tipo, urgência e janela de preferência do hóspede |
| **Dado gerado** | Atribuição do chamado · mudança de status |
| **Estado emocional** | **Controle.** A reclamação chega escrita, classificada e com contexto, em vez de por telefone no meio de um check-in |
| **Risco / oportunidade** | **Risco:** excesso de notificação. Se o Alert Center apitar para coisas que não exigem ação, ele passa a ignorar o painel — e vai ignorar também o chamado que importa |

### R6 — Checkout

| Camada | Conteúdo |
| --- | --- |
| **Ação** | Cléber fecha a conta no PMS e **confirma o checkout no painel** |
| **Canal** | PMS + painel web |
| **O que o OmniStay faz** | Emite `checkout_realizado` e dispara a pesquisa de avaliação |
| **Dado gerado** | Timestamp de checkout · encerramento da estadia |
| **Estado emocional** | **Rotina.** Um clique a mais, de baixo custo cognitivo |
| **Risco / oportunidade** | **Mesmo risco da R4:** esquecer o clique. A pesquisa não é enviada e a avaliação se perde — e ninguém percebe, porque a ausência de uma pesquisa não gera reclamação |

### R7 — Passagem de turno

| Camada | Conteúdo |
| --- | --- |
| **Ação** | Cléber olha o que fica em aberto e passa para o próximo turno |
| **Canal** | Painel web |
| **O que o OmniStay faz** | Apresenta chamados não resolvidos, fichas parciais e reservas do dia seguinte sem cadastro |
| **Dado gerado** | Nenhum. Leitura |
| **Estado emocional** | **Encerramento limpo**, se a informação estiver em uma tela só |
| **Risco / oportunidade** | **Oportunidade:** a passagem de turno hoje é oral e se perde. Registrá-la no painel é ganho operacional que o hotel percebe imediatamente |

---

## 5. Trilhas reduzidas

### 5.1 Staff operacional — o consumidor do Alert Center

O staff (manutenção, governança) não tem jornada contínua. Tem um ciclo curto e repetido:

**notificação → leitura do chamado → deslocamento → execução → marcação de resolvido**

| Aspecto | Descrição |
| --- | --- |
| **Canal** | Painel web pelo navegador do celular — não há app nativo (decisão do Artefato 1) |
| **Dado que recebe** | Quarto, tipo de problema, urgência, janela de preferência do hóspede |
| **Dado que gera** | `chamado_resolvido`, que dispara a confirmação ao hóspede |
| **Estado emocional** | **Indiferente ao sistema, sensível ao atrito.** Ele quer saber onde ir e o que levar |
| **Risco crítico** | **Login.** Um profissional de manutenção com as mãos ocupadas não digita e-mail e senha em navegador de celular a cada chamado. Se o acesso for trabalhoso, ele resolve o problema e não marca como resolvido — e o hóspede nunca recebe a confirmação, quebrando o passo 3.5 do Artefato 1 |

> **Pendência levantada por este artefato:** definir o mecanismo de acesso do staff ao Alert
> Center. **Recomendação:** sessão longa por dispositivo, com link de acesso por perfil
> operacional, sem senha por chamado. É o único desenho compatível com a realidade de uso.

### 5.2 Gestor — o consumidor do Market Intel

O gestor não opera o sistema no dia a dia. Ele consulta, em cadência semanal ou quinzenal,
para decidir preço e para avaliar a operação.

| Aspecto | Descrição |
| --- | --- |
| **Canal** | Painel web, provavelmente em desktop |
| **Dado que recebe** | Preços e avaliações de concorrentes (P5) · notas de avaliação dos hóspedes (P4) · volume e tipo de chamados (P3) |
| **Dado que gera** | Decisão de preço, executada **fora do OmniStay** — no PMS ou nas OTAs |
| **Estado emocional** | **Curiosidade utilitária.** Ele quer uma comparação legível, não um relatório |
| **Risco / oportunidade** | **Risco:** dado de concorrente coletado sem periodicidade definida envelhece e leva a decisão errada — pior do que não ter dado. **Oportunidade:** cruzar reclamação recorrente (P3) com nota de avaliação (P4) é a informação que ele hoje não tem em lugar nenhum |

O Market Intel é **informativo, não transacional** — o OmniStay não altera preço. Registrar
isso evita que o Business Model Canvas prometa automação de tarifa.

---

## 6. Cenário atual × cenário com OmniStay

Comparação restrita aos momentos em que há mudança real. Onde o sistema não muda nada, está
dito que não muda — um documento de banca perde credibilidade quando reivindica ganho em
todo lugar.

| Momento | Hoje, sem OmniStay | Com OmniStay | Ganho real |
| --- | --- | --- | --- |
| **Cadastro do hóspede** | Ficha de papel preenchida no balcão, de pé, com o hóspede cansado. Letra manuscrita, campos ilegíveis, recepcionista decifra na hora de digitar | Dados digitados pelo próprio hóspede, no celular, no tempo dele, antes de chegar | **Alto.** Elimina o papel e a ilegibilidade. Não elimina a digitação no PMS |
| **Tempo de balcão no check-in** | Preenchimento + conferência + lançamento, com fila atrás | Conferência do documento + clique de confirmação. O lançamento acontece depois | **Alto**, e é o ganho mais visível para o hóspede |
| **Pedido no quarto** | Ligar para a recepção. Se ninguém atende, descer ou desistir. Nenhum registro do pedido | Mensagem no WhatsApp, com confirmação de recebimento e registro | **Alto.** Assíncrono, rastreável, e existe prova de que o pedido foi feito |
| **Reclamação técnica** | Chega por telefone ou no balcão, sem registro estruturado. A urgência depende de quem atendeu | Classificada, com quarto e urgência, direto no Alert Center, com horário de preferência do hóspede | **Alto.** Cria histórico de manutenção que hoje não existe |
| **Insatisfação durante a estadia** | Descoberta no checkout — ou na avaliação pública, quando não há mais nada a fazer | Pulso do segundo dia, com janela para recuperar | **Alto**, e é o item de maior valor comercial do produto |
| **Avaliação pós-estadia** | Depende do hóspede lembrar de avaliar na OTA. Taxa de resposta baixa, e a reclamação vai direto para o público | Pesquisa por WhatsApp logo após o checkout, em canal privado | **Médio-alto.** Não impede a avaliação pública, mas dá ao hotel a chance de agir antes |
| **Lançamento no PMS** | Digitação a partir de ficha manuscrita, decifrando letra alheia | Digitação a partir de dados legíveis e validados, fora do momento de pico | **Médio.** Muda a qualidade e o momento, não a existência da tarefa |
| **Conta do hóspede** | Consolidada no PMS, com todos os consumos | Continua no PMS. O OmniStay vê só o que passou pelo chat | **Nenhum.** Fora de escopo por decisão registrada |
| **Precificação** | Gestor consulta concorrentes manualmente, quando lembra | Coleta periódica consolidada no painel | **Médio.** Depende de a periodicidade estar definida — pendência aberta |

## 7. Momentos de verdade

Pontos em que a percepção do produto é decidida. Merecem prioridade de qualidade acima da
média no desenvolvimento.

| # | Momento | Ator | Por que decide |
| --- | --- | --- | --- |
| **MV1** | A primeira mensagem de pré-chegada | Hóspede | Define se o hotel parece atencioso ou invasivo. É o único contato antes da chegada, e não há segunda chance |
| **MV2** | A tela inicial do painel no começo do turno | Recepcionista | Decide se o sistema é consultado ou abandonado. Adoção interna se ganha ou se perde aqui |
| **MV3** | A confirmação imediata de uma reclamação | Hóspede | Separa "assistente que resolve" de "robô que enrola". É o teste mais duro da IA |
| **MV4** | O esforço de transcrever a ficha para o PMS | Recepcionista | Se parecer digitação dupla, o sistema perde o defensor interno que precisa ter |
| **MV5** | A pesquisa pós-checkout | Hóspede | Última impressão, e o dado de maior valor comercial do produto |

## 8. Rastreabilidade

Amarração explícita entre este artefato, o Artefato 1 e o catálogo de eventos. Serve de
insumo direto para o DFD do Artefato 3.

| Fase da jornada | Processo (Art. 1) | Eventos envolvidos | Ator que dispara |
| --- | --- | --- | --- |
| F0 Reserva | — | — | Fora do sistema |
| F1 / R2 / R3 Pré-chegada | P1 | `reserva_cadastrada`, `cadastro_recebido`, `cadastro_nao_respondido` | Recepção (manual) + Hóspede (reativo) + Sistema (temporal) |
| F2 / R4 Chegada | P2 | `checkin_confirmado` | Recepção (manual) |
| F3a / F3b / R5 Estadia | P3 | `mensagem_recebida`, `chamado_aberto`, `chamado_resolvido` | Hóspede + Sistema + Staff |
| F3c Pulso | P3 | `pulso_segundo_dia` | Sistema (temporal) |
| F4 / R6 Checkout | P4 | `checkout_realizado` | Recepção (manual) |
| F5 Pós-estadia | — | — *(sem evento, por decisão)* | Nenhum |
| Gestor / Market Intel | P5 | `coleta_mercado` | Sistema (agendado) |

**Sobre a F5:** a lacuna de evento identificada na primeira redação deste artefato foi
resolvida pela via oposta — em vez de criar um evento, **a funcionalidade saiu do MVP**.
O catálogo de dez eventos do Artefato 1 permanece completo e fechado, sem adições.

---

## 9. Análise crítica

Esta seção reúne o que a jornada expôs de frágil. Cada ponto vem com proposta de solução.

### 9.1 A dependência do clique é o ponto único de falha do sistema

Três transições de fase dependem exclusivamente de uma ação manual: `reserva_cadastrada`,
`checkin_confirmado` e `checkout_realizado`. Não há integração que as corrija, por decisão
de arquitetura.

O agravante é que **a falha é silenciosa**. Se o Cléber esquece de confirmar o check-in, nada
quebra visivelmente: o hóspede simplesmente não recebe as boas-vindas, e o sistema segue
tratando-o como não chegado. Ninguém reclama de uma mensagem que não chegou.

**Mitigações propostas, todas dentro da premissa de não integração:**

1. **Detecção de divergência temporal.** Passado o horário previsto de check-in sem
   confirmação, a reserva é destacada na fila do painel. O sistema não sabe que o hóspede
   chegou, mas sabe que deveria ter chegado.
2. **Inferência por comportamento.** Se chega mensagem de um hóspede cuja estadia ainda não
   foi confirmada, o painel sinaliza *"possível chegada não registrada"*. O hóspede está
   escrevendo do quarto — é o sinal mais confiável disponível sem PMS.
3. **Confirmação em lote.** Ao final do pico de check-ins, o painel oferece a lista das
   chegadas previstas ainda não confirmadas, para resolução em uma tela só.

Nenhuma delas elimina a dependência. Elas a tornam **visível**, que é o máximo alcançável
sem integração — e reconhecer isso explicitamente é mais defensável em banca do que
apresentar o problema como resolvido.

### 9.2 Pontos frágeis por trilha

| # | Ponto frágil | Onde | Proposta |
| --- | --- | --- | --- |
| 1 | Telefone digitado errado envia dados a terceiro | F0 / R2 | Validar formato na digitação; expor status de entrega do webhook no painel; **primeira mensagem sem dado pessoal do hóspede além do primeiro nome** |
| 2 | Resposta parcial da ficha | F1 | Consolidar como `parcial` e completar no balcão — decisão já registrada na F1 |
| 3 | IA responde com confiança algo que não sabe | F3a | Resposta automática limitada à base cadastrada da propriedade; fora dela, ramo humano |
| 4 | Hóspede sem resposta durante o chamado | F3b | Confirmação imediata obrigatória, antes da tramitação |
| 5 | Pulso disparado em hora errada | F3c | Regra de supressão já registrada na F3c |
| 6 | Alert Center com excesso de notificação | R5 | Só notificar o que exige ação humana; pedido registrado e resolvido pela IA não notifica |
| 7 | Login do staff no celular | 5.1 | Sessão longa por dispositivo, sem senha por chamado |
| 8 | "Extrato" que não é a conta | F4 | Renomeado para "pedidos feitos pelo chat" — **aplicado no Art. 1 §6.1** |
| 9 | Percepção de digitação dupla | R4 | Ficha legível e validada no MVP; auxílios de colagem só após testar o PMS real |
| 10 | Acompanhantes na mesma reserva | F1 / Art. 4 | Ver abaixo |

**Sobre o item 10 — reserva com mais de um hóspede.** A jornada foi escrita para Marina, que
viaja sozinha. Uma reserva de casal ou família tem vários hóspedes que a legislação exige
registrar, mas **um único telefone** conversando com o sistema.

> **Decisão de escopo proposta (06/08/2026):** no MVP, a ficha coletada pelo WhatsApp é a do
> **hóspede titular da reserva**. Acompanhantes são registrados no balcão, no fluxo
> tradicional. Justificativa: coletar N fichas por uma conversa multiplica as idas e voltas
> na mensagem, contradiz a decisão de mensagem única e a de não ser intrusivo, e introduz
> ambiguidade sobre quem consentiu com o quê. A modelagem do Artefato 4, no entanto, deve
> prever a **cardinalidade 1 reserva : N hóspedes desde já**, porque mudar isso depois é
> migração de esquema, não ajuste de tela.

### 9.3 LGPD e conformidade — o ponto que a banca cobra

**a) A oferta de retorno era mensagem de marketing, não utility. — RESOLVIDO**

O Artefato 1 previa, no passo 4.4, o envio de "oferta de retorno conforme a nota", com duas
consequências que não estavam registradas: na classificação da Meta é **categoria
Marketing**, mais cara que Utility e fora da projeção de custo do projeto; e na LGPD a base
legal de execução de contrato **não cobre** comunicação promocional após o fim da hospedagem.

**Encaminhamento adotado:** a oferta de retorno foi **retirada do MVP** e o passo 4.4 do
Artefato 1 foi corrigido. O consentimento passa a ser coletado na pesquisa de checkout, com
data e hora. Decisão completa e justificativa na fase F5.

**Recomendação correlata para a arquitetura de templates:** manter **boas-vindas e oferta
comercial em templates separados**. Se o pacote de boas-vindas do P2 embutir desconto ou
promoção, a Meta pode reclassificá-lo como Marketing por conta própria — e o custo do MVP
muda sem que ninguém tenha alterado uma linha de código.

**b) Não existe política de retenção definida.** *(pendência herdada do Artefato 1)*

Dados cadastrais completos — incluindo documento de identidade — ficam armazenados por prazo
indefinido. É a lacuna mais visível do projeto para uma banca.

> **Recomendação de parâmetros:** ficha cadastral retida por **5 anos** após o checkout,
> alinhada ao prazo de guarda de registro de hóspedes da legislação de turismo e ao prazo
> prescricional do Código Civil; **histórico de conversas do WhatsApp por 12 meses**, por ser
> dado operacional sem exigência legal de guarda longa; **expurgo automático agendado**, não
> manual. Confirmar os prazos antes de fechar o Artefato 4 — a decisão pertence à modelagem
> de dados, e é ali que ela precisa aparecer como atributo, não como intenção.

**c) Aviso de privacidade no primeiro contato.** A mensagem da F1 é o primeiro contato do
sistema com o titular dos dados. Ela deve declarar, em uma linha, a finalidade da coleta e
oferecer o canal de contato do controlador. Custa uma frase e cobre a exigência de
transparência do Art. 9º da LGPD.

**d) Minimização já está atendida** na decisão de não aceitar foto do documento (Artefato 1).
Vale manter esse argumento explícito na defesa — é o exemplo mais concreto de aplicação
consciente do princípio no projeto inteiro.

---

## 10. Decisões registradas neste artefato

| # | Decisão | Seção |
| --- | --- | --- |
| 1 | Resposta parcial da ficha é consolidada como `parcial` e completada no balcão, sem nova rodada de mensagens | F1 |
| 2 | Pulso do segundo dia só dispara com ≥24h de estadia restante, e é suprimido se houver chamado em aberto | F3c |
| 3 | O extrato passa a ser rotulado "pedidos feitos pelo chat", nunca "extrato" ou "conta" | F4 |
| 4 | Confirmação imediata de recebimento é obrigatória em reclamação técnica, antes da tramitação | F3b |
| 5 | Cadastro de reserva no painel pede apenas nome, telefone e datas | R2 |
| 6 | Ficha coletada por WhatsApp é a do titular; acompanhantes vão pelo balcão, mas a modelagem prevê 1:N | 9.2 |
| 7 | Oferta de retorno sai do MVP; consentimento passa a ser coletado na pesquisa de checkout | F5 / 9.3a |
| 8 | Auxílios de transcrição (copiar ficha, ordem configurável) ficam como evolução futura, condicionados a testar colagem no PMS real | R4 |
| 9 | Boas-vindas e oferta comercial são templates separados, para evitar reclassificação para Marketing | 9.3a |

**Correções aplicadas ao Artefato 1 (v1.1):** decisões 7 e a renomeação do extrato (decisão
3) alteraram o documento anterior. O passo 4.4 e a seção 6.1 foram reescritos, e a seção 6.2
foi criada para registrar a retirada com justificativa.

## 11. Pendências abertas

Herdadas do Artefato 1:

- [ ] Intervalo do reenvio e janela de corte na pré-chegada
- [ ] Política de retenção e prazo de exclusão dos dados cadastrais (LGPD) — recomendação em 9.3b
- [ ] Lista de concorrentes e periodicidade da coleta do Market Intel
- [ ] Confirmar a lista oficial vigente de campos exigidos por lei para registro de hóspede
- [ ] Material do MVP de usuário, ainda não enviado

Levantadas por este artefato:

- [x] ~~Criar evento para a fase F5, ou retirar a oferta de retorno do MVP~~ Resolvido:
      retirada do MVP, catálogo de eventos permanece com dez entradas
- [ ] **Testar colagem no PMS real da propriedade** — o campo aceita `Ctrl+V`? Aceita bloco
      com tabulação entre campos, ou só valor por valor? Define se os auxílios de
      transcrição da R4 valem o esforço, e qual variação implementar
- [ ] Mecanismo de acesso do staff ao Alert Center pelo celular — recomendação em 5.1
- [ ] Definir a base de conhecimento da propriedade que limita a resposta automática da IA
- [ ] Confirmar a categoria de cobrança do template de pulso do segundo dia junto à Meta
- [ ] Redigir a pergunta de opt-in que encerra a pesquisa de checkout, e definir onde o
      consentimento é persistido (entra no dicionário de dados do Artefato 4)
- [ ] Validar as personas com um recepcionista real, se houver acesso a um durante o projeto

---

## Próximos artefatos

| # | Artefato | O que este documento entrega a ele |
| --- | --- | --- |
| 3 | Fluxo de dados (DFD) e catálogo de eventos detalhado | A camada **Dado gerado** de cada fase, já mapeada a processos e eventos na seção 8 |
| 4 | Modelagem de dados (DER + dicionário) | Cardinalidade 1 reserva : N hóspedes, status `parcial` da ficha, campos de consentimento e prazos de retenção |
| 5 | Arquitetura e stack | Requisitos de painel derivados das trilhas B e 5.1 — tela inicial única, sessão longa para staff |
| 6 | Business Model Canvas — revisão completa | Contraste as-is/to-be da seção 6 e a correção de custo da categoria Marketing (9.3a) |
