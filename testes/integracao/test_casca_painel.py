"""Casca do painel: estáticos em /app e atalho /demo."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import criar_aplicacao


def test_api_sobe_sem_dist(tmp_path: Path):
    aplicacao = criar_aplicacao(tmp_path / "inexistente")
    cliente = TestClient(aplicacao, base_url="https://testserver")
    assert cliente.get("/health").status_code == 200
    assert cliente.get("/app/").status_code == 404


def test_app_serve_html_quando_ha_dist(tmp_path: Path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html><body>casca</body></html>", encoding="utf-8")
    aplicacao = criar_aplicacao(dist)
    cliente = TestClient(aplicacao, base_url="https://testserver")
    raiz = cliente.get("/app/")
    assert raiz.status_code == 200
    assert "casca" in raiz.text
    entrar = cliente.get("/app/entrar")
    assert entrar.status_code == 200
    assert "casca" in entrar.text


def test_demo_redireciona_para_simulador_do_painel(tmp_path: Path):
    aplicacao = criar_aplicacao(tmp_path / "inexistente")
    cliente = TestClient(aplicacao, base_url="https://testserver", follow_redirects=False)
    for caminho in ("/demo", "/demo/"):
        resposta = cliente.get(caminho)
        assert resposta.status_code in {302, 307, 308}
        assert "/app/simulador" in (resposta.headers.get("location") or "")
