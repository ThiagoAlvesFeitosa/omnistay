from functools import lru_cache

from sqlalchemy import Engine, create_engine

from app.config import obter_configuracao


@lru_cache
def obter_engine() -> Engine:
    configuracao = obter_configuracao()
    timeout_segundos = configuracao.health_db_timeout_seconds
    timeout_milissegundos = int(timeout_segundos * 1000)

    return create_engine(
        configuracao.database_url,
        pool_pre_ping=False,
        connect_args={
            "connect_timeout": max(1, int(timeout_segundos)),
            "options": f"-c statement_timeout={timeout_milissegundos}",
        },
    )
