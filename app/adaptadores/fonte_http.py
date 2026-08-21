"""Fonte publica HTTP: stdlib, identidade honesta, so JSON-LD schema.org."""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from app.portas.fonte_publica import (
    DESFECHO_ENCONTRADO,
    DESFECHO_EXIGE_AUTENTICACAO,
    DESFECHO_INDISPONIVEL,
    DESFECHO_SEM_DADO,
    DIRETIVA_AUSENTE,
    DIRETIVA_PERMITE,
    DIRETIVA_RECUSA,
    ResultadoPublico,
)

IDENTIDADE = "OmniStay-Coletor/1.0"
TEMPO_LIMITE_SEGUNDOS = 10
_PADRAO_LD = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def _tipos(objeto: dict) -> set[str]:
    bruto = objeto.get("@type", "")
    if isinstance(bruto, list):
        valores = bruto
    else:
        valores = [bruto]
    return {str(item).rsplit("/", 1)[-1] for item in valores if item}


def _caminhar(objeto):
    if isinstance(objeto, list):
        for item in objeto:
            yield from _caminhar(item)
    elif isinstance(objeto, dict):
        yield objeto
        for valor in objeto.values():
            yield from _caminhar(valor)


def _decimal(valor) -> Decimal | None:
    if valor is None or valor == "":
        return None
    try:
        return Decimal(str(valor))
    except (InvalidOperation, ValueError):
        return None


def extrair_json_ld(html: str) -> ResultadoPublico:
    preco = None
    nota = None
    for bloco in _PADRAO_LD.findall(html):
        try:
            dados = json.loads(bloco)
        except json.JSONDecodeError:
            continue
        for objeto in _caminhar(dados):
            tipos = _tipos(objeto)
            if "Offer" in tipos and preco is None:
                preco = _decimal(objeto.get("price"))
            if "AggregateRating" in tipos and nota is None:
                nota = _decimal(objeto.get("ratingValue"))
    if preco is None and nota is None:
        return ResultadoPublico(desfecho=DESFECHO_SEM_DADO)
    return ResultadoPublico(
        desfecho=DESFECHO_ENCONTRADO, preco=preco, nota_media=nota
    )


class FonteHttp:
    def consultar_diretiva(self, url_fonte: str) -> str:
        origem = urlparse(url_fonte)
        robots = f"{origem.scheme}://{origem.netloc}/robots.txt"
        try:
            req = Request(robots, headers={"User-Agent": IDENTIDADE})
            with urlopen(req, timeout=TEMPO_LIMITE_SEGUNDOS) as resp:
                corpo = resp.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError, TimeoutError, OSError):
            return DIRETIVA_AUSENTE
        if not corpo.strip():
            return DIRETIVA_AUSENTE
        parser = RobotFileParser()
        parser.parse(corpo.splitlines())
        if parser.can_fetch(IDENTIDADE, url_fonte):
            return DIRETIVA_PERMITE
        return DIRETIVA_RECUSA

    def coletar_publico(self, url_fonte: str) -> ResultadoPublico:
        req = Request(url_fonte, headers={"User-Agent": IDENTIDADE})
        try:
            with urlopen(req, timeout=TEMPO_LIMITE_SEGUNDOS) as resp:
                html = resp.read().decode("utf-8", errors="replace")
        except HTTPError as erro:
            if erro.code in (401, 403):
                return ResultadoPublico(desfecho=DESFECHO_EXIGE_AUTENTICACAO)
            return ResultadoPublico(desfecho=DESFECHO_INDISPONIVEL)
        except (URLError, TimeoutError, OSError):
            return ResultadoPublico(desfecho=DESFECHO_INDISPONIVEL)
        return extrair_json_ld(html)
