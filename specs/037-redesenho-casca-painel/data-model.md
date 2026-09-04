# Modelo de dados — Redesenho da casca e apresentação

Referência: `docs/04-schema.sql`. Decisões em [research.md](./research.md).
Esta fatia **não cria tabela** e **não gera revisão Alembic**.

---

## Entidades de superfície (não persistidas)

### Destino do painel

Continua o mapa em `frontend/src/painel/destinos.ts`. Campos novos:

| Campo | Significado |
| --- | --- |
| `grupo` | `operacao` · `propriedade` · `gestao`, ou ausente (Simulador) |
| `noMenu` | `false` só em `reserva` (rota existe; item de menu não) |

`itensMenu(perfil)` devolve só destinos com `noMenu !== false` e
`perfis` contendo o papel, **agrupados**. Grupo vazio não existe na
árvore visível.

Sair não é destino. Nova reserva não é destino de menu.

### Sessão visível na casca

Não é tabela nova. É o JSON já existente mais um campo derivado:

| Campo | Origem |
| --- | --- |
| `nome`, `perfil`, … | como hoje (`usuario` / `sessao`) |
| `nome_hotel` | `hotel.nome` via `propriedade.service.ler_nome_hotel` |

Em branco no cadastro: string vazia; a área do nome permanece. Nunca
o nome de outro `id_hotel`.

### Bolha de conversa

Não é tabela. Superfície única para simulador e Estadia.

| Lado | Simulador | Estadia |
| --- | --- | --- |
| Hóspede | `direcao = recebida` | `origem = hospede` |
| Hotel | `direcao = enviada` | `origem` em `recepcao` · `automatico` |

Procedência automático × recepção: rótulo já entregue (F7.6), não
terceiro lado. Horário: regra de [apresentacao-br.md](./contracts/apresentacao-br.md).

---

## Entidades reusadas

### `hotel`

| Campo | Papel nesta fatia |
| --- | --- |
| `id_hotel` | Só na API / sessão interna. Não vai ao JSON da casca |
| `nome` | `nome_hotel` em `POST /sessoes` e `GET /sessoes/atual` |

Leitura **só** pelo módulo `propriedade`.

### `usuario` / `sessao`

Intocados no banco. Perfis `recepcao` · `staff` · `gestor` iguais.
A casca **traduz** para Recepção · Equipe · Gestão na UI.

### `mensagem`

Intocada. A tela passa a **mostrar** `em` / `enviada_em` com a regra
da bolha. Origem e janela continuam o contrato da F7.6.

---

## O que não nasce

- Tabela `destino`, `menu`, `grupo`
- Coluna `nome_hotel` em `sessao`
- Chave em `parametro_hotel` para largura de tela ou fuso
- Revisão Alembic
- Operação nova em `politica.py`

---

## Regras de validação (superfície)

| Situação | Efeito |
| --- | --- |
| `POST /sessoes` 201 | Corpo inclui `nome_hotel` da casa do usuário |
| `GET /sessoes/atual` 200 | Idem; hotel de outra propriedade não aparece |
| Hotel sem nome | `nome_hotel` vazio; casca não inventa rótulo |
| Destino `reserva` | Rota `/app/reserva` válida para recepção; **ausente** do menu |
| Grupo sem destino permitido | Rótulo do grupo não renderiza |
| Overlay estreito fecha por botão ou fundo | Destino corrente **não** muda |
| ISO data só dia ilegível | Não se fabrica `02/09/2026` |
| Instante ilegível | Não se fabrica `00:00` |
| Chamado sem `aberta_em` utilizável | Decorrido que já existia; sem instante fabricado |

---

## Relacionamentos

```text
usuario 1 ──< sessao          (F0.3, banco)
   │
   └── id_hotel ──> hotel.nome   (lido por propriedade, exposto como nome_hotel)
   └── perfil ──> destinos do painel (mapa estático + grupo + noMenu)
```
