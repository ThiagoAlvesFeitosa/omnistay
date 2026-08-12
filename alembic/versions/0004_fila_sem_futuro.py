"""Exclui reserva futura da vw_fila_do_dia.

Check-in previsto depois de hoje nao pertence a tela do turno. A contagem de
chegadas do dia permanece filtrando por igualdade com CURRENT_DATE.

Revision ID: 0004_fila_sem_futuro
Revises: 0003_fila_do_dia
"""

from pathlib import Path

from alembic import op

revision = "0004_fila_sem_futuro"
down_revision = "0003_fila_do_dia"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0004_fila_sem_futuro.sql"

VISAO_ANTERIOR = """
CREATE OR REPLACE VIEW vw_fila_do_dia AS
SELECT r.id_hotel,
       r.id_reserva,
       r.data_checkin_prevista,
       r.data_checkout_prevista,
       r.telefone_contato,
       r.status,
       h.nome_completo,
       rh.ficha_completa,
       (r.data_checkin_prevista < CURRENT_DATE
        AND r.status <> 'hospedado'
        AND r.status <> 'cancelada') AS chegada_nao_confirmada
  FROM reserva r
  LEFT JOIN reserva_hospede rh
         ON rh.id_reserva = r.id_reserva AND rh.titular
  LEFT JOIN hospede h
         ON h.id_hospede = rh.id_hospede
 WHERE r.status NOT IN ('encerrado', 'cancelada');

COMMENT ON VIEW vw_fila_do_dia IS
    'Alimenta a tela inicial do turno. A coluna chegada_nao_confirmada implementa a '
    'deteccao de divergencia temporal: o sistema nao sabe que o hospede chegou, mas '
    'sabe que ele deveria ter chegado. Inclui telefone_contato e data_checkout_prevista '
    'para a fila nominada da recepcao.';
"""


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute(VISAO_ANTERIOR)
