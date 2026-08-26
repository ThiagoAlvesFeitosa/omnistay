"""Fabrica de mensageria escolhe o adaptador pelo modo."""

import pytest

from app.adaptadores.fabrica_mensageria import (
    ConfiguracaoDeMensageriaInvalida,
    construir_mensageria,
)
from app.adaptadores.mensageria_simulada import MensageriaSimulada
from app.adaptadores.mensageria_whatsapp import MensageriaWhatsapp


def _cfg(modo: str):
    return type("C", (), {"mensageria_modo": modo})()


def test_demonstracao_devolve_simulada():
    porta = construir_mensageria(_cfg("demonstracao"))
    assert isinstance(porta, MensageriaSimulada)
    assert not isinstance(porta, MensageriaWhatsapp)


def test_real_devolve_whatsapp_sem_rede():
    porta = construir_mensageria(_cfg("real"))
    assert isinstance(porta, MensageriaWhatsapp)


@pytest.mark.parametrize("modo", ["", "whatsapp", "teste", "DEMO"])
def test_modo_ausente_ou_invalido_falha_alto(modo):
    with pytest.raises(ConfiguracaoDeMensageriaInvalida):
        construir_mensageria(_cfg(modo))
