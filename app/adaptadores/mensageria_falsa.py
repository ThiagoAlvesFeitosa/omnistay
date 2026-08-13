"""Implementacao falsa de MensageriaGateway para testes e desenvolvimento."""

from app.portas.mensageria import FalhaDeEnvio, ResultadoEnvio


class MensageriaFalsa:
    def __init__(self) -> None:
        self.envios: list[dict] = []
        self.falhar_sempre = False
        self.falhas_restantes = 0

    def enviar_coleta(
        self,
        *,
        telefone_destino: str,
        primeiro_nome: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        if self.falhar_sempre or self.falhas_restantes > 0:
            if self.falhas_restantes > 0:
                self.falhas_restantes -= 1
            raise FalhaDeEnvio("mensageria_indisponivel")
        registro = {
            "telefone_destino": telefone_destino,
            "primeiro_nome": primeiro_nome,
            "corpo": corpo,
            "id_mensagem": id_mensagem,
            "id_reserva": id_reserva,
        }
        self.envios.append(registro)
        return ResultadoEnvio(id_externo=f"fake-{id_mensagem}")
