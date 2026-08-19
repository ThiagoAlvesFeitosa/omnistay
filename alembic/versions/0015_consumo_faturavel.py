"""Item vendavel, especializacao de consumo e fila humana de identificacao.

Revision ID: 0015_consumo_faturavel
Revises: 0014_resolver_chamado
"""

from pathlib import Path

from alembic import op

revision = "0015_consumo_faturavel"
down_revision = "0014_resolver_chamado"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0015_consumo_faturavel.sql"

VISAO_ANTERIOR = """
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
       m.status_envio AS status_envio_coleta,
       CASE
           WHEN r.status = 'ficha_recebida' THEN 'completa'
           WHEN r.status = 'ficha_parcial' THEN 'parcial'
           WHEN r.status = 'sem_cadastro_previo' THEN 'sem_cadastro_previo'
           WHEN r.status = 'aguardando_cadastro'
                AND EXISTS (
                    SELECT 1
                      FROM mensagem mh
                     WHERE mh.id_reserva = r.id_reserva
                       AND mh.direcao = 'recebida'
                       AND mh.classificacao_bruta->>'desfecho'
                           IN ('irreconhecivel', 'falha_extrator')
                ) THEN 'leitura_humana'
           WHEN r.status = 'aguardando_cadastro' THEN 'aguardando'
           ELSE r.status
       END AS estado_cadastro,
       (r.status = 'hospedado'
        AND NOT EXISTS (
              SELECT 1 FROM trabalho t
               WHERE t.tipo = 'enviar_boas_vindas'
                 AND (t.payload->>'id_reserva')::bigint = r.id_reserva
            )) AS boas_vindas_nao_enviadas,
       (r.status = 'hospedado'
        AND EXISTS (
              SELECT 1
                FROM mensagem mh
               WHERE mh.id_reserva = r.id_reserva
                 AND mh.direcao = 'recebida'
                 AND mh.classificacao_bruta->>'tipo' = 'classificacao_intencao'
                 AND mh.classificacao_bruta->>'desfecho'
                     IN ('encaminhado_humano', 'formato_invalido', 'indisponivel',
                         'duvida_nao_coberta')
            )) AS precisa_atendimento_humano
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
"""


def upgrade() -> None:
    sql = ARQUIVO_SQL.read_text(encoding="utf-8")
    cursor = op.get_bind().connection.cursor()
    cursor.execute(sql)


def downgrade() -> None:
    cursor = op.get_bind().connection.cursor()
    cursor.execute("DROP VIEW IF EXISTS vw_fila_do_dia;")
    cursor.execute(VISAO_ANTERIOR)
    cursor.execute(
        "DROP TRIGGER IF EXISTS tg_valida_transicao_lancamento ON consumo;"
    )
    cursor.execute("DROP FUNCTION IF EXISTS fn_valida_transicao_lancamento();")
    cursor.execute(
        "DROP TRIGGER IF EXISTS tg_solicitacao_consumo_tem_filho ON solicitacao;"
    )
    cursor.execute("DROP FUNCTION IF EXISTS fn_solicitacao_consumo_tem_filho();")
    cursor.execute("DROP TRIGGER IF EXISTS tg_consumo_pai_tipo_consumo ON consumo;")
    cursor.execute("DROP FUNCTION IF EXISTS fn_consumo_pai_tipo_consumo();")
    cursor.execute(
        "ALTER TABLE consumo DROP CONSTRAINT IF EXISTS ck_consumo_terminal_tem_autor;"
    )
    cursor.execute(
        "ALTER TABLE consumo ADD CONSTRAINT ck_consumo_lancado_tem_autor "
        "CHECK (status_lancamento <> 'lancado' "
        "OR (id_usuario_lancamento IS NOT NULL AND lancado_em IS NOT NULL));"
    )
    cursor.execute("DROP INDEX IF EXISTS uq_item_vendavel_hotel_nome_ativo;")
    cursor.execute("DROP INDEX IF EXISTS ix_item_vendavel_hotel_ativo;")
    cursor.execute("DROP TABLE IF EXISTS item_vendavel;")
