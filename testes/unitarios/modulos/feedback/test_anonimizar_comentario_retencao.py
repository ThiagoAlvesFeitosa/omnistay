"""Anonimizacao de comentario: texto vira marca; vazio nao ganha marca."""

from datetime import UTC, datetime

from app.comum.retencao import MARCA_TEXTO, vencido_em_meses
from app.modulos.feedback import service as feedback

AGORA = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
CHECKOUT_VENCIDO = datetime(2025, 7, 24, 12, 0, tzinfo=UTC)


class RepoFeedback:
    def __init__(self, reservas, avaliacoes):
        self.reservas = reservas
        self.avaliacoes = avaliacoes
        self.deletes = []

    def delete(self, *args, **kwargs):
        self.deletes.append((args, kwargs))

    def anonimizar_comentarios_vencidos(
        self, conexao, *, id_hotel, agora, meses, marca
    ):
        afetadas = 0
        for item in self.avaliacoes:
            reserva = self.reservas[item["id_reserva"]]
            if reserva["id_hotel"] != id_hotel:
                continue
            if not vencido_em_meses(reserva.get("checkout_em"), agora, meses):
                continue
            comentario = item["comentario"]
            if comentario is None or not str(comentario).strip():
                continue
            if comentario == marca:
                continue
            item["comentario"] = marca
            afetadas += 1
        return afetadas


def test_comentario_com_texto_vira_marca_e_nota_permanece():
    repo = RepoFeedback(
        reservas={1: {"id_hotel": 10, "checkout_em": CHECKOUT_VENCIDO}},
        avaliacoes=[
            {
                "id_reserva": 1,
                "comentario": "cafe excelente",
                "nota": 5,
                "origem": "checkout",
            }
        ],
    )

    afetadas = feedback.anonimizar_comentarios_vencidos(
        object(), id_hotel=10, agora=AGORA, meses=12, repositorio=repo
    )

    assert afetadas == 1
    item = repo.avaliacoes[0]
    assert item["comentario"] == MARCA_TEXTO
    assert item["nota"] == 5
    assert item["origem"] == "checkout"


def test_comentario_nulo_ou_so_espacos_nao_recebe_marca():
    repo = RepoFeedback(
        reservas={
            1: {"id_hotel": 10, "checkout_em": CHECKOUT_VENCIDO},
            2: {"id_hotel": 10, "checkout_em": CHECKOUT_VENCIDO},
        },
        avaliacoes=[
            {"id_reserva": 1, "comentario": None, "nota": 4, "origem": "checkout"},
            {"id_reserva": 2, "comentario": "   ", "nota": 3, "origem": "pulso"},
        ],
    )

    afetadas = feedback.anonimizar_comentarios_vencidos(
        object(), id_hotel=10, agora=AGORA, meses=12, repositorio=repo
    )

    assert afetadas == 0
    assert repo.avaliacoes[0]["comentario"] is None
    assert repo.avaliacoes[1]["comentario"] == "   "
    assert repo.avaliacoes[0]["nota"] == 4
    assert repo.avaliacoes[1]["nota"] == 3


def test_anonimizar_comentario_nao_apaga_linha():
    repo = RepoFeedback(
        reservas={1: {"id_hotel": 10, "checkout_em": CHECKOUT_VENCIDO}},
        avaliacoes=[
            {
                "id_reserva": 1,
                "comentario": "cafe excelente",
                "nota": 5,
                "origem": "checkout",
            }
        ],
    )

    feedback.anonimizar_comentarios_vencidos(
        object(), id_hotel=10, agora=AGORA, meses=12, repositorio=repo
    )

    assert len(repo.avaliacoes) == 1
    assert repo.deletes == []
