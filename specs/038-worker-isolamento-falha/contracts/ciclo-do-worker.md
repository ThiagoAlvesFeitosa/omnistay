# Contrato: ciclo do worker

Fonte: `worker/__main__.py`.

## `executar_ciclo`

Ordem, cada item isolado:

1. Passagem de mensagens (`processar_uma_passagem_na_engine`)
2. Verificar cadastros (lembretes / silêncio)
3. Verificar boas-vindas
4. Verificar pulsos
5. Verificar coletas de mercado
6. Verificar retenção (expurgo)

Falha em um MUST NOT pular os seguintes **nem** os anteriores já
feitos. Log da etapa: identificador da etapa + nome da exceção.
Sem mensagem, sem payload, sem CPF.

Cadência: no modo contínuo, (2)–(6) continuam no intervalo horário
já existente. A passagem continua a cada `--intervalo-segundos`.

## Flags pontuais (sem mudança de significado)

| Flag | Efeito |
| --- | --- |
| `--uma-passagem` | Só a passagem; encerra |
| `--verificar-cadastros` etc. | Só aquela rotina; encerra |

Isolamento entre rotinas **não** se aplica a uma flag pontual (há
uma só etapa). Testes da US3 usam `executar_ciclo`, não o `while True`.

## O que MUST NOT existir

- Segundo processo só para expurgo
- Redis / APScheduler / fila nova
- Relançar a exceção da etapa para fora do ciclo contínuo
