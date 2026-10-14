"""A engine nao interpola parametros em mensagem de erro."""


def test_engine_esconde_parametros_da_consulta(limpar_caches_de_configuracao):
    from app.database import obter_engine

    obter_engine.cache_clear()
    engine = obter_engine()
    assert engine.hide_parameters is True
    obter_engine.cache_clear()
