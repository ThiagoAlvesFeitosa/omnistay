"""Porta de mensageria — o dominio depende so desta interface."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ResultadoEnvio:
    id_externo: str | None = None


class FalhaDeEnvio(Exception):
    """Falha tipada do provedor, sem corpo de mensagem."""

    def __init__(self, codigo: str) -> None:
        self.codigo = codigo
        super().__init__(codigo)


class MensageriaGateway(Protocol):
    def enviar_coleta(
        self,
        *,
        telefone_destino: str,
        primeiro_nome: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio: ...
