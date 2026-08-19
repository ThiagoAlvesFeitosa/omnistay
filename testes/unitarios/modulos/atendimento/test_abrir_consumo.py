"""Abre solicitacao tipo consumo com filho pendente."""

from decimal import Decimal

import pytest
from sqlalchemy import text

from app.modulos.atendimento.service import HotelIncompativel, abrir_consumo
from testes.suporte.consumo import NOME_ITEM, PRECO_ATUAL


def _reserva_e_mensagem(conexao, id_hotel: int, conteudo: str = "uma cerveja"):
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
def test_abrir_consumo_grava_pai_e_filho_pendente(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva, id_mensagem = _reserva_e_mensagem(
            conexao, id_hotel, "uma cerveja no quarto 402"
        )
        id_solicitacao = abrir_consumo(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            descricao="uma cerveja no quarto 402",
            descricao_item=NOME_ITEM,
            valor_praticado=PRECO_ATUAL,
            numero_quarto="402",
            urgencia="baixa",
        )
        pai = conexao.execute(
            text(
                "SELECT tipo, descricao, numero_quarto, urgencia, status,"
                " id_mensagem_origem FROM solicitacao WHERE id_solicitacao = :id"
            ),
            {"id": id_solicitacao},
        ).mappings().one()
        filho = conexao.execute(
            text(
                "SELECT descricao_item, valor_praticado, status_lancamento,"
                " id_usuario_lancamento, lancado_em FROM consumo"
                " WHERE id_solicitacao = :id"
            ),
            {"id": id_solicitacao},
        ).mappings().one()
        assert pai["tipo"] == "consumo"
        assert pai["numero_quarto"] == "402"
        assert pai["urgencia"] == "baixa"
        assert pai["status"] == "aberta"
        assert pai["id_mensagem_origem"] == id_mensagem
        assert filho["descricao_item"] == NOME_ITEM
        assert Decimal(str(filho["valor_praticado"])) == PRECO_ATUAL
        assert filho["status_lancamento"] == "pendente"
        assert filho["id_usuario_lancamento"] is None
        assert filho["lancado_em"] is None


@pytest.mark.postgres
def test_abrir_consumo_recusa_reserva_de_outro_hotel(ambiente):
    with ambiente.engine.begin() as conexao:
        id_reserva, id_mensagem = _reserva_e_mensagem(
            conexao, ambiente.propriedade_b.id_hotel
        )
        with pytest.raises(HotelIncompativel):
            abrir_consumo(
                conexao,
                id_hotel=ambiente.propriedade_a.id_hotel,
                id_reserva=id_reserva,
                id_mensagem=id_mensagem,
                descricao="uma cerveja",
                descricao_item=NOME_ITEM,
                valor_praticado=PRECO_ATUAL,
                numero_quarto=None,
                urgencia="media",
            )
        quantidade = conexao.execute(
            text("SELECT COUNT(*) FROM solicitacao WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        assert quantidade == 0
