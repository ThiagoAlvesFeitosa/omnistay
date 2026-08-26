"""Escolhe o adaptador de mensageria pela configuracao de plataforma."""

from app.adaptadores.mensageria_simulada import MensageriaSimulada
from app.adaptadores.mensageria_whatsapp import MensageriaWhatsapp
from app.portas.mensageria import MensageriaGateway


class ConfiguracaoDeMensageriaInvalida(Exception):
    """Modo de canal ausente ou desconhecido — o processo nao sobe no escuro."""


def construir_mensageria(config) -> MensageriaGateway:
    modo = getattr(config, "mensageria_modo", "") or ""
    if modo == "demonstracao":
        return MensageriaSimulada()
    if modo == "real":
        return MensageriaWhatsapp()
    raise ConfiguracaoDeMensageriaInvalida(modo)
