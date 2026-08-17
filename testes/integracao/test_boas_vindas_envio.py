"""Envio do recado de boas-vindas pelo worker."""

from datetime import date, timedelta

import pytest
from sqlalchemy import text

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.modulos.conversa import service as conversa
from testes.integracao.test_confirmar_chegada import _criar_elegivel
from testes.integracao.test_reservas import _login
from worker.consumidor import processar_uma_passagem_na_engine


def _apagar_slot(ambiente, id_hotel: int) -> None:
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "DELETE FROM parametro_hotel "
                "WHERE id_hotel = :h AND chave = 'boas_vindas_wifi'"
            ),
            {"h": id_hotel},
        )


def _trabalhos_boas_vindas(conexao, id_reserva: int):
    return conexao.execute(
        text(
            "SELECT status FROM trabalho "
            "WHERE tipo = 'enviar_boas_vindas' "
            "AND (payload->>'id_reserva')::bigint = :r"
        ),
        {"r": id_reserva},
    ).scalars().all()


def _mensagens_boas_vindas(conexao, id_reserva: int):
    return conexao.execute(
        text(
            "SELECT status_envio, enviada_em, id_externo, conteudo "
            "FROM mensagem WHERE id_reserva = :r "
            "AND conteudo LIKE '%chegada esta confirmada%'"
        ),
        {"r": id_reserva},
    ).mappings().all()


@pytest.mark.postgres
def test_worker_entrega_o_pacote_e_falha_nao_desfaz_checkin(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_elegivel(cliente, ambiente)

    resposta = cliente.post(f"/reservas/{id_reserva}/chegada")
    assert resposta.status_code == 200
    assert resposta.json()["boas_vindas"] == "agendada"

    with ambiente.conexao() as conexao:
        assert _trabalhos_boas_vindas(conexao, id_reserva) == ["pendente"]
        assert len(_mensagens_boas_vindas(conexao, id_reserva)) == 1
        assert _mensagens_boas_vindas(conexao, id_reserva)[0]["status_envio"] == "pendente"

    porta = MensageriaFalsa()
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta)
    envio = next(e for e in porta.envios if e["tipo"] == "boas_vindas")
    assert len(envio["variaveis"]) == 4

    with ambiente.conexao() as conexao:
        msg = _mensagens_boas_vindas(conexao, id_reserva)[0]
        assert msg["status_envio"] == "enviada"
        assert msg["enviada_em"] is not None
        assert msg["id_externo"]
        assert _trabalhos_boas_vindas(conexao, id_reserva) == ["concluido"]

    id_reserva_falha = _criar_elegivel(
        cliente, ambiente, nome="Joao Lima", telefone="11988887777"
    )
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "UPDATE parametro_hotel SET valor = '5' "
                "WHERE id_hotel = :h AND chave = 'tentativas_max_envio_mensagem'"
            ),
            {"h": ambiente.propriedade_a.id_hotel},
        )
    assert cliente.post(f"/reservas/{id_reserva_falha}/chegada").status_code == 200
    porta_falha = MensageriaFalsa()
    porta_falha.falhar_sempre = True
    processar_uma_passagem_na_engine(ambiente.engine, gateway=porta_falha)
    with ambiente.conexao() as conexao:
        linha = conexao.execute(
            text(
                "SELECT status, checkin_em FROM reserva WHERE id_reserva = :id"
            ),
            {"id": id_reserva_falha},
        ).mappings().one()
    assert linha["status"] == "hospedado"
    assert linha["checkin_em"] is not None


@pytest.mark.postgres
def test_slot_ausente_nao_envia_e_segunda_tentativa_e_ja_agendada(
    app_sobre_ambiente,
):
    cliente, ambiente = app_sobre_ambiente
    hotel = ambiente.propriedade_a.id_hotel
    _apagar_slot(ambiente, hotel)
    id_reserva = _criar_elegivel(cliente, ambiente)

    resposta = cliente.post(f"/reservas/{id_reserva}/chegada")
    assert resposta.status_code == 200
    assert resposta.json()["boas_vindas"] == "nao_enviada_slot_ausente"
    assert resposta.json()["status"] == "hospedado"
    with ambiente.conexao() as conexao:
        assert _trabalhos_boas_vindas(conexao, id_reserva) == []
        assert _mensagens_boas_vindas(conexao, id_reserva) == []

    id_ok = _criar_elegivel(
        cliente, ambiente, nome="Ana Souza", telefone="11966665555"
    )
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "INSERT INTO parametro_hotel (id_hotel, chave, valor) "
                "VALUES (:h, 'boas_vindas_wifi', 'rede Hotel') "
                "ON CONFLICT (id_hotel, chave) DO UPDATE SET valor = EXCLUDED.valor"
            ),
            {"h": hotel},
        )
    assert cliente.post(f"/reservas/{id_ok}/chegada").json()["boas_vindas"] == "agendada"

    with ambiente.engine.begin() as conexao:
        titular = conexao.execute(
            text(
                "SELECT h.nome_completo FROM hospede h "
                "JOIN reserva_hospede rh ON rh.id_hospede = h.id_hospede "
                "WHERE rh.id_reserva = :r AND rh.titular"
            ),
            {"r": id_ok},
        ).scalar_one()
        desfecho = conversa.agendar_boas_vindas(
            conexao,
            id_hotel=hotel,
            id_reserva=id_ok,
            nome_completo=titular,
        )
        assert desfecho == "ja_agendada"
        assert len(_mensagens_boas_vindas(conexao, id_ok)) == 1
        assert len(_trabalhos_boas_vindas(conexao, id_ok)) == 1


@pytest.mark.postgres
def test_recuperacao_envia_so_dentro_da_janela(app_sobre_ambiente):
    from worker.agendador import verificar_boas_vindas_pendentes

    cliente, ambiente = app_sobre_ambiente
    hotel = ambiente.propriedade_a.id_hotel
    _apagar_slot(ambiente, hotel)
    recente = _criar_elegivel(cliente, ambiente, nome="Recente", telefone="11922220001")
    antiga = _criar_elegivel(
        cliente,
        ambiente,
        nome="Antiga",
        telefone="11922220002",
        data_checkin_prevista=(date.today() - timedelta(days=3)).isoformat(),
        data_checkout_prevista=date.today().isoformat(),
    )
    assert cliente.post(f"/reservas/{recente}/chegada").json()["boas_vindas"] == (
        "nao_enviada_slot_ausente"
    )
    assert cliente.post(f"/reservas/{antiga}/chegada").json()["boas_vindas"] == (
        "nao_enviada_slot_ausente"
    )
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "UPDATE reserva SET checkin_em = now() - interval '40 minutes' "
                "WHERE id_reserva = :id"
            ),
            {"id": recente},
        )
        conexao.execute(
            text(
                "UPDATE reserva SET checkin_em = now() - interval '3 days' "
                "WHERE id_reserva = :id"
            ),
            {"id": antiga},
        )
        conexao.execute(
            text(
                "INSERT INTO parametro_hotel (id_hotel, chave, valor) "
                "VALUES (:h, 'boas_vindas_wifi', 'rede Hotel') "
                "ON CONFLICT (id_hotel, chave) DO UPDATE SET valor = EXCLUDED.valor"
            ),
            {"h": hotel},
        )
        n = verificar_boas_vindas_pendentes(conexao)
    assert n == 1
    with ambiente.conexao() as conexao:
        assert len(_trabalhos_boas_vindas(conexao, recente)) == 1
        assert len(_trabalhos_boas_vindas(conexao, antiga)) == 0
    itens = {i["id_reserva"]: i for i in cliente.get("/fila-do-dia").json()["itens"]}
    assert itens[antiga]["boas_vindas_nao_enviadas"] is True
