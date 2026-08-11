"""Documento de referencia e banco migrado nao podem divergir.

A comparacao acontece entre dois bancos limpos: um recebe todas as migracoes, o outro
recebe `docs/04-schema.sql`. Comparar inventarios extraidos do catalogo, e nao texto de
SQL, evita falhar por indentacao ou por normalizacao de expressao.
"""

import pytest

from testes.suporte.banco_descartavel import banco_vazio
from testes.suporte.inventario import diferencas, extrair_inventario, faltando
from testes.suporte.migracao import SQL_DO_DOCUMENTO, aplicar_migracoes


@pytest.fixture
def inventarios():
    with banco_vazio() as url_migrado, banco_vazio() as url_referencia:
        aplicar_migracoes(url_migrado)
        migrado = extrair_inventario(url_migrado)
        referencia = extrair_inventario(url_referencia, sql_inicial=SQL_DO_DOCUMENTO)
        yield referencia, migrado


@pytest.mark.postgres
def test_nenhuma_estrutura_do_documento_falta_no_banco_migrado(inventarios):
    referencia, migrado = inventarios

    assert faltando(referencia, migrado) == []


@pytest.mark.postgres
def test_banco_migrado_e_documento_nao_divergem(inventarios):
    referencia, migrado = inventarios

    assert diferencas(referencia, migrado) == []


@pytest.mark.postgres
def test_alteracao_do_documento_sem_migracao_e_apontada():
    documento_alterado = SQL_DO_DOCUMENTO + (
        "\nALTER TABLE reserva ADD COLUMN numero_quarto VARCHAR(10);\n"
    )

    with banco_vazio() as url_migrado, banco_vazio() as url_referencia:
        aplicar_migracoes(url_migrado)
        migrado = extrair_inventario(url_migrado)
        referencia = extrair_inventario(url_referencia, sql_inicial=documento_alterado)

        assert any("numero_quarto" in linha for linha in diferencas(referencia, migrado))


@pytest.mark.postgres
def test_alteracao_na_maquina_de_estados_sem_migracao_e_apontada():
    """O caso mais perigoso: mudar o corpo da funcao sem mudar nome nem assinatura."""
    documento_alterado = SQL_DO_DOCUMENTO + """
CREATE OR REPLACE FUNCTION fn_valida_transicao_reserva()
RETURNS TRIGGER AS $$
BEGIN
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

    with banco_vazio() as url_migrado, banco_vazio() as url_referencia:
        aplicar_migracoes(url_migrado)
        migrado = extrair_inventario(url_migrado)
        referencia = extrair_inventario(url_referencia, sql_inicial=documento_alterado)

        assert any(
            "fn_valida_transicao_reserva" in linha
            for linha in diferencas(referencia, migrado)
        )
