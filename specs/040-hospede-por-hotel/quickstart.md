# Quickstart: cada hóspede pertence a um hotel

Validação local da F9.3. Implementação e lista de testes ficam em
`tasks.md` (ainda não gerado).

## Pré-requisitos

- PostgreSQL 16 da suíte (mesmo `DATABASE_URL` do `.env`)
- `python -m pytest` e `npm test` no `frontend/` como no restante
- Portas falsas: não chamar Gemini nem WhatsApp

Contratos: [put-ficha.md](./contracts/put-ficha.md),
[superficie-painel.md](./contracts/superficie-painel.md),
[migracao-e-logs.md](./contracts/migracao-e-logs.md),
[artigo-xiv.md](./contracts/artigo-xiv.md),
[consentimento-e-expurgo.md](./contracts/consentimento-e-expurgo.md).
Modelo: [data-model.md](./data-model.md).

## Setup

```bash
# na raiz
alembic upgrade head   # inclui 0028 (hospede.id_hotel)
```

Não há variável de ambiente nova. Não há chave nova em
`parametro_hotel`. Não há operação nova.

## O que tem de ficar verde

```bash
pytest testes/unitarios/modulos/hospedagem/test_completar_ficha.py -q
pytest testes/unitarios/modulos/hospedagem/test_hospede_migracao.py -q
pytest testes/integracao/test_alterar_ficha.py testes/integracao/test_artigo_xiv.py testes/integracao/test_retencao.py -q
cd frontend && npm test -- --run src/painel/TelaFicha.test.tsx
```

Nomes esperados (comportamento, em português), no espírito:

- dois hotéis gravam o mesmo documento
- no mesmo hotel o PUT recusa e o aviso nomeia, com caminho para
  a ficha desta casa, sem o documento
- o aviso nunca cita o outro hotel
- consentimento e expurgo do A não alcançam o B
- migração atribui; parte o multi-hotel; órfão com um hotel fica
  dele
- walker estrutural: `hospede` reprova sem a coluna e passa no
  `head`; `evento_webhook` é exceção nomeada
- log da recusa e da migração sem número de documento
- política sem operação nova; `ROTAS_PUBLICAS` iguais

## Sinais de pronto

- Painel: salvar documento já usado na casa mostra o nome e o
  link da ficha já gravada; o rascunho permanece
- Dois hotéis de teste: o mesmo CPF nos dois, sem `409` cruzado
- `GET` de consentimento do outro hotel: `404`
- nenhum teste chama rede externa
