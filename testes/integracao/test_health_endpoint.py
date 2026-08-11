import pytest

URL_PORTA_FECHADA = "postgresql+psycopg2://usuario:senha@localhost:59999/omnistay"


@pytest.fixture
def banco_indisponivel(monkeypatch):
    from app.config import obter_configuracao
    from app.database import obter_engine

    monkeypatch.setenv("DATABASE_URL", URL_PORTA_FECHADA)
    obter_configuracao.cache_clear()
    obter_engine.cache_clear()
    yield
    obter_configuracao.cache_clear()
    obter_engine.cache_clear()


@pytest.mark.postgres
def test_banco_disponivel_retorna_200(cliente):
    resposta = cliente.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"aplicacao": "ok", "banco": "ok"}


def test_banco_indisponivel_retorna_503(cliente, banco_indisponivel):
    resposta = cliente.get("/health")

    assert resposta.status_code == 503
    assert resposta.json() == {"aplicacao": "ok", "banco": "indisponivel"}


def test_banco_indisponivel_app_continua_respondendo(cliente, banco_indisponivel):
    cliente.get("/health")

    segunda_resposta = cliente.get("/health")

    assert segunda_resposta.status_code == 503
