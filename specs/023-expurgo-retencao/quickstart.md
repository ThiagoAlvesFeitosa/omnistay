# Quickstart — validar o Expurgo por Retenção

Roteiro depois de `/speckit-implement`. Contratos:
[agendador-e-retencao.md](./contracts/agendador-e-retencao.md),
[anonimizacao-e-exclusao.md](./contracts/anonimizacao-e-exclusao.md),
[api-de-comprovante.md](./contracts/api-de-comprovante.md),
[politica-de-autorizacao.md](./contracts/politica-de-autorizacao.md).
Modelo: [data-model.md](./data-model.md).

Comandos na raiz do repositório. Sem WhatsApp, sem React, sem PMS.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. Hotel + gestão como no quickstart da F0.3.
Migração desta fatia: `0021_expurgo_retencao`. Relógio da suíte injetável
(não espere doze meses reais).

```powershell
pytest testes/unitarios -q
pytest testes/integracao -q -k retencao
```

---

## 1. Semente dos prazos

Hotel novo (bootstrap) tem `meses_retencao_conteudo_livre = 12` e
`anos_retencao_ficha = 5`. Hotel migrado recebe as mesmas chaves na
`0021` (idempotente).

```sql
SELECT chave, valor FROM parametro_hotel
 WHERE id_hotel = :id
   AND chave IN ('meses_retencao_conteudo_livre', 'anos_retencao_ficha');
```

**Esperado:** `12` e `5`. Apagar a chave de meses e rodar a varredura:
0 mensagens marcadas; log `prazo_conteudo_ausente`; comprovante do dia
com `prazo_conteudo_ausente = true`. A chave de anos, se válida, ainda
apaga ficha vencida na mesma passagem.

---

## 2. Conteúdo livre vence; a linha fica

Reserva com `checkout_em` anterior a `agora` menos 12 meses, mensagem
com texto, comentário preenchido, descrição de solicitação, evento de
webhook com o mesmo `id_externo` da mensagem:

```powershell
python -m worker --verificar-retencao
```

Na suíte, `agora` avançado — não o relógio de parede.

**Esperado:** `conteudo`, `descricao` e `comentario` = `[anonimizado]`;
`payload` = `{"anonimizado": true}`; `classificacao_bruta` nula; eixos
e nota intactos; `COUNT(*)` de mensagem/solicitação/avaliação igual ao
de antes. `--uma-passagem` **não** faz isso. Segunda `--verificar-retencao`
no **mesmo** dia UTC: 0 tratamentos novos; um só comprovante.

Reserva com saída há 11 meses: texto original intacto.

---

## 3. Ficha some no prazo de cinco anos

Hóspede cuja única reserva tem `checkout_em` anterior a `agora` menos
5 anos, com consentimento:

**Esperado:** linha de `hospede` e de `consentimento` ausentes; reserva
ainda existe; `telefone_contato` = `anonimizado`. Hóspede com saída mais
recente, ou `checkout_em` nulo: ficha intacta.

---

## 4. Gestão lê o comprovante; recepção não

Com cookie de gestão, depois da passagem:

```powershell
curl.exe -s -b cookies-gestao.txt http://127.0.0.1:8000/retencao
```

**Esperado:** `200`, `execucoes` com instante e quantidades (zeros se
nada venceu). Cookie de recepção ou operação: `403`. Sem cookie: `401`.
`POST /retencao`: `405`. Log da consulta sem texto de hóspede.

Hotel B não vê a linha do hotel A.

---

## 5. Volume e log

Contar mensagens por intenção e solicitações por tipo **antes** e
**depois** da anonimização: iguais. Capturar log da passagem: há
`id_hotel` e quantidades; **não** há o texto original nem documento.
