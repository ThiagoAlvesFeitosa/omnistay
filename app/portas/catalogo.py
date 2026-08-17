"""Porta de catalogo — o dominio consumidor depende so desta interface."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ItemCatalogo:
    id_catalogo_item: int
    categoria: str
    titulo: str
    conteudo: str


class CatalogoRepository(Protocol):
    def listar_ativos(self, id_hotel: int) -> tuple[ItemCatalogo, ...]: ...
