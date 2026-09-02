"""Chamados abertos no painel: reclamacao e servico, nunca consumo."""

from app.modulos.atendimento import service as atendimento


class Repo:
    def __init__(self, linhas):
        self.linhas = linhas

    def contar_chamados_abertos(self, conexao, *, id_hotel):
        return sum(
            1
            for linha in self.linhas
            if linha["id_hotel"] == id_hotel
            and linha["tipo"] in ("reclamacao", "servico")
            and linha["status"] in ("aberta", "em_andamento")
        )


def test_reclamacao_e_servico_abertos_somam():
    repo = Repo(
        [
            {"id_hotel": 3, "tipo": "reclamacao", "status": "aberta"},
            {"id_hotel": 3, "tipo": "servico", "status": "em_andamento"},
            {"id_hotel": 3, "tipo": "consumo", "status": "aberta"},
            {"id_hotel": 3, "tipo": "reclamacao", "status": "resolvida"},
            {"id_hotel": 3, "tipo": "servico", "status": "cancelada"},
        ]
    )

    assert (
        atendimento.contar_chamados_abertos(object(), id_hotel=3, repositorio=repo)
        == 2
    )


def test_consumo_aberto_nao_entra():
    repo = Repo([{"id_hotel": 3, "tipo": "consumo", "status": "aberta"}])

    assert (
        atendimento.contar_chamados_abertos(object(), id_hotel=3, repositorio=repo)
        == 0
    )
