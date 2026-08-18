"""Extracao conservadora do numero de quarto no texto do pedido."""

import re

_PADRAO = re.compile(
    r"(?:quarto|apartamento|apto|\buh)\s*(?:n[ºo°.]?\s*)?(\d+[A-Za-z]?)",
    re.IGNORECASE,
)


def extrair_numero_quarto(texto: str | None) -> str | None:
    if not texto or not texto.strip():
        return None
    achado = _PADRAO.search(texto)
    if achado is None:
        return None
    return achado.group(1)[:10]
