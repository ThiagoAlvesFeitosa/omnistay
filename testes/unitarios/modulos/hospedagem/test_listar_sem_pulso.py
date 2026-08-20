"""Listagem de hospedados sem trabalho de pulso."""

import pytest

from app.modulos.hospedagem.service import listar_hospedados_sem_pulso
from testes.suporte.pulso import gravar_pulso_enviado, montar_hospedado_para_pulso


@pytest.mark.postgres
def test_lista_hospedado_sem_trabalho_de_pulso(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000301"
        )
        linhas = listar_hospedados_sem_pulso(conexao)
    ids = {item["id_reserva"] for item in linhas if item["id_hotel"] == id_hotel}
    assert id_reserva in ids
    candidata = next(item for item in linhas if item["id_reserva"] == id_reserva)
    assert candidata["checkin_em"] is not None
    assert candidata["data_checkout_prevista"] is not None
    assert candidata["nome_completo"]


@pytest.mark.postgres
def test_reserva_com_trabalho_de_pulso_nao_entra(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000302"
        )
        gravar_pulso_enviado(conexao, id_hotel=id_hotel, id_reserva=id_reserva)
        linhas = listar_hospedados_sem_pulso(conexao)
    ids = {item["id_reserva"] for item in linhas}
    assert id_reserva not in ids
