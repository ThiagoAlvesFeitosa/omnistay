import pytest

from app.comum.versao_do_banco import (
    VERSAO_MINIMA,
    VersaoDeBancoInsuficiente,
    exigir_versao_minima,
)


def test_versao_adotada_pelo_projeto_e_aceita():
    exigir_versao_minima(160004)


def test_versao_futura_e_aceita():
    exigir_versao_minima(170000)


def test_versao_anterior_e_recusada():
    with pytest.raises(VersaoDeBancoInsuficiente):
        exigir_versao_minima(150004)


def test_recusa_nomeia_a_versao_encontrada():
    with pytest.raises(VersaoDeBancoInsuficiente) as erro:
        exigir_versao_minima(140010)

    assert "14.10" in str(erro.value)


def test_recusa_nomeia_a_versao_exigida():
    with pytest.raises(VersaoDeBancoInsuficiente) as erro:
        exigir_versao_minima(150004)

    assert str(VERSAO_MINIMA // 10000) in str(erro.value)
