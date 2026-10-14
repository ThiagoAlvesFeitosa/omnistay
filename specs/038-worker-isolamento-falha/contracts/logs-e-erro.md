# Contrato: log e campo de erro

Artigo VIII. Teste obrigatório: exceção cuja mensagem contém um CPF
(e, se couber, SQL com parâmetros).

## Trabalho

`erro_ultima_tentativa` no caminho de isolamento = `type(exc).__name__`
(exemplo: `IntegrityError`). MUST NOT conter o CPF, a mensagem, o
SQL interpolado nem o payload.

Códigos estáveis já usados na falha de envio (`falha_envio`, …)
permanecem nesse caminho; esta fatia não os reescreve.

## Evento de log

Campos permitidos: `id_trabalho`, `tipo`, `id_hotel`, nome da
exceção, etapa do ciclo (`passagem`, `cadastros`, …), quantidade
processada.

Campos proibidos: conteúdo de mensagem, telefone, nome de hóspede,
CPF, `str(exc)`, `params` de cursor, corpo de webhook.

## Engine

`hide_parameters=True` em `obter_engine()` (API e worker passam a
compartilhar). O `create_engine` direto do worker some.

## Tratador

Nenhum `except Exception as e: logger.exception(e)` no consumidor
nem no ciclo que imprima traceback com parâmetros. `logger.exception`
só se a mensagem formatada pelo projeto já for o nome da classe +
identificadores.
