"""Protocolo de mensageria declara envio de pulso."""

import inspect

from app.portas.mensageria import MensageriaGateway


def test_protocolo_declara_enviar_pulso():
    parametros = inspect.signature(MensageriaGateway.enviar_pulso).parameters
    assert {
        "telefone_destino",
        "primeiro_nome",
        "corpo",
        "id_mensagem",
        "id_reserva",
    }.issubset(parametros)
