"""CRUD HTTP de item vendavel."""

from decimal import Decimal

import pytest

from testes.integracao.test_reservas import _login
from testes.suporte.consumo import (
    DETALHE_ITEM_NAO_ENCONTRADO,
    DETALHE_NOME_DUPLICADO,
    NOME_ITEM,
    PRECO_ATUAL,
)


@pytest.mark.postgres
def test_recepcao_cria_lista_e_altera_item_vendavel(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    criado = cliente.post(
        "/itens-vendaveis",
        json={"nome": NOME_ITEM, "preco_atual": "12.00"},
    )
    assert criado.status_code == 201
    corpo = criado.json()
    assert corpo["nome"] == NOME_ITEM
    assert Decimal(str(corpo["preco_atual"])) == PRECO_ATUAL
    assert corpo["ativo"] is True
    id_item = corpo["id_item_vendavel"]
    lista = cliente.get("/itens-vendaveis")
    assert lista.status_code == 200
    assert any(i["id_item_vendavel"] == id_item for i in lista.json()["itens"])
    duplicado = cliente.post(
        "/itens-vendaveis",
        json={"nome": "cerveja", "preco_atual": "10.00"},
    )
    assert duplicado.status_code == 409
    assert duplicado.json()["detail"] == DETALHE_NOME_DUPLICADO
    negativo = cliente.post(
        "/itens-vendaveis", json={"nome": "Agua", "preco_atual": "-1"}
    )
    assert negativo.status_code == 422
    patch = cliente.patch(
        f"/itens-vendaveis/{id_item}", json={"preco_atual": "20.00"}
    )
    assert patch.status_code == 200
    assert Decimal(str(patch.json()["preco_atual"])) == Decimal("20.00")


@pytest.mark.postgres
def test_gestao_le_e_nao_altera_staff_recusado_hotel_b_isolado(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_item = cliente.post(
        "/itens-vendaveis",
        json={"nome": NOME_ITEM, "preco_atual": "12.00"},
    ).json()["id_item_vendavel"]
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    assert cliente.get("/itens-vendaveis").status_code == 200
    assert cliente.post(
        "/itens-vendaveis", json={"nome": "Agua", "preco_atual": "5.00"}
    ).status_code == 403
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.get("/itens-vendaveis").status_code == 403
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    lista_b = cliente.get("/itens-vendaveis")
    assert lista_b.status_code == 200
    assert lista_b.json()["itens"] == []
    ausente = cliente.patch(
        f"/itens-vendaveis/{id_item}", json={"ativo": False}
    )
    assert ausente.status_code == 404
    assert ausente.json()["detail"] == DETALHE_ITEM_NAO_ENCONTRADO
