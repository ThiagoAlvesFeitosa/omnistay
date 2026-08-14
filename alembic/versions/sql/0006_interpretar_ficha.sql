-- Interpretação de ficha: tipo de trabalho, unicidade e estado_cadastro na fila.
-- Copia congelada do delta correspondente em docs/04-schema.sql (revisao 0006).

ALTER TABLE trabalho DROP CONSTRAINT ck_trabalho_tipo;
ALTER TABLE trabalho
    ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN ('enviar_coleta', 'interpretar_ficha'));

CREATE UNIQUE INDEX uq_trabalho_interpretar_ficha_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'interpretar_ficha';

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
       END AS estado_cadastro
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
    'data_checkout_prevista, status_envio_coleta da mensagem de coleta e '
    'estado_cadastro (aguardando, completa, parcial, leitura_humana).';
