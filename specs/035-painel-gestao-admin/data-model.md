# Modelo de dados — Painel da gestão, mercado e administração

Referência: `docs/04-schema.sql`. Decisões em [research.md](./research.md).
Esta fatia **não cria tabela**. O que nasce é consulta agregada,
lista de funcionários e modelo de superfície no frontend.

---

## Entidades novas (só de superfície / leitura)

### Indicadores da operação

Não persistidos. Um objeto por consulta a `GET /indicadores`.

| Campo | Origem | Recorte |
| --- | --- | --- |
| `chegadas_hoje` | `reserva` | `data_checkin_prevista = CURRENT_DATE` e `status NOT IN ('encerrado', 'cancelada')` — a função já existente |
| `hospedados` | `reserva` | `status = 'hospedado'` |
| `chamados_abertos` | `solicitacao` ⋈ `reserva` | `tipo IN ('reclamacao', 'servico')` e `status IN ('aberta', 'em_andamento')` |
| `consumo_a_lancar` | `consumo` ⋈ `solicitacao` ⋈ `reserva` | `SUM(valor_praticado)` onde `status_lancamento = 'pendente'`; `0` se vazio |

Nenhum destes campos é lista. Nenhum carrega nome, telefone,
documento, `id_reserva` ou `id_solicitacao`.

`tipo = 'consumo'` **não** entra em `chamados_abertos`.

### Funcionário na lista

Projeção de `GET /usuarios` (linhas de `usuario` do hotel da
sessão, ativos e desativados).

| Campo (API) | Uso na tela |
| --- | --- |
| `id_usuario` | Identidade do DELETE |
| `nome` | Coluna |
| `email` | Coluna; ocupado mesmo se `ativo = false` |
| `perfil` | `recepcao` · `staff` · `gestor` — rótulo de negócio |
| `ativo` | Situação; `false` → sem Reativar |

**Não existe** na lista: `senha`, `senha_hash`, sessão, dispositivo.

### Concorrente na visão atual

Projeção de `GET /mercado` (F5.3). A tela não persiste.

| Campo (API) | Uso na tela |
| --- | --- |
| `id_concorrente` | Clique → histórico |
| `nome` | Coluna |
| `ativo` | Distinguível se inativo |
| `situacao` | Marca de atual / desatualizado / falha / sem coleta / cadência ausente |
| `ultimo_sucesso` | Preço e/ou nota + `coletado_em`, ou ausente |
| `ultima_falha` | Marca de falha com data, ou ausente |

Sem `url_fonte`. Sem linha da própria casa.

### Ponto do histórico

Projeção de `GET /mercado/concorrentes/{id}`. Sucesso com valores
e data; falha sem preço zero.

### Comprovante na tela

Projeção de `GET /retencao`.

| Campo | Uso na tela |
| --- | --- |
| `meses_retencao_conteudo_livre` | Prazo vigente (ou “não configurado” se `null`) |
| `anos_retencao_ficha` | Prazo vigente (ou “não configurado” se `null`) |
| `execucoes[].executado_em` | Quando |
| quantidades por espécie | O quê / registros |
| flags de prazo ausente | Resultado daquela passagem, já existente |

---

## Entidades reusadas (banco, intocadas)

### `reserva`

Status `hospedado` = em casa agora. Chegadas do dia: regra F1.1.

### `solicitacao`

Tipos `reclamacao` e `servico` na conta de abertos. `consumo` não.
Status aberto: `aberta`, `em_andamento`. `resolvida` e `cancelada`
fora.

### `consumo`

`valor_praticado` ≥ 0. Soma só `pendente`. `lancado` e `dispensado`
fora da soma.

### `usuario`

`ativo` false = desativado, linha permanece. Unique de `email` em
toda a instalação. Sem coluna de reativação nova — não há
reativação nesta fatia.

### `execucao_retencao` / `parametro_hotel`

Comprovante e chaves `meses_retencao_conteudo_livre`,
`anos_retencao_ficha` como na F6.1. Sem botão de passagem.

### `concorrente` / `coleta_mercado`

Série somente leitura. Cadastro continua fora desta superfície.

---

## O que não nasce

- Tabela, coluna, visão ou revisão Alembic
- Operação nova em `politica.py`
- `PATCH` de reativar usuário
- Rota de disparo de retenção
- Campo de tarifa da casa
- Gráfico persistido ou série de mensagens/chamados por dia

---

## Regras de validação (superfície)

| Situação | Efeito |
| --- | --- |
| `GET /indicadores` 200, todos zero | Zeros honestos, não falha |
| `GET /indicadores` 5xx / rede | Falha de leitura; não zeros |
| Corpo com nome/telefone/`itens[]` | Fora do contrato; a tela não pede |
| `GET /usuarios` `usuarios: []` | Lista vazia honesta (só o bootstrap ainda não criou outros) |
| POST usuário 201 | GET da lista; nasce ativo |
| POST 409 / 422 | Motivo visível; nada criado |
| DELETE 204 | GET da lista; linha permanece `ativo: false` |
| DELETE da própria sessão | Controle ausente; `409` se forçado |
| DELETE 404 | Recado genérico; GET de novo |
| `GET /mercado` `concorrentes: []` | Vazio honesto |
| `situacao` `so_falha` ou `ultima_falha` | Marca de falha; valor do sucesso antigo, se houver, com data antiga |
| `situacao` `atual` | Sem marca de desatualizado |
| Histórico 404 | Não confirma concorrente alheio; visão atual intacta |
| `GET /retencao` `execucoes: []` | Vazio honesto; prazos ainda visíveis se vierem no envelope |
| Gestão | os quatro GET; POST/DELETE só em Usuários |
| Recepção / staff nestes paths | Casca redireciona; zero fetch |

---

## Relacionamentos

```text
sessao gestão ──> GET /indicadores ──────────────> TelaPainel
              ──> GET /mercado ──────────────────> TelaMercado
                     └─ clique → GET /mercado/concorrentes/{id}
              ──> GET /usuarios ─────────────────> TelaUsuarios
                     ├─ Novo → POST /usuarios
                     └─ Desativar → DELETE /usuarios/{id}
              ──> GET /retencao ─────────────────> TelaRetencao

sessao recepção/staff ──> casca redireciona; zero fetch destas telas
```
