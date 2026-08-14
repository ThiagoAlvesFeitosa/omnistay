"""Prazos de silencio: bootstrap e ausencia sem default magico."""

from app.modulos.propriedade.service import PARAMETROS_SILENCIO_PADRAO
from worker.agendador import CHAVE_ATE_REENVIO, CHAVE_CORTE, _inteiro_positivo


def test_defaults_de_bootstrap_sao_24_e_12():
    assert PARAMETROS_SILENCIO_PADRAO[CHAVE_ATE_REENVIO] == "24"
    assert PARAMETROS_SILENCIO_PADRAO[CHAVE_CORTE] == "12"


def test_valor_invalido_nao_vira_inteiro_positivo():
    assert _inteiro_positivo(None) is None
    assert _inteiro_positivo("abc") is None
    assert _inteiro_positivo("0") is None
    assert _inteiro_positivo("-1") is None
    assert _inteiro_positivo("12") == 12
