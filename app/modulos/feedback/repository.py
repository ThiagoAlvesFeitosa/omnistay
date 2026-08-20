"""Acesso a avaliacao — sem regra de negocio."""

from sqlalchemy import text
from sqlalchemy.engine import Connection

ORIGEM_PULSO = "pulso_segundo_dia"
ORIGEM_CHECKOUT = "checkout"


def inserir_avaliacao_pulso(
    conexao: Connection,
    *,
    id_reserva: int,
    comentario: str | None,
) -> int:
    return conexao.execute(
        text(
            "INSERT INTO avaliacao (id_reserva, origem, nota, comentario) "
            "VALUES (:id_reserva, :origem, NULL, :comentario) "
            "RETURNING id_avaliacao"
        ),
        {
            "id_reserva": id_reserva,
            "origem": ORIGEM_PULSO,
            "comentario": comentario,
        },
    ).scalar_one()


def id_avaliacao_de_pulso(conexao: Connection, *, id_reserva: int) -> int | None:
    return conexao.execute(
        text(
            "SELECT id_avaliacao FROM avaliacao"
            " WHERE id_reserva = :id AND origem = :origem"
        ),
        {"id": id_reserva, "origem": ORIGEM_PULSO},
    ).scalar_one_or_none()


def tem_avaliacao_de_pulso(conexao: Connection, *, id_reserva: int) -> bool:
    return id_avaliacao_de_pulso(conexao, id_reserva=id_reserva) is not None


def inserir_avaliacao_checkout(
    conexao: Connection,
    *,
    id_reserva: int,
    nota: int,
    comentario: str | None,
) -> int:
    return conexao.execute(
        text(
            "INSERT INTO avaliacao (id_reserva, origem, nota, comentario) "
            "VALUES (:id_reserva, :origem, :nota, :comentario) "
            "RETURNING id_avaliacao"
        ),
        {
            "id_reserva": id_reserva,
            "origem": ORIGEM_CHECKOUT,
            "nota": nota,
            "comentario": comentario,
        },
    ).scalar_one()


def id_avaliacao_de_checkout(conexao: Connection, *, id_reserva: int) -> int | None:
    return conexao.execute(
        text(
            "SELECT id_avaliacao FROM avaliacao"
            " WHERE id_reserva = :id AND origem = :origem"
        ),
        {"id": id_reserva, "origem": ORIGEM_CHECKOUT},
    ).scalar_one_or_none()


def completar_comentario_checkout(
    conexao: Connection,
    *,
    id_avaliacao: int,
    comentario: str,
) -> None:
    conexao.execute(
        text(
            "UPDATE avaliacao SET comentario = :comentario"
            " WHERE id_avaliacao = :id"
            " AND (comentario IS NULL OR comentario = '')"
        ),
        {"comentario": comentario, "id": id_avaliacao},
    )
