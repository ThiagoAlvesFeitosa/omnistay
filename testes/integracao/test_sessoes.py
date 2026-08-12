"""Listagem, revogacao e expiracao de sessoes."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from testes.suporte.ambiente_de_acesso import criar_sessao


def _autenticar(cliente, usuario, dispositivo="dispositivo"):
    resposta = cliente.post(
        "/sessoes",
        json={
            "email": usuario.email,
            "senha": usuario.senha,
            "dispositivo": dispositivo,
        },
    )
    assert resposta.status_code == 201
    return resposta


@pytest.mark.postgres
def test_recepcao_lista_sessoes_sem_token(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    recepcao = ambiente.propriedade_a.usuarios["recepcao"]
    staff = ambiente.propriedade_a.usuarios["staff"]

    _autenticar(cliente, recepcao, "balcao")
    with ambiente.engine.begin() as conexao:
        criar_sessao(conexao, staff.id_usuario, dispositivo="celular")

    # Reautentica recepcao para cookie valido apos outra conexao
    cliente.cookies.clear()
    _autenticar(cliente, recepcao, "balcao")
    resposta = cliente.get("/sessoes")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) >= 2
    for item in corpo:
        assert "token" not in item
        assert "token_hash" not in item
        assert "nome_usuario" in item


@pytest.mark.postgres
def test_staff_e_gestor_recebem_403_ao_listar_e_revogar(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente

    for perfil in ("staff", "gestor"):
        cliente.cookies.clear()
        usuario = ambiente.propriedade_a.usuarios[perfil]
        _autenticar(cliente, usuario)
        assert cliente.get("/sessoes").status_code == 403
        assert cliente.delete("/sessoes/1").status_code == 403


@pytest.mark.postgres
def test_revogar_uma_sessao_nao_afeta_a_outra(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    recepcao = ambiente.propriedade_a.usuarios["recepcao"]
    staff = ambiente.propriedade_a.usuarios["staff"]

    with ambiente.engine.begin() as conexao:
        token_a, id_a = criar_sessao(conexao, staff.id_usuario, dispositivo="a")
        token_b, id_b = criar_sessao(conexao, staff.id_usuario, dispositivo="b")

    _autenticar(cliente, recepcao)
    revogar = cliente.delete(f"/sessoes/{id_a}")
    assert revogar.status_code == 204

    cliente.cookies.clear()
    cliente.cookies.set("omnistay_sessao", token_a)
    assert cliente.get("/sessoes/atual").status_code == 401

    cliente.cookies.clear()
    cliente.cookies.set("omnistay_sessao", token_b)
    assert cliente.get("/sessoes/atual").status_code == 200


@pytest.mark.postgres
def test_revogar_sessao_ja_revogada_e_idempotente(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    recepcao = ambiente.propriedade_a.usuarios["recepcao"]
    staff = ambiente.propriedade_a.usuarios["staff"]

    with ambiente.engine.begin() as conexao:
        _, id_sessao = criar_sessao(conexao, staff.id_usuario, revogada=True)

    _autenticar(cliente, recepcao)
    assert cliente.delete(f"/sessoes/{id_sessao}").status_code == 204
    assert cliente.delete(f"/sessoes/{id_sessao}").status_code == 204


@pytest.mark.postgres
def test_revogar_sessao_de_outro_hotel_responde_404(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    recepcao_a = ambiente.propriedade_a.usuarios["recepcao"]
    staff_b = ambiente.propriedade_b.usuarios["staff"]

    with ambiente.engine.begin() as conexao:
        _, id_sessao = criar_sessao(conexao, staff_b.id_usuario)

    _autenticar(cliente, recepcao_a)
    assert cliente.delete(f"/sessoes/{id_sessao}").status_code == 404


@pytest.mark.postgres
def test_sessao_expirada_e_recusada(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    staff = ambiente.propriedade_a.usuarios["staff"]

    with ambiente.engine.begin() as conexao:
        token, _ = criar_sessao(conexao, staff.id_usuario, expirada=True)

    cliente.cookies.set("omnistay_sessao", token)
    assert cliente.get("/sessoes/atual").status_code == 401


@pytest.mark.postgres
def test_max_age_do_staff_reflete_duracao_longa(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    staff = ambiente.propriedade_a.usuarios["staff"]

    resposta = _autenticar(cliente, staff)
    morsel = resposta.headers.get_list("set-cookie")[0].lower()
    # 720h = 2592000s; tolerancia de alguns segundos
    assert "max-age=" in morsel
    max_age = int(
        [p for p in morsel.split(";") if "max-age=" in p][0].split("=")[1]
    )
    assert 2_591_000 <= max_age <= 2_592_000
