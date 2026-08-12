# Quickstart — validar a entrega de Autenticação e Perfis

Roteiro para verificar a fatia do zero, à mão, além da suíte automatizada. Os detalhes de cada rota
estão em [contracts/api-de-acesso.md](./contracts/api-de-acesso.md); aqui ficam apenas os comandos e
o que se espera ver.

Comandos em PowerShell, na raiz do repositório. `curl.exe` explícito porque `curl` pode ser apelido
de `Invoke-WebRequest`.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` precisa estar no ambiente ou no `.env`. Nenhum valor de conexão vive em arquivo
versionado.

---

## Cenário 0 — O esquema ganhou a tabela de sessão

```powershell
alembic current
docker compose exec db psql -U postgres -d omnistay -c "\d sessao"
```

**Esperado**: revisão corrente `0002_sessao`, e a tabela com `token_hash` único, `expira_em` não nulo
e `revogada_em` anulável.

---

## Cenário 1 — Primeiro acesso de uma instalação nova

```powershell
$env:BOOTSTRAP_SENHA_INICIAL = "senha-inicial-do-gestor"
python -m app.bootstrap --nome-hotel "Hotel Exemplo" `
                        --telefone-whatsapp "+5511999999999" `
                        --nome-gestor "Thiago Feitosa" `
                        --email-gestor "gestor@hotel.com.br"
```

**Esperado**: confirmação com o identificador do hotel criado. No banco: uma linha em `hotel`, uma em
`usuario` com perfil `gestor`, e três em `parametro_hotel` com as durações de sessão.

**A senha não aparece** na saída do comando nem no log.

## Cenário 2 — O comando não age duas vezes

```powershell
python -m app.bootstrap --nome-hotel "Outro Hotel" --telefone-whatsapp "+5511888888888" `
                        --nome-gestor "Outro" --email-gestor "outro@hotel.com.br"
```

**Esperado**: recusa explicando que já existe propriedade cadastrada. Nada criado, nada alterado.

---

## Cenário 3 — Autenticar e alcançar um recurso protegido

```powershell
uvicorn app.main:app --reload   # em outro terminal

curl.exe -i -X POST http://localhost:8000/sessoes `
  -H "Content-Type: application/json" `
  -d '{\"email\":\"gestor@hotel.com.br\",\"senha\":\"senha-inicial-do-gestor\",\"dispositivo\":\"Notebook da gestao\"}'
```

**Esperado**: `201`, corpo com nome, perfil `gestor` e `expira_em`, e um cabeçalho
`Set-Cookie: omnistay_sessao=…; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=43200`.

Copie o valor do cookie e use-o nas chamadas seguintes:

```powershell
$sessao = "omnistay_sessao=<valor copiado>"
curl.exe -i http://localhost:8000/sessoes/atual -H "Cookie: $sessao"
```

**Esperado**: `200` com o próprio usuário e perfil.

> **Por que copiar o cookie à mão:** `curl` não reenvia cookie marcado como `Secure` sobre `http://`,
> por isso o jarro de cookies (`-c`/`-b`) não funciona aqui. O navegador **reenvia**, porque trata
> `localhost` como origem confiável — então o painel da F1.1 em desenvolvimento local não terá esse
> problema. Nos testes automatizados, o cliente usa `https://testserver`.

## Cenário 4 — Sem sessão não se entra

```powershell
curl.exe -i http://localhost:8000/sessoes/atual
curl.exe -i http://localhost:8000/sessoes/atual -H "Cookie: omnistay_sessao=token-inventado"
```

**Esperado**: `401` nas duas, com a mesma mensagem. Nenhum dado no corpo.

## Cenário 5 — Credencial errada não conta nada a quem tentou

```powershell
curl.exe -i -X POST http://localhost:8000/sessoes -H "Content-Type: application/json" `
  -d '{\"email\":\"gestor@hotel.com.br\",\"senha\":\"errada\"}'
curl.exe -i -X POST http://localhost:8000/sessoes -H "Content-Type: application/json" `
  -d '{\"email\":\"ninguem@hotel.com.br\",\"senha\":\"errada\"}'
```

**Esperado**: `401` idêntico nas duas, e tempos de resposta na mesma ordem de grandeza — é o efeito da
derivação contra hash de referência quando o e-mail não existe.

---

## Cenário 6 — A gestão cadastra a equipe

Com a sessão de gestão do cenário 3:

```powershell
curl.exe -i -X POST http://localhost:8000/usuarios -H "Cookie: $sessao" `
  -H "Content-Type: application/json" `
  -d '{\"nome\":\"Cleber Rocha\",\"email\":\"cleber@hotel.com.br\",\"perfil\":\"staff\",\"senha\":\"senha-do-cleber-123\"}'

curl.exe -i -X POST http://localhost:8000/usuarios -H "Cookie: $sessao" `
  -H "Content-Type: application/json" `
  -d '{\"nome\":\"Recepcao Tarde\",\"email\":\"recepcao@hotel.com.br\",\"perfil\":\"recepcao\",\"senha\":\"senha-da-recepcao-123\"}'
```

**Esperado**: `201` nas duas, sem a senha no corpo. Repetir a primeira devolve `409`. Perfil
`supervisor` devolve `422`.

## Cenário 7 — Cada perfil no seu lugar

Autentique como `cleber@hotel.com.br` e guarde o cookie em `$staff`; autentique como
`recepcao@hotel.com.br` e guarde em `$recepcao`.

```powershell
curl.exe -i -X POST http://localhost:8000/usuarios -H "Cookie: $recepcao" `
  -H "Content-Type: application/json" `
  -d '{\"nome\":\"X\",\"email\":\"x@hotel.com.br\",\"perfil\":\"staff\",\"senha\":\"senha-qualquer-123\"}'

curl.exe -i http://localhost:8000/sessoes -H "Cookie: $staff"
curl.exe -i http://localhost:8000/sessoes -H "Cookie: $recepcao"
```

**Esperado**: `403` para a recepção cadastrando usuário, `403` para o staff listando sessões, `200`
para a recepção listando — com as três sessões ativas e nenhum token à vista.

## Cenário 8 — Celular extraviado

```powershell
curl.exe -i -X DELETE http://localhost:8000/sessoes/<id da sessao do staff> -H "Cookie: $recepcao"
curl.exe -i http://localhost:8000/sessoes/atual -H "Cookie: $staff"
curl.exe -i http://localhost:8000/sessoes/atual -H "Cookie: $recepcao"
```

**Esperado**: `204` na revogação; `401` imediato para o staff, sem qualquer espera; `200` para a
recepção — revogar uma sessão não toca as outras. Revogar a mesma novamente devolve `204`.

## Cenário 9 — Desligamento derruba o acesso

Autentique o staff de novo em dois "dispositivos" diferentes, então:

```powershell
curl.exe -i -X DELETE http://localhost:8000/usuarios/<id do staff> -H "Cookie: $sessao"
```

**Esperado**: `204`; as duas sessões do staff passam a responder `401`; e nova autenticação com a
senha correta também é recusada com `401`.

Tentar desativar o próprio gestor autenticado devolve `409`.

---

## Suíte automatizada

```powershell
pytest testes/unitarios -q        # rapido, durante o ciclo de TDD
pytest                            # tudo
$env:EXIGIR_POSTGRES = "1"; pytest   # verificacao final: pular teste de banco vira falha
```

**Esperado**: tudo verde, incluindo os testes herdados da F0.2 — em especial o de conformidade do
esquema, que agora compara também a tabela de sessão entre o banco migrado e `docs/04-schema.sql`.

Dois testes merecem atenção na leitura do resultado:

| Teste | O que ele protege |
| --- | --- |
| Varredura de rotas protegidas | Falha se qualquer rota fora da lista pública deixar de exigir sessão. É a guarda das fatias futuras |
| Conformidade do esquema | Falha se a migração e o documento divergirem em qualquer sentido |

---

## Verificação final da entrega

```powershell
docker compose down -v
docker compose up -d
alembic upgrade head
$env:EXIGIR_POSTGRES = "1"; pytest
python -m app.bootstrap --nome-hotel "Hotel Exemplo" --telefone-whatsapp "+5511999999999" `
                        --nome-gestor "Thiago Feitosa" --email-gestor "gestor@hotel.com.br"
```

Do volume descartado ao primeiro login, sem nenhum passo manual no banco. É a SC-001 sendo
verificada de ponta a ponta, e não apenas afirmada.
