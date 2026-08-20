"""Enfileira trabalhos de pulso sem consumir."""

import pytest
from sqlalchemy import text

from app.fila import repository as fila_repo
from app.fila import service as fila_service


@pytest.mark.postgres
def test_enfileirar_enviar_pulso_grava_tipo_e_ids(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = conexao.execute(
            text(
                "INSERT INTO reserva (id_hotel, telefone_contato,"
                " data_checkin_prevista, data_checkout_prevista) "
                "VALUES (:h, '5511999990101', CURRENT_DATE, CURRENT_DATE + 2) "
                "RETURNING id_reserva"
            ),
            {"h": id_hotel},
        ).scalar_one()
        id_trabalho = fila_service.enfileirar_enviar_pulso(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=11,
        )
        linha = conexao.execute(
            text("SELECT tipo, payload FROM trabalho WHERE id_trabalho = :id"),
            {"id": id_trabalho},
        ).mappings().one()
        assert linha["tipo"] == "enviar_pulso"
        assert linha["payload"]["id_reserva"] == id_reserva
        assert linha["payload"]["id_mensagem"] == 11
        assert "conteudo" not in linha["payload"]
        assert "enviar_pulso" in fila_repo.TIPOS_CONSUMIVEIS


@pytest.mark.postgres
def test_enfileirar_registrar_resposta_pulso_grava_tipo_e_ids(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = conexao.execute(
            text(
                "INSERT INTO reserva (id_hotel, telefone_contato,"
                " data_checkin_prevista, data_checkout_prevista) "
                "VALUES (:h, '5511999990102', CURRENT_DATE, CURRENT_DATE + 2) "
                "RETURNING id_reserva"
            ),
            {"h": id_hotel},
        ).scalar_one()
        id_trabalho = fila_service.enfileirar_registrar_resposta_pulso(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=22,
        )
        linha = conexao.execute(
            text("SELECT tipo, payload FROM trabalho WHERE id_trabalho = :id"),
            {"id": id_trabalho},
        ).mappings().one()
        assert linha["tipo"] == "registrar_resposta_pulso"
        assert linha["payload"]["id_reserva"] == id_reserva
        assert linha["payload"]["id_mensagem"] == 22
        assert "conteudo" not in linha["payload"]
        assert "registrar_resposta_pulso" in fila_repo.TIPOS_CONSUMIVEIS
