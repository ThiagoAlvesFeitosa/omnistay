"""Adaptador WhatsApp Cloud API (template Utility). Nao usado pela suite."""

import os

import httpx

from app.portas.mensageria import FalhaDeEnvio, ResultadoEnvio


class MensageriaWhatsapp:
    def __init__(
        self,
        *,
        token: str | None = None,
        phone_number_id: str | None = None,
        template_name: str = "coleta_dados",
        template_language: str = "pt_BR",
    ) -> None:
        self.token = token or os.environ.get("WHATSAPP_TOKEN", "")
        self.phone_number_id = phone_number_id or os.environ.get(
            "WHATSAPP_PHONE_NUMBER_ID", ""
        )
        self.template_name = template_name
        self.template_language = template_language

    def enviar_coleta(
        self,
        *,
        telefone_destino: str,
        primeiro_nome: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        del corpo, id_reserva  # corpo ja esta no historico; template usa variaveis
        if not self.token or not self.phone_number_id:
            raise FalhaDeEnvio("whatsapp_nao_configurado")
        url = (
            f"https://graph.facebook.com/v21.0/{self.phone_number_id}/messages"
        )
        payload = {
            "messaging_product": "whatsapp",
            "to": telefone_destino,
            "type": "template",
            "template": {
                "name": self.template_name,
                "language": {"code": self.template_language},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": primeiro_nome},
                        ],
                    }
                ],
            },
        }
        try:
            resposta = httpx.post(
                url,
                headers={"Authorization": f"Bearer {self.token}"},
                json=payload,
                timeout=15.0,
            )
        except httpx.HTTPError as erro:
            raise FalhaDeEnvio("whatsapp_rede") from erro
        if resposta.status_code >= 400:
            raise FalhaDeEnvio(f"whatsapp_http_{resposta.status_code}")
        dados = resposta.json()
        mensagens = dados.get("messages") or []
        id_externo = mensagens[0].get("id") if mensagens else None
        return ResultadoEnvio(id_externo=id_externo)

    def enviar_boas_vindas(
        self,
        *,
        telefone_destino: str,
        variaveis: tuple[str, str, str, str],
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        del corpo, id_mensagem, id_reserva
        if not self.token or not self.phone_number_id:
            raise FalhaDeEnvio("whatsapp_nao_configurado")
        url = (
            f"https://graph.facebook.com/v21.0/{self.phone_number_id}/messages"
        )
        payload = {
            "messaging_product": "whatsapp",
            "to": telefone_destino,
            "type": "template",
            "template": {
                "name": "boas_vindas",
                "language": {"code": self.template_language},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": valor} for valor in variaveis
                        ],
                    }
                ],
            },
        }
        try:
            resposta = httpx.post(
                url,
                headers={"Authorization": f"Bearer {self.token}"},
                json=payload,
                timeout=15.0,
            )
        except httpx.HTTPError as erro:
            raise FalhaDeEnvio("whatsapp_rede") from erro
        if resposta.status_code >= 400:
            raise FalhaDeEnvio(f"whatsapp_http_{resposta.status_code}")
        dados = resposta.json()
        mensagens = dados.get("messages") or []
        id_externo = mensagens[0].get("id") if mensagens else None
        return ResultadoEnvio(id_externo=id_externo)

    def enviar_lembrete(
        self,
        *,
        telefone_destino: str,
        primeiro_nome: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        return self.enviar_coleta(
            telefone_destino=telefone_destino,
            primeiro_nome=primeiro_nome,
            corpo=corpo,
            id_mensagem=id_mensagem,
            id_reserva=id_reserva,
        )

    def enviar_texto_sessao(
        self,
        *,
        telefone_destino: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        del id_mensagem, id_reserva
        if not self.token or not self.phone_number_id:
            raise FalhaDeEnvio("whatsapp_nao_configurado")
        url = (
            f"https://graph.facebook.com/v21.0/{self.phone_number_id}/messages"
        )
        payload = {
            "messaging_product": "whatsapp",
            "to": telefone_destino,
            "type": "text",
            "text": {"body": corpo},
        }
        try:
            resposta = httpx.post(
                url,
                headers={"Authorization": f"Bearer {self.token}"},
                json=payload,
                timeout=15.0,
            )
        except httpx.HTTPError as erro:
            raise FalhaDeEnvio("whatsapp_rede") from erro
        if resposta.status_code >= 400:
            raise FalhaDeEnvio(f"whatsapp_http_{resposta.status_code}")
        dados = resposta.json()
        mensagens = dados.get("messages") or []
        id_externo = mensagens[0].get("id") if mensagens else None
        return ResultadoEnvio(id_externo=id_externo)

    def enviar_pesquisa_saida(
        self,
        *,
        telefone_destino: str,
        primeiro_nome: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        raise NotImplementedError("template pesquisa_saida ainda nao cadastrado")

    def enviar_lista_pedidos_chat(
        self,
        *,
        telefone_destino: str,
        primeiro_nome: str,
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio:
        raise NotImplementedError("template lista_pedidos_chat ainda nao cadastrado")
