"""Tipos de pulso na fila, unicidade e prazo minimo por hotel.

Revision ID: 0016_pulso_segundo_dia
Revises: 0015_consumo_faturavel
"""

from pathlib import Path

from alembic import op

revision = "0016_pulso_segundo_dia"
down_revision = "0015_consumo_faturavel"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0016_pulso_segundo_dia.sql"

CHECK_ANTERIOR = """
ALTER TABLE trabalho DROP CONSTRAINT IF EXISTS ck_trabalho_tipo;
ALTER TABLE trabalho
    ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN (
        'enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
        'enviar_boas_vindas', 'classificar_mensagem',
        'responder_duvida', 'registrar_pedido_servico',
        'abrir_chamado_reclamacao', 'enviar_confirmacao_resolucao'
    ));
"""


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute("DROP INDEX IF EXISTS uq_trabalho_registrar_resposta_pulso_mensagem;")
    cursor.execute("DROP INDEX IF EXISTS uq_trabalho_enviar_pulso_reserva;")
    cursor.execute(CHECK_ANTERIOR)
    # Nao apaga horas_minimas_para_pulso ja semeado: recuo de tipo/indice, nao de prazo.
