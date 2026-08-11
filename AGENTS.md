# OmniStay — orientação para agentes de código

Leia este arquivo antes de escrever qualquer linha. Ele resume o que o projeto é, como o
código se organiza e o que nunca fazer.

**Documentação completa:** seis artefatos na pasta `docs/`. Quando uma decisão parecer
arbitrária, ela provavelmente está justificada lá.
**Princípios inegociáveis:** `.specify/memory/constitution.md`. Em caso de conflito, a
constituição vence.

---

## O que é o sistema

Hub conversacional para hotelaria. O hóspede conversa por WhatsApp; a recepção opera um
painel web; a equipe operacional recebe chamados; a gestão consulta indicadores.

**A premissa que governa tudo:** o sistema **não se integra ao PMS do hotel**. Ele roda em
paralelo, e o recepcionista é a ponte humana entre os dois. As transições entre fases do
processo são disparadas por cliques de funcionários, nunca por integração.

Isso não é limitação a contornar — é o argumento comercial do produto, porque o hotel adota
sem trocar o sistema que já usa. **Nunca proponha integração com o PMS.**

---

## Stack

| Camada | Tecnologia | Observação |
| --- | --- | --- |
| API | Python 3.11+ e FastAPI | Nunca faz trabalho demorado |
| Worker | Python | Consome a fila e roda o agendador |
| Banco | PostgreSQL 16 | `JSONB` para payloads e saídas de IA |
| Frontend | React e TypeScript | Protótipo já existente |
| Testes | pytest | Escritos antes do código |
| Migrações | Alembic | `04-schema.sql` é a referência documental |

**Não introduza** Redis, Celery, fila externa, cache distribuído, ORM alternativo ou
framework de frontend diferente. Cada peça a mais compete com tempo de implementar, e o
projeto tem um desenvolvedor e prazo fixo.

---

## Estrutura

```
app/
├── main.py            entrada da API
├── config.py          configuração por variável de ambiente
├── modulos/           propriedade · hospedagem · conversa · atendimento · feedback · mercado
├── portas/            LLMProvider · CatalogoRepository · MensageriaGateway
├── adaptadores/       implementações concretas das portas
├── fila/              enfileiramento e consumo
└── comum/             log, erros, segurança
worker/                consumidor e agendador
testes/                unitarios · integracao · ponta_a_ponta
```

### Camadas dentro de cada módulo

```
router      entrada HTTP. Valida formato, converte, delega. Sem regra de negócio
service     a regra de negócio. Não conhece HTTP nem SQL
repository  acesso ao banco. Não conhece regra de negócio
schema      contratos de entrada e saída
model       mapeamento das tabelas
```

**Regras de fronteira, sem exceção:**

- `service` não importa nada de `router` e não escreve SQL
- `router` não contém regra de negócio, só tradução de protocolo
- Um módulo só lê e grava nas tabelas que governa; para dado de outro, chama o serviço dele

---

## As três portas

O domínio depende de interfaces, nunca de implementações concretas.

| Porta | Para quê |
| --- | --- |
| `LLMProvider` | Classificação e conversação. Permite trocar de provedor e testar sem rede |
| `CatalogoRepository` | Fatos da propriedade. Isola a decisão de como buscar |
| `MensageriaGateway` | Envio de mensagem. Permite o simulador da apresentação |

Ao escrever teste, use as implementações falsas. **Teste que chama serviço externo não é
teste de unidade** — é teste lento, instável e que gasta cota.

---

## Regras que não se negociam

**Na dúvida, um humano vê.** Falha de classificação, texto não reconhecido, pergunta fora do
catálogo ou IA indisponível terminam em fila humana. Nunca em resposta inventada, nunca em
descarte.

**Gravar antes de enviar.** O webhook grava e responde imediato. Trabalho lento vai para a
fila. Falha de envio nunca causa perda de dado.

**Confirmação antes de tramitação.** Solicitação e reclamação recebem confirmação ao hóspede
antes de qualquer processamento.

**Conteúdo de mensagem nunca vai para log.** Logs registram identificadores, classificações e
códigos de erro. Nunca o texto.

**Sem número mágico.** Prazo, intervalo e periodicidade vêm de `parametro_hotel`.

**`id_hotel` em toda consulta de domínio**, mesmo com uma única propriedade cadastrada.

**Garantia no banco quando possível.** Idempotência é `UNIQUE`. Transição de estado é
trigger. Domínio de valor é `CHECK`.

**A palavra "extrato" não existe no produto.** A lista de consumos se chama "pedidos feitos
pelo chat", em interface e em mensagem.

---

## Ciclo de trabalho

1. Escreva o teste. Rode. **Veja falhar pelo motivo certo**
2. Implemente o mínimo para passar
3. Rode de novo. Verde
4. Refatore com o teste verde
5. Commit único e descritivo

Um teste que passa de primeira é suspeito: ou não testa o que diz, ou a funcionalidade já
existia.

```bash
pytest                              # tudo
pytest testes/unitarios -q          # rápido, durante o ciclo
pytest -k nome_do_teste             # um só
```

---

## Ao propor mudança de esquema

Toda alteração de modelo gera **migração Alembic e atualização do `04-schema.sql`**. Banco e
documento divergentes é pior do que documento inexistente.

---

## Quando algo parecer errado na documentação

Aconteceu antes e vai acontecer de novo: a documentação foi escrita sem execução real, e
alguns pontos só se revelam ao rodar.

**Não contorne silenciosamente.** Sinalize a divergência, proponha a correção no artefato
correspondente, e só então implemente. Um sistema que diverge da própria documentação perde o
valor de ter documentação.
