"""Consulta e revogacao de consentimento no painel."""

import pytest
from sqlalchemy import text

from testes.integracao.test_confirmar_saida import _criar_hospedada
from testes.integracao.test_reservas import _login


def _id_titular(ambiente, id_reserva: int) -> int:
    with ambiente.conexao() as conexao:
        return conexao.execute(
            text(
                "SELECT id_hospede FROM reserva_hospede"
                " WHERE id_reserva = :r AND titular"
            ),
            {"r": id_reserva},
        ).scalar_one()


@pytest.mark.postgres
def test_get_consentimento_recepcao_e_gestor_staff_recusado(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987654301")
    id_hospede = _id_titular(ambiente, id_reserva)

    resposta = cliente.get(f"/hospedes/{id_hospede}/consentimento")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["concedido"] is False
    assert corpo["momento"] is None
    assert corpo["origem"] is None

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    assert cliente.get(f"/hospedes/{id_hospede}/consentimento").status_code == 200

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.get(f"/hospedes/{id_hospede}/consentimento").status_code == 403


@pytest.mark.postgres
def test_post_append_only_e_origem_invalida(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987654302")
    id_hospede = _id_titular(ambiente, id_reserva)

    primeira = cliente.post(
        f"/hospedes/{id_hospede}/consentimento",
        json={"concedido": True, "origem": "painel"},
    )
    assert primeira.status_code == 201
    recusa = cliente.post(
        f"/hospedes/{id_hospede}/consentimento",
        json={"concedido": False, "origem": "solicitacao_titular"},
    )
    assert recusa.status_code == 201
    invalida = cliente.post(
        f"/hospedes/{id_hospede}/consentimento",
        json={"concedido": True, "origem": "pesquisa_checkout"},
    )
    assert invalida.status_code == 422
    with ambiente.conexao() as conexao:
        total = conexao.execute(
            text("SELECT COUNT(*) FROM consentimento WHERE id_hospede = :h"),
            {"h": id_hospede},
        ).scalar_one()
        primeiro_concedido = conexao.execute(
            text(
                "SELECT concedido FROM consentimento"
                " WHERE id_hospede = :h ORDER BY id_consentimento LIMIT 1"
            ),
            {"h": id_hospede},
        ).scalar_one()
    assert total == 2
    assert primeiro_concedido is True

    vigente = cliente.get(f"/hospedes/{id_hospede}/consentimento").json()
    assert vigente["concedido"] is False
    assert vigente["origem"] == "solicitacao_titular"


@pytest.mark.postgres
def test_staff_nao_registra_e_outro_hotel_e_404(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987654303")
    id_hospede = _id_titular(ambiente, id_reserva)

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.post(
        f"/hospedes/{id_hospede}/consentimento",
        json={"concedido": False, "origem": "painel"},
    ).status_code == 403

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    assert cliente.get(f"/hospedes/{id_hospede}/consentimento").status_code == 404
    assert cliente.post(
        f"/hospedes/{id_hospede}/consentimento",
        json={"concedido": False, "origem": "painel"},
    ).status_code == 404
