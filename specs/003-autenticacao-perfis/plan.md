# Implementation Plan: Autenticação e Perfis

**Branch**: `003-autenticacao-perfis` | **Date**: 2026-08-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-autenticacao-perfis/spec.md`

## Summary

Dar ao painel acesso controlado com os três perfis, e dar a uma instalação nova o primeiro usuário
capaz de entrar. A fatia entrega autenticação por credencial própria, sessão revogável por
dispositivo, autorização por perfil e um comando de bootstrap.

Cinco decisões técnicas sustentam o desenho, todas detalhadas em [research.md](./research.md):

1. **Derivação de senha com PBKDF2-HMAC-SHA256 da biblioteca padrão**, com sal por usuário e o
   número de iterações gravado na própria linha. Argon2id e bcrypt seriam preferíveis em tese, mas
   são pacotes compilados e a máquina roda Python 3.14, onde wheel ausente é risco já registrado.
2. **A sessão é um token opaco, e o banco guarda só o hash dele.** JWT foi rejeitado por um motivo
   direto: não é revogável, e a fatia exige revogação valendo na requisição seguinte. Isso remove o
   `JWT_SECRET` que o Artefato 5 declara — a primeira das divergências documentais.
3. **O token viaja em cookie inacessível a script**, restrito a canal seguro e a requisições do
   próprio site. O frontend nunca toca no token, o que também dispensa peça anti-CSRF.
4. **Autorização é uma decisão pura**, uma matriz de perfil por operação nomeada, testável sem HTTP
   nem banco. As operações de fatias futuras já estão declaradas, e uma varredura de rotas garante
   que nenhuma rota nova escape da guarda.
5. **O repositório passa a receber a conexão.** É a primeira fatia que precisa de duas escritas
   coerentes entre si — desativar usuário e derrubar as sessões dele, criar hotel e gestor e
   parâmetros de uma vez.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary. **Nenhuma
dependência nova** — a derivação de senha, a geração de token e a leitura de senha no terminal saem
todas da biblioteca padrão (`hashlib`, `hmac`, `secrets`, `getpass`, `argparse`)

**Storage**: PostgreSQL 16. Uma tabela nova (`sessao`), nenhuma tabela alterada, três chaves novas em
`parametro_hotel`

**Testing**: pytest. Unitários sem banco para derivação de senha, política de perfis e regras de
sessão; integração com PostgreSQL real, sob o marcador `postgres`, para as rotas e o bootstrap

**Target Platform**: Servidor Linux; desenvolvimento em Windows com PostgreSQL em contêiner

**Project Type**: Serviço web. Sem frontend nesta fatia, por decisão registrada na spec

**Performance Goals**: A validação de sessão roda em toda requisição autenticada e é uma busca por
chave única com uma junção. A derivação lenta só ocorre na autenticação e na criação de usuário —
nunca em requisição já autenticada

**Constraints**: Revogação sem janela de tolerância; senha e token nunca legíveis em banco, log ou
resposta; nenhum prazo em constante de código; bootstrap atômico

**Scale/Scope**: 7 rotas HTTP, 1 comando de linha, 14 operações na matriz de autorização, 1 tabela
nova. Escala de uso: uma propriedade, dezenas de funcionários

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas duas passagens, sem
violações. Dois pontos de atenção estão registrados abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Nenhuma credencial, usuário ou sessão vem do PMS. O bootstrap cria a propriedade a partir de dados digitados |
| V — Ausência de ação humana visível | A listagem de sessões ativas é o que torna visível o dispositivo que ninguém revogou. A fatia não cria pendência silenciosa nova |
| VIII — Minimização de dados | Senha só como derivado, token só como hash. O perfil operacional não alcança dado cadastral, e o de gestão também não, por escolha. Log recebe identificador e código, nunca senha, token ou cookie |
| IX — Garantias no banco | Unicidade de e-mail e de `token_hash` no banco; domínio de perfil em `CHECK`; coerência das datas da sessão em `CHECK`. O ciclo de vida da sessão não ganha trigger porque não há coluna de estado a transicionar — a garantia já é a forma da tabela |
| X — Portas trocáveis | Nenhuma porta nova é necessária: autenticação não fala com serviço externo. As três portas existentes não são tocadas |
| XI — Complexidade exige problema | Zero dependência nova. Sem framework de linha de comando, sem biblioteca de autenticação, sem JWT, sem coluna de auditoria de criação de usuário, sem registro de último uso de sessão |
| XII — Teste primeiro | Cada requisito tem teste que falha por ausência do código. A política de perfis e a derivação de senha são puras, o que mantém o ciclo rápido o suficiente para ser rodado a cada minuto |
| XIII — Parâmetro não é constante | As três durações de sessão vivem em `parametro_hotel`. Ausência da chave é falha explícita, não valor assumido. O número de iterações da derivação é parâmetro de segurança de plataforma, não de propriedade — mesma justificativa que a versão mínima do PostgreSQL na F0.2 |
| XIV — Multi-tenant desde a primeira linha | Toda leitura e escrita filtram pelo hotel do usuário da sessão. Listagem e revogação recusam alvo de outra propriedade com resposta que não revela sua existência |
| XV — Honestidade | A fatia declara o que não entrega: sem tela, sem contenção de tentativa repetida de senha, sem troca de senha, e a matriz de autorização ainda sem rotas para hóspede e domínio. Ver a seção própria abaixo |

**Ponto de atenção 1 — `id_hotel` ausente na tabela de sessão.** O Artigo XIV pede a coluna nas
tabelas de domínio. A sessão obtém o hotel por junção com o usuário. A alternativa literal criaria a
possibilidade de sessão e usuário divergirem de hotel, e impedir isso no banco exigiria chave
estrangeira composta, alterando a tabela `usuario` existente. A junção entrega o mesmo isolamento sem
estado inconsistente possível, e nenhuma migração futura fica devendo. Detalhe em
[research.md](./research.md) seção 4.

**Ponto de atenção 2 — módulo `acesso` fora da lista de seis módulos.** O `AGENTS.md` nomeia
propriedade, hospedagem, conversa, atendimento, feedback e mercado. Esta fatia acrescenta `acesso`,
que governa `usuario` e `sessao`. A alternativa era colocar autenticação dentro de `propriedade`, que
passaria a fazer duas coisas sem relação — catálogo e parâmetros de um lado, credenciais e sessões do
outro. A correção do `AGENTS.md` entra como tarefa.

## Project Structure

### Documentation (this feature)

```text
specs/003-autenticacao-perfis/
├── plan.md                          # Este arquivo
├── spec.md                          # Especificação, já esclarecida
├── research.md                      # Fase 0: 13 decisões e as divergências encontradas
├── data-model.md                    # Fase 1: tabela de sessão, ciclo de vida e consultas
├── quickstart.md                    # Fase 1: validação manual, do volume descartado ao login
├── contracts/
│   ├── api-de-acesso.md             # As 7 rotas, o cookie e o comando de bootstrap
│   └── politica-de-autorizacao.md   # Matriz de perfil por operação
├── checklists/
│   └── requirements.md
└── tasks.md                         # Fase 2, gerada por /speckit-tasks
```

### Source Code (repository root)

```text
app/
├── bootstrap.py                     # Entrada de linha de comando: primeira propriedade e gestor
├── config.py                        # Ganha o numero de iteracoes da derivacao
├── main.py                          # Registra o roteador de acesso
├── comum/
│   ├── relogio.py                   # agora(), injetavel, para testar expiracao sem esperar
│   ├── seguranca.py                 # Derivacao de senha, token opaco e hash do token
│   └── transacao.py                 # Dependencia que abre e fecha a transacao da requisicao
└── modulos/
    ├── acesso/
    │   ├── router.py                # /sessoes e /usuarios
    │   ├── service.py               # Autenticar, encerrar, revogar, criar e desativar usuario
    │   ├── repository.py            # usuario e sessao
    │   ├── schema.py                # Contratos de entrada e saida
    │   ├── politica.py              # Matriz perfil x operacao: decisao pura
    │   └── dependencias.py          # Sessao atual e exigencia de operacao
    └── propriedade/
        ├── service.py               # Criacao inicial da propriedade; leitura das duracoes
        └── repository.py            # hotel e parametro_hotel

alembic/versions/
├── 0002_sessao.py                   # Revisao com downgrade real
└── sql/
    └── 0002_sessao.sql              # Bloco congelado, identico ao que entra no documento

testes/
├── unitarios/
│   ├── comum/
│   │   └── test_seguranca.py        # FR-002, FR-003, FR-007
│   └── modulos/
│       ├── acesso/
│       │   ├── test_politica.py             # FR-018 a FR-021
│       │   ├── test_service_de_sessao.py    # FR-005, FR-010 a FR-017
│       │   └── test_service_de_usuario.py   # FR-004, FR-022, FR-023
│       └── propriedade/
│           └── test_bootstrap.py            # FR-026 a FR-029
└── integracao/
    ├── test_autenticacao.py         # FR-001, FR-006, FR-008, FR-009
    ├── test_sessoes.py              # FR-013 a FR-017 pelas rotas
    ├── test_usuarios.py             # FR-020, FR-022 a FR-024 pelas rotas
    ├── test_rotas_protegidas.py     # FR-008 para toda rota, inclusive as futuras
    └── test_bootstrap.py            # FR-025 a FR-029 contra banco real

docs/                                # Correcoes: schema, modelagem, arquitetura
```

**Structure Decision**: a estrutura da F0.1 continua valendo. Três acréscimos, cada um com motivo:
o módulo `acesso`, porque autenticação e sessão precisam de dono; um início do módulo `propriedade`,
porque `hotel` e `parametro_hotel` têm dono diferente e o bootstrap escreve nos dois sem que um
módulo invada a tabela do outro; e `app/bootstrap.py` como segunda entrada do processo, ao lado de
`main.py` — a API é uma forma de entrar no sistema, o comando de instalação é outra.

A camada `model` continua vazia: o projeto descreve o esquema em SQL e o aplica por migração, e
declarar as tabelas outra vez em classes criaria uma terceira descrição a manter em acordo. É
divergência com o `AGENTS.md`, registrada e com correção proposta.

## O que esta fatia não entrega

Declarado por exigência do Artigo XV, e para que nenhuma dessas ausências seja confundida com
esquecimento:

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Tela de login | O acesso só é exercitável por API e por teste | F1.1, junto da primeira tela com conteúdo |
| Contenção de tentativa repetida de senha | Força bruta não é contida. Hoje o painel não está publicado na internet — mas isto **precisa** entrar antes de qualquer exposição contínua, e a sessão longa amplia a consequência | Antes de publicar |
| Troca e redefinição de senha | O caminho é a gestão desativar e recriar o usuário | Fatia própria, quando houver demanda |
| Rotas de hóspede, reserva e solicitação com guarda ligada | A matriz declara as regras e os testes de unidade as verificam, mas nenhuma rota real as exerce ainda | F1.1, F1.3, F3.4 em diante |
| Expurgo das linhas de sessão vencidas | A tabela cresce indefinidamente. Em escala de dezenas de funcionários, isso é irrelevante por anos | F6.1, junto do expurgo por retenção |

A quarta linha merece ênfase: **as FR-018 e FR-019 são entregues como política testada e como
varredura de rotas, não como recusa em rota concreta de hóspede** — porque a rota não existe. A
varredura é o que impede que a F1.1 acrescente reservas sem guarda, e por isso ela é parte essencial
da entrega, não teste acessório.

## Correções nos artefatos de documentação

A orientação do projeto proíbe contornar divergência em silêncio. Sete correções entram como tarefa
desta fatia; o levantamento completo está em [research.md](./research.md) seção 13.

| Artefato | Correção |
| --- | --- |
| `docs/04-schema.sql` | Bloco de `sessao` na seção 1; chaves de duração no comentário de `parametro_hotel` |
| `docs/04-modelagem-de-dados.md` | Entidade `sessao` no DER e no dicionário, com classificação LGPD |
| `docs/05-arquitetura.md` §11.2 | Como a sessão existe: token opaco, cookie e revogação por linha |
| `docs/05-arquitetura.md` §11.3 | Remover `JWT_SECRET` — não há nada a assinar. Nenhum segredo novo entra |
| `.cursor/rules/30-seguranca-lgpd.mdc` | Mesma remoção; acrescentar o formato da senha derivada |
| `AGENTS.md` | Registrar o módulo `acesso` e que a camada `model` permanece vazia |
| `.env.example` | `SENHA_ITERACOES` e `BOOTSTRAP_SENHA_INICIAL`, sem valor |

O `docs/backlog.md` já foi corrigido durante a especificação, e o `docs/00-ESTADO-DO-PROJETO.md` será
atualizado no fechamento da fatia, quando o resultado da implementação for conhecido.

## Complexity Tracking

Sem violação constitucional a justificar. Quatro acréscimos estruturais, e por que cada um é o
caminho mais simples que resolve o problema:

| Acréscimo | Problema presente | Alternativa mais simples, rejeitada porque |
| --- | --- | --- |
| Módulo `acesso` | `usuario` e `sessao` precisam de um dono, e nenhum dos seis módulos existentes é sobre acesso | Colocar em `propriedade` faria um módulo cuidar de catálogo e de credenciais ao mesmo tempo |
| `app/bootstrap.py` | A FR-025 exige criar a primeira propriedade fora do painel | Uma tela de cadastro inicial recria o impasse: a tela exige login, o login exige usuário. Nenhum framework de linha de comando é introduzido — `argparse` e `getpass` bastam |
| Repositório recebendo conexão | Duas escritas que precisam ser atômicas: desativar usuário e derrubar sessões; criar hotel, gestor e parâmetros | Cada função abrir sua própria conexão, como na F0.1, deixaria o bootstrap criar hotel sem usuário quando algo falhasse no meio |
| `SENHA_ITERACOES` em configuração | 600.000 iterações por autenticação tornam a suíte lenta o bastante para a disciplina de teste ser abandonada | Fixar em constante obrigaria a escolher entre suíte lenta e derivação fraca em produção |
