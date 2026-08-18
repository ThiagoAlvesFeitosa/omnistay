"""Enfileira registrar_pedido_servico sem consumir."""

import pytest
from sqlalchemy import text

from app.fila import service as fila_service


@pytest.mark.postgres
def test_enfileirar_registrar_pedido_grava_tipo_e_ids(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = conexao.execute(
            text(
                "INSERT INTO reserva (id_hotel, telefone_contato,"
                " data_checkin_prevista, data_checkout_prevista) "
                "VALUES (:h, '5511999990001', CURRENT_DATE, CURRENT_DATE + 2) "
                "RETURNING id_reserva"
            ),
            {"h": id_hotel},
        ).scalar_one()
        id_trabalho = fila_service.enfileirar_registrar_pedido_servico(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=44,
        )
        linha = conexao.execute(
            text("SELECT tipo, payload FROM trabalho WHERE id_trabalho = :id"),
            {"id": id_trabalho},
        ).mappings().one()
        assert linha["tipo"] == "registrar_pedido_servico"
        assert linha["payload"]["id_reserva"] == id_reserva
        assert linha["payload"]["id_mensagem"] == 44
        assert "conteudo" not in linha["payload"]
