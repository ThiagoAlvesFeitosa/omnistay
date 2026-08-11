"""Aplicar migracoes e ler o estado de versionamento de um banco, a partir dos testes."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

RAIZ = Path(__file__).resolve().parents[2]
ARQUIVO_INI = RAIZ / "alembic.ini"
ARQUIVO_DO_DOCUMENTO = RAIZ / "docs" / "04-schema.sql"
ARQUIVO_DA_REVISAO_INICIAL = (
    RAIZ / "alembic" / "versions" / "sql" / "0001_esquema_inicial.sql"
)

SQL_DO_DOCUMENTO = ARQUIVO_DO_DOCUMENTO.read_text(encoding="utf-8")
SQL_DA_REVISAO_INICIAL = ARQUIVO_DA_REVISAO_INICIAL.read_text(encoding="utf-8")


def configuracao_para(url_do_banco: str) -> Config:
    configuracao = Config(str(ARQUIVO_INI))
    configuracao.set_main_option("script_location", str(RAIZ / "alembic"))
    configuracao.set_main_option("sqlalchemy.url", url_do_banco)
    return configuracao


def aplicar_migracoes(url_do_banco: str, alvo: str = "head") -> None:
    command.upgrade(configuracao_para(url_do_banco), alvo)


def revisao_registrada(url_do_banco: str) -> str | None:
    """A revisao corrente do banco, ou None quando nao ha versionamento registrado."""
    engine = create_engine(url_do_banco)
    try:
        with engine.connect() as conexao:
            existe = conexao.execute(
                text("SELECT to_regclass('public.alembic_version') IS NOT NULL")
            ).scalar()
            if not existe:
                return None
            return conexao.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar()
    finally:
        engine.dispose()
