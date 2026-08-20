-- Lista de pedidos feitos pelo chat: tipo de trabalho e unicidade por reserva.
-- Copia congelada do delta correspondente em docs/04-schema.sql (revisao 0018).

ALTER TABLE trabalho DROP CONSTRAINT ck_trabalho_tipo;
ALTER TABLE trabalho
    ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN (
        'enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
        'enviar_boas_vindas', 'classificar_mensagem',
        'responder_duvida', 'registrar_pedido_servico',
        'abrir_chamado_reclamacao', 'enviar_confirmacao_resolucao',
        'enviar_pulso', 'registrar_resposta_pulso',
        'enviar_pesquisa_saida', 'interpretar_pesquisa_saida',
        'enviar_lista_pedidos_chat'
    ));

CREATE UNIQUE INDEX uq_trabalho_enviar_lista_pedidos_chat_reserva
    ON trabalho ( ((payload->>'id_reserva')::bigint) )
    WHERE tipo = 'enviar_lista_pedidos_chat';
