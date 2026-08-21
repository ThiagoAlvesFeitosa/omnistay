"""Constantes estaveis dos testes de coleta de mercado. Sem segredo, sem rede."""

from decimal import Decimal

from testes.suporte.concorrentes import NOME, URL_FONTE

CHAVE_PERIODICIDADE = "periodicidade_coleta_mercado"
PERIODICIDADE_PADRAO = "24"
PRECO_FIXTURE = Decimal("150.00")
NOTA_FIXTURE = Decimal("4.50")
IDENTIDADE_COLETOR = "OmniStay-Coletor/1.0"

__all__ = [
    "CHAVE_PERIODICIDADE",
    "PERIODICIDADE_PADRAO",
    "PRECO_FIXTURE",
    "NOTA_FIXTURE",
    "IDENTIDADE_COLETOR",
    "NOME",
    "URL_FONTE",
]
