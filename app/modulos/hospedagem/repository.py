"""Acesso a hospede, reserva e fila — sem regra de negocio."""

from datetime import date

from sqlalchemy import text
from sqlalchemy.engine import Connection


def inserir_hospede(conexao: Connection, *, nome_completo: str, telefone: str) -> int:
    return conexao.execute(
        text(
            "INSERT INTO hospede (nome_completo, telefone) "
            "VALUES (:nome, :telefone) RETURNING id_hospede"
        ),
        {"nome": nome_completo, "telefone": telefone},
    ).scalar_one()


def inserir_reserva(
    conexao: Connection,
    *,
    id_hotel: int,
    telefone_contato: str,
    data_checkin_prevista: date,
    data_checkout_prevista: date,
    status: str,
) -> int:
    return conexao.execute(
        text(
            "INSERT INTO reserva ("
            " id_hotel, telefone_contato, data_checkin_prevista,"
            " data_checkout_prevista, status"
            ") VALUES ("
            " :id_hotel, :telefone, :checkin, :checkout, :status"
            ") RETURNING id_reserva"
        ),
        {
            "id_hotel": id_hotel,
            "telefone": telefone_contato,
            "checkin": data_checkin_prevista,
            "checkout": data_checkout_prevista,
            "status": status,
        },
    ).scalar_one()


def inserir_vinculo_titular(
    conexao: Connection,
    *,
    id_reserva: int,
    id_hospede: int,
) -> None:
    conexao.execute(
        text(
            "INSERT INTO reserva_hospede ("
            " id_reserva, id_hospede, titular, ficha_completa"
            ") VALUES (:id_reserva, :id_hospede, TRUE, FALSE)"
        ),
        {"id_reserva": id_reserva, "id_hospede": id_hospede},
    )


def listar_fila_do_hotel(conexao: Connection, *, id_hotel: int) -> list[dict]:
    linhas = conexao.execute(
        text(
            "SELECT id_hotel, id_reserva, data_checkin_prevista,"
            " data_checkout_prevista, telefone_contato, status,"
            " nome_completo, ficha_completa, chegada_nao_confirmada,"
            " status_envio_coleta"
            " FROM vw_fila_do_dia"
            " WHERE id_hotel = :id_hotel"
            " ORDER BY data_checkin_prevista ASC, id_reserva ASC"
        ),
        {"id_hotel": id_hotel},
    ).mappings().all()
    return [dict(linha) for linha in linhas]


def contar_chegadas_do_dia(conexao: Connection, *, id_hotel: int) -> int:
    return conexao.execute(
        text(
            "SELECT COUNT(*) FROM reserva"
            " WHERE id_hotel = :id_hotel"
            " AND data_checkin_prevista = CURRENT_DATE"
            " AND status NOT IN ('encerrado', 'cancelada')"
        ),
        {"id_hotel": id_hotel},
    ).scalar_one()
