# Modelo de dados — Chamados, pedidos e a tela da equipe

Referência: `docs/04-schema.sql`. Decisões em [research.md](./research.md).
Esta fatia **não cria tabela**. `solicitacao`, `consumo` e o gatilho
de resolução são os da F3.4–F3.7. O que nasce é modelo de superfície
no frontend.

---

## Entidades novas (só de superfície)

### Item da lista operacional

Projeção de um item de `GET /solicitacoes` para as duas telas. Não
é persistida. Ordem = ordem do array (já `aberta_em` crescente).

| Campo (API) | Uso na recepção | Uso na equipe |
| --- | --- | --- |
| `id_solicitacao` | Identidade do `POST .../resolucao` | o mesmo |
| `id_reserva` | Alvo de **Ver ficha** (`/ficha/{id}`) | **não exibir**; **não** link |
| `tipo` | Natureza (reclamação / serviço / consumo) | o mesmo |
| `descricao` | Texto do pedido/problema | o mesmo |
| `numero_quarto` | Quarto, ou vazio perceptível | o mesmo |
| `urgencia` | Urgência visível | o mesmo |
| `janela_preferencia` | Se houver, na reclamação | o mesmo |
| `status` | `aberta` / `em_andamento` — ambos são pendência | o mesmo |
| `aberta_em` | Instante + entrada de `tempoDecorrido` | o mesmo |
| `destaque_tempo_excedido` | Destaque só se `true` (reclamação) | o mesmo |
| `valor_praticado` | Se consumo, valor visível | o mesmo |
| `status_lancamento` | Não oferece lançar; pode ignorar na UI | o mesmo |

A tela **não** lê nome, telefone, documento. Esses campos **não**
existem neste JSON (contrato F3.4–F3.7).

### Tempo decorrido

Derivado: `tempoDecorrido(aberta_em, agora)`. Não há coluna. Não
tique contínuo.

### Natureza

Derivado de `tipo`. Três rótulos distintos. Não é urgência e não é
o destaque de prazo.

---

## Entidades reusadas

### `solicitacao` (banco)

| `tipo` | Nas listas desta fatia se `aberta`/`em_andamento`? | Resolvido nesta tela? |
| --- | :---: | :---: |
| `reclamacao` | sim | sim |
| `servico` | sim | sim |
| `consumo` | sim | sim (quarto; lançamento intacto) |

`resolvida` / `cancelada`: fora do GET, fora da tela.

Transição `aberta` → `resolvida` continua na F3.6/F3.7 (clique +
autor + instante + recado padrão). A tela não envia corpo no POST.

### `consumo` (filho)

Resolver o pai **não** altera `status_lancamento`. Fila financeira
é F8.5.

### `reserva` / ficha

Só a recepção, pelo **Ver ficha**. Staff recusado na casca e na
API de ficha (F8.3). Sem quarto na solicitação não impede o link:
`id_reserva` basta.

### `usuario` / `sessao`

Casca da F8.1. `recepcao` monta Chamados e pedidos; `staff` monta
Meus chamados (compacto, sessão longa). `gestor` não monta nenhuma.

---

## O que não nasce

- Tabela, coluna, visão ou revisão Alembic
- Operação nova em `politica.py`
- Atribuição de responsável, status `em_andamento` como passo de UI
- Lista de resolvidos do dia
- Campo de nome no JSON da lista
- Lançamento / dispensa
- Notificação empurrada

---

## Regras de validação (superfície)

| Situação | Efeito |
| --- | --- |
| `GET /solicitacoes` 200, `itens: []` | Lista vazia explícita; sem botão órfão |
| `GET` 401 | Casca devolve à entrada |
| `GET` 5xx / rede / corpo ilegível | Falha de leitura; não vazio; tentar de novo |
| Primeiro item do array | Mais antigo; a tela não reordena |
| **Ver ficha** (recepção) | Navega; zero `POST` de resolução |
| **Resolvido** | `POST .../resolucao`; botão daquele item indisponível até o retorno |
| `POST` 200 | `GET` de novo; id some das duas listas |
| `POST` 409 | Motivo visível; `GET` de novo; não afirma resolvido |
| `POST` 404 | Recado genérico da API; `GET` de novo |
| Clique fora do botão | Zero `POST` |
| Equipe: qualquer caminho à ficha | Ausente na tela; endereço `/ficha/:id` recusado pela casca |

---

## Relacionamentos

```text
sessao recepção ──> GET /solicitacoes ──> TelaAlertas
                         │                    ├─ Ver ficha → /ficha/{id_reserva}
                         │                    └─ Resolvido → POST .../resolucao → GET
sessao staff     ──> GET /solicitacoes ──> TelaChamados
                                              └─ Resolvido → POST .../resolucao → GET
sessao gestão    ──> casca redireciona; zero fetch destas telas
```
