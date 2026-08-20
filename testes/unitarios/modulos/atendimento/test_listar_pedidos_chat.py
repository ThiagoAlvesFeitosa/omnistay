"""Recorte cobravel da lista de pedidos feitos pelo chat."""

from decimal import Decimal

import pytest
from sqlalchemy import text

from app.modulos.atendimento.service import (
    abrir_consumo,
    abrir_servico,
    dispensar,
    lancar,
    listar_pedidos_feitos_pelo_chat,
)


def _reserva(conexao, id_hotel: int) -> int:
    return conexao.execute(
        text(
            "INSERT INTO reserva (id_hotel, telefone_contato,"
            " data_checkin_prevista, data_checkout_prevista) "
            "VALUES (:h, '5511911118800', CURRENT_DATE, CURRENT_DATE + 2) "
            "RETURNING id_reserva"
        ),
        {"h": id_hotel},
    ).scalar_one()


def _mensagem(conexao, id_reserva: int, conteudo: str) -> int:
    return conexao.execute(
        text(
            "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
            "VALUES (:r, 'recebida', :c) RETURNING id_mensagem"
        ),
        {"r": id_reserva, "c": conteudo},
    ).scalar_one()


@pytest.mark.postgres
def test_listar_so_cobraveis_na_ordem_de_abertura(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    recepcao = ambiente.propriedade_a.usuarios["recepcao"].id_usuario
    with ambiente.engine.begin() as conexao:
        id_reserva = _reserva(conexao, id_hotel)
        id_pendente = abrir_consumo(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=_mensagem(conexao, id_reserva, "uma cerveja"),
            descricao="uma cerveja",
            descricao_item="Cerveja",
            valor_praticado=Decimal("12.00"),
            numero_quarto="402",
            urgencia="baixa",
        )
        id_lancado = abrir_consumo(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=_mensagem(conexao, id_reserva, "uma agua"),
            descricao="uma agua",
            descricao_item="Agua",
            valor_praticado=Decimal("5.00"),
            numero_quarto=None,
            urgencia="baixa",
        )
        id_cortesia = abrir_consumo(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=_mensagem(conexao, id_reserva, "cortesia"),
            descricao="cortesia",
            descricao_item="Cortesia",
            valor_praticado=Decimal("0.00"),
            numero_quarto=None,
            urgencia="baixa",
        )
        abrir_servico(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=_mensagem(conexao, id_reserva, "toalha extra"),
            descricao="toalha extra",
            numero_quarto=None,
            urgencia="baixa",
        )
        lancar(
            conexao,
            id_hotel=id_hotel,
            id_solicitacao=id_lancado,
            id_usuario=recepcao,
        )
        dispensar(
            conexao,
            id_hotel=id_hotel,
            id_solicitacao=id_cortesia,
            id_usuario=recepcao,
        )
        itens = listar_pedidos_feitos_pelo_chat(
            conexao, id_hotel=id_hotel, id_reserva=id_reserva
        )

    ids = [item["id_solicitacao"] for item in itens]
    assert ids == [id_pendente, id_lancado]
    assert [item["descricao_item"] for item in itens] == ["Cerveja", "Agua"]
    assert "status_lancamento" not in itens[0]
    assert "descricao" not in itens[0]
    assert "Cortesia" not in [item["descricao_item"] for item in itens]
