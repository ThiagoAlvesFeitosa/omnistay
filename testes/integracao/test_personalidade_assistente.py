"""GET e PUT da descricao de tom da assistente."""

import pytest

from testes.integracao.test_reservas import _login


def _corpo(texto="Seja breve e caloroso."):
    return {"texto": texto}


@pytest.mark.postgres
def test_gestor_grava_e_le_o_tom(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])

    leitura = cliente.get("/propriedade/personalidade")
    assert leitura.status_code == 200
    assert leitura.json() == {"texto": ""}

    gravacao = cliente.put("/propriedade/personalidade", json=_corpo())
    assert gravacao.status_code == 200
    assert gravacao.json() == _corpo()
    assert cliente.get("/propriedade/personalidade").json() == _corpo()

    vazio = cliente.put("/propriedade/personalidade", json={"texto": "   "})
    assert vazio.status_code == 200
    assert vazio.json() == {"texto": ""}


@pytest.mark.postgres
def test_put_longo_nao_altera_valor_anterior(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    cliente.put("/propriedade/personalidade", json=_corpo("curto"))
    resposta = cliente.put(
        "/propriedade/personalidade", json={"texto": "z" * 501}
    )
    assert resposta.status_code == 422
    assert "longo" in resposta.json()["detail"].lower()
    assert cliente.get("/propriedade/personalidade").json() == {"texto": "curto"}


@pytest.mark.postgres
def test_recepcao_le_e_nao_grava(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert cliente.get("/propriedade/personalidade").status_code == 200
    assert cliente.put("/propriedade/personalidade", json=_corpo()).status_code == 403


@pytest.mark.postgres
def test_staff_e_recusado_na_leitura_e_na_gravacao(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.get("/propriedade/personalidade").status_code == 403
    assert cliente.put("/propriedade/personalidade", json=_corpo()).status_code == 403


@pytest.mark.postgres
def test_sem_cookie_responde_401(app_sobre_ambiente):
    cliente, _ambiente = app_sobre_ambiente
    assert cliente.get("/propriedade/personalidade").status_code == 401
    assert cliente.put("/propriedade/personalidade", json=_corpo()).status_code == 401


@pytest.mark.postgres
def test_hotel_b_nao_ve_tom_do_hotel_a(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    cliente.put(
        "/propriedade/personalidade", json=_corpo("tom do hotel a")
    )

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["gestor"])
    valor_b = cliente.get("/propriedade/personalidade").json()
    assert valor_b["texto"] != "tom do hotel a"
