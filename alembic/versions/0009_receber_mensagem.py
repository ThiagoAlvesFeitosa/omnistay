"""Tipo classificar_mensagem e unicidade por mensagem de entrada.

Revision ID: 0009_receber_mensagem
Revises: 0008_confirmar_chegada
"""

from pathlib import Path

from alembic import op

revision = "0009_receber_mensagem"
down_revision = "0008_confirmar_chegada"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0009_receber_mensagem.sql"


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute("DROP INDEX IF EXISTS uq_trabalho_classificar_mensagem_mensagem;")
    cursor.execute("ALTER TABLE trabalho DROP CONSTRAINT IF EXISTS ck_trabalho_tipo;")
    cursor.execute(
        "ALTER TABLE trabalho ADD CONSTRAINT ck_trabalho_tipo "
        "CHECK (tipo IN ('enviar_coleta', 'interpretar_ficha', "
        "'enviar_lembrete', 'enviar_boas_vindas'));"
    )
