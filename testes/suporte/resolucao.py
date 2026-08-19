"""Constantes estaveis da resolucao de solicitacao (F3.6)."""

DETALHE_JA_RESOLVIDA = "Esta solicitacao ja foi resolvida."
DETALHE_NAO_ENCONTRADA = "Solicitacao nao encontrada."
DETALHE_CANCELADA = "Solicitacao cancelada nao pode ser resolvida."
DETALHE_ESTADO = "O estado atual da solicitacao nao admite resolucao."


def proibicoes_do_recado() -> tuple[str, ...]:
    return (
        "extrato",
        "conta",
        "cardapio",
        "preferencia",
        "garantia",
        "minuto",
        "filtro",
        "toalha",
    )
