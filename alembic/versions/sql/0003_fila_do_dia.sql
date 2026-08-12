-- Visao ampliada da fila do dia (F1.1).
-- Copia congelada do bloco correspondente em docs/04-schema.sql.
-- DROP + CREATE: CREATE OR REPLACE nao permite inserir colunas no meio da lista.

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
