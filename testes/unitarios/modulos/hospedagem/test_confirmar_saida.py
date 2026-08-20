"""Confirmacao de saida — regras com repositorio falso."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.modulos.hospedagem import service as hospedagem


class Repo:
    def __init__(self, *, resultado=None, reserva=None):
        self.resultado = resultado
        self.reserva = reserva
        self.chamadas = []

    def confirmar_saida(self, conexao, *, id_hotel, id_reserva):
        self.chamadas.append({"id_hotel": id_hotel, "id_reserva": id_reserva})
        return self.resultado

    def ler_reserva_do_hotel(self, conexao, *, id_hotel, id_reserva):
        return self.reserva

    def ler_titular_da_reserva(self, conexao, *, id_hotel, id_reserva):
        return {"nome_completo": "Maria Silva"}


class Agendador:
    def __init__(self):
        self.chamadas = []

    def __call__(self, conexao, *, id_hotel, id_reserva, nome_completo):
        self.chamadas.append(
            {
                "id_hotel": id_hotel,
                "id_reserva": id_reserva,
                "nome_completo": nome_completo,
            }
        )
        return "agendada"


class AgendadorLista:
    def __init__(self):
        self.chamadas = []

    def __call__(self, conexao, *, id_hotel, id_reserva, nome_completo, itens):
        self.chamadas.append(
            {
                "id_hotel": id_hotel,
                "id_reserva": id_reserva,
                "nome_completo": nome_completo,
                "itens": itens,
            }
        )
        return "agendada"


def _sem_pedidos(*_args, **_kwargs):
    return []


def test_confirmacao_aceita_grava_encerrado_e_chama_agendador():
    instante = datetime(2026, 8, 20, 12, 4, tzinfo=UTC)
    repo = Repo(resultado={"status": "encerrado", "checkout_em": instante})
    agendador = Agendador()

    saida = hospedagem.confirmar_saida(
        object(),
        id_hotel=3,
        id_reserva=42,
        repositorio=repo,
        agendar_pesquisa_saida=agendador,
        listar_pedidos=_sem_pedidos,
    )

    assert repo.chamadas == [{"id_hotel": 3, "id_reserva": 42}]
    assert saida.status == "encerrado"
    assert saida.checkout_em == instante
    assert saida.pesquisa == "agendada"
    assert saida.lista == "ausente"
    assert agendador.chamadas == [
        {"id_hotel": 3, "id_reserva": 42, "nome_completo": "Maria Silva"}
    ]


def test_confirmacao_com_consumo_agenda_lista():
    instante = datetime(2026, 8, 20, 12, 4, tzinfo=UTC)
    repo = Repo(resultado={"status": "encerrado", "checkout_em": instante})
    agendador = Agendador()
    lista = AgendadorLista()
    itens = [
        {
            "id_solicitacao": 7,
            "descricao_item": "Cerveja",
            "valor_praticado": Decimal("12.00"),
        }
    ]

    saida = hospedagem.confirmar_saida(
        object(),
        id_hotel=3,
        id_reserva=42,
        repositorio=repo,
        agendar_pesquisa_saida=agendador,
        listar_pedidos=lambda *_a, **_k: itens,
        agendar_lista=lista,
    )

    assert saida.lista == "agendada"
    assert lista.chamadas == [
        {
            "id_hotel": 3,
            "id_reserva": 42,
            "nome_completo": "Maria Silva",
            "itens": itens,
        }
    ]


def test_listar_vazio_nao_agenda_lista():
    instante = datetime(2026, 8, 20, 12, 4, tzinfo=UTC)
    repo = Repo(resultado={"status": "encerrado", "checkout_em": instante})
    lista = AgendadorLista()

    saida = hospedagem.confirmar_saida(
        object(),
        id_hotel=3,
        id_reserva=42,
        repositorio=repo,
        agendar_pesquisa_saida=Agendador(),
        listar_pedidos=_sem_pedidos,
        agendar_lista=lista,
    )

    assert saida.lista == "ausente"
    assert lista.chamadas == []


def test_rowcount_zero_nao_chama_agendador():
    repo = Repo(
        resultado=None,
        reserva={"id_reserva": 42, "status": "aguardando_cadastro"},
    )
    agendador = Agendador()
    lista = AgendadorLista()

    with pytest.raises(hospedagem.SaidaNaoPermitida):
        hospedagem.confirmar_saida(
            object(),
            id_hotel=3,
            id_reserva=42,
            repositorio=repo,
            agendar_pesquisa_saida=agendador,
            listar_pedidos=_sem_pedidos,
            agendar_lista=lista,
        )

    assert agendador.chamadas == []
    assert lista.chamadas == []


@pytest.mark.parametrize(
    "status",
    [
        "aguardando_cadastro",
        "ficha_recebida",
        "ficha_parcial",
        "sem_cadastro_previo",
        "encerrado",
        "cancelada",
    ],
)
def test_estado_recusado_nao_chama_agendador(status, monkeypatch):
    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(hospedagem.logger, "info", fake_info)
    repo = Repo(
        resultado=None,
        reserva={"id_reserva": 42, "status": status},
    )
    agendador = Agendador()
    lista = AgendadorLista()

    with pytest.raises(hospedagem.SaidaNaoPermitida) as erro:
        hospedagem.confirmar_saida(
            object(),
            id_hotel=3,
            id_reserva=42,
            repositorio=repo,
            agendar_pesquisa_saida=agendador,
            listar_pedidos=_sem_pedidos,
            agendar_lista=lista,
        )

    assert erro.value.status_atual == status
    assert agendador.chamadas == []
    assert lista.chamadas == []
    texto = " ".join(registros)
    assert "saida_recusada" in texto
    assert f"status={status}" in texto
    assert "Maria" not in texto
