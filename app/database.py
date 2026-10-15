from functools import lru_cache

from sqlalchemy import Engine, create_engine

from app.config import obter_configuracao


def _criar_engine(timeout_segundos: float) -> Engine:
    configuracao = obter_configuracao()
    timeout_milissegundos = int(timeout_segundos * 1000)
    return create_engine(
        configuracao.database_url,
        pool_pre_ping=False,
        hide_parameters=True,
        connect_args={
            "connect_timeout": max(1, int(timeout_segundos)),
            "options": f"-c statement_timeout={timeout_milissegundos}",
        },
    )


@lru_cache
def obter_engine() -> Engine:
    return _criar_engine(obter_configuracao().health_db_timeout_seconds)


@lru_cache
def obter_engine_do_worker() -> Engine:
    return _criar_engine(obter_configuracao().worker_statement_timeout_seconds)
