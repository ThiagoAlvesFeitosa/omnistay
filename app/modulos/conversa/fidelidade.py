"""Fidelidade da resposta automatica ao catalogo ativo — funcao pura."""

from app.portas.catalogo import ItemCatalogo


def resposta_fiel_ao_catalogo(
    texto: str,
    trechos: tuple[str, ...],
    itens: tuple[ItemCatalogo, ...],
) -> bool:
    if not (texto or "").strip() or not trechos:
        return False
    corpus = tuple((item.titulo + " " + item.conteudo).casefold() for item in itens)
    enviado = texto.casefold()
    for trecho in trechos:
        normalizado = trecho.strip().casefold()
        if not normalizado:
            return False
        if not any(normalizado in bloco for bloco in corpus):
            return False
        if normalizado not in enviado:
            return False
    return True
