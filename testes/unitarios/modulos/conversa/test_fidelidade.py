"""Fidelidade da resposta automatica ao catalogo."""

from app.modulos.conversa.fidelidade import resposta_fiel_ao_catalogo
from testes.suporte.resposta_duvida import item_cafe, item_outro_hotel


def test_aceita_trecho_presente_no_catalogo_e_no_texto():
    itens = (item_cafe(),)
    assert resposta_fiel_ao_catalogo("Cafe das 7h as 10h", ("7h as 10h",), itens)


def test_rejeita_trechos_vazios():
    assert not resposta_fiel_ao_catalogo("7h as 10h", (), (item_cafe(),))


def test_rejeita_trecho_orfao():
    itens = (item_cafe(),)
    assert not resposta_fiel_ao_catalogo(
        "piscina olimpica 6h", ("piscina olimpica 6h",), itens
    )


def test_rejeita_trecho_ausente_do_texto():
    itens = (item_cafe(),)
    assert not resposta_fiel_ao_catalogo("horario do almoco", ("7h as 10h",), itens)


def test_nao_usa_item_de_outro_conjunto():
    assert not resposta_fiel_ao_catalogo(
        "piscina olimpica 6h",
        ("piscina olimpica 6h",),
        (item_cafe(),),
    )
    assert resposta_fiel_ao_catalogo(
        "abre piscina olimpica 6h",
        ("piscina olimpica 6h",),
        (item_outro_hotel(),),
    )
