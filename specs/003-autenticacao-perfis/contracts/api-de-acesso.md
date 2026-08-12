# Contrato: API de acesso ao painel

Sete rotas. Este é o contrato que a F1.1 vai consumir quando o painel React existir, e é por isso
que o transporte do cookie está fechado aqui e não deixado para a implementação.

**Corpo de erro**: o padrão do FastAPI, `{"detail": "<mensagem>"}`. Nenhum envelope próprio é
inventado (Artigo XI). O código estável de cada falha vai para o log, não para o corpo.

---

## Cookie de sessão

| Atributo | Valor | Por quê |
| --- | --- | --- |
| Nome | `omnistay_sessao` | — |
| Valor | Token opaco de 32 bytes em base64 url-safe | Nada legível; o banco guarda só o SHA-256 |
| `HttpOnly` | Sim | Script na página não alcança o token |
| `Secure` | Sim | Nunca trafega em texto claro |
| `SameSite` | `Strict` | Requisição partida de outro site não carrega a sessão |
| `Path` | `/` | — |
| `Max-Age` | Segundos restantes até `expira_em` | Cookie e linha de sessão expiram juntos |

O cliente **não** guarda o token em nenhum armazenamento acessível a script. Ele nunca aparece em
corpo de resposta, em log ou em URL.

---

## `POST /sessoes` — autenticar

Pública. Cria a sessão.

```json
{ "email": "cleber@hotel.com.br", "senha": "…", "dispositivo": "Celular da manutencao" }
```

`dispositivo` é opcional; ausente, a API grava o agente do cliente truncado em 120 caracteres.

**201** — cookie definido no cabeçalho `Set-Cookie`.

```json
{ "id_usuario": 3, "nome": "Cleber Rocha", "perfil": "staff", "expira_em": "2026-09-10T14:22:31Z" }
```

**401** — credencial inválida. **A mesma resposta e o mesmo tempo** para e-mail inexistente, senha
errada e usuário desativado: `{"detail": "Credenciais invalidas."}`. A resposta não diz qual dos três
aconteceu, e a igualdade de tempo é obtida derivando contra um hash de referência quando o e-mail
não existe (FR-003).

**422** — corpo malformado. Nunca ecoa a senha recebida.

---

## `DELETE /sessoes/atual` — encerrar a própria sessão

Pública por construção: quem não tem sessão válida também pode chamar.

**204** — sem corpo, com o cookie removido. Idempotente: chamar sem sessão, com sessão expirada ou
com sessão já revogada produz o mesmo 204 (FR-009).

---

## `GET /sessoes/atual` — quem sou eu

Protegida, qualquer perfil. É como o painel decidirá o que renderizar, e é o recurso protegido mais
simples possível para exercitar a FR-008.

**200**

```json
{
  "id_sessao": 42,
  "id_usuario": 3,
  "nome": "Cleber Rocha",
  "perfil": "staff",
  "dispositivo": "Celular da manutencao",
  "expira_em": "2026-09-10T14:22:31Z"
}
```

**401** — sessão ausente, expirada, revogada, forjada, ou de usuário desativado. Mesma resposta em
todos os casos: `{"detail": "Sessao ausente ou invalida."}`.

---

## `GET /sessoes` — listar sessões ativas

Protegida, **somente `recepcao`**. Devolve as sessões ativas dos usuários da própria propriedade,
mais recentes primeiro.

**200**

```json
[
  {
    "id_sessao": 42,
    "id_usuario": 3,
    "nome_usuario": "Cleber Rocha",
    "perfil": "staff",
    "dispositivo": "Celular da manutencao",
    "criada_em": "2026-08-11T14:22:31Z",
    "expira_em": "2026-09-10T14:22:31Z"
  }
]
```

Nenhum token nem hash de token aparece aqui. **Não há campo de último uso** — decisão registrada na
spec: custaria uma escrita por leitura e a decisão de revogar se sustenta sem ele.

**403** — perfil `staff` ou `gestor`.

---

## `DELETE /sessoes/{id_sessao}` — revogar uma sessão

Protegida, **somente `recepcao`**.

**204** — revogada. A sessão é recusada já na requisição seguinte que a apresentar, sem janela de
tolerância (FR-014). Idempotente: sessão já revogada ou já expirada também responde 204, sem efeito
adicional (FR-015). As outras sessões do mesmo usuário continuam válidas (FR-016).

**403** — perfil `staff` ou `gestor`.

**404** — sessão inexistente **ou de outra propriedade**. Os dois casos respondem igual, para que a
resposta não revele que a sessão existe em outro hotel.

---

## `POST /usuarios` — cadastrar funcionário

Protegida, **somente `gestor`**. O usuário nasce no hotel de quem o criou.

```json
{ "nome": "Cleber Rocha", "email": "cleber@hotel.com.br", "perfil": "staff", "senha": "…" }
```

**201**

```json
{ "id_usuario": 3, "nome": "Cleber Rocha", "email": "cleber@hotel.com.br", "perfil": "staff", "ativo": true }
```

A senha nunca volta, nem derivada.

**403** — perfil `recepcao` ou `staff`.

**409** — e-mail já cadastrado (FR-022).

**422** — perfil fora de `recepcao`, `staff`, `gestor` (FR-023), e-mail malformado, ou senha com
menos de 12 caracteres.

---

## `DELETE /usuarios/{id_usuario}` — desativar funcionário

Protegida, **somente `gestor`**. Desativa; não apaga. As sessões do usuário são revogadas na mesma
transação (FR-017).

**204** — desativado. Idempotente sobre usuário já inativo.

**403** — perfil `recepcao` ou `staff`.

**404** — usuário inexistente ou de outra propriedade.

**409** — o alvo é o próprio usuário autenticado. Sem essa recusa, o único gestor de uma propriedade
poderia se desativar e deixá-la sem ninguém capaz de cadastrar usuários — o mesmo impasse que o
comando de bootstrap existe para resolver.

---

## Rotas públicas — a lista é fechada

| Rota | Por quê |
| --- | --- |
| `GET /health` | Verificação de saúde, da F0.1 |
| `POST /sessoes` | É como se obtém sessão |
| `DELETE /sessoes/atual` | Encerrar sem sessão não é erro |

**Toda outra rota registrada na aplicação exige sessão válida**, e um teste percorre as rotas para
garantir isso — inclusive as que fatias futuras acrescentarem. Ver [research.md](../research.md)
seção 8.

---

## Comando de bootstrap

Não é rota HTTP: é entrada de linha de comando, executada por quem instala.

```bash
python -m app.bootstrap --nome-hotel "Hotel Exemplo" \
                        --telefone-whatsapp "+5511999999999" \
                        --nome-gestor "Thiago Feitosa" \
                        --email-gestor "gestor@hotel.com.br"
```

A senha inicial vem de `BOOTSTRAP_SENHA_INICIAL` no ambiente ou, na ausência, de leitura interativa
que não ecoa o que é digitado. **Não existe senha padrão** (FR-027).

| Saída | Quando |
| --- | --- |
| Confirmação com o identificador do hotel e o e-mail do gestor criado | Banco migrado e sem nenhuma propriedade |
| Recusa explicando que já existe propriedade cadastrada, sem alterar nada | Banco já com propriedade (FR-026) |
| Falha explicando que a senha inicial não foi fornecida | Sem variável de ambiente e sem terminal interativo |

Cria, em uma única transação: a propriedade, o usuário de perfil `gestor` e as três chaves de
duração de sessão (FR-028, FR-029). A senha não aparece em log nem na saída do comando.
