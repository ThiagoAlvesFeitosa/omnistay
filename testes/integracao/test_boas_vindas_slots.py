"""GET e PUT dos tres slots de boas-vindas."""

import pytest

from testes.integracao.test_reservas import _login


def _corpo(**kwargs):
    base = {
        "cafe": "Cafe da manha das 7h as 10h30",
        "wifi": "Wi-Fi: rede Hotel-Hospedes, senha 12345678",
        "checkout": "Checkout ate as 12h, bagagem na recepcao",
        "convite": "Pode perguntar sobre o cardapio e o horario do spa.",
    }
    base.update(kwargs)
    return base


@pytest.mark.postgres
def test_recepcao_le_e_grava_os_tres_slots(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])

    leitura = cliente.get("/propriedade/boas-vindas")
    assert leitura.status_code == 200
    atual = leitura.json()
    assert atual["cafe"]
    assert atual["wifi"]
    assert atual["checkout"]
    assert atual["convite"]

    gravacao = cliente.put("/propriedade/boas-vindas", json=_corpo())
    assert gravacao.status_code == 200
    assert gravacao.json() == _corpo()


@pytest.mark.postgres
def test_put_invalido_nao_altera_nada(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    antes = cliente.get("/propriedade/boas-vindas").json()

    resposta = cliente.put(
        "/propriedade/boas-vindas",
        json=_corpo(wifi="linha\nquebrada"),
    )
    assert resposta.status_code == 422
    assert "wifi" in resposta.json()["detail"].lower()
    assert cliente.get("/propriedade/boas-vindas").json() == antes


@pytest.mark.postgres
def test_gestao_le_e_nao_grava(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    assert cliente.get("/propriedade/boas-vindas").status_code == 200
    assert cliente.put("/propriedade/boas-vindas", json=_corpo()).status_code == 403


@pytest.mark.postgres
def test_staff_e_recusado_na_leitura_e_na_gravacao(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.get("/propriedade/boas-vindas").status_code == 403
    assert cliente.put("/propriedade/boas-vindas", json=_corpo()).status_code == 403


@pytest.mark.postgres
def test_hotel_b_nao_ve_valor_do_hotel_a(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    valor_a = cliente.get("/propriedade/boas-vindas").json()

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    valor_b = cliente.get("/propriedade/boas-vindas").json()
    assert valor_b["cafe"] != valor_a["cafe"]
    assert valor_b["wifi"] != valor_a["wifi"]
    assert valor_b["checkout"] != valor_a["checkout"]
    assert valor_b["convite"] != valor_a["convite"]


@pytest.mark.postgres
def test_put_sem_convite_e_recusado(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    tres = {
        "cafe": "Cafe da manha das 7h as 10h30",
        "wifi": "Wi-Fi: rede Hotel-Hospedes, senha 12345678",
        "checkout": "Checkout ate as 12h, bagagem na recepcao",
    }
    resposta = cliente.put("/propriedade/boas-vindas", json=tres)
    assert resposta.status_code == 422


@pytest.mark.postgres
def test_put_de_convite_com_quebra_nao_altera(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    antes = cliente.get("/propriedade/boas-vindas").json()
    resposta = cliente.put(
        "/propriedade/boas-vindas",
        json=_corpo(convite="Pode\nperguntar"),
    )
    assert resposta.status_code == 422
    assert "convite" in str(resposta.json()["detail"]).lower()
    assert cliente.get("/propriedade/boas-vindas").json() == antes
