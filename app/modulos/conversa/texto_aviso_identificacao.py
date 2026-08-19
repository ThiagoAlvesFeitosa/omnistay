"""Recado quando a identificacao do item precisa de pessoa."""

from app.modulos.conversa.texto_coleta import primeiro_nome


def montar_aviso_identificacao(*, nome_completo: str) -> str:
    prenome = primeiro_nome(nome_completo)
    return (
        f"Ola, {prenome}!\n\n"
        "Recebemos sua mensagem. A recepcao vai conferir e retornar."
    )
