"""Recado padrao quando a reclamacao tecnica vira chamado."""

from app.modulos.conversa.texto_coleta import primeiro_nome


def montar_confirmacao_reclamacao(
    *, nome_completo: str, perguntar_horario: bool
) -> str:
    prenome = primeiro_nome(nome_completo)
    partes = [
        f"Ola, {prenome}!",
        "",
        "Recebemos sua mensagem. A manutencao ja esta sendo acionada.",
    ]
    if perguntar_horario:
        partes.extend(
            ["", "Qual horario voce prefere para o atendimento?"]
        )
    return "\n".join(partes)
