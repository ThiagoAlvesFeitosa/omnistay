"""Transacao explicita: o repositorio recebe a conexao, nao a abre.

A F0.1 podia chamar `obter_engine()` por conta propria porque a saude e uma
consulta isolada. Esta fatia precisa de duas escritas coerentes — desativar
usuario e derrubar sessoes, criar hotel e gestor e parametros de uma vez.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.engine import Connection

from app.database import obter_engine


@contextmanager
def transacao() -> Iterator[Connection]:
    """Abre uma transacao e a confirma ao sair sem erro."""
    with obter_engine().begin() as conexao:
        yield conexao
