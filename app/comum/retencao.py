"""Marcas e vencimento civil da politica de retencao. Sem SQL."""

import calendar
from datetime import datetime

MARCA_TEXTO = "[anonimizado]"
MARCA_PAYLOAD = {"anonimizado": True}
MARCA_TELEFONE = "anonimizado"

CHAVE_MESES = "meses_retencao_conteudo_livre"
CHAVE_ANOS = "anos_retencao_ficha"


def adicionar_meses(instante: datetime, meses: int) -> datetime:
    """Soma meses civis; 31 jan + 1 mes cai no ultimo dia de fevereiro."""
    ano = instante.year + (instante.month - 1 + meses) // 12
    mes = (instante.month - 1 + meses) % 12 + 1
    dia = min(instante.day, calendar.monthrange(ano, mes)[1])
    return instante.replace(year=ano, month=mes, day=dia)


def vencido_em_meses(
    checkout_em: datetime | None, agora: datetime, meses: int
) -> bool:
    if checkout_em is None:
        return False
    return agora >= adicionar_meses(checkout_em, meses)


def vencido_em_anos(
    checkout_em: datetime | None, agora: datetime, anos: int
) -> bool:
    return vencido_em_meses(checkout_em, agora, anos * 12)
