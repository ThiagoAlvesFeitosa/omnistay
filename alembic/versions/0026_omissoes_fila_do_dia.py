"""Omissoes de trabalho em falha na visao da fila do dia.

Revision ID: 0026_omissoes_fila_do_dia
Revises: 0025_resposta_recepcao
"""

from pathlib import Path

from alembic import op

revision = "0026_omissoes_fila_do_dia"
down_revision = "0025_resposta_recepcao"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0026_omissoes_fila_do_dia.sql"

VISAO_ANTERIOR = Path(__file__).parent / "sql" / "0025_resposta_recepcao.sql"


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    sql = VISAO_ANTERIOR.read_text(encoding="utf-8")
    # Recria a visao da 0025 (sem omissoes_brutas). Ignora ALTER/INDEX.
    inicio = sql.find("CREATE OR REPLACE VIEW vw_fila_do_dia")
    if inicio < 0:
        return
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql[inicio:])
