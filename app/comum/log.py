import logging

from app.config import obter_configuracao

_FORMATO = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configurar_log() -> None:
    logging.basicConfig(
        level=obter_configuracao().log_level.upper(),
        format=_FORMATO,
    )


def obter_logger(nome: str) -> logging.Logger:
    return logging.getLogger(nome)
