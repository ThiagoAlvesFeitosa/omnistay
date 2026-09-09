"""Fidelidade da resposta automatica ao catalogo."""

from app.modulos.conversa.fidelidade import resposta_fiel_ao_catalogo
from app.portas.catalogo import ItemCatalogo
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


def _item_piscina() -> ItemCatalogo:
    return ItemCatalogo(
        id_catalogo_item=2,
        categoria="horario",
        titulo="Piscina",
        conteudo="Aberta das 8h as 22h",
    )


def test_aceita_trecho_com_acento_contra_catalogo_sem_acento():
    assert resposta_fiel_ao_catalogo(
        "A piscina fica aberta das 8h às 22h.",
        ("às 22h",),
        (_item_piscina(),),
    )


def test_aceita_trecho_com_espaco_duplo():
    assert resposta_fiel_ao_catalogo(
        "Cafe das 7h as 10h",
        ("7h as  10h",),
        (item_cafe(),),
    )


def test_rejeita_trecho_que_nao_existe_no_catalogo():
    assert not resposta_fiel_ao_catalogo(
        "Piscina aberta ate meia-noite",
        ("ate meia-noite",),
        (_item_piscina(),),
    )


def test_rejeita_resposta_que_nao_contem_o_trecho_citado():
    assert not resposta_fiel_ao_catalogo(
        "A piscina fica no terreo.",
        ("8h as 22h",),
        (_item_piscina(),),
    )


def test_aceita_trecho_no_formato_exato_do_prompt():
    item = _item_piscina()
    trecho = f"{item.titulo}: {item.conteudo}"
    assert trecho == "Piscina: Aberta das 8h as 22h"
    assert resposta_fiel_ao_catalogo(f"{trecho}.", (trecho,), (item,))


def test_rejeita_trecho_inventado_mesmo_no_formato_do_prompt():
    assert not resposta_fiel_ao_catalogo(
        "Sauna: Aberta 24h",
        ("Sauna: Aberta 24h",),
        (_item_piscina(),),
    )
