"""Porta falsa de mensageria — envio em sessao."""

import pytest

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.portas.mensageria import FalhaDeEnvio


def test_enviar_texto_sessao_registra_corpo():
    porta = MensageriaFalsa()
    resultado = porta.enviar_texto_sessao(
        telefone_destino="5511999999999",
        corpo="Cafe das 7h as 10h",
        id_mensagem=3,
        id_reserva=2,
    )
    assert resultado.id_externo == "fake-3"
    assert porta.envios[0]["tipo"] == "sessao"
    assert porta.envios[0]["corpo"] == "Cafe das 7h as 10h"


def test_enviar_texto_sessao_falha_tipada():
    porta = MensageriaFalsa()
    porta.falhar_sempre = True
    with pytest.raises(FalhaDeEnvio) as erro:
        porta.enviar_texto_sessao(
            telefone_destino="5511999999999",
            corpo="segredo",
            id_mensagem=1,
            id_reserva=1,
        )
    assert erro.value.codigo == "mensageria_indisponivel"
