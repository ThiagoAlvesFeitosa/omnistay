"""Recado padrao quando o pedido de servico e registrado."""

from app.modulos.conversa.texto_coleta import primeiro_nome


def montar_confirmacao_pedido(*, nome_completo: str) -> str:
    prenome = primeiro_nome(nome_completo)
    return (
        f"Ola, {prenome}!\n\n"
        "Recebemos seu pedido. A equipe ja foi avisada e vai atender."
    )
