"""Montagem pura do recado curto de boas-vindas."""

from app.modulos.conversa.texto_coleta import primeiro_nome


AVISO_ASSISTENTE_VIRTUAL = (
    "O atendimento inicial e feito por uma assistente virtual. "
    "Uma pessoa da recepcao assume quando necessario."
)


def montar_texto_boas_vindas(
    *, nome_completo: str, cafe: str, wifi: str, checkout: str
) -> str:
    prenome = primeiro_nome(nome_completo)
    return (
        f"Ola, {prenome}! Sua chegada esta confirmada, seja bem-vindo.\n"
        f"Cafe da manha: {cafe}\n"
        f"Wi-Fi: {wifi}\n"
        f"Checkout: {checkout}\n"
        f"{AVISO_ASSISTENTE_VIRTUAL}\n"
        "Quer saber mais alguma coisa da sua estadia? Pode perguntar por aqui."
    )
