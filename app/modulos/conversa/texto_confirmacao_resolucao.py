"""Recado padrao quando a solicitacao e marcada resolvida."""

from app.modulos.conversa.texto_coleta import primeiro_nome


def montar_confirmacao_resolucao(*, nome_completo: str, tipo: str) -> str:
    prenome = primeiro_nome(nome_completo)
    if tipo == "reclamacao":
        return (
            f"Ola, {prenome}!\n\n"
            "O problema que voce relatou foi atendido. "
            "A manutencao concluiu o chamado."
        )
    return (
        f"Ola, {prenome}!\n\n"
        "Seu pedido foi atendido. A equipe concluiu o servico."
    )
