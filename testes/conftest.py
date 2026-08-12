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
    # Custo real da derivacao vive na configuracao de producao. Aqui o numero
    # baixo mantem o ciclo de TDD rapido o bastante para ser rodado a cada minuto.
    os.environ.setdefault("SENHA_ITERACOES", "1000")
    from app.config import obter_configuracao

    obter_configuracao.cache_clear()


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
def cliente(ambiente_de_teste, limpar_caches_de_configuracao):
    from fastapi.testclient import TestClient

    from app.main import app

    # Cookie Secure so e reenviado sobre https. Sem isso, todo teste autenticado
    # falharia por um motivo alheio ao que o teste verifica.
    with TestClient(app, base_url="https://testserver") as cliente_de_teste:
        yield cliente_de_teste


@pytest.fixture
def ambiente():
    from testes.suporte.ambiente_de_acesso import ambiente_de_acesso

    with ambiente_de_acesso() as ambiente_montado:
        yield ambiente_montado


@pytest.fixture
def app_sobre_ambiente(ambiente, limpar_caches_de_configuracao, monkeypatch):
    """Aplica a aplicacao ao banco descartavel do ambiente de acesso."""
    import app.database as modulo_banco
    from app.config import obter_configuracao
    from fastapi.testclient import TestClient
    from app.main import app

    monkeypatch.setenv("DATABASE_URL", ambiente.url)
    obter_configuracao.cache_clear()
    modulo_banco.obter_engine.cache_clear()

    with TestClient(app, base_url="https://testserver") as cliente_de_teste:
        yield cliente_de_teste, ambiente

    obter_configuracao.cache_clear()
    modulo_banco.obter_engine.cache_clear()