# OmniStay

**Seu hotel sem fila.**

Hub conversacional B2B2C para hotelaria. Fala com o hóspede pelo WhatsApp da reserva ao checkout:
pede a ficha antes da chegada, responde dúvidas usando **apenas** o catálogo do hotel, registra
pedidos, abre chamados e devolve à recepção o que a inteligência artificial não pode responder com
segurança.

Não substitui o sistema de gestão do hotel. Convive com ele.

> Projeto acadêmico — Thiago Alves Feitosa · RM 550442 · Sistemas de Informação · FIAP
> **Vídeo de demonstração:** <https://youtu.be/QXgb0tpWDq8>

---

## A ideia

A fila do check-in existe porque o hotel pergunta tarde: no balcão, com o hóspede cansado, dados
que ele já informou na reserva. O OmniStay pergunta antes — e quando o hóspede chega, o balcão vira
entrega de chave.

## Stack

| Camada | Tecnologia |
| --- | --- |
| API | Python 3.14 · FastAPI |
| Persistência | SQLAlchemy · Alembic (25 migrações) |
| Banco | PostgreSQL — gerenciado no Neon |
| Assíncrono | Worker próprio, fila em banco |
| IA | Google Gemini, atrás de interface trocável |
| Mensageria | WhatsApp Business Cloud API · simulador para demonstração |
| Painel | React · TypeScript · Vite · Tailwind · shadcn/ui |
| Testes | pytest · Vitest — 211 arquivos |

## Arquitetura

Monólito modular com **quatro portas trocáveis**. Nenhum módulo de negócio importa detalhe de
fornecedor.

| Porta | Implementações |
| --- | --- |
| `LLMProvider` | Gemini · falsa (testes) |
| `MensageriaGateway` | WhatsApp · simulada · falsa |
| `CatalogoRepository` | Banco · falsa |
| `FontePublica` | HTTP · falsa |

```
app/
  portas/        contratos com o mundo externo
  adaptadores/   implementações reais e falsas
  modulos/       acesso · atendimento · conversa · feedback
                 hospedagem · mercado · propriedade · sistema
  fila/          trabalho assíncrono
worker/          consumidor da fila
alembic/         25 migrações
frontend/        painel de operação, 17 telas
testes/          178 arquivos de teste do back-end
specs/           especificação de cada fatia (GitHub Spec Kit)
docs/            processos, jornada, dados, arquitetura, backlog
```

## A garantia central: verificação de fidelidade

Toda resposta automática passa por uma barreira antes de sair. O modelo declara quais trechos do
catálogo usou, e a verificação confere que cada trecho **existe literalmente no catálogo** e
**aparece no texto** que seria enviado. O que não passa vira encaminhamento para a recepção.

Para uma informação falsa chegar ao hóspede, ela teria que estar escrita no catálogo do hotel.

O preço nunca vem do modelo: a IA identifica **qual** item foi pedido, o valor é lido do cadastro.

## Como rodar

```bash
# dependências
uv sync
cd frontend && npm install && npm run build && cd ..

# banco (local, via docker) ou aponte DATABASE_URL para o Neon
docker compose up -d
cp .env.example .env        # preencha DATABASE_URL e GEMINI_API_KEY
uv run alembic upgrade head
uv run python -m app.bootstrap

# API e worker
uv run uvicorn app.main:app --reload
uv run python -m worker.consumidor
```

Painel em `http://localhost:8000/painel` · simulador de conversa em `/simulacao`.

> **Neon:** use o endpoint **sem** connection pooling. O PgBouncer rejeita o `statement_timeout`
> que a aplicação define na conexão.

### Testes

```bash
uv run pytest
cd frontend && npm test
```

Os testes rodam contra PostgreSQL **local** — criam e destroem bancos descartáveis a cada execução.

## Como foi construído

Desenvolvimento guiado por especificação, com o **GitHub Spec Kit**. Cada funcionalidade percorreu
`specify → clarify → plan → tasks → analyze → implement → testes → commit`.

Duas regras governaram o processo:

- **Teste antes do código**, sem exceção. Foi isso que permitiu alterar o esquema do banco 25 vezes
  sem quebrar comportamento já entregue.
- **Uma fatia, uma conversa.** O estado do projeto mora nos arquivos, nunca no histórico de um chat.

A migração inicial carrega uma cópia congelada do SQL de referência, e um teste compara o
inventário do banco migrado com o documento **nos dois sentidos**. Divergência entre documentação e
banco é impossível por construção.

## Proteção de dados

Senhas com PBKDF2 (600 mil iterações). Sessão em cookie `HttpOnly`. A equipe operacional resolve
chamados **sem** ver dado cadastral — a restrição é da API, não da tela. Retenção com expurgo
automático e comprovante de execução: ficha 5 anos, conversas 12 meses.

## Próximos passos

| Item | Situação |
| --- | --- |
| Integração com PMS | Especificado. Elimina a transcrição manual da ficha pela recepção |
| Canal de e-mail | Especificado. O núcleo já é agnóstico de canal |
| Módulos por propriedade | Especificado. Expressa os três planos comerciais |
| Áudio e imagem do hóspede | Especificado. O modelo escolhido já é multimodal |

## Documentação

Em [`docs/`](docs/): mapa de processos, jornada do usuário, fluxo de dados, modelagem, arquitetura,
backlog e o estado do projeto.
