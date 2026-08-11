import os
from functools import lru_cache

import pytest

from testes.suporte.politica_de_banco import (
    Acao,
    banco_exigido_pelo_ambiente,
    decidir_execucao,
)


@pytest.fixture(scope="session", autouse=True)
def ambiente_de_teste() -> None:
    os.environ.setdefault("HEALTH_DB_TIMEOUT_SECONDS", "1")
    os.environ.setdefault("LOG_LEVEL", "INFO")


def url_do_banco() -> str | None:
    """URL de conexao configurada, ou None quando nao ha nenhuma.

    A leitura passa pela configuracao da aplicacao, que ja considera ambiente e `.env`.
    Nenhum valor de conexao e embutido aqui: arquivo versionado nao guarda credencial.
    """
    from app.config import Configuracao

    try:
        return Configuracao().database_url
    except Exception:
        return None


@lru_cache
def postgres_disponivel() -> bool:
    from sqlalchemy import create_engine, text

    url = url_do_banco()
    if url is None:
        return False

    try:
        engine = create_engine(url, connect_args={"connect_timeout": 2})
        with engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def pytest_runtest_setup(item: pytest.Item) -> None:
    if item.get_closest_marker("postgres") is None:
        return

    decisao = decidir_execucao(
        banco_alcancavel=postgres_disponivel(),
        banco_exigido=banco_exigido_pelo_ambiente(dict(os.environ)),
    )

    if decisao.acao is Acao.PULAR:
        pytest.skip(decisao.motivo)
    if decisao.acao is Acao.FALHAR:
        pytest.fail(decisao.motivo, pytrace=False)


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
