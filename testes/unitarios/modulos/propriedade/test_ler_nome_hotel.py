"""Nome da casa lido pela propriedade, sem vazar telefone."""

from dataclasses import dataclass


from app.modulos.propriedade import service as propriedade


@dataclass
class Repositorio:
    hoteis: dict[int, dict]

    def ler_nome_hotel(self, conexao, id_hotel: int) -> str | None:
        hotel = self.hoteis.get(id_hotel)
        if hotel is None:
            return None
        return hotel["nome"]


def test_ler_nome_hotel_devolve_o_nome_daquele_hotel():
    repo = Repositorio(
        hoteis={
            1: {"nome": "Hotel Alpha", "telefone_whatsapp": "5511999990001"},
            2: {"nome": "Hotel Beta", "telefone_whatsapp": "5511999990002"},
        }
    )

    nome = propriedade.ler_nome_hotel(object(), id_hotel=1, repositorio=repo)

    assert nome == "Hotel Alpha"
    assert "5511999990001" not in nome


def test_ler_nome_hotel_inexistente_devolve_vazio():
    repo = Repositorio(hoteis={})

    nome = propriedade.ler_nome_hotel(object(), id_hotel=99, repositorio=repo)

    assert nome == ""
