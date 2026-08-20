"""Texto puro da lista de pedidos feitos pelo chat."""

from decimal import Decimal

from app.modulos.conversa.texto_lista_pedidos_chat import (
    montar_texto_lista_pedidos_chat,
)
from testes.suporte.pedidos_chat import ROTULO, proibicoes_da_lista


def test_lista_usa_rotulo_prenome_total_e_alcance():
    texto = montar_texto_lista_pedidos_chat(
        nome_completo="Marina Duarte",
        itens=[
            {
                "descricao_item": "Cerveja",
                "valor_praticado": Decimal("12.00"),
            },
            {
                "descricao_item": "Agua",
                "valor_praticado": Decimal("5.50"),
            },
        ],
    )
    baixo = texto.casefold()
    assert "marina" in baixo
    assert "duarte" not in baixo
    assert ROTULO in baixo
    assert "Cerveja" in texto
    assert "R$ 12,00" in texto
    assert "Agua" in texto
    assert "R$ 5,50" in texto
    assert "Total dos pedidos feitos pelo chat" in texto
    assert "R$ 17,50" in texto
    assert "somente" in baixo
    assert "chat" in baixo
    assert "esta correto" not in baixo
    assert "?" not in texto
    for termo in proibicoes_da_lista():
        assert termo not in baixo
