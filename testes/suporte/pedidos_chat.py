"""Constantes estaveis da lista de pedidos feitos pelo chat (F4.2)."""

ROTULO = "pedidos feitos pelo chat"
CAMINHO_LISTA = "/reservas/{id}/pedidos-feitos-pelo-chat"


def proibicoes_da_lista() -> tuple[str, ...]:
    return ("extrato", "conta")
