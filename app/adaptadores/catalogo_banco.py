"""Catalogo ativo lido na mesma transacao, sem abrir conexao propria."""

from sqlalchemy.engine import Connection

from app.modulos.propriedade import repository as propriedade_repository
from app.portas.catalogo import ItemCatalogo


class CatalogoBanco:
    def __init__(self, conexao: Connection) -> None:
        self._conexao = conexao

    def listar_ativos(self, id_hotel: int) -> tuple[ItemCatalogo, ...]:
        linhas = propriedade_repository.listar_ativos(
            self._conexao, id_hotel=id_hotel
        )
        return tuple(
            ItemCatalogo(
                id_catalogo_item=linha["id_catalogo_item"],
                categoria=linha["categoria"],
                titulo=linha["titulo"],
                conteudo=linha["conteudo"],
            )
            for linha in linhas
        )
