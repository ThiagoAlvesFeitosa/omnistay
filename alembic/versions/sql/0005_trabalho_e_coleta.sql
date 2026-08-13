-- Fila de trabalho + status_envio_coleta na fila do dia.
-- Copia congelada do bloco correspondente em docs/04-schema.sql (revisao 0005).

CREATE TABLE trabalho (
    id_trabalho            BIGSERIAL    PRIMARY KEY,
    id_hotel               BIGINT       NOT NULL REFERENCES hotel (id_hotel),
    tipo                   VARCHAR(40)  NOT NULL,
    payload                JSONB        NOT NULL,
    status                 VARCHAR(20)  NOT NULL DEFAULT 'pendente',
    tentativas             INTEGER      NOT NULL DEFAULT 0,
    proxima_tentativa_em   TIMESTAMPTZ,
    erro_ultima_tentativa  TEXT,
    processando_desde      TIMESTAMPTZ,
    criado_em              TIMESTAMPTZ  NOT NULL DEFAULT now(),
    atualizado_em          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT ck_trabalho_tipo CHECK (tipo IN ('enviar_coleta')),
    CONSTRAINT ck_trabalho_status CHECK (
        status IN ('pendente', 'processando', 'concluido', 'falha')
    )
);

COMMENT ON TABLE trabalho IS
    'Fila duravel de trabalho assincrono. A API enfileira; o worker consome com '
    'SELECT FOR UPDATE SKIP LOCKED. Payload sem dado pessoal — so identificadores.';

CREATE UNIQUE INDEX uq_trabalho_enviar_coleta_reserva
    ON trabalho ( ((payload->>'id_reserva')::bigint) )
    WHERE tipo = 'enviar_coleta';

CREATE INDEX ix_trabalho_claim
    ON trabalho (status, proxima_tentativa_em)
    WHERE status IN ('pendente', 'processando');

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
