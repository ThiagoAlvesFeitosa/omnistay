"""Abre solicitacao de servico sem consumo."""

import pytest
from sqlalchemy import text

from app.modulos.atendimento.service import HotelIncompativel, abrir_servico


def _reserva_e_mensagem(conexao, id_hotel: int, conteudo: str = "toalha extra"):
    id_reserva = conexao.execute(
        text(
            "INSERT INTO reserva (id_hotel, telefone_contato,"
            " data_checkin_prevista, data_checkout_prevista) "
            "VALUES (:h, '5511911110000', CURRENT_DATE, CURRENT_DATE + 2) "
            "RETURNING id_reserva"
        ),
        {"h": id_hotel},
    ).scalar_one()
    id_mensagem = conexao.execute(
        text(
            "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
            "VALUES (:r, 'recebida', :c) RETURNING id_mensagem"
        ),
        {"r": id_reserva, "c": conteudo},
    ).scalar_one()
    return id_reserva, id_mensagem


@pytest.mark.postgres
def test_abrir_servico_grava_tipo_servico_sem_consumo(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva, id_mensagem = _reserva_e_mensagem(
            conexao, id_hotel, "toalha extra no quarto 402"
        )
        id_solicitacao = abrir_servico(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            descricao="toalha extra no quarto 402",
            numero_quarto="402",
            urgencia="baixa",
        )
        linha = conexao.execute(
            text(
                "SELECT tipo, descricao, numero_quarto, urgencia, status,"
                " id_mensagem_origem FROM solicitacao WHERE id_solicitacao = :id"
            ),
            {"id": id_solicitacao},
        ).mappings().one()
        assert linha["tipo"] == "servico"
        assert linha["descricao"] == "toalha extra no quarto 402"
        assert linha["numero_quarto"] == "402"
        assert linha["urgencia"] == "baixa"
        assert linha["status"] == "aberta"
        assert linha["id_mensagem_origem"] == id_mensagem
        consumo = conexao.execute(
            text("SELECT COUNT(*) FROM consumo WHERE id_solicitacao = :id"),
            {"id": id_solicitacao},
        ).scalar_one()
        assert consumo == 0


@pytest.mark.postgres
def test_abrir_servico_recusa_reserva_de_outro_hotel(ambiente):
    with ambiente.engine.begin() as conexao:
        id_reserva, id_mensagem = _reserva_e_mensagem(
            conexao, ambiente.propriedade_b.id_hotel
        )
        with pytest.raises(HotelIncompativel):
            abrir_servico(
                conexao,
                id_hotel=ambiente.propriedade_a.id_hotel,
                id_reserva=id_reserva,
                id_mensagem=id_mensagem,
                descricao="toalha extra",
                numero_quarto=None,
                urgencia="media",
            )
        quantidade = conexao.execute(
            text("SELECT COUNT(*) FROM solicitacao WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        assert quantidade == 0
