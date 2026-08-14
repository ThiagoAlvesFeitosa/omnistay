"""Tipo interpretar_ficha e estado_cadastro na vw_fila_do_dia.

Revision ID: 0006_interpretar_ficha
Revises: 0005_trabalho_e_coleta
"""

from pathlib import Path

from alembic import op

revision = "0006_interpretar_ficha"
down_revision = "0005_trabalho_e_coleta"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0006_interpretar_ficha.sql"

VISAO_ANTERIOR = """
DROP VIEW IF EXISTS vw_fila_do_dia;

CREATE VIEW vw_fila_do_dia AS
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
        AND r.status <> 'cancelada') AS chegada_nao_confirmada,
       m.status_envio AS status_envio_coleta
  FROM reserva r
  LEFT JOIN reserva_hospede rh
         ON rh.id_reserva = r.id_reserva AND rh.titular
  LEFT JOIN hospede h
         ON h.id_hospede = rh.id_hospede
  LEFT JOIN LATERAL (
        SELECT msg.status_envio
          FROM mensagem msg
         WHERE msg.id_reserva = r.id_reserva
           AND msg.direcao = 'enviada'
         ORDER BY msg.enviada_em ASC, msg.id_mensagem ASC
         LIMIT 1
       ) m ON TRUE
 WHERE r.status NOT IN ('encerrado', 'cancelada')
   AND r.data_checkin_prevista <= CURRENT_DATE;

COMMENT ON VIEW vw_fila_do_dia IS
    'Alimenta a tela inicial do turno: check-in previsto ate hoje (chegadas do dia, '
    'atrasadas e hospedados). Reserva futura fica de fora. A coluna '
    'chegada_nao_confirmada sinaliza divergencia temporal. Inclui telefone_contato, '
    'data_checkout_prevista e status_envio_coleta da mensagem de coleta.';
"""


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute("DROP INDEX IF EXISTS uq_trabalho_interpretar_ficha_mensagem;")
    cursor.execute("ALTER TABLE trabalho DROP CONSTRAINT IF EXISTS ck_trabalho_tipo;")
    cursor.execute(
        "ALTER TABLE trabalho ADD CONSTRAINT ck_trabalho_tipo "
        "CHECK (tipo IN ('enviar_coleta'));"
    )
    cursor.execute(VISAO_ANTERIOR)
