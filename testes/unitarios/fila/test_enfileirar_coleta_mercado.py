"""Enfileira coleta de mercado sem consumir."""

import pytest
from sqlalchemy import text

from app.fila import repository as fila_repo
from app.fila import service as fila_service


@pytest.mark.postgres
def test_enfileirar_coletar_mercado_grava_tipo_e_id_sem_url(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_concorrente = conexao.execute(
            text(
                "INSERT INTO concorrente (id_hotel, nome, url_fonte) "
                "VALUES (:h, 'Hotel Vizinho', 'https://www.exemplo.com/hotel') "
                "RETURNING id_concorrente"
            ),
            {"h": id_hotel},
        ).scalar_one()
        id_trabalho = fila_service.enfileirar_coletar_mercado(
            conexao,
            id_hotel=id_hotel,
            id_concorrente=id_concorrente,
        )
        linha = conexao.execute(
            text(
                "SELECT tipo, payload, id_hotel FROM trabalho "
                "WHERE id_trabalho = :id"
            ),
            {"id": id_trabalho},
        ).mappings().one()
        assert linha["tipo"] == "coletar_mercado"
        assert linha["id_hotel"] == id_hotel
        assert linha["payload"] == {"id_concorrente": id_concorrente}
        assert "url" not in linha["payload"]
        assert "url_fonte" not in linha["payload"]
        assert "preco" not in linha["payload"]
        assert "coletar_mercado" in fila_repo.TIPOS_CONSUMIVEIS


@pytest.mark.postgres
def test_enfileirar_coletar_mercado_aberto_duplicado_e_ignorado(ambiente):
    id_hotel = ambiente.propriedade_a.id_hotel
    with ambiente.engine.begin() as conexao:
        id_concorrente = conexao.execute(
            text(
                "INSERT INTO concorrente (id_hotel, nome, url_fonte) "
                "VALUES (:h, 'Hotel Vizinho', 'https://www.exemplo.com/hotel') "
                "RETURNING id_concorrente"
            ),
            {"h": id_hotel},
        ).scalar_one()
        primeiro = fila_service.enfileirar_coletar_mercado(
            conexao, id_hotel=id_hotel, id_concorrente=id_concorrente
        )
        segundo = fila_service.enfileirar_coletar_mercado(
            conexao, id_hotel=id_hotel, id_concorrente=id_concorrente
        )
        assert primeiro
        assert segundo is None
        qtd = conexao.execute(
            text("SELECT COUNT(*) FROM trabalho WHERE tipo = 'coletar_mercado'")
        ).scalar_one()
        assert qtd == 1
