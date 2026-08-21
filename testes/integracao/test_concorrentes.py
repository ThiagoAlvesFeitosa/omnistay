"""Cadastro de concorrentes: criacao, manutencao, ativos e isolamento."""

from sqlalchemy import text

import pytest

from testes.suporte.concorrentes import (
    DETALHE_FONTE_DUPLICADA,
    DETALHE_NAO_ENCONTRADO,
    NOME,
    URL_FONTE,
)


def _login(cliente, usuario):
    resposta = cliente.post(
        "/sessoes",
        json={"email": usuario.email, "senha": usuario.senha},
    )
    assert resposta.status_code == 201


def _corpo(nome=NOME, url_fonte=URL_FONTE):
    return {"nome": nome, "url_fonte": url_fonte}


@pytest.mark.postgres
def test_gestao_cria_concorrente_ativo(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    gestao = ambiente.propriedade_a.usuarios["gestor"]
    _login(cliente, gestao)

    resposta = cliente.post("/concorrentes", json=_corpo())
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["ativo"] is True
    assert corpo["nome"] == NOME
    assert corpo["url_fonte"] == URL_FONTE
    assert corpo["id_concorrente"]

    with ambiente.conexao() as conexao:
        linha = conexao.execute(
            text(
                "SELECT id_hotel, ativo FROM concorrente "
                "WHERE id_concorrente = :id"
            ),
            {"id": corpo["id_concorrente"]},
        ).mappings().one()
    assert linha["id_hotel"] == gestao.id_hotel
    assert linha["ativo"] is True


@pytest.mark.postgres
def test_url_invalida_e_nome_em_branco_nao_gravam(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])

    assert (
        cliente.post("/concorrentes", json=_corpo(url_fonte="mailto:x@y.com")).status_code
        == 422
    )
    assert cliente.post("/concorrentes", json=_corpo(nome="   ")).status_code == 422

    with ambiente.conexao() as conexao:
        qtd = conexao.execute(text("SELECT COUNT(*) FROM concorrente")).scalar_one()
    assert qtd == 0


@pytest.mark.postgres
def test_fonte_duplicada_responde_409(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    assert cliente.post("/concorrentes", json=_corpo()).status_code == 201

    resposta = cliente.post(
        "/concorrentes", json=_corpo(nome="Outro", url_fonte=URL_FONTE.upper())
    )
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == DETALHE_FONTE_DUPLICADA

    with ambiente.conexao() as conexao:
        qtd = conexao.execute(text("SELECT COUNT(*) FROM concorrente")).scalar_one()
    assert qtd == 1


@pytest.mark.postgres
def test_criar_sem_cookie_responde_401(app_sobre_ambiente):
    cliente, _ambiente = app_sobre_ambiente
    assert cliente.post("/concorrentes", json=_corpo()).status_code == 401


@pytest.mark.postgres
def test_patch_e_manutencao_listam_inativo(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    criado = cliente.post("/concorrentes", json=_corpo()).json()
    id_item = criado["id_concorrente"]

    resposta = cliente.patch(
        f"/concorrentes/{id_item}", json={"nome": "Novo nome", "ativo": False}
    )
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Novo nome"
    assert resposta.json()["ativo"] is False

    lista = cliente.get("/concorrentes")
    assert lista.status_code == 200
    itens = lista.json()["concorrentes"]
    assert len(itens) == 1
    assert itens[0]["ativo"] is False
    assert itens[0]["nome"] == "Novo nome"


@pytest.mark.postgres
def test_delete_nao_e_oferecido(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    id_item = cliente.post("/concorrentes", json=_corpo()).json()["id_concorrente"]

    assert cliente.delete(f"/concorrentes/{id_item}").status_code == 405

    with ambiente.conexao() as conexao:
        qtd = conexao.execute(text("SELECT COUNT(*) FROM concorrente")).scalar_one()
    assert qtd == 1


@pytest.mark.postgres
def test_post_com_url_de_ficha_inativa_responde_409(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    id_item = cliente.post("/concorrentes", json=_corpo()).json()["id_concorrente"]
    cliente.patch(f"/concorrentes/{id_item}", json={"ativo": False})

    resposta = cliente.post("/concorrentes", json=_corpo(nome="Outro"))
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == DETALHE_FONTE_DUPLICADA


@pytest.mark.postgres
def test_ativos_omit_inativo_e_vazio_e_200(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])

    vazio = cliente.get("/concorrentes/ativos")
    assert vazio.status_code == 200
    assert vazio.json() == {"fontes": []}

    id_ativo = cliente.post("/concorrentes", json=_corpo()).json()["id_concorrente"]
    id_inativo = cliente.post(
        "/concorrentes",
        json=_corpo(nome="Inativo", url_fonte="https://www.exemplo.com/inativo"),
    ).json()["id_concorrente"]
    cliente.patch(f"/concorrentes/{id_inativo}", json={"ativo": False})

    resposta = cliente.get("/concorrentes/ativos")
    assert resposta.status_code == 200
    fontes = resposta.json()["fontes"]
    assert [f["id_concorrente"] for f in fontes] == [id_ativo]
    assert "ativo" not in fontes[0]

    with ambiente.conexao() as conexao:
        qtd = conexao.execute(text("SELECT COUNT(*) FROM coleta_mercado")).scalar_one()
    assert qtd == 0


@pytest.mark.postgres
def test_recepcao_e_staff_sao_recusados(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    gestao = ambiente.propriedade_a.usuarios["gestor"]
    _login(cliente, gestao)
    id_item = cliente.post("/concorrentes", json=_corpo()).json()["id_concorrente"]
    cliente.cookies.clear()

    for perfil in ("recepcao", "staff"):
        _login(cliente, ambiente.propriedade_a.usuarios[perfil])
        assert cliente.get("/concorrentes").status_code == 403
        assert cliente.get("/concorrentes/ativos").status_code == 403
        assert cliente.post("/concorrentes", json=_corpo(nome="X")).status_code == 403
        assert (
            cliente.patch(f"/concorrentes/{id_item}", json={"ativo": False}).status_code
            == 403
        )
        cliente.cookies.clear()


@pytest.mark.postgres
def test_hotel_b_nao_ve_nem_altera_a(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    gestao_a = ambiente.propriedade_a.usuarios["gestor"]
    gestao_b = ambiente.propriedade_b.usuarios["gestor"]
    _login(cliente, gestao_a)
    id_a = cliente.post("/concorrentes", json=_corpo()).json()["id_concorrente"]
    cliente.cookies.clear()

    _login(cliente, gestao_b)
    lista = cliente.get("/concorrentes")
    assert lista.status_code == 200
    assert lista.json()["concorrentes"] == []
    recusa = cliente.patch(f"/concorrentes/{id_a}", json={"nome": "Invadir"})
    assert recusa.status_code == 404
    assert recusa.json()["detail"] == DETALHE_NAO_ENCONTRADO
    criado_b = cliente.post("/concorrentes", json=_corpo())
    assert criado_b.status_code == 201
    assert criado_b.json()["id_concorrente"] != id_a


@pytest.mark.postgres
def test_mesmo_nome_urls_distintas_sao_aceitos(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    um = cliente.post("/concorrentes", json=_corpo())
    outro = cliente.post(
        "/concorrentes",
        json=_corpo(url_fonte="https://www.exemplo.com/outra-fonte"),
    )
    assert um.status_code == 201
    assert outro.status_code == 201
    assert um.json()["id_concorrente"] != outro.json()["id_concorrente"]
