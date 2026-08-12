"""Contagem de chegadas do dia — so o numero."""

from datetime import date, timedelta

import pytest

from testes.integracao.test_reservas import _corpo_valido, _login


@pytest.mark.postgres
def test_gestor_ve_apenas_a_quantidade(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    cliente.post("/reservas", json=_corpo_valido())
    cliente.post("/reservas", json=_corpo_valido(nome="Outra", telefone="11966665555"))

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    resposta = cliente.get("/indicadores/chegadas-do-dia")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo == {"quantidade": 2}
    assert set(corpo.keys()) == {"quantidade"}


@pytest.mark.postgres
def test_recepcao_tambem_le_contagem_e_staff_e_recusado(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert cliente.get("/indicadores/chegadas-do-dia").json()["quantidade"] == 0

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.get("/indicadores/chegadas-do-dia").status_code == 403


@pytest.mark.postgres
def test_contagem_isola_hotel_e_ignora_checkin_outro_dia(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    cliente.post("/reservas", json=_corpo_valido())
    amanha = date.today() + timedelta(days=1)
    cliente.post(
        "/reservas",
        json=_corpo_valido(
            nome="Amanha",
            telefone="11955554444",
            data_checkin_prevista=amanha.isoformat(),
            data_checkout_prevista=(amanha + timedelta(days=1)).isoformat(),
        ),
    )

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    cliente.post("/reservas", json=_corpo_valido(nome="Beta", telefone="11944443333"))

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    assert cliente.get("/indicadores/chegadas-do-dia").json()["quantidade"] == 1
