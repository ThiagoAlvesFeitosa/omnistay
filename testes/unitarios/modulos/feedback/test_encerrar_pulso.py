"""Encerramento do pulso grava avaliacao unica."""

import pytest
from sqlalchemy import text

from app.modulos.feedback import service as feedback
from testes.suporte.pulso import montar_hospedado_para_pulso


@pytest.mark.postgres
def test_encerrar_pulso_grava_origem_e_nota_nula(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000101"
        )
        id_avaliacao = feedback.encerrar_pulso(
            conexao, id_reserva=id_reserva, comentario="tudo bem"
        )
        linha = conexao.execute(
            text(
                "SELECT origem, nota, comentario FROM avaliacao"
                " WHERE id_avaliacao = :id"
            ),
            {"id": id_avaliacao},
        ).mappings().one()
        assert linha["origem"] == "pulso_segundo_dia"
        assert linha["nota"] is None
        assert linha["comentario"] == "tudo bem"
        assert feedback.tem_avaliacao_de_pulso(conexao, id_reserva=id_reserva)


@pytest.mark.postgres
def test_segunda_chamada_trata_unicidade_como_ja_encerrado(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000102"
        )
        primeiro = feedback.encerrar_pulso(
            conexao, id_reserva=id_reserva, comentario="primeiro"
        )
        segundo = feedback.encerrar_pulso(
            conexao, id_reserva=id_reserva, comentario="segundo"
        )
        assert segundo == primeiro
        total = conexao.execute(
            text("SELECT COUNT(*) FROM avaliacao WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        assert total == 1
        comentario = conexao.execute(
            text("SELECT comentario FROM avaliacao WHERE id_avaliacao = :id"),
            {"id": primeiro},
        ).scalar_one()
        assert comentario == "primeiro"
