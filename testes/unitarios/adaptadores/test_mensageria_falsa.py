"""Porta falsa de mensageria."""

import pytest

from app.adaptadores.mensageria_falsa import MensageriaFalsa
from app.portas.mensageria import FalhaDeEnvio


def test_sucesso_registra_um_envio():
    porta = MensageriaFalsa()
    resultado = porta.enviar_coleta(
        telefone_destino="5511987654321",
        primeiro_nome="Maria",
        corpo="Ola, Maria!",
        id_mensagem=7,
        id_reserva=42,
    )
    assert resultado.id_externo == "fake-7"
    assert len(porta.envios) == 1
    assert porta.envios[0]["telefone_destino"] == "5511987654321"


def test_lembrete_registra_tipo_distinto_da_coleta():
    porta = MensageriaFalsa()
    porta.enviar_lembrete(
        telefone_destino="5511987654321",
        primeiro_nome="Maria",
        corpo="Ola, Maria!",
        id_mensagem=8,
        id_reserva=42,
    )
    assert porta.envios[0]["tipo"] == "lembrete"
    assert porta.envios[0]["id_mensagem"] == 8


def test_lembrete_modo_falha_levanta_erro_tipado():
    porta = MensageriaFalsa()
    porta.falhar_sempre = True
    with pytest.raises(FalhaDeEnvio) as exc:
        porta.enviar_lembrete(
            telefone_destino="5511987654321",
            primeiro_nome="Maria",
            corpo="x",
            id_mensagem=1,
            id_reserva=1,
        )
    assert exc.value.codigo == "mensageria_indisponivel"
    assert porta.envios == []


def test_modo_falha_levanta_erro_tipado():
    porta = MensageriaFalsa()
    porta.falhar_sempre = True
    with pytest.raises(FalhaDeEnvio) as exc:
        porta.enviar_coleta(
            telefone_destino="5511987654321",
            primeiro_nome="Maria",
            corpo="x",
            id_mensagem=1,
            id_reserva=1,
        )
    assert exc.value.codigo == "mensageria_indisponivel"
    assert porta.envios == []
