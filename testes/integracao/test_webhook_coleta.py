"""Webhook de coleta — grava sem interpretar."""

import hashlib
import hmac
import json

import pytest
from sqlalchemy import text

from testes.integracao.test_reservas import _corpo_valido, _login

SEGREDO = "segredo-teste-webhook"


def _assinar(corpo: bytes) -> str:
    digest = hmac.new(SEGREDO.encode(), corpo, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _post_webhook(cliente, payload: dict):
    corpo = json.dumps(payload).encode("utf-8")
    return cliente.post(
        "/webhook",
        content=corpo,
        headers={
            "Content-Type": "application/json",
            "X-Omnistay-Signature": _assinar(corpo),
        },
    )


@pytest.fixture
def webhook_configurado(app_sobre_ambiente, monkeypatch):
    cliente, ambiente = app_sobre_ambiente
    monkeypatch.setenv("WHATSAPP_APP_SECRET", SEGREDO)
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "token-teste")
    monkeypatch.setenv("WHATSAPP_ID_HOTEL", str(ambiente.propriedade_a.id_hotel))
    from app.config import obter_configuracao

    obter_configuracao.cache_clear()
    return cliente, ambiente


@pytest.mark.postgres
def test_assinatura_invalida_e_rejeitada(webhook_configurado):
    cliente, _ = webhook_configurado
    corpo = b'{"id_externo":"x"}'
    resposta = cliente.post(
        "/webhook",
        content=corpo,
        headers={
            "Content-Type": "application/json",
            "X-Omnistay-Signature": "sha256=00",
        },
    )
    assert resposta.status_code == 401


@pytest.mark.postgres
def test_evento_valido_cria_mensagem_e_trabalho_sem_mudar_status(webhook_configurado):
    cliente, ambiente = webhook_configurado
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_reserva = cliente.post("/reservas", json=_corpo_valido()).json()["id_reserva"]

    resposta = _post_webhook(
        cliente,
        {
            "id_externo": "evt-1",
            "telefone_origem": "11987654321",
            "texto": "1. Maria Silva\n2. Engenheira",
            "tem_texto_utilizavel": True,
        },
    )
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "enfileirado"

    with ambiente.conexao() as conexao:
        status = conexao.execute(
            text("SELECT status FROM reserva WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        recebidas = conexao.execute(
            text(
                "SELECT COUNT(*) FROM mensagem"
                " WHERE id_reserva = :r AND direcao = 'recebida'"
            ),
            {"r": id_reserva},
        ).scalar_one()
        trabalhos = conexao.execute(
            text(
                "SELECT COUNT(*) FROM trabalho"
                " WHERE tipo = 'interpretar_ficha'"
                " AND (payload->>'id_reserva')::bigint = :r"
            ),
            {"r": id_reserva},
        ).scalar_one()
        eventos = conexao.execute(
            text("SELECT COUNT(*) FROM evento_webhook WHERE id_externo = 'evt-1'")
        ).scalar_one()

    assert status == "aguardando_cadastro"
    assert recebidas == 1
    assert trabalhos == 1
    assert eventos == 1


@pytest.mark.postgres
def test_reenvio_idempotente(webhook_configurado):
    cliente, ambiente = webhook_configurado
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    cliente.post("/reservas", json=_corpo_valido())

    payload = {
        "id_externo": "evt-dup",
        "telefone_origem": "11987654321",
        "texto": "resposta",
        "tem_texto_utilizavel": True,
    }
    assert _post_webhook(cliente, payload).status_code == 200
    assert _post_webhook(cliente, payload).json()["status"] == "duplicado"

    with ambiente.conexao() as conexao:
        assert (
            conexao.execute(
                text("SELECT COUNT(*) FROM mensagem WHERE direcao = 'recebida'")
            ).scalar_one()
            == 1
        )
        assert (
            conexao.execute(
                text("SELECT COUNT(*) FROM trabalho WHERE tipo = 'interpretar_ficha'")
            ).scalar_one()
            == 1
        )


@pytest.mark.postgres
def test_telefone_sem_reserva_grava_so_evento(webhook_configurado):
    cliente, ambiente = webhook_configurado
    resposta = _post_webhook(
        cliente,
        {
            "id_externo": "evt-orfao",
            "telefone_origem": "11999999999",
            "texto": "oi",
            "tem_texto_utilizavel": True,
        },
    )
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "sem_reserva"
    with ambiente.conexao() as conexao:
        assert (
            conexao.execute(
                text(
                    "SELECT COUNT(*) FROM evento_webhook WHERE id_externo = 'evt-orfao'"
                )
            ).scalar_one()
            == 1
        )
        assert (
            conexao.execute(
                text("SELECT COUNT(*) FROM trabalho WHERE tipo = 'interpretar_ficha'")
            ).scalar_one()
            == 0
        )
