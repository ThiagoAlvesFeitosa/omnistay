"""Normalizacao e validacao de telefone brasileiro para mensageria."""

import pytest

from app.comum import telefone


def test_mascara_e_digitos_nacionais_viram_o_mesmo_canonico():
    assert telefone.normalizar("(11) 98765-4321") == "5511987654321"
    assert telefone.normalizar("11987654321") == "5511987654321"
    assert telefone.normalizar("+55 11 98765-4321") == "5511987654321"


def test_fixo_com_ddd_dez_digitos_e_aceito():
    assert telefone.normalizar("(11) 3456-7890") == "551134567890"
    assert telefone.normalizar("1134567890") == "551134567890"


def test_numero_curto_e_recusado():
    with pytest.raises(telefone.TelefoneInvalido):
        telefone.normalizar("123")


def test_estrangeiro_sem_prefixo_55_valido_e_recusado():
    with pytest.raises(telefone.TelefoneInvalido):
        telefone.normalizar("441234567890")


def test_saida_e_somente_digitos_com_prefixo_55():
    canonico = telefone.normalizar("11 98765 4321")
    assert canonico.isdigit()
    assert canonico.startswith("55")
    assert len(canonico) in (12, 13)
