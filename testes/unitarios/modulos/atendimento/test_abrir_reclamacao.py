"""Abre solicitacao de reclamacao sem consumo."""

import pytest
from sqlalchemy import text

from app.modulos.atendimento.service import (
    HotelIncompativel,
    abrir_reclamacao,
    completar_janela_se_resposta,
)


def _reserva_e_mensagem(conexao, id_hotel: int, conteudo: str = "o ar nao gela"):
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
def test_abrir_reclamacao_grava_tipo_sem_consumo(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva, id_mensagem = _reserva_e_mensagem(
            conexao, id_hotel, "o ar do quarto 402 nao esta gelando"
        )
        id_solicitacao = abrir_reclamacao(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            descricao="o ar do quarto 402 nao esta gelando",
            numero_quarto="402",
            urgencia="alta",
            janela_preferencia=None,
        )
        linha = conexao.execute(
            text(
                "SELECT tipo, descricao, numero_quarto, urgencia, status,"
                " janela_preferencia, id_mensagem_origem"
                " FROM solicitacao WHERE id_solicitacao = :id"
            ),
            {"id": id_solicitacao},
        ).mappings().one()
        assert linha["tipo"] == "reclamacao"
        assert linha["descricao"] == "o ar do quarto 402 nao esta gelando"
        assert linha["numero_quarto"] == "402"
        assert linha["urgencia"] == "alta"
        assert linha["status"] == "aberta"
        assert linha["janela_preferencia"] is None
        assert linha["id_mensagem_origem"] == id_mensagem
        consumo = conexao.execute(
            text("SELECT COUNT(*) FROM consumo WHERE id_solicitacao = :id"),
            {"id": id_solicitacao},
        ).scalar_one()
        assert consumo == 0


@pytest.mark.postgres
def test_abrir_reclamacao_grava_janela_quando_informada(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva, id_mensagem = _reserva_e_mensagem(
            conexao, id_hotel, "o chuveiro vazou, pode ser depois das 16h"
        )
        id_solicitacao = abrir_reclamacao(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            descricao="o chuveiro vazou, pode ser depois das 16h",
            numero_quarto=None,
            urgencia="media",
            janela_preferencia="depois das 16h",
        )
        janela = conexao.execute(
            text(
                "SELECT janela_preferencia FROM solicitacao"
                " WHERE id_solicitacao = :id"
            ),
            {"id": id_solicitacao},
        ).scalar_one()
        assert janela == "depois das 16h"


@pytest.mark.postgres
def test_abrir_reclamacao_recusa_reserva_de_outro_hotel(ambiente):
    with ambiente.engine.begin() as conexao:
        id_reserva, id_mensagem = _reserva_e_mensagem(
            conexao, ambiente.propriedade_b.id_hotel
        )
        with pytest.raises(HotelIncompativel):
            abrir_reclamacao(
                conexao,
                id_hotel=ambiente.propriedade_a.id_hotel,
                id_reserva=id_reserva,
                id_mensagem=id_mensagem,
                descricao="o ar nao gela",
                numero_quarto=None,
                urgencia="alta",
                janela_preferencia=None,
            )
        quantidade = conexao.execute(
            text("SELECT COUNT(*) FROM solicitacao WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        assert quantidade == 0


@pytest.mark.postgres
def test_completar_janela_preenche_reclamacao_aberta_mais_antiga(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva, id_mensagem = _reserva_e_mensagem(
            conexao, id_hotel, "o ar nao gela"
        )
        id_solicitacao = abrir_reclamacao(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            descricao="o ar nao gela",
            numero_quarto=None,
            urgencia="alta",
            janela_preferencia=None,
        )
        assert completar_janela_se_resposta(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            texto="o chuveiro tambem vazou",
        ) is None
        preenchida = completar_janela_se_resposta(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            texto="depois das 14h",
        )
        assert preenchida == id_solicitacao
        janela = conexao.execute(
            text(
                "SELECT janela_preferencia FROM solicitacao"
                " WHERE id_solicitacao = :id"
            ),
            {"id": id_solicitacao},
        ).scalar_one()
        assert janela == "depois das 14h"
        segunda = completar_janela_se_resposta(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            texto="depois das 16h",
        )
        assert segunda == id_solicitacao
        janela_final = conexao.execute(
            text(
                "SELECT janela_preferencia FROM solicitacao"
                " WHERE id_solicitacao = :id"
            ),
            {"id": id_solicitacao},
        ).scalar_one()
        assert janela_final == "depois das 14h"


@pytest.mark.postgres
def test_completar_janela_nao_preenche_outro_hotel_nem_sem_chamado(ambiente):
    with ambiente.engine.begin() as conexao:
        id_reserva, _ = _reserva_e_mensagem(
            conexao, ambiente.propriedade_b.id_hotel
        )
        assert completar_janela_se_resposta(
            conexao,
            id_hotel=ambiente.propriedade_a.id_hotel,
            id_reserva=id_reserva,
            texto="depois das 14h",
        ) is None
        id_a, _ = _reserva_e_mensagem(
            conexao, ambiente.propriedade_a.id_hotel
        )
        assert completar_janela_se_resposta(
            conexao,
            id_hotel=ambiente.propriedade_a.id_hotel,
            id_reserva=id_a,
            texto="depois das 14h",
        ) is None
