"""Tipo registrar_pedido_servico e unicidade da origem da solicitacao.

Revision ID: 0012_registrar_pedido_servico
Revises: 0011_responder_duvida_catalogo
"""

from pathlib import Path

from alembic import op

revision = "0012_registrar_pedido_servico"
down_revision = "0011_responder_duvida_catalogo"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0012_registrar_pedido_servico.sql"


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute("DROP INDEX IF EXISTS uq_solicitacao_mensagem_origem;")
    cursor.execute(
        "DROP INDEX IF EXISTS uq_trabalho_registrar_pedido_servico_mensagem;"
    )
    cursor.execute("ALTER TABLE trabalho DROP CONSTRAINT IF EXISTS ck_trabalho_tipo;")
    cursor.execute(
        "ALTER TABLE trabalho ADD CONSTRAINT ck_trabalho_tipo "
        "CHECK (tipo IN ('enviar_coleta', 'interpretar_ficha', "
        "'enviar_lembrete', 'enviar_boas_vindas', 'classificar_mensagem', "
        "'responder_duvida'));"
    )
