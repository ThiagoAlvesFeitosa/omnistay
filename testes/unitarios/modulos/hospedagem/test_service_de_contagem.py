"""Servico da contagem de chegadas."""

from app.modulos.hospedagem import service as hospedagem


class Repositorio:
    def __init__(self):
        self.chamadas = []

    def contar_chegadas_do_dia(self, conexao, *, id_hotel):
        self.chamadas.append(id_hotel)
        return 7


def test_contagem_usa_hotel_da_sessao_e_devolve_inteiro():
    repo = Repositorio()
    quantidade = hospedagem.contar_chegadas_do_dia(
        conexao=object(), id_hotel=10, repositorio=repo
    )
    assert quantidade == 7
    assert repo.chamadas == [10]
