"""Assinatura de envelopes de webhook para a suíte — sem segredo versionado.

O caminho da conversa da estadia (F3.1 + F3.2) é: POST /webhook assinado, depois
`python -m worker --uma-passagem` com `LLMFalso`. Nenhum teste chama o provedor real.
"""

import hashlib
import hmac
import json


def assinar(corpo: bytes, segredo: str) -> str:
    digest = hmac.new(segredo.encode("utf-8"), corpo, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def postar_webhook(
    cliente,
    payload: dict,
    *,
    segredo: str,
    cabecalho: str = "X-Omnistay-Signature",
):
    corpo = json.dumps(payload).encode("utf-8")
    return cliente.post(
        "/webhook",
        content=corpo,
        headers={
            "Content-Type": "application/json",
            cabecalho: assinar(corpo, segredo),
        },
    )
