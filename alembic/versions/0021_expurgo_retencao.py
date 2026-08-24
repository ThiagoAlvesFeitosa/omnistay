"""Comprovante de retencao e prazos de conteudo livre e ficha.

Revision ID: 0021_expurgo_retencao
Revises: 0020_coleta_agendada
"""

from pathlib import Path

from alembic import op

revision = "0021_expurgo_retencao"
down_revision = "0020_coleta_agendada"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0021_expurgo_retencao.sql"


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute("DROP INDEX IF EXISTS uq_execucao_retencao_hotel_dia;")
    cursor.execute("DROP TABLE IF EXISTS execucao_retencao;")
