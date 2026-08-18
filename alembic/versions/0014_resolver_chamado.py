"""Tipo enviar_confirmacao_resolucao, transicao e autor na resolucao.

Revision ID: 0014_resolver_chamado
Revises: 0013_abrir_chamado_reclamacao
"""

from pathlib import Path

from alembic import op

revision = "0014_resolver_chamado"
down_revision = "0013_abrir_chamado_reclamacao"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0014_resolver_chamado.sql"


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute(
        "DROP TRIGGER IF EXISTS tg_valida_transicao_solicitacao ON solicitacao;"
    )
    cursor.execute("DROP FUNCTION IF EXISTS fn_valida_transicao_solicitacao();")
    cursor.execute(
        "DROP INDEX IF EXISTS uq_trabalho_enviar_confirmacao_resolucao_solicitacao;"
    )
    cursor.execute("ALTER TABLE trabalho DROP CONSTRAINT IF EXISTS ck_trabalho_tipo;")
    cursor.execute(
        "ALTER TABLE trabalho ADD CONSTRAINT ck_trabalho_tipo "
        "CHECK (tipo IN ('enviar_coleta', 'interpretar_ficha', "
        "'enviar_lembrete', 'enviar_boas_vindas', 'classificar_mensagem', "
        "'responder_duvida', 'registrar_pedido_servico', "
        "'abrir_chamado_reclamacao'));"
    )
