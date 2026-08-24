"""Exclusao da ficha cadastral apos o prazo de anos."""

from datetime import UTC, datetime

from app.comum.retencao import MARCA_TELEFONE, vencido_em_anos
from app.modulos.hospedagem import service as hospedagem

AGORA = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
CHECKOUT_SEIS_ANOS = datetime(2020, 8, 24, 12, 0, tzinfo=UTC)
CHECKOUT_UM_ANO = datetime(2025, 8, 24, 12, 0, tzinfo=UTC)


class RepoHospedagem:
    def __init__(self, hospedes, vinculos, reservas, consentimentos):
        self.hospedes = hospedes
        self.vinculos = vinculos
        self.reservas = reservas
        self.consentimentos = consentimentos

    def apagar_fichas_vencidas(
        self, conexao, *, id_hotel, agora, anos, marca_telefone
    ):
        visiveis = {
            vinculo["id_hospede"]
            for vinculo in self.vinculos
            if self.reservas[vinculo["id_reserva"]]["id_hotel"] == id_hotel
        }
        apagados = 0
        for id_hospede in list(visiveis):
            vinculadas = [
                self.reservas[v["id_reserva"]]
                for v in self.vinculos
                if v["id_hospede"] == id_hospede
            ]
            if any(r.get("checkout_em") is None for r in vinculadas):
                continue
            ultima = max(r["checkout_em"] for r in vinculadas)
            if not vencido_em_anos(ultima, agora, anos):
                continue
            self.consentimentos[:] = [
                c for c in self.consentimentos if c["id_hospede"] != id_hospede
            ]
            reservas_do_hospede = [
                v["id_reserva"]
                for v in self.vinculos
                if v["id_hospede"] == id_hospede
            ]
            self.vinculos[:] = [
                v for v in self.vinculos if v["id_hospede"] != id_hospede
            ]
            self.hospedes[:] = [
                h for h in self.hospedes if h["id_hospede"] != id_hospede
            ]
            for id_reserva in reservas_do_hospede:
                ainda = any(v["id_reserva"] == id_reserva for v in self.vinculos)
                if not ainda:
                    self.reservas[id_reserva]["telefone_contato"] = marca_telefone
            apagados += 1
        return apagados


def test_ficha_elegivel_some_e_telefone_da_reserva_orfao_vira_marca():
    repo = RepoHospedagem(
        hospedes=[{"id_hospede": 1, "nome_completo": "Ana"}],
        vinculos=[{"id_reserva": 9, "id_hospede": 1}],
        reservas={
            9: {
                "id_hotel": 10,
                "checkout_em": CHECKOUT_SEIS_ANOS,
                "telefone_contato": "5511910000099",
            }
        },
        consentimentos=[{"id_hospede": 1, "concedido": True}],
    )

    n = hospedagem.apagar_fichas_vencidas(
        object(), id_hotel=10, agora=AGORA, anos=5, repositorio=repo
    )

    assert n == 1
    assert repo.hospedes == []
    assert repo.consentimentos == []
    assert repo.vinculos == []
    assert repo.reservas[9]["telefone_contato"] == MARCA_TELEFONE


def test_reserva_mais_nova_dentro_do_prazo_nao_apaga():
    repo = RepoHospedagem(
        hospedes=[{"id_hospede": 1, "nome_completo": "Ana"}],
        vinculos=[
            {"id_reserva": 9, "id_hospede": 1},
            {"id_reserva": 8, "id_hospede": 1},
        ],
        reservas={
            9: {
                "id_hotel": 10,
                "checkout_em": CHECKOUT_SEIS_ANOS,
                "telefone_contato": "5511910000099",
            },
            8: {
                "id_hotel": 10,
                "checkout_em": CHECKOUT_UM_ANO,
                "telefone_contato": "5511910000099",
            },
        },
        consentimentos=[{"id_hospede": 1}],
    )

    n = hospedagem.apagar_fichas_vencidas(
        object(), id_hotel=10, agora=AGORA, anos=5, repositorio=repo
    )

    assert n == 0
    assert repo.hospedes == [{"id_hospede": 1, "nome_completo": "Ana"}]


def test_reserva_sem_checkout_nao_apaga():
    repo = RepoHospedagem(
        hospedes=[{"id_hospede": 1, "nome_completo": "Ana"}],
        vinculos=[
            {"id_reserva": 9, "id_hospede": 1},
            {"id_reserva": 8, "id_hospede": 1},
        ],
        reservas={
            9: {
                "id_hotel": 10,
                "checkout_em": CHECKOUT_SEIS_ANOS,
                "telefone_contato": "5511910000099",
            },
            8: {
                "id_hotel": 99,
                "checkout_em": None,
                "telefone_contato": "5511910000099",
            },
        },
        consentimentos=[{"id_hospede": 1}],
    )

    n = hospedagem.apagar_fichas_vencidas(
        object(), id_hotel=10, agora=AGORA, anos=5, repositorio=repo
    )

    assert n == 0
    assert len(repo.hospedes) == 1
