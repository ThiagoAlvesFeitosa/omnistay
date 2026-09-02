# Roteiro da jornada — teste, capturas e ensaio da demonstração

**Para que serve:** percorrer o sistema inteiro uma vez, como um hóspede real, conferir que a IA
responde de verdade e capturar as telas para o documento e o vídeo. Leva uns 20 minutos.

**Atualizado em 02/09/2026:** agora contra o **banco em nuvem** e usando o **painel**, não o
`/docs`. As 16 telas existem.

---

## Preparação do ambiente

### 1. Refazer o build do painel

O build atual pode estar anterior às últimas telas.

```powershell
cd frontend
npm run build
cd ..
```

### 2. Subir a API

```powershell
uv run uvicorn app.main:app --reload
```

### 3. Subir o worker, em outro terminal

```powershell
uv run python -m worker
```

> **O worker precisa ficar rodando.** É ele que envia as mensagens. Sem ele, nada sai da fila.

### 4. Conferir que está na nuvem

```powershell
uv run python -c "from app.config import obter_configuracao; print(obter_configuracao().database_url.split('@')[-1].split('?')[0])"
```

Tem que aparecer o endereço do Neon. Se aparecer `localhost`, feche o terminal e abra outro — uma
sessão anterior pode ter deixado a variável antiga na memória.

### 5. Abrir as duas abas

| Aba | Endereço | Quem você é |
| --- | --- | --- |
| **1** | `http://localhost:8000/app` | O hotel — recepção e gestão |
| **2** | `http://localhost:8000/app/simulador` | O hóspede |

---

## Parte 1 — Preparação dos dados (uma vez só)

### 1.1 Entrar como gestor

Aba 1 → login com `thiago@hotel.com.br` e a senha do bootstrap.

### 1.2 Criar o usuário da recepção

Tela **Usuários** → novo usuário:

- Nome: `Cleber Rocha`
- E-mail: `cleber@hotel.com.br`
- Perfil: `recepcao`
- Senha: `recepcao2026demo`

> O gestor não cadastra reserva — só a recepção. É decisão de projeto, e vale mencionar no vídeo:
> autoridade e operação são papéis diferentes.

### 1.3 Entrar como recepção

Sair e entrar de novo, agora com `cleber@hotel.com.br`.

### 1.4 Cadastrar o catálogo

Tela **Catálogo** → quatro itens. É a única fonte que a IA pode usar.

| Categoria | Título | Conteúdo |
| --- | --- | --- |
| horário | Café da manhã | Servido das 7h às 10h no salão térreo. Aos domingos até as 11h. |
| horário | Piscina | Aberta das 8h às 22h. Crianças devem estar acompanhadas. |
| serviço | Lavanderia | Entrega em até 24 horas. Pedidos até as 18h saem no dia seguinte. |
| regra | Animais | Não aceitamos animais de estimação. |

📸 **Capture esta tela.**

### 1.5 Cadastrar um item vendável

Tela **Itens vendáveis** → `Caipirinha`, R$ 28,00.

📸 **Capture esta tela** — é onde se explica que a IA identifica o item e o sistema busca o preço.

### 1.6 Preencher o recado de boas-vindas

Tela **Recado de boas-vindas** → os quatro campos:

- Café: `das 7h às 10h no salão térreo`
- Wi-fi: `rede HotelExemplo, senha na recepção`
- Saída até: `12h`
- Convite: `Quer saber dos nossos serviços, do cardápio ou dos horários? É só perguntar por aqui.`

---

## Parte 2 — A jornada

### Passo 1 · Cadastrar a reserva

Aba 1 → **Fila do dia** → **Nova reserva**

- Nome: `Marina Duarte`
- Telefone: `11987654321`
- Entrada: hoje · Saída: daqui a dois dias

📸 **Capture a fila do dia** com a reserva aparecendo.

### Passo 2 · A mensagem de coleta chega

Aba 2 → atualize. A reserva aparece na lista; clique nela.

✅ **Confira:** a mensagem avisa que o atendimento é feito por assistente virtual?

📸 **Capture.**

### Passo 3 · A hóspede responde a ficha

Aba 2 → escreva como se fosse a Marina, numa mensagem só:

```
Marina Duarte Fonseca, gerente de contas, nasci em 14/03/1992,
CPF 123.456.789-00, moro na Rua das Acacias 220 apto 71,
CEP 04567-000, Sao Paulo
```

### Passo 4 · Conferir a ficha extraída

Aba 1 → **Fila do dia** → abrir a reserva → **Ficha**

✅ **Confira:** os campos foram separados certo?

📸 **Capture.** Esta tela prova a extração pela IA.

### Passo 5 · Confirmar a chegada

Aba 1 → **Fila do dia** → botão **Confirmar chegada**

### Passo 6 · O recado de boas-vindas

Aba 2 → atualize. Chega a confirmação com café, wi-fi, horário de saída e o convite.

📸 **Capture.**

### Passo 7 · A conversa — o teste principal

Aba 2 → pergunte uma de cada vez:

| Pergunta | Resposta esperada |
| --- | --- |
| *que horas abre a piscina?* | 8h às 22h |
| *vocês aceitam cachorro?* | Não aceitamos animais |
| *que horas é o desjejum?* | 7h às 10h — **paráfrase**, o catálogo diz "café da manhã" |
| **_tem berço no quarto?_** | **"a recepção vai te atender"** — e nada mais |

📸 **Capture as duas últimas.** São as mais fortes do vídeo: uma mostra que a IA entende
paráfrase; a outra, que ela **não inventa**.

> Se a IA inventar resposta sobre berço, a regra de fidelidade falhou. Anote e me avise.

Aba 1 → fila do dia deve mostrar **precisa da recepção**. Abrir **Estadia** (não mais “Ver ficha”).
A conversa vem no topo; os cadastrais ficam atrás de **ver dados cadastrais**.

Escreva a resposta livre (`Sim, temos berço no quarto.`) e **Enviar**. O histórico mostra
**enviando**, depois **enviada**. Se o canal falhar, aparece **falhou** com **nova tentativa
marcada** — o texto não some. Clique duplo no Enviar não duplica a mensagem.

✅ **Confira:** o campo permanece visível se a janela de 24h estiver fechada, com o motivo na tela.
✅ **Confira:** responder **não** marca o chamado como resolvido.

Aba 2 → o hóspede recebe o mesmo texto.

📸 **Capture a Estadia com a conversa no topo.**

### Passo 8 · Um pedido de serviço

Aba 2: `manda uma toalha extra por favor`

Aba 1 → **Chamados e pedidos**. 📸 **Capture.**

### Passo 9 · Um consumo faturável

Aba 2: `quero uma caipirinha`

Aba 1 → **Consumos a lançar** — deve aparecer com **R$ 28,00**.

✅ **Confira:** o valor da conversa é igual ao da fila? Tem que ser — a IA identifica o item, o
sistema busca o preço.

📸 **Capture.**

### Passo 10 · A tela da equipe, no celular

Abra `http://localhost:8000/app` no celular, ou reduza a janela do navegador, e entre com um
usuário de perfil `staff`.

📸 **Capture** — mostra o Alert Center substituindo o app da equipe.

### Passo 11 · A saída

Aba 1 → **Fila do dia** → **Abrir saída** → conferir a lista de pedidos feitos pelo chat →
**Confirmar saída**

✅ **Confira:** aparece o aviso de consumo pendente antes de confirmar?
✅ **Confira:** em nenhum lugar da tela aparece a palavra "extrato" ou "conta"?

📸 **Capture.**

Aba 2 → chegam a pesquisa de saída e a lista de pedidos.

### Passo 12 · A visão da gestão

Sair, entrar como gestor, abrir o **Painel**.

✅ **Confira:** só números agregados, nenhum nome de hóspede.

📸 **Capture** — é a prova de "números, não pessoas".

---

## Capturas necessárias, em resumo

| # | Tela | Onde entra |
| --- | --- | --- |
| 1 | Catálogo | Documento — o que alimenta a IA |
| 2 | Itens vendáveis | Documento — a IA não escreve preço |
| 3 | Fila do dia | Documento e slides — a tela principal |
| 4 | Ficha extraída | Documento — a IA lendo texto livre |
| 5 | Conversa com resposta pelo catálogo | **Slides e vídeo** |
| 6 | Conversa com pergunta fora do catálogo | **Slides e vídeo** — não inventa |
| 7 | Chamados e pedidos | Documento |
| 8 | Consumos a lançar | Documento |
| 9 | Tela da equipe no celular | Slides |
| 10 | Saída com a lista de pedidos | Documento |
| 11 | Painel da gestão | Documento |

---

## O que anotar

**Texto a ajustar** — mensagem longa, tom errado, palavra esquisita. É a maioria, e é barato.

**Comportamento errado** — IA inventando, preço divergente, mensagem que não chega, campo no lugar
errado. Estes viram tarefa.

---

## Se algo não acontecer

| Sintoma | Causa mais provável |
| --- | --- |
| Nenhuma mensagem chega | O worker não está rodando |
| Painel não abre em `/app` | Falta rodar `npm run build` no `frontend/` |
| `403` ao cadastrar reserva | Logado como gestor, não como recepção |
| `401` em tudo | Sessão caiu — entre de novo |
| Tudo responde "a recepção vai te atender" | `LLM_MODO` não está `real`, ou a chave do Gemini falhou |
| Conecta no banco errado | `$env:DATABASE_URL` de uma sessão anterior — abra terminal novo |

---

## Antes de gravar o vídeo

- [ ] Trocar a senha do Neon (*Roles → Reset password*)
- [ ] Trocar a chave do Gemini (apagar e gerar outra no AI Studio)
- [ ] Fechar qualquer janela que mostre o `.env`
- [ ] Conferir que o terminal visível não tem a string de conexão na tela
