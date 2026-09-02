# Quickstart — validar painel da gestão, mercado, usuários e retenção

Roteiro depois de `/speckit-implement`. Contratos:
[api-indicadores.md](./contracts/api-indicadores.md),
[api-usuarios.md](./contracts/api-usuarios.md),
[api-reusada.md](./contracts/api-reusada.md),
[superficie-painel.md](./contracts/superficie-painel.md),
[superficie-mercado.md](./contracts/superficie-mercado.md),
[superficie-usuarios.md](./contracts/superficie-usuarios.md),
[superficie-retencao.md](./contracts/superficie-retencao.md),
[destinos-e-perfis.md](./contracts/destinos-e-perfis.md),
[logs.md](./contracts/logs.md).
Modelo: [data-model.md](./data-model.md).

Comandos na raiz do repositório. Sem PMS, sem WhatsApp, sem visita
à fonte.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. Propriedade e usuários dos três perfis
como no quickstart da F0.3 / F8.1.

```powershell
pytest testes/unitarios -q
pytest testes/integracao -q -k "indicador or usuario or retencao or mercado"
cd frontend
npm test
```

`npm test` cobre as quatro telas e a casca. Pytest cobre os
números puros, a lista sem hash e os prazos no comprovante.

---

## 1. Painel: quatro números, zero pessoas

Uvicorn na API. No `frontend/`:

```powershell
npm run dev
```

Abrir `http://127.0.0.1:5173/app/entrar`. Entrar como gestão.
Casa: **Painel**.

Quatro números: chegadas hoje, hospedados, chamados em aberto,
consumo a lançar. Sem nome de hóspede. Sem gráfico.

Hotel sem movimento: zeros, não “falha”.

Recepção no endereço `/app/indicadores`: cai na fila; não vê os
números. Staff: cai em meus chamados.

---

## 2. Mercado: falha marcada, sem cadastro

Menu **Mercado**. Concorrentes com preço/nota datados. Coleta
falhada distinguível; valor antigo com data antiga se houver
sucesso anterior. Sem linha da própria casa. Sem criar
concorrente.

Clique num concorrente: histórico com falha ≠ preço zero.

---

## 3. Usuários: criar, desativar, sem reativar

Menu **Usuários**. Lista com ativos e desativados. **+ Novo**:
perfil e senha com ao menos 12 caracteres. Senha curta: recusa
nesta tela.

**Desativar** outro funcionário: permanece na lista marcado. A
própria linha: sem desativar. Sem **Reativar**. Sem revogar
sessão.

Criar de novo com o e-mail do desativado: recusa.

---

## 4. Retenção: data, tipo, quantidade

Menu **Retenção de dados**. Prazos vigentes (ou “não
configurado”). Execuções com data e quantidades, inclusive zero.
Sem botão de expurgar agora. Sem dado de hóspede.

---

## 5. Falha de leitura

Desligar a API com Painel aberto e **Tentar de novo**: o painel
permanece e **não** mostra o estado de zeros honestos.

---

## Fora deste roteiro

CRUD de concorrente. Reativar usuário. Tela de sessões da
recepção. Gráfico de 30 dias. Fichas antecipadas. Nota média.
Módulos por propriedade. Personalidade da assistente.
