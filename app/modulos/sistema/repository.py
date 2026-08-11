from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.comum.log import obter_logger
from app.database import obter_engine

_logger = obter_logger(__name__)

CODIGO_TIMEOUT = "DB_TIMEOUT"
CODIGO_FALHA_DE_CONEXAO = "DB_CONNECTION_FAILED"


def _classificar(erro: SQLAlchemyError) -> str:
    if "timeout" in str(erro).lower():
        return CODIGO_TIMEOUT
    return CODIGO_FALHA_DE_CONEXAO


def verificar_conectividade_banco() -> bool:
    try:
        with obter_engine().connect() as conexao:
            conexao.execute(text("SELECT 1"))
    except SQLAlchemyError as erro:
        # Somente o codigo vai para o log: a mensagem carrega host, porta e DSN.
        _logger.warning(_classificar(erro))
        return False
    return True
