"""Personalidade da assistente: valor largo e chave semeada.

Revision ID: 0022_personalidade_assistente
Revises: 0021_expurgo_retencao
"""

from pathlib import Path

from alembic import op

revision = "0022_personalidade_assistente"
down_revision = "0021_expurgo_retencao"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0022_personalidade_assistente.sql"


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute(
        "DELETE FROM parametro_hotel WHERE chave = 'personalidade_assistente';"
    )
    cursor.execute(
        "ALTER TABLE parametro_hotel ALTER COLUMN valor TYPE VARCHAR(255);"
    )
