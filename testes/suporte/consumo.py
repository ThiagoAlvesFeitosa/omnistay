"""Constantes estaveis de consumo faturavel (F3.7)."""

from decimal import Decimal

NOME_ITEM = "Cerveja"
PRECO_ATUAL = Decimal("12.00")
DETALHE_JA_LANCADO = "Este consumo ja foi lancado."
DETALHE_JA_DISPENSADO = "Este consumo ja foi dispensado."
DETALHE_SOLICITACAO_NAO_ENCONTRADA = "Solicitacao nao encontrada."
DETALHE_ITEM_NAO_ENCONTRADO = "Item vendavel nao encontrado."
DETALHE_NOME_DUPLICADO = "Ja existe item vendavel ativo com este nome."
TEXTO_PEDIDO_CERVEJA = "uma cerveja no quarto 402"


def proibicoes_do_recado_consumo() -> tuple[str, ...]:
    return ("extrato", "conta", "lancado no pms", "ja foi lancado")
