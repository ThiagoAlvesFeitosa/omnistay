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

    def enviar_lembrete(
        self,
        *,
        telefone_destino: str,
        primeiro_nome: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio: ...

    def enviar_boas_vindas(
        self,
        *,
        telefone_destino: str,
        variaveis: tuple[str, str, str, str],
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio: ...

    def enviar_texto_sessao(
        self,
        *,
        telefone_destino: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio: ...

    def enviar_pulso(
        self,
        *,
        telefone_destino: str,
        primeiro_nome: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio: ...

    def enviar_pesquisa_saida(
        self,
        *,
        telefone_destino: str,
        primeiro_nome: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio: ...

    def enviar_lista_pedidos_chat(
        self,
        *,
        telefone_destino: str,
        primeiro_nome: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio: ...
