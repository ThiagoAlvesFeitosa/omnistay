"""Consolidacao da ficha do titular."""

from app.modulos.conversa.validacao_ficha import refinar_resultado
from app.modulos.hospedagem import service as hospedagem
from app.portas.llm import CAMPOS_FICHA_CHAVE, ResultadoExtracao
from testes.suporte.cpf_ficha import CPF_REPROVADO, CPF_VALIDO, CPF_VALIDO_PONTUADO


class RepoFake:
    def __init__(self):
        self.titular = {
            "id_reserva": 10,
            "id_hotel": 1,
            "status": "aguardando_cadastro",
            "id_hospede": 7,
            "ficha_completa": False,
            "nome_completo": "Maria",
            "telefone": "5511987654321",
        }
        self.atualizacoes = []
        self.status = None
        self.completa = None

    def ler_titular_da_reserva(self, conexao, *, id_hotel, id_reserva):
        return dict(self.titular)

    def atualizar_hospede_titular(self, conexao, *, id_hospede, campos):
        self.atualizacoes.append({"id_hospede": id_hospede, "campos": dict(campos)})

    def marcar_ficha_completa(self, conexao, *, id_reserva, completa):
        self.completa = completa

    def atualizar_status_reserva(self, conexao, *, id_hotel, id_reserva, status):
        self.status = status
        self.titular["status"] = status


def test_consolidacao_completa_marca_ficha_recebida():
    repo = RepoFake()
    campos = {
        "nome_completo": "Maria Silva",
        "profissao": "Engenheira",
        "data_nascimento": "1990-05-12",
        "tipo_documento": "rg",
        "numero_documento": "123",
        "endereco": "Rua A",
        "cep": "01310100",
        "cidade": "Sao Paulo",
        "telefone": "5511987654321",
    }
    hospedagem.consolidar_ficha_titular(
        object(),
        id_hotel=1,
        id_reserva=10,
        campos=campos,
        desfecho="completa",
        repositorio=repo,
    )
    assert repo.status == "ficha_recebida"
    assert repo.completa is True
    assert "idade" not in repo.atualizacoes[0]["campos"]


def test_cpf_reprovado_nao_vai_ao_titular_e_fica_parcial():
    bruto = {
        "nome_completo": "Maria Silva",
        "profissao": "Engenheira",
        "data_nascimento": "1990-05-12",
        "tipo_documento": "cpf",
        "numero_documento": CPF_REPROVADO,
        "endereco": "Rua A",
        "cep": "01310100",
        "cidade": "Sao Paulo",
        "telefone": "5511987654321",
    }
    refinado = refinar_resultado(
        ResultadoExtracao(
            desfecho="completa",
            campos=bruto,
            campos_reconhecidos=tuple(CAMPOS_FICHA_CHAVE),
        )
    )
    repo = RepoFake()
    hospedagem.consolidar_ficha_titular(
        object(),
        id_hotel=1,
        id_reserva=10,
        campos=refinado.campos,
        desfecho=refinado.desfecho,
        repositorio=repo,
    )
    assert "numero_documento" not in repo.atualizacoes[0]["campos"]
    assert repo.status == "ficha_parcial"
    assert repo.completa is False


def test_cpf_pontuado_valido_grava_onze_digitos_no_titular():
    bruto = {
        "nome_completo": "Maria Silva",
        "profissao": "Engenheira",
        "data_nascimento": "1990-05-12",
        "tipo_documento": "cpf",
        "numero_documento": CPF_VALIDO_PONTUADO,
        "endereco": "Rua A",
        "cep": "01310100",
        "cidade": "Sao Paulo",
        "telefone": "5511987654321",
    }
    refinado = refinar_resultado(
        ResultadoExtracao(
            desfecho="completa",
            campos=bruto,
            campos_reconhecidos=tuple(CAMPOS_FICHA_CHAVE),
        )
    )
    repo = RepoFake()
    hospedagem.consolidar_ficha_titular(
        object(),
        id_hotel=1,
        id_reserva=10,
        campos=refinado.campos,
        desfecho=refinado.desfecho,
        repositorio=repo,
    )
    assert repo.atualizacoes[0]["campos"]["numero_documento"] == CPF_VALIDO
    assert repo.status == "ficha_recebida"


def test_consolidacao_parcial_marca_ficha_parcial():
    repo = RepoFake()
    hospedagem.consolidar_ficha_titular(
        object(),
        id_hotel=1,
        id_reserva=10,
        campos={"nome_completo": "Maria Silva", "cidade": "Sao Paulo"},
        desfecho="parcial",
        repositorio=repo,
    )
    assert repo.status == "ficha_parcial"
    assert repo.completa is False
