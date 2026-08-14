"""Verificacao periodica de cadastros pendentes (silencio na pre-chegada)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.engine import Connection

from app.comum import relogio
from app.comum.log import obter_logger
from app.modulos.conversa import service as conversa_service
from app.modulos.hospedagem import service as hospedagem_service
from app.modulos.propriedade import repository as propriedade_repository

logger = obter_logger(__name__)

CHAVE_ATE_REENVIO = "horas_ate_reenvio"
CHAVE_CORTE = "horas_corte_antes_checkin"


def instante_de_corte(data_checkin, horas_corte: int) -> datetime:
    inicio = datetime(
        data_checkin.year,
        data_checkin.month,
        data_checkin.day,
        tzinfo=UTC,
    )
    return inicio - timedelta(hours=horas_corte)


def _inteiro_positivo(valor: str | None) -> int | None:
    if valor is None:
        return None
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None
    if numero < 1:
        return None
    return numero


def _prazos_do_hotel(
    conexao: Connection,
    id_hotel: int,
    repositorio_propriedade=propriedade_repository,
) -> dict | None:
    ate = _inteiro_positivo(
        repositorio_propriedade.ler_parametro(
            conexao, id_hotel, CHAVE_ATE_REENVIO
        )
    )
    corte = _inteiro_positivo(
        repositorio_propriedade.ler_parametro(conexao, id_hotel, CHAVE_CORTE)
    )
    if ate is None or corte is None:
        logger.info("prazo_ausente id_hotel=%s", id_hotel)
        return None
    return {"ate": ate, "corte": corte}


def verificar_cadastros_pendentes(
    conexao: Connection,
    *,
    agora=None,
    repositorio_propriedade=propriedade_repository,
) -> int:
    """Aplica lembrete unico e marcacao sem_cadastro_previo. Devolve afetados."""
    if agora is None:
        instante = relogio.agora()
    elif callable(agora):
        instante = agora()
    else:
        instante = agora
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=UTC)

    afetados = 0
    reservas = hospedagem_service.listar_reservas_aguardando_cadastro(conexao)
    cache_prazos: dict[int, dict | None] = {}
    for reserva in reservas:
        id_hotel = reserva["id_hotel"]
        id_reserva = reserva["id_reserva"]
        if id_hotel not in cache_prazos:
            cache_prazos[id_hotel] = _prazos_do_hotel(
                conexao,
                id_hotel,
                repositorio_propriedade=repositorio_propriedade,
            )
        prazos = cache_prazos[id_hotel]
        if prazos is None:
            continue
        if conversa_service.tem_mensagem_recebida(
            conexao, id_reserva=id_reserva
        ):
            continue
        corte_em = instante_de_corte(
            reserva["data_checkin_prevista"], prazos["corte"]
        )
        data_vencida = instante.date() > reserva["data_checkin_prevista"]
        if instante >= corte_em or data_vencida:
            hospedagem_service.marcar_sem_cadastro_previo(
                conexao, id_hotel=id_hotel, id_reserva=id_reserva
            )
            logger.info(
                "marcado_sem_cadastro id_reserva=%s id_hotel=%s",
                id_reserva,
                id_hotel,
            )
            afetados += 1
            continue
        if reserva.get("reenvio_realizado"):
            continue
        coleta_em = conversa_service.instante_coleta_enviada(
            conexao, id_reserva=id_reserva
        )
        if coleta_em is None:
            continue
        if instante >= coleta_em + timedelta(hours=prazos["ate"]):
            conversa_service.agendar_lembrete(
                conexao,
                id_hotel=id_hotel,
                id_reserva=id_reserva,
                nome_completo=reserva["nome_completo"],
            )
            hospedagem_service.marcar_reenvio_realizado(
                conexao, id_hotel=id_hotel, id_reserva=id_reserva
            )
            logger.info(
                "lembrete_agendado id_reserva=%s id_hotel=%s",
                id_reserva,
                id_hotel,
            )
            afetados += 1
    return afetados
