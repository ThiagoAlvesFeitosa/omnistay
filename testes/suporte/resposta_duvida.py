"""Factories de item de catalogo e ResultadoResposta."""

from app.portas.catalogo import ItemCatalogo
from app.portas.llm import ResultadoResposta


def item_cafe(*, id_hotel: int = 1, id_catalogo_item: int = 1) -> ItemCatalogo:
    del id_hotel
    return ItemCatalogo(
        id_catalogo_item=id_catalogo_item,
        categoria="horario",
        titulo="Cafe da manha",
        conteudo="7h as 10h",
    )


def item_outro_hotel(*, id_catalogo_item: int = 99) -> ItemCatalogo:
    return ItemCatalogo(
        id_catalogo_item=id_catalogo_item,
        categoria="horario",
        titulo="Piscina",
        conteudo="piscina olimpica 6h",
    )


def resposta_coberta(
    *, texto: str = "7h as 10h", trecho: str = "7h as 10h"
) -> ResultadoResposta:
    return ResultadoResposta(coberta=True, texto=texto, trechos_citados=(trecho,))


def resposta_nao_coberta() -> ResultadoResposta:
    return ResultadoResposta(coberta=False)
