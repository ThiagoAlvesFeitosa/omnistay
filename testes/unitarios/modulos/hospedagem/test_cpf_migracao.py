"""Planejamento da migracao de CPF para onze digitos."""

from app.modulos.hospedagem.cpf_migracao import planejar_migracao_cpf
from testes.suporte.cpf_ficha import CPF_VALIDO, CPF_VALIDO_PONTUADO


def test_pontuado_isolado_entra_na_conversao():
    plano = planejar_migracao_cpf([(7, CPF_VALIDO_PONTUADO)])
    assert plano.converter == (7,)
    assert plano.pular == ()


def test_ja_em_onze_digitos_isolado_entra_na_conversao():
    plano = planejar_migracao_cpf([(3, CPF_VALIDO)])
    assert plano.converter == (3,)
    assert plano.pular == ()


def test_par_pontuado_e_digitos_iguais_e_pulado_inteiro():
    plano = planejar_migracao_cpf(
        [(1, CPF_VALIDO_PONTUADO), (2, CPF_VALIDO)]
    )
    assert plano.converter == ()
    assert set(plano.pular) == {1, 2}
    assert plano.pares == 1


def test_tres_no_mesmo_grupo_sao_pulados():
    plano = planejar_migracao_cpf(
        [(10, "529.982.247-25"), (11, "52998224725"), (12, "529 982 247 25")]
    )
    assert plano.converter == ()
    assert set(plano.pular) == {10, 11, 12}
    assert plano.pares == 1


def test_texto_de_colisao_nao_traz_o_numero():
    plano = planejar_migracao_cpf(
        [(1, CPF_VALIDO_PONTUADO), (2, CPF_VALIDO)]
    )
    recado = plano.texto_colisao()
    assert "cpf_migracao_colisao" in recado
    assert "pares=1" in recado
    assert "ids=" in recado
    assert CPF_VALIDO not in recado
    assert CPF_VALIDO_PONTUADO not in recado
