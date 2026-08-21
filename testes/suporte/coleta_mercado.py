"""Constantes estaveis dos testes de coleta de mercado. Sem segredo, sem rede."""

from datetime import UTC, datetime
from decimal import Decimal

from testes.suporte.concorrentes import NOME, URL_FONTE

CHAVE_PERIODICIDADE = "periodicidade_coleta_mercado"
PERIODICIDADE_PADRAO = "24"
PRECO_FIXTURE = Decimal("150.00")
NOTA_FIXTURE = Decimal("4.50")
IDENTIDADE_COLETOR = "OmniStay-Coletor/1.0"

SITUACAO_ATUAL = "atual"
SITUACAO_DESATUALIZADO = "desatualizado"
SITUACAO_CADENCIA_AUSENTE = "cadencia_ausente"
SITUACAO_SEM_COLETA = "sem_coleta"
SITUACAO_SO_FALHA = "so_falha"

AGORA_PAINEL = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)

__all__ = [
    "CHAVE_PERIODICIDADE",
    "PERIODICIDADE_PADRAO",
    "PRECO_FIXTURE",
    "NOTA_FIXTURE",
    "IDENTIDADE_COLETOR",
    "SITUACAO_ATUAL",
    "SITUACAO_DESATUALIZADO",
    "SITUACAO_CADENCIA_AUSENTE",
    "SITUACAO_SEM_COLETA",
    "SITUACAO_SO_FALHA",
    "AGORA_PAINEL",
    "NOME",
    "URL_FONTE",
]
