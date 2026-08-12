"""Cadastro e desativacao de usuarios pela gestao."""

import pytest
from sqlalchemy import text

from testes.suporte.ambiente_de_acesso import criar_sessao


def _login(cliente, usuario):
    resposta = cliente.post(
        "/sessoes",
        json={"email": usuario.email, "senha": usuario.senha},
    )
    assert resposta.status_code == 201


@pytest.mark.postgres
def test_gestor_cria_usuario_que_autentica(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    gestor = ambiente.propriedade_a.usuarios["gestor"]
    _login(cliente, gestor)

    resposta = cliente.post(
        "/usuarios",
        json={
            "nome": "Novo Staff",
            "email": "novo@alpha.com",
            "perfil": "staff",
            "senha": "senha-nova-1234",
        },
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["perfil"] == "staff"
    assert "senha" not in corpo

    cliente.cookies.clear()
    login = cliente.post(
        "/sessoes",
        json={"email": "novo@alpha.com", "senha": "senha-nova-1234"},
    )
    assert login.status_code == 201


@pytest.mark.postgres
def test_recepcao_e_staff_nao_administram_usuario(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    for perfil in ("recepcao", "staff"):
        cliente.cookies.clear()
        _login(cliente, ambiente.propriedade_a.usuarios[perfil])
        assert (
            cliente.post(
                "/usuarios",
                json={
                    "nome": "X",
                    "email": f"x-{perfil}@alpha.com",
                    "perfil": "staff",
                    "senha": "senha-qualquer-123",
                },
            ).status_code
            == 403
        )
        assert cliente.delete("/usuarios/1").status_code == 403


@pytest.mark.postgres
def test_email_duplicado_e_perfil_invalido(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    gestor = ambiente.propriedade_a.usuarios["gestor"]
    staff = ambiente.propriedade_a.usuarios["staff"]
    _login(cliente, gestor)

    duplicado = cliente.post(
        "/usuarios",
        json={
            "nome": "Dup",
            "email": staff.email,
            "perfil": "staff",
            "senha": "senha-qualquer-123",
        },
    )
    invalido = cliente.post(
        "/usuarios",
        json={
            "nome": "X",
            "email": "supervisor@alpha.com",
            "perfil": "supervisor",
            "senha": "senha-qualquer-123",
        },
    )
    curta = cliente.post(
        "/usuarios",
        json={
            "nome": "X",
            "email": "curta@alpha.com",
            "perfil": "staff",
            "senha": "curta",
        },
    )

    assert duplicado.status_code == 409
    assert invalido.status_code == 422
    assert curta.status_code == 422


@pytest.mark.postgres
def test_desativar_derruba_sessoes_e_impede_login(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    gestor = ambiente.propriedade_a.usuarios["gestor"]
    staff = ambiente.propriedade_a.usuarios["staff"]

    with ambiente.engine.begin() as conexao:
        token_a, _ = criar_sessao(conexao, staff.id_usuario, dispositivo="a")
        token_b, _ = criar_sessao(conexao, staff.id_usuario, dispositivo="b")

    _login(cliente, gestor)
    assert cliente.delete(f"/usuarios/{staff.id_usuario}").status_code == 204

    for token in (token_a, token_b):
        cliente.cookies.clear()
        cliente.cookies.set("omnistay_sessao", token)
        assert cliente.get("/sessoes/atual").status_code == 401

    cliente.cookies.clear()
    assert (
        cliente.post(
            "/sessoes",
            json={"email": staff.email, "senha": staff.senha},
        ).status_code
        == 401
    )


@pytest.mark.postgres
def test_gestor_nao_desativa_a_si_mesmo(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    gestor = ambiente.propriedade_a.usuarios["gestor"]
    _login(cliente, gestor)

    assert cliente.delete(f"/usuarios/{gestor.id_usuario}").status_code == 409


@pytest.mark.postgres
def test_desativar_usuario_de_outro_hotel_responde_404(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    gestor_a = ambiente.propriedade_a.usuarios["gestor"]
    staff_b = ambiente.propriedade_b.usuarios["staff"]
    _login(cliente, gestor_a)

    assert cliente.delete(f"/usuarios/{staff_b.id_usuario}").status_code == 404
