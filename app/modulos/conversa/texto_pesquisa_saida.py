"""Montagem pura do texto da pesquisa de saida."""

from app.modulos.conversa.texto_coleta import primeiro_nome


def montar_texto_pesquisa_saida(*, nome_completo: str) -> str:
    prenome = primeiro_nome(nome_completo)
    return (
        f"Ola, {prenome}!\n\n"
        "Sua estadia encerrou. Responda com a lista numerada:\n\n"
        "1. De 1 a 5, que nota voce da a esta estadia?\n"
        "2. Comentario, se quiser (opcional)\n"
        "3. Aceita receber comunicacoes futuras do hotel? Responda sim ou nao"
    )
