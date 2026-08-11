# OmniStay — Estado do Projeto

**Atualizado em:** 06/08/2026
**Para que serve:** ponto de retomada. Leia este arquivo antes de continuar o trabalho.

---

## Onde paramos

**Os seis artefatos estão concluídos**, e a **preparação da implementação também**. A pasta
`implementacao/` tem o kit completo para começar a programar: guia de setup, constituição,
backlog de 24 fatias verticais e as regras do Cursor.

**Próximo passo:** seguir o `implementacao/00-GUIA-DE-SETUP.md`, passo a passo, e fazer o
primeiro ciclo com a fatia F0.1 para calibrar o ambiente.

**Método escolhido:** spec-driven development com GitHub Spec Kit, no Cursor, com TDD
obrigatório. Os seis artefatos são a especificação de alto nível; o backlog traduz isso em
fatias que o `/speckit.specify` consome.

**Para a próxima entrega**, além da implementação: a implantação em nuvem, que o ADR-008
deixou deliberadamente adiada para ser decidida contra um sistema funcionando.

## Arquivos nesta pasta

| Arquivo | Conteúdo |
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

## Ficha de cadastro do hóspede

Nome completo · Profissão · Data de nascimento · Tipo de documento · Número do documento ·
Endereço · CEP · Cidade · Telefone

## Regra de reenvio na pré-chegada

Um único reenvio com mensagem explicando que o cadastro antecipado é opcional. Persistindo
o silêncio, o sistema para de insistir e sinaliza no painel que a reserva chegará sem
cadastro prévio. **Não ser intrusivo é requisito explícito do projeto.**

Os parâmetros são linhas em `parametro_hotel`, configuráveis por propriedade:
`horas_ate_reenvio` e `horas_corte_antes_checkin`. Os **valores** ainda precisam ser
definidos com o hotel, mas a estrutura para armazená-los já existe.

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
- [x] ~~Mecanismo de agendamento~~ `APScheduler` no worker
- [x] ~~Rotina de expurgo por retenção~~ Tarefa agendada, com anonimização e auditoria
- [x] ~~Acesso do staff ao Alert Center~~ Sessão longa por dispositivo

Resolvidas pelo Artefato 6:

- [x] ~~Faixa de preço e margem~~ Três planos com custo unitário e margem em dois cenários
- [x] ~~Contradições entre o Canvas e a arquitetura~~ Seis corrigidas, com registro de
      alterações no próprio documento

Ainda abertas:

- [ ] **Executar o `04-schema.sql` num PostgreSQL real** — a verificação feita foi
      estrutural, não uma execução. Fazer isso antes de iniciar a implementação
- [ ] **Confirmar junto à Meta a tarifação das mensagens dentro da janela a partir de
      01/10/2026** — as margens do cenário B do Canvas dependem disso
- [ ] Definir os **valores** dos parâmetros com o hotel (horas de reenvio, janela de corte,
      periodicidade da coleta)
- [ ] Cadastrar a lista de concorrentes e **verificar os termos de uso de cada fonte**
- [ ] Confirmar a lista oficial vigente de campos exigidos por lei para registro de hóspede
- [ ] Testar colagem no PMS real
- [ ] Confirmar junto à Meta a categoria do template de pulso do segundo dia
- [ ] Redigir a pergunta de opt-in da pesquisa de checkout
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
