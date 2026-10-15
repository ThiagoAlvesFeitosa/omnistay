# Contrato: isolamento da passagem

Fonte: `worker/consumidor.py`, `app/fila/service.py`.

## Passagem (`processar_uma_passagem`)

1. Reclama o próximo elegível (`pendente`, tipo conhecido, espera
   vencida).
2. Despacha como hoje.
3. Passos 1–2 de **um** trabalho vivem num savepoint.
4. Sucesso: savepoint confirma; o trabalho permanece `concluido` se o
   handler marcou.
5. Exceção **qualquer**: savepoint desfaz o efeito daquele trabalho;
   chama `registrar_falha_de_envio` com
   `codigo_erro = type(exc).__name__`, `id_hotel` do trabalho,
   `tentativas_atuais` do snapshot reclamado; **não** relança; segue
   o próximo da mesma passagem.
6. Fila só com `falha`: zero claims; retorno 0; processo no ar.

Tipo desconhecido: continua `falha` com código estável
`tipo_desconhecido` (não é nome de exceção).

## Teto e espera

Mesmo contrato da falha de envio:

- teto = `tentativas_maximas` da propriedade do trabalho
- ausente/ilegível = 5
- abaixo do teto → `pendente`, `proxima_tentativa_em = backoff_apos(novas)`
- no teto → `status = falha`, não reclamável

`backoff_apos(3)` é **depois** de `backoff_apos(1)` (já testado).

## O que a passagem MUST NOT fazer

- Encerrar o processo.
- Abortar os demais trabalhos da mesma passagem.
- Desfazer `concluido` de outro trabalho já confirmado no savepoint
  anterior.
- Gravar `str(exc)` ou parâmetros SQL em `erro_ultima_tentativa`.

## Tempo por consulta

Conexão do worker = `obter_engine_do_worker()`:
`worker_statement_timeout_seconds` (padrão 30). A API permanece em
`obter_engine()` com `health_db_timeout_seconds` (padrão 1). As duas
escondem parâmetros. Estouro é exceção: mesmo ciclo de tentativa,
registro pelo nome da classe, sem parâmetros.

`processar_uma_passagem_na_engine` abre **uma transação por
trabalho** (`limite=1`); o savepoint permanece dentro de cada uma.
