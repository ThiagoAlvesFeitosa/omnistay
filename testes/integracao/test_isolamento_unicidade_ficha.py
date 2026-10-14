"""Unicidade ao consolidar ficha nao encerra a passagem."""

import pytest
from sqlalchemy import text

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from testes.suporte.isolamento_falha import excecao_com_cpf, trabalho_minimo
from worker.consumidor import processar_uma_passagem


def _reserva(conexao, id_hotel: int) -> int:
    return conexao.execute(
        text(
            "INSERT INTO reserva (id_hotel, telefone_contato,"
            " data_checkin_prevista, data_checkout_prevista) "
            "VALUES (:h, '5511970000099', CURRENT_DATE, CURRENT_DATE + 2) "
            "RETURNING id_reserva"
        ),
        {"h": id_hotel},
    ).scalar_one()


@pytest.mark.postgres
def test_unicidade_ao_consolidar_ficha_nao_derruba_a_passagem(
    ambiente, monkeypatch
):
    def _unicidade(conexao, **kwargs):
        raise excecao_com_cpf()

    monkeypatch.setattr(
        "worker.consumidor.conversa_service.processar_trabalho_interpretar_ficha",
        lambda conexao, **kwargs: _unicidade(conexao, **kwargs),
    )
    from app.fila import repository as fila_repo

    def _conclui(conexao, *, trabalho, **kwargs):
        fila_repo.marcar_concluido(conexao, id_trabalho=trabalho["id_trabalho"])

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
        processados = processar_uma_passagem(
            conexao, gateway=MensageriaFalsa()
        )
        assert processados == 2
        statuses = {
            row["id_trabalho"]: row["status"]
            for row in conexao.execute(
                text(
                    "SELECT id_trabalho, status FROM trabalho"
                    " WHERE id_trabalho IN (:a, :b)"
                ),
                {"a": id_ruim, "b": id_bom},
            ).mappings()
        }
        assert statuses[id_ruim] == "pendente"
        assert statuses[id_bom] == "concluido"
