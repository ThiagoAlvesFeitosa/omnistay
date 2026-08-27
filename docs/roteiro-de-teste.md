# Roteiro de teste da jornada — e ensaio da demonstração

**Para que serve:** percorrer o sistema inteiro uma vez, como um hóspede real, e conferir que a
IA responde de verdade. Leva uns 15 minutos.

**Quando fazer:** depois da F7.1 (adaptador de IA). Antes dela, tudo responde "a recepção vai te
atender" e o teste não diz nada.

**Enquanto o painel não existe, o `/docs` é o painel.**

---

## Antes de começar

Três terminais abertos, na pasta `omnistay`:

```powershell
docker compose up -d
```

```powershell
uv run uvicorn app.main:app --reload
```

```powershell
uv run python -m worker
```

> **O worker precisa ficar rodando.** É ele que envia as mensagens. Sem ele, nada sai da fila e
> você vai achar que está quebrado.

Duas abas no navegador:

| Aba | Endereço | Quem você é |
| --- | --- | --- |
| **1** | `http://localhost:8000/docs` | A recepção |
| **2** | `http://localhost:8000/demo/` | O hóspede |

### Como usar o `/docs`

1. Clique no nome do endpoint para abrir
2. Clique em **Try it out** (canto direito)
3. Edite o texto do corpo da requisição
4. Clique em **Execute**
5. A resposta aparece abaixo, em **Server response**. Código **200** ou **201** é sucesso

O login guarda um cookie na aba. Depois dele, todos os outros endpoints funcionam sem repetir.

---

## Parte 1 — Preparação (uma vez só)

Sem isto a IA não tem o que responder.

### 1.1 Entrar como gestor

**`POST /sessoes`**

```json
{
  "email": "thiago@hotel.com.br",
  "senha": "sua-senha-de-12-caracteres"
}
```

### 1.2 Criar o usuário da recepção

**`POST /usuarios`** — o gestor não pode cadastrar reserva; a recepção pode.

```json
{
  "nome": "Cleber Rocha",
  "email": "cleber@hotel.com.br",
  "perfil": "recepcao",
  "senha": "recepcao2026demo"
}
```

### 1.3 Entrar como recepção

**`POST /sessoes`**

```json
{
  "email": "cleber@hotel.com.br",
  "senha": "recepcao2026demo"
}
```

> Daqui em diante você é a recepção. Todo o resto do roteiro usa este login.

### 1.4 Cadastrar o catálogo

**`POST /catalogo`** — quatro vezes, uma para cada item. É a **única** fonte que a IA pode usar.

```json
{ "categoria": "horario", "titulo": "Cafe da manha", "conteudo": "Servido das 7h as 10h no salao terreo. Aos domingos ate as 11h." }
```

```json
{ "categoria": "horario", "titulo": "Piscina", "conteudo": "Aberta das 8h as 22h. Criancas devem estar acompanhadas." }
```

```json
{ "categoria": "servico", "titulo": "Lavanderia", "conteudo": "Entrega em ate 24 horas. Pedidos ate as 18h saem no dia seguinte." }
```

```json
{ "categoria": "regra", "titulo": "Animais", "conteudo": "Nao aceitamos animais de estimacao." }
```

### 1.5 Cadastrar um item vendável

**`POST /itens-vendaveis`**

```json
{ "nome": "Caipirinha", "preco_atual": 28.00 }
```

### 1.6 Preencher o recado de boas-vindas

**`PUT /propriedade/boas-vindas`**

```json
{
  "cafe": "das 7h as 10h no salao terreo",
  "wifi": "rede HotelExemplo, senha na recepcao",
  "checkout": "12h"
}
```

---

## Parte 2 — A jornada

### Passo 1 · A recepção cadastra a reserva

**Aba 1 · `POST /reservas`**

```json
{
  "nome": "Marina Duarte",
  "telefone": "11987654321",
  "data_checkin_prevista": "2026-08-27",
  "data_checkout_prevista": "2026-08-29"
}
```

Anote o `id_reserva` que voltar na resposta — você vai usar depois.

### Passo 2 · A mensagem de coleta chega

**Aba 2** — atualize a página. A reserva aparece na lista à esquerda. Clique nela.

> Se a mensagem não apareceu, espere alguns segundos e atualize de novo. O worker trabalha em
> ciclos, não instantaneamente.

**Confira:** a mensagem avisa que o atendimento é por assistente virtual? (a partir da F7.1)

### Passo 3 · A hóspede responde a ficha

**Aba 2** — escreva como se fosse a Marina, tudo numa mensagem só:

```
Marina Duarte Fonseca, gerente de contas, nasci em 14/03/1992,
CPF 123.456.789-00, moro na Rua das Acacias 220 apto 71,
CEP 04567-000, Sao Paulo
```

### Passo 4 · Conferir a ficha extraída

**Aba 1 · `GET /reservas/{id_reserva}/ficha`**

**Confira:** os campos foram separados certo? Nome, profissão, nascimento, documento, endereço,
CEP e cidade nos lugares corretos?

> Este passo é o que testa a extração pela IA. Se vier tudo vazio ou embaralhado, é problema de
> prompt — anote e siga em frente.

### Passo 5 · Confirmar a chegada

**Aba 1 · `POST /reservas/{id_reserva}/chegada`** — corpo vazio `{}`

### Passo 6 · O recado de boas-vindas

**Aba 2** — atualize. Deve chegar a confirmação com café, wi-fi e horário de saída.

### Passo 7 · A conversa — o teste principal

**Aba 2** — pergunte uma de cada vez, esperando a resposta:

| Pergunta | Resposta esperada |
| --- | --- |
| *que horas abre a piscina?* | 8h às 22h |
| *vocês aceitam cachorro?* | Não aceitamos animais |
| *quanto tempo demora a lavanderia?* | Até 24 horas |
| *que horas é o desjejum?* | 7h às 10h — **paráfrase**, o catálogo diz "café da manhã" |
| **_tem berço no quarto?_** | **"a recepção vai te atender"** — e nada mais |

> A última é a mais importante do roteiro. Berço **não está no catálogo**. Se a IA inventar uma
> resposta, a regra de fidelidade falhou — e isso é problema sério, não detalhe. Anote e me avise.

### Passo 8 · Um pedido de serviço

**Aba 2:** `manda uma toalha extra por favor`

**Aba 1 · `GET /solicitacoes`** — deve aparecer como tipo serviço.

### Passo 9 · Um consumo faturável

**Aba 2:** `quero uma caipirinha`

**Aba 1 · `GET /consumos/pendentes`** — deve aparecer com **R$ 28,00**.

> **Confira o valor.** Ele tem que vir do item cadastrado, não de um número que a IA escreveu.
> Se o preço na conversa for diferente do preço aqui, é o problema que a decisão de "a IA nunca
> escreve preço" existe para evitar.

### Passo 10 · A saída

**Aba 1 · `POST /reservas/{id_reserva}/saida`** — corpo vazio `{}`

**Aba 2** — devem chegar **duas** mensagens: a pesquisa de saída e a lista de pedidos feitos pelo
chat.

> **Confira o vocabulário:** a lista não pode ser chamada de "extrato" nem de "conta" em lugar
> nenhum.

---

## O que anotar enquanto percorre

Nem tudo que parecer estranho é defeito de código. Separe em duas listas:

**Texto a ajustar** — mensagem longa demais, tom errado, palavra esquisita. É a maioria, e é
barato de corrigir.

**Comportamento errado** — IA inventando resposta, preço divergente, mensagem que não chega,
campo extraído no lugar errado. Estes viram tarefa.

---

## Se algo não acontecer

| Sintoma | Causa mais provável |
| --- | --- |
| Nenhuma mensagem chega | O worker não está rodando |
| "Nenhuma reserva nesta casa" | Não há reserva cadastrada, ou você está logado noutro hotel |
| `403` ao cadastrar reserva | Você está logado como gestor, não como recepção |
| `401` em tudo | A sessão caiu — refaça o `POST /sessoes` |
| Tudo responde "a recepção vai te atender" | A F7.1 ainda não foi feita, ou `LLM_MODO` não está `real` |
| Erro de autenticação do modelo | Chave do Gemini errada ou expirada |
