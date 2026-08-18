"""Extracao conservadora da janela de preferencia no texto do hospede."""

import re

_PADROES = [
    re.compile(r"depois das?\s+\d{1,2}(?::\d{2})?\s*(?:h(?:oras)?)?", re.I),
    re.compile(r"a partir das?\s+\d{1,2}(?::\d{2})?\s*(?:h(?:oras)?)?", re.I),
    re.compile(r"antes das?\s+\d{1,2}(?::\d{2})?\s*(?:h(?:oras)?)?", re.I),
    re.compile(r"de manh[ãa]", re.I),
    re.compile(r"de tarde", re.I),
    re.compile(r"(?:à|a)\s+noite", re.I),
    re.compile(r"o quanto antes", re.I),
    re.compile(r"imediatamente", re.I),
    re.compile(r"\bagora\b", re.I),
    re.compile(r"\d{1,2}:\d{2}"),
    re.compile(r"\d{1,2}h(?:oras)?", re.I),
]


def extrair_janela_preferencia(texto: str | None) -> str | None:
    if not texto or not texto.strip():
        return None
    for padrao in _PADROES:
        achado = padrao.search(texto)
        if achado is None:
            continue
        trecho = achado.group(0).strip()
        return trecho[:60]
    return None


def parece_resposta_de_horario(texto: str | None) -> bool:
    if not texto or not texto.strip():
        return False
    limpo = texto.strip().rstrip(".,;!? ").strip()
    janela = extrair_janela_preferencia(limpo)
    return janela is not None and janela.casefold() == limpo.casefold()
