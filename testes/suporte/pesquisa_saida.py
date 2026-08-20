"""Constantes da pesquisa de saida (F4.1)."""

CHAVE_ATRIBUICAO_PESQUISA = "horas_atribuicao_pesquisa_saida"
VALOR_PADRAO_ATRIBUICAO = "24"


def proibicoes_da_pesquisa() -> tuple[str, ...]:
    return (
        "extrato",
        "conta",
        "oferta",
        "desconto",
        "promocao",
        "pedidos feitos pelo chat",
    )
