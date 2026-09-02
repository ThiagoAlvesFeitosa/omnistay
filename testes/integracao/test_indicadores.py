"""GET /indicadores: quatro numeros, sem lista, staff recusado."""

from decimal import Decimal

import pytest
from sqlalchemy import text

from testes.integracao.test_reservas import _corpo_valido, _login
from testes.integracao.test_confirmar_chegada import _tornar


CAMPOS = {
    "chegadas_hoje",
    "hospedados",
    "chamados_abertos",
    "consumo_a_lancar",
}

PROIBIDOS = {
    "itens",
    "nome",
    "telefone",
    "id_reserva",
    "id_solicitacao",
    "id_hospede",
}


@pytest.mark.postgres
def test_gestao_le_quatro_zeros_sem_lista_nem_dado_de_hospede(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])

    resposta = cliente.get("/indicadores")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert set(corpo.keys()) == CAMPOS
    assert corpo["chegadas_hoje"] == 0
    assert corpo["hospedados"] == 0
    assert corpo["chamados_abertos"] == 0
    assert Decimal(str(corpo["consumo_a_lancar"])) == Decimal("0")
    for chave in PROIBIDOS:
        assert chave not in corpo
    texto = str(corpo)
    assert "Marina" not in texto
    assert "5511" not in texto


@pytest.mark.postgres
def test_staff_e_recusado_e_chegadas_do_dia_permanece(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.get("/indicadores").status_code == 403

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    chegadas = cliente.get("/indicadores/chegadas-do-dia")
    assert chegadas.status_code == 200
    assert chegadas.json() == {"quantidade": 0}


@pytest.mark.postgres
def test_recorte_de_hospedado_chamado_e_soma_pendente(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    recepcao = ambiente.propriedade_a.usuarios["recepcao"]
    _login(cliente, recepcao)
    id_reserva = cliente.post("/reservas", json=_corpo_valido()).json()["id_reserva"]
    _tornar(ambiente, id_reserva, "ficha_recebida")
    _tornar(ambiente, id_reserva, "hospedado")

    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "INSERT INTO solicitacao (id_reserva, tipo, descricao, status)"
                " VALUES (:id, 'reclamacao', 'barulho', 'aberta')"
            ),
            {"id": id_reserva},
        )
        conexao.execute(
            text(
                "INSERT INTO solicitacao (id_reserva, tipo, descricao, status)"
                " VALUES (:id, 'servico', 'toalha', 'em_andamento')"
            ),
            {"id": id_reserva},
        )
        id_consumo = conexao.execute(
            text(
                "INSERT INTO solicitacao (id_reserva, tipo, descricao, status)"
                " VALUES (:id, 'consumo', 'minibar', 'aberta')"
                " RETURNING id_solicitacao"
            ),
            {"id": id_reserva},
        ).scalar_one()
        conexao.execute(
            text(
                "INSERT INTO consumo (id_solicitacao, descricao_item, valor_praticado)"
                " VALUES (:id, 'minibar', 10.00)"
            ),
            {"id": id_consumo},
        )
        id_segundo = conexao.execute(
            text(
                "INSERT INTO solicitacao (id_reserva, tipo, descricao, status)"
                " VALUES (:id, 'consumo', 'lanche', 'aberta')"
                " RETURNING id_solicitacao"
            ),
            {"id": id_reserva},
        ).scalar_one()
        conexao.execute(
            text(
                "INSERT INTO consumo (id_solicitacao, descricao_item, valor_praticado)"
                " VALUES (:id, 'lanche', 20.00)"
            ),
            {"id": id_segundo},
        )
        conexao.execute(
            text(
                "INSERT INTO solicitacao (id_reserva, tipo, descricao, status)"
                " VALUES (:id, 'reclamacao', 'resolvida', 'cancelada')"
            ),
            {"id": id_reserva},
        )

    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    corpo = cliente.get("/indicadores").json()
    assert corpo["hospedados"] == 1
    assert corpo["chamados_abertos"] == 2
    assert Decimal(str(corpo["consumo_a_lancar"])) == Decimal("30.00")
    assert "itens" not in corpo
    assert "id_reserva" not in corpo
    assert "barulho" not in str(corpo)
