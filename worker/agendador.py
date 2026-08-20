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
CHAVE_VALIDADE_BOAS_VINDAS = "horas_validade_boas_vindas"


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


def verificar_boas_vindas_pendentes(
    conexao: Connection,
    *,
    agora=None,
    repositorio_propriedade=propriedade_repository,
    agendar=None,
) -> int:
    """Registra pendencia de recado para hospedados na janela. Devolve afetados."""
    if agora is None:
        instante = relogio.agora()
    elif callable(agora):
        instante = agora()
    else:
        instante = agora
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=UTC)

    agendar_fn = agendar or conversa_service.agendar_boas_vindas
    reservas = hospedagem_service.listar_hospedados_sem_boas_vindas(conexao)
    cache_prazos: dict[int, int | None] = {}
    afetados = 0
    for reserva in reservas:
        id_hotel = reserva["id_hotel"]
        checkin_em = reserva.get("checkin_em")
        if checkin_em is None:
            continue
        if checkin_em.tzinfo is None:
            checkin_em = checkin_em.replace(tzinfo=UTC)
        if id_hotel not in cache_prazos:
            horas = _inteiro_positivo(
                repositorio_propriedade.ler_parametro(
                    conexao, id_hotel, CHAVE_VALIDADE_BOAS_VINDAS
                )
            )
            if horas is None:
                logger.info("prazo_ausente id_hotel=%s", id_hotel)
            cache_prazos[id_hotel] = horas
        horas = cache_prazos[id_hotel]
        if horas is None:
            continue
        if checkin_em < instante - timedelta(hours=horas):
            continue
        desfecho = agendar_fn(
            conexao,
            id_hotel=id_hotel,
            id_reserva=reserva["id_reserva"],
            nome_completo=reserva["nome_completo"],
        )
        if desfecho != "agendada":
            continue
        logger.info(
            "boas_vindas_recuperadas id_reserva=%s id_hotel=%s",
            reserva["id_reserva"],
            id_hotel,
        )
        afetados += 1
    return afetados


CHAVE_MINIMO_PULSO = "horas_minimas_para_pulso"
HORAS_POR_DIA_CIVIL = 24


def horas_restantes_de_estadia(data_checkout, hoje) -> int:
    return HORAS_POR_DIA_CIVIL * (data_checkout - hoje).days


def verificar_pulsos_pendentes(
    conexao: Connection,
    *,
    agora=None,
    repositorio_propriedade=propriedade_repository,
    tem_reclamacao_aberta=None,
    agendar=None,
) -> int:
    from app.modulos.atendimento import service as atendimento_service

    if agora is None:
        instante = relogio.agora()
    elif callable(agora):
        instante = agora()
    else:
        instante = agora
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=UTC)

    if tem_reclamacao_aberta is None:
        tem_reclamacao_aberta = atendimento_service.tem_reclamacao_aberta
    if agendar is None:
        agendar = conversa_service.agendar_pulso

    afetados = 0
    reservas = hospedagem_service.listar_hospedados_sem_pulso(conexao)
    cache_minimo: dict[int, int | None] = {}
    hoje = instante.date()
    for reserva in reservas:
        id_hotel = reserva["id_hotel"]
        id_reserva = reserva["id_reserva"]
        if id_hotel not in cache_minimo:
            minimo = _inteiro_positivo(
                repositorio_propriedade.ler_parametro(
                    conexao, id_hotel, CHAVE_MINIMO_PULSO
                )
            )
            if minimo is None:
                logger.info("prazo_ausente id_hotel=%s", id_hotel)
            cache_minimo[id_hotel] = minimo
        minimo = cache_minimo[id_hotel]
        if minimo is None:
            continue
        checkin_em = reserva.get("checkin_em")
        if checkin_em is None:
            continue
        if getattr(checkin_em, "tzinfo", None) is None:
            checkin_em = checkin_em.replace(tzinfo=UTC)
        if hoje <= checkin_em.date():
            continue
        restante = horas_restantes_de_estadia(
            reserva["data_checkout_prevista"], hoje
        )
        if restante < minimo:
            continue
        if tem_reclamacao_aberta(conexao, id_reserva=id_reserva):
            continue
        desfecho = agendar(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            nome_completo=reserva["nome_completo"],
        )
        if desfecho != "agendada":
            continue
        logger.info(
            "pulso_agendado id_reserva=%s id_hotel=%s",
            id_reserva,
            id_hotel,
        )
        afetados += 1
    return afetados
