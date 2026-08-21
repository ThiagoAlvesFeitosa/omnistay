"""Unicidade da fonte, CHECK de URL e indice de concorrentes ativos.

Revision ID: 0019_cadastrar_concorrentes
Revises: 0018_lista_pedidos_chat
"""

from pathlib import Path

from alembic import op

revision = "0019_cadastrar_concorrentes"
down_revision = "0018_lista_pedidos_chat"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0019_cadastrar_concorrentes.sql"


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute("DROP INDEX IF EXISTS ix_concorrente_hotel_ativo;")
    cursor.execute("DROP INDEX IF EXISTS uq_concorrente_hotel_fonte;")
    cursor.execute(
        "ALTER TABLE concorrente DROP CONSTRAINT IF EXISTS ck_concorrente_url_fonte;"
    )
