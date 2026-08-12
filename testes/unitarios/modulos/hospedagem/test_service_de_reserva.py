"""Servico de criacao de reserva — regras com repositorio falso."""

from dataclasses import dataclass, field
from datetime import date

import pytest

from app.modulos.hospedagem import service as hospedagem


@dataclass
class Repositorio:
    hospedes: list = field(default_factory=list)
    reservas: list = field(default_factory=list)
    vinculos: list = field(default_factory=list)
    proximo_hospede: int = 1
    proximo_reserva: int = 1

    def inserir_hospede(self, conexao, *, nome_completo, telefone):
        id_hospede = self.proximo_hospede
        self.proximo_hospede += 1
        self.hospedes.append(
            {"id_hospede": id_hospede, "nome_completo": nome_completo, "telefone": telefone}
        )
        return id_hospede

    def inserir_reserva(
        self,
        conexao,
        *,
        id_hotel,
        telefone_contato,
        data_checkin_prevista,
        data_checkout_prevista,
        status,
    ):
        id_reserva = self.proximo_reserva
        self.proximo_reserva += 1
        self.reservas.append(
            {
                "id_reserva": id_reserva,
                "id_hotel": id_hotel,
                "telefone_contato": telefone_contato,
                "data_checkin_prevista": data_checkin_prevista,
                "data_checkout_prevista": data_checkout_prevista,
                "status": status,
            }
        )
        return id_reserva

    def inserir_vinculo_titular(self, conexao, *, id_reserva, id_hospede):
        self.vinculos.append(
            {
                "id_reserva": id_reserva,
                "id_hospede": id_hospede,
                "titular": True,
                "ficha_completa": False,
            }
        )


def _criar(repo, **kwargs):
    padrao = {
        "conexao": object(),
        "id_hotel": 10,
        "nome": "Maria Silva",
        "telefone": "(11) 98765-4321",
        "data_checkin_prevista": date(2026, 8, 20),
        "data_checkout_prevista": date(2026, 8, 23),
        "repositorio": repo,
    }
    padrao.update(kwargs)
    return hospedagem.criar_reserva(**padrao)


def test_criacao_valida_grava_hospede_reserva_e_titular():
    repo = Repositorio()
    criada = _criar(repo)

    assert criada.status == "aguardando_cadastro"
    assert criada.id_hotel == 10
    assert criada.telefone_contato == "5511987654321"
    assert criada.nome == "Maria Silva"
    assert len(repo.hospedes) == 1
    assert len(repo.reservas) == 1
    assert repo.vinculos == [
        {
            "id_reserva": criada.id_reserva,
            "id_hospede": repo.hospedes[0]["id_hospede"],
            "titular": True,
            "ficha_completa": False,
        }
    ]


def test_telefone_repetido_cria_segundo_hospede():
    repo = Repositorio()
    primeira = _criar(repo, nome="Maria")
    segunda = _criar(repo, nome="Joao")

    assert primeira.id_reserva != segunda.id_reserva
    assert len(repo.hospedes) == 2
    assert repo.hospedes[0]["id_hospede"] != repo.hospedes[1]["id_hospede"]
    assert repo.hospedes[0]["telefone"] == repo.hospedes[1]["telefone"]


def test_nome_ou_telefone_em_branco_nao_grava():
    repo = Repositorio()
    with pytest.raises(hospedagem.DadosInvalidos):
        _criar(repo, nome="   ")
    with pytest.raises(hospedagem.DadosInvalidos):
        _criar(repo, telefone="   ")
    assert repo.hospedes == []
    assert repo.reservas == []


def test_telefone_invalido_nao_grava():
    repo = Repositorio()
    with pytest.raises(hospedagem.DadosInvalidos):
        _criar(repo, telefone="123")
    assert repo.hospedes == []


def test_checkout_nao_posterior_nao_grava():
    repo = Repositorio()
    with pytest.raises(hospedagem.DadosInvalidos):
        _criar(
            repo,
            data_checkin_prevista=date(2026, 8, 23),
            data_checkout_prevista=date(2026, 8, 20),
        )
    with pytest.raises(hospedagem.DadosInvalidos):
        _criar(
            repo,
            data_checkin_prevista=date(2026, 8, 20),
            data_checkout_prevista=date(2026, 8, 20),
        )
    assert repo.reservas == []
