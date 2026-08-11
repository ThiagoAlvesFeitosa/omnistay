"""Bancos vazios de vida curta, para testes que precisam do PostgreSQL de verdade.

Restricao, trigger e unicidade sao justamente o que nao se verifica com dependencia
falsa. Cada teste recebe um banco proprio, criado vazio e removido ao fim, inclusive
quando o teste falha.
"""

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

BANCO_DE_MANUTENCAO = "postgres"


def url_de_manutencao(url_do_banco: str) -> URL:
    """A mesma conexao, apontada para o banco de manutencao.

    `CREATE DATABASE` nao pode rodar de dentro do banco que se quer criar, e nenhuma
    credencial e embutida aqui: tudo vem da URL configurada.
    """
    return make_url(url_do_banco).set(database=BANCO_DE_MANUTENCAO)


def _texto_com_senha(url: URL) -> str:
    """URL em texto preservando a senha: `str(URL)` a substitui por asteriscos."""
    return url.render_as_string(hide_password=False)


def _url_configurada() -> str:
    from testes.conftest import url_do_banco

    url = url_do_banco()
    if url is None:
        raise RuntimeError("DATABASE_URL nao esta configurada.")
    return url


@contextmanager
def banco_vazio() -> Iterator[str]:
    """Cria um banco vazio de nome unico e devolve a URL de conexao com ele."""
    url_base = make_url(_url_configurada())
    nome = f"omnistay_teste_{uuid.uuid4().hex[:12]}"

    manutencao = create_engine(
        url_base.set(database=BANCO_DE_MANUTENCAO),
        isolation_level="AUTOCOMMIT",
        connect_args={"connect_timeout": 5},
    )
    try:
        with manutencao.connect() as conexao:
            conexao.execute(text(f'CREATE DATABASE "{nome}"'))
        try:
            yield _texto_com_senha(url_base.set(database=nome))
        finally:
            with manutencao.connect() as conexao:
                conexao.execute(
                    text(f'DROP DATABASE IF EXISTS "{nome}" WITH (FORCE)')
                )
    finally:
        manutencao.dispose()
