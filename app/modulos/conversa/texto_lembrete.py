"""Montagem pura do texto do lembrete de cadastro."""

from app.modulos.conversa.texto_coleta import primeiro_nome


def montar_texto_lembrete(*, nome_completo: str) -> str:
    prenome = primeiro_nome(nome_completo)
    return (
        f"Ola, {prenome}!\n\n"
        "Lembramos que o cadastro antecipado e opcional. Sem ele, o preenchimento "
        "sera feito na recepcao."
    )
