"""Fila do dia da recepcao."""

from datetime import date, timedelta

import pytest

from testes.integracao.test_reservas import _corpo_valido, _login


@pytest.mark.postgres
def test_reserva_aparece_na_fila_do_dia(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    recepcao = ambiente.propriedade_a.usuarios["recepcao"]
    _login(cliente, recepcao)

    criada = cliente.post("/reservas", json=_corpo_valido()).json()
    fila = cliente.get("/fila-do-dia")
    assert fila.status_code == 200
    itens = fila.json()["itens"]
    assert len(itens) == 1
    item = itens[0]
    assert item["id_reserva"] == criada["id_reserva"]
    assert item["nome"] == "Maria Silva"
    assert item["telefone_contato"] == "5511987654321"
    assert item["status"] == "aguardando_cadastro"
    assert item["ficha_completa"] is False
    assert item["chegada_nao_confirmada"] is False


@pytest.mark.postgres
def test_chegada_passada_sem_confirmacao_e_sinalizada(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    ontem = date.today() - timedelta(days=1)
    cliente.post(
        "/reservas",
        json=_corpo_valido(
            data_checkin_prevista=ontem.isoformat(),
            data_checkout_prevista=date.today().isoformat(),
        ),
    )
    item = cliente.get("/fila-do-dia").json()["itens"][0]
    assert item["chegada_nao_confirmada"] is True


@pytest.mark.postgres
def test_fila_isola_hotels(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    cliente.post("/reservas", json=_corpo_valido(nome="Alpha"))

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    cliente.post("/reservas", json=_corpo_valido(nome="Beta", telefone="11977776666"))

    fila_b = cliente.get("/fila-do-dia").json()["itens"]
    assert len(fila_b) == 1
    assert fila_b[0]["nome"] == "Beta"

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    fila_a = cliente.get("/fila-do-dia").json()["itens"]
    assert len(fila_a) == 1
    assert fila_a[0]["nome"] == "Alpha"


@pytest.mark.postgres
def test_reserva_futura_nao_aparece_na_fila_do_dia(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])

    hoje = date.today()
    futura = hoje + timedelta(days=30)
    cliente.post(
        "/reservas",
        json=_corpo_valido(
            nome="Dezembro",
            telefone="11933332222",
            data_checkin_prevista=futura.isoformat(),
            data_checkout_prevista=(futura + timedelta(days=2)).isoformat(),
        ),
    )
    cliente.post("/reservas", json=_corpo_valido(nome="Hoje"))

    itens = cliente.get("/fila-do-dia").json()["itens"]
    nomes = [item["nome"] for item in itens]
    assert "Hoje" in nomes
    assert "Dezembro" not in nomes


@pytest.mark.postgres
def test_staff_e_gestor_nao_leem_fila_nominada(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    cliente.post("/reservas", json=_corpo_valido())

    for perfil in ("staff", "gestor"):
        cliente.cookies.clear()
        _login(cliente, ambiente.propriedade_a.usuarios[perfil])
        assert cliente.get("/fila-do-dia").status_code == 403
