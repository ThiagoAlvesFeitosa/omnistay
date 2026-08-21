"""Coleta agendada de mercado: ciclo, historico, isolamento e inativo."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from app.adaptadores.fonte_falsa import FonteFalsa
from app.adaptadores.mensageria_falsa import MensageriaFalsa
from testes.suporte.coleta_mercado import (
    CHAVE_PERIODICIDADE,
    NOTA_FIXTURE,
    PRECO_FIXTURE,
    URL_FONTE,
)
from worker.agendador import verificar_coletas_mercado
from worker.consumidor import processar_uma_passagem

AGORA = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)
URL_B = "https://www.outro-exemplo.com/hotel"


def _inserir_concorrente(conexao, id_hotel, *, url=URL_FONTE, ativo=True):
    return conexao.execute(
        text(
            "INSERT INTO concorrente (id_hotel, nome, url_fonte, ativo) "
            "VALUES (:h, 'Hotel Vizinho', :url, :ativo) "
            "RETURNING id_concorrente"
        ),
        {"h": id_hotel, "url": url, "ativo": ativo},
    ).scalar_one()


def _coletas(conexao, id_concorrente):
    return conexao.execute(
        text(
            "SELECT id_coleta, preco, nota_media, sucesso, coletado_em "
            "FROM coleta_mercado WHERE id_concorrente = :id "
            "ORDER BY id_coleta"
        ),
        {"id": id_concorrente},
    ).mappings().all()


def _status_trabalho(conexao):
    return conexao.execute(
        text("SELECT status FROM trabalho WHERE tipo = 'coletar_mercado'")
    ).scalars().all()


@pytest.mark.postgres
def test_fonte_ativa_devida_gera_coleta_de_sucesso(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_concorrente = _inserir_concorrente(conexao, id_hotel)
        n = verificar_coletas_mercado(conexao, agora=AGORA)
        assert n == 1
        processados = processar_uma_passagem(
            conexao, gateway=MensageriaFalsa(), fonte=FonteFalsa()
        )
        assert processados == 1
        linhas = _coletas(conexao, id_concorrente)
        assert len(linhas) == 1
        assert linhas[0]["sucesso"] is True
        assert linhas[0]["preco"] == PRECO_FIXTURE
        assert linhas[0]["nota_media"] == NOTA_FIXTURE
        assert _status_trabalho(conexao) == ["concluido"]


@pytest.mark.postgres
def test_segundo_ciclo_insere_linha_nova_sem_alterar_a_primeira(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_concorrente = _inserir_concorrente(conexao, id_hotel)
        verificar_coletas_mercado(conexao, agora=AGORA)
        processar_uma_passagem(
            conexao, gateway=MensageriaFalsa(), fonte=FonteFalsa()
        )
        primeira = dict(_coletas(conexao, id_concorrente)[0])
        depois = primeira["coletado_em"] + timedelta(hours=24)

    with ambiente.engine.begin() as conexao:
        n = verificar_coletas_mercado(conexao, agora=depois)
        assert n == 1
        processar_uma_passagem(
            conexao, gateway=MensageriaFalsa(), fonte=FonteFalsa()
        )
        linhas = _coletas(conexao, id_concorrente)
        assert len(linhas) == 2
        assert linhas[0]["id_coleta"] == primeira["id_coleta"]
        assert linhas[0]["preco"] == primeira["preco"]
        assert linhas[0]["sucesso"] == primeira["sucesso"]


@pytest.mark.postgres
def test_fonte_inativa_nao_enfileira(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        _inserir_concorrente(conexao, id_hotel, ativo=False)
        n = verificar_coletas_mercado(conexao, agora=AGORA)
        assert n == 0
        qtd = conexao.execute(text("SELECT COUNT(*) FROM trabalho")).scalar_one()
        assert qtd == 0


@pytest.mark.postgres
def test_falha_nao_reescreve_coleta_anterior(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_concorrente = _inserir_concorrente(conexao, id_hotel)
        verificar_coletas_mercado(conexao, agora=AGORA)
        processar_uma_passagem(
            conexao, gateway=MensageriaFalsa(), fonte=FonteFalsa()
        )
        primeira = dict(_coletas(conexao, id_concorrente)[0])
        depois = primeira["coletado_em"] + timedelta(hours=24)

    with ambiente.engine.begin() as conexao:
        verificar_coletas_mercado(conexao, agora=depois)
        fonte = FonteFalsa()
        from app.portas.fonte_publica import DESFECHO_SEM_DADO, ResultadoPublico

        fonte.configurar(
            URL_FONTE, resultado=ResultadoPublico(desfecho=DESFECHO_SEM_DADO)
        )
        processar_uma_passagem(
            conexao, gateway=MensageriaFalsa(), fonte=fonte
        )
        linhas = _coletas(conexao, id_concorrente)
        assert len(linhas) == 2
        assert linhas[0]["sucesso"] is True
        assert linhas[0]["preco"] == primeira["preco"]
        assert linhas[1]["sucesso"] is False
        assert linhas[1]["preco"] is None
        assert "falha" not in _status_trabalho(conexao)


@pytest.mark.postgres
def test_isolamento_entre_hoteis(ambiente):
    hotel_a = ambiente.propriedade_a.id_hotel
    hotel_b = ambiente.propriedade_b.id_hotel
    with ambiente.engine.begin() as conexao:
        conexao.execute(
            text(
                "UPDATE parametro_hotel SET valor = '12' "
                "WHERE id_hotel = :h AND chave = :c"
            ),
            {"h": hotel_a, "c": CHAVE_PERIODICIDADE},
        )
        conexao.execute(
            text(
                "UPDATE parametro_hotel SET valor = '48' "
                "WHERE id_hotel = :h AND chave = :c"
            ),
            {"h": hotel_b, "c": CHAVE_PERIODICIDADE},
        )
        id_a = _inserir_concorrente(conexao, hotel_a)
        id_b = _inserir_concorrente(conexao, hotel_b, url=URL_B)
        verificar_coletas_mercado(conexao, agora=AGORA)
        processar_uma_passagem(
            conexao, gateway=MensageriaFalsa(), fonte=FonteFalsa()
        )
        primeira_a = dict(_coletas(conexao, id_a)[0])
        meio = primeira_a["coletado_em"] + timedelta(hours=13)

    with ambiente.engine.begin() as conexao:
        n = verificar_coletas_mercado(conexao, agora=meio)
        assert n == 1
        processar_uma_passagem(
            conexao, gateway=MensageriaFalsa(), fonte=FonteFalsa()
        )
        assert len(_coletas(conexao, id_a)) == 2
        assert len(_coletas(conexao, id_b)) == 1


@pytest.mark.postgres
def test_processador_nao_altera_item_vendavel(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        antes = conexao.execute(
            text("SELECT COUNT(*) FROM item_vendavel")
        ).scalar_one()
        _inserir_concorrente(conexao, id_hotel)
        verificar_coletas_mercado(conexao, agora=AGORA)
        processar_uma_passagem(
            conexao, gateway=MensageriaFalsa(), fonte=FonteFalsa()
        )
        depois = conexao.execute(
            text("SELECT COUNT(*) FROM item_vendavel")
        ).scalar_one()
        assert depois == antes
