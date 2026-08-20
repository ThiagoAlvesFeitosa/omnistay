"""Reclamacao aberta so conta conserto nao resolvido."""

import pytest
from sqlalchemy import text

from app.modulos.atendimento.service import (
    abrir_consumo,
    abrir_reclamacao,
    abrir_servico,
    tem_reclamacao_aberta,
)
from testes.suporte.consumo import NOME_ITEM, PRECO_ATUAL


def _mensagem(conexao, id_reserva: int, texto: str) -> int:
    return conexao.execute(
        text(
            "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
            "VALUES (:r, 'recebida', :c) RETURNING id_mensagem"
        ),
        {"r": id_reserva, "c": texto},
    ).scalar_one()


@pytest.mark.postgres
def test_tem_reclamacao_aberta_so_para_conserto_nao_resolvido(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = conexao.execute(
            text(
                "INSERT INTO reserva (id_hotel, telefone_contato,"
                " data_checkin_prevista, data_checkout_prevista) "
                "VALUES (:h, '5511910000201', CURRENT_DATE, CURRENT_DATE + 2) "
                "RETURNING id_reserva"
            ),
            {"h": id_hotel},
        ).scalar_one()
        id_msg = _mensagem(conexao, id_reserva, "ar condicionado")
        assert not tem_reclamacao_aberta(conexao, id_reserva=id_reserva)
        abrir_reclamacao(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_msg,
            descricao="ar condicionado",
            numero_quarto="201",
            urgencia="media",
            janela_preferencia=None,
        )
        assert tem_reclamacao_aberta(conexao, id_reserva=id_reserva)


@pytest.mark.postgres
def test_servico_e_consumo_nao_contam_como_reclamacao_aberta(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = conexao.execute(
            text(
                "INSERT INTO reserva (id_hotel, telefone_contato,"
                " data_checkin_prevista, data_checkout_prevista) "
                "VALUES (:h, '5511910000202', CURRENT_DATE, CURRENT_DATE + 2) "
                "RETURNING id_reserva"
            ),
            {"h": id_hotel},
        ).scalar_one()
        abrir_servico(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=_mensagem(conexao, id_reserva, "toalha"),
            descricao="toalha extra",
            numero_quarto="201",
            urgencia="baixa",
        )
        abrir_consumo(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=_mensagem(conexao, id_reserva, "cerveja"),
            descricao="cerveja",
            descricao_item=NOME_ITEM,
            valor_praticado=PRECO_ATUAL,
            numero_quarto="201",
            urgencia="baixa",
        )
        assert not tem_reclamacao_aberta(conexao, id_reserva=id_reserva)


@pytest.mark.postgres
def test_reclamacao_resolvida_nao_suprime(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = conexao.execute(
            text(
                "INSERT INTO reserva (id_hotel, telefone_contato,"
                " data_checkin_prevista, data_checkout_prevista) "
                "VALUES (:h, '5511910000203', CURRENT_DATE, CURRENT_DATE + 2) "
                "RETURNING id_reserva"
            ),
            {"h": id_hotel},
        ).scalar_one()
        id_solicitacao = abrir_reclamacao(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=_mensagem(conexao, id_reserva, "pia"),
            descricao="pia entupida",
            numero_quarto="201",
            urgencia="media",
            janela_preferencia=None,
        )
        conexao.execute(
            text(
                "UPDATE solicitacao SET status = 'resolvida',"
                " resolvida_em = now(), id_usuario_responsavel = :uid"
                " WHERE id_solicitacao = :id"
            ),
            {
                "id": id_solicitacao,
                "uid": ambiente.propriedade_a.usuarios["staff"].id_usuario,
            },
        )
        assert not tem_reclamacao_aberta(conexao, id_reserva=id_reserva)
