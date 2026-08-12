"""Amplia vw_fila_do_dia com telefone e checkout previsto.

O SQL nao e transcrito em chamadas do Alembic: aplica-se o arquivo companheiro
`sql/0003_fila_do_dia.sql`, copia congelada do bloco em `docs/04-schema.sql`.

Revision ID: 0003_fila_do_dia
Revises: 0002_sessao
"""

from pathlib import Path

from alembic import op

revision = "0003_fila_do_dia"
down_revision = "0002_sessao"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0003_fila_do_dia.sql"

VISAO_ANTERIOR = """
DROP VIEW IF EXISTS vw_fila_do_dia;

CREATE VIEW vw_fila_do_dia AS
SELECT r.id_hotel,
       r.id_reserva,
       r.data_checkin_prevista,
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
    'sabe que ele deveria ter chegado.';
"""


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute(VISAO_ANTERIOR)
