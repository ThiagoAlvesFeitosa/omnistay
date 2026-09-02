"""Contagem de hospedados: so status hospedado, isolada por hotel."""

from app.modulos.hospedagem import service as hospedagem


class Repo:
    def __init__(self, reservas):
        self.reservas = reservas
        self.chamadas = []

    def contar_hospedados(self, conexao, *, id_hotel):
        self.chamadas.append(id_hotel)
        return sum(
            1
            for linha in self.reservas
            if linha["id_hotel"] == id_hotel and linha["status"] == "hospedado"
        )


def test_uma_reserva_hospedada_conta_um():
    repo = Repo(
        [
            {"id_hotel": 10, "status": "hospedado"},
            {"id_hotel": 10, "status": "aguardando_cadastro"},
            {"id_hotel": 10, "status": "encerrado"},
        ]
    )

    quantidade = hospedagem.contar_hospedados(
        object(), id_hotel=10, repositorio=repo
    )

    assert quantidade == 1
    assert repo.chamadas == [10]


def test_so_aguardando_ou_encerrado_conta_zero():
    repo = Repo(
        [
            {"id_hotel": 10, "status": "aguardando_cadastro"},
            {"id_hotel": 10, "status": "encerrado"},
        ]
    )

    assert hospedagem.contar_hospedados(object(), id_hotel=10, repositorio=repo) == 0


def test_hotel_alheio_nao_entra_na_contagem():
    repo = Repo(
        [
            {"id_hotel": 10, "status": "hospedado"},
            {"id_hotel": 99, "status": "hospedado"},
        ]
    )

    assert hospedagem.contar_hospedados(object(), id_hotel=10, repositorio=repo) == 1


def test_log_de_indicadores_nao_traz_dado_de_hospede(monkeypatch):
    from decimal import Decimal

    registros = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(hospedagem.logger, "info", fake_info)

    class Repo:
        def contar_chegadas_do_dia(self, conexao, *, id_hotel):
            return 0

        def contar_hospedados(self, conexao, *, id_hotel):
            return 0

    class Atendimento:
        def contar_chamados_abertos(self, conexao, *, id_hotel):
            return 0

        def somar_consumo_pendente(self, conexao, *, id_hotel):
            return Decimal("0")

    hospedagem.ler_indicadores(
        object(), id_hotel=10, repositorio=Repo(), atendimento=Atendimento()
    )
    texto = " ".join(registros)
    assert "id_hotel=10" in texto
    assert "indicadores" in texto
    assert "Marina" not in texto
    assert "senha" not in texto
    assert "5511" not in texto
