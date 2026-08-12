"""Toda rota fora da lista publica fechada exige sessao."""

from fastapi.testclient import TestClient

from app.main import app

ROTAS_PUBLICAS = {
    ("GET", "/health"),
    ("POST", "/sessoes"),
    ("DELETE", "/sessoes/atual"),
}

# Documentacao automatica do FastAPI — nao sao recursos de dominio.
PREFIXOS_IGNORADOS = ("/docs", "/redoc", "/openapi.json")


def test_nenhuma_rota_protegida_dispensa_sessao():
    cliente = TestClient(app, base_url="https://testserver")
    desprotegidas = []

    for rota in app.routes:
        metodos = getattr(rota, "methods", None)
        caminho = getattr(rota, "path", None)
        if not metodos or not caminho:
            continue
        if any(caminho.startswith(p) for p in PREFIXOS_IGNORADOS):
            continue
        for metodo in metodos:
            if metodo in {"HEAD", "OPTIONS"}:
                continue
            chave = (metodo, caminho)
            if chave in ROTAS_PUBLICAS:
                continue
            caminho_requisicao = caminho
            for parte in caminho.split("/"):
                if parte.startswith("{") and parte.endswith("}"):
                    caminho_requisicao = caminho_requisicao.replace(parte, "1")

            resposta = cliente.request(metodo, caminho_requisicao)
            if resposta.status_code != 401:
                desprotegidas.append(
                    f"{metodo} {caminho} → {resposta.status_code}"
                )

    assert desprotegidas == [], (
        "Rotas fora da lista publica sem exigir sessao: "
        + "; ".join(desprotegidas)
    )
