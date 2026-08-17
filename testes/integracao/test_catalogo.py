"""Catalogo da propriedade: criacao, manutencao, ativo e isolamento."""

from sqlalchemy import text

import pytest


def _login(cliente, usuario):
    resposta = cliente.post(
        "/sessoes",
        json={"email": usuario.email, "senha": usuario.senha},
    )
    assert resposta.status_code == 201


def _corpo(categoria="horario", titulo="Cafe da manha", conteudo="7h as 10h"):
    return {"categoria": categoria, "titulo": titulo, "conteudo": conteudo}


@pytest.mark.postgres
def test_recepcao_cria_item_ativo(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    recepcao = ambiente.propriedade_a.usuarios["recepcao"]
    _login(cliente, recepcao)

    resposta = cliente.post("/catalogo", json=_corpo())
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["ativo"] is True
    assert corpo["categoria"] == "horario"
    assert corpo["titulo"] == "Cafe da manha"
    assert corpo["id_catalogo_item"]

    with ambiente.conexao() as conexao:
        linha = conexao.execute(
            text(
                "SELECT id_hotel, ativo FROM catalogo_item "
                "WHERE id_catalogo_item = :id"
            ),
            {"id": corpo["id_catalogo_item"]},
        ).mappings().one()
    assert linha["id_hotel"] == recepcao.id_hotel
    assert linha["ativo"] is True


@pytest.mark.postgres
def test_categoria_invalida_e_titulo_em_branco_nao_gravam(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])

    assert (
        cliente.post("/catalogo", json=_corpo(categoria="spa")).status_code
        == 422
    )
    assert cliente.post("/catalogo", json=_corpo(titulo="   ")).status_code == 422

    with ambiente.conexao() as conexao:
        qtd = conexao.execute(text("SELECT COUNT(*) FROM catalogo_item")).scalar_one()
    assert qtd == 0


@pytest.mark.postgres
def test_criar_sem_cookie_responde_401(app_sobre_ambiente):
    cliente, _ambiente = app_sobre_ambiente
    assert cliente.post("/catalogo", json=_corpo()).status_code == 401


@pytest.mark.postgres
def test_patch_e_manutencao_listam_inativo(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    criado = cliente.post("/catalogo", json=_corpo()).json()
    id_item = criado["id_catalogo_item"]

    resposta = cliente.patch(
        f"/catalogo/{id_item}", json={"titulo": "Novo horario", "ativo": False}
    )
    assert resposta.status_code == 200
    assert resposta.json()["titulo"] == "Novo horario"
    assert resposta.json()["ativo"] is False

    lista = cliente.get("/catalogo")
    assert lista.status_code == 200
    itens = lista.json()["itens"]
    assert len(itens) == 1
    assert itens[0]["ativo"] is False
    assert itens[0]["titulo"] == "Novo horario"


@pytest.mark.postgres
def test_delete_nao_e_oferecido(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_item = cliente.post("/catalogo", json=_corpo()).json()["id_catalogo_item"]

    assert cliente.delete(f"/catalogo/{id_item}").status_code == 405

    with ambiente.conexao() as conexao:
        qtd = conexao.execute(text("SELECT COUNT(*) FROM catalogo_item")).scalar_one()
    assert qtd == 1


@pytest.mark.postgres
def test_catalogo_ativo_omite_inativo_e_agrupa(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    ids = {}
    for categoria in ("horario", "cardapio", "servico", "programacao", "regra"):
        ids[categoria] = cliente.post(
            "/catalogo", json=_corpo(categoria=categoria, titulo=categoria)
        ).json()["id_catalogo_item"]
    inativo = cliente.post(
        "/catalogo", json=_corpo(categoria="horario", titulo="Antigo")
    ).json()["id_catalogo_item"]
    cliente.patch(f"/catalogo/{inativo}", json={"ativo": False})

    resposta = cliente.get("/catalogo/ativo")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert set(corpo) == {"horario", "cardapio", "servico", "programacao", "regra"}
    ids_horario = [i["id_catalogo_item"] for i in corpo["horario"]]
    assert ids["horario"] in ids_horario
    assert inativo not in ids_horario
    assert "ativo" not in corpo["horario"][0]
    assert corpo["cardapio"][0]["id_catalogo_item"] == ids["cardapio"]

    from app.adaptadores.catalogo_banco import CatalogoBanco
    from app.modulos.propriedade import repository as repo

    with ambiente.conexao() as conexao:
        porta = CatalogoBanco(conexao)
        via_porta = {
            item.id_catalogo_item for item in porta.listar_ativos(ambiente.propriedade_a.id_hotel)
        }
        via_repo = {
            linha["id_catalogo_item"]
            for linha in repo.listar_ativos(
                conexao, id_hotel=ambiente.propriedade_a.id_hotel
            )
        }
    assert via_porta == via_repo
    assert inativo not in via_porta


@pytest.mark.postgres
def test_gestor_le_e_nao_altera(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_item = cliente.post("/catalogo", json=_corpo()).json()["id_catalogo_item"]
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])

    assert cliente.get("/catalogo").status_code == 200
    assert cliente.get("/catalogo/ativo").status_code == 200
    assert cliente.post("/catalogo", json=_corpo(titulo="Outro")).status_code == 403
    assert cliente.patch(f"/catalogo/{id_item}", json={"ativo": False}).status_code == 403


@pytest.mark.postgres
def test_staff_nao_le_nem_altera(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["staff"])
    assert cliente.get("/catalogo").status_code == 403
    assert cliente.get("/catalogo/ativo").status_code == 403
    assert cliente.post("/catalogo", json=_corpo()).status_code == 403


@pytest.mark.postgres
def test_catalogo_isola_hoteis(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    id_a = cliente.post("/catalogo", json=_corpo(titulo="Do hotel A")).json()[
        "id_catalogo_item"
    ]
    cliente.cookies.clear()
    _login(cliente, ambiente.propriedade_b.usuarios["recepcao"])

    lista = cliente.get("/catalogo").json()["itens"]
    assert all(item["id_catalogo_item"] != id_a for item in lista)
    ativo = cliente.get("/catalogo/ativo").json()
    ids_ativos = [
        item["id_catalogo_item"]
        for grupo in ativo.values()
        for item in grupo
    ]
    assert id_a not in ids_ativos
    assert cliente.patch(f"/catalogo/{id_a}", json={"titulo": "Invadir"}).status_code == 404


@pytest.mark.postgres
def test_titulo_duplicado_na_mesma_categoria_e_permitido(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["recepcao"])
    primeiro = cliente.post("/catalogo", json=_corpo(titulo="Cafe da manha"))
    segundo = cliente.post("/catalogo", json=_corpo(titulo="Cafe da manha"))
    assert primeiro.status_code == 201
    assert segundo.status_code == 201
    assert primeiro.json()["id_catalogo_item"] != segundo.json()["id_catalogo_item"]
