"""Contrato da porta de identificacao de item vendavel."""

import pytest

from app.portas.llm import FalhaDeIdentificacao, ResultadoIdentificacao


def test_resultado_unico_carrega_id_e_quantidade():
    resultado = ResultadoIdentificacao(
        desfecho="unico", id_item_vendavel=3, quantidade=2
    )
    assert resultado.desfecho == "unico"
    assert resultado.id_item_vendavel == 3
    assert resultado.quantidade == 2


def test_resultado_nenhum_e_ambiguo_nao_carregam_item():
    nenhum = ResultadoIdentificacao(desfecho="nenhum")
    ambiguo = ResultadoIdentificacao(desfecho="ambiguo")
    assert nenhum.id_item_vendavel is None
    assert ambiguo.id_item_vendavel is None


def test_falha_de_identificacao_nao_ecoa_texto():
    erro = FalhaDeIdentificacao("indisponivel")
    assert erro.codigo == "indisponivel"
    assert "cerveja" not in str(erro).casefold()
    with pytest.raises(FalhaDeIdentificacao):
        raise FalhaDeIdentificacao("tempo_esgotado")
