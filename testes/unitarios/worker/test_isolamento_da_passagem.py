"""Passagem: um trabalho que estoura nao impede o seguinte."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.fila import repository as fila_repo
from testes.suporte.isolamento_falha import (
    CPF_NA_MENSAGEM,
    excecao_com_cpf,
    trabalho_minimo,
)
from worker.consumidor import processar_uma_passagem


def _reserva(conexao, id_hotel: int) -> int:
    return conexao.execute(
        text(
            "INSERT INTO reserva (id_hotel, telefone_contato,"
            " data_checkin_prevista, data_checkout_prevista) "
            "VALUES (:h, '5511970000001', CURRENT_DATE, CURRENT_DATE + 2) "
            "RETURNING id_reserva"
        ),
        {"h": id_hotel},
    ).scalar_one()


def _status(conexao, id_trabalho: int) -> dict:
    return dict(
        conexao.execute(
            text(
                "SELECT status, tentativas, proxima_tentativa_em, erro_ultima_tentativa"
                " FROM trabalho WHERE id_trabalho = :id"
            ),
            {"id": id_trabalho},
        ).mappings().one()
    )


def _estoura(conexao, **kwargs):
    raise RuntimeError("estouro isolado")


def _conclui(conexao, *, trabalho, **kwargs):
    fila_repo.marcar_concluido(conexao, id_trabalho=trabalho["id_trabalho"])


@pytest.mark.postgres
def test_trabalho_com_excecao_e_reagendado_e_o_seguinte_corre(
    ambiente, monkeypatch
):
    monkeypatch.setattr(
        "worker.consumidor.conversa_service.processar_trabalho_interpretar_ficha",
        _estoura,
    )
    monkeypatch.setattr(
        "worker.consumidor.conversa_service.processar_trabalho_enviar_lembrete",
        _conclui,
    )
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        ruim = _reserva(conexao, id_hotel)
        boa = _reserva(conexao, id_hotel)
        id_ruim = trabalho_minimo(
            conexao, "interpretar_ficha", id_hotel=id_hotel, id_reserva=ruim
        )
        id_bom = trabalho_minimo(
            conexao, "enviar_lembrete", id_hotel=id_hotel, id_reserva=boa
        )
        agora = datetime.now(UTC)
        processados = processar_uma_passagem(
            conexao, gateway=MensageriaFalsa()
        )
        assert processados == 2
        estado_ruim = _status(conexao, id_ruim)
        estado_bom = _status(conexao, id_bom)
        assert estado_ruim["status"] == "pendente"
        assert estado_ruim["tentativas"] == 1
        assert estado_ruim["proxima_tentativa_em"] is not None
        assert estado_ruim["proxima_tentativa_em"] > agora
        assert estado_bom["status"] == "concluido"


@pytest.mark.postgres
def test_no_teto_o_trabalho_fica_em_falha_e_nao_e_reclamado(
    ambiente, monkeypatch
):
    monkeypatch.setattr(
        "worker.consumidor.conversa_service.processar_trabalho_interpretar_ficha",
        _estoura,
    )
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = _reserva(conexao, id_hotel)
        id_trabalho = trabalho_minimo(
            conexao,
            "interpretar_ficha",
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            tentativas=4,
        )
        processados = processar_uma_passagem(
            conexao, gateway=MensageriaFalsa()
        )
        assert processados == 1
        estado = _status(conexao, id_trabalho)
        assert estado["status"] == "falha"
        assert estado["tentativas"] == 5
        segunda = processar_uma_passagem(conexao, gateway=MensageriaFalsa())
        assert segunda == 0
        assert fila_repo.reclamar_proximo(conexao) is None


@pytest.mark.postgres
def test_concluido_permanece_quando_outro_trabalho_falha(ambiente, monkeypatch):
    monkeypatch.setattr(
        "worker.consumidor.conversa_service.processar_trabalho_enviar_lembrete",
        _conclui,
    )
    monkeypatch.setattr(
        "worker.consumidor.conversa_service.processar_trabalho_interpretar_ficha",
        _estoura,
    )
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        boa = _reserva(conexao, id_hotel)
        ruim = _reserva(conexao, id_hotel)
        id_bom = trabalho_minimo(
            conexao, "enviar_lembrete", id_hotel=id_hotel, id_reserva=boa
        )
        trabalho_minimo(
            conexao, "interpretar_ficha", id_hotel=id_hotel, id_reserva=ruim
        )
        processar_uma_passagem(conexao, gateway=MensageriaFalsa())
        assert _status(conexao, id_bom)["status"] == "concluido"


@pytest.mark.postgres
def test_registro_da_falha_nao_repete_cpf_da_mensagem(ambiente, monkeypatch):
    def _estoura_com_cpf(conexao, **kwargs):
        raise excecao_com_cpf()

    registros = []

    def _info(msg, *args, **kwargs):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(
        "worker.consumidor.conversa_service.processar_trabalho_interpretar_ficha",
        _estoura_com_cpf,
    )
    monkeypatch.setattr("worker.consumidor.logger.info", _info)
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_reserva = _reserva(conexao, id_hotel)
        id_trabalho = trabalho_minimo(
            conexao,
            "interpretar_ficha",
            id_hotel=id_hotel,
            id_reserva=id_reserva,
        )
        processar_uma_passagem(conexao, gateway=MensageriaFalsa())
        estado = _status(conexao, id_trabalho)
    assert estado["erro_ultima_tentativa"] == "IntegrityError"
    assert CPF_NA_MENSAGEM not in (estado["erro_ultima_tentativa"] or "")
    texto_log = " ".join(registros)
    assert CPF_NA_MENSAGEM not in texto_log
    assert "IntegrityError" in texto_log
