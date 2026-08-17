"""Recado padrao quando a duvida nao esta no catalogo."""

from app.modulos.conversa.texto_coleta import primeiro_nome


def montar_aviso_duvida_nao_coberta(*, nome_completo: str) -> str:
    prenome = primeiro_nome(nome_completo)
    return (
        f"Ola, {prenome}!\n\n"
        "Recebemos sua pergunta. A recepcao vai atender por aqui em seguida."
    )
