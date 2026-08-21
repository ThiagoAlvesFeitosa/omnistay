"""Painel de mercado: visao atual, historico, perfis e isolamento."""

from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.comum import relogio
from testes.suporte.coleta_mercado import (
    CHAVE_PERIODICIDADE,
    NOTA_FIXTURE,
    PRECO_FIXTURE,
    SITUACAO_ATUAL,
    SITUACAO_CADENCIA_AUSENTE,
    SITUACAO_DESATUALIZADO,
)
from testes.suporte.concorrentes import NOME, URL_FONTE
from testes.suporte.painel_mercado import gravar_coleta

URL_B = "https://www.outro-exemplo.com/hotel"


def _login(cliente, usuario):
    resposta = cliente.post(
        "/sessoes",
        json={"email": usuario.email, "senha": usuario.senha},
    )
    assert resposta.status_code == 201


def _inserir_concorrente(conexao, id_hotel, *, url=URL_FONTE, ativo=True, nome=NOME):
    return conexao.execute(
        text(
            "INSERT INTO concorrente (id_hotel, nome, url_fonte, ativo) "
            "VALUES (:h, :nome, :url, :ativo) RETURNING id_concorrente"
        ),
        {"h": id_hotel, "nome": nome, "url": url, "ativo": ativo},
    ).scalar_one()


def _preco(valor) -> Decimal:
    return Decimal(str(valor))


@pytest.mark.postgres
def test_gestao_ve_sucesso_datado_e_lista_vazia(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    gestao = ambiente.propriedade_a.usuarios["gestor"]
    _login(cliente, gestao)

    vazio = cliente.get("/mercado")
    assert vazio.status_code == 200
    corpo_vazio = vazio.json()
    assert corpo_vazio["concorrentes"] == []
    assert corpo_vazio["periodicidade_horas"] == 24

    coletado_em = relogio.agora() - timedelta(hours=1)
    with ambiente.engine.begin() as conexao:
        id_concorrente = _inserir_concorrente(conexao, ambiente.propriedade_a.id_hotel)
        gravar_coleta(
            conexao,
            id_concorrente,
            sucesso=True,
            preco=PRECO_FIXTURE,
            nota_media=NOTA_FIXTURE,
            coletado_em=coletado_em,
        )

    resposta = cliente.get("/mercado")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["periodicidade_horas"] == 24
    assert len(corpo["concorrentes"]) == 1
    item = corpo["concorrentes"][0]
    assert item["id_concorrente"] == id_concorrente
    assert item["nome"] == NOME
    assert item["situacao"] == SITUACAO_ATUAL
    assert _preco(item["ultimo_sucesso"]["preco"]) == PRECO_FIXTURE
    assert _preco(item["ultimo_sucesso"]["nota_media"]) == NOTA_FIXTURE
    assert item["ultimo_sucesso"]["coletado_em"]
    assert item["ultima_falha"] is None
    assert "url_fonte" not in item


@pytest.mark.postgres
def test_dado_velho_e_falha_posterior_nao_se_disfarcam(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    agora = relogio.agora()
    with ambiente.engine.begin() as conexao:
        id_velho = _inserir_concorrente(
            conexao, ambiente.propriedade_a.id_hotel, nome="Velho"
        )
        sucesso_velho = gravar_coleta(
            conexao,
            id_velho,
            sucesso=True,
            preco=PRECO_FIXTURE,
            nota_media=NOTA_FIXTURE,
            coletado_em=agora - timedelta(hours=48),
        )
        id_falha = _inserir_concorrente(
            conexao,
            ambiente.propriedade_a.id_hotel,
            url=URL_B,
            nome="Com falha",
        )
        sucesso_antigo = gravar_coleta(
            conexao,
            id_falha,
            sucesso=True,
            preco=PRECO_FIXTURE,
            nota_media=NOTA_FIXTURE,
            coletado_em=agora - timedelta(hours=2),
        )
        falha = gravar_coleta(
            conexao,
            id_falha,
            sucesso=False,
            preco=None,
            nota_media=None,
            coletado_em=agora - timedelta(minutes=10),
        )

    corpo = cliente.get("/mercado").json()
    por_id = {item["id_concorrente"]: item for item in corpo["concorrentes"]}
    velho = por_id[id_velho]
    assert velho["situacao"] == SITUACAO_DESATUALIZADO
    assert velho["ultimo_sucesso"]["coletado_em"]
    com_falha = por_id[id_falha]
    assert com_falha["situacao"] == SITUACAO_DESATUALIZADO
    assert _preco(com_falha["ultimo_sucesso"]["preco"]) == PRECO_FIXTURE
    assert com_falha["ultima_falha"]["coletado_em"]
    assert sucesso_velho["coletado_em"]
    assert sucesso_antigo["id_coleta"] != falha["id_coleta"]


@pytest.mark.postgres
def test_cadencia_ausente_nao_marca_atual(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    with ambiente.engine.begin() as conexao:
        id_concorrente = _inserir_concorrente(conexao, ambiente.propriedade_a.id_hotel)
        gravar_coleta(
            conexao,
            id_concorrente,
            sucesso=True,
            preco=PRECO_FIXTURE,
            nota_media=NOTA_FIXTURE,
            coletado_em=relogio.agora() - timedelta(hours=1),
        )
        conexao.execute(
            text(
                "DELETE FROM parametro_hotel"
                " WHERE id_hotel = :h AND chave = :chave"
            ),
            {"h": ambiente.propriedade_a.id_hotel, "chave": CHAVE_PERIODICIDADE},
        )

    corpo = cliente.get("/mercado").json()
    assert corpo["periodicidade_horas"] is None
    assert corpo["concorrentes"][0]["situacao"] == SITUACAO_CADENCIA_AUSENTE
    assert _preco(corpo["concorrentes"][0]["ultimo_sucesso"]["preco"]) == PRECO_FIXTURE


@pytest.mark.postgres
def test_historico_mostra_serie_e_isola_hotel(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    agora = relogio.agora()
    with ambiente.engine.begin() as conexao:
        id_a = _inserir_concorrente(conexao, ambiente.propriedade_a.id_hotel)
        gravar_coleta(
            conexao,
            id_a,
            sucesso=True,
            preco=Decimal("140.00"),
            nota_media=NOTA_FIXTURE,
            coletado_em=agora - timedelta(days=2),
        )
        gravar_coleta(
            conexao,
            id_a,
            sucesso=False,
            preco=None,
            nota_media=None,
            coletado_em=agora - timedelta(days=1),
        )
        gravar_coleta(
            conexao,
            id_a,
            sucesso=True,
            preco=PRECO_FIXTURE,
            nota_media=NOTA_FIXTURE,
            coletado_em=agora - timedelta(hours=1),
        )
        id_inativo = _inserir_concorrente(
            conexao,
            ambiente.propriedade_a.id_hotel,
            url=URL_B,
            ativo=False,
            nome="Inativo",
        )
        gravar_coleta(
            conexao,
            id_inativo,
            sucesso=True,
            preco=PRECO_FIXTURE,
            nota_media=None,
            coletado_em=agora - timedelta(hours=2),
        )
        id_b = _inserir_concorrente(conexao, ambiente.propriedade_b.id_hotel)
        gravar_coleta(
            conexao,
            id_b,
            sucesso=True,
            preco=PRECO_FIXTURE,
            nota_media=NOTA_FIXTURE,
            coletado_em=agora - timedelta(hours=1),
        )
        id_vazio = _inserir_concorrente(
            conexao,
            ambiente.propriedade_a.id_hotel,
            url="https://www.exemplo.com/vazio",
            nome="Sem coleta",
        )

    historico = cliente.get(f"/mercado/concorrentes/{id_a}")
    assert historico.status_code == 200
    coletas = historico.json()["coletas"]
    assert len(coletas) == 3
    assert coletas[0]["sucesso"] is True
    assert coletas[1]["sucesso"] is False
    assert coletas[1]["preco"] is None
    assert _preco(coletas[2]["preco"]) == PRECO_FIXTURE

    inativo = cliente.get(f"/mercado/concorrentes/{id_inativo}")
    assert inativo.status_code == 200
    assert inativo.json()["ativo"] is False
    assert len(inativo.json()["coletas"]) == 1

    vazio = cliente.get(f"/mercado/concorrentes/{id_vazio}")
    assert vazio.status_code == 200
    assert vazio.json()["coletas"] == []

    alheio = cliente.get(f"/mercado/concorrentes/{id_b}")
    assert alheio.status_code == 404


@pytest.mark.postgres
def test_recepcao_e_staff_nao_leem_painel(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    with ambiente.engine.begin() as conexao:
        id_concorrente = _inserir_concorrente(
            conexao, ambiente.propriedade_a.id_hotel
        )
    for perfil in ("recepcao", "staff"):
        cliente.cookies.clear()
        _login(cliente, ambiente.propriedade_a.usuarios[perfil])
        assert cliente.get("/mercado").status_code == 403
        assert (
            cliente.get(f"/mercado/concorrentes/{id_concorrente}").status_code
            == 403
        )


@pytest.mark.postgres
def test_hotel_b_nao_ve_concorrentes_de_a(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    with ambiente.engine.begin() as conexao:
        id_a = _inserir_concorrente(conexao, ambiente.propriedade_a.id_hotel)
        gravar_coleta(
            conexao,
            id_a,
            sucesso=True,
            preco=PRECO_FIXTURE,
            nota_media=NOTA_FIXTURE,
            coletado_em=relogio.agora(),
        )
    _login(cliente, ambiente.propriedade_b.usuarios["gestor"])
    lista = cliente.get("/mercado")
    assert lista.status_code == 200
    assert lista.json()["concorrentes"] == []
    assert cliente.get(f"/mercado/concorrentes/{id_a}").status_code == 404


@pytest.mark.postgres
def test_escrita_e_coleta_nao_existem_no_painel(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    with ambiente.engine.begin() as conexao:
        id_concorrente = _inserir_concorrente(
            conexao, ambiente.propriedade_a.id_hotel
        )
        antes_coletas = conexao.execute(
            text("SELECT COUNT(*) FROM coleta_mercado")
        ).scalar_one()
        antes_trabalhos = conexao.execute(
            text(
                "SELECT COUNT(*) FROM trabalho WHERE tipo = 'coletar_mercado'"
            )
        ).scalar_one()

    assert cliente.post("/mercado").status_code == 405
    assert cliente.patch("/mercado").status_code == 405
    assert cliente.put("/mercado").status_code == 405
    assert cliente.delete("/mercado").status_code == 405
    assert cliente.post(f"/mercado/concorrentes/{id_concorrente}").status_code == 405
    assert cliente.patch(f"/mercado/concorrentes/{id_concorrente}").status_code == 405
    assert cliente.delete(f"/mercado/concorrentes/{id_concorrente}").status_code == 405

    assert cliente.get("/mercado").status_code == 200
    with ambiente.engine.begin() as conexao:
        depois_coletas = conexao.execute(
            text("SELECT COUNT(*) FROM coleta_mercado")
        ).scalar_one()
        depois_trabalhos = conexao.execute(
            text(
                "SELECT COUNT(*) FROM trabalho WHERE tipo = 'coletar_mercado'"
            )
        ).scalar_one()
    assert depois_coletas == antes_coletas
    assert depois_trabalhos == antes_trabalhos


@pytest.mark.postgres
def test_inativo_aparece_na_visao_atual(app_sobre_ambiente):
    cliente, ambiente = app_sobre_ambiente
    _login(cliente, ambiente.propriedade_a.usuarios["gestor"])
    with ambiente.engine.begin() as conexao:
        id_inativo = _inserir_concorrente(
            conexao,
            ambiente.propriedade_a.id_hotel,
            ativo=False,
            nome="Fora do radar",
        )
        gravar_coleta(
            conexao,
            id_inativo,
            sucesso=True,
            preco=PRECO_FIXTURE,
            nota_media=NOTA_FIXTURE,
            coletado_em=relogio.agora() - timedelta(hours=1),
        )
    corpo = cliente.get("/mercado").json()
    assert len(corpo["concorrentes"]) == 1
    item = corpo["concorrentes"][0]
    assert item["id_concorrente"] == id_inativo
    assert item["ativo"] is False
    assert _preco(item["ultimo_sucesso"]["preco"]) == PRECO_FIXTURE


@pytest.mark.postgres
def test_mercado_sem_cookie_responde_401(app_sobre_ambiente):
    cliente, _ambiente = app_sobre_ambiente
    resposta = cliente.get("/mercado")
    assert resposta.status_code == 401
