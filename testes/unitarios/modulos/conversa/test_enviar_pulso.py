"""Envio do pulso: falha retoma o mesmo trabalho; janela fechada conclui sem porta."""

import pytest
from sqlalchemy import text

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.modulos.atendimento.service import abrir_reclamacao
from app.modulos.conversa import service as conversa
from testes.suporte.pulso import montar_hospedado_para_pulso
from worker.agendador import verificar_pulsos_pendentes


def _trabalho_pendente(conexao, id_reserva: int) -> dict:
    linha = conexao.execute(
        text(
            "SELECT id_trabalho, id_hotel, tipo, payload, status, tentativas"
            " FROM trabalho"
            " WHERE tipo = 'enviar_pulso'"
            " AND (payload->>'id_reserva')::bigint = :r"
        ),
        {"r": id_reserva},
    ).mappings().one()
    return dict(linha)


@pytest.mark.postgres
def test_falha_de_envio_nao_apaga_o_trabalho(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    porta = MensageriaFalsa()
    porta.falhar_sempre = True
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000901"
        )
        verificar_pulsos_pendentes(conexao)
        trabalho = _trabalho_pendente(conexao, id_reserva)
        conversa.processar_trabalho_enviar_pulso(
            conexao, trabalho=trabalho, gateway=porta
        )
        status = conexao.execute(
            text("SELECT status FROM trabalho WHERE id_trabalho = :id"),
            {"id": trabalho["id_trabalho"]},
        ).scalar_one()
        envio = conexao.execute(
            text(
                "SELECT status_envio FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'enviada'"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert status in ("pendente", "processando")
    assert envio == "pendente"
    assert porta.envios == []


@pytest.mark.postgres
def test_reprocessar_ainda_elegivel_chama_a_porta_de_novo(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    porta = MensageriaFalsa()
    porta.falhas_restantes = 1
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000902"
        )
        verificar_pulsos_pendentes(conexao)
        trabalho = _trabalho_pendente(conexao, id_reserva)
        conversa.processar_trabalho_enviar_pulso(
            conexao, trabalho=trabalho, gateway=porta
        )
        trabalho = _trabalho_pendente(conexao, id_reserva)
        conversa.processar_trabalho_enviar_pulso(
            conexao, trabalho=trabalho, gateway=porta
        )
        status = conexao.execute(
            text("SELECT status FROM trabalho WHERE id_trabalho = :id"),
            {"id": trabalho["id_trabalho"]},
        ).scalar_one()
    assert status == "concluido"
    assert len([e for e in porta.envios if e["tipo"] == "pulso"]) == 1


@pytest.mark.postgres
def test_inelegivel_marca_concluido_sem_chamar_a_porta(ambiente, caplog):
    caplog.set_level("INFO")
    id_hotel = ambiente.propriedade_a.id_hotel
    porta = MensageriaFalsa()
    with ambiente.engine.begin() as conexao:
        id_reserva = montar_hospedado_para_pulso(
            conexao, id_hotel=id_hotel, telefone="5511910000903"
        )
        verificar_pulsos_pendentes(conexao)
        id_msg = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
                "VALUES (:r, 'recebida', 'ar') RETURNING id_mensagem"
            ),
            {"r": id_reserva},
        ).scalar_one()
        abrir_reclamacao(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_msg,
            descricao="ar",
            numero_quarto="101",
            urgencia="media",
            janela_preferencia=None,
        )
        trabalho = _trabalho_pendente(conexao, id_reserva)
        conversa.processar_trabalho_enviar_pulso(
            conexao, trabalho=trabalho, gateway=porta
        )
        status = conexao.execute(
            text("SELECT status FROM trabalho WHERE id_trabalho = :id"),
            {"id": trabalho["id_trabalho"]},
        ).scalar_one()
        envio = conexao.execute(
            text(
                "SELECT status_envio FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'enviada'"
            ),
            {"r": id_reserva},
        ).scalar_one()
    assert status == "concluido"
    assert envio == "pendente"
    assert porta.envios == []
    assert "Como esta" not in caplog.text
