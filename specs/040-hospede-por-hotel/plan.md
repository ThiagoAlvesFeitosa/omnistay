# Implementation Plan: Cada hóspede pertence a um hotel

**Branch**: `040-hospede-por-hotel` | **Date**: 2026-10-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/040-hospede-por-hotel/spec.md`

## Summary

O cadastro de hóspede passa a ter dono: o hotel controlador.
Documento único **dentro** da casa; o mesmo par tipo+número em
hotéis diferentes não conflita. PUT da ficha, em colisão na mesma
casa, recusa com nome e caminho `/ficha/{id_reserva}` (como a fila);
sem o documento no aviso; só recepção. Consentimento e expurgo
filtram pelo hotel do cadastro. Revisão Alembic `0028` preenche,
parte quem tem reserva em mais de um hotel, e troca o UNIQUE para
`(id_hotel, tipo_documento, numero_documento)`. Teste estrutural do
Artigo XIV: cada tabela tem `id_hotel` ou é filha, por FK
obrigatória, de uma que tem.

Decisões em [research.md](./research.md). Sem PMS, sem F9.4/F9.5,
sem operação nova, sem Redis.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de
desenvolvimento); TypeScript no `frontend/` já existente

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic,
pytest, Vitest. **Nenhuma dependência nova.**

**Storage**: PostgreSQL 16. `hospede.id_hotel` NOT NULL FK
`hotel`. Índice `uq_hospede_documento` passa a
`(id_hotel, tipo_documento, numero_documento)` (parcial, como
hoje). Revisão `0028`. `0001` congelado. `docs/04-schema.sql`
acompanha coluna, índice e comentário

**Testing**: pytest — dois hotéis gravam o mesmo documento; no
mesmo hotel o PUT `409` nomeia e traz `id_reserva` da ficha já
gravada, sem o número; consentimento/expurgo do A não tocam o B;
migração atribui, parte o multi-hotel, órfão com um hotel fica
dele, com dois ou mais loga ids e não inventa dono; walker
estrutural reprova `hospede` sem coluna e passa depois. Vitest —
aviso com nome e link `/ficha/{id}` sem documento. Portas falsas.
Banco real na migração, PUT e Artigo XIV

**Target Platform**: Servidor Linux; desenvolvimento Windows.
API + worker + SPA `/app`. Sem app nova

**Project Type**: Serviço web. Ampliação de hospedagem (F0.2 /
F1.3 / F8.3) e garantia constitucional (Artigo XIV)

**Performance Goals**: Um hotel no MVP; dois só nos testes. Migração
é DML pontual. Sem meta de throughput

**Constraints**: Sem PMS; sem foto; documento fora do log e do
aviso; sem lib; F9.4 e F9.5 fora; conferência de CPF (F9.2)
inalterada; sem operação nova na matriz; `evento_webhook` e
`alembic_version` são exceções nomeadas no teste estrutural

**Scale/Scope**: 1 coluna, 1 índice recriado, 1 revisão, 0 rotas
novas, 0 operações novas. Núcleo: `inserir_hospede` +
`completar_ficha_titular` (409) + `TelaFicha` + walker Artigo XIV +
expurgo/`hospede_do_hotel`

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Cópia da ficha continua texto. Sem SNRHos |
| II — Na dúvida, humano vê | Colisão no balcão: recusa nomeada + caminho. Coleta não ganha pendência (F9.5) |
| III — Gravar antes de enviar | Intocado |
| IV — Fila como verdade | Caminho do aviso é o mesmo da fila (`/ficha/{id_reserva}`) |
| V — Ausência humana visível | Órfão com dois hotéis: log de ids, revisão não inventa dono |
| VI — Confirmação antes de tramitar | Intocado |
| VII — Não ser intrusivo | Zero mensagem nova |
| VIII — Minimização | Número nunca no aviso nem no log. Sem foto |
| IX — Garantias no banco | UNIQUE parcial passa a incluir `id_hotel`. `id_hotel` NOT NULL no hóspede |
| X — Portas trocáveis | Sem porta nova |
| XI — Complexidade exige problema | Sem coluna em mensagem/consentimento; filho segue o pai. Sem tela de vínculo |
| XII — Teste primeiro | Cada FR com teste que falha por ausência |
| XIII — Parâmetro não é constante | Sem chave nova em `parametro_hotel` |
| XIV — Multi-tenant | Fecha o buraco do hóspede. Teste estrutural pega tabela nova sem dono |
| XV — Honestidade | Não promete reaproveitar quem volta (F9.4) nem fundir fichas (F9.5) |

**Ponto de atenção 1 — NOT NULL vs órfão.** Com um hotel, o órfão
fica dele e o NOT NULL entra. Com dois ou mais e hóspede sem
reserva, a revisão **registra ids e aborta** — não inventa dono e
não deixa coluna anulável. Demo tem um hotel.

**Ponto de atenção 2 — `evento_webhook`.** Não tem `id_hotel` nem
pai com hotel: é idempotência do canal. Exceção **nomeada no
teste**, com o motivo. `alembic_version` idem (versionamento).

**Ponto de atenção 3 — `0001` congelado.** Coluna e índice novos só
na `0028`. `04-schema.sql` e o banco migrado precisam continuar
iguais (`test_conformidade_do_esquema`).

**Ponto de atenção 4 — documentação viva.** Ao implementar, a
pendência `id_hotel` em `hospede` no estado do projeto sai desta
lista — atualizar, não silenciar F9.4/F9.5.

## Project Structure

### Documentation (this feature)

```text
specs/040-hospede-por-hotel/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── put-ficha.md
│   ├── superficie-painel.md
│   ├── migracao-e-logs.md
│   ├── artigo-xiv.md
│   └── consentimento-e-expurgo.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
alembic/versions/0028_*.py              # coluna, DML, UNIQUE, NOT NULL
app/modulos/hospedagem/
├── cpf_migracao.py                     # intocado (F9.2)
├── hospede_migracao.py                 # planejamento da 0028 (puro)
├── repository.py                       # inserir_hospede + hospede_do_hotel + expurgo
├── service.py                          # DocumentoEmUso com nome e id_reserva
├── schema.py                           # se o 409 estruturado pedir modelo
└── router.py                           # 409 sem eco do documento
app/modulos/acesso/                     # sem operação nova
docs/04-schema.sql
docs/00-ESTADO-DO-PROJETO.md
frontend/src/painel/TelaFicha.tsx       # nome + Link /ficha/{id}
testes/suporte/artigo_xiv.py            # walker estrutural
testes/unitarios/modulos/hospedagem/
testes/integracao/test_alterar_ficha.py
testes/integracao/test_artigo_xiv.py
testes/integracao/test_retencao.py
```

**Structure Decision**: o dono mora em `hospede`; filhos
(consentimento, vínculo) seguem o pai. Superfície reusa a rota da
ficha. Sem módulo de identidade novo, sem F9.5.

## Complexity Tracking

> Nenhum item: o Constitution Check passou nas duas passagens.
> Abortar a revisão com órfãos em dois hotéis é cumprimento da
> clarificação (não inventar dono) + Artigo IX (NOT NULL), não
> violação.
