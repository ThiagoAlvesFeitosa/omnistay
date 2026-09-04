"""Autenticacao HTTP: cookie, recurso protegido, recusas indistinguiveis."""

import logging

import pytest
from sqlalchemy import text

from testes.suporte.ambiente_de_acesso import criar_sessao


@pytest.fixture
def cliente_e_ambiente(app_sobre_ambiente):
    return app_sobre_ambiente


@pytest.mark.postgres
def test_autenticacao_define_cookie_com_atributos_de_seguranca(cliente_e_ambiente):
    cliente, ambiente = cliente_e_ambiente
    gestor = ambiente.propriedade_a.usuarios["gestor"]

    resposta = cliente.post(
        "/sessoes",
        json={
            "email": gestor.email,
            "senha": gestor.senha,
            "dispositivo": "Notebook da gestao",
        },
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["perfil"] == "gestor"
    assert "token" not in corpo
    assert "senha" not in corpo
    cookie = resposta.cookies.get("omnistay_sessao")
    assert cookie
    # httpx/Starlette expoe atributos do cookie setado
    morsel = resposta.headers.get_list("set-cookie")[0].lower()
    assert "httponly" in morsel
    assert "secure" in morsel
    assert "samesite=strict" in morsel
    assert "path=/" in morsel
    assert "max-age=" in morsel


@pytest.mark.postgres
def test_token_nao_aparece_no_corpo_da_autenticacao(cliente_e_ambiente):
    cliente, ambiente = cliente_e_ambiente
    gestor = ambiente.propriedade_a.usuarios["gestor"]

    resposta = cliente.post(
        "/sessoes",
        json={"email": gestor.email, "senha": gestor.senha},
    )

    texto = resposta.text.lower()
    assert "omnistay_sessao" not in texto or "set-cookie" in resposta.headers.get(
        "set-cookie", ""
    ).lower()
    assert resposta.json().get("token") is None


@pytest.mark.postgres
def test_recusas_de_credencial_sao_indistinguiveis(cliente_e_ambiente):
    cliente, ambiente = cliente_e_ambiente
    gestor = ambiente.propriedade_a.usuarios["gestor"]

    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text("UPDATE usuario SET ativo = FALSE WHERE email = :email"),
            {"email": gestor.email},
        )

    respostas = [
        cliente.post(
            "/sessoes",
            json={"email": gestor.email, "senha": "senha-errada-12345"},
        ),
        cliente.post(
            "/sessoes",
            json={"email": "ninguem@hotel.com.br", "senha": "senha-errada-12345"},
        ),
        cliente.post(
            "/sessoes",
            json={"email": gestor.email, "senha": gestor.senha},
        ),
    ]

    assert {r.status_code for r in respostas} == {401}
    assert {r.json()["detail"] for r in respostas} == {"Credenciais invalidas."}


@pytest.mark.postgres
def test_recurso_protegido_exige_sessao_valida(cliente_e_ambiente):
    cliente, ambiente = cliente_e_ambiente
    gestor = ambiente.propriedade_a.usuarios["gestor"]

    sem = cliente.get("/sessoes/atual")
    forjada = cliente.get(
        "/sessoes/atual", cookies={"omnistay_sessao": "token-inventado"}
    )

    login = cliente.post(
        "/sessoes",
        json={"email": gestor.email, "senha": gestor.senha, "dispositivo": "pc"},
    )
    com = cliente.get("/sessoes/atual")

    assert sem.status_code == 401
    assert forjada.status_code == 401
    assert sem.json() == forjada.json()
    assert login.status_code == 201
    assert com.status_code == 200
    assert com.json()["perfil"] == "gestor"


@pytest.mark.postgres
def test_sessao_inclui_nome_hotel_da_propriedade_da_pessoa(cliente_e_ambiente):
    cliente, ambiente = cliente_e_ambiente
    gestor_a = ambiente.propriedade_a.usuarios["gestor"]
    gestor_b = ambiente.propriedade_b.usuarios["gestor"]

    login_a = cliente.post(
        "/sessoes",
        json={"email": gestor_a.email, "senha": gestor_a.senha},
    )
    atual_a = cliente.get("/sessoes/atual")

    assert login_a.status_code == 201
    assert login_a.json()["nome_hotel"] == ambiente.propriedade_a.nome
    assert "id_hotel" not in login_a.json()
    assert atual_a.status_code == 200
    assert atual_a.json()["nome_hotel"] == ambiente.propriedade_a.nome
    assert "id_hotel" not in atual_a.json()

    cliente.delete("/sessoes/atual")
    login_b = cliente.post(
        "/sessoes",
        json={"email": gestor_b.email, "senha": gestor_b.senha},
    )
    atual_b = cliente.get("/sessoes/atual")

    assert login_b.json()["nome_hotel"] == ambiente.propriedade_b.nome
    assert atual_b.json()["nome_hotel"] == ambiente.propriedade_b.nome
    assert login_b.json()["nome_hotel"] != ambiente.propriedade_a.nome


@pytest.mark.postgres
def test_recusa_de_credencial_nao_traz_nome_hotel(cliente_e_ambiente):
    cliente, ambiente = cliente_e_ambiente
    gestor = ambiente.propriedade_a.usuarios["gestor"]

    recusa = cliente.post(
        "/sessoes",
        json={"email": gestor.email, "senha": "senha-errada-12345"},
    )

    assert recusa.status_code == 401
    assert "nome_hotel" not in recusa.json()


@pytest.mark.postgres
def test_encerrar_sessao_invalida_o_cookie(cliente_e_ambiente):
    cliente, ambiente = cliente_e_ambiente
    gestor = ambiente.propriedade_a.usuarios["gestor"]

    cliente.post(
        "/sessoes",
        json={"email": gestor.email, "senha": gestor.senha},
    )
    encerrar = cliente.delete("/sessoes/atual")
    depois = cliente.get("/sessoes/atual")
    sem_sessao = cliente.delete("/sessoes/atual")

    assert encerrar.status_code == 204
    assert depois.status_code == 401
    assert sem_sessao.status_code == 204


@pytest.mark.postgres
def test_log_nao_registra_senha_nem_token(cliente_e_ambiente, caplog):
    cliente, ambiente = cliente_e_ambiente
    gestor = ambiente.propriedade_a.usuarios["gestor"]

    with caplog.at_level(logging.INFO):
        cliente.post(
            "/sessoes",
            json={"email": gestor.email, "senha": gestor.senha},
        )
        cliente.post(
            "/sessoes",
            json={"email": gestor.email, "senha": "senha-errada-12345"},
        )

    assert gestor.senha not in caplog.text
    assert "omnistay_sessao=" not in caplog.text
