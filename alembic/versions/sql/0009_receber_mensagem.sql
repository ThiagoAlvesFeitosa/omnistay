-- Receber mensagem da estadia: tipo classificar_mensagem e unicidade por mensagem.
-- Copia congelada do delta correspondente em docs/04-schema.sql (revisao 0009).

ALTER TABLE trabalho DROP CONSTRAINT ck_trabalho_tipo;
ALTER TABLE trabalho
    ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN ('enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
                    'enviar_boas_vindas', 'classificar_mensagem'));

CREATE UNIQUE INDEX uq_trabalho_classificar_mensagem_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'classificar_mensagem';
