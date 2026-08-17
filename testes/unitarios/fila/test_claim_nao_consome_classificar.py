"""Claim da fila consome classificar_mensagem."""

import pytest
from sqlalchemy import text

from app.fila import repository as fila_repo


@pytest.mark.postgres
def test_reclamar_proximo_consome_classificar_mensagem(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = conexao.execute(
            text(
                "INSERT INTO reserva (id_hotel, telefone_contato,"
                " data_checkin_prevista, data_checkout_prevista) "
                "VALUES (:h, '5511999999999', CURRENT_DATE, CURRENT_DATE + 2) "
                "RETURNING id_reserva"
            ),
            {"h": id_hotel},
        ).scalar_one()
        conexao.execute(
            text(
                "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
                "VALUES (:h, 'classificar_mensagem',"
                " CAST(:p AS jsonb), 'pendente')"
            ),
            {
                "h": id_hotel,
                "p": (
                    '{"id_reserva": %s, "id_mensagem": 9, "id_evento": 9}'
                    % id_reserva
                ),
            },
        )

        reclamado = fila_repo.reclamar_proximo(conexao)
        assert reclamado is not None
        assert reclamado["tipo"] == "classificar_mensagem"
        status = conexao.execute(
            text(
                "SELECT status FROM trabalho WHERE tipo = 'classificar_mensagem'"
            )
        ).scalar_one()
        assert status == "processando"


@pytest.mark.postgres
def test_reclamar_proximo_ainda_consome_enviar_coleta(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = conexao.execute(
            text(
                "INSERT INTO reserva (id_hotel, telefone_contato,"
                " data_checkin_prevista, data_checkout_prevista) "
                "VALUES (:h, '5511988888888', CURRENT_DATE, CURRENT_DATE + 3) "
                "RETURNING id_reserva"
            ),
            {"h": id_hotel},
        ).scalar_one()
        conexao.execute(
            text(
                "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
                "VALUES (:h, 'enviar_coleta',"
                " CAST(:p AS jsonb), 'pendente')"
            ),
            {
                "h": id_hotel,
                "p": '{"id_reserva": %s, "id_mensagem": 2}' % id_reserva,
            },
        )
        reclamado = fila_repo.reclamar_proximo(conexao)
        assert reclamado is not None
        assert reclamado["tipo"] == "enviar_coleta"
