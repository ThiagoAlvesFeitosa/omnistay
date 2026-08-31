"""Admite ficha_parcial <-> ficha_recebida no gatilho da reserva.

Revision ID: 0024_ficha_parcial_completa
Revises: 0023_convite_boas_vindas
"""

from pathlib import Path

from alembic import op

revision = "0024_ficha_parcial_completa"
down_revision = "0023_convite_boas_vindas"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0024_ficha_parcial_completa.sql"

FUNCAO_ANTERIOR = """
CREATE OR REPLACE FUNCTION fn_valida_transicao_reserva()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;

    IF NOT (
        (OLD.status = 'aguardando_cadastro' AND NEW.status IN
            ('ficha_recebida', 'ficha_parcial', 'sem_cadastro_previo', 'cancelada'))
     OR (OLD.status IN ('ficha_recebida', 'ficha_parcial', 'sem_cadastro_previo')
            AND NEW.status IN ('hospedado', 'cancelada'))
     OR (OLD.status = 'hospedado' AND NEW.status = 'encerrado')
    ) THEN
        RAISE EXCEPTION
            'Transicao de status invalida na reserva %: % -> %',
            OLD.id_reserva, OLD.status, NEW.status;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute(FUNCAO_ANTERIOR)
