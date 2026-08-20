"""Montagem pura dos recados do pulso do segundo dia."""

from app.modulos.conversa.texto_coleta import primeiro_nome

RECONHECIMENTO_PULSO = (
    "Obrigado por responder! Se precisar de qualquer coisa, e so chamar por aqui."
)

CONFIRMACAO_PULSO_NEGATIVO = (
    "Sinto muito. Ja avisei a recepcao e alguem vai falar com voce."
)


def montar_pergunta_pulso(*, nome_completo: str) -> str:
    prenome = primeiro_nome(nome_completo)
    return (
        f"Ola, {prenome}! Como esta sendo sua estadia? "
        "Pode responder por aqui em uma frase."
    )


def montar_reconhecimento_pulso() -> str:
    return RECONHECIMENTO_PULSO


def montar_confirmacao_pulso_negativo() -> str:
    return CONFIRMACAO_PULSO_NEGATIVO
