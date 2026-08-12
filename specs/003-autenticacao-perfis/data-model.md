# Fase 1 — Modelo de dados: Autenticação e Perfis

Uma tabela nova, nenhuma tabela alterada, três chaves novas de parâmetro. O bloco de DDL abaixo é
o que entra tanto na revisão `0002_sessao` quanto em `docs/04-schema.sql` — literalmente o mesmo
texto, porque é o teste de conformidade da F0.2 que garante o acordo entre os dois.

---

## Entidade nova: `sessao`

```sql
CREATE TABLE sessao (
    id_sessao   BIGSERIAL   PRIMARY KEY,
    id_usuario  BIGINT      NOT NULL REFERENCES usuario (id_usuario),
    token_hash  CHAR(64)    NOT NULL UNIQUE,
    dispositivo VARCHAR(120),
    criada_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    expira_em   TIMESTAMPTZ NOT NULL,
    revogada_em TIMESTAMPTZ,
    CONSTRAINT ck_sessao_expira_depois_de_criada
        CHECK (expira_em > criada_em),
    CONSTRAINT ck_sessao_revogada_depois_de_criada
        CHECK (revogada_em IS NULL OR revogada_em >= criada_em)
);

COMMENT ON TABLE sessao IS
    'Sessao do painel, uma linha por dispositivo autenticado. Guarda o hash do token e nunca '
    'o token: vazamento desta tabela nao equivale a vazamento de acesso.';
COMMENT ON COLUMN sessao.token_hash IS
    'Credencial de acesso. SHA-256 do token opaco; o token existe apenas no cookie do cliente.';
COMMENT ON COLUMN sessao.dispositivo IS
    'LGPD: dado pessoal (DP) de funcionario. Rotulo informado no login ou agente do cliente.';
COMMENT ON COLUMN sessao.expira_em IS
    'Fixado na criacao a partir da duracao configurada para o perfil. Alterar a configuracao '
    'afeta as sessoes seguintes, nunca as existentes.';

CREATE INDEX ix_sessao_usuario_ativas
    ON sessao (id_usuario) WHERE revogada_em IS NULL;
```

### Campos e regras

| Campo | Regra | Requisito |
| --- | --- | --- |
| `id_usuario` | Obrigatório; o hotel da sessão é o hotel deste usuário, por junção | FR-005, FR-024 |
| `token_hash` | SHA-256 em hexadecimal do token opaco. Único: dois tokens não colidem sem que o banco recuse | FR-005, FR-007 |
| `dispositivo` | Opcional. Rótulo livre, para a recepção saber o que está revogando | FR-013 |
| `criada_em` | Instante da autenticação | FR-005 |
| `expira_em` | Gravado na criação, a partir da duração configurada para o perfil | FR-005, FR-010, FR-012 |
| `revogada_em` | Nulo enquanto ativa. Preenchido no encerramento pelo próprio usuário, na revogação pela recepção e na desativação do usuário | FR-009, FR-014, FR-017 |

**Por que não há `id_hotel` nesta tabela**: duplicar a coluna permitiria uma sessão apontar para
hotel diferente do dono, e impedir isso no banco exigiria chave estrangeira composta, alterando a
tabela `usuario` existente. A junção com `usuario` entrega o mesmo isolamento sem estado
inconsistente possível. Discussão completa em [research.md](./research.md) seção 4.

**Por que a revogação é uma marca de instante e não a remoção da linha**: a recepção precisa ver que
revogou, e uma linha apagada não conta essa história. O expurgo dessas linhas não entra nesta fatia.

### Ciclo de vida

```
                    autenticacao
                         │
                         ▼
                      ATIVA ─────────── expira_em <= agora ──────► EXPIRADA
                         │
                         ├── encerramento pelo proprio usuario ──► REVOGADA
                         ├── revogacao pela recepcao ────────────► REVOGADA
                         └── desativacao do usuario ─────────────► REVOGADA
```

Não há transição de volta: sessão que saiu de ativa nunca retorna. Reautenticar cria linha nova.

**Uma sessão é válida quando as três condições valem ao mesmo tempo**: `revogada_em IS NULL`,
`expira_em > agora` e o usuário dono está ativo. A terceira é redundante com a revogação em massa
que a desativação faz — e é proposital: se algum caminho futuro desativar um usuário sem passar pelo
serviço, o acesso ainda cai, porque a verificação de validade também olha `usuario.ativo`.

Diferente do ciclo de vida da reserva, este **não** ganha trigger de validação. A tabela não tem
coluna de estado a transicionar: o estado é derivado de duas datas e de um `NULL`, e não existe
transição inválida a impedir — o Artigo IX pede garantia no banco quando ela cabe no banco, e aqui a
garantia já é a forma da tabela.

---

## Entidade existente: `usuario`

**Não é alterada por esta fatia.** As colunas necessárias já existem desde a F0.2.

| Campo | Uso nesta fatia |
| --- | --- |
| `email` | Identificador da autenticação. Já é único no esquema, o que sustenta a FR-022 |
| `senha_hash` | Recebe o valor derivado no formato descrito em [research.md](./research.md) seção 1. `VARCHAR(255)` acomoda com folga os ~80 caracteres do formato |
| `perfil` | `recepcao`, `staff` ou `gestor`. O `CHECK` do esquema sustenta a FR-023 no banco, além da validação de entrada |
| `ativo` | Falso impede autenticar e invalida as sessões existentes |
| `id_hotel` | Determina o hotel da sessão e o alcance de toda consulta |

**Sem coluna de auditoria de criação de usuário**, por decisão registrada na spec: `criado_em` já
existe e quem criou não é pergunta que o MVP precise responder (Artigo XI).

**Nomenclatura**: o esquema grava o perfil operacional como `staff`. A spec e a interface falam em
"equipe operacional". A tradução acontece na camada de apresentação; o valor gravado não muda, para
não exigir migração de dado por questão de rótulo.

---

## Entidade existente: `parametro_hotel`

Três chaves novas, semeadas pelo comando de bootstrap:

| Chave | Valor padrão | Significado |
| --- | --- | --- |
| `duracao_sessao_recepcao_horas` | `12` | Cobre um turno sem cobrir o seguinte |
| `duracao_sessao_gestor_horas` | `12` | Perfil de consulta, mesmo raciocínio |
| `duracao_sessao_staff_horas` | `720` | Trinta dias — é a decisão de sessão longa por dispositivo |

O comentário da tabela em `docs/04-schema.sql` lista as chaves previstas e passa a incluir estas
três. Valores são padrão de instalação e ficam sujeitos a ajuste com o hotel, como as demais chaves.

**Ausência de parâmetro é falha explícita, não valor embutido.** Se a chave não existir para a
propriedade, a autenticação falha com erro claro em vez de assumir um prazo — assumir seria
reintroduzir o número mágico que o Artigo XIII proíbe, disfarçado de tolerância.

---

## Entidade existente: `hotel`

Criada pelo comando de bootstrap, com nome e telefone informados. Nenhuma alteração de estrutura.

---

## Consultas que esta fatia introduz

| Consulta | Para quê | Índice que a serve |
| --- | --- | --- |
| Usuário ativo por e-mail | Autenticar | `usuario_email_key`, já existente |
| Sessão por `token_hash`, com o usuário e o perfil | Validar cada requisição autenticada | `sessao_token_hash_key`, unicidade já criada |
| Sessões ativas dos usuários de um hotel | Listagem para a recepção | `ix_sessao_usuario_ativas`, com junção em `usuario` |
| Sessões ativas de um usuário | Invalidar tudo ao desativar | `ix_sessao_usuario_ativas` |
| Parâmetros de duração de um hotel | Calcular a expiração | `uq_parametro_hotel_chave`, já existente |

A validação de sessão acontece em **toda** requisição autenticada, e é a consulta mais frequente do
sistema. Ela é uma busca por chave única com uma junção, o que é o menor custo possível sem abrir
mão da revogação imediata — o preço explícito da decisão da seção 2 da pesquisa.
