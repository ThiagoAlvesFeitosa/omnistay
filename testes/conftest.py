import os

import pytest

DATABASE_URL_PADRAO = "postgresql+psycopg2://postgres:omnistay@localhost:5432/omnistay"


@pytest.fixture(scope="session", autouse=True)
def ambiente_de_teste() -> None:
    os.environ.setdefault("DATABASE_URL", DATABASE_URL_PADRAO)
    os.environ.setdefault("HEALTH_DB_TIMEOUT_SECONDS", "1")
    os.environ.setdefault("LOG_LEVEL", "INFO")


@pytest.fixture
def limpar_caches_de_configuracao():
    from app.config import obter_configuracao
    from app.database import obter_engine

    obter_configuracao.cache_clear()
    obter_engine.cache_clear()
    yield
    obter_configuracao.cache_clear()
    obter_engine.cache_clear()


@pytest.fixture
def cliente(ambiente_de_teste):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as cliente_de_teste:
        yield cliente_de_teste


def postgres_disponivel() -> bool:
    from sqlalchemy import create_engine, text

    try:
        engine = create_engine(
            os.environ.get("DATABASE_URL", DATABASE_URL_PADRAO),
            connect_args={"connect_timeout": 2},
        )
        with engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
