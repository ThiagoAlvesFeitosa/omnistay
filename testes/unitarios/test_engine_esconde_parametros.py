"""A engine nao interpola parametros em mensagem de erro."""


def test_engine_esconde_parametros_da_consulta(limpar_caches_de_configuracao):
    from app.database import obter_engine

    obter_engine.cache_clear()
    engine = obter_engine()
    assert engine.hide_parameters is True
    obter_engine.cache_clear()


def test_timeout_do_worker_e_trinta_por_padrao():
    from app.config import Configuracao

    assert Configuracao.model_fields["worker_statement_timeout_seconds"].default == 30.0


def test_engine_do_worker_esconde_parametros_e_nao_reusa_a_da_api(
    limpar_caches_de_configuracao,
):
    from app.database import obter_engine, obter_engine_do_worker

    obter_engine.cache_clear()
    obter_engine_do_worker.cache_clear()
    api = obter_engine()
    worker = obter_engine_do_worker()
    assert worker.hide_parameters is True
    assert api.hide_parameters is True
    assert worker is not api
    obter_engine.cache_clear()
    obter_engine_do_worker.cache_clear()
