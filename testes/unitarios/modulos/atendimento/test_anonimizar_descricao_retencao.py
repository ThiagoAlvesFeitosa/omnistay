"""Anonimizacao de descricao de solicitacao: marca no vencido, status intacto."""

from datetime import UTC, datetime

from app.comum.retencao import MARCA_TEXTO, vencido_em_meses
from app.modulos.atendimento import service as atendimento

AGORA = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
CHECKOUT_VENCIDO = datetime(2025, 7, 24, 12, 0, tzinfo=UTC)


class RepoAtendimento:
    def __init__(self, reservas, solicitacoes):
        self.reservas = reservas
        self.solicitacoes = solicitacoes
        self.deletes = []

    def delete(self, *args, **kwargs):
        self.deletes.append((args, kwargs))

    def anonimizar_descricoes_vencidas(
        self, conexao, *, id_hotel, agora, meses, marca
    ):
        afetadas = 0
        for item in self.solicitacoes:
            reserva = self.reservas[item["id_reserva"]]
            if reserva["id_hotel"] != id_hotel:
                continue
            if not vencido_em_meses(reserva.get("checkout_em"), agora, meses):
                continue
            if not (item["descricao"] or "").strip():
                continue
            if item["descricao"] == marca:
                continue
            item["descricao"] = marca
            afetadas += 1
        return afetadas


def test_descricao_vencida_vira_marca_e_status_permanece():
    repo = RepoAtendimento(
        reservas={1: {"id_hotel": 10, "checkout_em": CHECKOUT_VENCIDO}},
        solicitacoes=[
            {
                "id_reserva": 1,
                "descricao": "toalha extra no 201",
                "tipo": "servico",
                "status": "aberta",
                "urgencia": "media",
            }
        ],
    )

    afetadas = atendimento.anonimizar_descricoes_vencidas(
        object(), id_hotel=10, agora=AGORA, meses=12, repositorio=repo
    )

    assert afetadas == 1
    item = repo.solicitacoes[0]
    assert item["descricao"] == MARCA_TEXTO
    assert item["status"] == "aberta"
    assert item["tipo"] == "servico"
    assert item["urgencia"] == "media"


def test_descricao_vazia_ou_so_espacos_nao_recebe_marca():
    repo = RepoAtendimento(
        reservas={1: {"id_hotel": 10, "checkout_em": CHECKOUT_VENCIDO}},
        solicitacoes=[
            {
                "id_reserva": 1,
                "descricao": "",
                "tipo": "servico",
                "status": "aberta",
                "urgencia": "media",
            },
            {
                "id_reserva": 1,
                "descricao": "   ",
                "tipo": "reclamacao",
                "status": "aberta",
                "urgencia": "alta",
            },
        ],
    )

    afetadas = atendimento.anonimizar_descricoes_vencidas(
        object(), id_hotel=10, agora=AGORA, meses=12, repositorio=repo
    )

    assert afetadas == 0
    assert repo.solicitacoes[0]["descricao"] == ""
    assert repo.solicitacoes[1]["descricao"] == "   "


def test_janela_e_quarto_permanecem_ao_anonimizar_descricao():
    repo = RepoAtendimento(
        reservas={1: {"id_hotel": 10, "checkout_em": CHECKOUT_VENCIDO}},
        solicitacoes=[
            {
                "id_reserva": 1,
                "descricao": "toalha extra no 201",
                "tipo": "servico",
                "status": "aberta",
                "urgencia": "media",
                "numero_quarto": "201",
                "janela_preferencia": "depois das 16h",
            }
        ],
    )

    atendimento.anonimizar_descricoes_vencidas(
        object(), id_hotel=10, agora=AGORA, meses=12, repositorio=repo
    )

    item = repo.solicitacoes[0]
    assert item["numero_quarto"] == "201"
    assert item["janela_preferencia"] == "depois das 16h"


def test_descricao_ja_marcada_nao_conta_de_novo():
    repo = RepoAtendimento(
        reservas={1: {"id_hotel": 10, "checkout_em": CHECKOUT_VENCIDO}},
        solicitacoes=[
            {
                "id_reserva": 1,
                "descricao": MARCA_TEXTO,
                "tipo": "servico",
                "status": "aberta",
                "urgencia": "media",
            }
        ],
    )

    afetadas = atendimento.anonimizar_descricoes_vencidas(
        object(), id_hotel=10, agora=AGORA, meses=12, repositorio=repo
    )

    assert afetadas == 0


def test_anonimizar_descricao_nao_apaga_linha():
    repo = RepoAtendimento(
        reservas={1: {"id_hotel": 10, "checkout_em": CHECKOUT_VENCIDO}},
        solicitacoes=[
            {
                "id_reserva": 1,
                "descricao": "toalha extra",
                "tipo": "servico",
                "status": "aberta",
                "urgencia": "media",
            }
        ],
    )

    atendimento.anonimizar_descricoes_vencidas(
        object(), id_hotel=10, agora=AGORA, meses=12, repositorio=repo
    )

    assert len(repo.solicitacoes) == 1
    assert repo.deletes == []
