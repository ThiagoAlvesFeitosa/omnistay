"""Soma de consumo a lancar: valor pendente, nao quantidade de linhas."""

from decimal import Decimal

from app.modulos.atendimento import service as atendimento


class Repo:
    def __init__(self, linhas):
        self.linhas = linhas

    def somar_consumo_pendente(self, conexao, *, id_hotel):
        total = Decimal("0")
        for linha in self.linhas:
            if (
                linha["id_hotel"] == id_hotel
                and linha["status_lancamento"] == "pendente"
            ):
                total += Decimal(str(linha["valor_praticado"]))
        return total


def test_lista_vazia_devolve_zero():
    repo = Repo([])
    assert atendimento.somar_consumo_pendente(
        object(), id_hotel=3, repositorio=repo
    ) == Decimal("0")


def test_dois_pendentes_somam_trinta():
    repo = Repo(
        [
            {"id_hotel": 3, "status_lancamento": "pendente", "valor_praticado": "10.00"},
            {"id_hotel": 3, "status_lancamento": "pendente", "valor_praticado": "20.00"},
            {"id_hotel": 3, "status_lancamento": "lancado", "valor_praticado": "99.00"},
            {"id_hotel": 3, "status_lancamento": "dispensado", "valor_praticado": "5.00"},
        ]
    )

    assert atendimento.somar_consumo_pendente(
        object(), id_hotel=3, repositorio=repo
    ) == Decimal("30.00")
