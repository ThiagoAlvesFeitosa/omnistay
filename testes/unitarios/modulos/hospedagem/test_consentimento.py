"""Consentimento append-only e consulta vigente."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from app.modulos.hospedagem import service as hospedagem
from testes.suporte.pulso import montar_hospedado_para_pulso


def _id_titular(conexao, id_reserva: int) -> int:
    return conexao.execute(
        text(
            "SELECT id_hospede FROM reserva_hospede"
            " WHERE id_reserva = :r AND titular"
        ),
        {"r": id_reserva},
    ).scalar_one()


@pytest.mark.postgres
def test_silencio_nao_insere_consentimento(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910001201"
        )
        saida = hospedagem.registrar_consentimento_pesquisa(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            concedido=None,
        )
        id_hospede = conexao.execute(
            text(
                "SELECT id_hospede FROM reserva_hospede"
                " WHERE id_reserva = :r AND titular"
            ),
            {"r": id_reserva},
        ).scalar_one()
        total = conexao.execute(
            text("SELECT COUNT(*) FROM consentimento WHERE id_hospede = :h"),
            {"h": id_hospede},
        ).scalar_one()
    assert saida is None
    assert total == 0


@pytest.mark.postgres
def test_aceite_insere_origem_pesquisa_checkout_sem_update(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910001202"
        )
        primeiro = hospedagem.registrar_consentimento_pesquisa(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            concedido=True,
        )
        segundo = hospedagem.registrar_consentimento_pesquisa(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            concedido=False,
        )
        linhas = conexao.execute(
            text(
                "SELECT concedido, origem FROM consentimento"
                " WHERE id_hospede = :h ORDER BY id_consentimento"
            ),
            {"h": primeiro["id_hospede"]},
        ).mappings().all()
    assert primeiro["origem"] == "pesquisa_checkout"
    assert primeiro["concedido"] is True
    assert segundo["concedido"] is False
    assert len(linhas) == 2
    assert linhas[0]["concedido"] is True
    assert linhas[1]["concedido"] is False


@pytest.mark.postgres
def test_vigente_responde_antes_entre_e_depois(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    agora = datetime.now(UTC)
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910001203"
        )
        id_hospede = _id_titular(conexao, id_reserva)
        conexao.execute(
            text(
                "INSERT INTO consentimento"
                " (id_hospede, finalidade, concedido, origem, momento)"
                " VALUES (:h, 'comunicacao_marketing', TRUE,"
                " 'pesquisa_checkout', :m)"
            ),
            {"h": id_hospede, "m": agora - timedelta(days=10)},
        )
        conexao.execute(
            text(
                "INSERT INTO consentimento"
                " (id_hospede, finalidade, concedido, origem, momento)"
                " VALUES (:h, 'comunicacao_marketing', FALSE, 'painel', :m)"
            ),
            {"h": id_hospede, "m": agora - timedelta(days=1)},
        )
        antes = hospedagem.consultar_consentimento_vigente(
            conexao,
            id_hotel=id_hotel,
            id_hospede=id_hospede,
            em=agora - timedelta(days=20),
        )
        meio = hospedagem.consultar_consentimento_vigente(
            conexao,
            id_hotel=id_hotel,
            id_hospede=id_hospede,
            em=agora - timedelta(days=5),
        )
        depois = hospedagem.consultar_consentimento_vigente(
            conexao,
            id_hotel=id_hotel,
            id_hospede=id_hospede,
            em=agora,
        )
    assert antes.concedido is False
    assert antes.momento is None
    assert meio.concedido is True
    assert meio.origem == "pesquisa_checkout"
    assert depois.concedido is False
    assert depois.origem == "painel"


@pytest.mark.postgres
def test_painel_recusa_origem_da_pesquisa(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910001204"
        )
        id_hospede = _id_titular(conexao, id_reserva)
        with pytest.raises(hospedagem.DadosInvalidos):
            hospedagem.registrar_consentimento_painel(
                conexao,
                id_hotel=id_hotel,
                id_hospede=id_hospede,
                concedido=True,
                origem="pesquisa_checkout",
            )
        total = conexao.execute(
            text("SELECT COUNT(*) FROM consentimento WHERE id_hospede = :h"),
            {"h": id_hospede},
        ).scalar_one()
    assert total == 0
