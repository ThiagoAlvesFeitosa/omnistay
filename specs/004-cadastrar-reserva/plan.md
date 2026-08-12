# Implementation Plan: Cadastrar Reserva

**Branch**: `004-cadastrar-reserva` | **Date**: 2026-08-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-cadastrar-reserva/spec.md`

## Summary

A recepção passa a registrar uma reserva com três campos (nome, telefone, datas) e a enxergar
essa reserva na fila do dia do próprio hotel. A reserva nasce em `aguardando_cadastro`. Telefone
inválido e datas inconsistentes são recusados na borda; isolamento por hotel e recusa de
`staff`/`gestor` reutilizam a sessão e a matriz da F0.3.

Sete decisões técnicas sustentam o desenho ([research.md](./research.md)):

1. **Nome = titular provisório** criado na mesma transação (`hospede` + `reserva` +
   `reserva_hospede`), sem coluna nova em `reserva`.
2. **API autenticada apenas** — sem tela React nesta fatia; comportamento exercitado por rotas e
   testes.
3. **Telefone canônico** com dígitos e prefixo `55`, validado na aplicação.
4. **Datas**: recusa clara na aplicação + `CHECK` no banco.
5. **Fila nominada** via `vw_fila_do_dia` ampliada, só recepção (`ler_fila_do_dia`); **contagem
   de chegadas do dia** (só o número) para recepção e gestão via `ler_indicadores` — o dado
   cadastral nunca trafega até o cliente da gestão.
6. **Telefone repetido sempre cria hóspede novo**; consolidação por pessoa, se existir um dia, é
   problema futuro explícito.
7. **Módulo `hospedagem`** como dono de `reserva` / `hospede` / `reserva_hospede`.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic, psycopg2-binary. **Nenhuma
dependência nova** — normalização de telefone é função pura no módulo

**Storage**: PostgreSQL 16. Sem tabela nova. Revisão `0003` só para ampliar `vw_fila_do_dia`.
Escrita em `hospede`, `reserva` e `reserva_hospede` (já existentes)

**Testing**: pytest. Unitários sem banco para telefone, regras de datas e serviço de reserva com
repositório falso; integração com PostgreSQL real (`postgres`) para rotas, isolamento por hotel e
atomicidade das três escritas

**Target Platform**: Servidor Linux; desenvolvimento em Windows com PostgreSQL em contêiner

**Project Type**: Serviço web. Sem frontend nesta fatia (decisão em research §2)

**Performance Goals**: Criar reserva é uma transação curta de três inserts; listar a fila é uma
consulta indexada por hotel/status. Volume esperado: dezenas de reservas por dia por propriedade

**Constraints**: `id_hotel` sempre da sessão, nunca do corpo; nome e telefone nunca em log;
nenhuma mensagem enviada ao hóspede; status inicial exclusivamente `aguardando_cadastro`

**Scale/Scope**: 3 rotas HTTP, 1 operação nova na matriz (`ler_fila_do_dia`), 1 revisão de visão,
1 módulo novo. Escopo de uso: uma propriedade em produção típica, testes com dois hotéis para
isolamento

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1. Nas duas passagens, sem
violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | A reserva é digitada pela recepção; nada é lido do PMS |
| V — Ausência de ação humana visível | A fila do dia torna a reserva (e a chegada não confirmada) perceptível no painel operacional |
| VIII — Minimização de dados | Só nome + telefone + datas na criação; log sem conteúdo pessoal; gestão recebe contagem, nunca lista nominada |
| IX — Garantias no banco | `CHECK` de datas e status inicial/default já existem; unicidade do titular parcial; visão e aplicação não substituem essas restrições |
| X — Portas trocáveis | Nenhuma porta nova: ainda não há mensageria nesta fatia |
| XI — Complexidade exige problema | Sem dependência nova, sem coluna `nome_contato` redundante, sem tela React nesta entrega |
| XII — Teste primeiro | Cada FR tem teste que falha por ausência; unitários de telefone/datas/serviço rápidos o bastante para o ciclo |
| XIII — Parâmetro não é constante | Nenhum prazo operacional novo; não há número mágico de negócio a extrair |
| XIV — Multi-tenant desde a primeira linha | `reserva.id_hotel` da sessão; fila filtra por hotel; tentativa de ver outro hotel devolve vazio, nunca vazamento |
| XV — Honestidade | Declara ausência de tela, de envio WhatsApp, de edição/cancelamento e de particionamento de `hospede` por hotel — ver seção própria |

**Ponto de atenção 1 — `hospede` sem `id_hotel`.** O Artigo XIV pede a coluna nas tabelas de
domínio. O esquema real (e a migração `0001`) não a tem, embora o DER mermaid do artefato 4
sugira o contrário. Isolamento desta fatia é garantido por `reserva.id_hotel`. Particionar
hóspede agora seria migração ampla sem caso de uso de reuso entre propriedades — fica registrado
como dívida consciente, não como bloqueio.

**Ponto de atenção 2 — previsão de tela na F0.3.** Aquela fatia adiava a UI para "F1.1, junto da
primeira tela com conteúdo". Esta fatia entrega o conteúdo via API e **não** a tela. A previsão
escorrega; declarado em research §2 e na tabela de ausências.

## Project Structure

### Documentation (this feature)

```text
specs/004-cadastrar-reserva/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-de-hospedagem.md
│   └── politica-de-autorizacao.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
app/
├── main.py                              # Registra o roteador de hospedagem
├── comum/
│   └── telefone.py                      # Normalizacao e validacao (puro)
└── modulos/
    ├── acesso/
    │   └── politica.py                  # Ganha ler_fila_do_dia
    └── hospedagem/
        ├── __init__.py
        ├── router.py                    # POST /reservas, GET /fila-do-dia,
        │                                # GET /indicadores/chegadas-do-dia
        ├── service.py                   # Criar reserva, fila e contagem
        ├── repository.py                # hospede, reserva, reserva_hospede, visao, contagem
        └── schema.py                    # Contratos de entrada e saida

alembic/versions/
├── 0003_fila_do_dia.py                  # Recria vw_fila_do_dia ampliada
└── sql/
    └── 0003_fila_do_dia.sql             # Bloco congelado

testes/
├── unitarios/
│   ├── comum/
│   │   └── test_telefone.py
│   └── modulos/
│       ├── acesso/
│       │   └── test_politica.py         # Acrescenta ler_fila_do_dia
│       └── hospedagem/
│           ├── test_service_de_reserva.py
│           ├── test_service_da_fila.py
│           └── test_service_de_contagem.py
└── integracao/
    ├── test_reservas.py                 # Criacao, validacoes, status, telefone repetido
    ├── test_fila_do_dia.py              # Ordenacao, sinalizacao, isolamento; gestor 403
    ├── test_contagem_chegadas.py        # So numero; gestor 200; staff 403
    └── test_rotas_protegidas.py         # Inclui as tres rotas novas na varredura

docs/
├── 04-schema.sql                        # Visao ampliada + comentario do titular minimo
└── 04-modelagem-de-dados.md             # Fluxo: criacao cria titular provisório
```

**Structure Decision**: a estrutura do monolito modular continua. O acréscimo é o módulo
`hospedagem`, já previsto no `AGENTS.md`. Função pura de telefone fica em `comum/` porque não é
regra de negócio de reserva — é normalização reutilizável pela F1.2. Camada `model` permanece
vazia.

## O que esta fatia não entrega

| Ausência | Consequência aceita | Quando entra |
| --- | --- | --- |
| Tela React / login no painel | Uso manual só via API e testes | Fatia de UI do painel (ou início da F1.2) |
| Envio da mensagem de coleta | Reserva existe sem o hóspede ser avisado | F1.2 |
| Interpretação da ficha / `ficha_completa` | Titular permanece provisório | F1.3 |
| Cancelamento e edição de reserva | Correção exige novo cadastro ou SQL | Fatia futura de ciclo de vida |
| Consolidação de hóspedes duplicados | Mesmo indivíduo pode ter várias linhas; histórico por pessoa fica inconsistente até consolidar | Fatia própria, se/quando houver histórico por pessoa |
| `id_hotel` em `hospede` | Hóspede é global no MVP; isolamento via reserva | Se/quando particionamento por propriedade exigir |

## Complexity Tracking

> Sem violações a justificar. Tabela omitida.
