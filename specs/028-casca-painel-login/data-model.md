# Modelo de dados — Casca do painel e login

Referência: `docs/04-schema.sql`. Decisões em [research.md](./research.md).
Esta fatia **não cria tabela**. Sessão e usuário são os da F0.3. Destino
de tela não é linha de banco.

---

## Entidades novas (só de superfície)

### Destino do painel

Não é tabela. É um item do mapa em `frontend/src/painel/destinos.ts`.

| Campo | Significado |
| --- | --- |
| `id` | Identidade estável (`fila`, `chamados`, `indicadores`, `simulador`, …) |
| `titulo` | Texto visível no menu e no cabeçalho da tela |
| `caminho` | Path sob `/app` (sem colidir com a API) |
| `perfis` | Subconjunto de `recepcao` · `staff` · `gestor` |

Casa do papel é um destino marcado como inicial. Sair não é destino: é
ação da casca sobre `DELETE /sessoes/atual`.

### Tela nomeada

Destino cujo trabalho operacional pertence a F8.2–F8.7. Nesta fatia
existe só o título. Sem entidade de “hóspede de maquete”, sem número
falso de chamado, sem indicador inventado.

---

## Entidades reusadas

### `usuario`

| Campo | Papel na casca |
| --- | --- |
| `email` / senha (hash) | `POST /sessoes` — a tela envia; nunca lê o hash |
| `perfil` | Escolhe casa e menu (`recepcao` · `staff` · `gestor`) |
| `ativo` | Desativado recusa a entrada com a mesma recusa visível |
| `id_hotel` | A casca **não** exibe nem envia. Vai na sessão; a API isola |

### `sessao`

| Campo | Papel na casca |
| --- | --- |
| token (só no cookie) | A tela não vê. `HttpOnly` |
| `expira_em` | Recarregar com prazo vencido → entrada |
| `revogada_em` | Mesmo efeito visível da expiração |
| `id_usuario` / `id_hotel` | `GET /sessoes/atual` não precisa devolver hotel; o cookie basta às APIs |

Nenhum `localStorage` / `sessionStorage` espelha a sessão.

---

## O que não nasce

- Tabela `destino`, `menu` ou `tela`
- Coluna de “último caminho” no usuário
- Chave em `parametro_hotel` para a casca
- Revisão Alembic
- Operação nova em `politica.py`

---

## Regras de validação (superfície)

| Situação | Efeito |
| --- | --- |
| E-mail ou senha em branco | Não dispara `POST /sessoes`; aviso de campo, não “credenciais inválidas” |
| `POST /sessoes` 401 | Permanecer em `/app/entrar`; texto único de recusa |
| `GET /sessoes/atual` 200 | Ir à casa do `perfil` se o caminho for entrada ou raiz |
| `GET /sessoes/atual` 401 | Só `/app/entrar` |
| Caminho cujo `perfis` não inclui o perfil | Não renderiza o conteúdo; vai à casa (ou à entrada se sem sessão) |
| Sair | `DELETE /sessoes/atual` e `/app/entrar`; outras sessões do usuário intactas |

---

## Relacionamentos

```text
usuario 1 ──< sessao          (F0.3, banco)
   │
   └── perfil ──> destinos do painel   (mapa estático, não persistido)
                      └── um deles é a casa
```

O hotel não aparece neste diagrama da casca: ele já está na sessão e
em toda consulta de domínio.
