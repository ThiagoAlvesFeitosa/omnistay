"""Completar a ficha do titular no balcao — sem mensagem."""

import pytest

from app.modulos.hospedagem import service as hospedagem
from testes.suporte.cpf_ficha import CPF_REPROVADO, CPF_VALIDO, CPF_VALIDO_PONTUADO


NOVE = {
    "nome_completo": "Maria Silva",
    "profissao": "Engenheira",
    "data_nascimento": "1990-05-12",
    "tipo_documento": "rg",
    "numero_documento": "1234567",
    "endereco": "Rua A, 100",
    "cep": "01310100",
    "cidade": "Sao Paulo",
    "telefone": "5511987654321",
}


class RepoFake:
    def __init__(self, status="ficha_parcial"):
        self.titular = {
            "id_reserva": 10,
            "id_hotel": 1,
            "status": status,
            "id_hospede": 7,
            "ficha_completa": False,
            "nome_completo": "Maria",
            "telefone": "5511987654321",
        }
        self.atualizacoes = []
        self.status = None
        self.completa = None
        self.telefone_contato_atualizado = False

    def ler_titular_da_reserva(self, conexao, *, id_hotel, id_reserva):
        return dict(self.titular)

    def atualizar_hospede_titular(self, conexao, *, id_hospede, campos):
        self.atualizacoes.append({"id_hospede": id_hospede, "campos": dict(campos)})

    def marcar_ficha_completa(self, conexao, *, id_reserva, completa):
        self.completa = completa

    def atualizar_status_reserva(self, conexao, *, id_hotel, id_reserva, status):
        self.status = status
        self.titular["status"] = status

    def estado_cadastro_da_reserva(self, conexao, *, id_hotel, id_reserva):
        return "completa" if self.completa else "parcial"


def test_nove_campos_em_ficha_parcial_viram_ficha_recebida():
    repo = RepoFake("ficha_parcial")
    hospedagem.completar_ficha_titular(
        object(),
        id_hotel=1,
        id_reserva=10,
        campos=NOVE,
        repositorio=repo,
    )
    assert repo.status == "ficha_recebida"
    assert repo.completa is True
    assert repo.atualizacoes[0]["campos"]["nome_completo"] == "Maria Silva"
    assert "idade" not in repo.atualizacoes[0]["campos"]
    assert repo.telefone_contato_atualizado is False


def test_incompleto_permanece_parcial():
    repo = RepoFake("ficha_parcial")
    hospedagem.completar_ficha_titular(
        object(),
        id_hotel=1,
        id_reserva=10,
        campos={**NOVE, "cep": "", "cidade": None},
        repositorio=repo,
    )
    assert repo.status == "ficha_parcial"
    assert repo.completa is False


def test_hospedado_nao_muda_status():
    repo = RepoFake("hospedado")
    hospedagem.completar_ficha_titular(
        object(),
        id_hotel=1,
        id_reserva=10,
        campos=NOVE,
        repositorio=repo,
    )
    assert repo.status is None
    assert repo.titular["status"] == "hospedado"
    assert repo.completa is True


def test_idade_no_corpo_e_ignorada():
    repo = RepoFake("ficha_parcial")
    hospedagem.completar_ficha_titular(
        object(),
        id_hotel=1,
        id_reserva=10,
        campos={**NOVE, "idade": "34"},
        repositorio=repo,
    )
    assert "idade" not in repo.atualizacoes[0]["campos"]


def test_cpf_reprovado_nao_grava_e_recado_nao_repete_numero():
    repo = RepoFake("ficha_parcial")
    with pytest.raises(hospedagem.DadosInvalidos) as captura:
        hospedagem.completar_ficha_titular(
            object(),
            id_hotel=1,
            id_reserva=10,
            campos={
                **NOVE,
                "tipo_documento": "cpf",
                "numero_documento": CPF_REPROVADO,
                "endereco": "Rua Nova, 9",
            },
            repositorio=repo,
        )
    recado = str(captura.value)
    assert "CPF" in recado
    assert "confere" in recado.lower()
    assert CPF_REPROVADO not in recado
    assert repo.atualizacoes == []


def test_cpf_valido_pontuado_grava_onze_digitos():
    repo = RepoFake("ficha_parcial")
    hospedagem.completar_ficha_titular(
        object(),
        id_hotel=1,
        id_reserva=10,
        campos={
            **NOVE,
            "tipo_documento": "cpf",
            "numero_documento": CPF_VALIDO_PONTUADO,
        },
        repositorio=repo,
    )
    assert repo.atualizacoes[0]["campos"]["numero_documento"] == CPF_VALIDO


def test_cep_invalido_continua_recusando():
    repo = RepoFake("ficha_parcial")
    with pytest.raises(hospedagem.DadosInvalidos, match="cep"):
        hospedagem.completar_ficha_titular(
            object(),
            id_hotel=1,
            id_reserva=10,
            campos={**NOVE, "cep": "12"},
            repositorio=repo,
        )
    assert repo.atualizacoes == []
