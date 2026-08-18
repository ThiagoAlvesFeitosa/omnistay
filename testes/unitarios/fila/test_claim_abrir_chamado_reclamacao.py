"""Claim da fila consome abrir_chamado_reclamacao."""

import pytest
from sqlalchemy import text

from app.fila import repository as fila_repo


@pytest.mark.postgres
def test_reclamar_proximo_consome_abrir_chamado_reclamacao(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = conexao.execute(
            text(
                "INSERT INTO reserva (id_hotel, telefone_contato,"
                " data_checkin_prevista, data_checkout_prevista) "
                "VALUES (:h, '5511977779999', CURRENT_DATE, CURRENT_DATE + 2) "
                "RETURNING id_reserva"
            ),
            {"h": id_hotel},
        ).scalar_one()
        conexao.execute(
            text(
                "INSERT INTO trabalho (id_hotel, tipo, payload, status) "
                "VALUES (:h, 'abrir_chamado_reclamacao',"
                " CAST(:p AS jsonb), 'pendente')"
            ),
            {
                "h": id_hotel,
                "p": '{"id_reserva": %s, "id_mensagem": 8}' % id_reserva,
            },
        )

        reclamado = fila_repo.reclamar_proximo(conexao)
        assert reclamado is not None
        assert reclamado["tipo"] == "abrir_chamado_reclamacao"
        status = conexao.execute(
            text(
                "SELECT status FROM trabalho"
                " WHERE tipo = 'abrir_chamado_reclamacao'"
            )
        ).scalar_one()
        assert status == "processando"
