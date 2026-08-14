"""Ponto de entrada: python -m worker [--uma-passagem|--verificar-cadastros]."""

import argparse
import time
from datetime import timedelta

from sqlalchemy import create_engine

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.config import obter_configuracao
from app.comum import relogio
from app.comum.log import configurar_log, obter_logger
from worker.agendador import verificar_cadastros_pendentes
from worker.consumidor import processar_uma_passagem_na_engine

logger = obter_logger(__name__)

INTERVALO_VERIFICACAO = timedelta(hours=1)


def _rodar_verificacao(engine) -> int:
    with engine.begin() as conexao:
        n = verificar_cadastros_pendentes(conexao)
    logger.info("verificacao_concluida afetados=%s", n)
    return n


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Worker OmniStay")
    parser.add_argument(
        "--uma-passagem",
        action="store_true",
        help="Processa trabalhos elegiveis uma vez e encerra",
    )
    parser.add_argument(
        "--verificar-cadastros",
        action="store_true",
        help="Verifica cadastros pendentes uma vez e encerra",
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
    if args.verificar_cadastros:
        _rodar_verificacao(engine)
        return
    logger.info("worker_iniciado")
    ultima_verificacao = None
    while True:
        processar_uma_passagem_na_engine(engine, gateway=gateway)
        agora = relogio.agora()
        if (
            ultima_verificacao is None
            or agora - ultima_verificacao >= INTERVALO_VERIFICACAO
        ):
            _rodar_verificacao(engine)
            ultima_verificacao = agora
        time.sleep(args.intervalo_segundos)


if __name__ == "__main__":
    main()
