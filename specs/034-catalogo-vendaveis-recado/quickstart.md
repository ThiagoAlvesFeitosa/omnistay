# Quickstart — validar catálogo, itens vendáveis e recado

Roteiro depois de `/speckit-implement`. Contratos:
[api-reusada.md](./contracts/api-reusada.md),
[superficie-catalogo.md](./contracts/superficie-catalogo.md),
[superficie-vendaveis.md](./contracts/superficie-vendaveis.md),
[superficie-boas-vindas.md](./contracts/superficie-boas-vindas.md),
[destinos-e-perfis.md](./contracts/destinos-e-perfis.md),
[logs.md](./contracts/logs.md).
Modelo: [data-model.md](./data-model.md).

Comandos na raiz do repositório. Sem PMS, sem WhatsApp.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. Propriedade e usuários dos três perfis
como no quickstart da F0.3 / F8.1. A suíte Vitest não depende de
fato cadastrado à mão.

```powershell
pytest testes/unitarios -q
pytest testes/integracao -q -k "catalogo or vendavel or boas_vindas or sessao"
cd frontend
npm test
```

A suíte Python continua verde **sem** teste novo de regra de
catálogo, preço ou recado. `npm test` é o portão desta fatia.

---

## 1. Catálogo deixa de ser só título

Uvicorn na API. No `frontend/`:

```powershell
npm run dev
```

Abrir `http://127.0.0.1:5173/app/entrar`. Entrar como recepção.
Menu **Catálogo**.

Abas das cinco categorias. **+ Novo item** na aba visível: título
e conteúdo; nasce ativo. **Desativar** mantém a linha marcada;
não há apagar. **Reativar** devolve à lista ativa.

Staff no mesmo endereço `/app/catalogo`: não vê a lista; cai na
casa do papel.

Gestão: vê Catálogo no menu, lê a lista, **não** vê novo / editar
/ desativar.

---

## 2. Item vendável: preço próprio, proxy no ar

Menu **Itens vendáveis**. Cadastrar nome e preço em campos
separados. Alterar **só** o preço: o nome permanece. Desativar;
reativar.

Nome duplicado entre ativos: recusa visível ao salvar.

Se a lista não carregar no `npm run dev` enquanto a API responde
em `http://127.0.0.1:8000/itens-vendaveis`, o proxy Vite não
encaminhou o prefixo — é o ajuste desta fatia em
`frontend/vite.config.ts`.

Gestão lê; staff recusado.

---

## 3. Recado: quatro campos, recusa ao salvar

Menu **Recado de boas-vindas**. Os quatro campos (café, wi-fi,
horário de saída, convite). **Salvar** válido atualiza na hora e
**não** manda mensagem ao hóspede.

Colar quebra de linha ou cinco espaços seguidos e salvar: aviso
nesta tela; valores anteriores intactos. Não espera o check-in.

Gestão lê os quatro; sem **Salvar**.

---

## 4. Falha de leitura

Desligar a API com Catálogo aberto e **Tentar de novo**: o painel
permanece e **não** mostra o estado de lista vazia.

---

## Fora deste roteiro

Indicadores da gestão, mercado, usuários, retenção (F8.7).
Personalidade da assistente. Prévia do recado com nome de
hóspede. Coluna descrição no item vendável.
