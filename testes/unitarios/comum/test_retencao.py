"""Vencimento civil e marcas da politica de retencao."""

from datetime import UTC, datetime

from app.comum.retencao import (
    MARCA_PAYLOAD,
    MARCA_TELEFONE,
    MARCA_TEXTO,
    vencido_em_anos,
    vencido_em_meses,
)
from testes.suporte.retencao import (
    MARCA_PAYLOAD as MARCA_PAYLOAD_TESTE,
    MARCA_TELEFONE as MARCA_TELEFONE_TESTE,
    MARCA_TEXTO as MARCA_TEXTO_TESTE,
)


def test_marcas_coincidem_com_o_suporte():
    assert MARCA_TEXTO == MARCA_TEXTO_TESTE
    assert MARCA_PAYLOAD == MARCA_PAYLOAD_TESTE
    assert MARCA_TELEFONE == MARCA_TELEFONE_TESTE


def test_um_mes_a_partir_de_31_de_janeiro_cai_no_ultimo_dia_de_fevereiro():
    checkout = datetime(2026, 1, 31, 12, 0, tzinfo=UTC)
    limite = datetime(2026, 2, 28, 12, 0, tzinfo=UTC)
    assert vencido_em_meses(checkout, limite, 1) is True
    um_segundo_antes = datetime(2026, 2, 28, 11, 59, 59, tzinfo=UTC)
    assert vencido_em_meses(checkout, um_segundo_antes, 1) is False


def test_no_limite_vence_e_antes_nao():
    checkout = datetime(2025, 8, 24, 12, 0, tzinfo=UTC)
    limite = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
    assert vencido_em_meses(checkout, limite, 12) is True
    assert vencido_em_meses(
        checkout, datetime(2026, 8, 24, 11, 59, tzinfo=UTC), 12
    ) is False


def test_checkout_nulo_nunca_vence():
    agora = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
    assert vencido_em_meses(None, agora, 12) is False
    assert vencido_em_anos(None, agora, 5) is False


def test_cinco_anos_no_limite():
    checkout = datetime(2021, 8, 24, 12, 0, tzinfo=UTC)
    limite = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
    assert vencido_em_anos(checkout, limite, 5) is True
    assert vencido_em_anos(
        checkout, datetime(2026, 8, 24, 11, 59, tzinfo=UTC), 5
    ) is False
