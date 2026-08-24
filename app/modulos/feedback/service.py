"""Regras de avaliacao do pulso — sem HTTP e sem SQL de conversa."""

from contextlib import nullcontext

from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from app.comum.log import obter_logger
from app.modulos.feedback import repository as repositorio_padrao

logger = obter_logger(__name__)


def _savepoint(conexao):
    begin = getattr(conexao, "begin_nested", None)
    if begin is None:
        return nullcontext()
    return begin()


def encerrar_pulso(
    conexao: Connection,
    *,
    id_reserva: int,
    comentario: str | None,
    repositorio=repositorio_padrao,
) -> int:
    existente = repositorio.id_avaliacao_de_pulso(conexao, id_reserva=id_reserva)
    if existente is not None:
        logger.info(
            "pulso_ja_encerrado id_reserva=%s id_avaliacao=%s origem=pulso_segundo_dia",
            id_reserva,
            existente,
        )
        return existente
    try:
        with _savepoint(conexao):
            id_avaliacao = repositorio.inserir_avaliacao_pulso(
                conexao, id_reserva=id_reserva, comentario=comentario
            )
    except IntegrityError:
        id_avaliacao = repositorio.id_avaliacao_de_pulso(
            conexao, id_reserva=id_reserva
        )
        logger.info(
            "pulso_ja_encerrado id_reserva=%s id_avaliacao=%s origem=pulso_segundo_dia",
            id_reserva,
            id_avaliacao,
        )
        return id_avaliacao or 0
    logger.info(
        "pulso_encerrado id_reserva=%s id_avaliacao=%s origem=pulso_segundo_dia",
        id_reserva,
        id_avaliacao,
    )
    return id_avaliacao


def encerrar_pulso_em_silencio(
    conexao: Connection,
    *,
    id_reserva: int,
    comentario: str | None,
    repositorio=repositorio_padrao,
) -> int:
    return encerrar_pulso(
        conexao,
        id_reserva=id_reserva,
        comentario=comentario,
        repositorio=repositorio,
    )


def tem_avaliacao_de_pulso(
    conexao: Connection,
    *,
    id_reserva: int,
    repositorio=repositorio_padrao,
) -> bool:
    return repositorio.tem_avaliacao_de_pulso(conexao, id_reserva=id_reserva)


def gravar_avaliacao_checkout(
    conexao: Connection,
    *,
    id_reserva: int,
    nota: int,
    comentario: str | None,
    repositorio=repositorio_padrao,
) -> int:
    existente = repositorio.id_avaliacao_de_checkout(
        conexao, id_reserva=id_reserva
    )
    if existente is not None:
        if comentario:
            repositorio.completar_comentario_checkout(
                conexao, id_avaliacao=existente, comentario=comentario
            )
        logger.info(
            "avaliacao_checkout_ja_existente id_reserva=%s id_avaliacao=%s",
            id_reserva,
            existente,
        )
        return existente
    try:
        with _savepoint(conexao):
            id_avaliacao = repositorio.inserir_avaliacao_checkout(
                conexao,
                id_reserva=id_reserva,
                nota=nota,
                comentario=comentario,
            )
    except IntegrityError:
        id_avaliacao = repositorio.id_avaliacao_de_checkout(
            conexao, id_reserva=id_reserva
        )
        if comentario and id_avaliacao:
            repositorio.completar_comentario_checkout(
                conexao, id_avaliacao=id_avaliacao, comentario=comentario
            )
        logger.info(
            "avaliacao_checkout_ja_existente id_reserva=%s id_avaliacao=%s",
            id_reserva,
            id_avaliacao,
        )
        return id_avaliacao or 0
    logger.info(
        "avaliacao_checkout_gravada id_reserva=%s id_avaliacao=%s nota=%s",
        id_reserva,
        id_avaliacao,
        nota,
    )
    return id_avaliacao


def anonimizar_comentarios_vencidos(
    conexao: Connection,
    *,
    id_hotel: int,
    agora,
    meses: int,
    repositorio=repositorio_padrao,
) -> int:
    from app.comum.retencao import MARCA_TEXTO

    return repositorio.anonimizar_comentarios_vencidos(
        conexao,
        id_hotel=id_hotel,
        agora=agora,
        meses=meses,
        marca=MARCA_TEXTO,
    )
