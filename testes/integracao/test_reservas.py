"""Criacao de reserva pela recepcao."""

from datetime import date, timedelta

import pytest
from sqlalchemy import text


def _login(cliente, usuario):
    resposta = cliente.post(
        "/sessoes",
        json={"email": usuario.email, "senha": usuario.senha},
    )
    assert resposta.status_code == 201


def _corpo_valido(**kwargs):
    hoje = date.today()
    base = {
        "nome": "Maria Silva",
        "telefone": "(11) 98765-4321",
        "data_checkin_prevista": hoje.isoformat(),
        "data_checkout_prevista": (hoje + timedelta(days=3)).isoformat(),
    }
    base.update(kwargs)
    return base


@pytest.mark.postgres
def test_recepcao_cria_reserva_aguardando_cadastro(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    recepcao = ambiente.propriedade_a.usuarios["recepcao"]
    _login(cliente, recepcao)

    resposta = cliente.post("/reservas", json=_corpo_valido())
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "aguardando_cadastro"
    assert corpo["telefone_contato"] == "5511987654321"
    assert corpo["nome"] == "Maria Silva"
    assert corpo["id_hotel"] == recepcao.id_hotel

    with ambiente.conexao() as conexao:
        reservas = conexao.execute(
            text("SELECT COUNT(*) FROM reserva WHERE id_hotel = :h"),
            {"h": recepcao.id_hotel},
        ).scalar_one()
        hospedes = conexao.execute(text("SELECT COUNT(*) FROM hospede")).scalar_one()
        vinculos = conexao.execute(
            text(
                "SELECT titular, ficha_completa FROM reserva_hospede "
                "WHERE id_reserva = :r"
            ),
            {"r": corpo["id_reserva"]},
        ).mappings().one()
    assert reservas == 1
    assert hospedes == 1
    assert vinculos["titular"] is True
    assert vinculos["ficha_completa"] is False


@pytest.mark.postgres
def test_telefone_repetido_cria_segundo_hospede(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])

    assert cliente.post("/reservas", json=_corpo_valido(nome="Maria")).status_code == 201
    assert cliente.post("/reservas", json=_corpo_valido(nome="Joao")).status_code == 201

    with ambiente.conexao() as conexao:
        qtd = conexao.execute(
            text("SELECT COUNT(*) FROM hospede WHERE telefone = :t"),
            {"t": "5511987654321"},
        ).scalar_one()
        ids = list(
            conexao.execute(
                text("SELECT id_hospede FROM hospede WHERE telefone = :t"),
                {"t": "5511987654321"},
            ).scalars()
        )
    assert qtd == 2
    assert len(set(ids)) == 2


@pytest.mark.postgres
def test_telefone_invalido_e_datas_invertidas_nao_gravam(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    hotel = ambiente.propriedade_a.usuarios["recepcao"].id_hotel
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])

    telefone = cliente.post(
        "/reservas", json=_corpo_valido(telefone="123")
    )
    assert telefone.status_code == 422
    assert "telefone" in telefone.json()["detail"].lower() or "DDD" in telefone.json()["detail"]

    hoje = date.today()
    datas = cliente.post(
        "/reservas",
        json=_corpo_valido(
            data_checkin_prevista=(hoje + timedelta(days=3)).isoformat(),
            data_checkout_prevista=hoje.isoformat(),
        ),
    )
    assert datas.status_code == 422
    assert "saida" in datas.json()["detail"].lower() or "entrada" in datas.json()["detail"].lower()

    with ambiente.conexao() as conexao:
        assert (
            conexao.execute(
                text("SELECT COUNT(*) FROM reserva WHERE id_hotel = :h"),
                {"h": hotel},
            ).scalar_one()
            == 0
        )
        assert conexao.execute(text("SELECT COUNT(*) FROM hospede")).scalar_one() == 0


@pytest.mark.postgres
def test_staff_e_gestor_nao_cadastram_reserva(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    for perfil in ("staff", "gestor"):
        cliente.cookies.clear()
        _login(cliente, ambiente.propriedade_a.usuarios[perfil])
        assert cliente.post("/reservas", json=_corpo_valido()).status_code == 403

    with ambiente.conexao() as conexao:
        assert conexao.execute(text("SELECT COUNT(*) FROM reserva")).scalar_one() == 0
