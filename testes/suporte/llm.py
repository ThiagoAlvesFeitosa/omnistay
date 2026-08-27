"""Apoio da suíte do adaptador de linguagem. Uso só em teste."""

from collections.abc import Callable

import httpx


def cfg_llm(
    modo: str,
    chave: str = "",
    timeout: float = 15.0,
    modelo: str = "gemini-2.0-flash",
    mensageria_modo: str = "demonstracao",
):
    return type(
        "C",
        (),
        {
            "llm_modo": modo,
            "gemini_api_key": chave,
            "llm_timeout_seconds": timeout,
            "llm_modelo": modelo,
            "mensageria_modo": mensageria_modo,
        },
    )()


def cliente_gemini_falso(
    handler: Callable[[httpx.Request], httpx.Response],
) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))
