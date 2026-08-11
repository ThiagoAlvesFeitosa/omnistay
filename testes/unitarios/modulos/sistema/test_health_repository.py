import pytest
from sqlalchemy import create_engine

from app.modulos.sistema import repository


@pytest.fixture
def engine_para_porta_fechada(monkeypatch):
    engine = create_engine(
        "postgresql+psycopg2://postgres:invalida@localhost:59999/omnistay",
        connect_args={"connect_timeout": 1},
    )
    monkeypatch.setattr(repository, "obter_engine", lambda: engine)


def test_repository_retorna_falso_quando_banco_nao_responde(engine_para_porta_fechada):
    respondeu = repository.verificar_conectividade_banco()

    assert respondeu is False
