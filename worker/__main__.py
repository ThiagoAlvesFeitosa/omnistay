"""Ponto de entrada: python -m worker [--uma-passagem]."""

import argparse
import time

from sqlalchemy import create_engine

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.config import obter_configuracao
from app.comum.log import configurar_log, obter_logger
from worker.consumidor import processar_uma_passagem_na_engine

logger = obter_logger(__name__)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Worker OmniStay")
    parser.add_argument(
        "--uma-passagem",
        action="store_true",
        help="Processa trabalhos elegiveis uma vez e encerra",
    )
    parser.add_argument(
        "--intervalo-segundos",
        type=float,
        default=2.0,
        help="Intervalo entre passagens no modo continuo",
    )
    args = parser.parse_args(argv)
    configurar_log()
    engine = create_engine(obter_configuracao().database_url)
    gateway = MensageriaFalsa()
    if args.uma_passagem:
        n = processar_uma_passagem_na_engine(engine, gateway=gateway)
        logger.info("passagem_concluida processados=%s", n)
        return
    logger.info("worker_iniciado")
    while True:
        processar_uma_passagem_na_engine(engine, gateway=gateway)
        time.sleep(args.intervalo_segundos)


if __name__ == "__main__":
    main()
