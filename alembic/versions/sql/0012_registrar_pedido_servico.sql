-- Registrar pedido de servico: tipo de trabalho e unicidade da origem.
-- Copia congelada do delta correspondente em docs/04-schema.sql (revisao 0012).

ALTER TABLE trabalho DROP CONSTRAINT ck_trabalho_tipo;
ALTER TABLE trabalho
    ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN ('enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
                    'enviar_boas_vindas', 'classificar_mensagem',
                    'responder_duvida', 'registrar_pedido_servico'));

CREATE UNIQUE INDEX uq_trabalho_registrar_pedido_servico_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'registrar_pedido_servico';

CREATE UNIQUE INDEX uq_solicitacao_mensagem_origem
    ON solicitacao (id_mensagem_origem)
    WHERE id_mensagem_origem IS NOT NULL;
