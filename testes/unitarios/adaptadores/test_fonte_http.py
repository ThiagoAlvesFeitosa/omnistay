"""Fonte HTTP: fixture local, sem rede externa."""

from urllib.error import HTTPError

from app.adaptadores import fonte_http
from app.adaptadores.fonte_http import IDENTIDADE, FonteHttp, extrair_json_ld
from app.portas.fonte_publica import (
    DESFECHO_ENCONTRADO,
    DESFECHO_EXIGE_AUTENTICACAO,
    DESFECHO_INDISPONIVEL,
    DESFECHO_SEM_DADO,
    DIRETIVA_AUSENTE,
    DIRETIVA_PERMITE,
    DIRETIVA_RECUSA,
)

URL = "https://local.test/oferta"
ROBOTS = "https://local.test/robots.txt"

HTML_OFERTA = """
<html><head>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Hotel",
 "makesOffer":{"@type":"Offer","price":"150.00"},
 "aggregateRating":{"@type":"AggregateRating","ratingValue":"4.5"}}
</script>
</head><body>pagina</body></html>
"""


class _Resp:
    def __init__(self, corpo: str, status: int = 200):
        self.status = status
        self._corpo = corpo.encode("utf-8")

    def read(self):
        return self._corpo

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_json_ld_extrai_preco_e_nota():
    resultado = extrair_json_ld(HTML_OFERTA)
    assert resultado.desfecho == DESFECHO_ENCONTRADO
    assert str(resultado.preco) == "150.00"
    assert str(resultado.nota_media) == "4.5"


def test_html_sem_json_ld_e_sem_dado():
    resultado = extrair_json_ld("<html><body>sem dado estruturado</body></html>")
    assert resultado.desfecho == DESFECHO_SEM_DADO
    assert resultado.preco is None


def test_robots_ausente_nao_permite(monkeypatch):
    def urlopen(req, timeout=None):
        raise HTTPError(ROBOTS, 404, "not found", hdrs=None, fp=None)

    monkeypatch.setattr(fonte_http, "urlopen", urlopen)
    assert FonteHttp().consultar_diretiva(URL) == DIRETIVA_AUSENTE


def test_robots_vazio_nao_permite(monkeypatch):
    monkeypatch.setattr(
        fonte_http, "urlopen", lambda req, timeout=None: _Resp("")
    )
    assert FonteHttp().consultar_diretiva(URL) == DIRETIVA_AUSENTE


def test_robots_disallow_recusa(monkeypatch):
    corpo = "User-agent: *\nDisallow: /\n"
    monkeypatch.setattr(
        fonte_http, "urlopen", lambda req, timeout=None: _Resp(corpo)
    )
    assert FonteHttp().consultar_diretiva(URL) == DIRETIVA_RECUSA


def test_robots_allow_permite(monkeypatch):
    corpo = "User-agent: *\nAllow: /\n"
    monkeypatch.setattr(
        fonte_http, "urlopen", lambda req, timeout=None: _Resp(corpo)
    )
    assert FonteHttp().consultar_diretiva(URL) == DIRETIVA_PERMITE


def test_identidade_vai_no_user_agent(monkeypatch):
    vistos = []

    def urlopen(req, timeout=None):
        vistos.append(req)
        return _Resp(HTML_OFERTA)

    monkeypatch.setattr(fonte_http, "urlopen", urlopen)
    FonteHttp().coletar_publico(URL)
    assert vistos[0].get_header("User-agent") == IDENTIDADE


def test_401_exige_autenticacao(monkeypatch):
    def urlopen(req, timeout=None):
        raise HTTPError(URL, 401, "auth", hdrs=None, fp=None)

    monkeypatch.setattr(fonte_http, "urlopen", urlopen)
    resultado = FonteHttp().coletar_publico(URL)
    assert resultado.desfecho == DESFECHO_EXIGE_AUTENTICACAO


def test_500_e_indisponivel(monkeypatch):
    def urlopen(req, timeout=None):
        raise HTTPError(URL, 500, "erro", hdrs=None, fp=None)

    monkeypatch.setattr(fonte_http, "urlopen", urlopen)
    resultado = FonteHttp().coletar_publico(URL)
    assert resultado.desfecho == DESFECHO_INDISPONIVEL
