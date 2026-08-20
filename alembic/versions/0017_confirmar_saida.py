"""Tipos de pesquisa de saida, unicidade, nota de checkout e visao.

Revision ID: 0017_confirmar_saida
Revises: 0016_pulso_segundo_dia
"""

from pathlib import Path

from alembic import op

revision = "0017_confirmar_saida"
down_revision = "0016_pulso_segundo_dia"
branch_labels = None
depends_on = None

ARQUIVO_SQL = Path(__file__).parent / "sql" / "0017_confirmar_saida.sql"

CHECK_ANTERIOR = """
ALTER TABLE trabalho DROP CONSTRAINT IF EXISTS ck_trabalho_tipo;
ALTER TABLE trabalho
    ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN (
        'enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
        'enviar_boas_vindas', 'classificar_mensagem',
        'responder_duvida', 'registrar_pedido_servico',
        'abrir_chamado_reclamacao', 'enviar_confirmacao_resolucao',
        'enviar_pulso', 'registrar_resposta_pulso'
    ));
"""

VISAO_ANTERIOR = r"""
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
                         'duvida_nao_coberta', 'item_ambiguo',
                         'identificacao_indisponivel')
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
    cursor.execute("DROP INDEX IF EXISTS uq_trabalho_interpretar_pesquisa_saida_mensagem;")
    cursor.execute("DROP INDEX IF EXISTS uq_trabalho_enviar_pesquisa_saida_reserva;")
    cursor.execute(
        "ALTER TABLE avaliacao DROP CONSTRAINT IF EXISTS ck_avaliacao_checkout_tem_nota;"
    )
    cursor.execute(CHECK_ANTERIOR)
    cursor.execute(VISAO_ANTERIOR)
    # Nao apaga horas_atribuicao_pesquisa_saida ja semeado: recuo de tipo/indice/visao.
