"""Fila destacada e clique de lancamento/dispensa."""

from decimal import Decimal

import pytest
from sqlalchemy import text

from app.modulos.atendimento.service import abrir_consumo, abrir_servico
from testes.integracao.test_reservas import _login
from testes.integracao.test_webhook_estadia import _criar_hospedada
from testes.suporte.consumo import (
    DETALHE_JA_DISPENSADO,
    DETALHE_JA_LANCADO,
    NOME_ITEM,
    PRECO_ATUAL,
)


def _semear_consumo(ambiente, id_reserva: int, descricao: str, quarto: str | None):
    with ambiente.engine.begin() as conexao:
        id_mensagem = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
                "VALUES (:r, 'recebida', :c) RETURNING id_mensagem"
            ),
            {"r": id_reserva, "c": descricao},
        ).scalar_one()
        id_hotel = conexao.execute(
            text("SELECT id_hotel FROM reserva WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        return abrir_consumo(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            descricao=descricao,
            descricao_item=NOME_ITEM,
            valor_praticado=PRECO_ATUAL,
            numero_quarto=quarto,
            urgencia="baixa",
        )


def _semear_servico(ambiente, id_reserva: int):
    with ambiente.engine.begin() as conexao:
        id_mensagem = conexao.execute(
            text(
                "INSERT INTO mensagem (id_reserva, direcao, conteudo) "
                "VALUES (:r, 'recebida', 'toalha extra') RETURNING id_mensagem"
            ),
            {"r": id_reserva},
        ).scalar_one()
        id_hotel = conexao.execute(
            text("SELECT id_hotel FROM reserva WHERE id_reserva = :r"),
            {"r": id_reserva},
        ).scalar_one()
        abrir_servico(
            conexao,
            id_hotel=id_hotel,
            id_reserva=id_reserva,
            id_mensagem=id_mensagem,
            descricao="toalha extra",
            numero_quarto=None,
            urgencia="baixa",
        )


@pytest.mark.postgres
def test_recepcao_lanca_e_segundo_clique_conflita(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987657001")
    id_sol = _semear_consumo(ambiente, id_reserva, "uma cerveja", "402")
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    primeira = cliente.post(f"/solicitacoes/{id_sol}/lancamento")
    assert primeira.status_code == 200
    corpo = primeira.json()
    assert corpo["status_lancamento"] == "lancado"
    assert corpo["id_usuario_lancamento"]
    assert corpo["lancado_em"]
    segunda = cliente.post(f"/solicitacoes/{id_sol}/lancamento")
    assert segunda.status_code == 409
    assert segunda.json()["detail"] == DETALHE_JA_LANCADO
    with ambiente.conexao() as conexao:
        valor = conexao.execute(
            text("SELECT valor_praticado FROM consumo WHERE id_solicitacao = :id"),
            {"id": id_sol},
        ).scalar_one()
    assert Decimal(str(valor)) == PRECO_ATUAL


@pytest.mark.postgres
def test_pendentes_so_lista_consumo_pendente_do_hotel(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_pendente = _criar_hospedada(cliente, ambiente, telefone="11987657002")
    id_servico = _criar_hospedada(cliente, ambiente, telefone="11987657003")
    id_lancado = _criar_hospedada(cliente, ambiente, telefone="11987657004")
    id_sol_pendente = _semear_consumo(ambiente, id_pendente, "uma cerveja", "402")
    _semear_servico(ambiente, id_servico)
    id_sol_lancado = _semear_consumo(ambiente, id_lancado, "outra cerveja", None)
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    assert cliente.post(f"/solicitacoes/{id_sol_lancado}/lancamento").status_code == 200
    lista = cliente.get("/consumos/pendentes")
    assert lista.status_code == 200
    ids = [i["id_solicitacao"] for i in lista.json()["itens"]]
    assert id_sol_pendente in ids
    assert id_sol_lancado not in ids
    item = next(i for i in lista.json()["itens"] if i["id_solicitacao"] == id_sol_pendente)
    assert item["status_lancamento"] == "pendente"
    assert Decimal(str(item["valor_praticado"])) == PRECO_ATUAL
    assert "nome" not in item
    assert "telefone" not in item
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    ids_b = [i["id_solicitacao"] for i in cliente.get("/consumos/pendentes").json()["itens"]]
    assert id_sol_pendente not in ids_b


@pytest.mark.postgres
def test_staff_e_gestao_nao_lancam_e_gestao_le_pendentes(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987657005")
    id_sol = _semear_consumo(ambiente, id_reserva, "uma cerveja", None)
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    fila = cliente.get("/solicitacoes").json()["itens"]
    item = next(i for i in fila if i["id_solicitacao"] == id_sol)
    assert Decimal(str(item["valor_praticado"])) == PRECO_ATUAL
    assert "nome" not in item
    assert cliente.post(f"/solicitacoes/{id_sol}/lancamento").status_code == 403
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    assert cliente.get("/consumos/pendentes").status_code == 200
    assert cliente.post(f"/solicitacoes/{id_sol}/lancamento").status_code == 403
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])
    assert cliente.post(f"/solicitacoes/{id_sol}/lancamento").status_code == 404


@pytest.mark.postgres
def test_recepcao_dispensa_e_nao_aparece_como_lancado(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    id_reserva = _criar_hospedada(cliente, ambiente, telefone="11987657006")
    id_sol = _semear_consumo(ambiente, id_reserva, "uma cerveja", None)
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    primeira = cliente.post(f"/solicitacoes/{id_sol}/dispensa")
    assert primeira.status_code == 200
    assert primeira.json()["status_lancamento"] == "dispensado"
    segunda = cliente.post(f"/solicitacoes/{id_sol}/dispensa")
    assert segunda.status_code == 409
    assert segunda.json()["detail"] == DETALHE_JA_DISPENSADO
    ids = [i["id_solicitacao"] for i in cliente.get("/consumos/pendentes").json()["itens"]]
    assert id_sol not in ids
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.post(f"/solicitacoes/{id_sol}/dispensa").status_code == 403
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    assert cliente.post(f"/solicitacoes/{id_sol}/dispensa").status_code == 403
