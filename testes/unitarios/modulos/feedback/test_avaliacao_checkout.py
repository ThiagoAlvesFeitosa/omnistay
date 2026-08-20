"""Avaliacao de checkout grava origem checkout com nota."""

import pytest
from sqlalchemy import text

from app.modulos.feedback import service as feedback
from testes.suporte.pulso import montar_hospedado_para_pulso


@pytest.mark.postgres
def test_gravar_avaliacao_checkout_insere_origem_e_nota(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910001101"
        )
        id_avaliacao = feedback.gravar_avaliacao_checkout(
            conexao, id_reserva=id_reserva, nota=5, comentario=None
        )
        linha = conexao.execute(
            text(
                "SELECT origem, nota, comentario FROM avaliacao"
                " WHERE id_avaliacao = :id"
            ),
            {"id": id_avaliacao},
        ).mappings().one()
        assert linha["origem"] == "checkout"
        assert linha["nota"] == 5
        assert linha["comentario"] is None


@pytest.mark.postgres
def test_segunda_nota_nao_duplica_avaliacao_de_checkout(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910001102"
        )
        primeiro = feedback.gravar_avaliacao_checkout(
            conexao, id_reserva=id_reserva, nota=4, comentario=None
        )
        segundo = feedback.gravar_avaliacao_checkout(
            conexao, id_reserva=id_reserva, nota=1, comentario="depois"
        )
        assert segundo == primeiro
        total = conexao.execute(
            text(
                "SELECT COUNT(*) FROM avaliacao"
                " WHERE id_reserva = :r AND origem = 'checkout'"
            ),
            {"r": id_reserva},
        ).scalar_one()
        assert total == 1
        linha = conexao.execute(
            text(
                "SELECT nota, comentario FROM avaliacao WHERE id_avaliacao = :id"
            ),
            {"id": primeiro},
        ).mappings().one()
        assert linha["nota"] == 4
        assert linha["comentario"] == "depois"
