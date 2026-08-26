"""Listagem e fio do simulador: modo, hotel e log sem conteudo."""

import pytest

from app.modulos.conversa import service as conversa


def test_modo_real_recusa_lista_antes_de_ler():
    class Repo:
        def listar_mensagens_simulador(self, *args, **kwargs):
            raise AssertionError("nao deve ler banco")

    with pytest.raises(conversa.ModoRealRecusado):
        conversa.listar_conversas_simulador(
            object(),
            id_hotel=1,
            modo="real",
            repositorio=Repo(),
            listar_rotulos=lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("nao deve listar")
            ),
        )


def test_lista_devolve_reservas_do_hotel_em_ordem_desc():
    rotulos = [
        {
            "id_reserva": 12,
            "status": "hospedado",
            "nome_titular": "Marina",
            "telefone_contato": "5511999990000",
        },
        {
            "id_reserva": 7,
            "status": "aguardando_cadastro",
            "nome_titular": "Joao",
            "telefone_contato": "5511888880000",
        },
    ]
    resultado = conversa.listar_conversas_simulador(
        object(),
        id_hotel=3,
        modo="demonstracao",
        listar_rotulos=lambda conexao, *, id_hotel: rotulos
        if id_hotel == 3
        else [],
    )
    assert resultado["modo"] == "demonstracao"
    assert [c["id_reserva"] for c in resultado["conversas"]] == [12, 7]


def test_fio_inclui_pendente_e_ordem():
    class Repo:
        def listar_mensagens_simulador(self, conexao, *, id_hotel, id_reserva):
            assert id_hotel == 3
            assert id_reserva == 12
            return [
                {
                    "id_mensagem": 1,
                    "direcao": "enviada",
                    "conteudo": "segredo",
                    "status_envio": "pendente",
                    "enviada_em": "t0",
                },
                {
                    "id_mensagem": 2,
                    "direcao": "recebida",
                    "conteudo": "oi",
                    "status_envio": None,
                    "enviada_em": "t1",
                },
            ]

        def obter_rotulo_simulador(self, *args, **kwargs):
            raise AssertionError("rotulo vem de hospedagem")

    rotulo = {
        "id_reserva": 12,
        "status": "hospedado",
        "nome_titular": "Marina",
        "telefone_contato": "5511999990000",
    }
    resultado = conversa.obter_conversa_simulador(
        object(),
        id_hotel=3,
        id_reserva=12,
        modo="demonstracao",
        repositorio=Repo(),
        obter_rotulo=lambda conexao, *, id_hotel, id_reserva: rotulo,
    )
    assert [m["id_mensagem"] for m in resultado["mensagens"]] == [1, 2]
    assert resultado["mensagens"][0]["status_envio"] == "pendente"


def test_fio_inexistente_ou_de_outro_hotel():
    with pytest.raises(conversa.ConversaSimuladorNaoEncontrada):
        conversa.obter_conversa_simulador(
            object(),
            id_hotel=3,
            id_reserva=99,
            modo="demonstracao",
            obter_rotulo=lambda conexao, *, id_hotel, id_reserva: None,
        )


def test_lista_loga_so_identificadores(monkeypatch):
    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(conversa.logger, "info", fake_info)
    conversa.listar_conversas_simulador(
        object(),
        id_hotel=3,
        modo="demonstracao",
        listar_rotulos=lambda conexao, *, id_hotel: [
            {
                "id_reserva": 12,
                "status": "hospedado",
                "nome_titular": "Marina",
                "telefone_contato": "5511999990000",
            }
        ],
    )
    texto = " ".join(registros)
    assert "id_hotel=3" in texto
    assert "Marina" not in texto
    assert "5511999990000" not in texto
    assert "segredo" not in texto


def test_fio_loga_so_identificadores(monkeypatch):
    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    class Repo:
        def listar_mensagens_simulador(self, conexao, *, id_hotel, id_reserva):
            return [
                {
                    "id_mensagem": 1,
                    "direcao": "enviada",
                    "conteudo": "segredo",
                    "status_envio": "enviada",
                    "enviada_em": "t0",
                }
            ]

    monkeypatch.setattr(conversa.logger, "info", fake_info)
    conversa.obter_conversa_simulador(
        object(),
        id_hotel=3,
        id_reserva=12,
        modo="demonstracao",
        repositorio=Repo(),
        obter_rotulo=lambda conexao, *, id_hotel, id_reserva: {
            "id_reserva": 12,
            "status": "hospedado",
            "nome_titular": "Marina",
            "telefone_contato": "5511999990000",
        },
    )
    texto = " ".join(registros)
    assert "id_reserva=12" in texto
    assert "Marina" not in texto
    assert "5511999990000" not in texto
    assert "segredo" not in texto
