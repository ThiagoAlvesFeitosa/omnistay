"""Cookie Secure acompanha o esquema da requisicao."""

import pytest

from fastapi.testclient import TestClient

from app.main import app
from app.modulos.acesso.service import NOME_DO_COOKIE


def _partes_cookie(resposta) -> list[str]:
    bruto = resposta.headers.get_list("set-cookie")[0].lower()
    return [parte.strip() for parte in bruto.split(";")]


@pytest.mark.postgres
def test_cookie_http_nao_leva_secure(app_sobre_ambiente):
    _cliente_https, ambiente = app_sobre_ambiente
    gestor = ambiente.propriedade_a.usuarios["gestor"]

    with TestClient(app, base_url="http://testserver") as cliente_http:
        resposta = cliente_http.post(
            "/sessoes",
            json={"email": gestor.email, "senha": gestor.senha},
        )

    assert resposta.status_code == 201
    assert "token" not in resposta.json()
    partes = _partes_cookie(resposta)
    assert any(p.startswith(f"{NOME_DO_COOKIE}=") for p in partes)
    assert "httponly" in partes
    assert "samesite=strict" in partes
    assert "secure" not in partes


@pytest.mark.postgres
def test_cookie_https_leva_secure(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    gestor = ambiente.propriedade_a.usuarios["gestor"]

    resposta = cliente.post(
        "/sessoes",
        json={"email": gestor.email, "senha": gestor.senha},
    )

    assert resposta.status_code == 201
    assert "token" not in resposta.json()
    partes = _partes_cookie(resposta)
    assert "httponly" in partes
    assert "samesite=strict" in partes
    assert "secure" in partes
