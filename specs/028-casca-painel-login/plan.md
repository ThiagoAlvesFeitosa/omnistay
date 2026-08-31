# Implementation Plan: Casca do painel e login

**Branch**: `028-casca-painel-login` | **Date**: 2026-08-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/028-casca-painel-login/spec.md`

## Summary

O funcionário passa a entrar no painel com o e-mail e a senha que já
existem, permanece reconhecido no mesmo dispositivo, e cai na tela
inicial do seu papel. Sair encerra a sessão no servidor. O menu só
mostra o que o perfil pode usar.

Decisões em [research.md](./research.md): reuso de `POST/GET/DELETE
/sessoes`; SPA em `/app` (sem colidir com a API); simulador vira rota;
Tailwind + shadcn copiado; cookie `Secure` acompanha o esquema HTTP;
Vitest na casca, pytest no HTTP. **Sem** tabela, **sem** operação nova
na matriz, **sem** Playwright.

## Technical Context

**Language/Version**: Python 3.11+ (3.14 na máquina de desenvolvimento);
TypeScript no `frontend/` já existente

**Primary Dependencies**: FastAPI (intocado nas regras de acesso, salvo
`Secure` do cookie e o mount estático). Frontend: Vite + React 19 +
React Router + Tailwind. shadcn copiado (campo, botão, rótulo). Sem
Redux, sem Playwright, sem fila, sem cache

**Storage**: PostgreSQL 16. **Nenhuma tabela nova.** `usuario` e
`sessao` da F0.3. `0001`…`0023` intactos. Sem revisão Alembic

**Testing**: pytest — cookie conforme esquema, mount `/app`, redirect
`/demo`, regressão das rotas de sessão já verdes. Vitest + Testing
Library no `frontend/` — destino inicial, menu por perfil, entrar/sair
com `fetch` falso, token ausente de armazenamento de script. **Nenhum**
teste abre navegador nem chama rede externa

**Target Platform**: Servidor Linux; desenvolvimento Windows. API e SPA
no mesmo origin (proxy Vite em `/app` → API; estáticos em `/app` no
uvicorn). Equipe no celular; recepção e gestão no computador

**Project Type**: Serviço web + worker (intocado) + **casca** React no
`frontend/` existente. O simulador deixa de ser a única página

**Performance Goals**: um hotel no MVP; `GET /sessoes/atual` no
carregamento da casca. Sem meta de throughput. Entrada humana < 1 min
(SC-001)

**Constraints**: tela nunca lê o token; recusa de credencial
indistinguível; `id_hotel` só na API (já da sessão); log sem senha e
sem token; sem PMS; telas nomeadas sem dado inventado; F7.4 não filtra
menu

**Scale/Scope**: 0 tabelas, 0 operações novas na matriz, 3 rotas de
sessão reusadas, 1 prefixo de SPA, 1 redirect, 1 ajuste de cookie, 1
mapa de destinos, ~10 telas nomeadas (3 casas + mapa + simulador +
entrada). Worker intocado

## Constitution Check

*GATE: verificado antes da Fase 0 e novamente após o desenho da Fase 1.
Nas duas passagens, sem violações. Pontos de atenção abaixo da tabela.*

| Artigo | Como esta fatia se comporta |
| --- | --- |
| I — Não se integra ao PMS | Casca não infere chegada/saída. Zero clique operacional novo |
| II — Na dúvida, humano vê | Intocado. A casca não classifica mensagem |
| III — Gravar antes de enviar | Intocado. Login grava sessão (já F0.3) antes de qualquer tela |
| IV — Fila como verdade | Sem push. Recarregar consulta `GET /sessoes/atual` |
| V — Ausência humana visível | Não é desta fatia; as casas são pontos de chegada |
| VI — Confirmação antes de tramitar | Intocado |
| VII — Não ser intrusivo | Sem recado proativo novo |
| VIII — Minimização | Staff não vê nome/telefone/documento. Log sem senha, sem token, sem conteúdo. Foto continua recusada |
| IX — Garantias no banco | Nenhuma regra nova de sessão; UNIQUE e prazo já existem |
| X — Portas trocáveis | Intocado. Casca não instancia LLM nem mensageria |
| XI — Complexidade exige problema | Sem app nova, sem estado global, sem Playwright. Router e Tailwind são o problema presente (endereço + visual fechados). Vitest é o menor teste da tela |
| XII — Teste primeiro | Cada FR com teste que falha por ausência (pytest ou Vitest) |
| XIII — Parâmetro não é constante | Prazos de sessão continuam em `parametro_hotel`; a casca não os lê |
| XIV — Multi-tenant | Cookie da sessão já carrega `id_hotel`; a casca não pede hotel. Destino de outro hotel continua 404 na API |
| XV — Honestidade | A casca sozinha não opera o hotel. Sessão longa da equipe segue com dispositivo perdido até revogação no balcão. `/demo` deixa de ser a casa |

**Ponto de atenção 1 — cookie `Secure`.** O TestClient ignora o
atributo; o navegador não. Sem o ajuste ao esquema, o quickstart no
browser falha com “não entra” e a suíte continua verde. O teste novo
precisa inspecionar `Set-Cookie` em HTTP e em HTTPS.

**Ponto de atenção 2 — colisão de path.** `GET /fila-do-dia` vs tela
`/app/fila`. O prefixo `/app` é obrigatório. Montar o SPA em `/`
quebra a F1.1.

**Ponto de atenção 3 — login do simulador.** Remover o formulário de
`TelaSimulacao` sem a casca pronta deixa a banca sem entrada. A ordem
de implementação é: casca autenticar → rota do simulador → então
apagar o login embutido. Quickstart da F6.2 passa a apontar
`/app/simulador`.

**Ponto de atenção 4 — `frontend/dist` ausente.** Hoje o mount `/demo`
só existe se o build rodou. O mesmo vale para `/app`. A suíte não
depende do `dist`; o teste do mount usa diretório temporário ou skip
explícito quando não houver build — nunca falha a API por SPA ausente.

## Project Structure

### Documentation (this feature)

```text
specs/028-casca-painel-login/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── sessao-no-navegador.md
│   ├── casca-e-rotas.md
│   ├── destinos-por-perfil.md
│   ├── politica-de-autorizacao.md
│   └── logs.md
├── checklists/
│   └── requirements.md
└── tasks.md                 # Fase 2 — /speckit-tasks
```

### Source Code (repository root)

```text
app/
├── main.py                              # mount /app; redirect /demo → /app/simulador
└── modulos/acesso/
    ├── router.py                        # Secure do cookie conforme esquema
    ├── politica.py                      # intacta
    └── schema.py                        # intacto (perfil já sai em GET /sessoes/atual)

frontend/                                # o mesmo da F6.2, agora painel
├── package.json                         # + react-router-dom, tailwind, vitest
├── vite.config.ts                       # base /app/; proxy da API
├── src/
│   ├── main.tsx                         # RouterProvider
│   ├── painel/
│   │   ├── destinos.ts                  # mapa perfil → destinos
│   │   ├── Casca.tsx                    # menu, sair, recusa 401
│   │   ├── TelaEntrada.tsx
│   │   └── TelaNomeada.tsx              # título, sem dado inventado
│   ├── components/ui/                   # shadcn copiado (mínimo)
│   └── TelaSimulacao.tsx                # sem formulário de login
└── src/**/*.test.ts(x)                  # Vitest

testes/
├── unitarios/modulos/acesso/            # cookie Secure × esquema
└── integracao/
    └── test_casca_painel.py             # mount /app; redirect /demo
```

**Structure Decision**: estende o `frontend/` e o `app/main.py` já
existentes. Sem módulo Python novo, sem segundo app, sem worker
alterado.

## Complexity Tracking

> Nenhum item: o Constitution Check passou nas duas passagens. Router,
> Tailwind e Vitest estão justificados no Artigo XI da tabela acima
> (problema presente: endereço, visual fechado, TDD da tela).
