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
        return self._registrar(
            tipo="coleta",
            telefone_destino=telefone_destino,
            primeiro_nome=primeiro_nome,
            corpo=corpo,
            id_mensagem=id_mensagem,
            id_reserva=id_reserva,
        )

    def enviar_lembrete(
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
        return self._registrar(
            tipo="lembrete",
            telefone_destino=telefone_destino,
            primeiro_nome=primeiro_nome,
            corpo=corpo,
            id_mensagem=id_mensagem,
            id_reserva=id_reserva,
        )

    def enviar_boas_vindas(
        self,
        *,
        telefone_destino: str,
        variaveis: tuple[str, str, str, str],
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        if self.falhar_sempre or self.falhas_restantes > 0:
            if self.falhas_restantes > 0:
                self.falhas_restantes -= 1
            raise FalhaDeEnvio("mensageria_indisponivel")
        prenome, cafe, wifi, checkout = variaveis
        registro = {
            "tipo": "boas_vindas",
            "telefone_destino": telefone_destino,
            "variaveis": variaveis,
            "primeiro_nome": prenome,
            "cafe": cafe,
            "wifi": wifi,
            "checkout": checkout,
            "corpo": corpo,
            "id_mensagem": id_mensagem,
            "id_reserva": id_reserva,
        }
        self.envios.append(registro)
        return ResultadoEnvio(id_externo=f"fake-{id_mensagem}")

    def enviar_texto_sessao(
        self,
        *,
        telefone_destino: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        if self.falhar_sempre or self.falhas_restantes > 0:
            if self.falhas_restantes > 0:
                self.falhas_restantes -= 1
            raise FalhaDeEnvio("mensageria_indisponivel")
        registro = {
            "tipo": "sessao",
            "telefone_destino": telefone_destino,
            "corpo": corpo,
            "id_mensagem": id_mensagem,
            "id_reserva": id_reserva,
        }
        self.envios.append(registro)
        return ResultadoEnvio(id_externo=f"fake-{id_mensagem}")

    def enviar_pulso(
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
        return self._registrar(
            tipo="pulso",
            telefone_destino=telefone_destino,
            primeiro_nome=primeiro_nome,
            corpo=corpo,
            id_mensagem=id_mensagem,
            id_reserva=id_reserva,
        )

    def enviar_pesquisa_saida(
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
        return self._registrar(
            tipo="pesquisa_saida",
            telefone_destino=telefone_destino,
            primeiro_nome=primeiro_nome,
            corpo=corpo,
            id_mensagem=id_mensagem,
            id_reserva=id_reserva,
        )

    def _registrar(
        self,
        *,
        tipo: str,
        telefone_destino: str,
        primeiro_nome: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        registro = {
            "tipo": tipo,
            "telefone_destino": telefone_destino,
            "primeiro_nome": primeiro_nome,
            "corpo": corpo,
            "id_mensagem": id_mensagem,
            "id_reserva": id_reserva,
        }
        self.envios.append(registro)
        return ResultadoEnvio(id_externo=f"fake-{id_mensagem}")
