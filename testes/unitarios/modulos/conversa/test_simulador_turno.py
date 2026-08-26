"""Turno do hospede no simulador: valida, delega e nao loga texto."""

import pytest

from app.modulos.conversa import service as conversa
from app.modulos.conversa.schema import EventoEntrada


def test_modo_real_nao_chama_receber_evento():
    def receber(*args, **kwargs):
        raise AssertionError("nao deve receber evento")

    with pytest.raises(conversa.ModoRealRecusado):
        conversa.enviar_turno_hospede_simulador(
            object(),
            id_hotel=3,
            id_reserva=12,
            modo="real",
            texto="Qual o horario do cafe?",
            id_externo="sim:1",
            receber_evento=receber,
        )


def test_texto_vazio_recusa_sem_receber():
    def receber(*args, **kwargs):
        raise AssertionError("nao deve receber evento")

    with pytest.raises(conversa.EntradaSimuladorInvalida) as erro:
        conversa.enviar_turno_hospede_simulador(
            object(),
            id_hotel=3,
            id_reserva=12,
            modo="demonstracao",
            texto="   ",
            id_externo="sim:1",
            receber_evento=receber,
        )
    assert erro.value.codigo == "texto_vazio"


def test_id_externo_ausente_recusa_sem_receber():
    def receber(*args, **kwargs):
        raise AssertionError("nao deve receber evento")

    with pytest.raises(conversa.EntradaSimuladorInvalida) as erro:
        conversa.enviar_turno_hospede_simulador(
            object(),
            id_hotel=3,
            id_reserva=12,
            modo="demonstracao",
            texto="oi",
            id_externo="",
            receber_evento=receber,
        )
    assert erro.value.codigo == "id_externo_ausente"


def test_reserva_de_outro_hotel_recusa():
    def receber(*args, **kwargs):
        raise AssertionError("nao deve receber evento")

    with pytest.raises(conversa.ConversaSimuladorNaoEncontrada):
        conversa.enviar_turno_hospede_simulador(
            object(),
            id_hotel=3,
            id_reserva=99,
            modo="demonstracao",
            texto="oi",
            id_externo="sim:1",
            receber_evento=receber,
            obter_rotulo=lambda conexao, *, id_hotel, id_reserva: None,
        )


def test_caminho_feliz_usa_telefone_da_reserva_e_hotel_da_sessao():
    capturado = {}

    def receber(conexao, *, evento, id_hotel, repositorio=None):
        capturado["evento"] = evento
        capturado["id_hotel"] = id_hotel
        return {"status": "enfileirado", "id_mensagem": 41, "id_reserva": 12}

    rotulo = {
        "id_reserva": 12,
        "status": "hospedado",
        "nome_titular": "Marina",
        "telefone_contato": "5511999990000",
    }
    resultado = conversa.enviar_turno_hospede_simulador(
        object(),
        id_hotel=3,
        id_reserva=12,
        modo="demonstracao",
        texto="Qual o horario do cafe?",
        id_externo="sim:abc",
        receber_evento=receber,
        obter_rotulo=lambda conexao, *, id_hotel, id_reserva: rotulo,
    )
    evento = capturado["evento"]
    assert isinstance(evento, EventoEntrada)
    assert evento.telefone_origem == "5511999990000"
    assert evento.texto == "Qual o horario do cafe?"
    assert evento.id_externo == "sim:abc"
    assert evento.id_mensagem_canal == "sim:abc"
    assert evento.tem_texto_utilizavel is True
    assert capturado["id_hotel"] == 3
    assert resultado["status"] == "enfileirado"
    assert resultado["id_mensagem"] == 41
    assert resultado["id_reserva"] == 12


def test_duplicata_devolve_status_duplicado():
    chamadas = []

    def receber(conexao, *, evento, id_hotel, repositorio=None):
        chamadas.append(evento.id_externo)
        if len(chamadas) == 1:
            return {"status": "enfileirado", "id_mensagem": 41, "id_reserva": 12}
        return {"status": "duplicado"}

    rotulo = {
        "id_reserva": 12,
        "status": "hospedado",
        "nome_titular": "Marina",
        "telefone_contato": "5511999990000",
    }
    kwargs = dict(
        id_hotel=3,
        id_reserva=12,
        modo="demonstracao",
        texto="oi",
        id_externo="sim:dup",
        receber_evento=receber,
        obter_rotulo=lambda conexao, *, id_hotel, id_reserva: rotulo,
    )
    primeiro = conversa.enviar_turno_hospede_simulador(object(), **kwargs)
    segundo = conversa.enviar_turno_hospede_simulador(object(), **kwargs)
    assert primeiro["status"] == "enfileirado"
    assert segundo["status"] == "duplicado"
    assert segundo.get("id_reserva") == 12


def test_turno_loga_so_identificadores(monkeypatch):
    registros: list[str] = []

    def fake_info(msg, *args):
        registros.append(msg % args if args else msg)

    monkeypatch.setattr(conversa.logger, "info", fake_info)
    conversa.enviar_turno_hospede_simulador(
        object(),
        id_hotel=3,
        id_reserva=12,
        modo="demonstracao",
        texto="segredo do hospede",
        id_externo="sim:log",
        receber_evento=lambda *a, **k: {"status": "enfileirado", "id_mensagem": 7},
        obter_rotulo=lambda conexao, *, id_hotel, id_reserva: {
            "id_reserva": 12,
            "telefone_contato": "5511999990000",
        },
    )
    texto = " ".join(registros)
    assert "id_reserva=12" in texto
    assert "sim:log" in texto
    assert "segredo do hospede" not in texto
    assert "5511999990000" not in texto
