"""Tipo abrir_chamado_reclamacao e prazo de destaque do chamado.

Revision ID: 0013_abrir_chamado_reclamacao
Revises: 0012_registrar_pedido_servico
"""

from pathlib import Path

from alembic import op

revision = "0013_abrir_chamado_reclamacao"
down_revision = "0012_registrar_pedido_servico"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0013_abrir_chamado_reclamacao.sql"


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute(
        "DROP INDEX IF EXISTS uq_trabalho_abrir_chamado_reclamacao_mensagem;"
    )
    cursor.execute("ALTER TABLE trabalho DROP CONSTRAINT IF EXISTS ck_trabalho_tipo;")
    cursor.execute(
        "ALTER TABLE trabalho ADD CONSTRAINT ck_trabalho_tipo "
        "CHECK (tipo IN ('enviar_coleta', 'interpretar_ficha', "
        "'enviar_lembrete', 'enviar_boas_vindas', 'classificar_mensagem', "
        "'responder_duvida', 'registrar_pedido_servico'));"
    )
