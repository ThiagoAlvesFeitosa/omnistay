"""Verifica a propria ferramenta de verificacao.

Se o extrator de inventario nao percebesse uma diferenca, os testes de conformidade
do esquema passariam sem provar nada. Cada caso aqui introduz uma divergencia
deliberada em uma categoria e exige que ela seja apontada pelo nome.
"""

import pytest

from testes.suporte.banco_descartavel import banco_vazio
from testes.suporte.inventario import diferencas, extrair_inventario

ESQUEMA_BASE = """
CREATE TABLE reserva (
    id_reserva BIGSERIAL PRIMARY KEY,
    status     VARCHAR(30) NOT NULL DEFAULT 'aguardando_cadastro',
    CONSTRAINT ck_reserva_status CHECK (status IN ('aguardando_cadastro', 'hospedado'))
);

CREATE INDEX ix_reserva_status ON reserva (status);

CREATE FUNCTION fn_valida_transicao_reserva()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT (OLD.status = 'aguardando_cadastro' AND NEW.status = 'hospedado') THEN
        RAISE EXCEPTION 'Transicao invalida: % -> %', OLD.status, NEW.status;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_valida_transicao_reserva
    BEFORE UPDATE OF status ON reserva
    FOR EACH ROW
    EXECUTE FUNCTION fn_valida_transicao_reserva();

CREATE VIEW vw_reservas_ativas AS
SELECT id_reserva FROM reserva WHERE status <> 'hospedado';
"""


@pytest.fixture
def inventario_base():
    with banco_vazio() as url:
        yield extrair_inventario(url, sql_inicial=ESQUEMA_BASE)


def inventario_com(sql_extra: str, sql_base: str = ESQUEMA_BASE):
    with banco_vazio() as url:
        return extrair_inventario(url, sql_inicial=sql_base + sql_extra)


@pytest.mark.postgres
def test_esquemas_iguais_nao_produzem_diferenca(inventario_base):
    outro = inventario_com("")

    assert diferencas(inventario_base, outro) == []


@pytest.mark.postgres
def test_coluna_a_mais_e_apontada(inventario_base):
    outro = inventario_com("ALTER TABLE reserva ADD COLUMN numero_quarto VARCHAR(10);")

    assert any("numero_quarto" in linha for linha in diferencas(inventario_base, outro))


@pytest.mark.postgres
def test_restricao_alterada_e_apontada(inventario_base):
    outro = inventario_com(
        "ALTER TABLE reserva DROP CONSTRAINT ck_reserva_status;"
        "ALTER TABLE reserva ADD CONSTRAINT ck_reserva_status"
        " CHECK (status IN ('aguardando_cadastro', 'hospedado', 'cancelada'));"
    )

    assert any("ck_reserva_status" in linha for linha in diferencas(inventario_base, outro))


@pytest.mark.postgres
def test_indice_ausente_e_apontado(inventario_base):
    outro = inventario_com("DROP INDEX ix_reserva_status;")

    assert any("ix_reserva_status" in linha for linha in diferencas(inventario_base, outro))


@pytest.mark.postgres
def test_corpo_de_funcao_alterado_e_apontado(inventario_base):
    outro = inventario_com(
        """
        CREATE OR REPLACE FUNCTION fn_valida_transicao_reserva()
        RETURNS TRIGGER AS $$
        BEGIN
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    assert any(
        "fn_valida_transicao_reserva" in linha for linha in diferencas(inventario_base, outro)
    )


@pytest.mark.postgres
def test_corpo_de_visao_alterado_e_apontado(inventario_base):
    outro = inventario_com(
        "CREATE OR REPLACE VIEW vw_reservas_ativas AS"
        " SELECT id_reserva FROM reserva WHERE status = 'hospedado';"
    )

    assert any("vw_reservas_ativas" in linha for linha in diferencas(inventario_base, outro))


@pytest.mark.postgres
def test_momento_de_trigger_alterado_e_apontado(inventario_base):
    outro = inventario_com(
        "DROP TRIGGER tg_valida_transicao_reserva ON reserva;"
        "CREATE TRIGGER tg_valida_transicao_reserva"
        " AFTER UPDATE OF status ON reserva"
        " FOR EACH ROW EXECUTE FUNCTION fn_valida_transicao_reserva();"
    )

    assert any(
        "tg_valida_transicao_reserva" in linha for linha in diferencas(inventario_base, outro)
    )


@pytest.mark.postgres
def test_alembic_version_nao_entra_no_inventario(inventario_base):
    outro = inventario_com("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL);")

    assert diferencas(inventario_base, outro) == []
