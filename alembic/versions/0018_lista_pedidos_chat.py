"""Tipo enviar_lista_pedidos_chat e unicidade por reserva.

Revision ID: 0018_lista_pedidos_chat
Revises: 0017_confirmar_saida
"""

from pathlib import Path

from alembic import op

revision = "0018_lista_pedidos_chat"
down_revision = "0017_confirmar_saida"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0018_lista_pedidos_chat.sql"

CHECK_ANTERIOR = """
ALTER TABLE trabalho DROP CONSTRAINT IF EXISTS ck_trabalho_tipo;
ALTER TABLE trabalho
    ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN (
        'enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
        'enviar_boas_vindas', 'classificar_mensagem',
        'responder_duvida', 'registrar_pedido_servico',
        'abrir_chamado_reclamacao', 'enviar_confirmacao_resolucao',
        'enviar_pulso', 'registrar_resposta_pulso',
        'enviar_pesquisa_saida', 'interpretar_pesquisa_saida'
    ));
"""


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute(
        "DROP INDEX IF EXISTS uq_trabalho_enviar_lista_pedidos_chat_reserva;"
    )
    cursor.execute(CHECK_ANTERIOR)
