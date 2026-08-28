"""Adaptador WhatsApp envia o template de boas-vindas sem abrir a rede."""

import json

import httpx

from app.adaptadores.mensageria_whatsapp import MensageriaWhatsapp


def test_enviar_boas_vindas_manda_cinco_parametros_na_ordem(monkeypatch):
    pedidos: list[httpx.Request] = []

    def handler(pedido: httpx.Request) -> httpx.Response:
        pedidos.append(pedido)
        return httpx.Response(200, json={"messages": [{"id": "wamid.1"}]})

    cliente = httpx.Client(transport=httpx.MockTransport(handler))

    def fake_post(url, **kwargs):
        return cliente.post(url, **kwargs)

    monkeypatch.setattr(
        "app.adaptadores.mensageria_whatsapp.httpx.post", fake_post
    )

    porta = MensageriaWhatsapp(token="tok", phone_number_id="12345")
    resultado = porta.enviar_boas_vindas(
        telefone_destino="5511999990000",
        variaveis=("Maria", "7h", "wifi", "12h", "Pode perguntar sobre o spa."),
        corpo="nao deve ir no template",
        id_mensagem=9,
        id_reserva=3,
    )

    assert resultado.id_externo == "wamid.1"
    assert len(pedidos) == 1
    corpo = json.loads(pedidos[0].content)
    assert corpo["template"]["name"] == "boas_vindas"
    parametros = corpo["template"]["components"][0]["parameters"]
    assert [p["text"] for p in parametros] == [
        "Maria",
        "7h",
        "wifi",
        "12h",
        "Pode perguntar sobre o spa.",
    ]
    assert "nao deve ir no template" not in pedidos[0].content.decode()
