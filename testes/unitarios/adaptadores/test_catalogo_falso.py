"""CatalogoFalso devolve o que o teste configurou, sem banco."""

from app.adaptadores.catalogo_falso import CatalogoFalso
from app.portas.catalogo import ItemCatalogo


def test_falso_devolve_ativos_do_hotel_configurado():
    falso = CatalogoFalso()
    item = ItemCatalogo(
        id_catalogo_item=1,
        categoria="horario",
        titulo="Cafe",
        conteudo="7h",
    )
    falso.configurar(3, (item,))
    assert falso.listar_ativos(3) == (item,)
    assert falso.listar_ativos(9) == ()


def test_falso_sem_configuracao_e_tupla_vazia():
    assert CatalogoFalso().listar_ativos(1) == ()
