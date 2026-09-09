"""Fidelidade da resposta automatica ao catalogo ativo — funcao pura."""

import unicodedata

from app.portas.catalogo import ItemCatalogo


def formatar_item_catalogo(item: ItemCatalogo) -> str:
    return f"{item.titulo}: {item.conteudo}"


def _normalizar(valor: str) -> str:
    sem_marca = "".join(
        caractere
        for caractere in unicodedata.normalize("NFKD", valor)
        if unicodedata.category(caractere) != "Mn"
    )
    return " ".join(sem_marca.split()).casefold()


def resposta_fiel_ao_catalogo(
    texto: str,
    trechos: tuple[str, ...],
    itens: tuple[ItemCatalogo, ...],
) -> bool:
    if not (texto or "").strip() or not trechos:
        return False
    corpus = tuple(_normalizar(formatar_item_catalogo(item)) for item in itens)
    enviado = _normalizar(texto)
    for trecho in trechos:
        normalizado = _normalizar(trecho)
        if not normalizado:
            return False
        if not any(normalizado in bloco for bloco in corpus):
            return False
        if normalizado not in enviado:
            return False
    return True
