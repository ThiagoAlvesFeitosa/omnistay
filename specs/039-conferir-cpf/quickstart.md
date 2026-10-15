# Quickstart: conferir o CPF

Validação local da F9.2. Implementação e lista de testes ficam em
`tasks.md` (ainda não gerado).

## Pré-requisitos

- PostgreSQL 16 da suíte (mesmo `DATABASE_URL` do `.env`)
- `python -m pytest` e `npm test` no `frontend/` como no restante do
  repositório
- Portas falsas: não chamar Gemini nem WhatsApp

Contratos: [conferir-numero.md](./contracts/conferir-numero.md),
[coleta.md](./contracts/coleta.md),
[put-ficha.md](./contracts/put-ficha.md),
[superficie-painel.md](./contracts/superficie-painel.md),
[migracao-e-logs.md](./contracts/migracao-e-logs.md).
Modelo: [data-model.md](./data-model.md).

## Setup

```bash
# na raiz
alembic upgrade head   # inclui 0027 (forma canônica de CPF)
```

Não há variável de ambiente nova. Não há chave nova em
`parametro_hotel`.

## O que tem de ficar verde

```bash
pytest testes/unitarios/modulos/conversa/test_validacao_ficha.py -q
pytest testes/unitarios/modulos/hospedagem/test_completar_ficha.py -q
pytest testes/integracao/test_alterar_ficha.py testes/integracao/test_interpretar_ficha.py -q
cd frontend && npm test -- --run src/painel/TelaFicha.test.tsx src/painel/ficha.test.ts
```

Nomes esperados (comportamento, em português), no espírito:

- CPF com dígitos que fecham, com ou sem pontuação, grava onze dígitos
- CPF com dígito trocado não entra na coleta; ficha parcial; sem
  mensagem nova
- onze dígitos iguais são reprovados
- PUT com CPF reprovado não grava nenhum campo daquele salvamento
- RG continua aceito com o número que os testes já usam
- log da recusa e da migração não trazem o número
- migração converte o isolado e deixa o par com a escrita original
- painel mostra e copia `000.000.000-00`; aviso no campo; rascunho
  conservado após `422`

## Sinais de pronto

- Simulador: ficha com CPF inválido não completa o cadastro sozinha
- Painel: salvar CPF inválido mostra recado no campo e não perde o
  que foi digitado nos outros
- `GET` da ficha traz onze dígitos quando o valor é canônico
- nenhum teste chama rede externa
