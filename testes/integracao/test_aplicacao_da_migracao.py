"""A migracao leva um banco vazio ao esquema atual, de forma atomica e repetivel."""

import pytest
from sqlalchemy import create_engine, text

from testes.suporte.banco_descartavel import banco_vazio
from testes.suporte.migracao import (
    SQL_DA_REVISAO_INICIAL,
    aplicar_migracoes,
    revisao_registrada,
)

TABELAS_ESPERADAS = {
    "hotel",
    "usuario",
    "parametro_hotel",
    "catalogo_item",
    "hospede",
    "reserva",
    "reserva_hospede",
    "consentimento",
    "mensagem",
    "evento_webhook",
    "solicitacao",
    "consumo",
    "avaliacao",
    "concorrente",
    "coleta_mercado",
}


def tabelas_de(url_do_banco: str) -> set[str]:
    engine = create_engine(url_do_banco)
    try:
        with engine.connect() as conexao:
            linhas = conexao.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                )
            ).fetchall()
        return {linha[0] for linha in linhas}
    finally:
        engine.dispose()


@pytest.mark.postgres
def test_banco_vazio_chega_ao_esquema_atual():
    with banco_vazio() as url:
        aplicar_migracoes(url)

        assert TABELAS_ESPERADAS <= tabelas_de(url)


@pytest.mark.postgres
def test_visao_de_apoio_passa_a_existir():
    with banco_vazio() as url:
        aplicar_migracoes(url)

        engine = create_engine(url)
        try:
            with engine.connect() as conexao:
                existe = conexao.execute(
                    text("SELECT to_regclass('public.vw_fila_do_dia') IS NOT NULL")
                ).scalar()
        finally:
            engine.dispose()

        assert existe is True


@pytest.mark.postgres
def test_reaplicacao_nao_altera_nada():
    with banco_vazio() as url:
        aplicar_migracoes(url)
        tabelas_apos_primeira = tabelas_de(url)

        aplicar_migracoes(url)

        assert tabelas_de(url) == tabelas_apos_primeira


@pytest.mark.postgres
def test_falha_no_meio_da_aplicacao_nao_deixa_estrutura():
    sql_com_erro = SQL_DA_REVISAO_INICIAL + "\nCREATE TABLE ;\n"

    with banco_vazio() as url:
        engine = create_engine(url)
        try:
            from testes.suporte.inventario import aplicar_sql

            with pytest.raises(Exception):
                aplicar_sql(engine, sql_com_erro)
        finally:
            engine.dispose()

        assert tabelas_de(url) == set()


@pytest.mark.postgres
def test_banco_vazio_nao_tem_versao_registrada():
    with banco_vazio() as url:
        assert revisao_registrada(url) is None


@pytest.mark.postgres
def test_banco_migrado_informa_a_revisao_corrente():
    with banco_vazio() as url:
        aplicar_migracoes(url)

        assert revisao_registrada(url) is not None
