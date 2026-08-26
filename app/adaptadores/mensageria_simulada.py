"""Adaptador de demonstracao: sucede localmente, sem rede."""

from app.portas.mensageria import ResultadoEnvio


class MensageriaSimulada:
    def enviar_coleta(
        self,
        *,
        telefone_destino: str,
        primeiro_nome: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        del telefone_destino, primeiro_nome, corpo, id_reserva
        return ResultadoEnvio(id_externo=f"sim-{id_mensagem}")

    def enviar_lembrete(
        self,
        *,
        telefone_destino: str,
        primeiro_nome: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        del telefone_destino, primeiro_nome, corpo, id_reserva
        return ResultadoEnvio(id_externo=f"sim-{id_mensagem}")

    def enviar_boas_vindas(
        self,
        *,
        telefone_destino: str,
        variaveis: tuple[str, str, str, str],
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        del telefone_destino, variaveis, corpo, id_reserva
        return ResultadoEnvio(id_externo=f"sim-{id_mensagem}")

    def enviar_texto_sessao(
        self,
        *,
        telefone_destino: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        del telefone_destino, corpo, id_reserva
        return ResultadoEnvio(id_externo=f"sim-{id_mensagem}")

    def enviar_pulso(
        self,
        *,
        telefone_destino: str,
        primeiro_nome: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        del telefone_destino, primeiro_nome, corpo, id_reserva
        return ResultadoEnvio(id_externo=f"sim-{id_mensagem}")

    def enviar_pesquisa_saida(
        self,
        *,
        telefone_destino: str,
        primeiro_nome: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        del telefone_destino, primeiro_nome, corpo, id_reserva
        return ResultadoEnvio(id_externo=f"sim-{id_mensagem}")

    def enviar_lista_pedidos_chat(
        self,
        *,
        telefone_destino: str,
        primeiro_nome: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        del telefone_destino, primeiro_nome, corpo, id_reserva
        return ResultadoEnvio(id_externo=f"sim-{id_mensagem}")
