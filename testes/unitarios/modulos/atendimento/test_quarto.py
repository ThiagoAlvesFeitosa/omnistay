"""Extracao de numero de quarto a partir do texto do pedido."""

from app.modulos.atendimento.quarto import extrair_numero_quarto


def test_extrai_quarto_apartamento_apto_e_uh():
    assert extrair_numero_quarto("pode mandar uma toalha extra no quarto 402") == "402"
    assert extrair_numero_quarto("travesseiro, apto 12") == "12"
    assert extrair_numero_quarto("cobertor no apartamento 8B") == "8B"
    assert extrair_numero_quarto("uh 15 precisa de toalha") == "15"


def test_sem_palavra_chave_nao_inventa_quarto():
    assert extrair_numero_quarto("toalha extra") is None
    assert extrair_numero_quarto("estou no 402") is None
    assert extrair_numero_quarto("") is None
