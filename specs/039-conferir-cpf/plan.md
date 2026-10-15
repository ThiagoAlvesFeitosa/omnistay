# Implementation Plan: Conferir o CPF antes de gravar

**Branch**: `039-conferir-cpf` | **Date**: 2026-10-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/039-conferir-cpf/spec.md`

## Summary

Quando o tipo de documento é CPF, o número só é aceito depois do
dígito verificador. Reprovado não grava: na coleta a ficha fica
parcial (sem mensagem nova); no painel o salvamento inteiro é
recusado, com aviso no campo, e o rascunho permanece. Gravado: onze
dígitos. Painel e cópia: `000.000.000-00`. RG e passaporte iguais.
Migração 0027 converte quem não colide; pares que colapsam ficam com
a escrita original; índice único intacto; log só com ids.

Decisões em [research.md](./research.md): um sítio
(`validar_campos_extraidos`); sem lib; sem CHECK; sem algoritmo no
frontend. Sem PMS, sem operação nova, sem Redis.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de
desenvolvimento); TypeScript no `frontend/` já existente

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 Core, Alembic,
pytest, Vitest. **Nenhuma dependência nova.**

**Storage**: PostgreSQL 16. Tabela `hospede` sem coluna nova. Índice
`uq_hospede_documento` **intocado**. Revisão `0027` só atualiza
valores de `numero_documento` tipo CPF. `0001` congelado;
`docs/04-schema.sql` só se o comentário da coluna acompanhar a forma
canônica (onze dígitos)

**Testing**: pytest — CPF válido com/sem pontuação grava onze
dígitos; reprovado (dígito, onze iguais, tamanho) não entra na
coleta (ficha parcial, sem mensagem) nem no PUT (nada persistido);
RG inalterado; log sem o número; migração converte o isolado e
pula o par, logando ids. Vitest — aviso no campo do CPF; rascunho
conservado; leitura e cópia formatadas. Portas falsas. Banco real
na integração da migração e do PUT

**Target Platform**: Servidor Linux; desenvolvimento Windows.
API + worker + SPA `/app`. Sem app nova

**Project Type**: Serviço web. Ampliação da validação da ficha
(F1.3 / F8.3). Sem destino novo

**Performance Goals**: Um hotel no MVP. Conferência é CPU sobre
onze dígitos. Migração é um `UPDATE` pontual. Sem meta de
throughput

**Constraints**: Sem PMS; sem foto de documento; número fora do
log; sem lib de CPF; sem CHECK que recuse escrita original dos
pares; sem mexer no UNIQUE; F9.3–F9.5 fora; `id_hotel` continua
nas consultas da ficha

**Scale/Scope**: 0 tabelas, 0 rotas, 0 operações na matriz, 1
revisão de dados, 1 função de conferência, superfície da
`TelaFicha` (aviso + formatação). Núcleo: `validacao_ficha.py` +
`completar_ficha_titular` (já recusa o lote) + tela

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Cópia da ficha continua texto para colar. Sem consulta à Receita além do dígito |
| II — Na dúvida, humano vê | CPF reprovado na coleta → ficha parcial, recepção confere. Sem inventar número |
| III — Gravar antes de enviar | Coleta já grava a mensagem; o número ruim simplesmente não entra no hóspede |
| IV — Fila como verdade | Pendência é a ficha parcial já visível na fila do dia |
| V — Ausência humana visível | Mesmo sinal de parcial; sem “ciente” |
| VI — Confirmação antes de tramitar | Intocado |
| VII — Não ser intrusivo | Zero mensagem nova ao hóspede (FR-005) |
| VIII — Minimização | Número nunca no log (recusa e migração). Sem foto. Aviso no painel não ecoa o documento no log |
| IX — Garantias no banco | UNIQUE existente permanece. CHECK do algoritmo **não** entra: os pares não convertidos ficariam ilegais (clarificação). Aplicação barra o caminho novo |
| X — Portas trocáveis | Sem porta nova. Testes com LLM/mensageria falsos na coleta |
| XI — Complexidade exige problema | Sem lib, sem rota, sem tela nova, sem segundo algoritmo em TS |
| XII — Teste primeiro | Cada FR com teste que falha por ausência |
| XIII — Parâmetro não é constante | Dígito verificador é regra federal, não prazo da casa. Sem chave nova em `parametro_hotel` |
| XIV — Multi-tenant | `completar_ficha` e consolidação já filtram `id_hotel`. Índice único global **não** é desta fatia (F9.3) |
| XV — Honestidade | Não promete que o CPF existe na Receita nem que dois cadastros antigos iguais foram fundidos |

**Ponto de atenção 1 — Artigo IX vs CHECK.** A garantia possível
aqui é o UNIQUE que já existe. CHECK “CPF = onze dígitos” violaria
FR-012. Registrado, não contornado em silêncio.

**Ponto de atenção 2 — `completar_ficha` já recusa o lote.** O
trabalho do painel é mensagem + aviso **no campo** + formatação.
Não reescrever o serviço para “salvar o resto”.

**Ponto de atenção 3 — conformidade do esquema.** Sem mudança de
tabela; `04-schema.sql` só no comentário se a forma canônica for
documentada. Revisão `0027` é DML + log.

**Ponto de atenção 4 — documentação viva.** Ao implementar, a
pendência “Validar `numero_documento`” em
`docs/00-ESTADO-DO-PROJETO.md` e o CPF do roteiro/wireframe saem
desta lista — atualizar o estado, não silenciar.

## Project Structure

### Documentation (this feature)

```text
specs/039-conferir-cpf/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── conferir-numero.md
│   ├── coleta.md
│   ├── put-ficha.md
│   ├── superficie-painel.md
│   └── migracao-e-logs.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks (ainda não)
```

### Source Code (repository root)

```text
app/modulos/conversa/validacao_ficha.py   # conferência + onze dígitos
app/modulos/hospedagem/service.py         # mensagem 422 sem eco (já aborta)
alembic/versions/0027_*.py                # DML + log de colisão
docs/04-schema.sql                        # comentário da coluna, se couber
docs/00-ESTADO-DO-PROJETO.md
docs/roteiro-de-teste.md
docs/wireframes-painel.html
frontend/src/painel/
├── ficha.ts                 # formatar CPF na leitura e na cópia
├── TelaFicha.tsx            # aviso no campo; rascunho intacto
└── TelaFicha.test.tsx
testes/unitarios/modulos/conversa/test_validacao_ficha.py
testes/unitarios/modulos/hospedagem/test_completar_ficha.py
testes/integracao/test_alterar_ficha.py
testes/integracao/test_interpretar_ficha.py
```

**Structure Decision**: a conferência entra no validador que coleta
e painel já usam (F1.3 / F8.3). Sem módulo Python novo, sem rota
nova, sem segundo app.

## Complexity Tracking

> Nenhum item: o Constitution Check passou nas duas passagens.
> A ausência de CHECK é cumprimento da clarificação (FR-012), não
> violação do Artigo IX.
