"""Montagem pura do recado curto de boas-vindas."""

from app.modulos.conversa.texto_coleta import primeiro_nome


def montar_texto_boas_vindas(
    *, nome_completo: str, cafe: str, wifi: str, checkout: str
) -> str:
    prenome = primeiro_nome(nome_completo)
    return (
        f"Ola, {prenome}! Sua chegada esta confirmada, seja bem-vindo.\n"
        f"Cafe da manha: {cafe}\n"
        f"Wi-Fi: {wifi}\n"
        f"Checkout: {checkout}\n"
        "Quer saber mais alguma coisa da sua estadia? Pode perguntar por aqui."
    )
