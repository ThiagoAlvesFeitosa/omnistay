"""Implementacao falsa de CatalogoRepository para testes."""

from app.portas.catalogo import ItemCatalogo


class CatalogoFalso:
    def __init__(self) -> None:
        self._por_hotel: dict[int, tuple[ItemCatalogo, ...]] = {}

    def configurar(
        self, id_hotel: int, itens: tuple[ItemCatalogo, ...]
    ) -> None:
        self._por_hotel[id_hotel] = itens

    def listar_ativos(self, id_hotel: int) -> tuple[ItemCatalogo, ...]:
        return self._por_hotel.get(id_hotel, ())
